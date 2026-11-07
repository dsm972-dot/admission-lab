#!/usr/bin/env python3
"""Publie le correctif CSS de la carte Energie (t_ded30fab).

Publication STRICTEMENT limitee au template "Énergie compacte" :
le dashboard live est relu, seule cette carte est reecrite avec le
nouveau corps produit par le generateur, puis ecrit. Toute autre carte
est conservee exactement telle quelle (comparaison md5 avant/apres).

Rollback : python3 tools/rollback_energy_fix.py
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from ha_client import HA  # noqa: E402
from prepare_energy_fix import BACKUP, DASH, TARGET, find_cards  # noqa: E402

CSS_RULE = ".panel .metric>ha-icon,.panel .head>ha-icon{margin-left:0;margin-right:0}"


def node_hash(node):
    return hashlib.md5(
        json.dumps(node, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def main():
    dashboard = HA().read_dashboard(DASH, force=True)
    cards = find_cards(dashboard)
    if len(cards) != 1:
        raise SystemExit(f"[abort] {len(cards)} cartes '{TARGET}' (attendu 1)")

    card = cards[0]
    body_before = card["custom_fields"]["body"]

    if CSS_RULE in body_before:
        print("[ok] correctif deja publie - rien a faire")
        return 0

    # Le nouveau corps provient du generateur (source unique de verite).
    import visual_design as vd

    new_body = vd.CSS  # sanity: la regle doit exister dans le generateur
    if CSS_RULE not in new_body:
        raise SystemExit("[abort] la regle CSS est absente du generateur")

    # On remplace le bloc <style> du corps live par celui du generateur.
    start = body_before.index("<style>")
    end = body_before.index("</style>") + len("</style>")
    body_after = body_before[:start] + vd.CSS + body_before[end:]

    if body_after == body_before:
        raise SystemExit("[abort] aucune diff dans le corps")

    # Fingerprint de tout le dashboard sauf la carte cible.
    # NB: on ne hash que les noeuds "carte" (dict possessing custom_fields).
    # Hasher le dict racine serait un faux positif: la carte cible y est
    # imbriquee, donc son hash change des que la carte est patchee.
    def is_card(node):
        return isinstance(node, dict) and "custom_fields" in node and "name" in node

    def card_fingerprints(config):
        return sorted(
            node_hash(n)
            for n in _walk(config)
            if is_card(n) and n.get("name") != TARGET
        )

    others_before = card_fingerprints(dashboard)

    card["custom_fields"]["body"] = body_after
    HA().save_dashboard(DASH, dashboard, force=True)

    readback = HA().read_dashboard(DASH, force=True)
    rb_cards = find_cards(readback)
    if len(rb_cards) != 1:
        raise SystemExit("[abort] relecture: nombre de cartes inattendu")

    rb_body = rb_cards[0]["custom_fields"]["body"]
    others_after = card_fingerprints(readback)

    ok_rule = CSS_RULE in rb_body
    ok_scope = others_before == others_after

    evidence = ROOT / "evidence" / "energy-fix-20261004"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "card_after.json").write_text(
        json.dumps(rb_cards[0], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (evidence / "body_after.txt").write_text(rb_body, encoding="utf-8")
    (evidence / "publish_report.json").write_text(
        json.dumps(
            {
                "task": "t_ded30fab",
                "dashboard": DASH,
                "target": TARGET,
                "css_rule": CSS_RULE,
                "css_rule_in_readback": ok_rule,
                "other_cards_unchanged": ok_scope,
                "nodes_compared": len(others_after),
                "body_before_len": len(body_before),
                "body_after_len": len(rb_body),
                "backup": str(BACKUP),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"[{'ok' if ok_rule else 'KO'}] regle CSS relue      : {ok_rule}")
    print(f"[{'ok' if ok_scope else 'KO'}] autres cartes intactes : {ok_scope} ({len(others_after)} noeuds)")
    print(f"[ok] backup rollback : {BACKUP}")
    if not (ok_rule and ok_scope):
        raise SystemExit(1)
    return 0


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


if __name__ == "__main__":
    raise SystemExit(main())