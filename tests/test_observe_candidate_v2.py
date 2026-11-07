#!/usr/bin/env python3
"""Tests du canary 2 (t_61e35cc3) : classe dérivée, aucune régression gen 1."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import observe_candidate as gen1  # noqa: E402
from observe_candidate_v2 import FamilyVehicleObserver  # noqa: E402


class TestGen2(unittest.TestCase):
    def test_isolation(self):
        self.assertEqual(FamilyVehicleObserver.DIRECTORY, Path("data/canary-t_61e35cc3"))
        self.assertNotEqual(FamilyVehicleObserver.DIRECTORY, gen1.DIRECTORY)
        self.assertNotEqual(FamilyVehicleObserver.READBACK, gen1.READBACK)
        self.assertNotEqual(FamilyVehicleObserver.VERIFIED, gen1.VERIFIED)
        self.assertNotEqual(FamilyVehicleObserver.VERIFY_COMMAND, gen1.Observer.VERIFY_COMMAND)
        # aucune écriture dans le répertoire de la génération 1
        self.assertNotIn(str(gen1.DIRECTORY), str(FamilyVehicleObserver.READBACK))
        self.assertIn("verify_family_vehicle_light.py", FamilyVehicleObserver.VERIFY_COMMAND[0])

    def test_reuses_observable_surface(self):
        for name in ("init", "sample", "report", "append", "state", "locked", "markdown"):
            self.assertTrue(hasattr(FamilyVehicleObserver, name), name)

    def test_boolean_fields_match_light_verifier(self):
        readback = json.loads(
            (Path(__file__).resolve().parents[1]
             / "data/family-vehicle-observation/readback.json").read_text())
        for field in FamilyVehicleObserver.BOOLEAN_FIELDS:
            self.assertIn(field, readback, field)
        self.assertEqual(FamilyVehicleObserver.VERIFIED, readback["status"])
        self.assertNotEqual(FamilyVehicleObserver.BOOLEAN_FIELDS, gen1.BOOLEAN_FIELDS)

    def test_assert_readback_rejects_false(self):
        fields = {k: True for k in FamilyVehicleObserver.BOOLEAN_FIELDS}
        fields.update(status=FamilyVehicleObserver.VERIFIED,
                      url="http://10.0.0.47:8123/ai-nexus-v4/accueil", views=17)
        observer = FamilyVehicleObserver()
        observer.assert_readback(fields)
        fields["default_unchanged"] = False
        with self.assertRaises(AssertionError):
            observer.assert_readback(fields)
        fields["default_unchanged"] = True
        fields["status"] = "AUTRE"
        with self.assertRaises(AssertionError):
            observer.assert_readback(fields)

    def test_markdown_declares_unproven(self):
        text = FamilyVehicleObserver().markdown(
            {"status": "IN_PROGRESS", "start_utc": "2026-10-04T20:00:00Z",
             "end_utc": "2026-10-05T20:00:00Z", "observations": 1, "valid_samples": 1,
             "failures": 0, "max_gap_seconds": 0})
        self.assertIn("t_61e35cc3", text)
        self.assertIn("NON PROUVÉS", text)
        self.assertIn("PENDING", text)


if __name__ == "__main__":
    unittest.main()
