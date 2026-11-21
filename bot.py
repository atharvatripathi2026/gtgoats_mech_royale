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

    def jet_obscures_return_fire(self, obs, plan, action, jet):
        """Drop tactical thrust once a low rival falls below reachable pitch."""
        me = obs["self"]
        if (not action["boost"] or me.get("grounded", True) or jet or plan["dodge"]
                or plan["mode"] not in ("evade", "zone") or len(plan["goal"]) != 2
                or obs.get("t", 0) < 170 or obs.get("zone", {}).get("next_radius", 560) > 110
                or obs.get("alive", 16) <= 2
                or not me.get("in_zone", True) or not self.nav.loaded
                or any(action.get("fire", ()))):
            return False
        stats = me.get("stats", {})
        if action["aim"][1] >= stats.get("min_pitch", -.7) - .06:
            return False
        if any(w and w.get("charge", 0) > 0 for w in me.get("weapons", ())):
            return False
        target = self.loadout.last_decision.get("target_id")
        opponent = next((e for e in obs.get("mechs", ()) if e.get("kind") == "mech"
                         and e.get("id") == target), None)
        if opponent is None:
            return False
        x, y, z = me["pos"]
        distance = math.dist((x, y), opponent["pos"][:2])
        if not 12 <= distance <= 115:
            return False

        # Brake only when the nearby surface stays well below the feet,
        # so lowering altitude is compatible with the existing horizontal plan.
        vx, vy = me.get("vel", (0, 0, 0))[:2]
        ux, uy = action["move"]
        walk = stats.get("walk_speed", 11.7)
        points = ((x, y), (x + .3 * vx, y + .3 * vy), (x + .45 * walk * ux, y + .45 * walk * uy))
        if not all(z - self.nav.surface(*point) >= 5 for point in points):
            return False
        gun = next((w for w in me.get("weapons", ()) if w and w.get("kind") == "gun"), None)
        if gun is None:
            return True
        # Releasing the jet helps only if the selected mech can enter a firing
        # angle before an extended descent leaves the bot exposed.
        horizon = 1.25
        if gun.get("reload", 0) > horizon or gun.get("cooldown", 0) > horizon:
            return False
        sx = x + horizon * (vx + walk * ux) * .5
        sy = y + horizon * (vy + walk * uy) * .5
        own_z = max(self.nav.surface(sx, sy), z + horizon * me["vel"][2]
                    - .5 * stats.get("gravity", 22) * horizon ** 2)
        muzzle = (sx, sy, own_z + stats.get("muzzle_height", 7))
        target = tuple(p + horizon * v for p, v in zip(opponent["pos"], opponent.get("vel", (0., 0., 0.))))
        _, height = self.loadout.dimensions(opponent)
        hull = (*target[:2], target[2] + .49 * height)
        weapon = self.loadout.weapons.get("gun", {}) | gun.get("stats", {})
        aim = self.loadout.solution("gun", muzzle, hull, opponent.get("vel", (0., 0., 0.)),
                                    weapon, stats.get("radius", 2.5) + .5, stats.get("max_pitch", 1.3))
        return bool(aim and stats.get("min_pitch", -.7) <= aim[1] <= stats.get("max_pitch", 1.3)
                    and self.nav.line_clear(muzzle, hull))

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
        if self.jet_obscures_return_fire(obs, plan, action, jet):
            action["boost"] = False
            reason = "descend_to_return_fire"
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
