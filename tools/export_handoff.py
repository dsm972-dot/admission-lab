#!/usr/bin/env python3
"""Construit le dossier de soumission pour Claude Opus 3.5.

Lit les artefacts live (/root/.hermes/cache/scratch/nexus/) + la config du depot,
et ecrit un ensemble de fichiers JSON/Markdown exploitables dans
/root/workspace/maison/ai-nexus-handoff-20261106/.
"""
from __future__ import annotations

import collections
import hashlib
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ha_client import HA_URL, load_token  # noqa: E402

SCRATCH = Path("/root/.hermes/cache/scratch/nexus")
OUT = Path("/root/workspace/maison/ai-nexus-handoff-20261106")
DATA = OUT / "data"
DATA.mkdir(parents=True, exist_ok=True)

live = json.load(open(SCRATCH / "live_lovelace.json"))["data"]["config"]
states = {s["entity_id"]: s for s in json.load(open(SCRATCH / "live_states.json"))}
resources = json.load(open(SCRATCH / "live_resources.json"))["data"]["items"]
repo_path = ROOT / "config" / "ai-nexus-v4.json"
repo = json.load(open(repo_path)) if repo_path.exists() else None

ENT = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")


def walk_views(config):
    """(view_title, view_path, node) pour chaque noeud dict du dashboard."""
    def rec(o, vt, vp):
        if isinstance(o, dict):
            yield vt, vp, o
            for k, v in o.items():
                if k in ("card_mod", "styles"):
                    continue
                yield from rec(v, vt, vp)
        elif isinstance(o, list):
            for v in o:
                yield from rec(v, vt, vp)

    for i, v in enumerate(config.get("views", [])):
        vt = v.get("title") or v.get("path") or str(i)
        vp = v.get("path") or str(i)
        yield from rec(v, vt, vp)


def label_of(n):
    for k in ("name", "title", "label", "heading"):
        v = n.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    e = n.get("entity")
    if isinstance(e, str):
        return states.get(e, {}).get("attributes", {}).get("friendly_name") or e
    return "(sans libellé)"


def action_kind(n):
    for k in ("tap_action", "hold_action", "double_tap_action"):
        a = n.get(k)
        if isinstance(a, str):
            if a != "none":
                return k, a
        elif isinstance(a, dict):
            act = a.get("action")
            if act and act != "none":
                return k, act
    return None, None


# ---------------------------------------------------------------- entités
ent_refs = collections.defaultdict(lambda: {"count": 0, "views": set(), "attrs": []})
nav_paths = collections.Counter()
services = collections.Counter()
card_types = collections.Counter()
inert = []
per_view = collections.Counter()

for vt, vp, n in walk_views(live):
    t = n.get("type")
    if isinstance(t, str):
        card_types[t] += 1
    for key in ("entity", "entity_id"):
        e = n.get(key)
        if isinstance(e, str) and ENT.match(e):
            ent_refs[e]["count"] += 1
            ent_refs[e]["views"].add(vt)
    for k, v in n.items():
        if isinstance(v, str):
            if k in ("navigation_path", "url_path") and v.startswith("/"):
                nav_paths[v] += 1
            elif k in ("service", "perform_action") and "." in v:
                services[v] += 1
            elif ENT.match(v) and k not in ("entity", "entity_id"):
                ent_refs[v]["count"] += 1
                ent_refs[v]["views"].add(vt)
                ent_refs[v]["attrs"].append(k)
    # boutons inertes
    if t == "custom:button-card":
        per_view[vt] += 1
        ak, av = action_kind(n)
        if ak is None:
            inert.append(
                {
                    "vue": vt,
                    "chemin_vue": vp,
                    "libelle": label_of(n),
                    "entite": n.get("entity"),
                    "raison": "aucune action (tap/hold/double_tap absents ou none)",
                }
            )

used = sorted(ent_refs)
missing = [e for e in used if e not in states]
degraded = sorted(
    (e, states[e]["state"]) for e in used if e in states and states[e]["state"] in ("unavailable", "unknown")
)

ent_report = {
    "total_etats_ha": len(states),
    "entites_referencees_uniques": len(used),
    "entites_inexistantes": len(missing),
    "entites_indisponibles_ou_inconnues": len(degraded),
    "detail_inexistantes": [
        {
            "entity_id": e,
            "references": ent_refs[e]["count"],
            "vues": sorted(ent_refs[e]["views"]),
            "suggestion": next(
                (s for s in states if s.startswith(e.split(".")[0] + ".") and
                 (s.endswith(e.split(".", 1)[1].split("_")[-1]) or e.split(".", 1)[1].split("_")[0] in s)),
                None,
            ),
        }
        for e in missing
    ],
    "detail_indisponibles": [{"entity_id": e, "state": s, "vues": sorted(ent_refs[e]["views"])} for e, s in degraded],
    "entites_par_domaine": collections.Counter(e.split(".")[0] for e in states).most_common(),
    "referencees_par_domaine": collections.Counter(e.split(".")[0] for e in used).most_common(),
}
(DATA / "entites.json").write_text(json.dumps(ent_report, ensure_ascii=False, indent=1))

# ---------------------------------------------------------------- navigation
view_paths = {v.get("path") or str(i) for i, v in enumerate(live.get("views", []))}
PREFIX = "/ai-nexus-v4/"


