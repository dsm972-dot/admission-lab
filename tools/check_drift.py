#!/usr/bin/env python3
"""Compare le dashboard GÉNÉRÉ au dashboard PUBLIÉ — LECTURE SEULE côté HA.

Raison d'être : `build_dashboard.py` valide les références contre `data/states.json`
(un dump). Un LOCAL_PASS ne prouve donc PAS que le candidat est valable sur le HA
du jour. Cet outil relit le dashboard live par WebSocket et donne l'écart exact,
vue par vue, avec le chemin JSON de chaque différence.

Les propriétés de vue possédées par l'interface (ex. `visible`) sont ignorées :
elles sont reprises automatiquement au moment de la publication
(`publish_full_update.preserve_view_properties`).

Codes de sortie : 0 = identique, 1 = écart réel, 2 = erreur d'exécution.

Usage :
    python3 tools/check_drift.py                     # artefact config/ai-nexus-v4.json
    python3 tools/check_drift.py --candidate /tmp/x.json --json /tmp/drift.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from ha_client import HA  # noqa: E402

DASH = "ai-nexus-v4"
IDS_RE = re.compile(r"const ids=(\[[^\]]*\])")


def load_publisher():
    """Réutilise la liste IGNORED de l'outil de publication (source unique)."""
    spec = importlib.util.spec_from_file_location("publish_full_update", ROOT / "tools/publish_full_update.py")
    assert spec and spec.loader, "impossible de charger publish_full_update.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def norm_ids(value):
    """Normalise l'ordre du tableau `const ids=[...]` d'un template JS."""
    if not isinstance(value, str) or "const ids=[" not in value:
        return value
    match = IDS_RE.search(value)
    if not match:
        return value
    try:
        ids = json.loads(match.group(1))
    except json.JSONDecodeError:
        return value
    return value[: match.start()] + "const ids=" + json.dumps(sorted(ids)) + value[match.end():]


def diff(a, b, path="", ignore_keys=()):
    """Écarts entre deux structures. kind = VALUE (réel) ou ORDER (même contenu)."""
    out = []
    if type(a) is not type(b):
        return [(path, a, b, "VALUE")]
    if isinstance(a, dict):
        for key in sorted(set(a) | set(b)):
            if key in ignore_keys:
                continue
            if key not in a:
                out.append((f"{path}/{key}", "<absent>", b[key], "VALUE"))
            elif key not in b:
                out.append((f"{path}/{key}", a[key], "<absent>", "VALUE"))
            else:
                out += diff(a[key], b[key], f"{path}/{key}", ignore_keys)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((f"{path}[len {len(a)} != {len(b)}]", "", "", "VALUE"))
        if a != b and len(a) == len(b) and all(isinstance(x, str) for x in a + b) and sorted(a) == sorted(b):
            out.append((f"{path}[ordre]", a, b, "ORDER"))
            return out
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, f"{path}[{i}]", ignore_keys)
    elif a != b:
        # Un template JS qui ne diffère que par l'ordre de son tableau d'ids est un
        # réordonnancement, pas un changement de comportement.
        if norm_ids(a) == norm_ids(b):
            out.append((path, a, b, "ORDER"))
        else:
            out.append((path, a, b, "VALUE"))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=ROOT / "config" / "ai-nexus-v4.json")
    parser.add_argument("--json", type=Path, help="écrit le rapport structuré")
    parser.add_argument("--max-print", type=int, default=8, help="écarts affichés par vue")
    args = parser.parse_args()

    candidate = json.loads(args.candidate.read_text())
    live = HA().read_dashboard(DASH, force=True)
    user_owned = load_publisher().USER_OWNED_VIEW_KEYS

    report, total = {"dashboard": DASH, "candidate": str(args.candidate), "views": {}, "total_diffs": 0}, 0
    live_by_path = {v.get("path"): v for v in live.get("views", [])}
    for view in candidate.get("views", []):
        path = view.get("path")
        src = live_by_path.get(path)
        if src is None:
            report["views"][path] = {"state": "ABSENTE_EN_LIGNE", "diffs": []}
            total += 1
            continue
        # Un candidat sans `visible` n'est pas une dérive : la publication le reprend.
        ignore = tuple(k for k in user_owned if k not in view)
        diffs = diff(src, view, ignore_keys=ignore)
        reels = [d for d in diffs if d[3] == "VALUE"]
        ordres = len(diffs) - len(reels)
        report["views"][path] = {"state": "OK" if not diffs else ("ORDRE" if not reels else "DIFF"), "diffs": len(reels), "order_only": ordres}
        total += len(reels)
        if diffs:
            label = "DIFF" if reels else "ORDRE"
            print(f"{label} {view.get('title')} ({path}) : {len(reels)} écart(s) réel(s), {ordres} ordre(s) de liste")
            for where, old, new, kind in diffs[: args.max_print]:
                print(f"      [{kind}] {where[:140]}")
                if kind == "VALUE":
                    print(f"        live      : {str(old)[:110]}")
                    print(f"        candidat  : {str(new)[:110]}")
        else:
            print(f"OK    {view.get('title')} ({path})")

    extras = set(live_by_path) - {v.get("path") for v in candidate.get("views", [])}
    if extras:
        print(f"NOTE  vues présentes en ligne mais absentes du candidat : {sorted(extras)}")
        total += len(extras)

    report["total_diffs"] = total
    report["verdict"] = "IDENTIQUE" if total == 0 else "ECART_REEL"
    print(f"\n{report['verdict']} — {total} écart(s) au total")
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"JSON : {args.json}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
