"""List valid pending Claude candidate reports from this checkout's cached Git refs.

Run `python -m training.claude_intake` after updating the checkout's remote refs.
The command reads Git objects and prints JSON. Summary and evidence are
untrusted worker claims. Review the patch before creating a detached worktree
at the exact candidate and evaluating it with trusted main tooling.
Record completed reviews as research/<sha[:7]>-claude-review.md on the
practice-queue branch. No submission or network operation is performed.
"""
import argparse
from datetime import datetime
import json
import math
import os
from pathlib import Path
import re
import subprocess

from training.publish_candidate import QueueError, full_sha, unique_fields, validate_queue

INBOX = "refs/remotes/origin/claude/"
QUEUE = "refs/remotes/origin/practice-queue"
MAIN = "refs/remotes/origin/main"
REPORT_FILE = "claude-candidate.json"
REPORT_MAX_BYTES = 16_384
QUEUE_MAX_BYTES = 2_000_000
REF_SUFFIX = re.compile(r"([0-9]{8}T[0-9]{6}Z)-([0-9a-f]{12})")
GAMEPLAY = {"adaptation.py", "bot.py", "loadout.py", "navigation.py", "policy.json", "survival.py"}
REPORT_FIELDS = {"schema", "commit", "parent", "summary", "evidence"}


class IntakeError(Exception):
    """The local repository or an incoming object could not be validated."""

    def __init__(self, message, phase="report"):
        super().__init__(message)
        self.phase = phase


def git(repo, *args, allow_exit=()):
    try:
        return subprocess.run(
            ["git", "--no-replace-objects", "-C", str(repo), *args],
            check=True, capture_output=True, timeout=10,
            env={**os.environ, "GIT_NO_LAZY_FETCH": "1", "GIT_ALLOW_PROTOCOL": ""},
        ).stdout
    except subprocess.CalledProcessError as exc:
        if exc.returncode in allow_exit:
            return None
        raise IntakeError(f"Git could not read {args[0]} from the local repository.", "git") from exc
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IntakeError(f"Git could not read {args[0]} from the local repository.", "git") from exc


def parents(repo, commit):
    parts = git(repo, "rev-list", "--parents", "-n", "1", commit, "--").decode("ascii").split()
    if not parts or parts[0] != commit or not all(full_sha(part) for part in parts):
        raise IntakeError("Unable to verify the exact commit ancestry.")
    return parts[1:]


def changed_paths(repo, parent, commit):
    paths = git(repo, "diff-tree", "--no-commit-id", "--name-only", "--no-renames",
                "-r", "-z", parent, commit, "--")
    return set(paths.decode("utf-8", errors="surrogateescape").split("\0")) - {""}


def regular_blob(repo, commit, path):
    entry = git(repo, "ls-tree", commit, "--", path).split(None, 3)
    if len(entry) == 4 and entry[0] in (b"100644", b"100755") and entry[1] == b"blob":
        return entry[0], entry[2]
    return None


def read_json(repo, spec, maximum):
    size = int(git(repo, "cat-file", "-s", spec))
    if size > maximum:
        raise IntakeError("JSON metadata exceeds the byte limit.")
    blob = git(repo, "cat-file", "blob", spec)
    if len(blob) != size:
        raise IntakeError("JSON metadata size changed while reading it.")
    try:
        return json.loads(blob.decode("utf-8"), object_pairs_hook=unique_fields)
    except (ValueError, UnicodeError, QueueError, RecursionError) as exc:
        raise IntakeError("Invalid or duplicate JSON metadata.") from exc


