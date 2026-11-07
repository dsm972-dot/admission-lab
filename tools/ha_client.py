#!/usr/bin/env python3
"""Client Home Assistant pour AI Nexus Home V4.

- REST lecture seule (etat, config, services) : /api/
- WebSocket : dashboards Lovelace (creation, lecture, sauvegarde)
- Supervisor : backups (via proxy HA -> http://supervisor)

Aucune action actionneur. Le token est lu depuis /root/.hermes/.env (jamais imprime).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import aiohttp

HA_URL = os.environ.get("HASS_SERVER", "http://10.0.0.47:8123")
ENV_FILE = Path("/root/.hermes/.env")
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load_token() -> str:
    tok = os.environ.get("HA_TOKEN")
    if tok:
        return tok
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("HA_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("HA_TOKEN introuvable")


class HA:
    def __init__(self, token: str | None = None):
        self.token = token or load_token()
        self._id = 0

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    # ---------------- REST ----------------
    def rest_get(self, path: str, params: dict | None = None):
        import urllib.request

        url = f"{HA_URL}{path}"
        if params:
            from urllib.parse import urlencode

            url += "?" + urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.token}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())

    def states(self) -> list[dict]:
        return self.rest_get("/api/states")

    def config(self) -> dict:
        return self.rest_get("/api/config")

    def services(self) -> list[dict]:
        return self.rest_get("/api/services")

    # ---------------- WebSocket ----------------
    async def _ws_cmd_many(self, cmds: list[dict]):
        async with aiohttp.ClientSession() as session:
            ws = await session.ws_connect(f"{HA_URL}/api/websocket", heartbeat=30)
            await ws.receive_json()  # auth_required
            await ws.send_json({"type": "auth", "access_token": self.token})
            auth = await ws.receive_json()
            if auth.get("type") != "auth_ok":
                raise SystemExit("auth échouée")
            results = []
            for cmd in cmds:
                cmd = dict(cmd)
                cmd["id"] = self._next_id()
                await ws.send_json(cmd)
                while True:
                    msg = await ws.receive_json()
                    if msg.get("id") == cmd["id"]:
                        results.append(msg)
                        break
            await ws.close()
            return results

    def ws(self, cmds: list[dict]):
        return asyncio.run(self._ws_cmd_many(cmds))

    def ws_one(self, cmd: dict):
        return self.ws([cmd])[0]

    # ---------------- Raccourcis Lovelace ----------------
    def dashboards(self) -> list[dict]:
        r = self.ws_one({"type": "lovelace/dashboards/list"})
        return r.get("result", []) if r.get("success") else []

    def resources(self) -> list[dict]:
        r = self.ws_one({"type": "lovelace/resources"})
        return r.get("result", []) if r.get("success") else []

    def read_dashboard(self, url_path: str | None, force: bool = False) -> dict:
        r = self.ws_one({"type": "lovelace/config", "url_path": url_path, "force": force})
        if not r.get("success"):
            raise RuntimeError(f"lecture dashboard impossible: {r}")
        return r["result"]

    def save_dashboard(self, url_path: str | None, config: dict, force: bool = False) -> dict:
        r = self.ws_one(
            {"type": "lovelace/config/save", "url_path": url_path, "config": config}
        )
        if not r.get("success"):
            raise RuntimeError(f"sauvegarde dashboard impossible: {r}")
        return r

    def create_dashboard(
        self,
        url_path: str,
        title: str,
        icon: str,
        show_in_sidebar: bool = True,
        require_admin: bool = True,
        mode: str = "storage",
    ) -> dict:
        return self.ws_one(
            {
                "type": "lovelace/dashboards/create",
                "url_path": url_path,
                "title": title,
                "icon": icon,
                "show_in_sidebar": show_in_sidebar,
                "require_admin": require_admin,
                "mode": mode,
            }
        )

    def service(self, domain: str, service: str, data: dict | None = None):
        """Appel de service REST (utilise uniquement pour les rechargements inoffensifs)."""
        import urllib.request

        if (domain, service) != ("frontend", "reload_themes"):
            raise PermissionError("Contrôle physique HA interdit : seul frontend.reload_themes est autorisé")
        req = urllib.request.Request(
            f"{HA_URL}/api/services/{domain}/{service}",
            data=json.dumps(data or {}).encode(),
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode() or "[]")

    def delete_dashboard(self, url_path: str) -> dict:
        return self.ws_one({"type": "lovelace/dashboards/delete", "dashboard_id": url_path})

    # ---------------- Frontend / themes ----------------
    def themes(self) -> list[dict]:
        try:
            return self.rest_get("/api/frontend/themes")  # peut ne pas exister
        except Exception:
            return []


def dump(name: str, obj) -> Path:
    DATA.mkdir(exist_ok=True)
    p = DATA / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1))
    return p


if __name__ == "__main__":
    ha = HA()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "info"
    if cmd == "info":
        st = ha.states()
        cfg = ha.config()
        print("version", cfg.get("version"), "state", cfg.get("state"))
        print("entities", len(st))
        print("dashboards", json.dumps(ha.dashboards(), ensure_ascii=False)[:2000])
        print("resources", len(ha.resources()))
    elif cmd == "dump":
        dump("states.json", ha.states())
        dump("config.json", ha.config())
        dump("dashboards.json", ha.dashboards())
        dump("resources.json", ha.resources())
        print("dumped")
    elif cmd == "legacy":
        # Export de sauvegarde des dashboards EXISTANTS (lecture seule, aucune ecriture).
        for url_path, fname in (
            ("lovelace", "legacy_lovelace.json"),
            ("dashboard-map", "legacy_dashboard_map.json"),
            ("navimow-view", "legacy_navimow_view.json"),
        ):
            cfg = ha.read_dashboard(url_path, force=True)
            p = dump(fname, cfg)
            views = cfg.get("views", []) if isinstance(cfg, dict) else []
            print(f"{fname}: {p.stat().st_size} octets, {len(views)} vues")
    elif cmd == "themes":
        print(json.dumps(ha.themes(), ensure_ascii=False)[:3000])
    elif cmd == "reload-themes":
        print(json.dumps(ha.service("frontend", "reload_themes"), ensure_ascii=False)[:500])
