#!/usr/bin/env python3
"""Vérificateur LECTURE SEULE de la republication Famille + Sportage.

 unlike tools/publish_verify_family_vehicle.py --verify-current, ce contrôle ne
lance PAS de navigateur : pas de rendu, pas de captures, à chaque échantillon.
Il compare le dashboard HA vivant au candidat publié, et les autres dashboards,
le défaut, le registre de dashboards et les ressources à la sauvegarde.

Sortie : data/family-vehicle-observation/readback.json (écriture locale).
Aucune écriture dans HA, aucun service, aucun actionneur.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ha_client import HA  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/family-sportage-20261004T154222Z"
OUT = ROOT / "data/family-vehicle-observation"
SLUG = "ai-nexus-v4"
VERIFIED = "FAMILY_VEHICLE_PUBLISHED_READBACK_VERIFIED"
TIMEOUT_MARK = None


def digest(obj) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def load(name: str):
    return json.loads((EVIDENCE / name).read_text())


def snapshot(h, cfg):
    dashboards = h.dashboards()
    return {
        "dashboards": dashboards,
        "resources": h.resources(),
        "default_hash": digest(h.read_dashboard(None, force=True)),
        "configs": {d["url_path"]: digest(h.read_dashboard(d["url_path"], force=True))
                    for d in dashboards if d["url_path"] != SLUG},
    }


def main() -> int:
    started = datetime.now(timezone.utc)
    OUT.mkdir(parents=True, exist_ok=True)
    candidate = json.loads((EVIDENCE / "native/dashboard-readback.json").read_text())
    backup = load("dashboard-before.json")
    legacy = load("legacy-before.json")
    default = load("default-before.json")

    h = HA()
    live = h.read_dashboard(SLUG, force=True)
    live_dashboards = snapshot(h, live)
    report = {
        "checked_at": started.isoformat(),
        "status": VERIFIED,
        "url": "http://10.0.0.47:8123/ai-nexus-v4/accueil",
        "views": len(live["views"]),
        "dashboard_hash": digest(live),
        "candidate_hash": digest(candidate),
        "candidate_match": live == candidate,
        "only_accueil_changed": all(
            a == b for i, (a, b) in enumerate(zip(live["views"], backup["views"]))
            if live["views"][i]["path"] != "accueil"
        ),
        "legacy_unchanged": all(
            live_dashboards["configs"].get(slug) == digest(value)
            for slug, value in legacy.items()
        ),
        "default_unchanged": live_dashboards["default_hash"] == digest(default),
        "resources_unchanged": live_dashboards["resources"] == load("resources-before.json"),
        "dashboard_registry_unchanged":
            live_dashboards["dashboards"] == load("dashboards-before.json"),
        "human_validation": "PENDING",
        "browser_rendering": "NOT_PROVEN",
        "real_usage": "NOT_PROVEN",
        "physical_action_executed": False,
    }
    report["passed"] = all(report[key] for key in (
        "candidate_match", "only_accueil_changed", "legacy_unchanged",
        "default_unchanged", "resources_unchanged", "dashboard_registry_unchanged",
    )) and report["views"] > 0
    report["status"] = VERIFIED if report["passed"] else "FAMILY_VEHICLE_READBACK_MISMATCH"
    report["duration_seconds"] = round(
        (datetime.now(timezone.utc) - started).total_seconds(), 6)
    (OUT / "readback.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())