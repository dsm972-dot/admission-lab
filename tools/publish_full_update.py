#!/usr/bin/env python3
"""Publish full generator update to existing ai-nexus-v4 dashboard.

Follows same safety patterns as publish_candidate.py and energy enrichment:
- Snapshot live before change
- Validate generator output against live HA
- Write only via WebSocket (save_dashboard)
- Verify readback matches exactly
- Preserve theme, resources, other dashboards, defaults
- Rollback capability
"""
import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from ha_client import HA, HA_URL  # noqa: E402
from build_dashboard import validate, references, service_names, walk, RESOURCE  # noqa: E402
import urllib.request
import yaml

DASH = "ai-nexus-v4"
THEME_PATH = "/homeassistant/themes/ai-nexus-glass.yaml"
# Propriétés de vue décidées dans l'interface HA et non produites par le générateur.
# Sans cette reprise, publier exposerait à tous une vue restreinte à certains comptes.
USER_OWNED_VIEW_KEYS = ("visible",)
BACKUP_DIR = ROOT / "data" / f"full-update-{datetime.now().strftime('%Y%m%d')}"


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def store(name, obj):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    (BACKUP_DIR / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2))


def load(name):
    return json.loads((BACKUP_DIR / name).read_text())


def snapshot(h):
    dashboards = h.ws_one({"type": "lovelace/dashboards/list"})["result"]
    return {
        "dashboards": dashboards,
        "resources": h.ws_one({"type": "lovelace/resources"})["result"],
        "default_hash": digest(h.read_dashboard(None)),
        "configs": {
            d["url_path"]: digest(h.read_dashboard(d["url_path"]))
            for d in dashboards if d["url_path"] != DASH
        },
        "themes": h.ws_one({"type": "frontend/get_themes"})["result"],
        "version": h.config()["version"],
    }


def theme_hash():
    import subprocess
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "ha", "sudo python3 -c",
         f"import json,hashlib; from pathlib import Path; p=Path('{THEME_PATH}'); print(json.dumps(hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None))"],
        capture_output=True, text=True, timeout=30
    ).stdout.strip()


def artifact():
    data = json.loads((ROOT / "config/ai-nexus-v4.json").read_text())
    assert data == yaml.safe_load((ROOT / "config/ai-nexus-v4.yaml").read_text())
    registration = json.loads((ROOT / "config/ai-nexus-v4-registration.json").read_text())
    assert registration["url_path"] == DASH and registration["require_admin"] is True
    assert registration["mode"] == "storage"
    return data, registration


def resources_http(h, cfg):
    resources = h.ws_one({"type": "lovelace/resources"})["result"]
    needed = {RESOURCE[n["type"][7:]] for n in walk(cfg) if n.get("type", "").startswith("custom:")}
    report = []
    for name in sorted(needed):
        urls = [r["url"] for r in resources if r["url"].split("?")[0].endswith("/" + name)]
        assert urls, f"missing frontend resource: {name}"
        for url in urls:
            assert url.startswith("/") and not url.startswith("//")
            with urllib.request.urlopen(HA_URL + url, timeout=30) as resp:
                assert resp.status == 200 and "javascript" in resp.headers.get("Content-Type", "")
                report.append({"url": url, "status": resp.status})
    return report


def unchanged(before, now):
    assert before["resources"] == now["resources"], "Resources changed"
    assert before["default_hash"] == now["default_hash"], "Default dashboard changed"
    assert before["configs"] == now["configs"], "Existing dashboard changed"
    assert before["version"] == now["version"], "HA version changed"
    old_before = [d for d in before["dashboards"] if d["url_path"] != DASH]
    old = [d for d in now["dashboards"] if d["url_path"] != DASH]
    assert old == old_before, "Existing dashboard registrations changed"
    current_themes = dict(now["themes"])
    current_themes["themes"] = {k: v for k, v in current_themes["themes"].items() if k != "AI Nexus Glass"}
    assert current_themes == before["themes"], "Existing themes/default theme changed"


