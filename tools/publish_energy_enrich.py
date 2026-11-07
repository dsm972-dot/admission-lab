#!/usr/bin/env python3
"""Enrichit la carte Energie de 4 a 8 metriques reelles (t_e805f498).

Meme strategie que publish_energy_fix.py : le dashboard live est relu, seule
la carte cible est reecrite avec le corps canonique produit par le generateur
(source unique de verite), puis ecrit.

Correction du fingerprint de portee : la carte "Énergie compacte" est
IMBRIQUEE dans la carte parente "Énergie véhicule multimédia accès". Le hash
du parent change donc legitimement des que la cible est patchee : l'exclure
aussi, sinon other_cards_unchanged est un faux negatif permanent.

Rollback : python3 tools/rollback_energy_enrich.py
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from ha_client import HA  # noqa: E402
from prepare_energy_fix import DASH, TARGET, find_cards, walk  # noqa: E402

PARENT = "Énergie véhicule multimédia accès"
BACKUP = ROOT / "data" / "energy-enrich-20261004"


def node_hash(node):
    return hashlib.md5(
        json.dumps(node, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def generated_body():
    """Corps canonique de la carte cible, produit par le generateur."""
    import build_dashboard as bd
    import visual_design as vd

    builder = bd.Builder()
    builder.build()
    built = vd.build_home(builder)
    return find_cards(built)


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)

    dashboard = HA().read_dashboard(DASH, force=True)
    cards = find_cards(dashboard)
    if len(cards) != 1:
        raise SystemExit(f"[abort] {len(cards)} cartes '{TARGET}' (attendu 1)")

    card = cards[0]
    body_before = card["custom_fields"]["body"]

    # Le backup n'est ecrit qu'une seule fois : une re-execution idempotente
    # relirait la carte deja publiee et ecraserait la reference "avant" par
    # l'etat "apres", rendant le rollback inoperant.
    if not (BACKUP / "card_before.json").exists():
        (BACKUP / "card_before.json").write_text(
            json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (BACKUP / "dashboard_before.json").write_text(
            json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (BACKUP / "dashboard_before.md5").write_text(
            hashlib.md5((BACKUP / "dashboard_before.json").read_bytes()).hexdigest()
            + "\n",
            encoding="utf-8",
        )
    else:
        print("[info] backup deja present - non ecrase (reference 'avant' preservee)")

    # Corps canonique depuis le generateur.
    new_cards = generated_body()
    if len(new_cards) != 1:
        raise SystemExit(f"[abort] generateur: {len(new_cards)} cartes '{TARGET}'")
    body_after = new_cards[0]["custom_fields"]["body"]

    if body_after == body_before:
        print("[ok] carte deja enrichie - rien a faire")
        return 0

    def is_card(node):
        return isinstance(node, dict) and "custom_fields" in node and "name" in node

    def card_fingerprints(config):
        # La cible ET son parent imbriquant sont exclus : leurs corps
        # changent par construction.
        skip = {TARGET, PARENT}
        return sorted(
            node_hash(n) for n in walk(config) if is_card(n) and n.get("name") not in skip
        )

    others_before = card_fingerprints(dashboard)
    n_scoped = len(others_before)

    card["custom_fields"]["body"] = body_after
    HA().save_dashboard(DASH, dashboard, force=True)

    readback = HA().read_dashboard(DASH, force=True)
    rb_cards = find_cards(readback)
    if len(rb_cards) != 1:
        raise SystemExit("[abort] relecture: nombre de cartes inattendu")

    rb_body = rb_cards[0]["custom_fields"]["body"]
    others_after = card_fingerprints(readback)

    ok_body = rb_body == body_after
    ok_scope = others_before == others_after

    evidence = ROOT / "evidence" / "energy-enrich-20261004"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "card_after.json").write_text(
        json.dumps(rb_cards[0], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (evidence / "body_after.txt").write_text(rb_body, encoding="utf-8")
    (evidence / "publish_report.json").write_text(
        json.dumps(
            {
                "task": "t_e805f498",
                "dashboard": DASH,
                "target": TARGET,
                "excluded_from_fingerprint": [TARGET, PARENT],
                "body_matches_generator": ok_body,
                "other_cards_unchanged": ok_scope,
                "nodes_compared": n_scoped,
                "body_before_len": len(body_before),
                "body_after_len": len(rb_body),
                "published_at": datetime.now().isoformat(timespec="seconds"),
                "backup": str(BACKUP),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"[{'ok' if ok_body else 'KO'}] corps = generateur   : {ok_body}")
    print(
        f"[{'ok' if ok_scope else 'KO'}] autres cartes intactes : {ok_scope} "
        f"({n_scoped} noeuds, cible+parent exclus)"
    )
    print(f"[ok] backup rollback : {BACKUP}")
    if not (ok_body and ok_scope):
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
