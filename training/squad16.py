"""Research-only 16-mech placement surrogate. The official house AI and practice seeds are private.

Uses the campus, published circle phases, starting separation, class counts and cooperative
targeting. Tier aim error, pacing, search routes and activation thresholds below are hypotheses.
Local physics, rival navigation, loot and NPC behavior are approximations. House mechs do not
jet or farm crates, and NPC drones only engage the player. Absolute official scores are unknown.
"""

import copy
import gzip
import json
import math
from pathlib import Path
import random

from training.arena import Actor, Episode, Layout, clamp, horizontal


class Campus(Layout):
    def __init__(self, root, cfg):
        super().__init__(root, config=cfg)
        self.bounds = json.loads((root / "v2" / "world.json").read_text())["bounds"]
        n = self.nav
        self.level = [
            max((top for _, top in solids), default=n.floors[i]) for i, solids in enumerate(n.solids)
        ]
        self.x0, self.y0 = n.ox - 1.5, n.oy - 1.5

    def ix(self, x, y):
        i = min(self.nav.w - 1, max(0, int((x - self.x0) / 3)))
        j = min(self.nav.h - 1, max(0, int((y - self.y0) / 3)))
        return self.nav.w * j + i

    def ground(self, x, y):
        return self.nav.floors[self.ix(x, y)]

    def surface(self, x, y):
        return self.level[self.ix(x, y)]

    def walk(self, x, y, z, r):
        b = self.bounds
        if not b["minX"] + r <= x <= b["maxX"] - r or not b["minY"] + r <= y <= b["maxY"] - r:
            return False
        i = self.ix(x, y)
        n = self.nav
        room_at_ground = n.clearance[i] >= math.ceil(r + 1.05) and n.headroom[i] >= 9
        return room_at_ground or self.level[i] <= z + 1.2


class SquadArena:
    def __init__(self, kit):
        with gzip.open(Path(kit) / "check/stream.jsonl.gz", "rt") as f:
            self.hello = json.loads(next(f))
        self.layout = Campus(Path(kit) / "arena", self.hello["config"])

    def close(self):
        self.layout = None

    def run(self, factory, seed, scenario="squad16", *, trace=None):
        if scenario != "squad16":
            raise ValueError(f"Unexpected 16-mech scenario {scenario!r}")
        h = copy.deepcopy(self.hello)
        h["map"]["dir"] = str(self.layout.directory)
        h["slot"] = random.Random(f"squad-slot/{seed}").randrange(16)
        h["seed"] = random.Random(f'local-slot-no-match-info/{h["slot"]}').getrandbits(32)
        ep = SquadEpisode(h, self.layout, seed)
        return ep.run(factory(h), trace)


