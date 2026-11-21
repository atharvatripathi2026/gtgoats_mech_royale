"""Physics and placement invariants for the cooperative 16-mech local scenario."""
from collections import Counter
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import unittest

from bot import Bot
from training.squad16 import SquadArena, SquadEpisode


class Squad16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        kit = os.environ.get("MECHFIGHT_KIT")
        if not kit:
            raise unittest.SkipTest("Set MECHFIGHT_KIT to the extracted official kit.")
        cls.arena = SquadArena(Path(kit))

    def episode(self, seed=78342):
        hello = copy.deepcopy(self.arena.hello)
        hello["map"]["dir"] = str(self.arena.layout.directory)
        hello["slot"] = 7
        return hello, SquadEpisode(hello, self.arena.layout, seed)

    def test_official_map_spawns_all_mechs_with_required_spacing_and_guns(self):
        hello, ep = self.episode()
        cfg = hello["config"]
        mechs = [a for a in ep.actors.values() if a.kind == "mech"]
        self.assertEqual({a.id for a in mechs}, set(range(cfg["match"]["mechs"])))
        self.assertEqual(ep.player.id, hello["slot"])
        self.assertEqual(Counter(ep.tiers.values()), {0: 4, 1: 4, 2: 4, 3: 3})
        self.assertEqual(len(ep.npcs), cfg["npc"]["count"])
        self.assertEqual(len(ep.pickups), cfg["loot"]["floor_count"])
        for i, actor in enumerate(mechs):
            self.assertEqual([w["kind"] if w else None for w in actor.weapons], ["gun", None])
            self.assertLessEqual(math.dist(actor.pos[:2], cfg["zone"]["start_center"]),
                                 cfg["zone"]["start_radius"] * cfg["match"]["spawn_zone_fraction"])
            self.assertTrue(self.arena.layout.walk(*actor.pos, actor.radius))
            for other in mechs[i + 1:]:
                self.assertGreaterEqual(math.dist(actor.pos[:2], other.pos[:2]),
                                        cfg["match"]["spawn_min_separation"])
        ep.update_zone()
        self.assertEqual(ep.obs(0)["alive"], 16)

    def test_shared_sighting_hunter_escalation_and_memory_expiry(self):
        _, ep = self.episode()
        scout = next(i for i in ep.opponents if ep.tiers[i] == 3)
        ep.visible = lambda actor, *unused: actor.id == scout
        ep.update_zone()
        first_hunters = ep.hunters.copy()
        self.assertEqual(len(first_hunters), 1)
        self.assertEqual(ep.tiers[next(iter(first_hunters))], 0)
        self.assertNotIn(scout, first_hunters)
        self.assertEqual(ep.last_seen, ep.player.pos)
        expiry = ep.shared_until
        self.assertEqual(expiry, ep.cfg["vision"]["memory_s"])
        ep.visible = lambda *unused: False
        ep.player.pos[0] += 12
        ep.player.vel[0] = 7
        ep.now = expiry - 0.5
        ep.update_zone()
        self.assertEqual(ep.last_seen, ep.player.pos)
        self.assertEqual(ep.last_velocity, ep.player.vel)
        self.assertEqual(ep.shared_until, expiry)
        tracked_pos = ep.last_seen.copy()
        tracked_vel = ep.last_velocity.copy()
        victim = next(i for i in ep.opponents if i != scout and i not in first_hunters)
        ep.actors[victim].hp = 0
        ep.dead[victim] = ep.now
        ep.now = expiry + 1
        ep.player.pos[0] += 20
        ep.player.vel[0] = -3
        ep.update_zone()
        self.assertEqual(ep.last_seen, tracked_pos)
        self.assertEqual(ep.last_velocity, tracked_vel)
        self.assertNotEqual(ep.last_seen, ep.player.pos)
        active = ep.actors[next(iter(first_hunters))]
        command = ep.command(active)
        ep.player.pos[:2] = active.pos[:2]
        ep.player.vel[1] = 16
        self.assertEqual(ep.command(active), command)
        self.assertEqual(len(ep.hunters), 2)
        self.assertTrue(first_hunters <= ep.hunters)
        self.assertTrue(all(not any(c["fire"]) for c in ep.commands.values()))
        ep.now = ep.phases[-2][0]
        ep.update_zone()
        self.assertEqual(ep.hunters, set(ep.opponents) - {victim})

    def test_simultaneous_deaths_share_placement(self):
        _, ep = self.episode()
        ep.now = ep.duration
        ep.player.hp = 0
        ep.dead[ep.player.id] = 90.
        for rival, when in zip(ep.opponents, [80.] * 4 + [90.] * 2 + [91.] * 3):
            ep.actors[rival].hp = 0
            ep.dead[rival] = when
        result = ep.run(object(), trace=None)
        # Four died earlier; three on the same tick; nine outlived all three.
        self.assertEqual((result["place_proxy"], result["score"]), (10, 6))

    def test_same_bot_and_seed_repeat_decision_trajectory(self):
        def replay():
            hello, ep = self.episode(69811)
            ep.duration = 10
            digest = hashlib.sha256()
            n = 0

            def record(obs, action, outcome):
                nonlocal n
                n += 1
                # Measured CPU/wall time is the only nondeterministic field.
                facts = {k: v for k, v in outcome.items() if k != "decision_ms"}
                digest.update(json.dumps([obs, action, facts], sort_keys=True, allow_nan=False).encode())

            result = ep.run(Bot(hello), record)
            self.assertGreater(n, 5)
            return digest.hexdigest(), result

        self.assertEqual(replay(), replay())


if __name__ == "__main__":
    unittest.main()
