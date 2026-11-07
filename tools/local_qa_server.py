#!/usr/bin/env python3
"""Serveur local, en lecture seule, pour le banc navigateur AI Nexus V4.

Le serveur ne reprend ni session ni secret Home Assistant. Il expose seulement les
snapshots explicitement nécessaires au banc et relaie trois familles d'assets
frontend publics en GET.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from html.parser import HTMLParser
import json
import mimetypes
from pathlib import Path
import posixpath
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen

import yaml


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ORIGIN = "http://10.0.0.47:8123"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8766
LOCAL_CARD_PATHS = ("/local/navimower-map-card.js", "/local/yamp/")
PUBLIC_ASSET_PREFIXES = ("/frontend_latest/", "/static/", "/hacsfiles/") + LOCAL_CARD_PATHS
LOCAL_FILES = {
    "/local_qa/": ROOT / "local_qa" / "index.html",
    "/local_qa/index.html": ROOT / "local_qa" / "index.html",
    "/local_qa/app.js": ROOT / "local_qa" / "app.js",
}


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def request_path_is_safe(raw_path: str) -> bool:
    """Refuse les variantes usuelles de traversal avant tout routage."""
    candidate = raw_path
    for _ in range(3):
        decoded = unquote(candidate)
        if decoded == candidate:
            break
        candidate = decoded
    if "\x00" in candidate or "\\" in candidate:
        return False
    segments = candidate.split("/")
    if any(segment in (".", "..") for segment in segments):
        return False
    # posixpath.normpath est une seconde barrière pour les formes inhabituelles.
    normalized = posixpath.normpath(candidate)
    return normalized == candidate.rstrip("/") or candidate in ("/", "/local_qa/")


def public_asset_path(raw_url: str, upstream_origin: str = UPSTREAM_ORIGIN) -> str | None:
    """Retourne path+query seulement pour un asset public du même serveur."""
    parsed = urlsplit(raw_url)
    origin = urlsplit(upstream_origin)
    if parsed.scheme or parsed.netloc:
        if (parsed.scheme, parsed.netloc) != (origin.scheme, origin.netloc):
            return None
    if not request_path_is_safe(parsed.path):
        return None
    if not any(parsed.path.startswith(prefix) for prefix in PUBLIC_ASSET_PREFIXES):
        return None
    return parsed.path + (("?" + parsed.query) if parsed.query else "")


class FrontendHTMLParser(HTMLParser):
    def __init__(self, upstream_origin: str = UPSTREAM_ORIGIN) -> None:
        super().__init__(convert_charrefs=True)
        self.upstream_origin = upstream_origin
        self.scripts: list[str] = []
        self.preloads: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "script" and values.get("src"):
            asset = public_asset_path(values["src"], self.upstream_origin)
            if asset:
                self.scripts.append(asset)
        elif tag.lower() == "link" and values.get("href"):
            relation = {item.lower() for item in values.get("rel", "").split()}
            if "modulepreload" in relation:
                asset = public_asset_path(values["href"], self.upstream_origin)
                if asset:
                    self.preloads.append(asset)


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def discover_frontend_assets(html: str, upstream_origin: str = UPSTREAM_ORIGIN) -> dict[str, list[str]]:
    """Extrait sans exécuter l'HTML les entrypoints frontend publics."""
    parser = FrontendHTMLParser(upstream_origin)
    parser.feed(html)
    scripts = _unique(parser.scripts)
    preloads = _unique(parser.preloads)
    candidates = _unique(scripts + preloads)

    def named(prefix: str) -> list[str]:
        return [
            value for value in candidates
            if Path(urlsplit(value).path).name.lower().startswith(prefix)
        ]

    return {
        "scripts": scripts,
        "modulepreloads": preloads,
        "core": named("core"),
        "app": named("app"),
    }


def normalize_resource_prefix(value: str) -> str:
    value = value.strip()
    if not value.startswith("/"):
        value = "/" + value
    if not value.endswith("/"):
        value += "/"
    if value not in PUBLIC_ASSET_PREFIXES:
        allowed = ", ".join(PUBLIC_ASSET_PREFIXES)
        raise ValueError(f"préfixe de ressources interdit ({value}); valeurs: {allowed}")
    return value


