"""Regression checks for the isolated, read-only browser harness."""
import importlib.util
import sys
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

SPEC = importlib.util.spec_from_file_location('local_qa_server', Path(__file__).resolve().parents[1] / 'tools/local_qa_server.py')
assert SPEC is not None and SPEC.loader is not None
qa = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = qa
SPEC.loader.exec_module(qa)

class LocalQASecurityTests(unittest.TestCase):
    def test_no_external_origin(self):
        self.assertIsNone(qa.public_asset_path('https://example.org/hacsfiles/card.js'))

    def test_no_auth_or_api_proxy(self):
        for path in ['/api/states', '/api/websocket', '/auth/token', '/config/.storage/core.config']:
            self.assertIsNone(qa.public_asset_path(path))

    def test_no_traversal(self):
        for path in ['/static/../api/states', '/static/%2e%2e/api/states', '/static/%252e%252e/api/states', '/static/a\\b', '/static/%00x']:
            self.assertIsNone(qa.public_asset_path(path), path)

    def test_public_card_assets(self):
        for path in ['/hacsfiles/button-card/button-card.js', '/local/navimower-map-card.js', '/local/yamp/yet-another-media-player.js']:
            self.assertEqual(qa.public_asset_path(path), path)
        self.assertIsNone(qa.public_asset_path('/local/secrets.yaml'))

    def test_real_frontend_discovery(self):
        assets = qa.discover_frontend_assets('<script src="/frontend_latest/app.abc.js"></script><link rel="modulepreload" href="/frontend_latest/core.def.js">')
        self.assertEqual(assets['app'], ['/frontend_latest/app.abc.js'])
        self.assertEqual(assets['core'], ['/frontend_latest/core.def.js'])

    def test_http_mutations_and_backend_denied_without_upstream(self):
        calls = []
        def opener(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError('Denied requests must not reach HA')
        server = ThreadingHTTPServer(('127.0.0.1', 0), qa.build_handler(opener=opener))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = 'http://127.0.0.1:' + str(server.server_port)
            for method, path, expected in [('GET', '/api/states', 404), ('GET', '/api/websocket', 404), ('POST', '/api/services/light/turn_on', 405), ('PUT', '/qa/dashboard', 405), ('DELETE', '/qa/dashboard', 405), ('PATCH', '/qa/dashboard', 405)]:
                with self.assertRaises(HTTPError) as caught:
                    urlopen(Request(origin + path, method=method), timeout=3)
                self.assertEqual(caught.exception.code, expected)
            self.assertEqual(calls, [])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(3)

if __name__ == '__main__':
    unittest.main()
