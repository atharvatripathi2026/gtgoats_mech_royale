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
        self.last_attacker = None
        self.last_bearing = 0
        self.last_swap = -100
        self.last_gun_capacity = None
        self.dodge_reload_floor = None
        self.arm_evidence_stage = None
        self.arm_damage = {"gun": 0., "laser": 0.}
        self.last_target = None
        self.laser_contact = None
        self.last_gun_hit = None
        self.used_gun_hit = None
        self.sight = {}

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

    def target(self, obs, origin, evade, target_id):
        me = obs["self"]
        x, y, _ = me["pos"]
        t = obs.get("t", 0)
        health = me.get("hp", 1) / max(1, me.get("max_hp", 1))
        late = obs.get("alive", 16) <= 3 or obs.get("zone", {}).get("radius", 560) < 55
        armed = {w["kind"] for w in me.get("weapons", []) if w}
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
                fight = (late or attacker or dist < 45 or
                         (health >= .82 and dist < (198 if pursuer else 166)) or
                         (health >= .65 and pursuer and dist < 120) or
                         (wounded and dist < (145 if pursuer else 100)))
                score = (150 if fight else 30) - dist * .23 + 18 * attacker + 8 * wounded
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

    def direct_lightning_on_threat(self, obs, selected, aim, origin, offset, stats, *, reserve_boost=False):
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
        energy = me.get("energy", 0)
        cost = ws.get("energy", 3)
        if weapon.get("cooldown", 0) > self.step or energy < cost + 30:
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
        turn = self.step * stats.get("turn_rate", 4)
        tilt = self.step * stats.get("pitch_rate", 3)
        yaw = current[0] + clamp(angle_delta(aim[0], current[0]), -turn, turn)
        pitch = current[1] + clamp(aim[1] - current[1], -tilt, tilt)
        direction = (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))
        speed = me.get("vel", (0., 0., 0.))
        projected = tuple(x + self.step * v for x, v in zip(origin, speed))
        muzzles = [tuple(x + offset * v for x, v in zip(point, direction))
                   for point in (origin, projected)]
        if any(not self.nav.line_clear(point, muzzle)
               for point, muzzle in zip((origin, projected), muzzles)):
            return None
        reach = ws.get("range", 45)
        cone = math.radians(ws.get("cone_deg", 30))
        hits = []
        for ent in (*obs.get("mechs", ()), *obs.get("crates", ())):
            pos = ent["pos"]
            if math.dist(origin, pos) > reach + 12:
                continue
            _, height = self.dimensions(ent)
            body = (*pos[:2], pos[2] + .5 * height)
            future = tuple(x + self.step * v for x, v in zip(body, ent.get("vel", (0., 0., 0.))))
            bearing = math.atan2(pos[1] - origin[1], pos[0] - origin[0])
            forecast_bearing = math.atan2(future[1] - projected[1], future[0] - projected[0])
            errors = (abs(angle_delta(bearing, yaw)), abs(angle_delta(forecast_bearing, yaw)))
            distances = (math.dist(muzzles[0], body), math.dist(muzzles[1], future))
            if min(errors) > cone or min(distances) > reach:
                continue
            if not (self.nav.line_clear(muzzles[0], body) or self.nav.line_clear(muzzles[1], future)):
                continue
            hits.append((min(distances), max(distances), max(errors), bearing, ent, body, future))
        if not hits:
            return None
        nearest = min(hits, key=lambda hit: hit[0])
        near, far, error, bearing, threat, body, future = nearest
        if (threat.get("kind") != "mech" or threat.get("id") == selected.get("id")
                or far > reach - 2 or error > .8 * cone
                or any(hit is not nearest and hit[0] <= far + 1 for hit in hits)):
            return None
        facing = threat.get("aim")
        if (not threat.get("charging") and
                ("gun" not in threat.get("weapons", ()) or not facing
                 or abs(angle_delta(bearing + math.pi, facing[0])) > .43)):
            return None
        if not (self.nav.line_clear(muzzles[0], body) and self.nav.line_clear(muzzles[1], future)):
            return None
        return index

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

    def decide(self, obs, travel_yaw, evade=False, target_id=None, climbing=False, *, line_dodge=False, steady=False):
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
                primary = max(shots.values(), key=lambda shot: shot[0])
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
                )
                if backup is not None:
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
            if ammo == 0 or (not engage and ammo < mag * .80 and not protect):
                action["reload"] = True
        action["aim"] = aim
        return action
