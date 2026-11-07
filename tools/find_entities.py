#!/usr/bin/env python3
"""Recherche d'entites dans data/entities_index.json (local, lecture seule)."""
import json, re, sys, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = json.load(open(os.path.join(BASE, "data/entities_index.json")))


def find(pattern, limit=25, dom=None):
    rx = re.compile(pattern, re.I)
    out = []
    for e in IDX:
        if dom and not e["eid"].startswith(dom + "."):
            continue
        if rx.search(e["eid"]) or rx.search(e.get("name") or ""):
            out.append(e)
    out.sort(key=lambda e: e["eid"])
    return out[:limit]


if __name__ == "__main__":
    dom = None
    args = sys.argv[1:]
    if args and args[0].startswith("--dom="):
        dom = args[0][6:]
        args = args[1:]
    lim = 25
    if args and args[0].startswith("--limit="):
        lim = int(args[0][8:])
        args = args[1:]
    for pat in args:
        res = find(pat, lim, dom)
        print("### %s  (%d)" % (pat, len(res)))
        for e in res:
            unit = e.get("unit") or ""
            print("   %-58s | %-28s | %s %s" % (e["eid"], (e.get("name") or "")[:28], e.get("state"), unit))
