#!/usr/bin/env python3
"""Aperçu local du dashboard. Aucune commande n'atteint Home Assistant."""
from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def resolve(url_path: str) -> Path | None:
    path = urlparse(url_path).path
    if path == '/favicon.ico':
        return None
    if path in ('/', '/index.html'):
        return ROOT / 'preview' / 'index.html'
    if path.startswith('/local/ai-nexus-v4/visual/'):
        candidate = ROOT / 'assets' / 'visual' / Path(path).name
        return candidate if candidate.is_file() else None
    candidate = (ROOT / path.lstrip('/')).resolve()
    if not str(candidate).startswith(str(ROOT.resolve())) or not candidate.is_file():
        return None
    return candidate


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        target = resolve(self.path)
        if target is None:
            self.send_error(404)
            return
        body = target.read_bytes()
        kind = {
            '.html': 'text/html; charset=utf-8',
            '.json': 'application/json; charset=utf-8',
            '.webp': 'image/webp',
            '.css': 'text/css; charset=utf-8',
            '.js': 'text/javascript; charset=utf-8',
            '.svg': 'image/svg+xml',
        }.get(target.suffix, 'application/octet-stream')
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


def main():
    port = int(os.environ.get('PORT', '8765'))
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'Aperçu local : http://127.0.0.1:{port}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