def cible_valide(p: str) -> bool:
    p = p.split("?")[0].rstrip("/")
    if p.startswith(PREFIX):
        return p[len(PREFIX):].split("/")[0] in view_paths
    if p.startswith("/lovelace/"):
        return p[len("/lovelace/"):].split("/")[0] in view_paths or p == "/lovelace"
    return p.strip("/").split("/")[0] in view_paths


nav = {
    "vues_existantes": sorted(view_paths),
    "cibles_referencees": [
        {"cible": p, "occurrences": c, "valide": cible_valide(p)}
        for p, c in nav_paths.most_common()
    ],
    "cibles_invalides": [
        {"cible": p, "occurrences": c}
        for p, c in nav_paths.most_common()
        if not cible_valide(p)
    ],
}
(DATA / "navigation.json").write_text(json.dumps(nav, ensure_ascii=False, indent=1))

# ---------------------------------------------------------------- boutons inertes
(DATA / "boutons-inertes.json").write_text(
    json.dumps(
        {
            "total_button_card": sum(per_view.values()),
            "total_inertes": len(inert),
            "par_vue": per_view.most_common(),
            "boutons": inert,
        },
        ensure_ascii=False,
        indent=1,
    )
)
with open(DATA / "boutons-inertes.csv", "w") as f:
    f.write("vue;libelle;entite;raison\n")
    for b in inert:
        f.write(f"{b['vue']};{b['libelle']};{b['entite'] or ''};{b['raison']}\n")

# ---------------------------------------------------------------- ressources
req = urllib.request.Request(
    HA_URL.rstrip("/") + "/api/services", headers={"Authorization": "Bearer " + load_token()}
)
svc_live = set()
try:
    for dom in json.load(urllib.request.urlopen(req, timeout=20)):
        for s in dom.get("services", {}):
            svc_live.add(f"{dom['domain']}.{s}")
except Exception as e:  # noqa: BLE001
    svc_live = set()
    print("services indisponibles:", e)

res_report = {
    "ressources_enregistrees": resources,
    "urls_cassees": [
        {"url": "/webrtc/webrtc-camera.js", "erreur": "404", "impact": "cartes caméra WebRTC non rendues"},
        {"url": "/local/community/mushroom-cards/mushroom.js", "erreur": "404 (dossier réel: lovelace-mushroom)", "impact": "aucune carte mushroom utilisée dans la config live, donc sans effet visible"},
        {"url": "/local/community/lovelace-card-mod/card-mod.js", "erreur": "déclaré deux fois (module + css) → MIME refusé", "impact": "card_mod inopérant ; 0 usage dans la config live actuelle"},
        {"url": "/local/bubble/bubble-modules.yaml", "erreur": "404", "impact": "Bubble Card fonctionne sans ses modules optionnels"},
    ],
    "types_de_cartes_utilises": card_types.most_common(),
    "services_appeles": [
        {"service": s, "occurrences": c, "existe": s in svc_live}
        for s, c in services.most_common()
    ],
}
(DATA / "ressources-et-services.json").write_text(json.dumps(res_report, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- diff live/repo
def h(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


diff = {"live_sha": h(live), "repo_sha": h(repo) if repo else None, "identique": bool(repo) and h(live) == h(repo)}
if repo:
    diff["vues_live"] = len(live.get("views", []))
    diff["vues_repo"] = len(repo.get("views", []))
    diff["titre_live"] = [v.get("title") for v in live.get("views", [])]
    diff["titre_repo"] = [v.get("title") for v in repo.get("views", [])]
    diff["themes_live"] = live.get("theme")
    diff["themes_repo"] = repo.get("theme")
    lv = {v.get("path") or str(i): v for i, v in enumerate(live.get("views", []))}
    rv = {v.get("path") or str(i): v for i, v in enumerate(repo.get("views", []))}
    diff["vues_absentes_du_live"] = sorted(set(rv) - set(lv))
    diff["vues_absentes_du_repo"] = sorted(set(lv) - set(rv))
    diff["vues_modifiees"] = sorted(k for k in set(lv) & set(rv) if h(lv[k]) != h(rv[k]))
(DATA / "diff-live-repo.json").write_text(json.dumps(diff, ensure_ascii=False, indent=1))

# ---------------------------------------------------------------- copie des sources
for src, name in (
    (SCRATCH / "live_lovelace.json", "lovelace-live.json"),
    (SCRATCH / "live_resources.json", "ressources-enregistrees-live.json"),
    (SCRATCH / "live_states.json", "etats-entites-live.json"),
    (repo_path, "lovelace-repo.json"),
):
    if src.exists():
        shutil.copy2(src, DATA / name)

print("écrit dans", DATA)
for f in sorted(DATA.iterdir()):
    print(f"  {f.name:38} {f.stat().st_size/1024:8.1f} Ko")
print("\n-- entités:", ent_report["entites_referencees_uniques"], "référencées /",
      ent_report["entites_inexistantes"], "inexistantes /", ent_report["entites_indisponibles_ou_inconnues"], "indispo")
print("-- boutons:", len(inert), "inertes sur", sum(per_view.values()))
print("-- navigation invalide:", nav["cibles_invalides"][:10])
print("-- services appelés:", [(s["service"], s["existe"]) for s in res_report["services_appeles"]])
print("-- diff:", diff["identique"], diff.get("vues_absentes_du_live"), diff.get("vues_modifiees"))
