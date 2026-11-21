"""Run from the repository with MECHFIGHT_KIT=/path/to/kit python3 -m unittest discover -s tests."""
from contextlib import redirect_stdout
import gzip
from io import StringIO
import json
import math
import os
from pathlib import Path
from queue import Queue
import subprocess
import sys
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch

import mechfight

from loadout import Loadout
from navigation import Navigator
from survival import Survival


class DecisionTests(unittest.TestCase):
    def setUp(self):
        if "MECHFIGHT_KIT" not in os.environ:
            self.fail("Set MECHFIGHT_KIT to the extracted official starter kit to run these tests.")
        kit = Path(os.environ["MECHFIGHT_KIT"])
        with gzip.open(kit / "check/stream.jsonl.gz", "rt") as stream:
            self.hello = json.loads(next(stream))
            self.obs = json.loads(next(stream))
        self.hello["map"]["dir"] = str(kit / "arena")
        for field in ("mechs", "projectiles", "crates", "cubes", "pickups", "sounds", "beams", "events", "drops"):
            self.obs[field] = []
        self.me = self.obs["self"]
        self.me.update(pos=[0, 0, 0], aim=[0, 0], vel=[0, 0, 0])
        self.obs["offer"] = None

    def test_future_zone_overrides_loot_outside(self):
        self.obs.update(t=100, zone={"center": [0, 0], "radius": 50,
                                    "next_center": [0, 0], "next_radius": 35,
                                    "shrink_start": 90, "shrink_end": 105, "dps": 160})
        self.me.update(pos=[65, 0, 0], in_zone=False)
        self.obs["cubes"] = [{"id": 5000, "pos": [77, 0, 0]}]
        goal = Survival(self.hello).decide(self.obs)["goal"]
        self.assertLess(math.hypot(*goal[:2]), 65)

    def test_projectile_crossing_preserves_clear_directions(self):
        sim = Survival(self.hello)
        circle = ([0, 0], 90)
        self.obs["projectiles"] = [{"kind": "gun", "pos": [-80, 0.5, 5], "vel": [252, 0, 0]}]
        # The current heading crosses the shot. Accelerating south takes the
        # cylinder toward the far side of the projectile before it arrives.
        south = sim._avoid_crossing_shot(self.obs, (15, 0), 2.5, circle, False)
        self.assertLess(south[1], -5)
        # Already moving away from the bullet corridor: keep that direction.
        self.me["vel"] = [0, -11, 0]
        self.assertEqual(sim._avoid_crossing_shot(self.obs, (0, -15), 2.5, circle, False), (0, -15))
        self.obs["projectiles"][0]["pos"][2] = 20
        self.assertEqual(sim._avoid_crossing_shot(self.obs, (15, 0), 2.5, circle, False), (15, 0))

    def test_isolated_finisher_requires_health_and_room(self):
        policy = Survival(self.hello)
        enemy = {"kind": "mech", "pos": [73, 0, 0], "hp": 400, "max_hp": 1400}
        self.obs["mechs"] = [enemy]
        foe = (enemy["pos"], .72, 73, True)
        fallback = (-20, 0)
        def goal(foes, circle=([0, 0], 150)):
            return policy._finish_goal(self.obs, foes, circle, 2.5, .8, fallback)

        flank = goal([foe])
        self.assertGreater(flank[0], 0)
        self.assertGreater(abs(flank[1]), flank[0])
        self.assertEqual(goal([foe, foe]), fallback)
        self.assertEqual(goal([foe], ([0, 0], 10)), fallback)
        enemy["hp"] = 1200
        self.assertEqual(goal([foe]), fallback)
        enemy.pop("hp")
        self.assertEqual(goal([foe]), fallback)

    def test_first_weapon_worth_a_safe_detour(self):
        self.obs["pickups"] = [{"id": 8000, "kind": "laser", "pos": [88, 0, 0]}]
        self.obs["zone"] = {"center": [0, 0], "radius": 300,
                            "next_center": [0, 0], "next_radius": 230,
                            "shrink_start": 65, "shrink_end": 100, "dps": 20}
        self.assertEqual(Survival(self.hello).decide(self.obs)["target_id"], 8000)

    def test_sustained_gun_upgrade_credit_keeps_defense_competitive(self):
        self.me["weapons"] = [{"kind": "gun", "stats": self.hello["config"]["weapons"]["gun"]}, None]
        self.me["hp"] = self.me["max_hp"]
        self.obs["zone"]["next_radius"] = 140
        policy = Loadout(self.hello)

        def pick(*ids):
            return ids[policy.upgrade(self.obs, [{"id": ident} for ident in ids])]

        self.assertEqual(pick("armor", "gun_mag"), "gun_mag")
        self.assertEqual(pick("gun_mag", "plating"), "plating")
        self.assertEqual(pick("gun_damage", "armor"), "armor")
        self.assertEqual(pick("gun_rate", "armor"), "armor")
        self.me["hp"] = .65 * self.me["max_hp"]
        self.assertEqual(pick("gun_mag", "armor"), "armor")
        self.me["hp"] = self.me["max_hp"]
        self.obs["zone"]["next_radius"] = 90
        self.assertEqual(pick("gun_mag", "armor"), "armor")

    def test_final_point_zone(self):
        self.obs.update(t=420, zone={"center": [0, 0], "radius": 0,
                                    "next_center": [0, 0], "next_radius": 0,
                                    "shrink_start": 380, "shrink_end": 415, "dps": 260})
        self.me.update(pos=[15, 20, 0], in_zone=False)
        goal = Survival(self.hello).decide(self.obs)["goal"]
        self.assertLess(math.hypot(*goal[:2]), 25)

    def test_weapon_pickup_requires_both_horizontal_and_vertical_range(self):
        for pos, reachable in [([3.9, 0, 3.9], True), ([4.1, 0, 0], False), ([0, 0, 4.1], False)]:
            with self.subTest(pos=pos):
                self.obs["pickups"] = [{"id": 8001, "kind": "laser", "pos": pos}]
                action = Loadout(self.hello).decide(self.obs, 0)
                self.assertEqual(action.get("take") == 8001, reachable)

    def test_gun_leads_transverse_target(self):
        self.me["aim"] = [0.05, 0]
        self.obs["mechs"] = [{"id": 8, "kind": "mech", "pos": [90, 0, 0],
                              "vel": [0, 15, 0], "aim": [math.pi, 0], "weapons": ["gun"],
                              "hp": 60, "max_hp": 1400}]
        action = Loadout(self.hello).decide(self.obs, 0)
        self.assertGreater(action["aim"][0], 0.02)
        self.assertLess(action["aim"][0], 0.15)

    def test_lightning_uses_remaining_energy_only_in_a_safe_close_duel(self):
        self.obs["zone"].update(center=[0, 0], next_center=[0, 0], next_radius=300)
        self.me.update(energy=4, in_zone=True)
        self.me["weapons"][1] = {"kind": "lightning", "stats": {}, "cooldown": 0}
        pursuer = {"id": 4, "kind": "mech", "pos": [34, 0, 0], "aim": [math.pi, 0],
                   "vel": [0, 0, 0], "weapons": ["gun", "lightning"]}
        self.obs["mechs"] = [pursuer]
        for distance, climb, shoot in [(34, False, True), (34, True, False), (48, False, False)]:
            with self.subTest(distance=distance, climbing=climb):
                pursuer["pos"][0] = distance
                action = Loadout(self.hello).decide(self.obs, 0, evade=True, climbing=climb)
                self.assertEqual(action.get("fire", [False, False])[1], shoot)

    def test_laser_charges_then_releases_while_kiting(self):
        self.obs.update(alive=2)
        self.obs["zone"].update(center=[0, 0], next_center=[0, 0], next_radius=300)
        self.obs["mechs"] = [{"id": 7, "kind": "mech", "pos": [90, 0, 0],
                              "aim": [math.pi, 0], "weapons": ["gun"], "vel": [0, 0, 0]}]
        laser = {"kind": "laser", "cooldown": 0, "charge": 0, "stats": {}}
        self.me["weapons"][1] = laser
        loadout = Loadout(self.hello)
        self.assertTrue(loadout.decide(self.obs, 0, evade=True)["fire"][1])
        laser["charge"] = self.hello["config"]["weapons"]["laser"]["charge"]
        self.assertFalse(loadout.decide(self.obs, 0, evade=True)["fire"][1])

    def test_live_offer_uses_effects_and_current_choice_order(self):
        # New upgrade IDs and ordering force the policy to use the live definitions.
        upgrades = [
            {"id": "display", "effects": [{"path": "mech.vision_bonus", "add": 1}]},
            {"id": "hull", "effects": [{"path": "mech.hp", "mul": 1.5}]},
        ]
        self.hello["config"]["upgrades"] = upgrades
        for order in (upgrades, upgrades[::-1]):
            choices = [{"id": u["id"], "name": u["id"], "desc": ""} for u in order]
            self.obs["offer"] = {"id": 99, "expires": self.obs["t"] + 5, "choices": choices}
            action = Loadout(self.hello).decide(self.obs, 0)
            self.assertEqual(choices[action["pick"]]["id"], "hull")

    def test_prequeued_burst_answers_only_the_latest_tick(self):
        burst = Queue()
        burst.put(json.dumps(self.hello))
        for tick in (10, 12, 14):
            burst.put(json.dumps(dict(self.obs, tick=tick)))
        class Probe:
            def act(self, obs):
                burst.put('{"type":"end","place":1,"kills":0}')
                return {}

        output = StringIO()
        with patch.object(mechfight.queue, "Queue", return_value=burst), \
             patch.object(mechfight.threading.Thread, "start"), redirect_stdout(output):
            mechfight.run(lambda hello: Probe())
        messages = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(messages[0]["type"], "ready")
        self.assertEqual([message["tick"] for message in messages[1:]], [14])

    def test_wire_protocol_recovers_from_invalid_line_and_exits(self):
        # Put all three observations in the pipe before the reader starts. Remove optional
        # fields and send malformed JSON too, exercising the normal stdin/stdout entrypoint.
        self.obs.pop("offer")
        self.obs.pop("beams")
        root = Path(__file__).resolve().parents[1]
        with subprocess.Popen([sys.executable, "-u", str(root / "bot.py")],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True) as bot:
            lines = Queue()
            def read_lines():
                for output in bot.stdout:
                    lines.put(output)
                lines.put(None)

            Thread(target=read_lines, daemon=True).start()
            try:
                bot.stdin.write(json.dumps(self.hello) + "\n{broken json\n")
                for tick in (2, 4, 6):
                    bot.stdin.write(json.dumps(dict(self.obs, tick=tick)) + "\n")
                bot.stdin.flush()
                self.assertEqual(json.loads(lines.get(timeout=20))["type"], "ready")
                line = json.loads(lines.get(timeout=2))
                # Startup is slower than the pipe reader. On a slow machine, permit actions
                # for observations the reader had not queued yet, just as the official checker does.
                while line["tick"] in (2, 4):
                    line = json.loads(lines.get(timeout=2))
                self.assertEqual(line["tick"], 6)
                bot.stdin.write('{"type":"end","place":1,"kills":0}\n')
                bot.stdin.flush()
                self.assertEqual(bot.wait(timeout=3), 0)
                self.assertNotIn("Traceback", bot.stderr.read())
            finally:
                if bot.poll() is None:
                    bot.kill()


