#!/usr/bin/env python3
"""Canary 2 (t_61e35cc3) : observation de la republication Famille + Sportage.

Même discipline que la génération 1 (fenêtre 24 h, 30 min, aucun agent, verrou,
journal en ajout seul, rapport local-only), mais le contrôle technique porte sur
la ligne de base réellement publiée aujourd'hui : le readback famille/véhicule
(tools/verify_family_vehicle_light.py), sans navigateur ni rendu.

Honnêteté : rendu navigateur et usage réel restent NON PROUVÉS ; la validation
humaine reste PENDING. Aucun PASS global n'est produit.
"""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from observe_candidate import Observer  # noqa: E402


class FamilyVehicleObserver(Observer):
    DIRECTORY = Path("data/canary-t_61e35cc3")
    READBACK = Path("data/family-vehicle-observation/readback.json")
    VERIFIED = "FAMILY_VEHICLE_PUBLISHED_READBACK_VERIFIED"
    BOOLEAN_FIELDS = (
        "candidate_match", "only_accueil_changed", "legacy_unchanged",
        "default_unchanged", "resources_unchanged", "dashboard_registry_unchanged",
    )
    VERIFY_COMMAND = ["tools/verify_family_vehicle_light.py"]
    TITLE = "# AI Nexus V4 — canary 2 (t_61e35cc3), Famille + Sportage\n\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "sample", "report"))
    args = parser.parse_args(argv)
    observer = FamilyVehicleObserver()
    try:
        result = getattr(observer, args.command)()
    except BlockingIOError:
        print(json.dumps({"error": "OBSERVER_BUSY", "human_validation": "PENDING"}))
        return 2
    except Exception:
        print(json.dumps({"error": "LOCAL_STATE_OR_IO_ERROR", "human_validation": "PENDING"}))
        return 2
    print(observer.markdown(result) if args.command == "report"
          else json.dumps(result, sort_keys=True))
    if args.command == "sample" and result["outcome"] in ("ERROR", "TIMEOUT"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
