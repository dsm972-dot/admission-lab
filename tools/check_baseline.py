#!/usr/bin/env python3
"""Read-only baseline/resource checks. Never print states or secrets."""
import hashlib
import json
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from ha_client import HA, HA_URL

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def main():
    h = HA()
    resources = h.resources()
    dashboards = h.dashboards()
    config = h.config()
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'core_version': config['version'],
              'resources_hash': digest(resources), 'dashboards_hash': digest(dashboards),
              'legacy_default_hash': digest(h.read_dashboard(None)), 'resource_http': [],
              'dashboard_checks': [], 'browser_authenticated': False}
    for d in dashboards:
        path = d['url_path']
        snapshot = h.read_dashboard(path)
        report['dashboard_checks'].append({'url_path': path, 'hash': digest(snapshot), 'views': len(snapshot.get('views', []))})
    counts = Counter(r['url'].split('?')[0] for r in resources)
    report['duplicate_resources'] = {u:n for u,n in counts.items() if n > 1}
    for r in resources:
        url = r['url']
        if not url.startswith('/') or url.startswith('//'):
            report['resource_http'].append({'url':url, 'status':'SKIPPED_EXTERNAL'})
            continue
        try:
            with urllib.request.urlopen(HA_URL + url, timeout=30) as resp:
                report['resource_http'].append({'url':url,'status':resp.status,'content_type':resp.headers.get('Content-Type')})
        except urllib.error.HTTPError as e:
            report['resource_http'].append({'url':url,'status':e.code})
        except (urllib.error.URLError, TimeoutError):
            report['resource_http'].append({'url':url,'status':'NETWORK_ERROR'})
    baseline = DATA / 'baseline_fingerprints.json'
    if baseline.exists():
        previous = json.loads(baseline.read_text())
        report['legacy_unchanged'] = all(report[k] == previous[k] for k in ('resources_hash','dashboards_hash','legacy_default_hash','dashboard_checks'))
        (DATA / 'baseline_readback.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        baseline.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
