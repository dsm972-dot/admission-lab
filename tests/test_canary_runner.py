"""Tests runner sans ordonnanceur, sans HA et sans attente."""
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
SPEC = importlib.util.spec_from_file_location('canary_runner', ROOT / 'tools/canary_runner.py')
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class RunnerTests(unittest.TestCase):
    def run_case(self, outcome, status, previous=None):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'report.md'
            if previous is not None:
                report.write_text(previous)
            observer = MagicMock()
            observer.sample.return_value = {'outcome': outcome, 'error': 'VERIFY_TIMEOUT'}
            observer.report.return_value = {'status': status}
            output = io.StringIO()
            with patch.object(runner, 'Observer', return_value=observer), \
                 patch.object(runner, 'REPORT', report), \
                 patch.object(runner, 'markdown', return_value=status), redirect_stdout(output):
                code = runner.main()
            self.assertEqual(report.read_text(), status)
            self.assertFalse(report.with_suffix('.md.new').exists())
            observer.sample.assert_called_once_with()
            return code, output.getvalue()

    def test_intermediate_success_silent(self):
        self.assertEqual(self.run_case('VERIFIED', 'IN_PROGRESS'), (0, ''))

    def test_first_final_report_delivered(self):
        code, output = self.run_case('NO_OP_FINISHED', 'TECHNICAL_PASS', 'IN_PROGRESS')
        self.assertEqual(code, 0)
        self.assertEqual(output, 'TECHNICAL_PASS\n')

    def test_final_report_not_repeated(self):
        self.assertEqual(self.run_case('NO_OP_FINISHED', 'TECHNICAL_PASS', 'TECHNICAL_PASS'), (0, ''))

    def test_error_is_visible_and_nonzero(self):
        code, output = self.run_case('TIMEOUT', 'IN_PROGRESS')
        self.assertEqual(code, 1)
        self.assertIn('VERIFY_TIMEOUT', output)
        self.assertIn('Aucune correction', output)
