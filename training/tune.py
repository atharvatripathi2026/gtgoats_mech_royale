"""Evaluate and promote Astra policies against matched local game simulations.

Run from the repository with python3 -m training.tune --help.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import tempfile

from adaptation import POLICY_BOUNDS, load_policy, validate_policy
from bot import Bot
from recorder import MatchRecorder
from training.arena import Arena, SCENARIOS


ROOT = Path(__file__).resolve().parents[1]
EPSILON = 1e-9


def json_text(value):
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))


def atomic_json(path, value):
    """Either the previous complete file or the new complete file is visible."""
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as stream:
        temp = Path(stream.name)
        try:
            stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    try:
        if path.exists():
            temp.chmod(path.stat().st_mode & 0o777)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def read_trace(path, compress=False):
    """Summarize decisions and their observed consequences in temporal order."""
    op = gzip.open if path.suffix == ".gz" else open
    events, modes = Counter(), Counter()
    arm_counts, arm_rewards, reasons = Counter(), Counter(), Counter()
    action_hash = hashlib.sha256()
    applied_outcomes = opportunities = loot_seen = 0
    previous_arm = previous_tick = None
    hits = damage = attacking = armed_ticks = ticks = 0
    header = end = None
    with op(path, "rt") as stream:
        for line in stream:
            record = json.loads(line)
            tag = record.get("type")
            if tag == "header":
                header = record
            elif tag == "tick":
                ticks += 1
                action_hash.update(json_text([record.get("tick"), record.get("action")]).encode())
                if record.get("action") is not None:
                    attacking += any(record["action"].get("fire") or [])
                me = (record.get("obs") or {}).get("self") or {}
                armed_ticks += sum(w is not None for w in me.get("weapons") or []) > 1
                decision = record.get("decision") or {}
                modes[str(decision.get("mode", "unknown"))] += 1
                learning = decision.get("learning") or {}
                reasons[str(learning.get("reason", "unknown"))] += 1
                opportunities += learning.get("reason") == "engagement"
                observation = record.get("obs") or {}
                loot_seen += bool(observation.get("pickups") or observation.get("cubes"))
                tick = record.get("tick")
                stride = ((header or {}).get("config") or {}).get("match", {}).get("decide_every", 2)
                if (learning.get("credited") and previous_arm and previous_tick is not None
                        and tick == previous_tick + stride):
                    # Feedback arrives with the next observation. Assign it to
                    # the preceding recorded action, even when the arm changes.
                    arm_counts[previous_arm] += 1
                    arm_rewards[previous_arm] += learning.get("reward", 0.)
                previous_arm = learning.get("arm") if learning.get("reason") == "engagement" else None
                previous_tick = tick
                outcome = record.get("outcome")
                if outcome is not None:
                    # Local arena transitions include the final post-action events.
                    # Live referee logs expose only events in the next observation.
                    applied_outcomes += 1
                    hits += outcome.get("damage_dealt", 0)
                    damage += outcome.get("damage_taken", 0)
                observed_events = outcome.get("events", []) if outcome is not None else record.get("events")
                for event in observed_events or []:
                    kind = event.get("type")
                    if kind:
                        events[kind] += 1
                    if outcome is None and kind == "hit":
                        hits += event.get("amount", 0)
                    elif outcome is None and kind == "damaged":
                        damage += event.get("amount", 0)
            elif tag == "end":
                end = record
    if (header is None or end is None or end.get("end_received") is False
            or not isinstance(end.get("place"), (int, float)) or end["place"] < 1):
        raise ValueError(f"Incomplete match trace in {path}")
    signal = dict(ticks=ticks, attacking=attacking, armed_ticks=armed_ticks, modes=dict(modes),
                  events=dict(events), dealt=hits, taken=damage, dropped=end.get("dropped_ticks", 0),
                  place=end.get("place"), kills=end.get("kills"),
                  arm_counts=dict(arm_counts), arm_rewards=dict(arm_rewards),
                  engagement_opportunities=opportunities, loot_visible_ticks=loot_seen,
                  learning_reasons=dict(reasons), action_digest=action_hash.hexdigest(),
                  simulator_transitions=applied_outcomes)
    meta = header.get("metadata") or {}
    signal["source"] = meta.get("source")
    signal["seed"] = meta.get("seed", header.get("seed"))
    if compress and path.suffix != ".gz":
        compressed = path.with_suffix(path.suffix + ".gz")
        with path.open("rb") as source, gzip.open(compressed, "wb", compresslevel=1) as target:
            while data := source.read(256 * 1024):
                target.write(data)
        path.unlink()
        path = compressed
    return signal, path


def make_splits(seed, train, validation, test):
    # All episodes have new local seeds. A seed never crosses a split.
    values = random.Random(seed).sample(range(1, 2**31 - 1), train + validation + test)
    return {"train": values[:train], "validation": values[train:train + validation],
            "test": values[train + validation:]}


def paired(reference, candidate):
    """Compare identical seed/scenario pairs and count independent seed wins."""
    by_seed, by_scenario = defaultdict(list), defaultdict(list)
    differences = []
    changed = comparable = 0
    for a, b in zip(reference, candidate, strict=True):
        if (a["seed"], a["scenario"]) != (b["seed"], b["scenario"]):
            raise ValueError("Mismatched evaluation episodes")
        digests = [(r.get("telemetry") or {}).get("action_digest") for r in (a, b)]
        if all(digests):
            comparable += 1
            changed += digests[0] != digests[1]
        delta = b["score"] - a["score"]
        by_seed[a["seed"]].append(delta)
        by_scenario[a["scenario"]].append(delta)
        differences.append(delta)
    seed_means = [statistics.mean(ds) for ds in by_seed.values()]
    positives = sum(d > EPSILON for d in seed_means)
    negatives = sum(d < -EPSILON for d in seed_means)
    improvement = statistics.mean(differences)
    return {"baseline": statistics.mean(r["score"] for r in reference),
            "candidate": statistics.mean(r["score"] for r in candidate),
            "delta": improvement, "pairs": len(differences),
            "action_comparable_pairs": comparable, "changed_action_pairs": changed,
            "coverage": ("behavior_changed" if changed else "unexercised" if comparable else "unknown"),
            "improved_pairs": sum(d > 0 for d in differences),
            "regressed_pairs": sum(d < 0 for d in differences),
            "improved_seeds": positives, "regressed_seeds": negatives,
            "scenario_deltas": {k: statistics.mean(v) for k, v in by_scenario.items()},
            "consistent_gain": improvement > EPSILON and positives > negatives
                               and positives >= max(2, math.ceil(len(by_seed) / 2))}


def suggestions(policy, rows, external, round_index):
    evidence = [row["telemetry"] for row in rows] + list(external)
    totals = Counter()
    modes, arm_counts, arm_rewards, reasons = Counter(), Counter(), Counter(), Counter()
    for log in evidence:
        for k in ("ticks", "attacking", "armed_ticks", "taken", "dealt"):
            totals[k] += log[k]
        for key in ("engagement_opportunities", "loot_visible_ticks"):
            totals[key] += log.get(key, 0)
        modes.update(log["modes"])
        reasons.update(log.get("learning_reasons", {}))
        arm_counts.update(log.get("arm_counts", {}))
        arm_rewards.update(log.get("arm_rewards", {}))
    threatened = totals["taken"] > totals["dealt"]
    active = totals["attacking"] / max(1, totals["ticks"])
    retreat_share = sum(modes[mode] for mode in ("evade", "retreat")) / max(1, totals["ticks"])
    # Each round starts from the most recent promoted policy. Direction follows
    # observed damage trades and actions; a counterproposal tests that inference.
    avoid = 1 if threatened else -1
    arm_means = {k: arm_rewards[k] / n for k, n in arm_counts.items() if n}
    alternatives = [v for k, v in arm_means.items() if k != "space" and arm_counts[k] >= 20]
    if arm_counts["space"] >= 20 and alternatives:
        avoid = 1 if arm_means["space"] >= statistics.mean(alternatives) else -1
    directions = {"engage_range_m": 1 if threatened or active < .09 else -1,
                  "retreat_bias": avoid, "pressure_gain": 1 if threatened and retreat_share < .55 else -1}
    armed_fraction = totals["armed_ticks"] / max(1, totals["ticks"])
    if "loot_priority" in policy:
        directions["loot_priority"] = 1 if armed_fraction < .65 else -1
    diagnostics = {"damage_in": totals["taken"], "damage_out": totals["dealt"],
                   "firing_fraction": active, "retreat_fraction": retreat_share,
                   "armed_fraction": armed_fraction, "loot_visible_ticks": totals["loot_visible_ticks"],
                   "engagement_opportunities": totals["engagement_opportunities"],
                   "learning_reasons": dict(reasons),
                   "credited_arm_counts": dict(arm_counts), "mean_credited_reward": arm_means}
    candidates = {}
    def add(name, signs):
        trial = dict(policy)
        for key, sign in signs.items():
            low, high = POLICY_BOUNDS[key]
            value = policy[key] + sign * (high - low) * max(.10, .30 / math.sqrt(round_index + 1))
            trial[key] = round(min(high, max(low, value)), 4)
        validate_policy(trial)
        if trial != policy:
            candidates.setdefault(json_text(trial), (name, trial))

    add("observed-damage-response", directions)
    add("opposite-response", {k: -v for k, v in directions.items()})
    for key, direction in directions.items():
        add("single-variable-" + key, {key: direction})
    if "loot_priority" in policy:
        add("early-equipment", {"loot_priority": 2.0, "retreat_bias": .4})
    return list(candidates.values()), diagnostics


class Evaluation:
    def __init__(self, arena, directory, scenarios):
        self.arena = arena
        self.directory = directory
        self.scenarios = scenarios
        self.trace_dir = directory / "traces"
        self.trace_dir.mkdir()
        self.cache = {}

    def episodes(self, policy, seeds, split):
        policy_id = hashlib.sha256(json_text(policy).encode()).hexdigest()[:16]
        rows = []
        for seed in seeds:
            for scenario in self.scenarios:
                key = (policy_id, seed, scenario)
                if key not in self.cache:
                    self.cache[key] = self.episode(policy, policy_id, seed, scenario, split)
                rows.append(self.cache[key])
        return rows

    def episode(self, policy, policy_id, seed, scenario, split):
        recorder = None
        applied_decisions = 0
        def factory(hello):
            nonlocal recorder
            agent = Bot(hello, policy=dict(policy))
            metadata = {**getattr(agent, "match_metadata", {}), "source": "training.arena", "scenario": scenario, "seed": seed,
                        "split": split, "policy_id": policy_id, "policy": policy}
            recorder = MatchRecorder(hello, "Astra", metadata=metadata, output_dir=self.trace_dir, lossless=True)
            return agent

        def record(obs, action, info):
            nonlocal applied_decisions
            applied_decisions += 1
            outcome = {k: info[k] for k in ("hp_after", "damage_dealt", "damage_taken", "zone_damage",
                                            "kills", "cubes", "events") if k in info}
            recorder.record(obs, action, decision=info.get("decision"), decision_ms=info.get("decision_ms"),
                            on_time=info.get("on_time", True), outcome=outcome)

        end = None
        try:
            result = self.arena.run(factory, seed, scenario, trace=record)
            end = {"type": "end", "place": result["place_proxy"], "kills": result["kills"]}
        finally:
            if recorder is not None:
                recorder.close(end)
        if recorder is None or not recorder.path:
            raise RuntimeError("Local training could not write its match telemetry")
        telemetry, trace = read_trace(Path(recorder.path), compress=True)
        if (not applied_decisions or telemetry["dropped"] or telemetry["ticks"] != applied_decisions
                or telemetry["simulator_transitions"] != applied_decisions):
            raise RuntimeError(f"Incomplete local trajectory in {trace} ({applied_decisions} applied decisions, "
                               f'{telemetry["ticks"]} recorded ticks, {telemetry["dropped"]} dropped).')
        if telemetry["place"] != result["place_proxy"]:
            raise RuntimeError(f"Local outcome did not match the recorded match in {trace}")
        row = {**result, "policy_id": policy_id, "split": split, "seed": seed, "scenario": scenario,
               "telemetry": telemetry, "trace": str(trace.relative_to(self.directory))}
        with (self.directory / "episodes.jsonl").open("a") as stream:
            stream.write(json_text(row) + "\n")
        return row


def tune(args):
    directory = args.output_dir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise ValueError(f"Output directory already contains files: {directory}")
    splits = make_splits(args.seed, args.train_seeds, args.validation_seeds, args.test_seeds)
    original = dict(load_policy(args.policy))
    validate_policy(original)
    current = dict(original)
    external = [read_trace(path)[0] for path in args.match_log]
    protected_seeds = set(splits["test"] + splits["validation"])
    if any(log["source"] == "training.arena" and log["seed"] in protected_seeds for log in external):
        raise ValueError("An external local trace overlaps this run's validation or test seeds.")
    evaluation = Evaluation(Arena(args.kit), directory, args.scenarios)
    sources = (list(ROOT.glob("*.py")) + [Path(__file__), ROOT / "training" / "arena.py"])
    fingerprints = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in sources}
    fingerprints["kit/check/stream.jsonl.gz"] = hashlib.sha256(
        (args.kit / "check/stream.jsonl.gz").read_bytes()).hexdigest()
    report = {"source": "local synthetic matches", "source_sha256": fingerprints, "score": "4 - place_proxy, maximum 3",
              "splits": splits, "seed": args.seed, "scenarios": list(args.scenarios),
              "input_policy": original, "policy_path": str(args.policy),
              "external_telemetry": [{"path": str(p), "summary": s} for p, s in zip(args.match_log, external)],
              "rounds": []}
    for i in range(args.rounds):
        base = evaluation.episodes(current, splits["train"], "train")
        proposals, diagnostics = suggestions(current, base, external, i)
        record = {"round": i + 1, "incumbent": dict(current), "diagnostics": diagnostics, "proposals": []}
        eligible = []
        for name, candidate in proposals:
            trial = evaluation.episodes(candidate, splits["train"], "train")
            train = paired(base, trial)
            record["proposals"].append({"name": name, "policy": candidate, "train": train})
            if train["consistent_gain"]:
                eligible.append((train["delta"], name, candidate))
        record["promoted"] = False
        if eligible:
            _, name, candidate = max(eligible, key=lambda entry: entry[0])
            validation = paired(evaluation.episodes(current, splits["validation"], "validation"),
                                evaluation.episodes(candidate, splits["validation"], "validation"))
            record.update(challenger=name, validation=validation, promoted=validation["consistent_gain"])
            if record["promoted"]:
                current = candidate
        report["rounds"].append(record)
        atomic_json(directory / "report.json", report)
        print(f'Round {i+1}/{args.rounds} evaluated {len(proposals)} proposals; promoted={record["promoted"]}', flush=True)

    # View this split only once per run, after deciding on one finalist.
    final = paired(evaluation.episodes(original, splits["test"], "test"),
                   evaluation.episodes(current, splits["test"], "test"))
    accepted = current != original and final["consistent_gain"]
    decision = "accepted" if accepted else "incumbent_retained"
    changes = sum(p["train"]["changed_action_pairs"] for round_ in report["rounds"] for p in round_["proposals"])
    final["distinct_finalist"] = current != original
    report.update(finalist=current, final_test=final, decision=decision,
                  training_coverage="behavior_changed" if changes else "unexercised",
                  selected_policy=current if accepted else original, policy_applied=False)
    logs = [row["telemetry"] for row in evaluation.cache.values()]
    report["recording"] = {"episodes": len(logs), "decisions": sum(row["ticks"] for row in logs),
                           "dropped": sum(row["dropped"] for row in logs),
                           "engagement_opportunities": sum(row["engagement_opportunities"] for row in logs)}
    if args.apply and accepted:
        # A directory lock serializes compare-and-replace across concurrent local
        # trainers, including when the destination file changes inode on rename.
        import fcntl
        parent_fd = os.open(args.policy.parent, os.O_RDONLY)
        try:
            fcntl.flock(parent_fd, fcntl.LOCK_EX)
            if dict(load_policy(args.policy)) == original:
                atomic_json(args.policy, current)
                report["policy_applied"] = True
            else:
                report["apply_status"] = "skipped_input_policy_changed"
        finally:
            os.close(parent_fd)
    atomic_json(directory / "report.json", report)
    print(f'Training coverage: {report["training_coverage"]}.', flush=True)
    print(f'Final held-out local score {final["baseline"]:.3f} -> {final["candidate"]:.3f}; '
          f'{decision}; applied={report["policy_applied"]}. Report: {directory / "report.json"}', flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", required=True, type=Path, help="Extracted official starter kit")
    parser.add_argument("--output-dir", required=True, type=Path, help="Empty run directory for reports and match traces")
    parser.add_argument("--policy", type=Path, default=ROOT / "policy.json")
    parser.add_argument("--seed", type=int, default=582913, help="Reproducible local split generator seed")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--train-seeds", type=int, default=4)
    parser.add_argument("--validation-seeds", type=int, default=4)
    parser.add_argument("--test-seeds", type=int, default=6)
    parser.add_argument("--scenarios", nargs="+", choices=SCENARIOS, default=SCENARIOS)
    parser.add_argument("--match-log", type=Path, action="append", default=[],
                        help="Additional completed match JSONL[.gz] for proposal diagnostics only")
    parser.add_argument("--apply", action="store_true", help="Atomically replace the input policy after promotion gates pass")
    args = parser.parse_args()
    if args.rounds < 1 or min(args.train_seeds, args.validation_seeds, args.test_seeds) < 2:
        parser.error("Use at least one tuning round and at least two seeds per split.")
    if len(set(args.scenarios)) != len(args.scenarios):
        parser.error("Scenarios must be unique.")
    try:
        tune(args)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Training failed: {exc}\n")


if __name__ == "__main__":
    main()