@dataclass(frozen=True)
class QARepository:
    root: Path = ROOT

    @property
    def dashboard_path(self) -> Path:
        return self.root / "config" / "ai-nexus-v4.json"

    @property
    def states_path(self) -> Path:
        return self.root / "data" / "states.json"

    @property
    def resources_path(self) -> Path:
        return self.root / "data" / "resources.json"

    @property
    def theme_path(self) -> Path:
        return self.root / "config" / "ai-nexus-glass.yaml"

    @property
    def hass_config_path(self) -> Path:
        preferred = self.root / "data" / "ha_config.json"
        return preferred if preferred.is_file() else self.root / "data" / "config.json"

    def read_json(self, path: Path) -> object:
        return json.loads(path.read_text(encoding="utf-8"))

    def bootstrap(
        self,
        frontend: dict[str, list[str]],
        resource_prefix: str,
        discovery_warning: str | None = None,
    ) -> dict[str, object]:
        resources = self.read_json(self.resources_path)
        allowed: list[dict[str, str]] = []
        skipped: list[dict[str, str]] = []
        for row in resources:
            url = row.get("url", "")
            safe_url = public_asset_path(url)
            if safe_url and (urlsplit(safe_url).path.startswith(resource_prefix) or
                             any(urlsplit(safe_url).path.startswith(p) for p in LOCAL_CARD_PATHS)):
                allowed.append({"url": safe_url, "type": row.get("type", "module")})
            else:
                skipped.append({"url": url, "reason": "hors du préfixe public configuré"})

        raw_theme = yaml.safe_load(self.theme_path.read_text(encoding="utf-8")) or {}
        warnings: list[str] = []
        if self.hass_config_path.name != "ha_config.json":
            warnings.append("data/ha_config.json absent : repli explicite sur data/config.json.")
        if discovery_warning:
            warnings.append(discovery_warning)
        if not frontend["core"]:
            warnings.append("Aucun entrypoint core identifié dans l’HTML public amont.")
        if not frontend["app"]:
            warnings.append("Aucun entrypoint app identifié dans l’HTML public amont.")
        if skipped:
            warnings.append(
                f"{len(skipped)} ressource(s) ignorée(s), car non relayée(s) par le banc local."
            )

        return {
            "schema_version": 1,
            "mode": "snapshot-read-only",
            "frontend": frontend,
            "resources": allowed,
            "skipped_resources": skipped,
            "resource_prefix": resource_prefix,
            "config": self.read_json(self.hass_config_path),
            "themes": {
                "themes": raw_theme,
                "default_theme": "AI Nexus Glass",
                "default_dark_theme": "AI Nexus Glass",
            },
            "locale": {
                "language": "fr",
                "number_format": "language",
                "time_format": "language",
                "first_weekday": "language",
            },
            "user": {
                "id": "local-qa-mock",
                "name": "QA locale (utilisateur simulé)",
                "is_admin": False,
                "is_owner": False,
            },
            "warnings": warnings,
        }


UpstreamOpen = Callable[..., object]


def fetch_frontend_html(
    opener: UpstreamOpen = urlopen,
    upstream_origin: str = UPSTREAM_ORIGIN,
) -> str:
    request = Request(
        upstream_origin + "/",
        headers={"Accept": "text/html", "User-Agent": "AI-Nexus-Local-QA/1"},
        method="GET",
    )
    with opener(request, timeout=5) as response:
        return response.read(2 * 1024 * 1024).decode("utf-8", errors="replace")


