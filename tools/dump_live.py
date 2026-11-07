#!/usr/bin/env python3
"""Rafraîchit les dumps HA utilisés par le générateur — LECTURE SEULE côté HA.

Écrit uniquement sous data/ :
  - states.json          copie brute de /api/states (attendu par build_dashboard)
  - entities_index.json  index compact à schéma unique {eid,name,domain,dc,unit,state,sf}
  - services.json        copie brute de /api/services
  - resources.json       ressources Lovelace (WebSocket)
  - dashboards.json      registre des dashboards (WebSocket)

Aucune écriture HA : aucun service, aucun lovelace/config/save.
Sauvegarde préalable de chaque fichier remplacé, écriture atomique, contrôle
de vraisemblance avant remplacement (échec net plutôt que dump vide).

Usage :
    python3 tools/dump_live.py            # rafraîchit tout
    python3 tools/dump_live.py --check    # compare seulement, n'écrit rien
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from ha_client import HA, HA_URL  # noqa: E402

DATA = ROOT / "data"
MIN_STATES = 1000          # garde-fou : un dump tronqué ne doit jamais remplacer le précédent
REQUIRED = ("states.json", "entities_index.json", "services.json", "resources.json", "dashboards.json")


def index_entry(state: dict) -> dict:
    """Une entrée d'index, schéma unique et minimal (identique au format historique)."""
    attrs = state.get("attributes") or {}
    eid = state["entity_id"]
    return {
        "eid": eid,
        "name": attrs.get("friendly_name") or eid,
        "domain": eid.split(".", 1)[0],
        "dc": attrs.get("device_class"),
        "unit": attrs.get("unit_of_measurement") or "",
        "state": state.get("state"),
        "sf": attrs.get("supported_features"),
    }


def atomic_write(path: Path, obj) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(DATA), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def build_payload(h: HA) -> dict:
    states = h.states()
    if not isinstance(states, list) or len(states) < MIN_STATES:
        raise SystemExit(f"[KO] /api/states invraisemblable ({len(states) if isinstance(states, list) else 'non-liste'} entrées) — rien écrit")

    seen, entries = set(), []
    for s in states:
        eid = s.get("entity_id")
        if not eid or eid in seen:
            continue
        seen.add(eid)
        entries.append(index_entry(s))

    payload = {
        "states.json": states,
        "entities_index.json": sorted(entries, key=lambda e: e["eid"]),
        "services.json": h.services(),
        "resources.json": h.ws_one({"type": "lovelace/resources"})["result"],
        "dashboards.json": h.ws_one({"type": "lovelace/dashboards/list"})["result"],
    }
    # Contrôles de vraisemblance sur chaque volet
    assert len(payload["entities_index.json"]) == len(seen)
    assert all({"eid", "name", "domain", "dc", "unit", "state", "sf"} <= set(e) for e in payload["entities_index.json"]), "schéma d'index hétérogène"
    assert isinstance(payload["resources.json"], list) and payload["resources.json"], "ressources Lovelace vides"
    assert isinstance(payload["dashboards.json"], list) and payload["dashboards.json"], "registre dashboards vide"
    assert isinstance(payload["services.json"], list) and payload["services.json"], "catalogue services vide"
    return payload


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    h = HA()
    payload = build_payload(h)

    print(f"HA           : {HA_URL}")
    print(f"entités      : {len(payload['states.json'])}")
    print(f"index        : {len(payload['entities_index.json'])} (schéma unique vérifié)")
    print(f"services     : {len(payload['services.json'])} domaines")
    print(f"ressources   : {len(payload['resources.json'])}")
    print(f"dashboards   : {len(payload['dashboards.json'])}")

    if check_only:
        print("\n[check] aucun fichier écrit")
        return 0

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = ROOT / "backups" / f"dumps-{stamp}"
    backup.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED:
        src = DATA / name
        if src.exists():
            shutil.copy2(src, backup / name)

    for name, obj in payload.items():
        atomic_write(DATA / name, obj)

    print(f"\n[ok] dumps rafraîchis ({stamp}) — sauvegarde : {backup.relative_to(ROOT)}")
    for name in REQUIRED:
        print(f"     data/{name:22s} {DATA.joinpath(name).stat().st_size:>9d} o")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
