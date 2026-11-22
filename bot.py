"""Astra's mechfight/1 entry point."""
from functools import lru_cache
import hashlib
import math
from pathlib import Path
import os
import time

import mechfight
from adaptation import AdaptivePolicy, load_policy
from loadout import Loadout
from navigation import Navigator
from survival import Survival


@lru_cache(maxsize=1)
def controller_id():
    digest = hashlib.sha256()
    for name in ("bot.py", "adaptation.py", "loadout.py", "navigation.py", "survival.py"):
        digest.update(name.encode("ascii") + bytes(1))
        digest.update(Path(__file__).with_name(name).read_bytes())
    return digest.hexdigest()


class Bot:
    name = "Astra"

    def __init__(self, hello, policy=None):
        if hello.get("protocol") != "mechfight/1":
            raise ValueError("Unsupported protocol")
        self.slot = hello["slot"]
        self.nav = Navigator(hello["map"]["dir"], hello["config"])
        settings = load_policy() if policy is None else policy
        self.survival = Survival(hello, self.nav, loot_priority=settings.get("loot_priority", 1.0))
        self.loadout = Loadout(hello, self.nav)
        self.adaptation = AdaptivePolicy(hello, self.nav, policy=settings)
        self.match_metadata = {"policy": dict(settings), "controller": "adaptive-ground-v1",
                               "controller_sha256": controller_id()}
        self.last_decision = {}
        self.trace = os.environ.get("MECHFIGHT_TRACE") == "1"
        self.scan_yaw = (self.slot % 16) * math.tau / 16

        self.zone_anchor_fallback = None
        self.zone_anchor_retry = 0
        self.ground_line_boost_tick = None
        self.pending_ground_line_boost_tick = None
        self.last_escape_grace = -math.inf
        self.outbound_hold_until = -math.inf
        self.outbound_hold_phase = None
        self.first_loot_targets = set()
        self.first_cube_rest = False
        self.loot_descent = None
        self.cube_taper = None
        self.wall_round_refill = None
        self.pending_wall_round = None
        self.postkill_refill_confirmation = None
        self.loot_scan_until = -math.inf
        self.loot_scan_point = None
        self.shelter_grounded_tick = None
        self.loot_escape_walk = None

    def quiet_ground_anchor(self, obs, plan, action, jet, settled):
        me = obs["self"]
        zone = obs.get("zone") or {}
        now = obs.get("t", 0)
        if (not self.nav.loaded or not me.get("grounded") or not me.get("in_zone")
                or (jet and not settled) or action["boost"] or plan["dodge"] or plan["mode"] != "zone"
                or plan["enemy_pressure"] > .1 or not zone.get("next_center")
                or not zone.get("shrink_start", now + 1) <= now < zone.get("shrink_end", now)
                or not 25 <= zone.get("next_radius", 0) <= 140
                or self.loadout.last_decision.get("target_id") is not None
                or any(e.get("kind") == "mech" for e in obs.get("mechs") or ())
                or any(action.get("fire", ()))
                or any(w and w.get("charge", 0) > 0 for w in me.get("weapons", ()))):
            self.zone_anchor_fallback = None
            return None
        x, y, z = me["pos"]
        goal = plan["goal"]
        center = tuple(zone["next_center"])
        radius = me.get("stats", {}).get("radius", 2.5)
        dimensions = self.nav._dimensions(radius)
        fallback = self.zone_anchor_fallback
        if fallback is not None and fallback[0] == center:
            points = fallback[1]
            if len(points) > 1 and math.dist((x, y), points[0]) < 1.8:
                points.pop(0)
            px, py = points[0]
            if self.nav._ground_segment(x, y, px, py, *dimensions):
                d = math.dist((x, y), (px, py))
                if d < .6:
                    return [0., 0.]
                scale = 1 / max(4., d)
                return [(px - x) * scale, (py - y) * scale]
        self.zone_anchor_fallback = None
        if (now < self.zone_anchor_retry or any(action["move"]) or len(goal) != 2
                or math.dist((x, y), goal) < 1.2 or self.nav.surface(*goal) - z < 3
                or self.nav._ground_segment(x, y, *goal, *dimensions)):
            return None
        self.zone_anchor_retry = now + .75
        original = math.dist((x, y), center)
        # Match the native future-circle safety buffer before incurring
        # extra travel to replace its preferred (deeper) approach point.
        buffered_radius = zone["next_radius"] - min(radius + 14, zone["next_radius"] * .33)
        if original <= buffered_radius:
            return None
        safe_radius = min(original - 3, zone["next_radius"] - radius - 7)
        current_radius = zone["radius"] - radius - 3
        current_center = zone["center"]
        angle = math.atan2(center[1] - y, center[0] - x)
        best = None

        def clear(start, dest):
            return (math.dist(dest, current_center) < current_radius
                    and self.nav._ground_segment(*start, *dest, *dimensions))

        def find_leg(start, options):
            nonlocal best
            for heading in options:
                for distance in (8., 12., 18.):
                    target = (start[0] + distance * math.cos(heading),
                              start[1] + distance * math.sin(heading))
                    remainder = math.dist(target, center)
                    if remainder > safe_radius or not clear(start, target):
                        continue
                    travel = math.dist((x, y), start) + distance
                    cost = travel + .5 * remainder
                    points = [target] if start == (x, y) else [start, target]
                    if best is None or cost < best[0]:
                        best = (cost, points)

        headings = [angle + turn * math.tau / 24 for turn in range(-6, 7)]
        find_leg((x, y), headings)
        if best is None and zone["radius"] - math.dist((x, y), current_center) >= 10:
            for heading in (angle + turn * math.tau / 16 for turn in range(16)):
                first = (x + 4.5 * math.cos(heading), y + 4.5 * math.sin(heading))
                if clear((x, y), first):
                    find_leg(first, headings)
        if best is None:
            return None
        points = best[1]
        self.zone_anchor_fallback = (center, points)
        px, py = points[0]
        scale = 1 / math.dist((x, y), (px, py))
        return [(px - x) * scale, (py - y) * scale]

    def escape_boost_grace(self, obs, plan, action, jet):
        """Carry a grounded sprint past line dodge while the rifle is firing."""
        me = obs["self"]
        tick = obs["tick"]
        match = self.survival.rules.get("match", {})
        stride = match.get("decide_every", 2)
        duration = self.loadout.step * stride
        if (self.ground_line_boost_tick != tick - stride or obs["t"] - self.last_escape_grace < .7
                or jet or action["boost"] or action["jump"] or plan["dodge"] or plan["mode"] != "evade"
                or plan["enemy_pressure"] <= .66 or not me.get("grounded") or not me.get("in_zone")
                or not self.nav.loaded or any(w and w.get("charge", 0) > 0 for w in me.get("weapons", ()))):
            return False
        # Keep enough rounds for follow-up pressure after this sprint.
        gun = next((weapon for trigger, weapon in zip(action.get("fire", ()), me.get("weapons", ()))
                    if trigger and weapon and weapon.get("kind") == "gun" and weapon.get("ammo", 0) > 1), None)
        if gun is None:
            return False
        target_id = self.loadout.last_decision.get("target_id")
        target = next((ent for ent in obs.get("mechs", ())
                       if ent.get("kind") == "mech" and ent.get("id") == target_id), None)
        if target is None:
            return False
        stats = self.survival.rules.get("mech", {}) | (me.get("stats") or {})
        radius = stats.get("radius", 2.5)
        gun_stats = self.loadout.weapons.get("gun", {}) | gun.get("stats", {})
        reach = duration * gun_stats.get("speed", 252) + radius + .5 + self.loadout.dimensions(target)[0]
        # Leave the native muzzle position in place for close, immediate hits.
        if math.dist(me["pos"][:2], target["pos"][:2]) <= reach:
            return False
        reserve = .36 * me.get("max_energy", 100)
        cost = duration * stats.get("boost_drain", 17)
        if me["energy"] < reserve - 2 * cost - 1e-6 or me["energy"] > reserve:
            return False
        x, y, z = me["pos"]
        ux, uy = action["move"]
        vx, vy = me["vel"][:2]
        speed = math.hypot(vx, vy)
        magnitude = math.hypot(ux, uy)
        if (speed < 1.3 * stats.get("walk_speed", 11.7) or magnitude < .9
                or vx * ux + vy * uy < .95 * speed * magnitude
                or math.dist((x, y), plan["goal"][:2]) < 5):
            return False
        advance = duration * stats.get("boost_speed", 19.5) + .25
        end = (x + advance * ux / magnitude, y + advance * uy / magnitude)
        zone = obs["zone"]
        if math.dist(end, zone["center"]) + radius > zone["radius"]:
            return False
        return (abs(self.nav.surface(*end) - z) < .25
                and self.nav._ground_segment(x, y, *end, *self.nav._dimensions(radius)))

    def quiet_outbound_hold(self, obs, plan, action):
        me, zone = obs["self"], obs.get("zone") or {}
        t = obs["t"]
        phase = zone.get("shrink_start", t)
        if (plan["mode"] != "zone" or plan["dodge"] or not me.get("grounded") or not me.get("in_zone")
                or phase - t < 10 or zone.get("dps", 0) < 70 or action.get("jump") or action.get("boost")
                or obs.get("mechs") or obs.get("projectiles") or any(action.get("fire", ()))
                or any(w and w.get("charge", 0) for w in me.get("weapons", ()))):
            self.outbound_hold_until = -math.inf
            return False
        if t < self.outbound_hold_until:
            return True
        if self.outbound_hold_phase == phase or not self.nav.loaded or len(plan["goal"]) != 2:
            return False
        xy, vel = me["pos"][:2], me["vel"][:2]
        center, radius = zone["center"], zone["radius"]
        stats = me.get("stats", {})
        speed = stats.get("walk_speed", 11.7)
        accel = stats.get("ground_accel", 58.5)
        motion = math.hypot(*vel)
        if motion < .6 * speed or accel <= 0:
            return False
        ground = self.nav._dimensions(stats.get("radius", 2.5))
        ux, uy = action["move"]
        native = xy[0] + speed * ux, xy[1] + speed * uy
        braking = tuple(x + v * motion / (2 * accel) for x, v in zip(xy, vel))
        if (math.dist(native, center) < radius or math.dist(braking, center) >= radius - 1
                or math.dist(plan["goal"], center) >= math.dist(xy, center) - 20
                or self.nav._ground_segment(*xy, *plan["goal"], *ground)
                or not self.nav._ground_segment(*xy, *native, *ground)):
            return False
        self.outbound_hold_phase = phase
        self.outbound_hold_until = t + 1.2
        return True

    def quiet_reachable_pickup(self, obs, plan, action, jet):
        me = obs["self"]
        target_id = plan["target_id"]
        first_cube = me.get("cubes", 0) == 0
        was_resting = self.first_cube_rest
        self.first_cube_rest = (first_cube and me.get("grounded") and not any(action["move"])
                                and math.hypot(*me["vel"][:2]) <= 1.)
        new_target = False
        if first_cube and plan["mode"] == "loot" and target_id is not None:
            new_target = target_id not in self.first_loot_targets
            self.first_loot_targets.add(target_id)
        if (not self.nav.loaded or plan["mode"] != "loot" or plan["dodge"]
                or plan["zone_urgency"] > .25 or plan["enemy_pressure"] > .1
                or not me.get("grounded") or not me.get("in_zone") or jet or action["jump"] or action["boost"]
                or "take" in action or any(action["move"])
                or any(action.get("fire", ())) or obs.get("projectiles")
                or obs.get("beams") or self.loadout.last_decision.get("target_id") is not None
                or any(w and w.get("charge", 0) for w in me.get("weapons", ()))):
            return None
        pickups = obs.get("pickups", ()) if None in me.get("weapons", ()) else ()
        item = next((item for item in pickups if item["id"] == target_id), None)
        cube = item is None
        rules = self.survival.rules
        if cube:
            if not (new_target and was_resting and self.first_cube_rest):
                return None
            item = next((item for item in obs.get("cubes", ()) if item["id"] == target_id), None)
        if item is None:
            return None
        reach = rules.get("cubes" if cube else "loot", {}).get("pickup_radius", 3.5 if cube else 4.)
        x, y, z = me["pos"]
        px, py, pz = item["pos"]
        distance = math.hypot(px - x, py - y)
        if not reach + .20 <= distance <= reach + 2. or abs(z - pz) > 3.5:
            return None
        stats = me.get("stats", {})
        radius = stats.get("radius", 2.5)
        if cube:
            growth = rules.get("cubes", {}).get("size_per_cube", .05)
            mech = rules.get("mech", {})
            base_radius, base_height = mech.get("radius", 2.5), mech.get("height", 9.)
            radius = max(radius, base_radius)
        dims = self.nav._dimensions(radius)
        if self.nav._ground_segment(x, y, px, py, *dims):
            return None
        heading = math.atan2(y - py, x - px)
        zone = obs["zone"]
        turns = (0, 20, -20, 40, -40, 60, -60) if cube else (0, 20, -20, 40, -40)
        for degrees in turns:
            angle = heading + math.radians(degrees)
            inside_reach = reach - (.32 if cube else .45)
            qx, qy = px + inside_reach * math.cos(angle), py + inside_reach * math.sin(angle)
            distance = math.hypot(qx - x, qy - y)
            qz = self.nav.surface(qx, qy)
            if (distance > 2.55 or abs(qz - z) > .65 or abs(qz - pz) > 3.5
                    or math.dist((qx, qy), zone["center"]) + radius + 6 >= zone["radius"]
                    or not self.nav._ground_segment(x, y, qx, qy, *dims)):
                continue
            if cube:
                vx, vy = me["vel"][:2]
                ux, uy = (qx - x) / distance, (qy - y) / distance
                if abs(vx * uy - vy * ux) > .45 or vx * ux + vy * uy < -.25:
                    continue
                # Reserve room for nearby cubes collected before the bot can
                # leave the corridor with its larger hull.
                extras = sum(math.dist((qx, qy), other["pos"][:2]) <= reach + distance
                             and abs(qz - other["pos"][2]) <= 4.65 for other in obs.get("cubes", ()))
                scale = 1 + growth * extras
                if not self.nav.raw_hull_corridor_clear((x, y, z), (qx, qy), max(radius, base_radius * scale),
                                                        max(stats.get("height", 9.), base_height * scale)):
                    continue
            scale = 1 / max(2., distance)
            return [(qx - x) * scale, (qy - y) * scale]
        return None

    def quiet_follow_collected_cube(self, obs, plan, action, jet):
        me = obs["self"]
        rules = self.survival.rules
        cubes = rules.get("cubes", {})
        count = me.get("cubes", 0)
        if (not self.nav.loaded or plan["mode"] != "loot" or plan["dodge"]
                or plan["zone_urgency"] > .25 or plan["enemy_pressure"] > .1
                or not 0 < count < cubes.get("stat_cap", 10)
                or not me.get("grounded") or not me.get("in_zone") or jet or action["jump"] or action["boost"]
                or any(action["move"]) or any(action.get("fire", ())) or "take" in action
                or obs.get("projectiles") or obs.get("beams") or self.loadout.last_decision.get("intent") == "engage"
                or any(w and w.get("charge", 0) for w in me.get("weapons", ()))
                or not any(event.get("type") == "pickup" and event.get("cubes") == count
                           for event in obs.get("events", ()))):
            return None
        items = obs.get("cubes", ())
        target = next((item for item in items if item["id"] == plan["target_id"]), None)
        if target is None:
            return None
        group = [item for item in items if math.dist(item["pos"], target["pos"]) <= 2.]
        if len(group) < 2:
            return None

        stats = rules.get("mech", {}) | me.get("stats", {})
        walk = stats.get("walk_speed", 11.7)
        vx, vy, _ = me["vel"]
        speed = math.hypot(vx, vy)
        if not .35 * walk <= speed <= .65 * walk:
            return None
        step = self.loadout.step
        stride = rules.get("match", {}).get("decide_every", 2)
        if not 1 <= stride <= 3:
            return None
        deceleration = max(1., stats.get("ground_accel", 58.5)) * step
        x, y, z = me["pos"]
        unit = vx / speed, vy / speed
        carry = step * speed * stride
        braking = step * sum(max(0., speed - deceleration * i) for i in range(1, stride + 1))
        reach = cubes.get("pickup_radius", 3.5)

        def endpoint(distance):
            return x + unit[0] * distance, y + unit[1] * distance

        extended, native = endpoint(carry), endpoint(braking)
        extra = {item["id"] for item in group if abs(item["pos"][2] - z) <= 3.5
                 and math.dist(item["pos"][:2], extended) <= reach - .01
                 and math.dist(item["pos"][:2], native) > reach}
        if target["id"] not in extra or len(extra) < 2:
            return None

        reserve = carry + step * sum(max(0., speed - deceleration * i) for i in (1, 2, 3))
        offer = obs.get("offer") or {}
        choices = offer.get("choices", ())
        picks = {action.get("pick")}
        if choices and offer.get("expires", math.inf) <= obs["t"] + stride * step:
            picks.add(0)
        faster_walk = walk
        for selected in picks:
            if selected is None or not 0 <= selected < len(choices):
                continue
            effects = self.loadout.upgrades.get(choices[selected]["id"], {}).get("effects", ())
            offered_walk = walk
            for effect in effects:
                if effect.get("path") == "mech.walk_speed":
                    offered_walk = offered_walk * effect.get("mul", 1) + effect.get("add", 0)
            faster_walk = max(faster_walk, offered_walk)
        if faster_walk > walk:
            # An upgrade can apply before the held movement command ends.
            faster_speed = speed * faster_walk / walk
            brake_steps = math.ceil(faster_speed / deceleration)
            reserve = step * (faster_speed * stride + sum(
                max(0., faster_speed - deceleration * i) for i in range(1, brake_steps)
            ))
        end = endpoint(reserve)
        possible = sum(abs(item["pos"][2] - z) < 4.3
                       and math.dist(item["pos"][:2], end) <= reach + reserve for item in items)
        base = rules.get("mech", {})
        scale = 1 + cubes.get("size_per_cube", .05) * (count + possible)
        radius = max(stats.get("radius", 2.5), base.get("radius", 2.5) * scale)
        height = max(stats.get("height", 9.), base.get("height", 9.) * scale)
        zone = obs["zone"]
        if (math.dist(end, zone["center"]) + radius + 6 >= zone["radius"]
                or any(abs(self.nav.surface(*endpoint(reserve * i / 4)) - z) > .025 for i in range(1, 5))
                or not self.nav._ground_segment(x, y, *end, *self.nav._dimensions(radius))
                or not self.nav.raw_hull_corridor_clear((x, y, z), end, radius, height)):
            return None
        return [vx / walk, vy / walk]

    @staticmethod
    def cube_taper_drive(pos, endpoint, walk):
        dx, dy = endpoint[0] - pos[0], endpoint[1] - pos[1]
        scale = min(.26 / max(.001, math.hypot(dx, dy)), 1 / (.18 * walk))
        return dx * scale, dy * scale

    def boost_cube_arrival(self, obs, plan, action, jet):
        """Sprint for one quiet command if it crosses the chosen cube's pickup radius."""
        me = obs["self"]
        rules = self.survival.rules
        if (plan["mode"] != "loot" or plan["dodge"] or plan["enemy_pressure"] > .05
                or plan["zone_urgency"] > .10 or jet or not self.nav.loaded
                or not me.get("grounded") or not me.get("in_zone")
                or action["boost"] or action["jump"] or any(action.get("fire", ()))
                or "take" in action or "pick" in action or obs.get("offer")
                or obs.get("projectiles") or obs.get("beams") or obs.get("sounds")
                or self.loadout.last_decision.get("target_id") is not None
                or any(event.get("type") == "damaged" for event in obs.get("events", ()))
                or any(weapon and weapon.get("charge", 0) for weapon in me.get("weapons", ()))):
            return False
        pos = me["pos"]
        npc_range = rules.get("npc", {}).get("aggro_range", 45.)
        if any(ent.get("kind") == "mech" or (ent.get("kind") == "npc"
               and math.dist(pos[:2], ent["pos"][:2]) < npc_range)
               for ent in obs.get("mechs", ())):
            return False
        cube = next((item["pos"] for item in obs.get("cubes", ()) if item["id"] == plan["target_id"]), None)
        stats = self.loadout.mech | (me.get("stats") or {})
        dt = self.loadout.step
        stride = rules.get("match", {}).get("decide_every", 2)
        cost = dt * stride * stats.get("boost_drain", 17.)
        if (cube is None or abs(cube[2] - pos[2]) > .45 or stride != 2 or not math.isclose(dt, .05)
                or me.get("energy", 0.) - cost < .90 * me.get("max_energy", 100.)):
            return False
        walk, sprint = stats.get("walk_speed", 11.7), stats.get("boost_speed", 19.5)
        reach = rules.get("cubes", {}).get("pickup_radius", 3.5)
        distance = math.dist(pos[:2], cube[:2])
        ux, uy = action["move"]
        velocity = me["vel"][:2]
        if (not reach + walk * dt * stride <= distance <= reach + sprint * dt * stride
                or math.hypot(ux, uy) < .99
                or math.dist((ux, uy), tuple((point - p) / distance for point, p in zip(cube[:2], pos))) > .10
                or math.dist(velocity, (ux * walk, uy * walk)) > .8):
            return False

        def path(speeds):
            x, y = pos[:2]
            vx, vy = velocity
            acceleration = stats.get("ground_accel", 58.5) * dt
            for speed in speeds:
                dx, dy = ux * speed - vx, uy * speed - vy
                scale = min(1., acceleration / max(.001, math.hypot(dx, dy)))
                vx += dx * scale
                vy += dy * scale
                x += vx * dt
                y += vy * dt
                yield x, y

        normal = list(path((walk, walk)))[-1]
        boosted = list(path((sprint, sprint, walk, walk)))
        if math.dist(normal, cube[:2]) <= reach + .05 or math.dist(boosted[1], cube[:2]) > reach - .08:
            return False
        cubes = rules.get("cubes", {})
        potential = sum(any(math.dist(item["pos"][:2], step) <= reach + .3 for step in boosted)
                        and abs(item["pos"][2] - pos[2]) <= 4.25 for item in obs.get("cubes", ()))
        if potential != 1:
            return False
        grown_count = me.get("cubes", 0) + 1
        if grown_count in cubes.get("upgrade_thresholds", (1, 3, 6, 10)):
            return False
        growth = 1. + grown_count * cubes.get("size_per_cube", .05)
        radius = max(stats.get("radius", 2.5), self.loadout.mech.get("radius", 2.5) * growth)
        height = max(stats.get("height", 9.), self.loadout.mech.get("height", 9.) * growth)
        zone = obs["zone"]
        if (math.dist(boosted[-1], zone["center"]) + radius + 5. >= zone["radius"]
                or not self.nav.raw_hull_corridor_clear(pos, boosted[-1], radius, height)):
            return False
        feet = pos[2]
        start = pos[:2]
        clearance, headroom = self.nav._dimensions(radius)
        for step in boosted:
            floor = self.nav.surface(*step)
            if (not feet - .03 <= floor <= feet + .18
                    or not self.nav._ground_segment(*start, *step, clearance, headroom)):
                return False
            feet = max(feet, floor)
            start = step
        return True

    def quiet_cube_taper(self, obs, plan, action, jet):
        me = obs["self"]
        now = obs["t"]
        rules = self.survival.rules
        cubes = rules.get("cubes", {})
        cap = cubes.get("stat_cap", 10)
        count = me.get("cubes", 0)
        prior = self.cube_taper
        self.cube_taper = None
        if (plan["mode"] not in ("loot", "hold", "zone") or plan["dodge"] or plan["enemy_pressure"] > .05
                or plan["zone_urgency"] > .1 or jet or not self.nav.loaded or action["jump"] or action["boost"]
                or not me.get("grounded") or not me.get("in_zone") or not 0 < count <= cap
                or me["hp"] > .65 * me["max_hp"] or "pick" in action or "take" in action
                or any(action.get("fire", ())) or self.loadout.last_decision.get("target_id") is not None
                or obs.get("projectiles") or obs.get("beams")
                or any(w and w.get("charge", 0) for w in me.get("weapons", ()))):
            return None
        pos = me["pos"]
        target = plan["target_id"]
        pack = obs.get("cubes", ())
        base = self.loadout.mech
        stats = base | (me.get("stats") or {})
        walk = stats.get("walk_speed", 11.7)
        reach = cubes.get("pickup_radius", 3.5)
        growth = cubes.get("size_per_cube", .05)
        stride = self.loadout.config.get("match", {}).get("decide_every", 2)
        if stride != 2 or not math.isclose(self.loadout.step, .05, abs_tol=1e-8):
            return None

        endpoint = None
        if prior and prior[3] is not None and now - prior[1] <= 1.1:
            target_id, started, previous_count, endpoint = prior
            if count == previous_count and target != target_id:
                return None
            if count > previous_count:
                # Finish the already proved low-speed stop after auto-collection.
                if math.dist(pos[:2], endpoint) > .16 or math.hypot(*me["vel"][:2]) > 1.5:
                    return None
                target_id = None
            target = target_id
        else:
            item = next((item["pos"] for item in pack if item["id"] == target), None)
            if (plan["mode"] != "loot" or count >= cap or item is None or any(action["move"])
                    or math.hypot(*me["vel"][:2]) > .35 or abs(item[2] - pos[2]) > .75):
                return None
            distance = math.dist(pos[:2], item[:2])
            if not reach + .2 <= distance <= reach + 1.35:
                return None
            if prior is None or prior[0] != target or prior[2] != count:
                self.cube_taper = target, now, count, None
                return None
            if now - prior[1] < 1.8 - 1e-8:
                self.cube_taper = prior
                return None
            pull = (reach - .05) / distance
            endpoint = tuple(item[i] + pull * (pos[i] - item[i]) for i in range(2))
            previous_count, started = count, now
        if not self.cube_taper_path_clear(obs, endpoint, target, stats, base, count, cap, growth, reach):
            return None
        self.cube_taper = (target, started, previous_count, endpoint)
        return self.cube_taper_drive(pos, endpoint, walk)

    def cube_taper_path_clear(self, obs, endpoint, target, stats, base, count, cap, growth, reach):
        pos = list(obs["self"]["pos"])
        vx, vy = obs["self"]["vel"][:2]
        walk = stats.get("walk_speed", 11.7)
        dt = self.loadout.step
        acceleration = dt * stats.get("ground_accel", 58.5)
        visible = {item["id"]: item["pos"] for item in obs.get("cubes", ())}
        landing_drop = min(.05, stats.get("gravity", 22.) * dt * dt)
        definite = set()
        possible = set()
        zone = obs["zone"]
        for step in range(22):
            if step % 2 == 0:
                mx, my = self.cube_taper_drive(pos, endpoint, walk)
            dx, dy = walk * mx - vx, walk * my - vy
            rate = min(1., acceleration / max(.001, math.hypot(dx, dy)))
            vx, vy = vx + rate * dx, vy + rate * dy
            xy = pos[0] + dt * vx, pos[1] + dt * vy
            floor = self.nav.surface(*xy)
            if (floor - pos[2] > .05 or pos[2] - floor > landing_drop
                    or abs(floor - self.nav.ground(*xy)) > .08):
                return False
            feet = max(floor, pos[2]) if pos[2] <= floor + .03 else floor
            for ident, item in visible.items():
                radial = math.dist(xy, item[:2])
                if abs(feet - item[2]) <= 4.08 and radial <= reach + .08:
                    possible.add(ident)
                if abs(feet - item[2]) <= 3.97 and radial <= reach - .015:
                    definite.add(ident)
            if count + len(possible) > cap:
                return False
            scale = 1 + (count + len(possible)) * growth
            radius = max(stats.get("radius", 0), base.get("radius", 2.5) * scale)
            height = max(stats.get("height", 0), base.get("height", 9.) * scale)
            if (any(math.dist(xy, zone[center]) + radius + 6 >= zone[ring]
                    for center, ring in (("center", "radius"), ("next_center", "next_radius")))
                    or not self.nav.raw_hull_corridor_clear(pos, xy, radius, height)):
                return False
            pos = [*xy, feet]
            if (math.hypot(vx, vy) <= .12 and math.dist(xy, endpoint) <= .03
                    and (target is None or target in definite)):
                return True
        return False

    def quiet_loot_landing_hull(self, obs, plan):
        me = obs["self"]
        target = plan["target_id"]
        tick = obs["tick"]
        if (plan["mode"] != "loot" or target is None or plan["dodge"] or plan["enemy_pressure"] > .1
                or plan["zone_urgency"] > .1 or not me.get("in_zone")
                or obs.get("projectiles") or obs.get("beams")):
            self.loot_descent = None
            return None
        if not me.get("grounded"):
            self.loot_descent = (target, tick) if me["vel"][2] < -3 else None
            return None
        descent = self.loot_descent
        stride = self.loadout.config.get("match", {}).get("decide_every", 2)
        if descent is None or descent[0] != target or not 0 < tick - descent[1] <= 2 * stride:
            self.loot_descent = None
            return None
        base = self.loadout.mech
        stats = me.get("stats", {})
        scale = 1 + self.loadout.config.get("cubes", {}).get("size_per_cube", .05) * me.get("cubes", 0)
        return (max(stats.get("radius", 0), base.get("radius", 2.5) * scale),
                max(stats.get("height", 0), base.get("height", 9) * scale))

    def reload_after_wall_round(self, obs, plan, action):
        confirmation = self.postkill_refill_confirmation
        self.postkill_refill_confirmation = None
        if "take" in action or "pick" in action:
            self.wall_round_refill = None
            return
        if confirmation is None:
            pending = self.wall_round_refill
            if pending is None:
                return
            slot, reloads, was_reloading = pending
        else:
            expected_tick, slot = confirmation
            if obs["tick"] != expected_tick:
                return
        me = obs["self"]
        weapons = me["weapons"]
        rifle = weapons[slot]
        if not rifle or rifle.get("kind") != "gun":
            self.wall_round_refill = None
            return
        reloading = bool(rifle.get("reload"))
        if confirmation is None:
            reloads += reloading and not was_reloading
            if reloads > 1:
                self.wall_round_refill = None
                return
            self.wall_round_refill = slot, reloads, reloading
            match_size = self.loadout.config.get("match", {}).get("mechs", 16)
            if not any(
                event.get("type") == "kill" and type(event.get("target")) is int and 0 <= event["target"] < match_size
                for event in obs.get("events", ())
            ):
                return
            self.wall_round_refill = None
        if (reloading
                or plan["mode"] not in ("loot", "hold") or plan["dodge"] or plan["zone_urgency"] > .10
                or not me.get("grounded") or not me.get("in_zone")
                or self.loadout.last_decision.get("intent") != "scan" or action.get("reload")
                or action["jump"] or action["boost"] or any(action.get("fire", ()))
                or obs.get("projectiles") or obs.get("beams") or obs.get("sounds")
                or any(event.get("type") == "damaged" for event in obs.get("events", ()))
                or any(entity.get("kind") == "mech" for entity in obs.get("mechs", ()))
                or any(weapon and weapon.get("charge", 0) for weapon in weapons)):
            return
        stats = self.loadout.weapons.get("gun", {}) | rifle.get("stats", {})
        magazine = stats.get("mag", 12)
        ammo = rifle.get("ammo", magazine)
        if ammo < magazine and ammo - 1 < .80 * magazine <= ammo:
            if confirmation is None:
                stride = self.loadout.config.get("match", {}).get("decide_every", 2)
                self.postkill_refill_confirmation = obs["tick"] + stride, slot
            else:
                action["reload"] = True

    def confirm_loot_scan_gap(self, me, stride, edge, witness):
        """Continue only when the observed hull and torso followed the held command."""
        old_pos, old_velocity, old_yaw, opening = witness
        seconds = 2 * stride * self.loadout.step
        x, y, z = me["pos"]
        expected = tuple(p + seconds * v for p, v in zip(old_pos[:2], old_velocity))
        if (math.dist((x, y), expected) > .30
                or math.dist(me["vel"][:2], old_velocity) > 1.25
                or abs(self.nav.ground(x, y) - z) > .15):
            return False
        stats = me.get("stats", {})
        yaw_speed = stats.get("turn_rate", self.loadout.mech.get("turn_rate", 4.))
        desired = math.atan2(edge[1] - old_pos[1], edge[0] - old_pos[0])
        turn = math.remainder(desired - old_yaw, math.tau)
        limit = seconds * yaw_speed
        expected_yaw = old_yaw + max(-limit, min(turn, limit))
        if abs(math.remainder(me["aim"][0] - expected_yaw, math.tau)) > .08:
            return False
        eye_height = stats.get("eye_height", self.loadout.mech.get("eye_height", 8.))
        return (not self.nav.short_segment_hits_raw_solid((x, y, z + eye_height), edge)
                and self.nav.raw_hull_corridor_clear(
                    (x, y, z), opening, stats.get("radius", self.nav.body_radius),
                    stats.get("height", self.nav.body_height)))

    def scan_loot_cover_edge(self, obs, plan, action):
        now = obs["t"]
        prior_point = self.loot_scan_point
        self.loot_scan_point = None
        events = obs.get("events", ())
        match_size = self.loadout.config.get("match", {}).get("mechs", 16)
        if any(event.get("type") == "kill" and type(event.get("target")) is int
               and 0 <= event["target"] < match_size for event in events):
            self.loot_scan_until = now + 1.
            prior_point = None
        elif prior_point:
            self.loot_scan_until = -math.inf
        if ((prior_point is None and now > self.loot_scan_until) or not self.nav.loaded or plan["mode"] != "loot"
                or plan["dodge"] or plan["zone_urgency"] > .1
                or self.loadout.last_decision.get("intent") != "scan"
                or action["jump"] or action["boost"] or action.get("reload")
                or any(action.get("fire", ())) or "take" in action or "pick" in action
                or obs.get("projectiles") or obs.get("beams") or obs.get("sounds")
                or any(event.get("type") == "damaged" for event in events)
                or any(entity.get("kind") == "mech" for entity in obs.get("mechs", ()))):
            return
        me = obs["self"]
        vx, vy, _ = me["vel"]
        dx, dy = action["move"]
        weapons = me.get("weapons", ())
        if (not me.get("grounded") or not me.get("in_zone")
                or not any(w and w.get("kind") == "gun" and w.get("ammo", 0) >= 2
                           and not w.get("reload") for w in weapons)
                or any(w and w.get("charge", 0) for w in weapons)
                or math.hypot(dx, dy) < .8 or math.hypot(vx, vy) < 6):
            return
        heading = math.atan2(dy, dx)
        if abs(math.remainder(heading - math.atan2(vy, vx), math.tau)) > .2:
            return
        x, y, z = me["pos"]
        tick = obs["tick"]
        stride = self.loadout.config.get("match", {}).get("decide_every", 2)
        if prior_point:
            expected_tick, expires, item_id, edge, witness = prior_point
            if now > expires or plan["target_id"] != item_id:
                return
            if tick != expected_tick:
                if (tick != expected_tick + stride or witness is None
                        or not self.confirm_loot_scan_gap(me, stride, edge, witness)):
                    return
                witness = None
            bearing = math.atan2(edge[1] - y, edge[0] - x)
            flank = abs(math.remainder(bearing - heading, math.tau))
            if not .28 <= flank <= .85:
                return
            action["aim"] = [bearing, action["aim"][1]]
            if witness is not None:
                witness = tuple(me["pos"]), (vx, vy), me["aim"][0], witness[3]
            self.loot_scan_point = tick + stride, expires, item_id, edge, witness
            return
        sweep = math.remainder(action["aim"][0] - heading, math.tau)
        if not .6 <= abs(sweep) <= 1.65:
            return
        side = math.copysign(1., sweep)
        bearing = heading + side * math.pi / 6
        shoulder = heading + side * math.radians(50)
        stats = me.get("stats", {})
        eye_height = stats.get("eye_height", self.loadout.mech.get("eye_height", 8.))
        eye = x, y, z + eye_height
        fx, fy = x + vx * .35, y + vy * .35
        ahead = fx, fy, self.nav.ground(fx, fy) + eye_height
        edge = ahead[0] + 25 * math.cos(bearing), ahead[1] + 25 * math.sin(bearing), ahead[2]
        covered = eye[0] + 25 * math.cos(shoulder), eye[1] + 25 * math.sin(shoulder), eye[2]
        if (self.nav.short_segment_hits_raw_solid(eye, covered)
                and not self.nav.short_segment_hits_raw_solid(ahead, edge)
                and self.nav.short_segment_hits_raw_solid(eye, edge)
                and self.nav.raw_hull_corridor_clear((x, y, z), (fx, fy),
                    stats.get("radius", self.nav.body_radius), stats.get("height", self.nav.body_height))):
            action["aim"] = [math.atan2(edge[1] - y, edge[0] - x), action["aim"][1]]
            witness = tuple(me["pos"]), (vx, vy), me["aim"][0], (fx, fy)
            self.loot_scan_point = tick + stride, now + .35, plan["target_id"], edge, witness

    def brake_toward_sheltered_pursuer(self, obs, plan, action, settled):
        """Keep the lateral shelter route without closing toward a rifle pursuer."""
        me = obs["self"]
        zone_rules = self.loadout.config.get("zone", {})
        phases = zone_rules.get("phases", ())
        if (not phases or obs["t"] >= phases[0].get("hold_s", 0.) or not me.get("in_zone")
                or obs["zone"]["radius"] != zone_rules.get("start_radius")
                or plan["mode"] != "shelter" or plan["dodge"] or plan["zone_urgency"] >= .15
                or not settled or not me.get("grounded") or not self.nav.loaded or action["boost"] or action["jump"]
                or any(action.get("fire", ())) or "take" in action or "pick" in action
                or obs.get("projectiles") or obs.get("beams")
                or any(w and w.get("charge", 0.) > 0. for w in me.get("weapons", ()))):
            return
        x, y, z = me["pos"]
        mx, my = action["move"]
        specs = self.loadout.mech | (me.get("stats") or {})
        walk = specs.get("walk_speed", 11.7)
        radius, height = specs.get("radius", 2.5), specs.get("height", 9.)
        muzzle = specs.get("muzzle_height", 7.)
        for rival in sorted(obs.get("mechs", ()), key=lambda ent: math.dist((x, y), ent["pos"][:2])):
            if rival.get("kind") != "mech" or "gun" not in rival.get("weapons", ()):
                continue
            rx, ry, rz = rival["pos"]
            separation = math.hypot(rx - x, ry - y)
            if not 2 * radius < separation < 3 * walk or abs(z - rz) > height:
                continue
            ux, uy = (rx - x) / separation, (ry - y) / separation
            rvx, rvy = rival.get("vel", (0., 0., 0.))[:2]
            inward = mx * ux + my * uy
            if inward <= .30 or rvx * ux + rvy * uy > -.65 * walk:
                continue
            body = (rx, ry, rz + .5 * self.loadout.dimensions(rival)[1])
            if not self.nav.short_segment_hits_raw_solid((x, y, z + muzzle), body):
                continue
            lateral = (mx - inward * ux, my - inward * uy)
            if self.covered_shelter_step(obs, lateral, body, specs):
                action["move"] = list(lateral)
            return

    def covered_shelter_step(self, obs, move, body, specs):
        me = obs["self"]
        trial = {"move": move, "boost": False, "jump": False}
        muzzle = specs.get("muzzle_height", 7.)
        origin = (*me["pos"][:2], me["pos"][2] + muzzle)
        bases = self.loadout.late_arc_bases(obs, origin, trial, specs)
        return bool(bases) and all(self.nav.short_segment_hits_raw_solid(point, body)
                                   for step in bases for point, _ in step)

    def keep_escape_before_weapon_reversal(self, obs, plan, action):
        """Preserve one retreat command when an empty rifle cannot cover a reversal."""
        previous, self.loot_escape_walk = self.loot_escape_walk, None
        me = obs["self"]
        arms = [w for w in me.get("weapons", ()) if w]
        zone = self.loadout.config.get("zone", {})
        phases = zone.get("phases", ())
        stride = self.loadout.config.get("match", {}).get("decide_every", 2)
        if (plan["mode"] not in ("evade", "loot") or plan["dodge"] or plan["zone_urgency"] >= .15
                or not phases or obs["t"] >= phases[0].get("hold_s", 0.)
                or not me.get("grounded") or not me.get("in_zone") or not self.nav.loaded
                or action["boost"] or action["jump"] or any(action.get("fire", ()))
                or "take" in action or "pick" in action or obs.get("projectiles") or obs.get("beams")
                or len(arms) != 1 or arms[0]["kind"] != "gun" or arms[0].get("ammo", 1) != 0
                or arms[0].get("reload", 0.) <= self.loadout.step * stride):
            return
        x, y, z = me["pos"]
        mx, my = action["move"]
        specs = self.loadout.mech | (me.get("stats") or {})
        walk = specs.get("walk_speed", 11.7)
        reach = self.loadout.weapons.get("gun", {}).get("range", 230.)
        origin = (x, y, z + specs.get("muzzle_height", 7.))
        bearings = {}
        for rival in obs.get("mechs", ()):
            if rival.get("kind") != "mech" or "gun" not in rival.get("weapons", ()) or not rival.get("aim"):
                continue
            rx, ry, rz = rival["pos"]
            separation = math.hypot(rx - x, ry - y)
            if not 0. < separation < reach:
                continue
            ux, uy = (rx - x) / separation, (ry - y) / separation
            vx, vy = rival["vel"][:2]
            facing = abs(math.remainder(math.atan2(-uy, -ux) - rival["aim"][0], math.tau))
            if vx * ux + vy * uy <= -.8 * walk and facing <= .25:
                bearings[rival["id"]] = (ux, uy, (rx, ry, rz + .5 * self.loadout.dimensions(rival)[1]))
        if plan["mode"] == "evade":
            if bearings:
                self.loot_escape_walk = obs["tick"], (mx, my), frozenset(bearings)
            return
        if previous is None or previous[0] != obs["tick"] - stride or not any(
            item["id"] == plan["target_id"] for item in obs.get("pickups", ())
        ):
            return
        old_x, old_y = previous[1]
        if old_x * mx + old_y * my > -.75:
            return
        for ident in bearings.keys() & previous[2]:
            ux, uy, body = bearings[ident]
            if (mx * ux + my * uy <= .5 or old_x * ux + old_y * uy >= -.5
                    or self.nav.short_segment_hits_raw_solid(origin, body)):
                continue
            trial = {"move": (old_x, old_y), "boost": False, "jump": False}
            if self.loadout.late_arc_bases(obs, origin, trial, specs) is not None:
                action["move"] = [old_x, old_y]
            return

    def act(self, obs):
        if self.trace:
            start = time.perf_counter()
        me = obs["self"]
        stride = self.loadout.config.get("match", {}).get("decide_every", 2)
        settled_shelter = self.shelter_grounded_tick == obs["tick"] - stride
        self.shelter_grounded_tick = obs["tick"] if me.get("grounded") else None
        pos = me["pos"]
        stats = me.get("stats", {})
        base = self.survival.decide(obs)
        plan = self.adaptation.decide(obs, base)
        goal = plan["goal"]
        landing_hull = self.quiet_loot_landing_hull(obs, plan)
        ux, uy, jet = self.nav.steer(pos, goal, obs["tick"], radius=stats.get("radius", 2.5),
                                      landing_hull=landing_hull)
        move = [ux, uy]
        distance = math.dist(pos[:2], goal[:2])
        if distance < 4 and not jet:
            # A full-speed approach can carry the mech through a small final circle.
            scale = distance / 4
            move = [ux * scale, uy * scale]
        if ux or uy:
            self.scan_yaw = math.atan2(uy, ux)
        yaw = plan["threat_yaw"] if plan["threat_yaw"] is not None else self.scan_yaw
        evade = plan["mode"] == "evade"
        grounded = me.get("grounded", True)
        energy = me.get("energy", 0)
        action = {
            "move": move,
            "jump": bool(jet and grounded and energy > 7),
            "boost": bool((plan["boost"] or (jet and not grounded)) and energy > 0),
        }
        release_move = action["move"] if not plan["dodge"] else None
        if (release_move and obs.get("projectiles")
                and any(w and w.get("charge", 0) > 0 for w in me.get("weapons", ()))):
            # Preserve the native charge when even a near miss would leave
            # little margin for the faster movement after release.
            radius = stats.get("radius", 2.5)
            if self.survival._dodge(obs, pos, radius + .5):
                release_move = None
        previous_swap = self.loadout.last_swap
        action.update(self.loadout.decide(obs, yaw, evade=evade,
                                          target_id=plan["target_id"], climbing=jet,
                                          line_dodge=plan["dodge"] == "line",
                                          steady=plan["mode"] == "hold" and grounded and not jet
                                          and math.hypot(*action["move"]) < .02,
                                          movement=release_move, motion_command=action))
        if plan["dodge"] == "line":
            brace = self.loadout.brace_for_incoming_round(obs, action)
            if brace is not None:
                action["aim"] = [brace, action["aim"][1]]
        fallback = self.zone_anchor_fallback
        zone = obs.get("zone") or {}
        settled = (fallback is not None and fallback[0] == tuple(zone.get("next_center", ()))
                   and len(fallback[1]) == 1 and math.dist(pos[:2], fallback[1][0]) < .6
                   and len(goal) == 2 and math.dist(pos[:2], zone["center"]) + 5 < zone["radius"])
        quiet_move = self.quiet_ground_anchor(obs, plan, action, jet, settled)
        if quiet_move is not None:
            action["move"] = quiet_move
            if settled:
                # The native tactical action is already computed. Suppress
                # recovery hops only at the reached quiet ground waypoint.
                action["jump"] = False
                self.nav.anchor = None
        escape_grace = self.escape_boost_grace(obs, plan, action, jet)
        if escape_grace:
            action["boost"] = True
            self.last_escape_grace = obs["t"]
        if self.quiet_outbound_hold(obs, plan, action):
            action["move"] = [0., 0.]
        pickup_move = self.quiet_reachable_pickup(obs, plan, action, jet)
        if pickup_move is not None:
            action["move"] = pickup_move
        cube_move = self.quiet_follow_collected_cube(obs, plan, action, jet)
        if cube_move is not None:
            action["move"] = cube_move
        cube_taper = self.quiet_cube_taper(obs, plan, action, jet)
        if cube_taper is not None:
            action["move"] = list(cube_taper)
        boosted_pickup = self.boost_cube_arrival(obs, plan, action, jet)
        if boosted_pickup:
            action["boost"] = True
        rifle_escape = self.survival.avoid_rifle_contact_this_command(obs, plan, action, jet)
        if rifle_escape is not None:
            action["move"] = list(rifle_escape)
        shell_steer = self.survival.airborne_mortar_step(obs, action, plan["dodge"])
        self.pending_ground_line_boost_tick = (
            obs["tick"] if grounded and plan["dodge"] == "line" and action["boost"] and not action["jump"]
            else None
        )
        reason = "reachable_zone_anchor" if quiet_move is not None else base["reason"]
        if shell_steer is not None:
            action["move"], shell_id = shell_steer
            reason = "airborne_mortar_clearance"
        ground_shell_move = self.survival.grounded_mortar_body_step(obs, action, plan)
        if ground_shell_move is not None:
            action["move"] = ground_shell_move
            reason = "grounded_mortar_body_clearance"
        self.loadout.defer_firing_mortar_swap(obs, action, previous_swap)
        unsafe_tube = self.loadout.mortar_self_blast_on_first_step(obs, action)
        if unsafe_tube is not None:
            action["fire"][unsafe_tube] = False
        self.reload_after_wall_round(obs, plan, action)
        self.scan_loot_cover_edge(obs, plan, action)
        self.brake_toward_sheltered_pursuer(obs, plan, action, settled_shelter)
        self.keep_escape_before_weapon_reversal(obs, plan, action)
        self.loadout.confirm_late_arc_command(action)
        obstructed_rifle = self.loadout.obstructed_rifle_launch(obs, action)
        self.pending_wall_round = None
        if obstructed_rifle is not None:
            action["fire"][obstructed_rifle] = False
            self.pending_wall_round = obs["tick"], obstructed_rifle
        self.last_decision = {
            "mode": plan["mode"], "reason": reason, "goal": list(goal),
            "base_goal": list(base["goal"]), "item_id": plan["target_id"],
            "zone_urgency": round(base["zone_urgency"], 3),
            "enemy_pressure": round(base["enemy_pressure"], 3), "dodge": base["dodge"],
            "jet_advised": jet, "combat": self.loadout.last_decision,
            "learning": self.adaptation.diagnostics(),
        }
        if obstructed_rifle is not None:
            self.last_decision["obstructed_rifle_slot"] = obstructed_rifle
        if rifle_escape is not None:
            self.last_decision["one_command_rifle_escape"] = True
        if shell_steer is not None:
            self.last_decision["airborne_shell"] = shell_id
        if escape_grace:
            self.last_decision["escape_boost_grace"] = True
        if boosted_pickup:
            self.last_decision["boosted_cube_arrival"] = True
        if self.trace:
            elapsed = (time.perf_counter() - start) * 1000
            mechfight.log(f'tick={obs["tick"]} hp={me["hp"]} mode={plan["mode"]} '
                          f'goal={goal} action={action} decision_ms={elapsed:.3f}')
        return action

    def sent(self, tick, action, on_time=True, applied=False):
        self.adaptation.sent(tick, action, on_time=on_time, applied=applied)
        if on_time and self.pending_wall_round and self.pending_wall_round[0] == tick:
            self.wall_round_refill = self.pending_wall_round[1], 0, False
        if on_time and self.pending_ground_line_boost_tick == tick and action.get("boost"):
            self.ground_line_boost_tick = tick


if __name__ == "__main__":
    mechfight.run(Bot)
