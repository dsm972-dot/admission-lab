#!/usr/bin/env python3
"""Rollback de l'enrichissement Energie (t_e805f498). Restaure le corps de
la carte tel qu'il etait avant publication depuis le backup local.

Usage : python3 tools/rollback_energy_enrich.py [--check]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from ha_client import HA  # noqa: E402
from prepare_energy_fix import DASH, TARGET, find_cards  # noqa: E402

BACKUP = ROOT / "data" / "energy-enrich-20261004" / "card_before.json"


def main():
    check = "--check" in sys.argv
    if not BACKUP.exists():
        raise SystemExit(f"[KO] backup introuvable : {BACKUP}")

    before = json.loads(BACKUP.read_text(encoding="utf-8"))
    body_before = before["custom_fields"]["body"]

    dashboard = HA().read_dashboard(DASH, force=True)
    cards = find_cards(dashboard)
    if len(cards) != 1:
        raise SystemExit(f"[KO] {len(cards)} cartes '{TARGET}' (attendu 1)")

    if check:
        same = cards[0]["custom_fields"]["body"] == body_before
        print(f"[{'ok' if same else 'info'}] live identique au backup : {same}")
        return 0

    cards[0]["custom_fields"]["body"] = body_before
    HA().save_dashboard(DASH, dashboard, force=True)

    rb = find_cards(HA().read_dashboard(DASH, force=True))
    ok = len(rb) == 1 and rb[0]["custom_fields"]["body"] == body_before
    print(f"[{'ok' if ok else 'KO'}] rollback applique et relu : {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
