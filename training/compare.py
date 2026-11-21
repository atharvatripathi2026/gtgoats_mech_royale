r"""Compare two bot worktrees on the same local scenarios and seeds.

    python3 -m training.compare --baseline /tmp/base --candidate /tmp/trial \
        --kit /tmp/mech-kit --seed-start 41001 --seeds 8 \
        --scenarios forage pursuit crossfire rotation --maps generated campus \
        --output-dir /tmp/paired-run --traces

Use --squad16 to run the optional 16-mech campus diagnostic instead.
This compares relative behaviors only. Its absolute scores are not calibrated to
the official scorer, and its ordering is uncertain for closely matched bots.

Each worktree must supply bot.py with Bot(hello). Each side has its own Python
process, working directory, source imports and default policy.json. The arena,
geometry implementation and recorder always come from the checkout running this
command. Use trusted worktrees. The comparison evaluates their code locally.

Per-game outcomes are in baseline/episodes.jsonl and candidate/episodes.jsonl.
report.json summarizes local placement deltas. --traces also saves a complete
compressed JSONL trajectory for each game alongside the outcome files. A point is one place in
the chosen simulation (4 or 16 minus local place). Official scores come from Builders.
"""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SIDES = ("baseline", "candidate")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(worktree):
    """Identify both committed controllers and local experiments."""
    source = list(worktree.glob("*.py"))
    if (worktree / "policy.json").is_file():
        source.append(worktree / "policy.json")
    result = {"worktree": str(worktree), "root_source_sha256": {p.name: digest(p) for p in sorted(source)}}
    git = ["git", "-C", str(worktree)]
    top = subprocess.run(git + ["rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode == 0 and Path(top.stdout.strip()).resolve() == worktree:
        result["commit"] = subprocess.check_output(git + ["rev-parse", "HEAD"], text=True).strip()
        result["dirty"] = bool(subprocess.check_output(git + ["status", "--porcelain"], text=True))
    return result


def json_line(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def record_game(arena, factory, seed, scenario, directory, metadata, recorder_class, read_trace):
    recorder = None
    ticks = 0
    end = None

    def make(hello):
        nonlocal recorder
        bot = factory(hello)
        recorder = recorder_class(hello, getattr(bot, "name", "bot"), output_dir=directory,
                                  metadata={**getattr(bot, "match_metadata", {}), **metadata}, lossless=True)
        return bot

    def record(obs, action, info):
        nonlocal ticks
        ticks += 1
        outcome = {k: info[k] for k in ("hp_after", "damage_dealt", "damage_taken", "zone_damage",
                                        "kills", "cubes", "events") if k in info}
        recorder.record(obs, action, decision=info.get("decision"), decision_ms=info.get("decision_ms"),
                        on_time=info.get("on_time", True), outcome=outcome)

    try:
        row = arena.run(make, seed, scenario, trace=record)
        end = {"type": "end", "place": row["place_proxy"], "kills": row["kills"]}
    finally:
        if recorder:
            recorder.close(end)
    if not recorder or not recorder.path:
        raise RuntimeError("The recorder could not save a local trajectory.")
    telemetry, path = read_trace(Path(recorder.path), compress=True)
    if (not ticks or telemetry["ticks"] != ticks or telemetry["simulator_transitions"] != ticks
            or telemetry["dropped"] or telemetry["place"] != row["place_proxy"]):
        raise RuntimeError(f"Incomplete local trajectory in {path}")
    row["trace"] = str(path.relative_to(directory.parent))
    row["trace_ticks"] = ticks
    return row


def worker(args):
    # The worker starts via -I, with neither the script's directory nor the
    # caller's PYTHONPATH on sys.path. Capture all required engine-side classes
    # before allowing the policy to import any modules with overlapping names.
    sys.path.insert(0, str(ROOT))
    from training.arena import Arena
    if args.squad16:
        from training.squad16 import SquadArena
    from recorder import MatchRecorder
    from training.tune import read_trace

    sys.path.pop(0)
    for name, module in list(sys.modules.items()):
        filename = getattr(module, "__file__", None)
        if filename and Path(filename).resolve().is_relative_to(ROOT) and name != "__main__":
            del sys.modules[name]

    worktree = getattr(args, args.worker)
    sys.path.insert(0, str(worktree))
    module = importlib.import_module("bot")
    if Path(module.__file__).resolve() != (worktree / "bot.py").resolve():
        raise ValueError(f"Expected bot.py under {worktree}")
    factory = module.Bot
    directory = args.output_dir / args.worker
    directory.mkdir()
    traces = directory / "traces"
    if args.traces:
        traces.mkdir()
    with (directory / "episodes.jsonl").open("x", encoding="utf-8") as stream:
        for domain in args.maps:
            arena = SquadArena(args.kit) if args.squad16 else Arena(args.kit, campus=domain == "campus")
            try:
                for seed in range(args.seed_start, args.seed_start + args.seeds):
                    for scenario in args.scenarios:
                        if args.traces:
                            metadata = {"source": "training.arena", "scenario": scenario, "seed": seed,
                                        "map_domain": domain, "comparison_side": args.worker}
                            row = record_game(arena, factory, seed, scenario, traces, metadata,
                                              MatchRecorder, read_trace)
                        else:
                            row = arena.run(factory, seed, scenario)
                        stream.write(json_line({**row, "map_domain": domain}) + "\n")
                        stream.flush()
            finally:
                arena.close()


def read_rows(path, players=4):
    result = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            key = (row["map_domain"], row["seed"], row["scenario"])
            if key in result or not (1 <= row["place_proxy"] <= players and row["score"] == players - row["place_proxy"]):
                raise ValueError(f"Invalid or duplicate outcome in {path}")
            result[key] = row
    return result


def contrast(keys, baseline, candidate):
    differences = [candidate[k]["score"] - baseline[k]["score"] for k in keys]
    return {"pairs": len(keys),
            "baseline_points": statistics.mean(baseline[k]["score"] for k in keys),
            "candidate_points": statistics.mean(candidate[k]["score"] for k in keys),
            "mean_points_delta": statistics.mean(differences),
            "improved": sum(d > 0 for d in differences), "tied": differences.count(0),
            "regressed": sum(d < 0 for d in differences)}


def compare(args):
    from training.arena import SCENARIOS

    allowed_scenarios = ("squad16",) if args.squad16 else SCENARIOS
    if args.seeds < 1 or not all(s in allowed_scenarios for s in args.scenarios):
        raise ValueError(f"Use a positive seed count and scenarios from {', '.join(allowed_scenarios)}.")
    if len(set(args.maps)) != len(args.maps) or len(set(args.scenarios)) != len(args.scenarios):
        raise ValueError("Specify each map domain and each scenario only once.")
    for worktree in (args.baseline, args.candidate):
        if not (worktree / "bot.py").is_file():
            raise ValueError(f"Missing bot.py in {worktree}")
    if not (args.kit / "check" / "stream.jsonl.gz").is_file():
        raise ValueError(f"Missing kit observation stream under {args.kit}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if any(args.output_dir.iterdir()):
        raise ValueError(f"Choose an empty output directory: {args.output_dir}")
    # Two scheduled invocations cannot append different runs to the same path.
    lock = args.output_dir / ".running"
    with lock.open("x"):
        pass
    try:
        before = {side: snapshot(getattr(args, side)) for side in SIDES}
        shared = {"arena": ROOT / "training/arena.py", "geometry": ROOT / "navigation.py",
                  "kit_stream": args.kit / "check/stream.jsonl.gz"}
        if args.squad16:
            shared["squad16"] = ROOT / "training/squad16.py"
        if "campus" in args.maps:
            shared.update(world=args.kit / "arena/v2/world.json", terrain=args.kit / "arena/v2/terrain.i16")
        pinned = {name: digest(path) for name, path in shared.items()}
        for side in SIDES:
            command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--worker", side,
                       "--baseline", str(args.baseline), "--candidate", str(args.candidate),
                       "--kit", str(args.kit), "--seed-start", str(args.seed_start),
                       "--seeds", str(args.seeds), "--scenarios", *args.scenarios,
                       "--maps", *args.maps, "--output-dir", str(args.output_dir)]
            if args.traces:
                command.append("--traces")
            if args.squad16:
                command.append("--squad16")
            subprocess.run(command, cwd=getattr(args, side), check=True)
        players = 16 if args.squad16 else 4
        rows = {side: read_rows(args.output_dir / side / "episodes.jsonl", players) for side in SIDES}
        expected = [(domain, seed, scenario) for domain in args.maps
                    for seed in range(args.seed_start, args.seed_start + args.seeds) for scenario in args.scenarios]
        if any(set(side_rows) != set(expected) for side_rows in rows.values()):
            raise ValueError("The paired comparison is missing some of the requested games.")
        for side in SIDES:
            if snapshot(getattr(args, side)) != before[side]:
                raise ValueError(f"The {side} worktree changed during evaluation; results remain in {args.output_dir}.")
        if pinned != {name: digest(path) for name, path in shared.items()}:
            raise ValueError("The shared arena or kit inputs changed during evaluation.")
        score_label = ("Local 16-mech placement points (16 minus local place, maximum 15)" if args.squad16
                       else "Local four-mech placement points: 4 minus local place, maximum 3")
        report = {"score": score_label,
                  "seed_start": args.seed_start, "seed_count": args.seeds,
                  "scenarios": args.scenarios, "maps": args.maps, "snapshots": before,
                  "shared_input_sha256": pinned,
                  "traces": args.traces, "episode_files": {s: f"{s}/episodes.jsonl" for s in SIDES},
                  "overall": contrast(expected, rows["baseline"], rows["candidate"]), "by_map_and_scenario": {}}
        for domain in args.maps:
            report["by_map_and_scenario"][domain] = {
                sc: contrast([k for k in expected if k[0] == domain and k[2] == sc],
                             rows["baseline"], rows["candidate"]) for sc in args.scenarios}
        if args.squad16:
            report["interpretation"] = ("Diagnostic only. Absolute points are not calibrated to official practice. "
                                        "Small paired gains may reverse on official house opponents.")
        target = args.output_dir / "report.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        os.replace(temporary, target)
        print(f"{len(expected)} paired games. Mean candidate minus baseline "
              f"{report['overall']['mean_points_delta']:+.3f}. Report {target}")
    finally:
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--baseline", required=True, type=Path, help="Baseline worktree containing bot.py")
    parser.add_argument("--candidate", required=True, type=Path, help="Candidate worktree containing bot.py")
    parser.add_argument("--kit", required=True, type=Path, help="Extracted official mechfight kit")
    parser.add_argument("--output-dir", required=True, type=Path, help="Empty directory for this comparison")
    parser.add_argument("--seed-start", type=int, default=41001, help="First matched simulation seed")
    parser.add_argument("--seeds", type=int, default=8, help="Number of consecutive seeds per scenario and map")
    parser.add_argument("--squad16", action="store_true", help="Optional 16-mech cooperative-squad campus diagnostic")
    parser.add_argument("--scenarios", nargs="+")
    parser.add_argument("--maps", nargs="+", choices=("generated", "campus"))
    parser.add_argument("--traces", action="store_true", help="Record and verify complete gzip JSONL trajectories")
    parser.add_argument("--worker", choices=SIDES, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.squad16:
        if args.scenarios not in (None, ["squad16"]) or args.maps not in (None, ["campus"]):
            parser.error("--squad16 uses one campus scenario; run four-mech comparisons separately.")
        args.maps = ["campus"]
        args.scenarios = ["squad16"]
    else:
        args.maps = args.maps or ["generated"]
        args.scenarios = args.scenarios or ["forage", "pursuit", "crossfire", "rotation"]
    for key in ("baseline", "candidate", "kit", "output_dir"):
        setattr(args, key, getattr(args, key).expanduser().resolve())
    try:
        if args.worker:
            worker(args)
        else:
            compare(args)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Comparison failed: {exc}\n")


if __name__ == "__main__":
    main()