class NavigationTests(unittest.TestCase):
    def make_map(self, tmp, prisms):
        folder = Path(tmp) / "v2"
        folder.mkdir()
        terrain = dict(file="terrain.i16", minX=0, minY=0, nx=101, ny=101, step=1, scale=0.01)
        bounds = dict(minX=0, minY=0, maxX=100, maxY=100)
        (folder / "world.json").write_text(json.dumps(dict(bounds=bounds, terrain=terrain, prisms=prisms)))
        (folder / "terrain.i16").write_bytes(bytes(2 * 101 * 101))
        nav = Navigator(tmp, {})
        self.assertTrue(nav.loaded)
        return nav

    def test_ground_route_around_tall_solid(self):
        # A 70 m tall solid makes climbing with a single energy bar impractical.
        with tempfile.TemporaryDirectory() as tmp:
            solid = dict(kind="building", base=0, top=70, ring=[43, 32, 57, 32, 57, 68, 43, 68], holes=[])
            nav = self.make_map(tmp, [solid])
            self.assertTrue(nav.line_clear([10, 10, 5], [90, 10, 5]))
            self.assertFalse(nav.line_clear([10, 50, 5], [90, 50, 5]))
            pos = [18., 50., 0.]
            for tick in range(0, 400, 2):
                dx, dy, _ = nav.steer(pos, [82, 50], tick)
                pos[0] += dx
                pos[1] += dy
                self.assertFalse(43 < pos[0] < 57 and 32 < pos[1] < 68)
                if math.dist(pos[:2], [82, 50]) <= 3:
                    break
            self.assertLessEqual(math.dist(pos[:2], [82, 50]), 3)

    def test_stuck_on_clear_ground_changes_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            nav = self.make_map(tmp, [])
            outputs = [nav.steer([10, 10, 0], [50, 10], tick) for tick in range(0, 81, 2)]
            self.assertGreater(outputs[0][0], 0.9)
            self.assertTrue(any(jet or abs(dy) > 0.25 for _, dy, jet in outputs[1:]))