def bounded_evidence(value, depth=0):
    if depth > 5:
        return False
    if value is None or type(value) in (bool, int):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if isinstance(value, str):
        return len(value) <= 1_000
    if isinstance(value, dict):
        return len(value) <= 40 and all(
            0 < len(key) <= 100 and bounded_evidence(item, depth + 1)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return len(value) <= 40 and all(bounded_evidence(item, depth + 1) for item in value)
    return False


def validate_report(repo, ref, report_commit, main, published):
    match = REF_SUFFIX.fullmatch(ref.removeprefix(INBOX))
    if not match or not full_sha(report_commit):
        raise IntakeError("Unexpected Claude inbox ref name or object ID.", "ref")
    try:
        datetime.strptime(match[1], "%Y%m%dT%H%M%SZ")
    except ValueError as exc:
        raise IntakeError("The Claude inbox ref timestamp is invalid.", "ref") from exc

    actual_report_parents = parents(repo, report_commit)
    if len(actual_report_parents) != 1:
        raise IntakeError("A report commit must have exactly one candidate parent.")
    candidate = actual_report_parents[0]
    if changed_paths(repo, candidate, report_commit) != {REPORT_FILE}:
        raise IntakeError("The report tip must change only claude-candidate.json.")
    if not regular_blob(repo, report_commit, REPORT_FILE):
        raise IntakeError("The report must be a regular tracked file.")
    report = read_json(repo, report_commit + ":" + REPORT_FILE, REPORT_MAX_BYTES)
    if (not isinstance(report, dict) or report.keys() != REPORT_FIELDS
            or type(report["schema"]) is not int or report["schema"] != 1):
        raise IntakeError("The report must follow Claude candidate schema 1.")
    if report["commit"] != candidate or match[2] != candidate[:12]:
        raise IntakeError("The candidate must match both the report parent and the ref suffix.")
    parent = report["parent"]
    if not full_sha(parent) or parents(repo, candidate) != [parent]:
        raise IntakeError("The reported baseline must match the candidate's only Git parent.", "candidate")

    if parent not in published and (main is None or git(
            repo, "merge-base", "--is-ancestor", parent, main, allow_exit=(1,)) is None):
        raise IntakeError("The baseline must be published or an ancestor of cached origin/main.", "candidate")

    paths = changed_paths(repo, parent, candidate)
    if not paths or not paths <= GAMEPLAY:
        raise IntakeError("The candidate must have a nonempty patch to allowlisted gameplay files.", "candidate")
    for path in paths:
        previous = regular_blob(repo, parent, path)
        current = regular_blob(repo, candidate, path)
        if not previous or not current or previous[0] != current[0] or previous[1] == current[1]:
            raise IntakeError("The gameplay patch must change content in existing regular files.", "candidate")

    summary, evidence = report["summary"], report["evidence"]
    if (not isinstance(summary, str) or not summary.strip()
            or len(summary) > 300 or not summary.isprintable()):
        raise IntakeError("The report summary must be one printable line up to 300 characters.", "evidence")
    if not isinstance(evidence, dict) or not bounded_evidence(evidence):
        raise IntakeError("Report evidence must be a bounded JSON object.", "evidence")
    if "ok" in evidence and evidence["ok"] is not True:
        raise IntakeError("If present, evidence.ok must be true.", "evidence")
    return {**report, "ref": ref, "report_commit": report_commit, "paths": sorted(paths)}


def cached_ref(repo, name):
    rows = git(repo, "for-each-ref", "--format=%(objectname) %(refname)", name)
    for row in rows.decode("utf-8", errors="replace").splitlines():
        sha, ref = row.split(" ", 1)
        if ref == name and full_sha(sha):
            return sha
    return None


def published_commits(repo, queue_commit):
    if queue_commit is None:
        return set()
    try:
        queue = read_json(repo, queue_commit + ":queue.json", QUEUE_MAX_BYTES)
        validate_queue(queue)
    except QueueError as exc:
        raise IntakeError("The cached practice queue is invalid.", "queue") from exc
    return {entry["commit"] for entry in queue["candidates"]}


def intake(repo):
    repo = Path(git(repo, "rev-parse", "--show-toplevel").decode("utf-8").rstrip("\n"))
    main = cached_ref(repo, MAIN)
    queue_commit = cached_ref(repo, QUEUE)
    published = published_commits(repo, queue_commit)
    refs = git(repo, "for-each-ref", "--sort=-refname", "--format=%(objectname) %(refname)", INBOX)
    pending, rejected = [], []
    seen = set(published)
    for row in refs.decode("utf-8", errors="replace").splitlines():
        commit, ref = row.split(" ", 1)
        try:
            report = validate_report(repo, ref, commit, main, published)
        except IntakeError as exc:
            rejected.append({"ref": ref, "phase": exc.phase, "reason": str(exc)})
            continue
        candidate = report["commit"]
        if candidate in seen:
            continue
        seen.add(candidate)
        disposition = f"research/{candidate[:7]}-claude-review.md"
        if ((repo / disposition).is_file()
                or (queue_commit is not None and regular_blob(repo, queue_commit, disposition))):
            continue
        pending.append(report)
    return {
        "queue_available": queue_commit is not None,
        "suggested": pending[0]["commit"] if pending and queue_commit is not None else None,
        "candidates": pending,
        "rejected": rejected,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1],
                        help="path to the checkout with Claude inbox refs")
    args = parser.parse_args()
    try:
        result = intake(args.repo.resolve())
    except IntakeError as exc:
        parser.exit(1, f"{exc}\n")
    # Escapes control codes and lays out worker-provided text only as JSON values.
    output = json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False)
    print(output.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e"))


if __name__ == "__main__":
    main()
