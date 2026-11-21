"""Checks for match evidence, adaptation, and offline policy promotion."""
from contextlib import redirect_stdout
from argparse import Namespace
import gzip
from io import StringIO
import json
import math
import os
from pathlib import Path
from select import select
import subprocess
import sys
import tempfile
from threading import Thread
import time
import unittest
from unittest.mock import patch

import mechfight


ROOT = Path(__file__).resolve().parents[1]


class MatchRecordingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        kit = Path(os.environ["MECHFIGHT_KIT"])
        with gzip.open(kit / "check/stream.jsonl.gz", "rt") as stream:
            cls.hello = json.loads(next(stream))
            cls.obs = json.loads(next(stream))
        cls.hello["map"]["dir"] = str(kit / "arena")

    def run_match(self, log_dir, observations):
        env = dict(os.environ, MECHFIGHT_LOG_DIR=str(log_dir), MECHFIGHT_LOG_RAW="1")
        with subprocess.Popen([sys.executable, "-u", str(ROOT / "bot.py")],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, env=env) as bot:
            def send(message):
                bot.stdin.write((json.dumps(message) + "\n").encode())
                bot.stdin.flush()

            def receive(timeout):
                self.assertTrue(select([bot.stdout], [], [], timeout)[0],
                                "Bot did not write its next protocol message")
                return json.loads(bot.stdout.readline())

            try:
                send(self.hello)
                self.assertEqual(receive(20)["type"], "ready")
                actions = []
                for obs in observations:
                    send(obs)
                    action = receive(2)
                    self.assertEqual(action["tick"], obs["tick"])
                    actions.append(action)
                send({"type": "end", "place": 4, "kills": 2})
                stdout, stderr = bot.communicate(timeout=3)
                self.assertEqual(bot.returncode, 0, stderr.decode())
                self.assertEqual(stdout, b"")
                return actions
            finally:
                if bot.poll() is None:
                    bot.kill()

    def test_observation_fallback_and_end_survive_process_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            first = dict(self.obs, tick=10)
            malformed = dict(self.obs, tick=12)
            del malformed["self"]
            recovered = dict(self.obs, tick=14)
            actions = self.run_match(folder, [first, malformed, recovered])
            path, = Path(folder).glob("match-*.jsonl")
            rows = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual([row["type"] for row in rows], ["header", "tick", "tick", "tick", "end"])
        header, one, fallback, three, end = rows
        self.assertEqual(header["slot"], self.hello["slot"])
        self.assertEqual([row["action"] for row in (one, fallback, three)], actions)
        self.assertEqual(one["obs"], first)
        self.assertEqual(three["obs"], recovered)
        for valid in (one, three):
            for field in ("mode", "reason", "goal", "combat", "learning"):
                self.assertTrue(valid["decision"][field], field)
        self.assertEqual(fallback["fallback"], "act_error")
        self.assertFalse(fallback["on_time"])
        self.assertEqual(three["events"], recovered["events"])
        self.assertTrue(end["end_received"])
        self.assertEqual((end["place"], end["kills"]), (4, 2))

    def test_unusable_log_directory_preserves_the_wire_protocol(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "regular-file"
            path.write_text("preexisting")
            self.run_match(path, [dict(self.obs, tick=2)])
            self.assertEqual(path.read_text(), "preexisting")

    def test_superseded_frames_are_distinguished_from_executed_actions(self):
        start_writer = Thread.start
        inbox = []
        def start(thread):
            if thread._target != mechfight._reader:
                return start_writer(thread)
            q, = thread._args
            inbox.append(q)
            for message in [self.hello, *(dict(self.obs, tick=i) for i in (8, 10, 12))]:
                q.put((time.perf_counter(), json.dumps(message)))

        class Probe:
            last_decision = {"mode": "hold", "reason": "settled"}
            def act(self, obs):
                inbox[0].put((time.perf_counter(), '{"type":"end","place":1,"kills":0}'))
                return {"move": [0, 0]}

        wire = StringIO()
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, MECHFIGHT_LOG_DIR=folder):
            with patch.object(Thread, "start", start), redirect_stdout(wire):
                mechfight.run(lambda hello: Probe())
            path, = Path(folder).glob("match-*.jsonl")
            rows = [json.loads(line) for line in path.read_text().splitlines()]
        actions = [json.loads(line) for line in wire.getvalue().splitlines()]
        self.assertEqual([a["tick"] for a in actions if "tick" in a], [12])
        ticks = [r for r in rows if r["type"] == "tick"]
        self.assertEqual([r["tick"] for r in ticks], [8, 10, 12])
        for skipped in ticks[:2]:
            self.assertIsNone(skipped["action"])
            self.assertEqual(skipped["fallback"], "superseded")
        self.assertEqual(ticks[-1]["action"], actions[-1])
        self.assertEqual((rows[-1]["skipped_ticks"], rows[-1]["dropped_ticks"]), (2, 0))


    def test_full_log_budget_keeps_the_end_and_counts_lost_ticks(self):
        from recorder import MatchRecorder

        with tempfile.TemporaryDirectory() as folder, patch("recorder.MAX_BYTES", 65536):
            log = MatchRecorder(self.hello, output_dir=folder, raw=True)
            # Reusing the same object also exercises snapshotting of caller-owned data.
            obs = dict(self.obs, events=[{"type": "hit", "weapon": "gun", "amount": 2, "target": 7}])
            for tick in range(600):
                obs["tick"] = tick
                log.record(obs, {"tick": tick, "move": [1, 0]}, {"reason": "inbound"})
            log.close({"type": "end", "place": 3, "kills": 0})
            self.assertLessEqual(log.path.stat().st_size, 65536)
            rows = [json.loads(line) for line in log.path.read_text().splitlines()]
        ticks, terminal = rows[1:-1], rows[-1]
        self.assertTrue(ticks)
        self.assertGreater(terminal["dropped_ticks"], 0)
        self.assertEqual(len(ticks) + terminal["dropped_ticks"], 600)
        self.assertEqual(terminal["damage_out"], 1200)
        self.assertEqual(terminal["place"], 3)
        for record in ticks:
            self.assertEqual(record["action"]["tick"], record["tick"])


