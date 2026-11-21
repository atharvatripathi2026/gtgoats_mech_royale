"""Inspect recorded decisions and outcomes in one match without loading it into memory."""
import argparse
from collections import Counter, defaultdict, deque
import gzip
import json
from pathlib import Path


def review(path, last=8):
    """Summarize the observed events, retaining the final decision window."""
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    tail = deque(maxlen=last)
    modes = defaultdict(lambda: {"decisions": 0, "damage_received": 0, "damage_dealt": 0})
    events = Counter()
    previous_mode = "before_first_action"
    first_tick = last_tick = None
    ticks = fallbacks = skipped = 0
    seen_event_ticks = set()
    header, end = {}, {}
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            kind = row.get("type")
            if kind == "header":
                header = row
                continue
            if kind == "end":
                end = row
                continue
            if kind != "tick":
                continue
            ticks += 1
            first_tick = row["tick"] if first_tick is None else first_tick
            last_tick = row["tick"]
            obs = row.get("obs") or {}
            decision = row.get("decision") or {}
            mode = decision.get("mode", "unknown")
            modes[mode]["decisions"] += 1
            outcome = row.get("outcome")
            observed = (outcome.get("events", []) if outcome is not None
                        else row.get("events", obs.get("events", [])))
            event_mode = mode if outcome is not None else previous_mode
            # The kit deliberately repeats prior ticks in some queue bursts.
            for event in ([] if last_tick in seen_event_ticks else observed):
                et = event.get("type", "other")
                events[et] += 1
                if et == "damaged":
                    modes[event_mode]["damage_received"] += event.get("amount", 0)
                elif et == "hit":
                    modes[event_mode]["damage_dealt"] += event.get("amount", 0)
            # Events arrive in the next observation. The previous decision is
            # temporal context, not proof it caused damage from a delayed shot.
            seen_event_ticks.add(last_tick)
            if row.get("action") is not None:
                previous_mode = mode
                fallbacks += bool(row.get("fallback"))
            else:
                skipped += 1
            tail.append({"tick": last_tick, "t": row.get("t"), "hp": obs.get("self", {}).get("hp"),
                         "mode": mode, "reason": decision.get("reason"), "goal": decision.get("goal"),
                         "learning": decision.get("learning"), "action": row.get("action"),
                         "events": observed, "outcome": outcome})
    return {
        "match_id": header.get("match_id"), "metadata": header.get("metadata", {}),
        "slot": header.get("slot"), "first_tick": first_tick, "last_tick": last_tick,
        "records": ticks, "skipped": skipped, "fallbacks": fallbacks, "events": dict(events), "by_mode": dict(modes),
        "end_received": end.get("end_received", False), "place": end.get("place"), "kills": end.get("kills"),
        "recorder_dropped_ticks": end.get("dropped_ticks"), "last_observed_hp": end.get("last_observed_hp"),
        "last_decisions": list(tail),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("match", type=Path, help="one recorded .jsonl or .jsonl.gz match")
    parser.add_argument("--last", type=int, default=8, help="number of final decisions to display")
    args = parser.parse_args()
    if args.last < 0:
        parser.error("--last must be zero or greater")
    try:
        print(json.dumps(review(args.match, args.last), indent=2, ensure_ascii=False))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Could not read {args.match}: {error}\n")


if __name__ == "__main__":
    main()
