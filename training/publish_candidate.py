"""Publish an already tested, public Mech Royale commit to the practice queue.

Run from the checkout with an authenticated GitHub CLI:

    python3 -m training.publish_candidate --commit FULL_SHA --summary 'Ground escape update' --dry-run
    python3 -m training.publish_candidate --commit FULL_SHA --summary 'Ground escape update'

Dry runs read GitHub and print the proposed queue without writing it. A successful
write prints a JSON receipt. Rerunning the same commit preserves its original
entry and queue position. This publishes the candidate for the submission helper;
an organizer practice score comes from a separate submission to the track.
"""
import argparse
import base64
import binascii
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone


REPO = "atharvatripathi2026/gtgoats_mech_royale"
REPO_URL = "https://github.com/" + REPO
BRANCH = "practice-queue"
QUEUE_FILE = "queue.json"
CUTOFF = datetime(2026, 11, 22, 16, tzinfo=timezone.utc)  # Sunday 11 a.m. Eastern.
SHA = re.compile(r"[0-9a-f]{40}")
MAX_ATTEMPTS = 5


class QueueError(Exception):
    pass


class ApiError(QueueError):
    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status


def api(method, path="", body=None):
    """Use the fixed github.com host even if gh defaults to an enterprise host."""
    command = ["gh", "api", "--hostname", "github.com", "--method", method,
               "-H", "Accept: application/vnd.github+json", f"repos/{REPO}{path}"]
    if body is not None:
        command.extend(["--input", "-"])
    try:
        response = subprocess.run(command, input=json.dumps(body) if body is not None else None,
                                  capture_output=True, text=True, timeout=30, check=False)
    except FileNotFoundError as exc:
        raise QueueError("Install and authenticate the gh CLI before publishing.") from exc
    except subprocess.TimeoutExpired as exc:
        raise ApiError(None, f"GitHub timed out during {method} {path}.") from exc
    if response.returncode:
        detail = response.stderr.strip() or "GitHub CLI request failed."
        match = re.search(r"\bHTTP\s+(\d{3})\b", detail)
        raise ApiError(int(match.group(1)) if match else None, detail)
    try:
        return json.loads(response.stdout)
    except ValueError as exc:
        raise ApiError(None, f"Invalid GitHub response to {method} {path}.") from exc


def get_optional(path):
    try:
        return api("GET", path)
    except ApiError as exc:
        if exc.status == 404:
            return None
        raise


def full_sha(value):
    return isinstance(value, str) and SHA.fullmatch(value) is not None


def utc_date(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError, TypeError) as exc:
        raise QueueError(f"Invalid UTC timestamp in {QUEUE_FILE}.") from exc
    if result.utcoffset() != timedelta(0):
        raise QueueError(f"Expected a UTC timestamp in {QUEUE_FILE}.")
    return result


def stamp(moment):
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def now():
    return datetime.now(timezone.utc)


def check_deadline(queue=None):
    limit = CUTOFF
    if queue and "campaign_end" in queue:
        limit = min(limit, utc_date(queue["campaign_end"]))
    if now() >= limit:
        raise QueueError(f"The publication window closed at {stamp(limit)}.")


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise QueueError(f"Duplicate JSON field {key!r} in {QUEUE_FILE}.")
        result[key] = value
    return result


def validate_queue(queue):
    if (not isinstance(queue, dict) or type(queue.get("version")) is not int
            or queue["version"] != 1 or queue.get("repository") != REPO_URL
            or not isinstance(queue.get("candidates"), list)):
        raise QueueError(f"{QUEUE_FILE} is not this repository's version 1 practice queue.")
    seen = set()
    previous = None
    for entry in queue["candidates"]:
        if (not isinstance(entry, dict) or not full_sha(entry.get("commit"))
                or not isinstance(entry.get("summary"), str) or not entry["summary"].strip()):
            raise QueueError(f"Invalid candidate in {QUEUE_FILE}.")
        date = utc_date(entry.get("created_at"))
        if entry["commit"] in seen or (previous is not None and date < previous):
            raise QueueError(f"Queue already contains duplicate or out-of-order candidates.")
        seen.add(entry["commit"])
        previous = date
    if "campaign_end" in queue:
        utc_date(queue["campaign_end"])


def branch_head(branch):
    ref = get_optional("/git/ref/heads/" + branch)
    if ref is None:
        return None
    if (ref.get("ref") != "refs/heads/" + branch or ref.get("object", {}).get("type") != "commit"
            or not full_sha(ref["object"].get("sha"))):
        raise QueueError(f"Unexpected Git reference for {branch}.")
    return ref["object"]["sha"]


