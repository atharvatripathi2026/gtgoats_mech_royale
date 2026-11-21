import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from training.claude_intake import INBOX, MAIN, QUEUE, REPORT_FILE, REPORT_MAX_BYTES, intake
from training.publish_candidate import REPO_URL


class ClaudeIntakeTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.repo = Path(directory.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgSign", "false")
        (self.repo / "bot.py").write_text("# original\n")
        self.base = self.commit("base")
        self.git("update-ref", MAIN, self.base)

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True,
        ).stdout.strip()

    def commit(self, message):
        self.git("add", "--all")
        self.git("commit", "--quiet", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def checkout(self, commit):
        self.git("checkout", "--quiet", "--detach", commit)

    def candidate(self, name, filename="bot.py"):
        self.checkout(self.base)
        (self.repo / filename).write_text(f"# {name}\n")
        return self.commit(name)

    def report(self, candidate, stamp, *, overrides=None, extra_file=False, raw=None):
        self.checkout(candidate)
        report = {
            "schema": 1,
            "commit": candidate,
            "parent": self.base,
            "summary": "Read-only <report> & $(touch SHOULD_NOT_EXIST)",
            "evidence": {"count": 300, "notes": ["\x1b[31m", "not a command"]},
        }
        report.update(overrides or {})
        (self.repo / REPORT_FILE).write_text(raw if raw is not None else json.dumps(report))
        if extra_file:
            (self.repo / "bot.py").write_text("# changed by the report\n")
        exact = self.commit("report")
        ref = f"{INBOX}{stamp}-{candidate[:12]}"
        self.git("update-ref", ref, exact)
        return ref

    def queue(self, *commits, reviewed=()):
        self.checkout(self.base)
        queue = {
            "version": 1,
            "repository": REPO_URL,
            "candidates": [
                {"commit": sha, "summary": "Already published", "created_at": "2026-11-21T01:00:00Z"}
                for sha in commits
            ],
        }
        (self.repo / "queue.json").write_text(json.dumps(queue))
        for sha in reviewed:
            dispositions = self.repo / "research"
            dispositions.mkdir(exist_ok=True)
            (dispositions / f"{sha[:7]}-claude-review.md").write_text("reviewed")
        self.git("update-ref", QUEUE, self.commit("cached queue"))

    def test_selects_newest_unique_pending_and_skips_published_or_reviewed(self):
        old = self.candidate("old")
        new = self.candidate("new")
        published = self.candidate("published")
        reviewed = self.candidate("reviewed")
        self.report(old, "20261121T010000Z")
        self.report(new, "20261121T010100Z")
        newest = self.report(new, "20261121T010200Z")
        self.report(published, "20261121T010300Z")
        self.report(reviewed, "20261121T010400Z")
        self.queue(published, reviewed=[reviewed])
        self.checkout(self.base)
        result = intake(self.repo)
        self.assertTrue(result["queue_available"])
        self.assertEqual(result["suggested"], new)
        self.assertEqual([entry["commit"] for entry in result["candidates"]], [new, old])
        self.assertEqual(result["candidates"][0]["ref"], newest)
        self.assertEqual(result["candidates"][0]["paths"], ["bot.py"])
        self.assertEqual(result["rejected"], [])

    def test_rejects_extraneous_report_changes_wrong_ancestry_and_disallowed_gameplay(self):
        candidate = self.candidate("ordinary")
        forbidden = self.candidate("report injection", "README.md")
        refs = [
            self.report(candidate, "20261121T010000Z", extra_file=True),
            self.report(candidate, "20261121T010010Z", overrides={"parent": candidate}),
            self.report(candidate, "20261121T010020Z", overrides={"commit": self.base}),
            self.report(candidate, "20261121T010030Z", raw=" " * (REPORT_MAX_BYTES + 1)),
            self.report(candidate, "20261121T010040Z", raw='{"schema": 1, "schema": 1}'),
            self.report(forbidden, "20261121T010050Z"),
        ]
        self.queue()
        result = intake(self.repo)
        self.assertEqual(result["candidates"], [])
        self.assertEqual(set(item["ref"] for item in result["rejected"]), set(refs))

    def test_rejects_empty_candidate_and_report_merge(self):
        self.checkout(self.base)
        unchanged = self.commit("empty")
        empty = self.report(unchanged, "20261121T010000Z")
        candidate = self.candidate("ordinary")
        ref = self.report(candidate, "20261121T010100Z")
        tree = self.git("rev-parse", "HEAD^{tree}")
        merge = self.git("commit-tree", tree, "-p", candidate, "-p", self.base, "-m", "merge")
        self.git("update-ref", ref, merge)
        self.queue()
        result = intake(self.repo)
        self.assertEqual(set(item["ref"] for item in result["rejected"]), {empty, ref})

    def test_rejects_unknown_base_but_accepts_a_previous_published_base(self):
        base = self.candidate("branch baseline")
        (self.repo / "bot.py").write_text("# candidate from a non-main baseline\n")
        candidate = self.commit("candidate")
        ref = self.report(candidate, "20261121T010100Z", overrides={"parent": base})
        self.queue()
        result = intake(self.repo)
        rejected = result["rejected"]
        self.assertEqual([(item["ref"], item["phase"]) for item in rejected], [(ref, "candidate")])
        self.queue(base)
        self.assertEqual(intake(self.repo)["suggested"], candidate)

    def test_rejects_failed_evidence_flag(self):
        candidate = self.candidate("ordinary")
        ref = self.report(candidate, "20261121T010100Z", overrides={"evidence": {"ok": False}})
        self.queue()
        result = intake(self.repo)
        self.assertEqual([(item["ref"], item["phase"]) for item in result["rejected"]],
                         [(ref, "evidence")])

    def test_no_queue_means_no_suggestion_and_json_escapes_worker_text(self):
        candidate = self.candidate("ordinary")
        self.report(candidate, "20261121T010100Z")
        result = intake(self.repo)
        self.assertFalse(result["queue_available"])
        self.assertIsNone(result["suggested"])
        self.assertEqual(result["candidates"][0]["commit"], candidate)
        script = Path(__file__).resolve().parents[1] / "training" / "claude_intake.py"
        process = subprocess.run(
            [sys.executable, "-B", "-m", "training.claude_intake", "--repo", str(self.repo)],
            check=True, capture_output=True, text=True, cwd=script.parents[1],
        )
        self.assertIn(r"\u001b", process.stdout)
        self.assertNotIn("<report>", process.stdout)
        self.assertEqual(json.loads(process.stdout), result)
        self.assertFalse((self.repo / "SHOULD_NOT_EXIST").exists())


if __name__ == "__main__":
    unittest.main()
