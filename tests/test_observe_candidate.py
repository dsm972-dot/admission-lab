"""Tests isolés : subprocess simulé, horloge injectée, aucun réseau/attente."""

from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "observe_candidate", Path(__file__).resolve().parents[1] / "tools/observe_candidate.py"
)
observer_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observer_module)


class ObserverTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.start = datetime(2026, 10, 4, tzinfo=timezone.utc)
        self.now = self.start
        self.tick = 0
        self.observer = observer_module.Observer(
            self.root, clock=lambda: self.now, monotonic=self.monotonic
        )
        self.readback = self.root / observer_module.READBACK
        self.readback.parent.mkdir(parents=True)
        self.directory = self.root / observer_module.DIRECTORY
        self.journal = self.directory / "observations.jsonl"
        # Même une régression dans le test ne doit jamais lancer un processus.
        run_patch = patch.object(observer_module.subprocess, "run", side_effect=self.verify)
        self.run = run_patch.start()
        self.addCleanup(run_patch.stop)
        for target in ("socket.socket", "time.sleep"):
            guard = patch(target, side_effect=AssertionError("Réseau/attente interdits"))
            guard.start()
            self.addCleanup(guard.stop)

    def monotonic(self):
        self.tick += 1.25
        return self.tick

    def valid_readback(self):
        return {"checked_at": observer_module.timestamp(self.now),
                "status": observer_module.VERIFIED,
                "url": "http://ha.invalid:8123/ai-nexus-v4/accueil",
                "views": 17,
                **dict.fromkeys(observer_module.BOOLEAN_FIELDS, True)}

    def write_readback(self, data):
        self.readback.write_text(json.dumps(data), encoding="utf-8")

    def verify(self, *args, **kwargs):
        self.write_readback(self.valid_readback())
        return subprocess.CompletedProcess(args[0], 0, "SECRET_STDOUT", "SECRET_STDERR")

    def rows(self):
        return [json.loads(line) for line in self.journal.read_text().splitlines()]

    def samples(self, minutes):
        self.observer.init()
        for minute in minutes:
            self.now = self.start + timedelta(minutes=minute)
            self.assertEqual(self.observer.sample()["outcome"], "VERIFIED")

    def finish(self):
        self.now = self.start + timedelta(hours=24)
        return self.observer.report()

    def test_init_idempotent_preserves_existing_observation_and_window(self):
        original = self.observer.init()
        self.observer.sample()
        state_bytes = (self.directory / "state.json").read_bytes()
        journal_bytes = self.journal.read_bytes()
        self.now += timedelta(days=3)
        self.assertEqual(self.observer.init(), original)
        self.assertEqual((self.directory / "state.json").read_bytes(), state_bytes)
        self.assertEqual(self.journal.read_bytes(), journal_bytes)
        self.assertEqual(original["start_utc"], "2026-10-04T00:00:00Z")
        self.assertEqual(original["end_utc"], "2026-10-05T00:00:00Z")
        self.assertEqual(original["interval_seconds"], 1800)

    def test_init_preserves_orphan_journal(self):
        self.directory.mkdir(parents=True)
        self.journal.write_bytes(b"existing evidence\n")
        with self.assertRaises(ValueError):
            self.observer.init()
        self.assertEqual(self.journal.read_bytes(), b"existing evidence\n")
        self.assertFalse((self.directory / "state.json").exists())
        self.run.assert_not_called()

    def test_each_sample_runs_verify_with_timeout_even_after_green_publication(self):
        self.observer.init()
        self.write_readback(self.valid_readback())
        self.observer.sample()
        prefix = self.journal.read_bytes()
        self.now += timedelta(minutes=30)
        self.observer.sample()
        self.assertEqual(self.run.call_count, 2)
        self.assertTrue(self.journal.read_bytes().startswith(prefix))
        self.assertEqual(len(self.rows()), 2)
        args, kwargs = self.run.call_args
        self.assertEqual(args[0], [observer_module.sys.executable, "tools/publish_candidate.py", "verify"])
        self.assertEqual(kwargs["timeout"], 180)
        self.assertEqual(kwargs["cwd"], self.root)
        self.assertEqual(kwargs["stdout"], subprocess.DEVNULL)
        self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)
        self.assertEqual(kwargs["env"]["PYTHONOPTIMIZE"], "")
        self.assertEqual(self.rows()[0]["duration_seconds"], 1.25)

    def test_exit_failure_timeout_and_exception_are_retained_without_secrets(self):
        self.observer.init()
        self.write_readback(self.valid_readback())
        self.run.side_effect = [
            subprocess.CompletedProcess([], 7, "SECRET_STDOUT", "SECRET_STDERR"),
            subprocess.TimeoutExpired("SECRET_COMMAND", 180, output="SECRET_OUTPUT", stderr="SECRET_ERROR"),
            OSError("SECRET_OS_ERROR"),
        ]
        for minute in (0, 30, 60):
            self.now = self.start + timedelta(minutes=minute)
            self.observer.sample()
        rows = self.rows()
        self.assertEqual([r["outcome"] for r in rows], ["ERROR", "TIMEOUT", "ERROR"])
        self.assertEqual([r["return_code"] for r in rows], [7, None, None])
        self.assertEqual(rows[1]["error"], "VERIFY_TIMEOUT")
        self.assertNotIn("SECRET", self.journal.read_text())
        self.assertEqual(self.observer.report()["status"], "IN_PROGRESS")
        self.assertEqual(self.finish()["status"], "TECHNICAL_FAIL")

    def test_after_end_sample_is_noop_without_readback_or_process(self):
        self.observer.init()
        state = (self.directory / "state.json").read_bytes()
        for hours in (24, 25, 72):
            self.now = self.start + timedelta(hours=hours)
            with patch.object(observer_module, "fingerprint", side_effect=AssertionError("No readback")):
                self.assertEqual(self.observer.sample()["outcome"], "NO_OP_FINISHED")
        self.run.assert_not_called()
        self.assertFalse(self.journal.exists())
        self.assertEqual((self.directory / "state.json").read_bytes(), state)

    def test_boolean_missing_false_or_truthy_never_passes(self):
        self.observer.init()
        for field in observer_module.BOOLEAN_FIELDS:
            for value in (None, False, 1, "true"):
                with self.subTest(field=field, value=value):
                    data = self.valid_readback()
                    if value is None:
                        del data[field]
                    else:
                        data[field] = value
                    def bad_verify(*args, **kwargs):
                        self.write_readback(data)
                        return subprocess.CompletedProcess([], 0)
                    self.run.side_effect = bad_verify
                    row = self.observer.sample()
                    self.assertEqual(row["outcome"], "ERROR")
                    self.assertEqual(row["error"], "READBACK_BOOLEAN_NOT_TRUE")
                    self.now += timedelta(minutes=1)
        self.assertEqual(self.finish()["status"], "TECHNICAL_FAIL")

    def test_stale_green_readback_is_rejected(self):
        self.observer.init()
        self.write_readback(self.valid_readback())
        self.run.side_effect = None
        self.run.return_value = subprocess.CompletedProcess([], 0)
        self.assertEqual(self.observer.sample()["error"], "READBACK_STALE")

    def test_rewritten_but_old_checked_at_is_rejected(self):
        self.observer.init()
        data = self.valid_readback()
        self.now += timedelta(minutes=30)
        def old_verify(*args, **kwargs):
            self.write_readback(data)
            return subprocess.CompletedProcess([], 0)
        self.run.side_effect = old_verify
        self.assertEqual(self.observer.sample()["error"], "READBACK_STALE")

    def test_missing_or_malformed_readback_is_recorded(self):
        self.observer.init()
        self.run.side_effect = None
        self.run.return_value = subprocess.CompletedProcess([], 0)
        self.assertEqual(self.observer.sample()["outcome"], "ERROR")
        def malformed(*args, **kwargs):
            self.readback.write_text("SECRET_INVALID_JSON")
            return subprocess.CompletedProcess([], 0)
        self.run.side_effect = malformed
        self.assertEqual(self.observer.sample()["outcome"], "ERROR")
        self.assertNotIn("SECRET", self.journal.read_text())

    def test_only_public_fields_and_sanitized_url_are_kept(self):
        self.observer.init()
        data = self.valid_readback()
        data.update(url="http://user:SECRET@ha.invalid:8123/ai-nexus-v4/accueil?token=SECRET#SECRET",
                    token="SECRET", registered={"private": "SECRET"})
        def private_verify(*args, **kwargs):
            self.write_readback(data)
            return subprocess.CompletedProcess([], 0, "SECRET", "SECRET")
        self.run.side_effect = private_verify
        row = self.observer.sample()
        self.assertEqual(row["outcome"], "VERIFIED")
        self.assertEqual(row["url"], "http://ha.invalid:8123/ai-nexus-v4/accueil")
        self.assertNotIn("SECRET", self.journal.read_text())
        self.assertNotIn("registered", row)

    def test_insufficient_count_cannot_pass_even_with_adequate_gaps(self):
        self.samples(range(0, 1440, 40))
        result = self.finish()
        self.assertLess(result["valid_samples"], 48)
        self.assertLessEqual(result["max_gap_seconds"], 2700)
        self.assertEqual(result["status"], "INCOMPLETE")

    def test_48_clustered_samples_do_not_cover_24_hours(self):
        self.samples(range(48))
        self.assertEqual(self.finish()["status"], "INCOMPLETE")

    def test_start_end_and_internal_gaps_count(self):
        schedules = (
            [46 + i * 28 for i in range(48)],
            [i * 28 for i in range(48)],
            [i * 30 for i in range(48) if i != 24] + [1411],
        )
        for index, minutes in enumerate(schedules):
            with self.subTest(index=index):
                self.root = self.root / str(index)
                self.observer = observer_module.Observer(self.root, clock=lambda: self.now,
                                                         monotonic=self.monotonic)
                self.directory = self.root / observer_module.DIRECTORY
                self.readback = self.root / observer_module.READBACK
                self.readback.parent.mkdir(parents=True)
                self.now = self.start
                self.samples(minutes)
                result = self.finish()
                self.assertEqual(result["valid_samples"], 48)
                self.assertGreater(result["max_gap_seconds"], 2700)
                self.assertEqual(result["status"], "INCOMPLETE")

    def test_24_hour_success_keeps_human_qa_pending_and_report_local(self):
        self.samples(range(0, 1440, 30))
        self.assertEqual(self.observer.report()["status"], "IN_PROGRESS")
        count = self.run.call_count
        result = self.finish()
        self.assertEqual(result["status"], "TECHNICAL_PASS")
        self.assertEqual(result["human_validation"], "PENDING")
        self.assertEqual(result["browser_rendering"], "NOT_PROVEN")
        self.assertEqual(result["real_usage"], "NOT_PROVEN")
        self.assertEqual(self.run.call_count, count)
        document = observer_module.markdown(result)
        self.assertIn("human_validation=PENDING", document)
        self.assertIn("Aucun PASS global", document)

    def test_exact_45_minute_gap_allowed(self):
        self.samples([45 + i * 29 for i in range(48)])
        result = self.finish()
        self.assertEqual(result["max_gap_seconds"], 2700)
        self.assertEqual(result["status"], "TECHNICAL_PASS")

    def test_one_failure_is_not_erased_by_48_successes(self):
        self.observer.init()
        self.run.side_effect = OSError("SECRET")
        self.observer.sample()
        self.run.side_effect = self.verify
        self.samples(range(0, 1440, 30))
        self.assertEqual(self.finish()["status"], "TECHNICAL_FAIL")
        self.assertEqual(len(self.rows()), 49)

    def test_corrupt_or_truncated_journal_never_passes(self):
        self.samples(range(0, 1440, 30))
        with self.journal.open("a") as stream:
            stream.write('{"truncated":')
        self.assertEqual(self.finish()["status"], "TECHNICAL_FAIL")

    def test_empty_window_is_incomplete(self):
        self.observer.init()
        self.assertEqual(self.finish()["status"], "INCOMPLETE")
        self.run.assert_not_called()

    def test_nonblocking_lock_prevents_concurrent_commands(self):
        self.observer.init()
        with self.observer.locked():
            for command in (self.observer.init, self.observer.sample, self.observer.report):
                with self.assertRaises(BlockingIOError):
                    command()
        self.run.assert_not_called()

    def test_observer_files_are_private_even_with_permissive_umask(self):
        previous = os.umask(0)
        try:
            self.observer.init()
            self.observer.sample()
        finally:
            os.umask(previous)
        for path in self.directory.iterdir():
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600, path.name)

    def test_cli_reports_sample_error_with_nonzero_exit(self):
        self.observer.init()
        self.run.side_effect = OSError("SECRET")
        with patch.object(observer_module, "Observer", return_value=self.observer), patch("builtins.print") as output:
            self.assertEqual(observer_module.main(["sample"]), 1)
        self.assertNotIn("SECRET", str(output.call_args))


if __name__ == "__main__":
    unittest.main()
