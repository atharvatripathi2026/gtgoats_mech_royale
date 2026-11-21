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
        # A short, unobstructed advance can collect the contents of the first
        # crate sooner. Keep the current aim/trigger and stop well outside it.
        combat = self.loadout.last_decision
        if (obs.get("t", 0) < 40 and me.get("cubes", 0) == 0 and plan["mode"] == "farm"
                and grounded and self.nav.loaded and not jet and not action["boost"]
                and not base["dodge"] and base["zone_urgency"] < .2
                and self.loadout.last_damage < obs.get("t", 0) - 3
                and base["enemy_pressure"] < .15
                and all(e.get("kind") != "mech" or math.dist(pos, e["pos"]) > 140
                        for e in obs.get("mechs") or ())
                and not any(w and w.get("charge", 0) > 0 for w in me.get("weapons", ()))
                and not any(move) and combat.get("intent") == "engage"
                and combat.get("target_id") == plan["target_id"]):
            crate = next((c for c in obs.get("crates") or () if c["id"] == plan["target_id"]), None)
            if crate is not None:
                px, py, pz = crate["pos"]
                dx, dy = px - pos[0], py - pos[1]
                span = math.hypot(dx, dy)
                if 12.5 < span <= 17 and abs(pz - pos[2]) < 1.5:
                    scale = (span - 12.5) / span
                    ex, ey = pos[0] + dx * scale, pos[1] + dy * scale
                    clearance, height = self.nav._dimensions(stats.get("radius", 2.5))
                    if self.nav._ground_segment(*pos[:2], ex, ey, clearance, height):
                        strength = min(.55, (span - 12.5) * .25)
                        action["move"] = [strength * dx / span, strength * dy / span]
        self.last_decision = {
            "mode": plan["mode"], "reason": base["reason"], "goal": list(goal),
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
