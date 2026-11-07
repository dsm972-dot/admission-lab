#!/usr/bin/env python3
"""Real Chromium snapshot matrix, explicitly NOT connected-dashboard QA."""
from pathlib import Path
import json
import subprocess
import time
import argparse
from urllib.request import urlopen
from urllib.parse import urlsplit, urlunsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--out', default='evidence/local-browser')
parser.add_argument('--port', type=int, default=8768)
args = parser.parse_args()
OUT = ROOT / args.out
OUT.mkdir(parents=True, exist_ok=True)
ORIGIN = f'http://127.0.0.1:{args.port}'
VIEWPORTS = {
    'desktop': {'width': 1920, 'height': 1080},
    'desktop-large': {'width': 2560, 'height': 1440},
    'phone-portrait': {'width': 412, 'height': 915},
    'phone-landscape': {'width': 915, 'height': 412},
    'tablet': {'width': 1280, 'height': 800},
    'phone-wide': {'width':480,'height':960},
    'phone-large': {'width':600,'height':960},
}
server = subprocess.Popen(['python3', 'tools/local_qa_server.py', '--port', str(args.port)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
result = {'mode': 'snapshot-read-only', 'qualification': 'NOT_PRODUCTION_QA', 'samples': [], 'limitations': ['Responsive CSS approximation, not the native HA sections shell', 'S25 Ultra CSS-sized proxy, not a physical device', 'No authenticated connection, reconnect, live actions or canary tested']}
try:
    for attempt in range(60):
        try:
            with urlopen(ORIGIN + '/qa/states', timeout=2):
                break
        except OSError:
            if server.poll() is not None:
                raise RuntimeError('Local QA server exited')
            time.sleep(.25)
    else:
        raise RuntimeError('Local QA server readiness failed')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport=VIEWPORTS['desktop'])
        errors = []
        requests = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        def log_request(req):
            # Snapshot image URLs may carry camera access tokens. Never persist queries.
            url = urlsplit(req.url)
            requests.append({'method': req.method, 'url': urlunsplit((url.scheme, url.netloc, url.path, '', ''))})
        page.on('request', log_request)
        started = time.perf_counter()
        page.goto(ORIGIN + '/local_qa/', wait_until='networkidle', timeout=90000)
        page.wait_for_function("window.qa && window.qa.renderer !== 'pending' && window.qa.renderer !== 'initializing' && ['real-cards-css-layout-approximation','native-sections','failed'].includes(window.qa.renderer)", timeout=90000)
        page.wait_for_timeout(2500)
        result['cold_load_seconds'] = round(time.perf_counter() - started, 3)
        views = page.locator('#view-select option').evaluate_all('(items) => items.map(x => ({value:x.value,title:x.textContent}))')
        result['views'] = views
        for name, viewport in VIEWPORTS.items():
            page.set_viewport_size(viewport)
            for view in views:
                started = time.perf_counter()
                page.select_option('#view-select', view['value'])
                page.wait_for_timeout(600)
                diagnostics = page.evaluate('({renderer:qa.renderer,errors:[...qa.errors],warnings:[...qa.warnings],limitations:[...new Set(qa.limitations)]})')
                filename = f"{name}-view-{int(view['value']):02d}.png"
                page.screenshot(path=str(OUT / filename), full_page=False)
                if view['value'] == '0':
                    page.locator('#view-host').screenshot(path=str(OUT / f'{name}-accueil-complet.png'))
                    diagnostics['document_overflow'] = page.evaluate('document.documentElement.scrollWidth > innerWidth')
                result['samples'].append({'viewport':name,'view':view, 'elapsed_seconds': round(time.perf_counter()-started,3), 'screenshot':filename, **diagnostics})
            print(f"completed {name}: {len(views)} views", flush=True)
        page.set_viewport_size(VIEWPORTS['desktop'])
        page.select_option('#view-select', '0')
        page.locator('#theme-toggle').click()
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / 'desktop-dark.png'))
        result['dark_theme_rendered'] = True
        result['qa'] = page.evaluate('window.qa')
        result['page_errors'] = errors
        result['requests'] = requests
        result['sample_count'] = len(result['samples'])
        result['expected_sample_count'] = len(views) * len(VIEWPORTS)
        result['count_verified'] = result['sample_count'] == result['expected_sample_count']
        result['mutation_requests'] = [r for r in requests if r['method'] not in ('GET', 'HEAD')]
        result['unique_errors'] = sorted(set(errors + result['qa']['errors']))
        (OUT / 'matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({k:result[k] for k in ['qualification','cold_load_seconds','sample_count','expected_sample_count','count_verified','mutation_requests','unique_errors']},ensure_ascii=False,indent=2))
        browser.close()
finally:
    server.terminate()
    try:
        server.wait(5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(5)
