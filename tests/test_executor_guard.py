"""Test the real service guard without loading credentials."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

class ExecutorGuardTests(unittest.TestCase):
    def test_physical_services_rejected_before_network(self):
        tree = ast.parse((ROOT / 'tools/ha_client.py').read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'HA')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'service')
        isolated = ast.Module(body=[method], type_ignores=[])
        namespace = {}
        exec(compile(ast.fix_missing_locations(isolated), '<service-guard>', 'exec'), namespace)
        for domain, service in [('lock', 'unlock'), ('cover', 'open_cover'), ('light', 'turn_on'), ('script', 'turn_on'), ('tts', 'speak')]:
            with self.subTest(domain=domain), patch('urllib.request.urlopen') as network:
                with self.assertRaises(PermissionError):
                    namespace['service'](object(), domain, service)
                network.assert_not_called()

if __name__ == '__main__':
    unittest.main()
