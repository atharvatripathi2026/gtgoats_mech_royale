"""Astra's placement-first policy for the Builders Mech Royale game."""
import math

import mechfight


class Bot:
    name = "Astra"

    def __init__(self, hello):
        if hello.get("protocol") != "mechfight/1":
            raise ValueError("Unsupported protocol")
        self.config = hello["config"]
        self.side = 1 if hello["slot"] % 2 else -1

    def act(self, obs):
        me, zone = obs["self"], obs["zone"]
        x, y, z = me["pos"]
        zx, zy = zone["next_center"]
        gx, gy = zx - x, zy - y
        travel = math.atan2(gy, gx)
        space = zone["next_radius"] - math.hypot(gx, gy)
        enemies = [a for a in obs.get("mechs", []) if a.get("kind") == "mech"]
        enemy = min(enemies, key=lambda a: math.dist(a["pos"], me["pos"]), default=None)
        yaw, pitch = travel, 0
        aim_ok = False
        if enemy:
            ex, ey, ez = enemy["pos"]
            distance = math.hypot(ex - x, ey - y)
            lead = distance / self.config["weapons"]["gun"]["speed"]
            vx, vy, vz = enemy.get("vel", (0, 0, 0))
            yaw = math.atan2(ey + vy * lead - y, ex + vx * lead - x)
            pitch = math.atan2(ez - z - 2.5 + vz * lead, max(1, distance))
            aim_ok = abs(math.remainder(yaw - me["aim"][0], math.tau)) < 0.10 and abs(pitch - me["aim"][1]) < 0.12
            if distance < 120 and space > 15:
                travel = yaw + self.side * (2.0 if distance < 45 else 1.45)
        move = [math.cos(travel), math.sin(travel)] if space < 20 or enemy else [0, 0]
        action = {"move": move, "aim": [yaw, pitch], "boost": not me["in_zone"] and me["energy"] > 8,
                  "fire": [aim_ok, aim_ok and enemy is not None and distance < 40]}
        offer = obs.get("offer")
        if offer and offer.get("choices"):
            choices = [c["id"] for c in offer["choices"]]
            action["pick"] = next((choices.index(k) for k in ("armor", "walk_speed", "gun_rate") if k in choices), 0)
        if not all(me["weapons"]):
            held = {w["kind"] for w in me["weapons"] if w}
            for item in obs.get("pickups", []):
                px, py, pz = item["pos"]
                if item["kind"] not in held and abs(pz - z) <= 4 and math.hypot(px-x, py-y) <= self.config["loot"]["pickup_radius"]:
                    action["take"] = item["id"]
                    break
        return action


if __name__ == "__main__":
    mechfight.run(Bot)
