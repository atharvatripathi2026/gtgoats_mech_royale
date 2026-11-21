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
        if not any(trigger and weapon and weapon.get("kind") == "gun" and weapon.get("ammo", 0) > 1
                   for trigger, weapon in zip(action.get("fire", ()), me.get("weapons", ()))):
            return False
        stats = self.survival.rules.get("mech", {}) | (me.get("stats") or {})
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
        radius = stats.get("radius", 2.5)
        zone = obs["zone"]
        if math.dist(end, zone["center"]) + radius > zone["radius"]:
            return False
        return (abs(self.nav.surface(*end) - z) < .25
                and self.nav._ground_segment(x, y, *end, *self.nav._dimensions(radius)))

    def act(self, obs):
        if self.trace:
            start = time.perf_counter()
        me = obs["self"]
        pos = me["pos"]
        stats = me.get("stats", {})
        base = self.survival.decide(obs)
        plan = self.adaptation.decide(obs, base)
        goal = plan["goal"]
        ux, uy, jet = self.nav.steer(pos, goal, obs["tick"], radius=stats.get("radius", 2.5))
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
        action.update(self.loadout.decide(obs, yaw, evade=evade,
                                          target_id=plan["target_id"], climbing=jet,
                                          line_dodge=plan["dodge"] == "line"))
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
        shell_steer = self.survival.airborne_mortar_step(obs, action, plan["dodge"])
        self.pending_ground_line_boost_tick = (
            obs["tick"] if grounded and plan["dodge"] == "line" and action["boost"] and not action["jump"]
            else None
        )
        reason = "reachable_zone_anchor" if quiet_move is not None else base["reason"]
        if shell_steer is not None:
            action["move"], shell_id = shell_steer
            reason = "airborne_mortar_clearance"
        self.last_decision = {
            "mode": plan["mode"], "reason": reason, "goal": list(goal),
            "base_goal": list(base["goal"]), "item_id": plan["target_id"],
            "zone_urgency": round(base["zone_urgency"], 3),
            "enemy_pressure": round(base["enemy_pressure"], 3), "dodge": base["dodge"],
            "jet_advised": jet, "combat": self.loadout.last_decision,
            "learning": self.adaptation.diagnostics(),
        }
        if shell_steer is not None:
            self.last_decision["airborne_shell"] = shell_id
        if escape_grace:
            self.last_decision["escape_boost_grace"] = True
        if self.trace:
            elapsed = (time.perf_counter() - start) * 1000
            mechfight.log(f'tick={obs["tick"]} hp={me["hp"]} mode={plan["mode"]} '
                          f'goal={goal} action={action} decision_ms={elapsed:.3f}')
        return action

    def sent(self, tick, action, on_time=True, applied=False):
        self.adaptation.sent(tick, action, on_time=on_time, applied=applied)
        if on_time and self.pending_ground_line_boost_tick == tick and action.get("boost"):
            self.ground_line_boost_tick = tick


if __name__ == "__main__":
    mechfight.run(Bot)
