#!/usr/bin/env python3
"""Prepare le correctif de la carte Energie (t_ded30fab).

1. Snapshot live du dashboard ai-nexus-v4 + copie des sources + export YAML
2. Empaquete une proposition limitee AU SEUL template 'Energie compacte'
   (le reste du dashboard live est conserve octet pour octet)
3. Rollback: tools/rollback_energy_fix.py

Le dashboard live n'est jamais remplace en entier : seule la carte
'Energie compacte' est reecrite avec le CSS corrige. Cela evite qu'une
generation locale divergente ecrase les retouches manuelles des autres
cartes (cf. t_61e35cc3 - conflits de hotspot sur le dashboard partage).
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from ha_client import HA  # noqa: E402

DASH = "ai-nexus-v4"
# NB: accent obligatoire - le nom publie est "Énergie compacte".
TARGET = "Énergie compacte"
BACKUP = ROOT / "backups" / "energy-fix-prep-20261004"
SOURCES = ("tools/visual_design.py",)


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def find_cards(config):
    return [n for n in walk(config) if n.get("name") == TARGET]


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().isoformat(timespec="seconds")

    dashboard = HA().read_dashboard(DASH, force=True)
    (BACKUP / "dashboard_before.json").write_text(
        json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for rel in SOURCES:
        src = ROOT / rel
        dest = BACKUP / rel.replace("/", "__")
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    before_md5 = hashlib.md5(
        (BACKUP / "dashboard_before.json").read_bytes()
    ).hexdigest()

    manifest = {
        "task": "t_ded30fab",
        "prepared_at": stamp,
        "dashboard": DASH,
        "target_template": TARGET,
        "dashboard_before_md5": before_md5,
        "sources": list(SOURCES),
        "fix": {
            "css_added": ".panel .metric>ha-icon,.panel .head>ha-icon{margin-left:0;margin-right:0}",
            "root_cause": (
                "button-card injecte :not(ha-state-icon) ha-icon{margin:auto} ; "
                "en flex cela centre l'icone dans l'espace libre et la "
                "separe de son libelle (visible sur la capture Denis)."
            ),
        },
        "rollback": "python3 tools/rollback_energy_fix.py",
    }
    (BACKUP / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    yaml_src = BACKUP / "dashboard_before.yaml"
    try:
        import yaml

        yaml_src.write_text(
            yaml.safe_dump(dashboard, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    except Exception as exc:  # pragma: no cover - export confort
        print(f"[warn] export YAML indisponible: {exc}")

    cards = find_cards(dashboard)
    manifest["target_cards_found"] = len(cards)

    # Le template JS correctif est produit par le generateur, puis injecte
    # dans la carte live par publish_energy_fix.py. On ecrit ici la copie
    # exacte du nouveau body pour allowlist verification.
    proposal = ROOT / "evidence" / "energy-fix-20261004"
    proposal.mkdir(parents=True, exist_ok=True)
    if len(cards) == 1:
        (proposal / "card_before.json").write_text(
            json.dumps(cards[0], ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (proposal / "body_before.txt").write_text(
            cards[0]["custom_fields"]["body"], encoding="utf-8"
        )

    print(f"[ok] backup     : {BACKUP}")
    print(f"[ok] md5 avant  : {before_md5}")
    print(f"[ok] cartes '{TARGET}' trouvées : {len(cards)}")
    print(f"[ok] yaml       : {yaml_src if yaml_src.exists() else 'n/a'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())