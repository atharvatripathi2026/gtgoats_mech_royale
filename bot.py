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
        self.storm_native_until = -1.
        self.match_rules = hello.get("config", {}).get("match", {})
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

    def storm_exit_walled(self, pos, direction, stats):
        x, y, z = pos
        dx, dy = direction
        body_height = stats.get("height", 9)
        # Sample up to three seconds of walking beyond the ingress approach.
        horizon = stats.get("walk_speed", 11.7) * 3
        consecutive_wall = 0
        for d in range(3, int(horizon) + 1, 3):
            px, py = x + d * dx, y + d * dy
            cell = self.nav._index(px, py)
            if any(top - z + self.nav.step_up >= body_height for _, top in self.nav.solids[cell]):
                consecutive_wall += 1
                if consecutive_wall == 2:
                    return True
            else:
                consecutive_wall = 0
        return False

    def storm_ingress(self, obs, plan, action, jet):
        me = obs["self"]
        zone = obs["zone"]
        if me.get("in_zone", True):
            self.storm_native_until = -1.
        if obs.get("t", 0) < self.storm_native_until:
            return None
        if (plan["mode"] != "zone" or obs.get("t", 0) < 175 or zone.get("dps", 0) < 55
                or me.get("in_zone", True) or not me.get("grounded") or not self.nav.loaded
                or jet or plan["dodge"] or any(action.get("fire", ()))
                or math.hypot(*action["move"]) < .9
                or any(w and w.get("charge", 0) > 0 for w in me.get("weapons", ()))):
            return None
        x, y, z = me["pos"]
        cx, cy = zone["center"]
        radius = zone["radius"]
        if not 0 < math.hypot(x - cx, y - cy) - radius < 20 or abs(z - self.nav.ground(x, y)) > 1:
            return None
        now = obs["t"]
        wait = max(0, zone.get("shrink_start", now) - now)
        duration = max(.001, zone.get("shrink_end", now) - now - wait)
        nx, ny = zone.get("next_center", (cx, cy))
        next_radius = zone.get("next_radius", radius)
        step = 1 / self.match_rules.get("tick_hz", 20)
        frames = self.match_rules.get("decide_every", 2)
        ticks = int(1.25 / step + 1e-8)
        stats = me.get("stats") or {}
        speed = stats.get("boost_speed", 19.5) if action["boost"] else stats.get("walk_speed", 11.7)
        acceleration = step * stats.get("ground_accel", 58.5)

        def crossings(direction):
            px, py = x, y
            vx, vy = me["vel"][:2]
            enter = None
            path = []
            for tick in range(1, ticks + 1):
                dvx, dvy = speed * direction[0] - vx, speed * direction[1] - vy
                scale = min(1., acceleration / max(.001, math.hypot(dvx, dvy)))
                vx, vy = vx + scale * dvx, vy + scale * dvy
                px, py = px + vx * step, py + vy * step
                elapsed = tick * step
                frac = max(0., min(1., (elapsed - wait) / duration))
                center = cx + frac * (nx - cx), cy + frac * (ny - cy)
                safe = radius + frac * (next_radius - radius) - .5
                if math.dist((px, py), center) <= safe:
                    if enter is None:
                        enter = elapsed
                else:
                    enter = None
                if tick % frames == 0 or tick == ticks:
                    path.append((px, py))
            return 1.5 if enter is None else enter, path

        native, _ = crossings(action["move"])
        if native < .65:
            return None
        clearance, height = self.nav._dimensions(stats.get("radius", 2.5))
        start_floor = self.nav.ground(x, y)
        bearing = math.atan2(cy - y, cx - x)
        best, next_move = native - .25, None
        for offset in (0, .45, -.45, .83, -.83, 1.1, -1.1):
            direction = math.cos(bearing + offset), math.sin(bearing + offset)
            eta, path = crossings(direction)
            if eta >= best or eta > 1.25:
                continue
            if (not self.nav._ground_segment(x, y, *path[-1], clearance, height)
                    or any(abs(self.nav.ground(*point) - start_floor) > 1
                           or not self.nav._ground_segment(*previous, *point, clearance, height)
                           for previous, point in zip(((x, y), *path), path))):
                continue
            best, next_move = eta, direction
        if (next_move is not None
                and sum(a * b for a, b in zip(next_move, action["move"])) < -.5
                and self.storm_exit_walled(me["pos"], next_move, stats)
                and not self.storm_exit_walled(me["pos"], action["move"], stats)):
            # Keep the native approach until it has had a chance to reach the
            # wall or initiate a climb, even if a cell moves past our horizon.
            self.storm_native_until = now + 1.25
            return None
        return next_move

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
                                          target_id=plan["target_id"], climbing=jet))
        reason = base["reason"]
        ingress = self.storm_ingress(obs, plan, action, jet)
        if ingress is not None:
            action["move"] = list(ingress)
            reason = "earlier_legal_storm_ingress"
        self.last_decision = {
            "mode": plan["mode"], "reason": reason, "goal": list(goal),
            "base_goal": list(base["goal"]), "item_id": plan["target_id"],
            "zone_urgency": round(base["zone_urgency"], 3),
            "enemy_pressure": round(base["enemy_pressure"], 3), "dodge": base["dodge"],
            "jet_advised": jet, "combat": self.loadout.last_decision,
            "learning": self.adaptation.diagnostics(),
        }
        if self.trace:
            elapsed = (time.perf_counter() - start) * 1000
            mechfight.log(f'tick={obs["tick"]} hp={me["hp"]} mode={plan["mode"]} '
                          f'goal={goal} action={action} decision_ms={elapsed:.3f}')
        return action

    def sent(self, tick, action, on_time=True, applied=False):
        self.adaptation.sent(tick, action, on_time=on_time, applied=applied)


if __name__ == "__main__":
    mechfight.run(Bot)
