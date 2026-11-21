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
        self.match_rules = hello["config"].get("match", {})
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

    def cross_shot_move(self, obs, plan, action, jet):
        me = obs["self"]
        if (plan["mode"] != "evade" or plan["dodge"] != "line" or plan["zone_urgency"] > .25
                or jet or not me.get("in_zone") or not me.get("grounded") or not self.nav.loaded
                or any(action.get("fire", ()))
                or any(w and w.get("charge", 0) > 0 for w in me.get("weapons", ()))):
            return None
        if sum(e.get("kind") == "mech" for e in obs.get("mechs", ())) < 2:
            return None
        x, y, z = me["pos"]
        step = 1 / self.match_rules.get("tick_hz", 20)
        ticks = self.match_rules.get("decide_every", 2)
        if ticks != 2 or abs(self.nav.surface(x, y) - z) > .15:
            return None
        stats = me.get("stats", {})
        if action["boost"] and me.get("energy", 0) <= step * 2 * max(
                stats.get("jet_drain", 15), stats.get("boost_drain", 11)):
            return None
        radius, height = stats.get("radius", 2.5), stats.get("height", 9)
        speed = stats.get("boost_speed", 19.5) if action["boost"] else stats.get("walk_speed", 11.7)
        accel = stats.get("ground_accel", 58.5) * step
        ux, uy = action["move"]
        if math.hypot(ux, uy) < .90:
            return None
        tracks = []
        for shot in obs.get("projectiles", ()):
            if shot.get("kind") != "gun" or math.dist(shot["pos"][:2], (x, y)) > 38:
                continue
            starts = [tuple(a + n * step * v for a, v in zip(shot["pos"], shot["vel"])) for n in range(3)]
            if not all(self.nav.line_clear(a, b) for a, b in zip(starts, starts[1:])):
                continue
            vx, vy = shot["vel"][:2]
            heading = math.atan2(vy, vx)
            if min(math.dist(p[:2], (x, y)) for p in starts) <= 17:
                tracks.append((shot.get("id"), starts, heading))
        if not any(abs((a[2] - b[2] + math.pi) % math.tau - math.pi) > .65
                   for index, a in enumerate(tracks) for b in tracks[:index]):
            return None

        def motion(dx, dy):
            px, py = x, y
            vx, vy = me["vel"][:2]
            path = []
            for _ in range(ticks):
                sx, sy = speed * dx - vx, speed * dy - vy
                gain = min(1., accel / max(.001, math.hypot(sx, sy)))
                vx, vy = vx + gain * sx, vy + gain * sy
                px, py = px + vx * step, py + vy * step
                path.append((px, py))
            return path

        def intersects(path, margin):
            collisions = set()
            for shot, points, _ in tracks:
                for i, (px, py) in enumerate(path):
                    ax, ay, az = points[i]
                    bx, by, bz = points[i+1]
                    dx, dy = bx - ax, by - ay
                    fraction = min(1., max(0., ((px - ax) * dx + (py - ay) * dy) / max(.01, dx*dx + dy*dy)))
                    if (math.hypot(ax + fraction * dx - px, ay + fraction * dy - py) <= radius + margin
                            and z + .12 <= az + fraction * (bz - az) <= z + height - .12):
                        collisions.add(shot)
            return collisions

        dims = self.nav._dimensions(radius)
        zone = obs["zone"]

        def flat_route(path):
            return (all(abs(self.nav.surface(*point) - z) <= .10
                        and math.dist(point, zone["center"]) + radius + 2 <= zone["radius"] for point in path)
                    and all(self.nav._ground_segment(*left, *right, *dims)
                            for left, right in zip(((x, y), *path), path)))

        native = motion(ux, uy)
        if not flat_route(native) or not intersects(native, -.07):
            return None
        for angle in (.54, -.54, .95, -.95):
            ca, sa = math.cos(angle), math.sin(angle)
            move = ux * ca - uy * sa, ux * sa + uy * ca
            path = motion(*move)
            if flat_route(path) and not intersects(path, .22):
                return list(move)
        return None

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
                                          walking_to_loot=(grounded and me.get("in_zone") and not jet
                                                           and plan["mode"] == "loot" and distance >= 4)))
        cross_step = self.cross_shot_move(obs, plan, action, jet)
        if cross_step is not None:
            action["move"] = cross_step
        self.last_decision = {
            "mode": plan["mode"], "reason": "cover_crossed_shots" if cross_step is not None else base["reason"], "goal": list(goal),
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