def preserve_view_properties(live: dict, cfg: dict) -> list[dict]:
    """Reprend les propriétés de vue possédées par l'interface HA (ex. `visible`).

    Copie uniquement si la clé est ABSENTE du candidat : une valeur produite
    explicitement par le générateur reste prioritaire. Idempotent.
    """
    by_path = {v.get("path"): v for v in live.get("views", [])}
    applied = []
    for view in cfg.get("views", []):
        src = by_path.get(view.get("path"))
        if not src:
            continue
        for key in USER_OWNED_VIEW_KEYS:
            if key in src and key not in view:
                view[key] = copy.deepcopy(src[key])
                applied.append({"view": view.get("path"), "key": key})
    return applied


def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    h = HA()
    cfg, registration = artifact()

    # Reprendre AVANT tout calcul d'empreinte les propriétés de vue possédées par HA
    live = h.read_dashboard(DASH, force=True)
    preserved_views = preserve_view_properties(live, cfg)
    for item in preserved_views:
        print(f"[info] propriété de vue reprise depuis le live : {item['view']} / {item['key']}")

    # Load states and validate
    states = {s["entity_id"]: s for s in h.states()}
    validate(cfg, states, h.ws_one({"type": "lovelace/resources"})["result"], service_names(h.services()))

    # Snapshot before
    before = snapshot(h)
    before["candidate_hash"] = digest(cfg)
    before["candidate_theme_sha256"] = hashlib.sha256((ROOT / "config/ai-nexus-glass.yaml").read_bytes()).hexdigest()
    before["checked_at"] = stamp
    before["live_entity_count"] = len(references(cfg))
    before["resource_http"] = resources_http(h, cfg)
    store("before.json", before)

    print(f"[ok] Snapshot saved: {BACKUP_DIR}/before.json")
    print(f"     Candidate hash: {before['candidate_hash']}")
    print(f"     Live views: {len(before['dashboards'])}")

    # Check current live dashboard
    live_hash = digest(live)
    print(f"     Live hash: {live_hash}")
    print(f"     Match: {live_hash == before['candidate_hash']}")

    if live_hash == before["candidate_hash"]:
        print("[ok] Live already matches generator - nothing to do")
        return 0

    # Write the generator output to the existing dashboard
    print("[info] Updating dashboard via WebSocket...")
    h.save_dashboard(DASH, cfg, force=True)

    # Verify readback
    readback = h.read_dashboard(DASH, force=True)
    rb_hash = digest(readback)
    ok = rb_hash == before["candidate_hash"]
    print(f"[{'ok' if ok else 'KO'}] Readback hash matches candidate: {ok}")

    if not ok:
        print("[error] Readback mismatch - manual intervention required")
        return 1

    # Verify theme
    th = theme_hash()
    theme_ok = th == before["candidate_theme_sha256"]
    print(f"[{'ok' if theme_ok else 'KO'}] Theme matches: {theme_ok}")

    # Verify unchanged
    now = snapshot(h)
    try:
        unchanged(before, now)
        unchanged_ok = True
        print("[ok] Other dashboards/resources/themes/defaults unchanged")
    except AssertionError as e:
        unchanged_ok = False
        print(f"[KO] Unchanged check failed: {e}")

    # Final report
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": "FULL_UPDATE_VERIFIED" if (ok and theme_ok and unchanged_ok) else "FULL_UPDATE_PARTIAL",
        "url": f"{HA_URL}/{DASH}/accueil",
        "views": len(readback["views"]),
        "dashboard_hash": rb_hash,
        "candidate_hash": before["candidate_hash"],
        "candidate_match": ok,
        "theme_sha256": th,
        "theme_match": theme_ok,
        "legacy_unchanged": unchanged_ok,
        "resources_unchanged": unchanged_ok,
        "defaults_unchanged": unchanged_ok,
        "existing_themes_unchanged": unchanged_ok,
        "preserved_view_properties": preserved_views,
        "core_version_unchanged": unchanged_ok,
        "human_validation": "PENDING",
        "browser_qa": "PENDING_DENIS",
        "canary": "PENDING",
        "physical_confirmation": "PENDING",
        "no_physical_service_sent": True,
        "no_restart_sent": True,
    }
    store("readback.json", report)
    store("dashboard-readback.json", readback)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if (ok and theme_ok and unchanged_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())