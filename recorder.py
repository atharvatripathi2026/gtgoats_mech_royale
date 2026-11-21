"""Bounded match JSONL recording for mechfight/1. All filesystem writes run off the decision loop."""
import json
import math
import os
from pathlib import Path
from queue import Full, Queue
import shutil
import sys
import threading
import uuid


MAX_BYTES = 48 * 1024 * 1024
END_RESERVE = 16 * 1024
SENSOR_LIMITS = {"mechs": 28, "projectiles": 12, "crates": 8, "cubes": 10,
                 "pickups": 8, "sounds": 8, "beams": 4, "drops": 3}


def encode(row):
    return (json.dumps(row, ensure_ascii=True, allow_nan=False, separators=(",", ":")) + "\n").encode("ascii")


def compact_obs(obs, detail=True):
    me = obs.get("self", {})
    state = {k: v for k, v in me.items() if k not in ("stats", "weapons")}
    state["weapons"] = [{k: v for k, v in w.items() if k != "stats"} if w else None
                        for w in me.get("weapons", [])]
    out = {k: obs[k] for k in ("tick", "t", "alive", "zone", "offer") if k in obs}
    out["self"] = state
    counts = {}
    for field, limit in SENSOR_LIMITS.items():
        items = obs.get(field, [])
        if not detail:
            limit = 2 if field == "mechs" else 1 if field == "projectiles" else 0
        if len(items) > limit:
            counts[field] = len(items)
            if limit and items and "pos" in items[0] and "pos" in me:
                items = sorted(items, key=lambda item: math.dist(item["pos"], me["pos"]))
        out[field] = items[:limit]
    if counts:
        out["sensor_counts_before_limit"] = counts
    return out