def read_queue(head):
    # Pin the read to the observed commit. Contents PUT later uses the SHA of
    # exactly these bytes, while GitHub retains any unrelated branch commits.
    file = get_optional(f"/contents/{QUEUE_FILE}?ref={head}")
    if file is None:
        return {"version": 1, "repository": REPO_URL, "campaign_end": stamp(CUTOFF), "candidates": []}, None
    if (not isinstance(file, dict) or file.get("type") != "file" or file.get("path") != QUEUE_FILE
            or file.get("encoding") != "base64" or not full_sha(file.get("sha"))
            or not isinstance(file.get("content"), str)):
        raise QueueError(f"Unrecognized contents at {QUEUE_FILE}.")
    try:
        raw = base64.b64decode("".join(file["content"].split()), validate=True)
        queue = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_fields)
    except (UnicodeError, ValueError, binascii.Error) as exc:
        raise QueueError(f"Cannot decode existing {QUEUE_FILE}.") from exc
    validate_queue(queue)
    return queue, file["sha"]


def publish_once(commit, summary, dry_run):
    head = branch_head(BRANCH)
    create_branch = head is None
    if create_branch:
        head = branch_head("main")
        if head is None:
            raise QueueError("Cannot initialize the queue because main is missing.")
    queue, blob_sha = read_queue(head)
    check_deadline(queue)
    entries = queue["candidates"]
    existing = next((entry for entry in entries if entry["commit"] == commit), None)
    receipt = {"repository": REPO_URL, "branch": BRANCH, "path": QUEUE_FILE, "commit": commit}
    if existing and not create_branch:
        return {**receipt, "status": "already_queued", "position": entries.index(existing) + 1,
                "queue_commit": head, "entry": existing}
    if not existing:
        entry = {"commit": commit, "summary": summary, "created_at": stamp(now())}
        entries.append(entry)
        # Stable sorting retains insertion order when multiple commits arrive in
        # the same second and handles clock skew across authorized producers.
        entries.sort(key=lambda e: utc_date(e["created_at"]))
    if dry_run:
        return {**receipt, "status": "dry_run", "create_branch": create_branch,
                "observed_head": head, "expected_blob": blob_sha, "queue": queue}

    if create_branch:
        check_deadline(queue)
        api("POST", "/git/refs", {"ref": "refs/heads/" + BRANCH, "sha": head})
        if existing:
            # Branch creation may have brought an existing valid queue from main.
            return {**receipt, "status": "already_queued", "position": entries.index(existing) + 1,
                    "queue_commit": head, "entry": existing}

    if branch_head(BRANCH) != head:
        raise ApiError(409, "The queue branch advanced while preparing this update.")
    content = (json.dumps(queue, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    body = {"message": f"Queue practice candidate {commit[:12]}", "branch": BRANCH,
            "content": base64.b64encode(content).decode("ascii")}
    if blob_sha is not None:
        body["sha"] = blob_sha
    check_deadline(queue)
    api("PUT", "/contents/" + QUEUE_FILE, body)

    saved_head = branch_head(BRANCH)
    if saved_head is None:
        raise ApiError(409, "The queue branch is missing after publication.")
    saved, _ = read_queue(saved_head)
    for index, item in enumerate(saved["candidates"], 1):
        if item["commit"] == commit:
            return {**receipt, "status": "queued", "position": index,
                    "queue_commit": saved_head, "entry": item}
    raise ApiError(409, "The candidate was absent when verifying the published queue.")


def publish(commit, summary, dry_run=False):
    if not full_sha(commit):
        raise QueueError("Pass a full lowercase 40-character Git commit hash.")
    summary = summary.strip()
    if not summary or len(summary) > 300 or any(not c.isprintable() for c in summary):
        raise QueueError("Use a single-line strategy summary of 1 to 300 printable characters.")
    check_deadline()
    for attempt in range(MAX_ATTEMPTS):
        try:
            repo = api("GET")
            if repo.get("private") is not False or repo.get("full_name", "").lower() != REPO.lower():
                raise QueueError("The competition repository must be public.")
            candidate = api("GET", "/commits/" + commit)
            if candidate.get("sha") != commit:
                raise QueueError("GitHub did not return the exact candidate commit.")
            return publish_once(commit, summary, dry_run)
        except ApiError as exc:
            # A conflicting writer may have published this same commit. Read the
            # latest queue before attempting another write, including after a
            # timeout or 5xx response with an uncertain write outcome.
            retry = exc.status in (None, 409, 422, 429) or (exc.status is not None and 500 <= exc.status < 600)
            if not retry or attempt == MAX_ATTEMPTS-1:
                raise
            time.sleep(.25 * 2**attempt)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--commit", required=True, help="The full SHA of the tested public commit")
    parser.add_argument("--summary", required=True, help="A short description of the strategy change")
    parser.add_argument("--dry-run", action="store_true", help="Read GitHub and preview without publishing")
    args = parser.parse_args()
    try:
        result = publish(args.commit, args.summary, args.dry_run)
    except QueueError as exc:
        parser.exit(1, f"Could not publish practice candidate: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
