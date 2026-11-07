#!/usr/bin/env python3
"""Vérificateur LECTURE SEULE de la nouvelle baseline (full generator match).

Contrôle technique sans navigateur : compare le dashboard HA vivant au générateur
actuel, et vérifie que les autres dashboards, le défaut, le registre de dashboards
et les ressources n'ont pas changé depuis l'instant T0 de cette observation.

Sortie : data/full-generator-observation/readback.json (écriture locale).
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
from build_dashboard import Builder  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/full-generator-observation"
SLUG = "ai-nexus-v4"
VERIFIED = "FULL_GENERATOR_OBSERVATION_VERIFIED"

# Baseline T0 : état des autres dashboards, défaut, ressources au lancement de l'observation
BASELINE_DIR = OUT / "baseline-t0"


def digest(obj) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def save_baseline(h: HA):
    """Sauvegarde l'état T0 des éléments qui ne doivent pas changer."""
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    dashboards = h.dashboards()
    (BASELINE_DIR / "dashboards-before.json").write_text(json.dumps(dashboards, ensure_ascii=False, indent=2))
    (BASELINE_DIR / "resources-before.json").write_text(json.dumps(h.resources(), ensure_ascii=False, indent=2))
    (BASELINE_DIR / "default-before.json").write_text(json.dumps(h.read_dashboard(None, force=True), ensure_ascii=False, indent=2))
    configs = {}
    for d in dashboards:
        if d["url_path"] != SLUG:
            configs[d["url_path"]] = h.read_dashboard(d["url_path"], force=True)
    (BASELINE_DIR / "legacy-before.json").write_text(json.dumps(configs, ensure_ascii=False, indent=2))
    print(f"[ok] Baseline T0 saved to {BASELINE_DIR}")


def load_baseline(name: str):
    return json.loads((BASELINE_DIR / name).read_text())


def main(init_baseline: bool = False) -> int:
    started = datetime.now(timezone.utc)
    OUT.mkdir(parents=True, exist_ok=True)

    # Générateur = source de vérité
    candidate = Builder().build()
    candidate_hash = digest(candidate)

    h = HA()
    live = h.read_dashboard(SLUG, force=True)
    live_hash = digest(live)

    if init_baseline:
        save_baseline(h)
        print("[ok] Baseline initialisée. Relancer sans --init pour les échantillons.")
        return 0

    # Charger baseline T0
    try:
        dashboards_before = load_baseline("dashboards-before.json")
        resources_before = load_baseline("resources-before.json")
        default_before = load_baseline("default-before.json")
        legacy_before = load_baseline("legacy-before.json")
    except FileNotFoundError:
        print("[error] Baseline T0 non trouvée. Lancer avec --init d'abord.", file=sys.stderr)
        return 1

    # Snapshot actuel
    live_dashboards = h.dashboards()
    live_resources = h.resources()
    live_default = h.read_dashboard(None, force=True)
    live_legacy = {}
    for d in live_dashboards:
        if d["url_path"] != SLUG:
            live_legacy[d["url_path"]] = h.read_dashboard(d["url_path"], force=True)

    report = {
        "checked_at": started.isoformat(),
        "status": VERIFIED,
        "url": "http://10.0.0.47:8123/ai-nexus-v4/accueil",
        "views": len(live["views"]),
        "dashboard_hash": live_hash,
        "candidate_hash": candidate_hash,
        "candidate_match": live_hash == candidate_hash,
        "legacy_unchanged": all(
            digest(live_legacy.get(slug, {})) == digest(legacy_before.get(slug, {}))
            for slug in set(live_legacy.keys()) | set(legacy_before.keys())
        ),
        "default_unchanged": digest(live_default) == digest(default_before),
        "resources_unchanged": live_resources == resources_before,
        "dashboard_registry_unchanged": live_dashboards == dashboards_before,
        "human_validation": "PENDING",
        "browser_rendering": "NOT_PROVEN",
        "real_usage": "NOT_PROVEN",
        "physical_action_executed": False,
    }
    report["passed"] = all(report[key] for key in (
        "candidate_match", "legacy_unchanged", "default_unchanged",
        "resources_unchanged", "dashboard_registry_unchanged",
    )) and report["views"] > 0
    report["status"] = VERIFIED if report["passed"] else "FULL_GENERATOR_OBSERVATION_MISMATCH"
    report["duration_seconds"] = round((datetime.now(timezone.utc) - started).total_seconds(), 6)

    (OUT / "readback.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    init = "--init" in sys.argv
    sys.exit(main(init_baseline=init))