class OnlineAdaptationTests(unittest.TestCase):
    def engagement(self):
        obs = {
            "tick": 0, "t": 0.0,
            "self": {"pos": [0.0, 0.0, 0.0], "vel": [0.0, 0.0, 0.0], "hp": 1400,
                     "max_hp": 1400, "in_zone": True, "grounded": True},
            "zone": {"center": [0, 0], "radius": 300, "next_center": [0, 0], "next_radius": 250},
            "mechs": [{"id": 7, "kind": "mech", "pos": [90., 0., 0.], "weapons": ["gun"]}],
            "events": [],
        }
        return obs, {"mode": "evade", "goal": (0., 15.)}

    def test_observed_damage_changes_a_later_move_only_after_confirmed_motion(self):
        from adaptation import AdaptivePolicy, DEFAULT_POLICY
        reliable = AdaptivePolicy({"config": {}}, policy=DEFAULT_POLICY)
        late = AdaptivePolicy({"config": {}}, policy=DEFAULT_POLICY)
        obs, plan = self.engagement()
        initial = reliable.decide(obs, plan)
        self.assertEqual(late.decide(obs, plan), initial)
        self.assertEqual(reliable.diagnostics()["arm"], "press")
        actual = initial
        for i in range(1, 11):
            dx, dy = (a - b for a, b in zip(actual["goal"], obs["self"]["pos"][:2]))
            length = math.hypot(dx, dy)
            ux, uy = dx / length, dy / length
            action = {"move": [ux, uy]}
            reliable.sent(obs["tick"], action)
            late.sent(obs["tick"], action, on_time=False)
            obs["tick"], obs["t"] = i * 2, i / 10
            me = obs["self"]
            # A new movement command produces measured acceleration on the first interval.
            speed = min(11.7, 3.0 * i)
            me["vel"][:2] = [ux * speed, uy * speed]
            me["pos"][0] += ux * speed * .1
            me["pos"][1] += uy * speed * .1
            x, y = me["pos"][:2]
            obs["mechs"][0]["pos"][:2] = [x + 90., y]
            plan["goal"] = (x, y + 15)
            obs["events"] = [{"type": "damaged", "amount": 100., "weapon": "gun", "by": 7}] if i == 1 else []
            if i == 1:
                me["hp"] -= 100
            actual = reliable.decide(obs, plan)
            control = late.decide(obs, plan)
            if i == 1:
                self.assertTrue(reliable.diagnostics()["credited"])
                self.assertLess(reliable.diagnostics()["reward"], 0)
        self.assertEqual((reliable.diagnostics()["arm"], late.diagnostics()["arm"]), ("space", "press"))
        self.assertLess(actual["goal"][0], control["goal"][0] - 2)
        self.assertEqual(late.diagnostics()["evidence"], 0)

    def test_gap_discards_feedback_and_urgent_zone_retains_its_goal(self):
        from adaptation import AdaptivePolicy, DEFAULT_POLICY
        policy = AdaptivePolicy({"config": {}}, policy=DEFAULT_POLICY)
        obs, plan = self.engagement()
        policy.decide(obs, plan)
        policy.sent(0, {"move": [0, 1]}, applied=True)
        obs.update(tick=4, t=.2, events=[{"type": "damaged", "amount": 90, "weapon": "gun"}])
        obs["self"]["in_zone"] = False
        self.assertEqual(policy.decide(obs, plan), plan)
        self.assertEqual(policy.diagnostics()["evidence"], 0)


