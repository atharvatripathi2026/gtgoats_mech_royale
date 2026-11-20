"""Astra's mechfight/1 entry point."""
import math
import os
import time

import mechfight
from loadout import Loadout
from navigation import Navigator
from survival import Survival


class Bot:
    name = "Astra"

    def __init__(self, hello):
        if hello.get("protocol") != "mechfight/1":
            raise ValueError("Unsupported protocol")
        self.slot = hello["slot"]
        self.nav = Navigator(hello["map"]["dir"], hello["config"])
        self.survival = Survival(hello, self.nav)
        self.loadout = Loadout(hello, self.nav)
        self.trace = os.environ.get("MECHFIGHT_TRACE") == "1"
        self.scan_yaw = (self.slot % 16) * math.tau / 16

    def act(self, obs):
        if self.trace:
            start = time.perf_counter()
        me = obs["self"]
        pos = me["pos"]
        stats = me.get("stats", {})
        plan = self.survival.decide(obs)
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
        if self.trace:
            elapsed = (time.perf_counter() - start) * 1000
            mechfight.log(f'tick={obs["tick"]} hp={me["hp"]} mode={plan["mode"]} '
                          f'goal={goal} action={action} decision_ms={elapsed:.3f}')
        return action


if __name__ == "__main__":
    mechfight.run(Bot)
