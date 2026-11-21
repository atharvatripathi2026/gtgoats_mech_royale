"""Weapon, sensing and upgrade policy for the mechfight/1 game."""
from copy import copy
import math


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
        self.last_arc_hit = -100
        self.last_long_hit = {}
        self.last_target = None
        self.sight = {}

    def mortar_replacement(self, obs, slots, target, engage, climbing):
        if (not engage or not target or target.get("kind") != "mech" or climbing
                or obs.get("zone", {}).get("radius", 560) < 100
                or obs.get("t", 0) - self.last_arc_hit <= 5
                or not self.safe_zone_time(obs)):
            return False
        arc = next((w for w in slots if w and w.get("kind") == "lightning"), None)
        if not arc or not any(w and w.get("kind") == "gun" for w in slots):
            return False
        me = obs["self"]
        stats = me.get("stats", {})
        arc_range = (self.weapons.get("lightning", {}) | arc.get("stats", {})).get("range", 45)
        rivals = [entity for entity in obs.get("mechs", ()) if entity.get("kind") == "mech"]
        if any(math.dist(me["pos"], entity["pos"]) <= arc_range + 18 for entity in rivals):
            return False
        muzzle = (*me["pos"][:2], me["pos"][2] + stats.get("muzzle_height", self.mech.get("muzzle_height", 7)))
        if math.dist(muzzle, target["pos"]) > 150:
            return False
        height = self.dimensions(target)[1]
        body = (*target["pos"][:2], target["pos"][2] + .49 * height)
        offset = stats.get("radius", 2.5) + .5
        limits = stats.get("min_pitch", -.7), stats.get("max_pitch", 1.3)
        origin = (*me["pos"][:2], me["pos"][2] + stats.get("height", 9) + .5)
        weapon = self.weapons.get("mortar", {})
        aim = self.solution("mortar", origin, body, target.get("vel", (0., 0., 0.)), weapon, offset, limits[1])
        if aim is None or not limits[0] <= aim[1] <= limits[1]:
            return False
        if self.nav is None:
            return True
        reach = weapon.get("splash_radius", 7) + offset + 2
        yaw, pitch = aim
        nearby = (origin[0] + reach * math.cos(yaw) * math.cos(pitch),
                  origin[1] + reach * math.sin(yaw) * math.cos(pitch),
                  origin[2] + reach * math.sin(pitch))
        return self.nav.line_clear(origin, nearby)

    def keeps_effective_ranged_weapon(self, obs, old, pickup, rivals):
        """Protect a recently successful ranged weapon while no arc can reach."""
        kind = old.get("kind")
        if pickup["kind"] != "lightning" or kind not in ("laser", "mortar"):
            return False
        hit_at, hit_target = self.last_long_hit.get(kind, (-100, None))
        if obs.get("t", 0) - hit_at > 4 or not any(e["id"] == hit_target for e in rivals):
            return False
        me = obs["self"]
        own_velocity = me.get("vel", (0., 0., 0.))
        reach = self.weapons.get("lightning", {}).get("range", 45) + 2
        ready = max(self.config.get("loot", {}).get("equip_s", 1), 1.5)
        for entity in rivals:
            delta = tuple(x - y for x, y in zip(entity["pos"], me["pos"]))
            velocity = tuple(x - y for x, y in zip(entity.get("vel", (0., 0., 0.)), own_velocity))
            opposing = -sum(x * y for x, y in zip(delta, velocity))
            nearest = clamp(opposing / max(.1, sum(v * v for v in velocity)), 0., ready)
            if math.hypot(*(x + nearest * v for x, v in zip(delta, velocity))) <= reach:
                return False
        return True

    def pickup(self, obs, action, target=None, engage=False, climbing=False):
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
        replacement = None
        for item in obs.get("pickups", []):
            kind = item.get("kind")
            if kind in held or kind not in value or "id" not in item:
                continue
            px, py, pz = item["pos"]
            distance = math.hypot(px - x, py - y)
            if distance <= reach and abs(z - pz) <= 4:
                if kind == "mortar" and replacement is None:
                    replacement = self.mortar_replacement(obs, slots, target, engage, climbing)
                pool.append((value[kind] + (2.2 if kind == "mortar" and replacement else 0),
                             -distance, item["id"]))
        if not pool:
            return
        rating, _, item_id = max(pool)
        if len(slots) < 2 or None in slots:
            action["take"] = item_id
        elif obs.get("t", 0) - self.last_swap > 10:
            replace = min(range(len(slots)), key=lambda i: value.get(slots[i].get("kind"), 0))
            old = slots[replace]
            if rating > value.get(old.get("kind"), 0) + .45 and old.get("charge", 0) <= 0:
                item = next(pickup for pickup in obs["pickups"] if pickup.get("id") == item_id)
                if self.keeps_effective_ranged_weapon(obs, old, item, enemies):
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

        def score(choice):
            total = 0.
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
                total += change * weight
            return total

        return max(range(len(choices)), key=lambda i: score(choices[i]))

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
        for _, ent, fight in sorted(priority, key=lambda row: -row[0])[:4]:
            h = self.sight_height(origin, ent, t)
            if h is not None:
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

    def gun_can_hit_pitch_edge(self, me, target, origin, yaw, pitch, weapon, offset, second_step):
        """Check a legal downward ray against the moving hull, not its center."""
        if not self.nav or not self.nav.loaded:
            return False
        stats = me.get("stats", {})
        low = stats.get("min_pitch", -.7)
        high = stats.get("max_pitch", 1.3)
        actual_yaw, actual_pitch = me.get("aim", (yaw, pitch))
        slew_time = self.step * (2 if second_step else 1)
        turn = stats.get("turn_rate", 4) * slew_time
        tilt = stats.get("pitch_rate", 3) * slew_time
        next_yaw = actual_yaw + clamp(angle_delta(yaw, actual_yaw), -turn, turn)
        next_pitch = clamp(actual_pitch + clamp(pitch - actual_pitch, -tilt, tilt), low, high)
        if abs(next_pitch - pitch) > .02:
            return False
        ray = (math.cos(next_yaw) * math.cos(next_pitch),
               math.sin(next_yaw) * math.cos(next_pitch), math.sin(next_pitch))
        horizontal = ray[0] ** 2 + ray[1] ** 2
        if horizontal < .01:
            return False
        pos = target["pos"]
        distance = math.dist(origin[:2], pos[:2])
        if not 13 <= distance <= 100:
            return False
        radius, height = self.dimensions(target)
        target_velocity = target.get("vel", (0., 0., 0.))
        velocity = me.get("vel", (0., 0., 0.))
        speed = max(1, weapon.get("speed", 252))
        first_launch = self.step if second_step else 0.
        for launch in (first_launch, first_launch + self.step):
            muzzle = tuple(x + launch * v + offset * component
                           for x, v, component in zip(origin, velocity, ray))
            delay = launch + distance / speed
            if second_step:
                # Advance to the intercept along the horizontal projection of the
                # steep ray. The projectile does not inherit our launch velocity.
                crossing = sum((pos[i] + launch * target_velocity[i] - muzzle[i]) * ray[i]
                               for i in (0, 1))
                closing_speed = speed * horizontal - sum(target_velocity[i] * ray[i] for i in (0, 1))
                if crossing <= 0 or closing_speed <= 0:
                    return False
                delay = launch + crossing / closing_speed
            feet = tuple(x + delay * v for x, v in zip(pos, target_velocity))
            depth = sum((feet[i] - muzzle[i]) * ray[i] for i in (0, 1)) / horizontal
            point = tuple(x + depth * component for x, component in zip(muzzle, ray))
            if (not 0 < depth <= weapon.get("range", 230)
                    or math.dist(point[:2], feet[:2]) > radius * .65
                    or not feet[2] + .12 * height <= point[2] <= feet[2] + .88 * height
                    or not self.nav.line_clear(muzzle, point)):
                return False
        return True

    def gun_flight_clear(self, origin, point, speed):
        length = math.dist(origin, point)
        if length <= 0:
            return False
        stride = speed * self.step
        if stride <= 0:
            return False
        start = origin
        for index in range(1, math.ceil(length / stride) + 1):
            fraction = min(1., index * stride / length)
            end = tuple(a + fraction * (b - a) for a, b in zip(origin, point))
            if not self.nav.line_clear(start, end) or (fraction < 1 and end[2] <= self.nav.ground(*end[:2])):
                return False
            start = end
        return True

    def imminent_gun_attacker(self, obs, duration):
        me = obs["self"]
        pos = me["pos"]
        own_vel = me.get("vel", (0., 0., 0.))
        stats = me.get("stats", {})
        radius, height = stats.get("radius", 2.5), stats.get("height", 9)
        rivals = [entity for entity in obs.get("mechs", ()) if entity.get("kind") == "mech"]
        if len(rivals) < 2:
            return None
        hits = []
        for shot in obs.get("projectiles", ()):
            if shot.get("kind") != "gun" or "vel" not in shot or "pos" not in shot:
                continue
            relative = tuple(a - b for a, b in zip(shot["vel"], own_vel))
            delta = tuple(a - b for a, b in zip(shot["pos"], pos))
            norm = relative[0] ** 2 + relative[1] ** 2
            if norm < 1:
                continue
            eta = -sum(delta[k] * relative[k] for k in (0, 1)) / norm
            if (not 0 < eta <= duration
                    or math.hypot(*(delta[k] + eta * relative[k] for k in (0, 1))) > radius * .8
                    or not 0 <= delta[2] + eta * relative[2] <= height):
                continue
            impact = tuple(x + eta * v for x, v in zip(shot["pos"], shot["vel"]))
            if not self.nav.line_clear(shot["pos"], impact):
                continue
            vx, vy = shot["vel"][:2]
            speed = math.hypot(vx, vy)
            if speed < 1:
                continue
            behind = []
            for rival in rivals:
                dx = shot["pos"][0] - rival["pos"][0]
                dy = shot["pos"][1] - rival["pos"][1]
                along = (dx * vx + dy * vy) / speed
                lateral = abs(dx * vy - dy * vx) / speed
                if 0 < along <= 235 and lateral <= self.dimensions(rival)[0] + 1:
                    behind.append(rival["id"])
            if len(behind) == 1:
                hits.append((eta, behind[0], math.atan2(-vy, -vx)))
        return max(hits, default=None)

    def next_gun_on_same_target(self, obs, ent, aim, gun_index, travel_yaw, evade, target_id, climbing):
        """Forecast a native next decision without consuming a gun round."""
        stride = self.config.get("match", {}).get("decide_every", 2)
        duration = self.step * stride
        me = obs["self"]
        stats = me.get("stats", {})

        def projected(entity):
            if "vel" not in entity:
                return entity
            return dict(entity, pos=[x + duration * v for x, v in zip(entity["pos"], entity["vel"])])

        projected_me = projected(me).copy()
        actual_yaw, actual_pitch = me["aim"]
        turn = stats.get("turn_rate", 4) * duration
        tilt = stats.get("pitch_rate", 3) * duration
        projected_me["aim"] = (actual_yaw + clamp(angle_delta(aim[0], actual_yaw), -turn, turn),
                               clamp(actual_pitch + clamp(aim[1] - actual_pitch, -tilt, tilt),
                                     stats.get("min_pitch", -.7), stats.get("max_pitch", 1.3)))
        projected_me["weapons"] = [dict(w, cooldown=max(0., w.get("cooldown", 0) - duration)) if w else None
                                   for w in me.get("weapons", ())]
        attacker = self.imminent_gun_attacker(obs, duration)
        events = []
        if attacker:
            _, source, bearing = attacker
            events.append({"type": "damaged", "by": source, "bearing": bearing})
        next_obs = dict(obs, self=projected_me, t=obs.get("t", 0) + duration,
                        events=events, offer=None,
                        mechs=[projected(entity) for entity in obs.get("mechs", ())])
        forecast = copy(self)
        forecast.sight = {}
        next_action = forecast.decide(next_obs, travel_yaw, evade, target_id, climbing)
        return (forecast.last_decision["target_id"] == ent["id"]
                and next_action.get("fire", (False, False))[gun_index])

    def gun_second_ray_reaches(self, me, target, muzzle, aim, weapon, offset):
        """Check the held ray when the gun becomes ready only on the second tick."""
        if not self.nav or not self.nav.loaded:
            return False
        position = target["pos"]
        if not 12 <= math.dist(position[:2], muzzle[:2]) <= 110:
            return False
        stats = me.get("stats", {})
        yaw, pitch = me.get("aim", aim)
        turn = 2 * self.step * stats.get("turn_rate", 4)
        tilt = 2 * self.step * stats.get("pitch_rate", 3)
        yaw += clamp(angle_delta(aim[0], yaw), -turn, turn)
        pitch = clamp(pitch + clamp(aim[1] - pitch, -tilt, tilt),
                      stats.get("min_pitch", -.7), stats.get("max_pitch", 1.3))
        ray = (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))
        horizontal = ray[0] ** 2 + ray[1] ** 2
        velocity = me.get("vel", (0., 0., 0.))
        target_velocity = target.get("vel", (0., 0., 0.))
        speed = weapon.get("speed", 252)
        closing = speed * horizontal - sum(target_velocity[i] * ray[i] for i in (0, 1))
        if horizontal < .05 or closing <= 0:
            return False
        radius, height = self.dimensions(target)
        for delay in (self.step, 2 * self.step):
            origin = tuple(x + delay * v + offset * r for x, v, r in zip(muzzle, velocity, ray))
            crossing = sum((position[i] + delay * target_velocity[i] - origin[i]) * ray[i]
                           for i in (0, 1))
            flight = crossing / closing
            if not 0 < flight * speed <= weapon.get("range", 230):
                return False
            point = tuple(x + r * flight * speed for x, r in zip(origin, ray))
            feet = tuple(x + v * (delay + flight) for x, v in zip(position, target_velocity))
            if (math.dist(point[:2], feet[:2]) > .8 * radius
                    or not .12 * height <= point[2] - feet[2] <= .88 * height
                    or not self.gun_flight_clear(origin, point, speed)):
                return False
        return True

    def lightning_reserve(self, obs, target, evade, climbing):
        if (target.get("kind") == "mech" and not climbing and self.safe_zone_time(obs)
                and (target.get("charging") or self.single_opponent(obs, target))):
            return 0
        return 30 if evade or target.get("kind") != "mech" else 12

    def lightning_muzzle_reaches(self, me, target, origin, aim, weapon, delay):
        """Check the short range band with the barrel's translated origin."""
        if not self.nav or not self.nav.loaded:
            return False
        stats = me.get("stats", {})
        current_yaw, current_pitch = me.get("aim", aim)
        turn = delay * stats.get("turn_rate", 4)
        tilt = delay * stats.get("pitch_rate", 3)
        yaw = current_yaw + clamp(angle_delta(aim[0], current_yaw), -turn, turn)
        desired_pitch = clamp(aim[1], stats.get("min_pitch", -.7), stats.get("max_pitch", 1.3))
        pitch = current_pitch + clamp(desired_pitch - current_pitch, -tilt, tilt)
        forward = math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch)
        offset = stats.get("radius", 2.5) + .5
        base = tuple(p + delay * v for p, v in zip(origin, me.get("vel", (0., 0., 0.))))
        muzzle = tuple(p + offset * ray for p, ray in zip(base, forward))
        x, y, z = target["pos"]
        current = (x, y, z + .5 * self.dimensions(target)[1])
        center = tuple(p + delay * v for p, v in zip(current, target.get("vel", (0., 0., 0.))))
        bearing = math.atan2(center[1] - muzzle[1], center[0] - muzzle[0])
        return (math.dist(muzzle, center) <= weapon.get("range", 45) - .7
                and abs(angle_delta(bearing, yaw)) <= .65 * math.radians(weapon.get("cone_deg", 30))
                and self.nav.line_clear(base, muzzle)
                and self.nav.line_clear(muzzle, current)
                and self.nav.line_clear(muzzle, center))

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

    def decide(self, obs, travel_yaw, evade=False, target_id=None, climbing=False, *, line_dodge=False):
        me = obs["self"]
        t = obs.get("t", 0)
        stats = me.get("stats", {})
        for event in obs.get("events", []):
            if (event.get("type") == "hit" and type(event.get("target")) is int
                    and 0 <= event["target"] < self.config.get("match", {}).get("mechs", 16)):
                weapon = event.get("weapon")
                if weapon == "lightning":
                    self.last_arc_hit = t
                elif weapon in ("laser", "mortar"):
                    self.last_long_hit[weapon] = (t, event["target"])
            if event.get("type") == "damaged" and event.get("bearing") is not None:
                self.last_damage, self.last_bearing = t, event["bearing"]
                self.last_attacker = event.get("by")
        pos = me["pos"]
        muzzle = pos[0], pos[1], pos[2] + stats.get("muzzle_height", self.mech.get("muzzle_height", 7))
        ent, h, engage = self.target(obs, muzzle, evade, target_id)
        action = {}
        self.pickup(obs, action, ent, engage, climbing)
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
            pitch_edge = None
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
                    reserve = self.lightning_reserve(obs, ent, evade, climbing)
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
                low_pitch = stats.get("min_pitch", -.7)
                if kind != "lightning" and not low_pitch <= pitch <= stats.get("max_pitch", 1.3):
                    if (kind == "gun" and pitch < low_pitch and ent.get("kind") == "mech"
                            and aim[1] < low_pitch):
                        second_step = w.get("cooldown", 0) > self.step
                        if not second_step or self.config.get("match", {}).get("decide_every", 2) >= 2:
                            pitch_edge = (i, yaw, low_pitch, ws, second_step)
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
            if (not shots and pitch_edge is not None
                    and not any(w and w.get("charge", 0) > 0 for w in slots)):
                i, yaw, pitch, weapon, second_step = pitch_edge
                if self.gun_can_hit_pitch_edge(me, ent, muzzle, yaw, pitch, weapon, offset, second_step):
                    aim = [yaw, pitch]
                    action["fire"] = [i == 0, i == 1]
                    self.last_decision["aim_weapon"] = "gun"
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
                if (line_dodge and primary[3] == "gun" and ent.get("kind") == "mech" and not any(fire)
                        and self.config.get("match", {}).get("decide_every", 2) >= 2
                        and not any(w and w.get("charge", 0) > 0 for w in slots)):
                    for i, (_, _, _, weapon_kind, weapon_stats, weapon) in shots.items():
                        if (weapon_kind == "gun" and weapon.get("ammo", 0) >= 2
                                and weapon.get("cooldown", 0) > self.step + 1e-7
                                and self.gun_second_ray_reaches(me, ent, muzzle, aim, weapon_stats, offset)
                                and not self.next_gun_on_same_target(obs, ent, aim, i, travel_yaw,
                                                                     evade, target_id, climbing)):
                            fire[i] = True
                action["fire"] = fire
        for w in slots:
            if w and w.get("kind") == "gun" and not w.get("reload", 0):
                mag = w.get("stats", {}).get("mag", self.weapons.get("gun", {}).get("mag", 12))
                ammo = w.get("ammo", mag)
                if ammo == 0 or (not engage and ammo < mag * .80):
                    action["reload"] = True
        if engage and ent.get("kind") == "mech" and not climbing and me.get("grounded", True):
            for i, w in enumerate(slots[:2]):
                if (not w or w.get("kind") != "lightning" or action.get("drop") == i
                        or action.get("fire", (False, False))[i]):
                    continue
                weapon = self.weapons.get("lightning", {}) | w.get("stats", {})
                reach = weapon.get("range", 45)
                if not reach - 1 < dist <= reach + 5:
                    continue
                reserve = max(12, self.lightning_reserve(obs, ent, evade, climbing))
                if energy < weapon.get("energy", 3) + reserve:
                    continue
                dt = self.step if w.get("cooldown", 0) <= self.step else 2 * self.step
                if (w.get("cooldown", 0) > dt or dt > self.step and
                        self.config.get("match", {}).get("decide_every", 2) < 2):
                    continue
                if self.lightning_muzzle_reaches(me, ent, muzzle, aim, weapon, dt):
                    action.setdefault("fire", [False, False])[i] = True
        action["aim"] = aim
        return action
