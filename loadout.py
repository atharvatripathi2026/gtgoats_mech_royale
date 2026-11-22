"""Weapon, sensing and upgrade policy for the mechfight/1 game."""
import math

from survival import SUSTAINED_BOOST_RESERVE


def angle_delta(goal, actual):
    return (goal - actual + math.pi) % math.tau - math.pi


def clamp(x, low, high):
    return max(low, min(x, high))


class Loadout:
    def __init__(self, hello, navigator=None):
        self.config = hello.get("config", {})
        self.mech = self.config.get("mech", {})
        self.weapons = self.config.get("weapons", {})
        self.upgrades = {u["id"]: u for u in self.config.get("upgrades", [])}
        self.nav = navigator
        self.step = 1 / max(1, self.config.get("match", {}).get("tick_hz", 20))
        self.scan_phase = (hello.get("seed", 0) % 360) * math.pi / 180
        self.last_damage = -100
        self.last_hits = {}
        self.last_attacker = None
        self.last_bearing = 0
        self.last_swap = -100
        self.deferred_mortar_swaps = set()
        self.deferred_laser_swaps = set()
        self.mortar_group = None
        self.last_gun_capacity = None
        self.dodge_reload_floor = None
        self.arm_evidence_stage = None
        self.arm_damage = {"gun": 0., "laser": 0.}
        self.last_target = None
        self.laser_contact = None
        self.last_gun_hit = None
        self.last_npc_gun_hit = None
        self.used_gun_hit = None
        self.sight = {}

    def keep_cluster_mortar(self, obs, old, item):
        if old.get("kind") != "mortar" or item.get("kind") != "laser" or self.mortar_group is None:
            return False
        time, group = self.mortar_group
        stats = self.weapons.get("mortar", {}) | old.get("stats", {})
        if not 0 <= obs["t"] - time <= stats.get("cooldown", 2.6):
            return False
        me = obs["self"]
        radius = stats.get("splash_radius", 7.)
        speed = stats.get("speed", 72.)
        reach = speed * speed / stats.get("gravity", 22.)
        targets = [rival for rival in obs.get("mechs", ()) if rival.get("kind") == "mech"
                   and rival.get("id") in group
                   and 2 * radius < math.dist(me["pos"], rival["pos"]) < .90 * reach]
        return any(sum(math.dist(rival["pos"], other["pos"]) <= radius for other in targets) >= 3
                   for rival in targets)

    def pickup(self, obs, action):
        me = obs["self"]
        x, y, z = me["pos"]
        slots = me.get("weapons", [])
        held = {w.get("kind") for w in slots if w}
        reach = self.config.get("loot", {}).get("pickup_radius", 4)
        # A gun supports all ranges and remains usable during a sprint.
        # Lightning is especially valuable in the small endgame circle.
        small_zone = obs.get("zone", {}).get("radius", 560) < 85
        value = {"gun": 8, "mortar": 2.6, "laser": 3.5, "lightning": 3.1 + small_zone}
        enemies = [e for e in obs.get("mechs", []) if e.get("kind") == "mech"]
        nearest = min(enemies, key=lambda e: math.dist(me["pos"], e["pos"]), default=None)
        if nearest and math.dist(nearest["pos"], me["pos"]) < 100:
            opponent = nearest.get("weapons", [])
            value["laser"] += ("mortar" in opponent) - ("lightning" in opponent)
            value["lightning"] += ("laser" in opponent)
            value["mortar"] += ("lightning" in opponent) - ("laser" in opponent)
        pool = []
        for item in obs.get("pickups", []):
            kind = item.get("kind")
            if kind in held or kind not in value or "id" not in item:
                continue
            px, py, pz = item["pos"]
            distance = math.hypot(px - x, py - y)
            if distance <= reach and abs(z - pz) <= 4:
                pool.append((value[kind], -distance, item["id"]))
        if not pool:
            return
        rating, _, item_id = max(pool)
        if len(slots) < 2 or None in slots:
            action["take"] = item_id
        elif obs.get("t", 0) - self.last_swap > 10:
            replace = min(range(len(slots)), key=lambda i: value.get(slots[i].get("kind"), 0))
            old = slots[replace]
            if rating > value.get(old.get("kind"), 0) + .45 and old.get("charge", 0) <= 0:
                item = next(item for item in obs["pickups"] if item["id"] == item_id)
                if self.keep_cluster_mortar(obs, old, item):
                    return
                action.update(take=item_id, drop=replace)
                self.last_swap = obs.get("t", 0)

    def upgrade(self, obs, choices):
        me = obs["self"]
        stats = me.get("stats", {})
        late = obs.get("zone", {}).get("next_radius", 380) < 100
        held = {w["kind"]: w.get("stats", {}) for w in me.get("weapons", []) if w}
        health = me.get("hp", 1) / max(1, me.get("max_hp", 1))
        # Weights value fractional improvements to effective HP, mobility and
        # healing. Absolute camera and armor bonuses use their natural units.
        weights = {
            "hp": 1.8, "armor": 2.05, "walk_speed": 1.25, "boost_speed": 1,
            "energy": .43, "energy_regen": .43, "boost_drain": -.42,
            "jet_drain": -.16, "regen_delay": -.31, "regen_per_s": .25,
            "turn_rate": .16, "pitch_rate": .05, "near_range_bonus": .16,
            "vision_bonus": .12, "hearing": -.03,
        }
        if late:
            weights.update(hp=2.5, armor=2.3, regen_delay=-.15, regen_per_s=.1)
        elif health < .7:
            weights["regen_per_s"] = .38
        weapon_weights = {"damage": .8, "cooldown": -.6, "speed": .27,
                          "range": .36, "mag": .14, "reload": -.2,
                          "charge": -.35, "splash_radius": .3,
                          "pierce": .04, "chain": .08, "energy": -.25,
                          "cone_deg": .13}

        gun_fields = {"damage", "mag", "cooldown", "reload"}
        gun = {"damage": 45, "mag": 12, "cooldown": .24, "reload": 2.4}
        gun.update(self.weapons.get("gun", {}))
        gun.update(held.get("gun", {}))
        sustain = "gun" in held and not late and health >= .7

        def sustained_damage(weapon):
            rounds = max(1, weapon["mag"])
            cycle = rounds * max(.05, weapon["cooldown"]) + max(0, weapon["reload"])
            return max(1, weapon["damage"]) * rounds / cycle

        def score(choice, credit_sustain=True):
            total = 0.
            upgraded_gun = None
            gun_credit = 0.
            for effect in self.upgrades.get(choice.get("id"), choice).get("effects", []):
                path = effect.get("path", "").split(".")
                field = path[-1]
                if path[0] == "mech":
                    current = stats.get(field, self.mech.get(field, 1))
                    weight = weights.get(field, 0)
                    if field == "armor":
                        current = max(.1, 1 - current)
                    elif field in ("near_range_bonus", "vision_bonus"):
                        key = "near_range" if field == "near_range_bonus" else "range"
                        current += self.config.get("vision", {}).get(key, 45)
                elif len(path) == 3 and path[0] == "weapons" and path[1] in held:
                    current = held[path[1]].get(field, self.weapons.get(path[1], {}).get(field, 1))
                    weight = weapon_weights.get(field, 0)
                else:
                    continue
                scale = max(.1 if field == "armor" else 1, abs(current))
                change = effect.get("mul", 1) - 1 + effect.get("add", 0) / scale
                value = change * weight
                total += value
                if credit_sustain and sustain and path[0:2] == ["weapons", "gun"] and field in gun_fields:
                    if upgraded_gun is None:
                        upgraded_gun = gun.copy()
                    upgraded_gun[field] = upgraded_gun[field] * effect.get("mul", 1) + effect.get("add", 0)
                    gun_credit += value
            if upgraded_gun is not None:
                # A large magazine and a quicker reload work together across
                # repeated bursts. Keep the extra credit bounded so defense
                # stays competitive and still wins when the hull is vulnerable.
                gain = sustained_damage(upgraded_gun) / sustained_damage(gun) - 1
                total += clamp(.95 * gain - gun_credit, 0, .12)
            return total

        selected = max(range(len(choices)), key=lambda i: score(choices[i]))
        if (choices[selected].get("id") == "gun_mag" and "laser" in held
                and self.arm_damage["laser"] > self.arm_damage["gun"]):
            gun_slot = next((w for w in me.get("weapons", ()) if w and w.get("kind") == "gun"), None)
            if gun_slot and gun_slot.get("reload", 0) <= 0 and gun_slot.get("ammo", 0) >= .8 * gun["mag"]:
                without_bonus = max(range(len(choices)), key=lambda i: score(choices[i], credit_sustain=False))
                if choices[without_bonus].get("id") == "laser_damage":
                    return without_bonus
        return selected

    def dimensions(self, entity):
        kind = entity.get("kind", "crate")
        if kind == "mech":
            size = 1 + entity.get("cubes", 0) * self.config.get("cubes", {}).get("size_per_cube", .05)
            return self.mech.get("radius", 2.5) * size, self.mech.get("height", 9) * size
        shape = self.config.get("npc" if kind == "npc" else "crates", {})
        return shape.get("radius", 1.5), shape.get("height", 3)

    def sight_height(self, origin, entity, t):
        """Tracked mechs can be on the other side of a wall for five seconds."""
        _, height = self.dimensions(entity)
        if self.nav is None:
            return height * .5
        key = entity.get("id")
        cached = self.sight.get(key)
        if cached and t < cached[0]:
            return cached[1]
        x, y, z = entity["pos"]
        h = height * .49
        if not self.nav.line_clear(origin, (x, y, z + h)):
            h = height * .84
            if not self.nav.line_clear(origin, (x, y, z + h)):
                h = None
        self.sight[key] = (t + .22, h)
        return h

    def keep_prepared_gun_target(self, obs, origin, winner, score, priority):
        hit = self.last_gun_hit
        previous = getattr(self, "last_decision", {})
        t = obs.get("t", 0)
        if (hit is None or hit == self.used_gun_hit or hit[1] != self.last_target
                or previous.get("intent") != "engage" or winner.get("id") == hit[1]
                or winner.get("kind") != "mech" or winner.get("charging")
                or (winner.get("id") == self.last_attacker and t - self.last_damage < 3.2)):
            return None
        me = obs["self"]
        slots = me.get("weapons", ())
        gun = next((w for w in slots if w and w.get("kind") == "gun"), None)
        if not gun or not gun.get("ammo") or gun.get("reload", 0) or gun.get("cooldown", 0) > 2 * self.step:
            return None
        weapon = self.weapons.get("gun", {}) | gun.get("stats", {})
        if t - hit[0] > weapon.get("cooldown", .24) + 2 * self.step:
            return None
        old = next(((e, s) for s, e, fighting in priority if fighting and e.get("id") == hit[1]), None)
        if old is None or score - old[1] > 4:
            return None
        target = old[0]
        if target.get("kind") != "mech":
            return None
        for other in slots:
            if not other or other is gun:
                continue
            if other.get("charge", 0) > 0:
                return None
            if other.get("cooldown", 0) <= 2 * self.step:
                if other.get("kind") != "lightning":
                    return None
                arc = self.weapons.get("lightning", {}) | other.get("stats", {})
                if any(math.dist(origin, e["pos"]) <= arc.get("range", 45) + 2
                       for e in (target, winner)):
                    return None
        aim = me.get("aim", (0., 0.))
        stats = me.get("stats", {})
        turn = self.step * stats.get("turn_rate", 4)
        wx, wy = (winner["pos"][i] - origin[i] for i in (0, 1))
        new_bearing = math.atan2(wy, wx)
        opposing_aim = winner.get("aim")
        if opposing_aim and abs(angle_delta(new_bearing + math.pi, opposing_aim[0])) < .43:
            return None
        if abs(angle_delta(new_bearing, aim[0])) <= 2 * turn + .07:
            return None
        h = self.sight_height(origin, target, t)
        if h is None:
            return None
        body = (*target["pos"][:2], target["pos"][2] + h)
        offset = stats.get("radius", 2.5) + .5
        solution = self.solution("gun", origin, body, target.get("vel", (0, 0, 0)), weapon,
                                 offset, stats.get("max_pitch", 1.3))
        if solution is None or not stats.get("min_pitch", -.7) <= solution[1] <= stats.get("max_pitch", 1.3):
            return None
        yaw, pitch = solution
        radius, height = self.dimensions(target)
        dist = max(.1, math.dist(origin, body))
        if (abs(angle_delta(yaw, aim[0])) > turn + math.atan2(.8 * radius, dist)
                or abs(pitch - aim[1]) > self.step * stats.get("pitch_rate", 3) + math.atan2(.35 * height, dist)):
            return None
        if self.nav and not self.nav.line_clear(origin, body):
            return None
        self.used_gun_hit = hit
        return target, h, True

    @staticmethod
    def should_engage_player(distance, health, pursuer, wounded, attacker, late):
        return (late or attacker or distance < 45
                or (health >= .82 and distance < (198 if pursuer else 166))
                or (health >= .65 and pursuer and distance < 120)
                or (wounded and distance < (145 if pursuer else 100)))

    def target(self, obs, origin, evade, target_id):
        me = obs["self"]
        x, y, _ = me["pos"]
        t = obs.get("t", 0)
        health = me.get("hp", 1) / max(1, me.get("max_hp", 1))
        late = obs.get("alive", 16) <= 3 or obs.get("zone", {}).get("radius", 560) < 55
        armed = {w["kind"] for w in me.get("weapons", []) if w}
        rivals = sum(e.get("kind") == "mech" and math.dist(e["pos"][:2], (x, y)) <= 165
                     for e in obs.get("mechs", []))
        hold = self.step * self.config.get("match", {}).get("decide_every", 2)
        last_rifle_round = any(slot and slot.get("kind") == "gun" and slot.get("ammo") == 1
                               and not slot.get("reload", 0) and slot.get("cooldown", 0) <= hold
                               for slot in me.get("weapons", ()))
        ready_beam = any(slot and slot.get("kind") == "laser" and slot.get("cooldown", 0) <= self.step
                         and not slot.get("charge", 0) for slot in me.get("weapons", ()))
        engaged_squad = rivals >= 2 and (t - self.last_damage < 3 or late) and last_rifle_round and ready_beam
        priority = []
        for ent in (*obs.get("mechs", []), *obs.get("crates", [])):
            px, py, pz = ent["pos"]
            dist = math.hypot(px - x, py - y)
            yaw = math.atan2(py - y, px - x)
            kind = ent.get("kind", "crate")
            attacker = ent.get("id") == self.last_attacker and t - self.last_damage < 3.2
            if kind == "mech":
                facing = abs(angle_delta(yaw + math.pi, ent.get("aim", [yaw, 0])[0])) < .43
                wounded = ent.get("hp", 1e4) < me.get("max_hp", 1400) * .23
                vx, vy, _ = ent.get("vel", (0, 0, 0))
                approaching = (vx * (x - px) + vy * (y - py)) / max(1, dist) > 3
                pursuer = facing or approaching or attacker
                # Legs can retreat while the torso keeps firing. At high HP
                # use a clear long shot before the pursuer closes the gap.
                # When injured, preserve a repair window if contact is light.
                fight = self.should_engage_player(dist, health, pursuer, wounded, attacker, late)
                hull = max(1, self.mech.get("hp", 1400))
                remaining = ent.get("hp", hull) / hull
                since = t - self.last_hits.get(ent.get("id"), -100)
                focus = engaged_squad and 0 <= since <= hold + 1e-8
                if focus and remaining < .42 and dist <= 145:
                    fight = True
                score = (150 if fight else 30) - dist * .23 + 18 * attacker + 8 * wounded
                if focus:
                    # Keep pressure on a proven target through the handoff
                    # from the last rifle round to an available laser.
                    score += 56 * clamp(1 - remaining, 0, 1)
                    score += 16 * clamp(1 - since / 2.4, 0, 1)
                if pursuer:
                    score += 6
                opponent = ent.get("weapons", [])
                if "laser" in armed and "mortar" in opponent:
                    score += 6
                if "lightning" in armed and ent.get("charging") and dist < 45:
                    score += 16
            else:
                # Farm cubes only where we can collect them. Drones remember
                # attackers, and damaging any entity interrupts our HP repair.
                defensive = kind == "npc" and attacker and dist < 42
                designated = target_id is not None and ent.get("id") == target_id
                if not defensive and (evade or health < .78 or late or not me.get("in_zone", True)):
                    continue
                if dist > (85 if designated else 50) or abs(pz - me["pos"][2]) > 18:
                    continue
                score = 49 + 18 * designated + 33 * defensive + (6 if kind == "npc" else 0) - .48 * dist
                fight = True
            score -= 2 * abs(angle_delta(yaw, me.get("aim", [yaw, 0])[0]))
            if self.last_target is not None and ent.get("id") == self.last_target:
                score += 4
            priority.append((score, ent, fight))
        for score, ent, fight in sorted(priority, key=lambda row: -row[0])[:4]:
            h = self.sight_height(origin, ent, t)
            if h is not None:
                alternate = self.keep_prepared_gun_target(obs, origin, ent, score, priority) if fight else None
                if alternate is not None:
                    return alternate
                self.last_target = ent.get("id")
                return ent, h, fight
        self.last_target = None
        return None, 0, False

    @staticmethod
    def safe_zone_time(obs):
        me, zone = obs["self"], obs.get("zone", {})
        pos = me["pos"]
        if not me.get("in_zone", True):
            return False
        if "next_center" in zone:
            walk = me.get("stats", {}).get("walk_speed", 11.7)
            outside_next = math.dist(pos[:2], zone["next_center"]) - zone.get("next_radius", 380)
            time_left = zone.get("shrink_end", 480) - obs.get("t", 0)
            if outside_next > 2 and outside_next / max(1, walk) + 2 > time_left:
                return False
        return True

    def single_opponent(self, obs, target):
        pos = obs["self"]["pos"]
        t = obs.get("t", 0)
        for enemy in obs.get("mechs", []):
            if enemy.get("kind") != "mech" or enemy.get("id") == target.get("id"):
                continue
            if math.dist(pos, enemy["pos"]) > 105:
                continue
            cache = self.sight.get(enemy.get("id"))
            if cache is None or cache[0] < t or cache[1] is not None:
                return False
        return True

    def can_charge(self, obs, target, dist, evade):
        me = obs["self"]
        arc_range = self.weapons.get("lightning", {}).get("range", 45)
        if not self.safe_zone_time(obs) or ("lightning" in target.get("weapons", []) and dist < arc_range + 3):
            return False
        if not evade or obs.get("alive", 16) <= 2:
            return True
        health = me.get("hp", 1) / max(1, me.get("max_hp", 1))
        if health < .6 and dist < 40:
            return False
        # A half-speed charge remains viable in a duel. Against a group, use
        # the gun while sprinting until the secondary lines of fire break.
        return self.single_opponent(obs, target)

    def quiet_aim(self, obs, travel_yaw):
        t = obs.get("t", 0)
        if t - self.last_damage < 1.8:
            return [self.last_bearing, 0.]
        sounds = [s for s in obs.get("sounds", []) if s.get("dist") in ("near", "mid")
                  and s.get("bearing") is not None
                  and s.get("kind") in ("gun", "laser_charge", "laser", "mortar", "lightning", "boost")]
        if sounds:
            alarm = max(sounds, key=lambda s: (s.get("dist") == "near", s.get("kind") == "laser_charge"))
            return [alarm["bearing"], 0.]
        # Sweep the space either side of our path. Near-range sensors cover
        # the blind side and new damage or sound interrupts the sweep.
        return [angle_delta(travel_yaw + 2.17 * math.sin(t * .79 + self.scan_phase), 0), 0.]

    @staticmethod
    def solution(kind, origin, body, vel, stats, offset, max_pitch):
        """Choose an aim for one slot in the game's world coordinates."""
        dx, dy, dz = (body[i] - origin[i] for i in range(3))
        vx, vy, vz = vel
        if kind == "mortar":
            speed = stats.get("speed", 72)
            gravity = stats.get("gravity", 22)
            flight = math.hypot(dx, dy) / max(1, speed)
            # Iterate the game's low trajectory against a moving target.
            for _ in range(5):
                ax, ay = dx + vx * flight, dy + vy * flight
                distance = math.hypot(ax, ay)
                span = max(.25, distance - offset)
                rise = dz + vz * min(flight, .16)
                v2 = speed * speed
                disc = v2 * v2 - gravity * (gravity * span * span + 2 * rise * v2)
                if disc < 0:
                    return None
                pitch = math.atan2(gravity * span * span + 2 * rise * v2,
                                   span * (v2 + math.sqrt(disc)))
                flight = span / max(1, speed * math.cos(pitch))
            if flight > stats.get("ttl", 7) or pitch > max_pitch:
                return None
            return math.atan2(ay, ax), pitch
        if kind == "gun":
            speed = max(1, stats.get("speed", 252))
            flight = 0
            for _ in range(3):
                ax, ay = dx + vx * flight, dy + vy * flight
                az = dz + vz * min(flight, .20)
                flight = max(0., math.hypot(ax, ay, az) - offset) / speed
            if flight * speed > stats.get("range", 230):
                return None
        else:
            ax, ay, az = dx, dy, dz
            if math.hypot(ax, ay, az) - offset > stats.get("range", 45 if kind == "lightning" else 280):
                return None
        return math.atan2(ay, ax), math.atan2(az, math.hypot(ax, ay))

    def late_arc_bases(self, obs, origin, command, stats, move_speeds=None):
        """Forecast two supported ground steps using the outgoing movement."""
        if command is None or command["jump"]:
            return None
        me = obs["self"]
        motion = self.mech | stats
        x, y, z = me["pos"]
        muzzle_height = origin[2] - z
        floor_offset = z - self.nav.surface(x, y)
        if abs(floor_offset) > .15:
            return None
        speed = (motion.get("boost_speed", 19.5) if command["boost"]
                 else motion.get("walk_speed", 11.7))
        ux, uy = command["move"]
        move_norm = max(1., math.hypot(ux, uy))
        vx, vy = me["vel"][:2]
        delta = motion.get("ground_accel", 58.5) * self.step
        radius, height = motion.get("radius", 2.5), motion.get("height", 9.)
        cubes = self.config.get("cubes", {})
        reach = cubes.get("pickup_radius", 3.5)
        growth = cubes.get("size_per_cube", .05)
        growth_per_cube = growth / (1. + growth * me.get("cubes", 0))
        possible_cubes = set()
        grown = 1.
        bases = []
        for step_speed in (move_speeds if move_speeds is not None else (speed, speed)):
            scale = step_speed / move_norm
            dx, dy = ux * scale - vx, uy * scale - vy
            factor = min(1., delta / max(.001, math.hypot(dx, dy)))
            vx += dx * factor
            vy += dy * factor
            end = x + vx * self.step, y + vy * self.step
            floor = self.nav.surface(*end) + floor_offset
            dims = self.nav._dimensions(radius * grown)
            if (not z - .03 <= floor <= z + motion.get("step_up", 1.2)
                    or not self.nav._ground_segment(x, y, *end, *dims)
                    or not self.nav.raw_hull_corridor_clear((x, y, z), end, radius * grown, height * grown)):
                return None
            x, y = end
            z = max(z, floor)
            for cube in obs.get("cubes", ()):
                point = cube["pos"]
                if math.dist(end, point[:2]) <= reach + .15 and abs(z - point[2]) <= 4.15:
                    possible_cubes.add(cube["id"])
            count = len(possible_cubes)
            if count > 2:
                return None
            grown = 1. + count * growth_per_cube
            if possible_cubes and not self.nav.raw_hull_corridor_clear(
                (x, y, z), end, radius * grown, height * grown,
            ):
                return None
            sizes = (1. + n * growth_per_cube for n in range(count + 1))
            bases.append(tuple(((x, y, z + muzzle_height * size), radius * size + .5) for size in sizes))
        return bases

    def direct_lightning_on_threat(self, obs, selected, aim, origin, offset, stats, *,
                                   reserve_boost=False, motion_command=None, new_move_speed=None):
        """Use an idle arc against a close aimed rival on the existing line."""
        if not self.nav or not self.nav.loaded:
            return None
        me = obs["self"]
        if not me.get("grounded") or not self.safe_zone_time(obs):
            return None
        slots = me.get("weapons", ())
        if any(w and w.get("charge", 0) > 0 for w in slots):
            return None
        arc = next(((i, w) for i, w in enumerate(slots[:2])
                    if w and w.get("kind") == "lightning"), None)
        if arc is None:
            return None
        index, weapon = arc
        ws = self.weapons.get("lightning", {}) | weapon.get("stats", {})
        cooldown = weapon.get("cooldown", 0)
        second_step = cooldown > self.step
        verify_motion = cooldown > self.step + 1e-8
        stride = self.config.get("match", {}).get("decide_every", 2)
        energy = me.get("energy", 0)
        cost = ws.get("energy", 3)
        if (cooldown > 2 * self.step + 1e-8 or (second_step and stride < 2)
                or energy < cost + 30):
            return None
        if reserve_boost and any(w and w.get("kind") == "gun" and w.get("ammo", 1) > 0
                                 and w.get("reload", 0) <= .01 and w.get("cooldown", 0) <= 6 * self.step
                                 for w in slots):
            # If the loaded rifle will be ready shortly, leave enough power
            # for the ordinary boost reserve and two held movement commands.
            drain = stats.get("boost_drain", self.mech.get("boost_drain", 17))
            floor = SUSTAINED_BOOST_RESERVE * me.get("max_energy", 100)
            if floor < energy <= floor + 4 * self.step * drain + cost:
                return None
        current = me.get("aim", aim)
        speed = me.get("vel", (0., 0., 0.))
        motion_bases = self.late_arc_bases(obs, origin, motion_command, stats) if verify_motion else None
        if verify_motion and motion_bases is None:
            return None
        if verify_motion and new_move_speed is not None:
            field, default = ("boost_speed", 19.5) if motion_command["boost"] else ("walk_speed", 11.7)
            move_speed = stats.get(field, self.mech.get(field, default))
            # Check an offer applied both before movement and between the two steps.
            for speeds in ((new_move_speed, new_move_speed), (move_speed, new_move_speed)):
                upgraded = self.late_arc_bases(obs, origin, motion_command, stats, speeds)
                if upgraded is None:
                    return None
                motion_bases = [tuple(dict.fromkeys(old + new)) for old, new in zip(motion_bases, upgraded)]
        turn = self.step * stats.get("turn_rate", 4)
        tilt = self.step * stats.get("pitch_rate", 3)
        sample_steps = (0, 1, 2) if second_step else (0, 1)
        samples = []
        for step in sample_steps:
            # Keep the exact native first-ready projection. If the arc can
            # only fire on the second step, require a clear conductor at
            # every sampled pose until that later fire.
            slew_steps = max(1, step)
            yaw = current[0] + clamp(angle_delta(aim[0], current[0]), -slew_steps * turn, slew_steps * turn)
            pitch = current[1] + clamp(aim[1] - current[1], -slew_steps * tilt, slew_steps * tilt)
            direction = (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))
            linear = tuple(x + step * self.step * v for x, v in zip(origin, speed))
            bases = ((linear, offset),)
            if step and motion_bases:
                bases += motion_bases[step - 1]
            for base, muzzle_offset in bases:
                muzzle = tuple(x + muzzle_offset * v for x, v in zip(base, direction))
                if not self.nav.line_clear(base, muzzle):
                    return None
                samples.append((step, yaw, base, muzzle))
        reach = ws.get("range", 45)
        cone = math.radians(ws.get("cone_deg", 30))
        hits = []
        near_after_accel = []
        # A rival can enter the cone between samples even if its last
        # velocity carries it just outside. Reserve two steps of acceleration.
        uncertainty = 3 * self.step ** 2 * self.mech.get("ground_accel", 58.5)
        for ent in (*obs.get("mechs", ()), *obs.get("crates", ())):
            pos = ent["pos"]
            if math.dist(origin, pos) > reach + 12:
                continue
            _, height = self.dimensions(ent)
            body = (*pos[:2], pos[2] + .5 * height)
            velocity = ent.get("vel", (0., 0., 0.))
            bearing = math.atan2(pos[1] - origin[1], pos[0] - origin[0])
            projections = []
            for step, yaw, base, muzzle in samples:
                point = tuple(x + step * self.step * v for x, v in zip(body, velocity))
                dx, dy = point[0] - base[0], point[1] - base[1]
                aim_error = abs(angle_delta(math.atan2(dy, dx), yaw))
                projections.append((math.dist(muzzle, point), aim_error, muzzle, point, math.hypot(dx, dy)))
            distances = tuple(sample[0] for sample in projections)
            errors = tuple(sample[1] for sample in projections)
            if verify_motion and ent.get("kind") in ("mech", "npc"):
                for dist, error, _, _, planar_range in projections:
                    margin = (math.pi if planar_range <= uncertainty
                              else math.asin(uncertainty / planar_range))
                    if error <= cone + margin:
                        near_after_accel.append((dist - uncertainty, ent["id"]))
            if min(errors) > cone or min(distances) > reach:
                continue
            clear = [self.nav.line_clear(muzzle, point) for _, _, muzzle, point, _ in projections]
            if any(clear):
                hits.append((min(distances), max(distances), max(errors), bearing, ent, all(clear)))
        if not hits:
            return None
        nearest = min(hits, key=lambda hit: hit[0])
        near, far, error, bearing, threat, clear = nearest
        if (threat.get("kind") != "mech" or threat.get("id") == selected.get("id")
                or far > reach - 2 or error > .8 * cone
                or any(hit is not nearest and hit[0] <= far + 1 for hit in hits)
                or any(possible <= far + 1 and ident != threat["id"]
                       for possible, ident in near_after_accel)):
            return None
        facing = threat.get("aim")
        if (not threat.get("charging") and
                ("gun" not in threat.get("weapons", ()) or not facing
                 or abs(angle_delta(bearing + math.pi, facing[0])) > .43)):
            return None
        if not clear:
            return None
        if verify_motion and not self.late_arc_rival_growth_clear(obs, threat, samples, reach, cone):
            return None
        return index

    def late_arc_rival_growth_clear(self, obs, threat, samples, reach, cone):
        """Check grown conductor visibility and separation on either actor phase."""
        cubes = obs.get("cubes", ())
        if not cubes:
            return True
        rules = self.config.get("cubes", {})
        pickup = rules.get("pickup_radius", 3.5)
        accel = self.step ** 2 * self.mech.get("ground_accel", 58.5)
        growth = .5 * self.mech.get("height", 9.) * rules.get("size_per_cube", .05)
        firing = [(yaw, base, muzzle) for step, yaw, base, muzzle in samples if step == 2]
        entities = (threat, *(ent for ent in (*obs.get("mechs", ()), *obs.get("crates", ()))
                              if ent["id"] != threat["id"]))
        bodies = []
        for ent in entities:
            feet = ent["pos"]
            vel = ent.get("vel", (0., 0., 0.))
            _, height = self.dimensions(ent)
            possible = set()
            phases = []
            for step, margin in ((1, accel), (2, 3 * accel)):
                point = tuple(x + step * self.step * v for x, v in zip(feet, vel))
                if ent.get("kind") == "mech":
                    possible.update(cube["id"] for cube in cubes
                                    if math.dist(point[:2], cube["pos"][:2]) <= pickup + margin
                                    and abs(point[2] - cube["pos"][2]) <= 4. + margin)
                phases.append(((*point[:2], point[2] + .5 * height), len(possible)))
            bodies.append(phases)
        for phase in range(2):
            point, count = bodies[0][phase]
            for yaw, base, muzzle in firing:
                grown = [(*point[:2], point[2] + n * growth) for n in range(1, count + 1)]
                if any(math.dist(muzzle, body) > reach or not self.nav.line_clear(muzzle, body)
                       for body in grown):
                    return False
                far = max(math.dist(muzzle, body) for body in (point, *grown))
                for ent, phases in zip(entities[1:], bodies[1:]):
                    # Rival order is independent on a firing step. An actor
                    # ahead of us has moved twice, while one after us has moved once.
                    for (other, other_count), margin in zip(phases, (accel, 3 * accel)):
                        if not (count or other_count):
                            continue
                        dx, dy = other[0] - base[0], other[1] - base[1]
                        planar = math.hypot(dx, dy)
                        uncertainty = margin if ent.get("kind") in ("mech", "npc") else 0.
                        angle = (math.pi if planar <= uncertainty else math.asin(uncertainty / planar))
                        if abs(angle_delta(math.atan2(dy, dx), yaw)) > cone + angle:
                            continue
                        # Continuous height gives a lower bound for whole-cube growth.
                        z = clamp(muzzle[2], other[2], other[2] + other_count * growth)
                        if math.dist(muzzle, (*other[:2], z)) - uncertainty <= far:
                            return False
        return True

    def rising_rifle_alternate(self, obs, target, slots, muzzle, native_pitch):
        me = obs["self"]
        stats = me.get("stats", {})
        velocity = me.get("vel", (0., 0., 0.))
        min_pitch = stats.get("min_pitch", -.7)
        max_pitch = stats.get("max_pitch", 1.3)
        if (target.get("kind") != "mech" or me.get("grounded") or velocity[2] <= 0
                or native_pitch > min_pitch - .10 or not self.nav or not self.nav.loaded
                or any(w and w.get("charge", 0) > 0 for w in slots)):
            return None
        gun = next(((i, w) for i, w in enumerate(slots[:2]) if w and w.get("kind") == "gun"
                    and w.get("cooldown", 0) <= self.step and w.get("ammo", 0)
                    and not w.get("reload", 0)), None)
        if gun is None:
            return None
        index, weapon = gun
        rifle = self.weapons.get("gun", {}) | weapon.get("stats", {})
        projected = tuple(x + v * self.step for x, v in zip(muzzle, velocity))
        offset = stats.get("radius", 2.5) + .5
        actual = me.get("aim", (0., 0.))
        turn = stats.get("turn_rate", 4) * self.step
        tilt = stats.get("pitch_rate", 3) * self.step
        best = None
        for rival in obs.get("mechs", ()):
            if rival.get("kind") != "mech" or rival.get("id") == target.get("id"):
                continue
            radius, height = self.dimensions(rival)
            body = (*rival["pos"][:2], rival["pos"][2] + .49 * height)
            dist = math.dist(muzzle, body)
            if dist > min(165., rifle.get("range", 230)) or best and dist >= best[0]:
                continue
            vel = rival.get("vel", (0., 0., 0.))
            future = tuple(x + v * self.step for x, v in zip(body, vel))
            solution = self.solution("gun", projected, future, vel, rifle, offset, max_pitch)
            if not solution or not min_pitch <= solution[1] <= max_pitch:
                continue
            if (abs(angle_delta(solution[0], actual[0])) > turn + math.atan2(.70 * radius, dist)
                    or abs(solution[1] - actual[1]) > tilt + math.atan2(.30 * height, dist)):
                continue
            if not (self.nav.line_clear(muzzle, body) and self.nav.line_clear(projected, future)):
                continue
            yaw = actual[0] + clamp(angle_delta(solution[0], actual[0]), -turn, turn)
            pitch = actual[1] + clamp(solution[1] - actual[1], -tilt, tilt)
            direction = (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))
            bore = tuple(x + offset * component for x, component in zip(projected, direction))
            reach = min(rifle.get("range", 230), max(0., math.dist(projected, future) - offset))
            segment = max(.1, rifle.get("speed", 252) * self.step)
            points = [bore] + [
                tuple(x + min(reach, step * segment) * component for x, component in zip(bore, direction))
                for step in range(1, math.ceil(reach / segment) + 1)
            ]
            if (not self.nav.line_clear(projected, bore)
                    or not all(self.nav.line_clear(start, end) for start, end in zip(points, points[1:]))):
                continue
            best = dist, solution, rival["id"]
        return (index, best[1], best[2]) if best else None

    def brace_for_incoming_round(self, obs, action):
        """Face the predicted contact at the edge of frontal armor."""
        me = obs["self"]
        if not me.get("grounded") or action.get("jump") or any(action.get("fire", ())):
            return None
        stride = self.config.get("match", {}).get("decide_every", 2)
        hold = stride * self.step
        for slot in me.get("weapons", ()):
            if not slot:
                continue
            reload_left = slot.get("reload", 0)
            if slot.get("charge", 0) > 0:
                return None
            if slot.get("kind") == "gun" and not slot.get("ammo") and not reload_left:
                continue
            if max(reload_left, slot.get("cooldown", 0)) < 2 * hold:
                return None

        stats = me.get("stats", {})
        front = math.radians(stats.get("front_arc_deg", 180) / 2)
        turn = self.step * stats.get("turn_rate", 4)
        if turn <= 0 or front <= .08 or not self.nav or not self.nav.loaded:
            return None
        yaw = me.get("aim", (0., 0.))[0]
        radius = stats.get("radius", 2.5) - .2
        height = stats.get("height", 9)
        threat = []
        for shot in obs.get("projectiles", ()):
            if shot.get("kind") != "gun":
                continue
            x, y, z = (p - q for p, q in zip(shot["pos"], me["pos"]))
            vx, vy, vz = (p - q for p, q in zip(shot["vel"], me["vel"]))
            speed2 = vx * vx + vy * vy
            if speed2 <= 1:
                continue
            eta = -(x * vx + y * vy) / speed2
            miss = math.hypot(x + vx * eta, y + vy * eta)
            if not 0 < eta <= hold + self.step or miss >= radius:
                continue
            entry = max(0., eta - math.sqrt((radius ** 2 - miss ** 2) / speed2))
            if entry > hold or not .15 <= z + vz * entry <= height - .15:
                continue
            endpoint = tuple(p + v * entry for p, v in zip(shot["pos"], shot["vel"]))
            if not self.nav.line_clear(shot["pos"], endpoint):
                continue
            horizon = min(stride, max(1, math.ceil(entry / self.step))) * turn
            bearing = math.atan2(-shot["vel"][1], -shot["vel"][0])
            threat.append((bearing, horizon))
        if not threat:
            return None
        bearing, horizon = threat[0]
        if any(abs(angle_delta(other, bearing)) > .16 for other, _ in threat[1:]):
            return None
        horizon = min(h for _, h in threat)
        gap = angle_delta(bearing, yaw)
        natural = yaw + clamp(angle_delta(action["aim"][0], yaw), -horizon, horizon)
        if not front < abs(gap) <= front - .08 + horizon or abs(angle_delta(bearing, natural)) <= front:
            return None
        return yaw + math.copysign(abs(gap) - front + .08, gap)

    def retain_aim_on_wounded_drone(self, obs, action):
        """Keep a prepared rifle pointed toward the same drone during its dodge."""
        me = obs["self"]
        slots = [slot for slot in me.get("weapons", ()) if slot]
        rounds = obs.get("projectiles", ())
        enemies = obs.get("mechs", ())
        contact = self.last_npc_gun_hit
        if (contact is None or self.last_decision["intent"] != "scan"
                or not me.get("grounded") or not me.get("in_zone") or action.get("jump")
                or "take" in action or "pick" in action or action.get("reload")
                or any(action.get("fire", ())) or len(slots) != 1 or slots[0]["kind"] != "gun"
                or len(enemies) != 1 or not rounds or any(shot["kind"] != "npc" for shot in rounds)):
            return None
        gun, drone = slots[0], enemies[0]
        spec = self.weapons.get("gun", {}) | gun.get("stats", {})
        if (gun.get("reload") or gun.get("ammo", 0) < 3 or drone.get("kind") != "npc"
                or drone["id"] != contact[1] or obs["t"] - contact[0] > spec.get("cooldown", .24) + 1e-6
                or not 0 < drone.get("hp", 0) <= 2 * spec.get("damage", 45)):
            return None
        x, y, z = me["pos"]
        dx, dy = drone["pos"][0] - x, drone["pos"][1] - y
        yaw, pitch = me["aim"]
        if (math.hypot(dx, dy) > self.config.get("npc", {}).get("aggro_range", 42)
                or abs(angle_delta(math.atan2(dy, dx), yaw)) > .25
                or not self.nav or not self.nav.loaded):
            return None
        # Preserve frontal armor against every visible round while the dodge continues.
        for shot in rounds:
            vx, vy = shot["vel"][:2]
            if abs(angle_delta(math.atan2(-vy, -vx), yaw)) > .65:
                return None
        muzzle = x, y, z + me.get("stats", {}).get("muzzle_height", self.mech.get("muzzle_height", 7))
        if self.sight_height(muzzle, drone, obs["t"]) is None:
            return None
        return [yaw, pitch]

    def hold_occluded_laser(self, obs, action, selected, engage, aim, muzzle, steady):
        previous, self.laser_contact = self.laser_contact, None
        own = obs["self"]
        laser = next(((i, slot) for i, slot in enumerate(own.get("weapons", ())[:2])
                      if slot and slot.get("kind") == "laser"), None)
        if laser is None or not steady or not self.nav or not self.nav.loaded:
            return aim
        index, slot = laser
        if engage and selected.get("kind") == "mech" and action.get("fire", [False, False])[index]:
            self.laser_contact = selected["id"], obs["t"], None
            return aim
        if selected is not None or previous is None or not self.safe_zone_time(obs):
            return aim
        ident, last, lost = previous
        hold = self.step * self.config.get("match", {}).get("decide_every", 2)
        if obs["t"] - last > hold + 1e-6 or (lost is not None and obs["t"] - lost >= 3 * hold - 1e-6):
            return aim
        params = self.weapons.get("laser", {}) | slot.get("stats", {})
        if not params.get("min_charge", .15) <= slot.get("charge", 0) < params.get("charge", .75):
            return aim
        targets = [e for e in obs.get("mechs", ()) if e.get("kind") == "mech"]
        target = next((e for e in targets if e["id"] == ident), None)
        if target is None or any(math.dist(own["pos"], e["pos"]) < 100 for e in targets):
            return aim
        _, height = self.dimensions(target)
        velocity = target.get("vel", (0., 0., 0.))
        body = (*target["pos"][:2], target["pos"][2] + .49 * height)
        aim_at_target = self.solution("laser", muzzle, body, velocity, params, 0.,
                                      own.get("stats", {}).get("max_pitch", 1.3))
        if aim_at_target is None:
            return aim
        if lost is None and not all(self.nav.line_clear(muzzle, tuple(x + dt * v for x, v in zip(body, velocity)))
                                    for dt in (self.step, hold)):
            return aim
        fire = action.setdefault("fire", [False, False])
        fire[index] = True
        self.laser_contact = ident, obs["t"], obs["t"] if lost is None else lost
        return aim_at_target

    def closing_rifle_window(self, obs, target, rifle, movement):
        """Check that this same pursuer will enter native engagement by rifle readiness."""
        if target is None or target.get("kind") != "mech" or movement is None:
            return False
        me = obs["self"]
        stride = self.config.get("match", {}).get("decide_every", 2)
        hold = self.step * stride
        if rifle.get("cooldown", 0) > hold + self.step + 1e-8:
            return False
        dx, dy = (b - a for a, b in zip(me["pos"][:2], target["pos"][:2]))
        distance = math.hypot(dx, dy)
        rival_x, rival_y, _ = target.get("vel", (0., 0., 0.))
        own_x, own_y, _ = me.get("vel", (0., 0., 0.))
        forward = math.atan2(dy, dx) + math.pi
        facing = abs(angle_delta(forward, target.get("aim", (forward + math.pi, 0.))[0])) < .43
        if not facing:
            return False
        relative = math.hypot(dx + hold * (rival_x - own_x), dy + hold * (rival_y - own_y))
        # Check the planned move at both movement limits and with release
        # before, during, or after the next pair of physics steps.
        if stride != 2:
            return False
        stats = self.mech | me.get("stats", {})
        charge = stats.get("charge_move_mult", .5)
        acceleration = self.step * stats.get("ground_accel", 58.5)
        norm = max(1., math.hypot(*movement))
        projected = relative
        for speed in (stats.get("walk_speed", 11.7), stats.get("boost_speed", 19.5)):
            for limits in ((charge, charge), (charge, 1.), (1., 1.)):
                vx, vy = own_x, own_y
                future_x, future_y = dx + hold * rival_x, dy + hold * rival_y
                for limit in limits:
                    scale = speed * limit / norm
                    change_x, change_y = movement[0] * scale - vx, movement[1] * scale - vy
                    portion = min(1., acceleration / max(.001, math.hypot(change_x, change_y)))
                    vx, vy = vx + portion * change_x, vy + portion * change_y
                    future_x -= self.step * vx
                    future_y -= self.step * vy
                projected = max(projected, math.hypot(future_x, future_y))
        health = me.get("hp", 1.) / max(1., me.get("max_hp", 1.))
        wounded = target.get("hp", math.inf) < me.get("max_hp", 1400.) * .23
        return (projected < distance and not self.should_engage_player(
                    distance, health, True, wounded, False, False)
                and self.should_engage_player(projected, health, True, wounded, False, False))

    def preserve_rifle_during_beam_release(self, obs, action, target, previous, aim, muzzle):
        """Keep a usable burst when the last engaged rival can take this beam."""
        if (target is None or target.get("kind") != "mech" or not previous
                or previous.get("target_id") != target.get("id") or previous.get("intent") != "engage"
                or previous.get("aim_weapon") != "laser" or not self.nav or not self.nav.loaded
                or "take" in action or "pick" in action):
            return False
        me = obs["self"]
        fire = action.get("fire", (False, False))
        laser = next((slot for i, slot in enumerate(me.get("weapons", ())[:2])
                      if slot and slot.get("kind") == "laser" and not fire[i]), None)
        if laser is None or laser.get("cooldown", 0) > self.step + 1e-8:
            return False
        weapon = self.weapons.get("laser", {}) | laser.get("stats", {})
        if laser.get("charge", 0) < weapon.get("min_charge", .15):
            return False

        stats = self.mech | me.get("stats", {})
        yaw, pitch = me["aim"]
        turn = stats.get("turn_rate", 4.) * self.step
        tilt = stats.get("pitch_rate", 3.) * self.step
        yaw += clamp(angle_delta(aim[0], yaw), -turn, turn)
        pitch += clamp(clamp(aim[1], stats.get("min_pitch", -.7), stats.get("max_pitch", 1.3))
                       - pitch, -tilt, tilt)
        dx, dy, dz = math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch)
        offset = stats.get("radius", 2.5) + .5
        radius, height = self.dimensions(target)
        x, y, z = target["pos"]
        body = (x, y, z + .49 * height)
        own_velocity = me.get("vel", (0., 0., 0.))
        rival_velocity = target.get("vel", (0., 0., 0.))
        for delay in (0., self.step):
            origin = tuple(p + delay * v for p, v in zip(muzzle, own_velocity))
            bore = tuple(p + offset * v for p, v in zip(origin, (dx, dy, dz)))
            point = tuple(p + delay * v for p, v in zip(body, rival_velocity))
            delta = tuple(t - p for t, p in zip(point, bore))
            forward = sum(u * v for u, v in zip(delta, (dx, dy, dz)))
            gap = math.sqrt(max(0., sum(v * v for v in delta) - forward * forward))
            if (not 0 < forward < weapon.get("range", 280.) or gap > .8 * radius
                    or not self.nav.line_clear(origin, bore) or not self.nav.line_clear(bore, point)):
                return False
        return True

    def first_step_rifle_after_this_command(self, slots):
        stride = self.config.get("match", {}).get("decide_every", 2)
        horizon = (stride + 1) * self.step
        # Releasing a beam lets the body accelerate before the next observation.
        # Preserve the existing charge movement when the rifle can fire before
        # a second physics step settles the next observation's aim command.
        return any(slot and slot.get("kind") == "gun" and slot.get("ammo", 0) > 0
                   and not slot.get("reload", 0) and slot.get("cooldown", 0) <= horizon + 1e-8
                   for slot in slots[:2])

    def running_beam_window_closes(self, obs, target, aim, remaining, reach, movement):
        """Check the future firing step, not the instant charge fills."""
        if not self.nav or not self.nav.loaded or not movement:
            return False
        me = obs["self"]
        velocity = me.get("vel", (0., 0., 0.))
        target_velocity = target.get("vel", (0., 0., 0.))
        speed = math.hypot(*velocity[:2])
        if (not me.get("grounded") or speed <= 3 or math.hypot(*target_velocity[:2]) < 4
                or sum(v * move for v, move in zip(velocity[:2], movement)) < .9 * speed):
            return False
        stats = me.get("stats", {})
        offset = stats.get("radius", 2.5) + .5
        muzzle_height = stats.get("muzzle_height", self.mech.get("muzzle_height", 7))
        yaw, pitch = aim
        ray = (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))
        horizontal = ray[0] ** 2 + ray[1] ** 2
        if horizontal < .01:
            return False
        radius, height = self.dimensions(target)

        def positions(delay):
            base = tuple(x + delay * v + (muzzle_height if i == 2 else 0.)
                         for i, (x, v) in enumerate(zip(me["pos"], velocity)))
            muzzle = tuple(x + offset * d for x, d in zip(base, ray))
            feet = tuple(x + delay * v for x, v in zip(target["pos"], target_velocity))
            return base, muzzle, feet

        for delay in (0., self.step):
            base, muzzle, feet = positions(delay)
            depth = sum((feet[i] - muzzle[i]) * ray[i] for i in (0, 1)) / horizontal
            point = tuple(x + depth * d for x, d in zip(muzzle, ray))
            if (not 0 < depth < reach or math.dist(point[:2], feet[:2]) > .8 * radius
                    or not feet[2] + .15 * height <= point[2] <= feet[2] + .85 * height
                    or not self.nav.line_clear(base, muzzle) or not self.nav.line_clear(muzzle, point)
                    or not self.nav.line_clear(muzzle, (*feet[:2], feet[2] + .5 * height))):
                return False
        hold = self.config.get("match", {}).get("decide_every", 2) * self.step
        scheduled = math.ceil(remaining / hold - 1e-8) * hold + self.step
        for delay in (scheduled, scheduled + self.step):
            _, muzzle, feet = positions(delay)
            if any(self.nav.line_clear(muzzle, (*feet[:2], feet[2] + fraction * height))
                   for fraction in (.25, .5, .75)):
                return False
        return True

    def lower_mortar_for_hull_contact(self, obs, target, aim, weapon):
        me = obs["self"]
        if (not self.nav or not self.nav.loaded or target.get("kind") != "mech"
                or not me.get("grounded") or math.hypot(*me["vel"][:2]) > 12):
            return None
        velocity = target.get("vel", (0., 0., 0.))
        if abs(velocity[2]) > 1 or math.hypot(*velocity[:2]) > 8:
            return None
        stats = me.get("stats", {})
        step = self.step
        origin = tuple(p + v * step + (stats.get("height", 9) + .5 if j == 2 else 0.)
                       for j, (p, v) in enumerate(zip(me["pos"], me["vel"])))
        distance = math.dist(origin[:2], target["pos"][:2])
        if not 30 <= distance <= 125:
            return None
        radius, height = self.dimensions(target)
        offset = stats.get("radius", 2.5) + .5
        speed, gravity = weapon["speed"], weapon["gravity"]
        actual_yaw, actual_pitch = me["aim"]
        turn, tilt = stats.get("turn_rate", 4) * step, stats.get("pitch_rate", 3) * step
        yaw = actual_yaw + clamp(angle_delta(aim[0], actual_yaw), -turn, turn)
        native_pitch = actual_pitch + clamp(aim[1] - actual_pitch, -tilt, tilt)
        horizon = min(weapon.get("ttl", 7), distance / max(1., speed * math.cos(native_pitch)) + .65)

        def contact(pitch, lateral, bottom, top):
            direction = math.cos(yaw)*math.cos(pitch), math.sin(yaw)*math.cos(pitch), math.sin(pitch)
            first = tuple(p + offset*d for p, d in zip(origin, direction))
            if not self.nav.line_clear(origin, first):
                return False
            motion = tuple(speed * d for d in direction)
            for tick in range(1, math.ceil(horizon / step) + 1):
                last = tuple(p + step * v for p, v in zip(first, motion))
                tx, ty, tz = (p + (tick + 1) * step * v for p, v in zip(target["pos"], velocity))
                dx, dy = last[0] - first[0], last[1] - first[1]
                fraction = clamp(((tx - first[0])*dx + (ty - first[1])*dy) / max(.001, dx*dx + dy*dy), 0, 1)
                point = tuple(p + fraction*(q-p) for p, q in zip(first, last))
                if (math.dist(point[:2], (tx, ty)) <= lateral * radius
                        and bottom * height <= point[2] - tz <= top * height
                        and self.nav.line_clear(first, point)):
                    return True
                if not self.nav.line_clear(first, last):
                    return False
                first = last
                motion = (*motion[:2], motion[2] - step * gravity)
            return False

        if contact(native_pitch, 1.20, -.10, 1.10):
            return None
        lowest = max(stats.get("min_pitch", -.7), actual_pitch - tilt)
        highest = min(stats.get("max_pitch", 1.3), actual_pitch + tilt)
        for adjustment in (.015, .030, .045, .060):
            pitch = aim[1] - adjustment
            if lowest <= pitch <= highest and contact(pitch, .72, .15, .85):
                return aim[0], pitch
        return None

    def loft_over_near_roof(self, obs, target, aim, weapon):
        me = obs["self"]
        if (not me.get("grounded") or target.get("kind") != "mech"
                or not self.nav or not self.nav.loaded
                or math.hypot(*me["vel"][:2]) > 12):
            return None
        velocity = target.get("vel", (0., 0., 0.))
        if math.hypot(*velocity[:2]) > 8 or abs(velocity[2]) > 1:
            return None
        stats = me.get("stats", {})
        step = self.step
        reference = (*me["pos"][:2], me["pos"][2] + stats.get("height", 9) + .5)
        origin = tuple(p + step * v for p, v in zip(reference, me["vel"]))
        body_radius, height = self.dimensions(target)
        center = (*target["pos"][:2], target["pos"][2] + .5 * height)
        distance = math.dist(origin[:2], center[:2])
        if not 30 <= distance <= 124:
            return None
        offset = stats.get("radius", 2.5) + .5
        radius = weapon.get("splash_radius", 7)
        speed, gravity, ttl = weapon.get("speed", 72), weapon.get("gravity", 22), weapon.get("ttl", 7)
        actual_yaw, actual_pitch = me["aim"]
        turn, tilt = stats.get("turn_rate", 4) * step, stats.get("pitch_rate", 3) * step
        yaw = actual_yaw + clamp(angle_delta(aim[0], actual_yaw), -turn, turn)
        native_pitch = actual_pitch + clamp(aim[1] - actual_pitch, -tilt, tilt)
        horizon = min(ttl, distance / (speed * max(.3, math.cos(native_pitch))) + .4)

        def ground_contact(pitch, limit):
            direction = (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))
            previous = tuple(p + offset * d for p, d in zip(origin, direction))
            if not self.nav.line_clear(origin, previous):
                return origin, 0., previous
            velocity = tuple(speed * d for d in direction)
            for tick in range(1, math.ceil(limit / step) + 1):
                after = tuple(p + v * step for p, v in zip(previous, velocity))
                if not self.nav.line_clear(previous, after):
                    for fraction in (.25, .50, .75, 1.):
                        point = tuple(p + fraction * (q - p) for p, q in zip(previous, after))
                        if not self.nav.line_clear(previous, point):
                            return point, (tick - 1 + fraction) * step, after
                previous = after
                velocity = (*velocity[:2], velocity[2] - gravity * step)
            return None

        def predicted_body(flight):
            return tuple(p + (flight + step) * v for p, v in zip(center, velocity))

        # A nearby edge can interrupt the rival's linear travel. Bound the
        # alternative from the current body through a full ground stop.
        ground_accel = max(1., self.mech.get("ground_accel", 58.5))
        brake_time = math.hypot(*velocity[:2]) / (2 * ground_accel)
        stopped = tuple(p + brake_time * v for p, v in zip(center, velocity))
        clearance, body_height = self.nav._dimensions(body_radius)

        def blast_reaches(point, end, body, distance_limit):
            return all(math.dist(origin, body) <= distance_limit and self.nav.line_clear(origin, body)
                       for origin in (point, end))

        impact = ground_contact(native_pitch, horizon)
        if impact is None or math.dist(impact[0][:2], origin[:2]) > .82 * distance:
            return None
        point, flight, end = impact
        if any(math.dist(impact_point, body) < 1.3 * radius
               for impact_point in (point, end) for body in (center, stopped, predicted_body(flight))):
            return None
        for rise in (.04, .08, .12, .16):
            pitch = aim[1] + rise
            if not max(stats.get("min_pitch", -.7), actual_pitch - tilt) <= pitch <= min(
                    stats.get("max_pitch", 1.3), actual_pitch + tilt):
                continue
            landed = ground_contact(pitch, min(ttl, horizon + .5))
            if landed is None:
                continue
            point, flight, end = landed
            body = predicted_body(flight)
            if blast_reaches(point, end, body, .75 * radius):
                return aim[0], pitch
            if (not self.nav._ground_segment(*center[:2], *body[:2], clearance, body_height)
                    and all(blast_reaches(point, end, sample, radius - .35) for sample in (center, stopped))):
                return aim[0], pitch
        return None

    def defer_prepared_laser_swap(self, obs, action, previous_swap):
        """Keep a native laser charge when a new arc cannot serve this engagement."""
        item_id, index = action.get("take"), action.get("drop")
        fire = action.get("fire", ())
        me = obs["self"]
        if (item_id is None or item_id in self.deferred_laser_swaps or index is None
                or len(fire) <= index or sum(fire) != 1 or not fire[index]
                or not me.get("grounded") or action.get("jump") or "pick" in action
                or obs.get("projectiles") or obs.get("beams")
                or not self.nav or not self.nav.loaded or not self.safe_zone_time(obs)):
            return
        laser = me["weapons"][index]
        if (not laser or laser["kind"] != "laser" or laser.get("charge", 0) > 0
                or laser.get("cooldown", 0) > self.step + 1e-8):
            return
        item = next((e for e in obs.get("pickups", ())
                     if e["id"] == item_id and e["kind"] == "lightning"), None)
        if item is None:
            return
        rivals = [e for e in obs.get("mechs", ()) if e.get("kind") == "mech"]
        if len(rivals) != 1:
            return
        target = rivals[0]
        if target["id"] != self.last_decision.get("target_id") or self.last_decision.get("intent") != "engage":
            return
        stats = self.mech | me.get("stats", {})
        pos = me["pos"]
        dx, dy = (p - q for p, q in zip(target["pos"][:2], pos[:2]))
        vx, vy = (p - q for p, q in zip(target["vel"][:2], me["vel"][:2]))
        mx, my = action["move"]
        if dx * mx + dy * my > 0:
            return
        beam = self.weapons.get("laser", {}) | laser.get("stats", {})
        loot = self.config.get("loot", {})
        horizon = max(loot.get("equip_s", 1.), beam.get("charge", .75))
        # Avoid giving a visible rival the pickup during the charge window.
        rival_speed = max(self.mech.get("boost_speed", 19.5), math.hypot(*target["vel"][:2]))
        if math.dist(target["pos"][:2], item["pos"][:2]) <= loot.get("pickup_radius", 4.) + horizon * rival_speed:
            return
        arc_reach = self.weapons.get("lightning", {}).get("range", 45.)
        own_reach = arc_reach
        for name in me.get("upgrades", ()):
            for effect in self.upgrades.get(name, {}).get("effects", ()):
                if effect.get("path") == "weapons.lightning.range":
                    own_reach = own_reach * effect.get("mul", 1.) + effect.get("add", 0.)
        # Enemy equipment upgrades are hidden. Its visible cube total bounds
        # how many range upgrades it could have chosen.
        enemy_reach = 0.
        if "lightning" in target.get("weapons", ()):
            enemy_reach = arc_reach
            offers = sum(n <= target.get("cubes", 0)
                         for n in self.config.get("cubes", {}).get("upgrade_thresholds", ()))
            for upgrade in self.upgrades.values():
                for effect in upgrade.get("effects", ()):
                    if effect.get("path") == "weapons.lightning.range":
                        for _ in range(min(offers, upgrade.get("max", 1))):
                            enemy_reach = enemy_reach * max(1., effect.get("mul", 1.)) + max(0., effect.get("add", 0.))
        offset = stats.get("radius", 2.5) + .5
        margin = offset + 2 * self.step * stats.get("boost_speed", 19.5)
        relative_speed2 = vx * vx + vy * vy
        nearest = clamp(-(dx * vx + dy * vy) / max(1e-8, relative_speed2), 0., horizon)
        if math.hypot(dx + nearest * vx, dy + nearest * vy) <= max(own_reach, enemy_reach) + margin:
            return
        _, height = self.dimensions(target)
        body = (*target["pos"][:2], target["pos"][2] + .5 * height)
        base = (*pos[:2], pos[2] + stats.get("muzzle_height", 7.))
        span = math.dist(base, body)
        if not offset < span <= beam.get("range", 280):
            return
        bore = tuple(p + offset * (q - p) / span for p, q in zip(base, body))
        if (not self.nav.line_clear(base, bore) or not self.nav.line_clear(bore, body)
                or self.nav.short_segment_hits_raw_solid(base, bore)
                or self.nav.short_segment_hits_raw_solid(bore, body)):
            return
        action.pop("take")
        action.pop("drop")
        self.last_swap = previous_swap
        self.deferred_laser_swaps.add(item_id)

    def defer_firing_mortar_swap(self, obs, action, previous_swap):
        item_id, slot = action.get("take"), action.get("drop")
        fire = action.get("fire", ())
        me = obs["self"]
        if (item_id is None or item_id in self.deferred_mortar_swaps or slot is None
                or len(fire) <= slot or sum(fire) != 1 or not fire[slot]
                or self.last_decision.get("aim_weapon") != "mortar"
                or not me.get("grounded") or action.get("jump") or action.get("boost")
                or "pick" in action or not self.nav or not self.nav.loaded):
            return
        mortar = me["weapons"][slot]
        if (not mortar or mortar["kind"] != "mortar" or mortar.get("cooldown", 0) > self.step + 1e-8
                or not any(item["id"] == item_id and item["kind"] == "laser" for item in obs.get("pickups", ()))
                or not any(ent["id"] == self.last_decision.get("target_id") and ent.get("kind") == "mech"
                           for ent in obs.get("mechs", ()))):
            return

        stats = self.mech | me.get("stats", {})
        weapon = self.weapons.get("mortar", {}) | mortar.get("stats", {})
        current_yaw, current_pitch = me["aim"]
        yaw, pitch = action["aim"]
        dt = self.step
        turn = stats.get("turn_rate", 4) * dt
        tilt = stats.get("pitch_rate", 3) * dt
        yaw = current_yaw + clamp(angle_delta(yaw, current_yaw), -turn, turn)
        pitch = current_pitch + clamp(clamp(pitch, stats.get("min_pitch", -.7), stats.get("max_pitch", 1.3))
                                      - current_pitch, -tilt, tilt)
        direction = (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))
        x, y, z = me["pos"]
        vx, vy = me["vel"][:2]
        mx, my = action["move"]
        walk = stats.get("walk_speed", 11.7) / max(1., math.hypot(mx, my))
        dx, dy = mx * walk - vx, my * walk - vy
        ramp = min(1., dt * stats.get("ground_accel", 58.5) / max(.001, math.hypot(dx, dy)))
        speed = weapon.get("speed", 72.)
        reach = stats.get("radius", 2.5) + .5 + speed * dt
        for px, py in ((x, y), (x + dt * (vx + ramp * dx), y + dt * (vy + ramp * dy))):
            floor = self.nav.surface(px, py)
            if abs(floor - z) > .20:
                return
            for feet in (floor, z):
                base = (px, py, feet + stats.get("height", 9.) + .5)
                end = tuple(p + reach * v for p, v in zip(base, direction))
                if self.nav.short_segment_hits_raw_solid(base, end):
                    return

        # Let the existing self-blast check inspect the retained shot before
        # committing to the one-command deferral.
        probe = {key: value for key, value in action.items() if key not in ("take", "drop")}
        if self.mortar_self_blast_on_first_step(obs, probe) is not None:
            return
        action.pop("take")
        action.pop("drop")
        self.last_swap = previous_swap
        self.deferred_mortar_swaps.add(item_id)

    def obstructed_rifle_launch(self, obs, action):
        """Spare a round when nearby solid cover intercepts its launch."""
        fire = action.get("fire", ())
        me = obs["self"]
        slots = me.get("weapons", ())
        if (not any(fire) or not me.get("grounded") or action.get("jump") or action.get("boost")
                or action.get("reload") or "take" in action or "pick" in action
                or not self.nav or not self.nav.loaded
                or any(slot and slot.get("charge", 0) > 0 for slot in slots)
                or self.config.get("match", {}).get("decide_every", 2) != 2):
            return None
        dt = self.step
        index = next((i for i, (slot, held) in enumerate(zip(slots, fire))
                      if held and slot and slot.get("kind") == "gun" and slot.get("ammo", 0) > 0
                      and not slot.get("reload", 0) and slot.get("cooldown", 0) <= 2 * dt + 1e-8), None)
        if index is None:
            return None
        gun = slots[index]
        weapon = self.weapons.get("gun", {}) | gun.get("stats", {})
        # After a shot below this floor, the next quiet observation can
        # start a top-off and erase the benefit of keeping the round.
        reload_floor = .80 * weapon.get("mag", 12)
        if gun["ammo"] - 1 < reload_floor:
            return None
        stats = self.mech | me.get("stats", {})
        offset = stats.get("radius", 2.5) + .5
        reach = offset + dt * weapon.get("speed", 252.)
        x, y, z = me["pos"]
        nearby = [(e, self.dimensions(e)[0] + 1.5)
                  for e in (*obs.get("mechs", ()), *obs.get("crates", ()))
                  if math.dist((x, y), e["pos"][:2]) <= reach + self.dimensions(e)[0] + 3.]
        collect_distance = self.config.get("cubes", {}).get("pickup_radius", 3.5)
        if any(math.dist((x, y), cube["pos"][:2]) <= collect_distance + 1.5
               and abs(cube["pos"][2] - z) <= 4.25 for cube in obs.get("cubes", ())):
            return None

        yaw, pitch = me["aim"]
        aim_yaw, aim_pitch = action["aim"]
        aim_pitch = clamp(aim_pitch, stats.get("min_pitch", -.7), stats.get("max_pitch", 1.3))
        firing_step = 1 if gun.get("cooldown", 0) <= dt + 1e-8 else 2
        if firing_step == 2 and any(held and slot and slot.get("kind") == "laser"
                                    for slot, held in zip(slots, fire)):
            return None
        vx, vy = me["vel"][:2]
        mx, my = action["move"]
        walk = stats.get("walk_speed", 11.7) / max(1., math.hypot(mx, my))
        for step in range(firing_step):
            before = (x, y, z, yaw, pitch)
            yaw += clamp(angle_delta(aim_yaw, yaw), -stats.get("turn_rate", 4.) * dt,
                         stats.get("turn_rate", 4.) * dt)
            pitch += clamp(aim_pitch - pitch, -stats.get("pitch_rate", 3.) * dt,
                           stats.get("pitch_rate", 3.) * dt)
            ax, ay = mx * walk - vx, my * walk - vy
            rate = min(1., stats.get("ground_accel", 58.5) * dt / max(.001, math.hypot(ax, ay)))
            vx, vy = vx + rate * ax, vy + rate * ay
            nx, ny = x + dt * vx, y + dt * vy
            hull, height = offset - .5, stats.get("height", 9.)
            if (not self.nav.walkable(nx, y, hull) or not self.nav.walkable(nx, ny, hull)
                    or not self.nav.raw_hull_corridor_clear((x, y, z), (nx, y), hull, height)
                    or not self.nav.raw_hull_corridor_clear((nx, y, z), (nx, ny), hull, height)):
                return None
            x, y = nx, ny
            floor = self.nav.surface(x, y)
            if floor > z + stats.get("step_up", 1.2):
                floor = self.nav.ground(x, y)
            if floor < z - .25 or floor > z + .08:
                return None
            if floor >= z - .03:
                z = max(z, floor)
            elif step + 1 < firing_step:
                return None
            else:
                z = max(z - stats.get("gravity", 22.) * dt * dt, floor)
        muzzle_height = stats.get("muzzle_height", 7.)
        spread = math.radians(3 * weapon.get("spread_deg", .6))
        perturbations = ((0., 0.), (-spread, -spread), (-spread, spread),
                         (spread, -spread), (spread, spread))
        # Engines can fire before or after movement. Keep the corresponding
        # torso angle and test each legal pose with the supported height bracket.
        after = (x, y, z, yaw, pitch)
        for px, py, feet, az, el in (before, after, (x, y, before[2], yaw, pitch)):
            origin = px, py, feet + muzzle_height
            if self.nav.short_segment_hits_raw_solid(origin, origin):
                return None
            for dyaw, dpitch in perturbations:
                azimuth, elevation = az + dyaw, el + dpitch
                nx, ny = math.cos(azimuth), math.sin(azimuth)
                horizontal = math.cos(elevation)
                length = reach
                for entity, radius in nearby:
                    ex, ey = entity["pos"][0] - px, entity["pos"][1] - py
                    longitudinal = ex * nx + ey * ny
                    if longitudinal >= -radius and abs(ex * ny - ey * nx) <= radius:
                        length = min(length, (longitudinal - radius) / max(.01, horizontal))
                if length <= offset:
                    return None
                direction = nx * horizontal, ny * horizontal, math.sin(elevation)
                muzzle = tuple(p + offset * d for p, d in zip(origin, direction))
                if (not self.nav.line_clear(origin, muzzle)
                        or self.nav.short_segment_hits_raw_solid(origin, muzzle)):
                    return None
                # Check the near interval separately from the full flight.
                # Raster sampling changes phase as the segment grows.
                for extent in (min(length, offset + 5.), length):
                    end = tuple(p + extent * d for p, d in zip(origin, direction))
                    if (not self.nav.line_clear(muzzle, end)
                            and self.nav.short_segment_hits_raw_solid(muzzle, end)):
                        break
                else:
                    return None
        return index

    def mortar_self_blast_on_first_step(self, obs, action):
        """Detect a nearly immediate collision inside our own splash radius."""
        fire = action.get("fire", ())
        me = obs["self"]
        slots = me.get("weapons", ())
        if (sum(fire) != 1 or not me.get("grounded") or action.get("jump")
                or "take" in action or "pick" in action or not self.nav or not self.nav.loaded
                or any(slot and slot.get("charge", 0) > 0 for slot in slots)):
            return None
        index = fire.index(True)
        mortar = slots[index]
        if not mortar or mortar.get("kind") != "mortar" or mortar.get("cooldown", 0) > self.step:
            return None
        stats = self.mech | me.get("stats", {})
        weapon = self.weapons.get("mortar", {}) | mortar.get("stats", {})
        radius = weapon.get("splash_radius", 7.)
        hull = stats.get("radius", 2.5)
        height = stats.get("height", 9.)
        if any(math.dist(me["pos"], rival["pos"]) < 2 * radius + hull + self.dimensions(rival)[0]
               for rival in obs.get("mechs", ()) if rival.get("kind") == "mech"):
            return None
        dt = self.step
        offset = hull + .5
        reach = min(offset + dt * weapon.get("speed", 72), radius - .15)
        if reach <= offset + .25:
            return None

        yaw, pitch = me["aim"]
        aim_yaw, aim_pitch = action["aim"]
        turn = stats.get("turn_rate", 4) * dt
        tilt = stats.get("pitch_rate", 3) * dt
        yaw += clamp(angle_delta(aim_yaw, yaw), -turn, turn)
        pitch += clamp(clamp(aim_pitch, stats.get("min_pitch", -.7), stats.get("max_pitch", 1.3)) - pitch,
                       -tilt, tilt)
        direction = (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))
        x, y, z = me["pos"]
        vx, vy = me.get("vel", (0., 0., 0.))[:2]
        mx, my = action["move"]
        length = math.hypot(mx, my)
        boost = action.get("boost") and length > .01 and me.get("energy", 0) > dt * max(
            stats.get("jet_drain", 15), stats.get("boost_drain", 17))
        speed = stats.get("boost_speed", 19.5) if boost else stats.get("walk_speed", 11.7)
        dx, dy = mx * speed / max(1., length) - vx, my * speed / max(1., length) - vy
        ramp = min(1., stats.get("ground_accel", 58.5) * dt / max(.001, math.hypot(dx, dy)))

        for ux, uy in ((0., 0.), (vx, vy), (vx + ramp * dx, vy + ramp * dy)):
            foot = x + dt * ux, y + dt * uy
            if abs(self.nav.ground(*foot) - z) > .15:
                return None
            base = *foot, z + height + .5
            bore = tuple(p + offset * v for p, v in zip(base, direction))
            first_end = tuple(p + reach * v for p, v in zip(base, direction))
            if (not self.nav.line_clear(base, bore) or self.nav.line_clear(bore, first_end)
                    or first_end[2] > z + height + .5 * radius):
                return None
        # The final sample projects the held movement. A wall before the
        # muzzle also stops the shell, so confirm the full launch segment.
        if (self.nav.short_segment_hits_raw_solid(base, base)
                or not self.nav.short_segment_hits_raw_solid(base, first_end)):
            return None
        return index

    def mortar_wall_stop(self, target, origin, body, aim, weapon, offset):
        """Forecast a shorter lead for a ground target running into a broad wall."""
        if not self.nav or not self.nav.loaded or target.get("kind") != "mech":
            return None
        x, y, z = target["pos"]
        vx, vy, vz = target.get("vel", (0., 0., 0.))
        speed = math.hypot(vx, vy)
        distance = math.dist(origin[:2], body[:2])
        if (not 35 <= distance <= 120 or speed < 3 or abs(vz) > 2
                or abs(self.nav.ground(x, y) - z) > 1.2):
            return None
        shell_speed = max(1., weapon.get("speed", 72) * math.cos(aim[1]))
        arrival = distance / shell_speed
        for _ in range(4):
            predicted = (x + vx * arrival, y + vy * arrival)
            arrival = max(0., math.dist(origin[:2], predicted) - offset) / shell_speed
        horizon = min(.9, arrival)
        radius, height = self.dimensions(target)
        nx, ny = -vy / speed, vx / speed
        ray_height = z + .55 * height

        def clear(t, side=0.):
            start = (x + nx * side, y + ny * side, ray_height)
            end = (start[0] + vx * t, start[1] + vy * t, ray_height)
            return self.nav.line_clear(start, end)

        if any(clear(horizon, side) for side in (0., .55 * radius, -.55 * radius)):
            return None
        before_wall = 0.
        while before_wall + self.step < horizon and clear(before_wall + self.step):
            before_wall += self.step
        if before_wall < .15 or (arrival - before_wall) * speed < 3:
            return None
        radius_time = radius / speed
        stop = max(0., before_wall - radius_time)
        if stop == 0 and before_wall + radius_time <= horizon:
            flank = .55 * radius
            # A flank already in cover plus room on the other side cannot
            # support predicting an immediate stop across the whole hull.
            if any(not clear(0., side) and clear(before_wall + radius_time, -side)
                   for side in (-flank, flank)):
                return None
        return (x + vx * stop, y + vy * stop, body[2])

    def reserve_rifle_for_wounded_drone(self, obs, gun, muzzle):
        """Avoid a partial top-off while a just-hit drone can be finished."""
        contact = self.last_npc_gun_hit
        if contact is None or any(w and w["kind"] != "gun" for w in obs["self"]["weapons"]):
            return False
        weapon = self.weapons["gun"] | gun.get("stats", {})
        elapsed = obs["t"] - contact[0]
        if not 0 <= elapsed <= 2 * weapon.get("cooldown", .24):
            return False
        enemies = obs.get("mechs", ())
        if any(e.get("kind") == "mech" for e in enemies):
            return False
        projectiles = obs.get("projectiles", ())
        if not projectiles or any(shot.get("kind") != "npc" for shot in projectiles):
            return False
        npc = next((e for e in enemies if e.get("id") == contact[1] and e.get("kind") == "npc"), None)
        if npc is None or math.dist(npc["pos"], obs["self"]["pos"]) > self.config.get("npc", {}).get("aggro_range", 42):
            return False
        return (0 < npc["hp"] <= (gun["ammo"] - 1) * weapon.get("damage", 45)
                and self.sight_height(muzzle, npc, obs["t"]) is not None)

    def decide(self, obs, travel_yaw, evade=False, target_id=None, climbing=False, *,
               line_dodge=False, steady=False, movement=None, motion_command=None):
        self.late_arc_command = None
        me = obs["self"]
        t = obs.get("t", 0)
        stats = me.get("stats", {})
        zone = obs.get("zone") or {}
        armed = {w.get("kind") for w in me.get("weapons", ()) if w}
        stage = (zone.get("shrink_start"), zone.get("next_radius")) if armed == {"gun", "laser"} else None
        measure = stage is not None and stage == self.arm_evidence_stage
        if stage != self.arm_evidence_stage:
            self.arm_evidence_stage = stage
            self.arm_damage = {"gun": 0., "laser": 0.}
        if "mortar" not in armed:
            self.mortar_group = None
        else:
            group = {event["target"] for event in obs.get("events", ())
                     if event.get("type") == "hit" and event.get("weapon") == "mortar"
                     and event.get("amount", 0) > 0 and type(event.get("target")) is int
                     and 0 <= event["target"] < self.config.get("match", {}).get("mechs", 16)}
            if len(group) >= 3:
                self.mortar_group = t, group
        for event in obs.get("events", []):
            # Stage and equipment changes invalidate the evidence from the
            # previous interval. NPC and crate work does not count here.
            arm, target = event.get("weapon"), event.get("target")
            if (event.get("type") == "hit" and arm == "gun" and event.get("amount", 0) > 0
                    and type(target) is int and 0 <= target < self.config.get("match", {}).get("mechs", 16)):
                self.last_gun_hit = (t, target)
            if (measure and event.get("type") == "hit" and arm in self.arm_damage
                    and type(target) is int and 0 <= target < self.config.get("match", {}).get("mechs", 16)):
                self.arm_damage[arm] += event.get("amount", 0.)
            if event.get("type") == "hit":
                target = event.get("target")
                if arm == "gun" and event.get("amount", 0) > 0 and any(
                        e.get("id") == target and e.get("kind") == "npc" for e in obs.get("mechs", ())):
                    self.last_npc_gun_hit = (t, target)
                if isinstance(target, (int, float)) and 0 <= target < self.config.get("match", {}).get("mechs", 16):
                    self.last_hits[target] = t
            if event.get("type") == "damaged" and event.get("bearing") is not None:
                self.last_damage, self.last_bearing = t, event["bearing"]
                self.last_attacker = event.get("by")
        pos = me["pos"]
        muzzle = pos[0], pos[1], pos[2] + stats.get("muzzle_height", self.mech.get("muzzle_height", 7))
        ent, h, engage = self.target(obs, muzzle, evade, target_id)
        action = {}
        self.pickup(obs, action)
        choices = (obs.get("offer") or {}).get("choices", [])
        if choices:
            action["pick"] = self.upgrade(obs, choices)
        energy = me.get("energy", 100)
        slots = me.get("weapons", [])
        aim = self.quiet_aim(obs, travel_yaw)
        shots = {}
        previous = getattr(self, "last_decision", None)
        self.last_decision = {
            "target_id": ent.get("id") if ent else None,
            "intent": "engage" if engage else "track" if ent else "scan",
        }
        if ent is not None:
            body = (*ent["pos"][:2], ent["pos"][2] + h)
            vel = ent.get("vel", (0, 0, 0))
            radius, height = self.dimensions(ent)
            dist = max(.1, math.dist(muzzle, body))
            offset = stats.get("radius", 2.5) + .5
            aim = [math.atan2(body[1] - pos[1], body[0] - pos[0]),
                   math.atan2(body[2] - muzzle[2], math.dist(body[:2], pos[:2]))]
            for i, w in enumerate(slots[:2]):
                if not engage or not w or w.get("cooldown", 0) > self.step * 2:
                    continue
                kind = w.get("kind")
                ws = self.weapons.get(kind, {}) | w.get("stats", {})
                origin = muzzle
                if kind == "mortar":
                    if dist < max(18, ws.get("splash_radius", 7) + offset + 5):
                        continue
                    origin = pos[0], pos[1], pos[2] + stats.get("height", 9) + .5
                elif kind == "laser":
                    if not self.can_charge(obs, ent, dist, evade):
                        continue
                elif kind == "gun" and (w.get("reload", 0) > .01 or w.get("ammo", 1) <= 0):
                    continue
                elif kind == "lightning":
                    if dist > ws.get("range", 45) - 1:
                        continue
                    reserve = 30 if evade or ent.get("kind") != "mech" else 12
                    if (ent.get("kind") == "mech" and not climbing and self.safe_zone_time(obs)
                            and (ent.get("charging") or self.single_opponent(obs, ent))):
                        reserve = 0
                    if energy < ws.get("energy", 3) + reserve:
                        continue
                if kind not in ("gun", "laser", "lightning", "mortar"):
                    continue
                result = self.solution(kind, origin, body, vel, ws, offset, stats.get("max_pitch", 1.3))
                if result is None:
                    continue
                if kind == "mortar":
                    stopped_body = self.mortar_wall_stop(ent, origin, body, result, ws, offset)
                    if stopped_body is not None:
                        adjusted = self.solution(kind, origin, stopped_body, (0., 0., 0.), ws, offset,
                                                 stats.get("max_pitch", 1.3))
                        if adjusted is not None and adjusted[1] >= stats.get("min_pitch", -.7):
                            result = adjusted
                yaw, pitch = result
                if kind != "lightning" and not stats.get("min_pitch", -.7) <= pitch <= stats.get("max_pitch", 1.3):
                    continue
                if kind == "mortar" and self.nav is not None:
                    # A ledge directly in front of the tube can cause self-splash.
                    reach = ws.get("splash_radius", 7) + offset + 2
                    nearby = (origin[0] + reach * math.cos(yaw) * math.cos(pitch),
                              origin[1] + reach * math.sin(yaw) * math.cos(pitch),
                              origin[2] + reach * math.sin(pitch))
                    if not self.nav.line_clear(origin, nearby):
                        continue
                score = {"gun": 2., "mortar": 3.8, "laser": 4., "lightning": 1.}[kind]
                if kind == "mortar" and dist > 105 and math.hypot(*vel[:2]) > 7:
                    score -= 2
                if kind == "laser":
                    # During the early charge the gun can lead a moving
                    # opponent, then the torso settles on the beam's aim.
                    if w.get("charge", 0) + .20 < ws.get("charge", .75):
                        score = 1.5
                    else:
                        score += 2
                shots[i] = (score, yaw, pitch, kind, ws, w)
            if shots:
                primary_slot = max(shots, key=lambda index: shots[index][0])
                primary = shots[primary_slot]
                _, yaw, pitch, kind, _, _ = primary
                self.last_decision["aim_weapon"] = kind
                aim = [yaw, pitch]
                actual = me.get("aim", aim)
                turn = stats.get("turn_rate", 4) * self.step
                tilt = stats.get("pitch_rate", 3) * self.step
                yaw_next = actual[0] + clamp(angle_delta(yaw, actual[0]), -turn, turn)
                pitch_next = actual[1] + clamp(pitch - actual[1], -tilt, tilt)
                fire = [False, False]
                for i, (_, sy, sp, kind, ws, w) in shots.items():
                    err = abs(angle_delta(sy, yaw_next))
                    travel = abs(sp - pitch_next)
                    hit = err <= math.atan2(radius * .85 + .22, dist) and travel <= math.atan2(height * .38, dist)
                    if kind == "lightning":
                        fire[i] = err < math.radians(ws.get("cone_deg", 30)) * .85
                    elif kind == "laser":
                        charge = w.get("charge", 0)
                        full = ws.get("charge", .75)
                        fraction = ws.get("min_frac", .35)
                        damage = ws.get("damage", 315) * (fraction + (1 - fraction) * min(1, charge / max(.01, full)))
                        if "mortar" in ent.get("weapons", []):
                            damage *= 1 + ws.get("cookoff", .6)
                        lethal = charge >= ws.get("min_charge", .15) and ent.get("hp", 1e9) < damage * .9
                        fire[i] = not (hit and (charge >= full - .015 or lethal))
                    else:
                        fire[i] = hit
                if (primary[3] == "laser" and ent.get("kind") == "mech" and not climbing
                        and fire[primary_slot] and sum(fire) == 1
                        and not self.first_step_rifle_after_this_command(slots)):
                    full = primary[4].get("charge", .75)
                    charge = primary[5].get("charge", 0.)
                    remaining = full - charge
                    if (.65 * full <= charge and self.step <= remaining <= .35
                            and self.running_beam_window_closes(
                                obs, ent, (yaw_next, pitch_next), remaining,
                                primary[4].get("range", 280), movement)):
                        fire[primary_slot] = False
                if (primary[3] == "mortar" and sum(fire) == 1 and fire[primary_slot]
                        and primary[5].get("cooldown", 0) <= self.step and not climbing
                        and "take" not in action and "pick" not in action
                        and not any(slot and slot.get("charge", 0) > 0 for slot in slots)):
                    mortar_aim = self.lower_mortar_for_hull_contact(obs, ent, aim, primary[4])
                    if mortar_aim is None:
                        mortar_aim = self.loft_over_near_roof(obs, ent, aim, primary[4])
                    if mortar_aim is not None:
                        aim = mortar_aim
                action["fire"] = fire
            if engage and not shots:
                alternate = self.rising_rifle_alternate(obs, ent, slots, muzzle, aim[1])
                if alternate is not None:
                    index, aim, rival = alternate
                    action["fire"] = [index == i for i in range(2)]
                    self.last_decision.update(target_id=rival, aim_weapon="gun")
            if engage and not any(action.get("fire", ())):
                backup = self.direct_lightning_on_threat(
                    obs, ent, aim, muzzle, offset, stats, reserve_boost=evade and not line_dodge,
                    motion_command=motion_command,
                )
                if backup is not None:
                    late = slots[backup].get("cooldown", 0) > self.step + 1e-8
                    gear = self.late_arc_gear_effects(obs, action, backup) if late else ()
                    if gear and motion_command is not None:
                        new_speed = self.late_arc_move_speed(stats, motion_command, gear)
                        if new_speed is not None and self.direct_lightning_on_threat(
                            obs, ent, aim, muzzle, offset, stats, reserve_boost=evade and not line_dodge,
                            motion_command=motion_command, new_move_speed=new_speed,
                        ) == backup:
                            gear = ()
                    if gear == ():
                        if late:
                            self.late_arc_command = (backup, self.arc_command_pose(motion_command, aim), "fire" in action)
                        fire = action.setdefault("fire", [False, False])
                        fire[backup] = True
        aim = self.hold_occluded_laser(obs, action, ent, engage, aim, muzzle, steady)
        gun_slot = next((w for w in slots if w and w.get("kind") == "gun"), None)
        mag = (gun_slot.get("stats", {}).get("mag", self.weapons.get("gun", {}).get("mag", 12))
               if gun_slot else None)
        previous_mag, self.last_gun_capacity = self.last_gun_capacity, mag
        if not evade or not gun_slot or gun_slot.get("reload", 0):
            self.dodge_reload_floor = None
        if gun_slot and not gun_slot.get("reload", 0):
            ammo = gun_slot.get("ammo", mag)
            if (ent is None and evade and line_dodge and previous_mag is not None and mag > previous_mag
                    and previous_mag * .80 <= ammo < mag * .80):
                self.dodge_reload_floor = previous_mag * .80
            protect = self.dodge_reload_floor is not None and ammo >= self.dodge_reload_floor
            if ammo == 0:
                action["reload"] = True
            elif (not engage and ammo < mag * .80 and not protect
                  and not (line_dodge and not action.get("take") and "pick" not in action
                           and self.reserve_rifle_for_wounded_drone(obs, gun_slot, muzzle))):
                beam_handoff = (ammo >= 2 and not evade and not climbing and me.get("grounded")
                                and self.closing_rifle_window(obs, ent, gun_slot, movement)
                                and self.preserve_rifle_during_beam_release(obs, action, ent, previous, aim, muzzle))
                if not beam_handoff:
                    action["reload"] = True
        action["aim"] = aim
        return action

    @staticmethod
    def arc_command_pose(action, aim):
        return tuple(action["move"]), action["boost"], action["jump"], tuple(aim)

    def late_arc_gear_effects(self, obs, action, slot):
        if "take" in action and action.get("drop") == slot:
            return None
        index = action.get("pick")
        offer = obs.get("offer") or {}
        choices = offer.get("choices", ())
        if not choices:
            return ()
        forecast_inputs = {
            "mech.radius", "mech.height", "mech.muzzle_height", "mech.step_up",
            "mech.walk_speed", "mech.boost_speed", "mech.ground_accel",
            "mech.turn_rate", "mech.pitch_rate", "mech.min_pitch", "mech.max_pitch",
            "mech.energy", "mech.energy_regen", "mech.energy_regen_delay",
            "mech.boost_drain", "mech.jet_drain", "weapons.lightning.energy",
            "weapons.lightning.range", "weapons.lightning.cone_deg", "weapons.lightning.cooldown",
        }
        def relevant_effects(choice):
            effects = self.upgrades.get(choice.get("id"), choice).get("effects", ())
            return tuple(effect for effect in effects if effect.get("path") in forecast_inputs)

        effects = relevant_effects(choices[index]) if type(index) is int and 0 <= index < len(choices) else ()
        # The default may apply before the late shot if the offer expires.
        if offer.get("expires", math.inf) <= obs["t"] + 2 * self.step:
            return None if effects or relevant_effects(choices[0]) else ()
        return effects

    def late_arc_move_speed(self, stats, command, effects):
        paths = [effect.get("path") for effect in effects]
        if len(set(paths)) != len(paths) or set(paths) - {"mech.walk_speed", "mech.boost_speed"}:
            return None
        field, default = ("boost_speed", 19.5) if command["boost"] else ("walk_speed", 11.7)
        effect = next((rule for rule in effects if rule["path"] == "mech." + field), {})
        current = stats.get(field, self.mech.get(field, default))
        speed = current * effect.get("mul", 1.) + effect.get("add", 0.)
        return speed if math.isfinite(speed) and speed > 0 else None

    def confirm_late_arc_command(self, action):
        if self.late_arc_command is None:
            return
        slot, pose, had_fire = self.late_arc_command
        if pose != self.arc_command_pose(action, action["aim"]):
            if had_fire:
                action["fire"][slot] = False
            else:
                action.pop("fire", None)