class MatchRecorder:
    """Each record() snapshots caller-owned data. close() drains accepted lines and writes the terminal row."""

    def __init__(self, hello, name="Astra", metadata=None, output_dir=None, raw=None, lossless=False):
        self.path = None
        self._thread = None
        self._q = Queue(maxsize=128)
        self._closed = False
        self._failed = False
        self._lossless = lossless
        self._bytes = 0
        self._written = 0
        self._ticks = self._skipped = self._fallbacks = self._truncated = 0
        self._last_tick = self._last_hp = self._last_damage = None
        self._death_observed = False
        self._events = {}
        self._damage_in = self._damage_out = 0.
        self._stats_key = None
        self._raw = os.environ.get("MECHFIGHT_LOG_RAW") == "1" if raw is None else raw
        config = hello.get("config", {})
        match = config.get("match", {})
        tick_hz = max(1, match.get("tick_hz", 20))
        self._expected = max(1, math.ceil(match.get("duration_s", 480) * tick_hz /
                                         max(1, match.get("decide_every", 2))) + 2)
        directory = Path(output_dir if output_dir is not None else
                         os.environ.get("MECHFIGHT_LOG_DIR", "/tmp/mechfight-logs"))
        match_id = uuid.uuid4().hex
        header = {"type": "header", "schema": 1, "match_id": match_id, "slot": hello.get("slot"),
                  "seed": hello.get("seed"), "protocol": hello.get("protocol"), "name": name,
                  "config": config, "metadata": metadata or {}, "raw_requested": self._raw,
                  "lossless": self._lossless}
        writer = None
        try:
            directory.mkdir(parents=True, exist_ok=True)
            self._capacity = min(MAX_BYTES, shutil.disk_usage(directory).free - 1024 * 1024)
            if self._capacity < END_RESERVE * 2:
                raise OSError("insufficient free space for a match trace")
            data = encode(header)
            if len(data) > self._capacity - END_RESERVE:
                raise ValueError("match header exceeds trace budget")
            path = directory / f"match-{match_id}.jsonl"
            writer = path.open("xb", buffering=0)
            self._thread = threading.Thread(target=self._write, args=(writer, data), daemon=True)
            self._thread.start()
            if self._thread.ident is None:
                raise RuntimeError("could not start match writer")
            self.path = path
            self._bytes = len(data)
        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            if writer is not None:
                writer.close()
            self._thread = None
            self._error(exc)
            if self._lossless:
                raise RuntimeError(f"cannot open lossless match trace: {exc}") from exc

    def _error(self, exc):
        if not self._failed:
            print(f"match recorder unavailable: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        self._failed = True

    def _write(self, writer, header):
        try:
            with writer:
                self._append(writer, header)
                while True:
                    terminal, data = self._q.get()
                    if terminal:
                        data["dropped_ticks"] = self._ticks - self._written
                        self._append(writer, encode(data))
                        writer.flush()
                        return
                    self._append(writer, data)
                    self._written += 1
        except Exception as exc:
            self._error(exc)

    @staticmethod
    def _append(writer, data):
        # A filesystem can report ENOSPC after writing only part of a line.
        # Roll back just that line so a previously completed prefix is readable.
        start = writer.tell()
        try:
            if writer.write(data) != len(data):
                raise OSError("short write to match trace")
        except OSError:
            writer.truncate(start)
            raise

    def record(self, obs, action, decision=None, decision_ms=None, fallback=None, on_time=None, outcome=None):
        if self._closed or self._failed:
            if self._lossless:
                raise RuntimeError("cannot record to a closed or failed lossless match trace")
            return
        try:
            events = obs.get("events", [])
            self._ticks += 1
            self._last_tick = obs.get("tick")
            me = obs.get("self", {})
            if me.get("hp") is not None:
                self._last_hp = me["hp"]
                self._death_observed |= me["hp"] <= 0
            self._skipped += action is None
            self._fallbacks += bool(fallback and action is not None)
            for event in events:
                kind = event.get("type", "unknown")
                self._events[kind] = self._events.get(kind, 0) + 1
                if kind == "damaged":
                    self._damage_in += event.get("amount", 0)
                    self._last_damage = {"tick": self._last_tick, **event}
                elif kind == "hit":
                    self._damage_out += event.get("amount", 0)
            # The JSON snapshot also protects offline self-play callers that
            # mutate a mech's state as soon as this function returns.
            stats = (me.get("stats"), [w.get("stats") if w else None for w in me.get("weapons", [])])
            # The live stat blocks change with equipment, cubes and upgrades.
            signature = (tuple(me.get("upgrades", [])), me.get("cubes"),
                         tuple(w.get("kind") if w else None for w in me.get("weapons", [])))
            row = {"type": "tick", "tick": self._last_tick, "t": obs.get("t"), "obs": obs if self._raw else compact_obs(obs),
                   "action": action, "decision": decision or {}, "events": events,
                   "decision_ms": decision_ms, "on_time": on_time}
            if fallback:
                row["fallback"] = fallback
            if outcome is not None:
                row["outcome"] = outcome
            if signature != self._stats_key and not self._raw:
                row["stats"] = {"self": stats[0], "weapons": stats[1]}
            available = self._capacity - self._bytes - END_RESERVE
            remaining = max(1, self._expected - self._ticks + 1)
            # Give short raw recordings headroom while protecting space for
            # later decisions in a full-length game. Compact rows share space.
            budget = min(available, max(8192, available - (remaining - 1) * 2048) if self._raw else
                         max(1024, available // remaining))
            data = encode(row)
            if self._lossless:
                budget = available
                if len(data) > budget:
                    raise RuntimeError(f"lossless trace capacity exceeded at tick {self._last_tick}")
            if len(data) > budget:
                self._truncated += 1
                row["obs"] = compact_obs(obs, detail=False)
                row["detail_limited"] = True
                data = encode(row)
            if len(data) > budget:
                # Retain a minimum observation, exact gameplay action and
                # authoritative events before giving up an oversized frame.
                row["obs"] = {k: row["obs"][k] for k in ("alive", "self", "zone") if k in row["obs"]}
                row.pop("stats", None)
                row["decision"] = {k: v for k, v in (decision or {}).items() if k in ("mode", "goal", "target_id")}
                data = encode(row)
            if len(data) <= budget:
                if self._lossless:
                    # Offline simulators may produce a whole game in a few
                    # milliseconds. Wait for room, checking for writer death.
                    while True:
                        if self._failed or not self._thread.is_alive():
                            raise RuntimeError("lossless match writer failed")
                        try:
                            self._q.put((False, data), timeout=.05)
                            break
                        except Full:
                            continue
                else:
                    try:
                        self._q.put_nowait((False, data))
                    except Full:
                        return
                self._bytes += len(data)
                if "stats" in row or self._raw:
                    self._stats_key = signature
        except (TypeError, KeyError, ValueError, AttributeError, ArithmeticError, RecursionError) as exc:
            if self._lossless:
                raise RuntimeError(f"cannot encode lossless record at tick {self._last_tick}: {exc}") from exc
            # A malformed rationale should not suppress an otherwise valid
            # observation or action, including an exception fallback.
            try:
                row = {"type": "tick", "tick": obs.get("tick"), "t": obs.get("t"),
                       "obs": compact_obs(obs, detail=False), "action": action, "events": obs.get("events", []),
                       "decision": {}, "decision_ms": decision_ms, "on_time": on_time,
                       "fallback": fallback, "record_error": type(exc).__name__}
                if outcome is not None:
                    row["outcome"] = outcome
                data = encode(row)
                if len(data) <= self._capacity - self._bytes - END_RESERVE:
                    self._q.put_nowait((False, data))
                    self._bytes += len(data)
            except (TypeError, KeyError, ValueError, AttributeError, ArithmeticError, RecursionError, Full):
                pass

    def close(self, end_msg=None):
        if self._closed:
            return
        self._closed = True
        if self._thread is None:
            return
        end = end_msg or {}
        terminal = {"type": "end", "end_received": end_msg is not None, "place": end.get("place"),
                    "kills": end.get("kills"), "ticks": self._ticks, "last_tick": self._last_tick,
                    "last_observed_hp": self._last_hp, "skipped_ticks": self._skipped,
                    "fallback_ticks": self._fallbacks, "detail_limited_ticks": self._truncated,
                    "event_counts": self._events, "damage_in": self._damage_in, "damage_out": self._damage_out,
                    "last_observed_damage": self._last_damage,
                    "death_observed": True if self._death_observed else None, "server_end": end_msg}
        # The writer may have failed while the queue was full. Never wait on
        # a queue with no consumer. A healthy writer drains before returning.
        while self._thread.is_alive():
            try:
                self._q.put((True, terminal), timeout=.05)
                break
            except Full:
                continue
        self._thread.join()
        if self._lossless and (self._failed or self._written != self._ticks):
            raise RuntimeError(f"incomplete lossless trace {self.path}: {self._written}/{self._ticks} ticks persisted")
