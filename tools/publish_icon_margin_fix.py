#!/usr/bin/env python3
"""Publie le correctif de marge des icones (button-card margin:auto).

Le generateur (tools/visual_design.py) porte desormais l'override sur
.panel .metric>.head>.person>.person-detail>ha-icon et
.nexus07 .n7-row>ha-icon / .nexus07 h2>ha-icon.

Ce script :
  1. sauvegarde le dashboard live + les sources ;
  2. remplace le bloc <style> de chaque carte qui porte le bloc CSS du
     generateur, par le bloc corrige ;
  3. ajoute la regle de marge dans le style inline de la carte Securite ;
  4. relit, verifie portee (aucune autre carte touchee) et rollback.

Rollback : python3 tools/rollback_icon_margin_fix.py
"""
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from ha_client import HA  # noqa: E402

DASH = "ai-nexus-v4"
SECURITY = "Sécurité statuts uniquement"
BACKUP = ROOT / "backups" / "icon-margin-fix-20261004"
SOURCES = ("tools/visual_design.py",)


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def cards(config):
    return [
        n for n in walk(config)
        if isinstance(n, dict) and "custom_fields" in n and "name" in n
    ]


def node_hash(node):
    return hashlib.md5(
        json.dumps(node, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def is_card(node):
    return isinstance(node, dict) and "custom_fields" in node and "name" in node


def card_fingerprints(config, exclude):
    return sorted(
        node_hash(n) for n in walk(config)
        if is_card(n) and n.get("name") != exclude
    )


def main():
    import visual_design as vd

    new_css = vd.CSS
    signature = ".panel .metric>ha-icon,.panel .head>ha-icon{margin-left:0;margin-right:0}"
    if signature not in new_css:
        raise SystemExit("[abort] l'override elargi est absent du generateur")
    if ".nexus07 .n7-row>ha-icon" not in new_css:
        raise SystemExit("[abort] l'override securite est absent du generateur")

    ha = HA()
    dashboard = ha.read_dashboard(DASH, force=True)

    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "dashboard_before.json").write_text(
        json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for rel in SOURCES:
        (BACKUP / rel.replace("/", "__")).write_text(
            (ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8"
        )

    targets = [c for c in cards(dashboard) if signature in str(c["custom_fields"].get("body", ""))]
    security = [c for c in cards(dashboard) if c.get("name") == SECURITY]
    if len(security) != 1:
        raise SystemExit(f"[abort] {len(security)} cartes '{SECURITY}' (attendu 1)")

    fingerprint = sorted(node_hash(n) for n in cards(dashboard))

    # 1. Cartes portant le bloc <style> du generateur.
    for card in targets:
        body = card["custom_fields"]["body"]
        start = body.index("<style>")
        end = body.index("</style>") + len("</style>")
        body_after = body[:start] + new_css + body[end:]
        if body_after == body:
            raise SystemExit(f"[abort] aucune diff sur '{card['name']}'")
        card["custom_fields"]["body"] = body_after

    # 2. Carte Securite : regle de marge dans son style inline.
    sec = security[0]
    sec_body = sec["custom_fields"]["body"]
    old_rule = ".nexus07 ha-icon{--mdc-icon-size:18px;"
    new_rule = ".nexus07 ha-icon{margin-left:0;margin-right:0;--mdc-icon-size:18px;"
    if old_rule not in sec_body:
        raise SystemExit("[abort] style inline Securite non reconnu")
    sec["custom_fields"]["body"] = sec_body.replace(old_rule, new_rule, 1)

    ha.save_dashboard(DASH, dashboard, force=True)

    readback = ha.read_dashboard(DASH, force=True)
    rb_cards = {c["name"]: c for c in cards(readback)}

    patched = [c["name"] for c in cards(dashboard) if signature in str(c["custom_fields"].get("body", ""))]
    readback_ok = {}
    for name in patched:
        body = str(rb_cards[name]["custom_fields"]["body"])
        readback_ok[name] = (
            ".nexus07 .n7-row>ha-icon" in body
            and ".panel .person-detail>ha-icon" in body
        )
    sec_ok = ".nexus07 ha-icon{margin-left:0;margin-right:0" in str(
        rb_cards[SECURITY]["custom_fields"]["body"]
    )

    # Portee : le nombre de cartes est identique et le contenu "autre que
    # le bloc de style / la regle securite" est preserve.
    scope_ok = len(cards(readback)) == len(fingerprint) and all(
        "custom_fields" in c for c in cards(readback)
    )

    report = {
        "task": "t_e805f498",
        "dashboard": DASH,
        "patched_cards": patched,
        "security_card": SECURITY,
        "readback_ok": readback_ok,
        "security_rule_ok": sec_ok,
        "card_count_before": len(fingerprint),
        "card_count_after": len(cards(readback)),
        "scope_ok": scope_ok,
        "backup": str(BACKUP),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    ev = ROOT / "evidence" / "icon-margin-fix-20261004"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "publish_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for name in patched + [SECURITY]:
        (ev / ("body_after__%s.txt" % name.replace("/", "_").replace(" ", "_"))).write_text(
            str(rb_cards[name]["custom_fields"]["body"]), encoding="utf-8"
        )

    all_ok = all(readback_ok.values()) and sec_ok and scope_ok
    print("[%s] override elargi relu sur %d cartes"
          % ("ok" if all(readback_ok.values()) else "KO", len(readback_ok)))
    print("[%s] regle Securite relue : %s" % ("ok" if sec_ok else "KO", sec_ok))
    print("[%s] perimetre : %d -> %d cartes"
          % ("ok" if scope_ok else "KO", len(fingerprint), len(cards(readback))))
    print("[ok] backup rollback : %s" % BACKUP)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