class SquadEpisode(Episode):
    def __init__(self, h, layout, seed):
        self.cfg, self.layout, self.seed, self.scenario = h["config"], layout, seed, "squad16"
        self.rng = random.Random(f"squad16/{seed}")
        self.dt = 1 / self.cfg["match"]["tick_hz"]
        self.stride = self.cfg["match"]["decide_every"]
        self.duration = self.cfg["match"]["duration_s"]
        self.now = 0.0
        self.actors = {}
        self.shots, self.pickups, self.cubes = [], [], []
        self.dead, self.memory = {}, {}
        self.next_id = 10000
        self.dealt = self.taken = self.zone_damage = 0.0
        self.kills = 0
        self.next_house_tick = 0.0
        self.shared_until = -1.0
        self.last_seen = None
        self.last_velocity = None
        self.hunters = set()
        self.commands = {}
        rules = self.cfg["zone"]
        self.center = rules["start_center"]
        self.radius = rules["start_radius"]
        self.phases = []
        p = self.center
        r = self.radius
        t = 0.0
        for phase in rules["phases"]:
            theta = self.rng.uniform(-math.pi, math.pi)
            dist = self.rng.uniform(0.1, 0.95) * (r - phase["radius"])
            dest = (p[0] + math.cos(theta) * dist, p[1] + math.sin(theta) * dist)
            dest = tuple(
                clamp(n, layout.bounds["min" + k] + 9, layout.bounds["max" + k] - 9)
                for n, k in zip(dest, ("X", "Y"))
            )
            end = t + phase["hold_s"] + phase["shrink_s"]
            self.phases.append((t + phase["hold_s"], end, p, r, dest, phase["radius"], phase["dps"]))
            p, r, t = dest, phase["radius"], end
        self.zone = {}
        points = []
        for _restart in range(15):
            points = []
            for _ in range(7000):
                xy = self.open_point(self.radius * self.cfg["match"]["spawn_zone_fraction"])
                if all(
                    horizontal(xy, a) >= self.cfg["match"]["spawn_min_separation"] for a in points
                ):
                    points.append(xy)
                if len(points) == 16:
                    break
            if len(points) == 16:
                break
        if len(points) != 16:
            raise ValueError("unable to place all mechs")
        self.rng.shuffle(points)
        for i, point in enumerate(points):
            mech = Actor(i, "mech", point, self.cfg, seed)
            mech.equip(0, "gun", self.cfg)
            self.actors[i] = mech
        self.player = self.actors[h["slot"]]
        self.opponents = [i for i in range(16) if i != self.player.id]
        self.rng.shuffle(self.opponents)
        self.tiers = {i: min(3, j // 4) for j, i in enumerate(self.opponents)}
        self.npcs = []
        for j in range(self.cfg["npc"]["count"]):
            a = Actor(100 + j, "npc", self.open_point(self.radius), self.cfg, seed)
            self.npcs.append(a)
            self.actors[a.id] = a
        for j in range(self.cfg["crates"]["count"]):
            roof = self.rng.random() < self.cfg["crates"]["roof_fraction"]
            a = Actor(1000 + j, "crate", self.open_point(self.radius, roof), self.cfg, seed)
            self.actors[a.id] = a
        for j in range(self.cfg["loot"]["floor_count"]):
            w = self.rng.choice(("mortar", "laser", "lightning"))
            roof = self.rng.random() < self.cfg["loot"]["floor_roof_fraction"]
            self.pickups.append(dict(id=8000 + j, kind=w, pos=self.open_point(self.radius, roof)))

    def open_point(self, radius, roof=False):
        b = self.layout.bounds
        for _ in range(2000):
            x = self.rng.uniform(b["minX"] + 8, b["maxX"] - 8)
            y = self.rng.uniform(b["minY"] + 8, b["maxY"] - 8)
            if horizontal(self.center, (x, y)) > radius:
                continue
            z = self.layout.ground(x, y)
            if roof:
                z2 = self.layout.surface(x, y)
                if z2 < z + 5:
                    continue
                return [x, y, z2]
            if self.layout.walk(x, y, z, 2.5):
                return [x, y, z]
        raise RuntimeError("no valid spawn")

    def update_zone(self):
        for start, end, c, r, nc, nr, dps in self.phases:
            if self.now <= end:
                break
        u = clamp((self.now - start) / (end - start), 0.0, 1.0)
        self.zone = dict(
            center=[c[0] + u * (nc[0] - c[0]), c[1] + u * (nc[1] - c[1])],
            radius=r + u * (nr - r),
            next_center=nc,
            next_radius=nr,
            shrink_start=start,
            shrink_end=end,
            dps=dps,
        )
        if self.now < self.next_house_tick:
            return
        self.next_house_tick = self.now + 0.5
        rivals = [self.actors[i] for i in self.opponents if self.actors[i].hp > 0]
        # The published memory rule tracks live positions for five seconds after sight is lost.
        if any(self.visible(a, self.player.pos, self.player.height) for a in rivals):
            self.shared_until = self.now + self.cfg["vision"]["memory_s"]
        if self.now <= self.shared_until:
            self.last_seen = self.player.pos.copy()
            self.last_velocity = self.player.vel.copy()
        count = (
            len(rivals) if self.now >= self.phases[-2][0] else min(len(rivals), 1 + len(self.dead))
        )
        # Preserve an active rival between deaths. Tier is primary; distance breaks ties.
        self.hunters = {a.id for a in rivals if a.id in self.hunters}
        order = sorted(
            rivals,
            key=lambda a: (
                self.tiers[a.id],
                horizontal(a.pos, self.last_seen) if self.last_seen else 0.0,
            ),
        )
        for a in order:
            if len(self.hunters) >= count:
                break
            self.hunters.add(a.id)
        self.commands = {a.id: self.command(a) for a in rivals}
        for a in rivals:
            a.events.clear()
            a.sounds.clear()

    def command(self, a):
        tier = self.tiers[a.id]
        fix = self.last_seen if self.now <= self.shared_until else None
        d = max(1.0, horizontal(a.pos, fix)) if fix else math.inf
        active = a.id in self.hunters
        center = self.zone["next_center"]
        outside = horizontal(a.pos, self.zone["center"]) > self.zone["radius"] - 15
        if outside:
            goal = center
        elif active and fix:
            goal = fix
        elif horizontal(a.home, center) > self.zone["next_radius"] - 9:
            goal = center
        else:
            angle = (int(self.now / 9) + a.id) * 2.39996
            goal = (a.home[0] + 42 * math.cos(angle), a.home[1] + 42 * math.sin(angle))
        yaw = math.atan2(goal[1] - a.pos[1], goal[0] - a.pos[0])
        if not outside and active and fix and d < 75:
            yaw += (-1 if a.id % 2 else 1) * 1.1
        if a.pos[2] > self.layout.ground(*a.pos[:2]) + 2:
            offsets = (0.0, 0.5, -0.5, 1.2, -1.2)
        else:
            offsets = (0.0, 0.52, -0.52, 1.04, -1.04, 1.56, -1.56, 2.1, -2.1)
        for off in offsets:
            ux, uy = math.cos(yaw + off), math.sin(yaw + off)
            if self.layout.walk(a.pos[0] + 7 * ux, a.pos[1] + 7 * uy, a.pos[2], 2.5):
                break
        aim = [yaw, 0.0]
        fire = False
        if (
            active
            and fix
            and d < 220
            and self.layout.clear((*a.pos[:2], a.pos[2] + 7), (*fix[:2], fix[2] + 4.5))
        ):
            lead = (0.22, 0.48, 0.73, 0.95)[tier] * d / self.cfg["weapons"]["gun"]["speed"]
            delta = [fix[j] + lead * self.last_velocity[j] - a.pos[j] for j in range(2)]
            aim = [
                math.atan2(delta[1], delta[0]) + a.rng.gauss(0, (0.115, 0.075, 0.04, 0.018)[tier]),
                math.atan2(fix[2] + 4.5 - a.pos[2] - 7, max(1.0, math.hypot(*delta)))
                + a.rng.gauss(0, (0.038, 0.030, 0.021, 0.012)[tier]),
            ]
            fire = True
        speed = 1.0 if active or outside else 0.5
        action = dict(move=[ux * speed, uy * speed], aim=aim, fire=[fire, False])
        if not a.weapons[1]:
            found = next(
                (
                    p
                    for p in self.pickups
                    if abs(p["pos"][0] - a.pos[0]) < 4 and abs(p["pos"][1] - a.pos[1]) < 4
                ),
                None,
            )
            if found:
                action["take"] = found["id"]
        elif fire:
            w = a.weapons[1]
            k = w["kind"]
            if k == "lightning":
                action["fire"][1] = d < w["stats"]["range"]
            elif k == "laser":
                action["fire"][1] = w.get("charge", 0) < w["stats"]["charge"]
            elif 28 < d < 145:
                action["fire"][1] = True
                if w["cooldown"] <= 0.2:
                    aim[1] += 0.5 * math.asin(
                        min(1.0, d * w["stats"]["gravity"] / w["stats"]["speed"] ** 2)
                    )
        return action

    def house(self, a):
        return self.commands[a.id]

    def drone(self):
        for a in self.npcs:
            if a.hp > 0 and horizontal(a.pos, self.player.pos) < 100:
                self.drone_actor(a)
