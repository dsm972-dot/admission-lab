#!/usr/bin/env python3
"""Capture le dashboard AI Nexus Home V4 tel qu'il est réellement rendu dans HA.

Usage: python3 tools/capture_live_dashboard.py [--url-path ai-nexus-v4]
Sortie: <handoff>/assets/captures-live/*.png + console-errors.json + rendition.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ha_client import HA_URL, load_token  # noqa: E402

URL_PATH = "ai-nexus-v4"
OUT = Path("/root/workspace/maison/ai-nexus-handoff-20261106/assets/captures-live")
OUT.mkdir(parents=True, exist_ok=True)

live = json.load(open("/root/.hermes/cache/scratch/nexus/live_lovelace.json"))["data"]["config"]
views = live["views"]
base = HA_URL.rstrip("/")
token = load_token()

errors: list[dict] = []
shots: list[dict] = []


def attach(page, label):
    def on_console(m):
        if m.type in ("error", "warning"):
            errors.append({"view": label, "kind": m.type, "text": m.text[:400]})

    page.on("console", on_console)
    page.on("pageerror", lambda e: errors.append({"view": label, "kind": "pageerror", "text": str(e)[:400]}))


def prepare(ctx):
    # injecte le jeton avant le chargement de chaque page (evite la page de login)
    ctx.add_init_script(
        """try { localStorage.setItem('hassTokens', JSON.stringify({
             access_token: %s, token_type: 'Bearer', expires_in: 1800,
             hassUrl: %s, clientId: null, expires: Date.now() + 1800000 })); } catch (e) {}"""
        % (json.dumps(token), json.dumps(base))
    )
    return ctx.new_page()


with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/chromium",
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    )

    # --- Desktop ---
    ctx = browser.new_context(viewport={"width": 1512, "height": 1000}, locale="fr-FR")
    page = prepare(ctx)
    for i, v in enumerate(views):
        path = v.get("path") or str(i)
        title = v.get("title") or path
        label = f"desktop/{i:02d}-{path}"
        attach(page, label)
        try:
            page.goto(f"{base}/{URL_PATH}/{path}", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(6000)
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            page.wait_for_timeout(1500)
            f = OUT / f"{label}.png"
            page.screenshot(path=str(f), full_page=True)
            h = page.evaluate("() => document.querySelector('hui-view') ? document.querySelector('hui-view').scrollHeight : 0")
            shots.append({"view": title, "path": path, "file": f.name, "height_px": h})
            print(f"OK {label} h={h}")
        except Exception as e:
            errors.append({"view": label, "kind": "capture", "text": str(e)[:300]})
            print(f"FAIL {label}: {e}")

    # --- Mobile (accueil + pieces) ---
    m = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=2,
        is_mobile=True,
        has_touch=True,
        locale="fr-FR",
    )
    mp = prepare(m)
    for path in ("accueil", "pieces", "voiture"):
        label = f"mobile/{path}"
        attach(mp, label)
        try:
            mp.goto(f"{base}/{URL_PATH}/{path}", wait_until="domcontentloaded", timeout=60000)
            mp.wait_for_timeout(6000)
            f = OUT / f"{label}.png"
            mp.screenshot(path=str(f), full_page=True)
            shots.append({"view": path, "path": path, "file": f.name, "device": "mobile"})
            print(f"OK {label}")
        except Exception as e:
            errors.append({"view": label, "kind": "capture", "text": str(e)[:300]})

    browser.close()

(OUT / "console-errors.json").write_text(json.dumps(errors, ensure_ascii=False, indent=1))
(OUT / "rendition.json").write_text(json.dumps(shots, ensure_ascii=False, indent=1))

seen = {}
for e in errors:
    seen.setdefault(e["text"][:160], []).append(e["view"])
print("\n--- erreurs/avertissements distincts:", len(seen), "| total:", len(errors))
for t, where in list(seen.items())[:40]:
    print(f"[{len(where)}] {t}")