class OfflinePromotionTests(unittest.TestCase):
    def test_heldout_result_gates_persistence_on_disk(self):
        from adaptation import DEFAULT_POLICY, load_policy
        from training import tune

        for final_gain in (-1, 1):
            with self.subTest(final_gain=final_gain), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                policy_path = root / "policy.json"
                original = json.dumps(DEFAULT_POLICY, indent=2) + "\n"
                policy_path.write_text(original)
                args = Namespace(policy=policy_path, output_dir=root / "run",
                                 kit=Path(os.environ["MECHFIGHT_KIT"]),
                                 seed=197, train_seeds=2, validation_seeds=2, test_seeds=2,
                                 rounds=1, scenarios=["duel"], match_log=[], apply=True)
                calls = []
                def episodes(policy, seeds, split):
                    calls.append((split, tuple(seeds)))
                    different = policy != DEFAULT_POLICY
                    change = (final_gain if split == "test" else 1) if different else 0
                    telemetry = dict(ticks=10, attacking=3, armed_ticks=0, taken=10, dealt=5, modes={})
                    return [dict(seed=s, scenario="duel", score=1+change, telemetry=telemetry)
                            for s in seeds]

                # Give the optimizer a controlled reversal on the final split. Exercise
                # the production proposal, comparison, report, disk write and reload.
                with patch.object(tune, "Arena"), patch.object(tune.Evaluation, "episodes", side_effect=episodes), \
                     redirect_stdout(StringIO()):
                    result = tune.tune(args)
                splits = result["splits"]
                self.assertEqual(len(set().union(*splits.values())), sum(map(len, splits.values())))
                self.assertTrue(result["rounds"][0]["promoted"])
                self.assertEqual(result["policy_applied"], final_gain > 0)
                self.assertEqual(json.loads((args.output_dir / "report.json").read_text()), result)
                self.assertEqual(load_policy(policy_path), result["selected_policy"])
                if final_gain > 0:
                    self.assertNotEqual(load_policy(policy_path), DEFAULT_POLICY)
                else:
                    self.assertEqual(policy_path.read_text(), original)
                first_test = next(i for i, (name, _) in enumerate(calls) if name == "test")
                self.assertTrue(all(name == "test" for name, _ in calls[first_test:]))
                for name, seeds in calls:
                    self.assertEqual(list(seeds), splits[name])

    def test_local_arena_keeps_every_move_and_post_action_outcome(self):
        from adaptation import DEFAULT_POLICY
        from training.arena import Arena
        from training.tune import Evaluation

        arena = Arena(os.environ["MECHFIGHT_KIT"])
        self.addCleanup(arena.close)
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            training = Evaluation(arena, directory, ["pursuit"])
            episode, = training.episodes(DEFAULT_POLICY, [130047], "train")
            with gzip.open(directory / episode["trace"], "rt") as stream:
                records = [json.loads(line) for line in stream]
        ticks, end = records[1:-1], records[-1]
        self.assertGreater(len(ticks), 10)
        self.assertEqual(end["ticks"], len(ticks))
        self.assertEqual(end["dropped_ticks"], 0)
        self.assertEqual(episode["place_proxy"], end["place"])
        for tick in ticks:
            self.assertEqual(tick["tick"], tick["action"]["tick"])
            self.assertIn("reason", tick["decision"])
        self.assertEqual(ticks[-1]["outcome"]["hp_after"], episode["final_hp"])
        for key in ("damage_dealt", "damage_taken", "zone_damage", "kills"):
            self.assertAlmostEqual(sum(tick["outcome"][key] for tick in ticks), episode[key])

    def test_interrupted_game_cannot_become_training_evidence(self):
        from training.tune import read_trace
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "partial.jsonl"
            rows = [{"type": "header"}, {"type": "tick", "tick": 1, "events": []},
                    {"type": "end", "place": None, "kills": None, "end_received": False}]
            path.write_text("".join(json.dumps(r) + "\n" for r in rows))
            with self.assertRaises(ValueError):
                read_trace(path)