def build_handler(
    repository: QARepository | None = None,
    resource_prefix: str = "/hacsfiles/",
    opener: UpstreamOpen = urlopen,
    upstream_origin: str = UPSTREAM_ORIGIN,
) -> type[BaseHTTPRequestHandler]:
    repository = repository or QARepository()
    resource_prefix = normalize_resource_prefix(resource_prefix)

    class LocalQAHandler(BaseHTTPRequestHandler):
        server_version = "AI-Nexus-Local-QA/1"

        def log_message(self, format: str, *args: object) -> None:
            print(f"[local-qa] {self.address_string()} {format % args}")

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; worker-src 'self' blob:")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, value: object) -> None:
            self._send(status, json_bytes(value), "application/json; charset=utf-8")

        def _error(self, status: int, message: str) -> None:
            self._json(status, {"error": message})

        def do_POST(self) -> None:
            self._error(405, "méthode refusée : banc local en lecture seule")

        do_PUT = do_POST
        do_DELETE = do_POST
        do_PATCH = do_POST

        def do_GET(self) -> None:
            parsed = urlsplit(self.path)
            path = parsed.path
            if not request_path_is_safe(path):
                self._error(400, "chemin refusé")
                return
            if path == "/":
                self.send_response(302)
                self.send_header("Location", "/local_qa/")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if path in LOCAL_FILES:
                target = repository.root / LOCAL_FILES[path].relative_to(ROOT)
                if not target.is_file():
                    self._error(404, "fichier QA absent")
                    return
                content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                if content_type.startswith("text/") or content_type in ("application/javascript",):
                    content_type += "; charset=utf-8"
                self._send(200, target.read_bytes(), content_type)
                return
            if path.startswith('/local/ai-nexus-v4/visual/'):
                relative = path.removeprefix('/local/ai-nexus-v4/visual/')
                target = repository.root / 'assets/visual' / relative
                if '/' in relative or not target.is_file() or target.suffix != '.webp':
                    self._error(404, 'asset illustratif absent')
                    return
                self._send(200, target.read_bytes(), 'image/webp')
                return
            if path == "/qa/dashboard":
                self._send(200, repository.dashboard_path.read_bytes(), "application/json; charset=utf-8")
                return
            if path == "/qa/states":
                self._send(200, repository.states_path.read_bytes(), "application/json; charset=utf-8")
                return
            if path == "/frontend_latest/qa-loader.js":
                # Local-only boot adapter: unchanged HA components, no auth entry.
                html = fetch_frontend_html(opener, upstream_origin)
                app_path = discover_frontend_assets(html, upstream_origin)['app'][0]
                with opener(Request(urljoin(upstream_origin + '/', app_path.lstrip('/')), method='GET'), timeout=15) as response:
                    source = response.read(32 * 1024 * 1024).decode('utf-8')
                panel = re.search(r'lovelace:\{load:\(\)=>Promise\.all\(\[(.*?)\]\)\.then\(a\.bind\(a,(\d+)\)\)', source)
                if not panel or source.count('o(91535);') != 1:
                    self._error(502, 'Version frontend non compatible avec le chargeur QA isolé')
                    return
                chunks = re.findall(r'a\.e\((\d+)\)', panel.group(1))
                loader = ('window.__qaFrontendRequire=o;window.__qaFrontendReady='
                          + 'Promise.all(' + json.dumps(chunks)
                          + '.map(id=>o.e(Number(id)))).then(()=>o(' + panel.group(2) + '));')
                source = source.replace('o(91535);', loader)
                self._send(200, source.encode(), 'text/javascript; charset=utf-8')
                return
            if path == "/qa/bootstrap":
                warning = None
                try:
                    html = fetch_frontend_html(opener, upstream_origin)
                    frontend = discover_frontend_assets(html, upstream_origin)
                except (HTTPError, URLError, OSError, TimeoutError) as error:
                    frontend = {"scripts": [], "modulepreloads": [], "core": [], "app": []}
                    warning = f"Découverte frontend amont indisponible : {type(error).__name__}."
                self._json(200, repository.bootstrap(frontend, resource_prefix, warning))
                return
            if any(path.startswith(prefix) for prefix in PUBLIC_ASSET_PREFIXES):
                self._proxy_asset(path, parsed.query)
                return
            self._error(404, "route non exposée par le banc local")

        def _proxy_asset(self, path: str, query: str) -> None:
            safe = public_asset_path(path + (("?" + query) if query else ""), upstream_origin)
            if not safe:
                self._error(403, "asset public refusé")
                return
            request = Request(
                urljoin(upstream_origin + "/", safe.lstrip("/")),
                headers={"Accept": "*/*", "User-Agent": "AI-Nexus-Local-QA/1"},
                method="GET",
            )
            try:
                with opener(request, timeout=10) as response:
                    body = response.read(32 * 1024 * 1024)
                    content_type = response.headers.get_content_type()
                    charset = response.headers.get_content_charset()
                    if charset:
                        content_type += f"; charset={charset}"
                    self._send(response.status, body, content_type)
            except HTTPError as error:
                self._error(error.code, "asset public amont indisponible")
            except (URLError, OSError, TimeoutError) as error:
                self._error(502, f"asset public amont indisponible : {type(error).__name__}")

    return LocalQAHandler


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--resource-prefix",
        default="/hacsfiles/",
        help="famille de ressources custom publiques à exposer au client",
    )
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port doit être compris entre 1 et 65535")
    try:
        args.resource_prefix = normalize_resource_prefix(args.resource_prefix)
    except ValueError as error:
        parser.error(str(error))
    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    handler = build_handler(resource_prefix=args.resource_prefix)
    server = ThreadingHTTPServer((DEFAULT_HOST, args.port), handler)
    print(f"Banc QA local : http://{DEFAULT_HOST}:{args.port}/local_qa/")
    print("Lecture seule : snapshots locaux et assets frontend publics uniquement.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
