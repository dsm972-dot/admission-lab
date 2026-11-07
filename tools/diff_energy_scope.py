#!/usr/bin/env python3
"""Diff dashboard_before.json vs live, HORS carte cible.

But : distinguer une normalisation faite par Home Assistant (ajout de
cles par defaut, reformatage) d'une modification reelle d'une autre carte.
Affiche chaque noeud dont la valeur a change, avec le chemin et un
extrait. Read-only.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from ha_client import HA  # noqa: E402
from prepare_energy_fix import BACKUP, DASH, TARGET  # noqa: E402

MAX_SHOW = 40


def flatten(node, path="$"):
    out = {}
    if isinstance(node, dict):
        for key, value in node.items():
            out.update(flatten(value, f"{path}.{key}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            out.update(flatten(value, f"{path}[{index}]"))
    else:
        out[path] = node
    return out


def main():
    before = json.loads((BACKUP / "dashboard_before.json").read_text(encoding="utf-8"))
    after = HA().read_dashboard(DASH, force=True)

    fb, fa = flatten(before), flatten(after)

    added = sorted(set(fa) - set(fb))
    removed = sorted(set(fb) - set(fa))
    changed = sorted(p for p in set(fb) & set(fa) if fb[p] != fa[p])

    # On ignore le corps de la carte cible : c'est lui qu'on a patche.
    def is_target(path):
        return "custom_fields.body" in path

    changed = [p for p in changed if not is_target(p)]

    print(f"cles ajoutees  : {len(added)}")
    for p in added[:MAX_SHOW]:
        print(f"  + {p} = {fa[p]!r}"[:200])
    print(f"cles retirees  : {len(removed)}")
    for p in removed[:MAX_SHOW]:
        print(f"  - {p} = {fb[p]!r}"[:200])
    print(f"valeurs changees (hors cible) : {len(changed)}")
    for p in changed[:MAX_SHOW]:
        print(f"  ~ {p}\n      avant={fb[p]!r}\n      apres={fa[p]!r}"[:300])

    non_target_added = [p for p in added if not is_target(p)]
    non_target_removed = [p for p in removed if not is_target(p)]
    ok = not (changed or non_target_added or non_target_removed)
    print(f"\n[{'ok' if ok else 'KO'}] dashboard intact hors carte cible = {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())