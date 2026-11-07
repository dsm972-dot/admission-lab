#!/usr/bin/env python3
"""Publish existing candidate only; never change old dashboards/resources/default.
Commands: prepare, publish, verify, rollback (dry-run), rollback --apply.
No physical service is allowed: only frontend.reload_themes through HA guard.
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import yaml
from ha_client import HA, HA_URL
from build_dashboard import validate, references, service_names, walk, RESOURCE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'candidate-publication'
THEME_PATH = '/config/themes/ai-nexus-glass.yaml'
SLUG = 'ai-nexus-v4'


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def store(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2))


def load(name):
    return json.loads((OUT / name).read_text())


def ssh(code):
    p = subprocess.run(['ssh', '-o', 'BatchMode=yes', 'ha', 'sudo python3 -'],
                       input=code, text=True, capture_output=True, timeout=120)
    if p.returncode:
        raise RuntimeError('SSH operation failed: ' + p.stderr[:300])
    return json.loads(p.stdout)


def result(h, cmd):
    response = h.ws_one(cmd)
    if not response.get('success'):
        raise RuntimeError('WS command failed: ' + cmd['type'])
    return response['result']


def snapshot(h):
    dashboards = result(h, {'type': 'lovelace/dashboards/list'})
    return {'dashboards': dashboards,
            'resources': result(h, {'type': 'lovelace/resources'}),
            'default_hash': digest(h.read_dashboard(None)),
            'configs': {d['url_path']: digest(h.read_dashboard(d['url_path']))
                        for d in dashboards if d['url_path'] != SLUG},
            'themes': result(h, {'type': 'frontend/get_themes'}),
            'version': h.config()['version']}


def remote_hashes():
    return ssh('''import json,hashlib
from pathlib import Path
paths=[Path('/config/configuration.yaml')]+list(Path('/config/.storage').glob('frontend.user_data*'))
print(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}))
''')


def theme_hash():
    return ssh('import json,hashlib; from pathlib import Path; p=Path(' + repr(THEME_PATH) + '); print(json.dumps(hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None))')


def artifact():
    data = json.loads((ROOT / 'config/ai-nexus-v4.json').read_text())
    assert data == yaml.safe_load((ROOT / 'config/ai-nexus-v4.yaml').read_text())
    registration = json.loads((ROOT / 'config/ai-nexus-v4-registration.json').read_text())
    assert registration['url_path'] == SLUG and registration['require_admin'] is True
    assert registration['mode'] == 'storage'
    return data, registration


def resources_http(h, cfg):
    resources = result(h, {'type': 'lovelace/resources'})
    needed = {RESOURCE[n['type'][7:]] for n in walk(cfg) if n.get('type', '').startswith('custom:')}
    report = []
    for name in sorted(needed):
        urls = [r['url'] for r in resources if r['url'].split('?')[0].endswith('/' + name)]
        assert urls, 'missing frontend resource: ' + name
        for url in urls:
            assert url.startswith('/') and not url.startswith('//')
            with urllib.request.urlopen(HA_URL + url, timeout=30) as resp:
                assert resp.status == 200 and 'javascript' in resp.headers.get('Content-Type', '')
                report.append({'url': url, 'status': resp.status})
    return report


def prepare():
    assert not (OUT / 'before.json').exists(), 'Prepublication snapshot already exists; do not overwrite'
    h = HA()
    cfg, registration = artifact()
    before = snapshot(h)
    assert not any(d['url_path'] == SLUG for d in before['dashboards']), 'V4 already exists'
    assert 'AI Nexus Glass' not in before['themes']['themes'], 'Theme already exists'
    assert theme_hash() is None, 'Theme file already exists'
    states = {s['entity_id']: s for s in h.states()}
    validate(cfg, states, before['resources'], service_names(h.services()))
    backup = json.loads((ROOT / 'data/backup_verified.json').read_text())
    assert backup['core_gzip_verified'] is True and backup['metadata']['type'] == 'full'
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(backup['metadata']['date'])).total_seconds()
    assert 0 <= age < 86400, 'Backup older than 24 hours'
    remote = ssh('''import json,os,tarfile
p='/backup/d2150955.tar'
with tarfile.open(p) as t:
 meta=json.load(t.extractfile('./backup.json'))
 members=[{'name':m.name,'size':m.size} for m in t]
s=os.stat(p)
print(json.dumps({'size':s.st_size,'mtime':s.st_mtime,'metadata':meta,'members':members}))
''')
    assert remote['size'] == backup['size'] and remote['mtime'] == backup['mtime']
    assert remote['metadata'] == backup['metadata'] and remote['members'] == backup['members']
    before['file_hashes'] = remote_hashes()
    before['candidate_hash'] = digest(cfg)
    before['candidate_theme_sha256'] = hashlib.sha256((ROOT / 'config/ai-nexus-glass.yaml').read_bytes()).hexdigest()
    before['checked_at'] = datetime.now(timezone.utc).isoformat()
    before['backup'] = {'slug': backup['metadata']['slug'], 'size': remote['size'], 'age_seconds': age,
                        'outer_inventory_matches': True, 'core_gzip_previously_verified': True,
                        'restore_tested': False, 'all_addons_integrity_tested': False}
    before['live_entity_count'] = len(references(cfg))
    before['resource_http'] = resources_http(h, cfg)
    store('before.json', before)
    print(json.dumps({'prepared': True, 'views': len(cfg['views']), 'entities': before['live_entity_count'],
                      'backup': before['backup'], 'used_resources': len(before['resource_http'])}, indent=2))


def unchanged(before, now):
    assert before['resources'] == now['resources'], 'Resources changed'
    assert before['default_hash'] == now['default_hash'], 'Default dashboard changed'
    assert before['configs'] == now['configs'], 'Existing dashboard changed'
    assert before['version'] == now['version'], 'HA version changed'
    assert before['file_hashes'] == remote_hashes(), 'Config/default preferences changed'
    old = [d for d in now['dashboards'] if d['url_path'] != SLUG]
    assert old == before['dashboards'], 'Existing dashboard registrations changed'
    current_themes = dict(now['themes'])
    current_themes['themes'] = {k: v for k, v in current_themes['themes'].items() if k != 'AI Nexus Glass'}
    assert current_themes == before['themes'], 'Existing themes/default theme changed'


def publish():
    h = HA()
    before = load('before.json')
    cfg, registration = artifact()
    assert digest(cfg) == before['candidate_hash']
    now = snapshot(h)
    unchanged(before, now)
    assert now['dashboards'] == before['dashboards'] and now['themes'] == before['themes']
    assert theme_hash() is None
    payload = (ROOT / 'config/ai-nexus-glass.yaml').read_bytes()
    assert hashlib.sha256(payload).hexdigest() == before['candidate_theme_sha256']
    code = 'import json; from pathlib import Path; p=Path(' + repr(THEME_PATH) + '); p.parent.mkdir(exist_ok=True); f=p.open("xb"); f.write(' + repr(payload) + '); f.close(); print(json.dumps({"created":True}))'
    ssh(code)
    assert theme_hash() == before['candidate_theme_sha256']
    h.service('frontend', 'reload_themes')
    assert result(h, {'type': 'frontend/get_themes'})['themes']['AI Nexus Glass'] == yaml.safe_load(payload)['AI Nexus Glass']
    response = h.create_dashboard(**registration)
    assert response.get('success'), 'Dashboard creation failed'
    store('created.json', response['result'])
    assert any(d == response['result'] for d in result(h, {'type': 'lovelace/dashboards/list'}))
    h.save_dashboard(SLUG, cfg)
    verify()


def verify():
    h = HA()
    before = load('before.json')
    cfg, registration = artifact()
    now = snapshot(h)
    unchanged(before, now)
    registered = next(d for d in now['dashboards'] if d['url_path'] == SLUG)
    for key, value in registration.items():
        assert registered[key] == value
    actual = h.read_dashboard(SLUG, force=True)
    assert actual == cfg and digest(actual) == before['candidate_hash']
    assert theme_hash() == before['candidate_theme_sha256']
    assert now['themes']['themes']['AI Nexus Glass'] == yaml.safe_load((ROOT / 'config/ai-nexus-glass.yaml').read_text())['AI Nexus Glass']
    http = resources_http(h, cfg)
    url = HA_URL + '/' + registered['url_path'] + '/' + actual['views'][0]['path']
    with urllib.request.urlopen(url, timeout=30) as resp:
        assert resp.status == 200 and 'text/html' in resp.headers.get('Content-Type', '')
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'status': 'PUBLISHED_CANDIDATE_VERIFIED',
              'url': url, 'views': len(actual['views']), 'dashboard_hash': digest(actual),
              'registered': registered, 'theme_sha256': theme_hash(), 'resource_http': http,
              'legacy_unchanged': True, 'resources_unchanged': True, 'defaults_unchanged': True,
              'existing_themes_unchanged': True, 'core_version_unchanged': True,
              'human_validation': 'PENDING', 'browser_qa': 'PENDING_DENIS',
              'canary': 'PENDING', 'physical_confirmation': 'PENDING',
              'no_physical_service_sent': True, 'no_restart_sent': True}
    store('readback.json', report)
    store('dashboard-readback.json', actual)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def rollback(apply=False):
    h = HA()
    before = load('before.json')
    now = snapshot(h)
    unchanged(before, now)
    registered = next((d for d in now['dashboards'] if d['url_path'] == SLUG), None)
    if registered:
        assert registered == load('created.json'), 'Registration changed; manual rollback required'
        assert digest(h.read_dashboard(SLUG)) == before['candidate_hash'], 'Candidate changed; manual rollback required'
    th = theme_hash()
    assert th in (None, before['candidate_theme_sha256']), 'Theme changed; manual rollback required'
    plan = {'dry_run': not apply, 'delete_dashboard_id': registered['id'] if registered else None,
            'remove_theme': THEME_PATH if th else None, 'legacy_resources_defaults_untouched': True}
    if apply:
        if registered:
            result(h, {'type': 'lovelace/dashboards/delete', 'dashboard_id': registered['id']})
            assert not any(d['url_path'] == SLUG for d in result(h, {'type': 'lovelace/dashboards/list'}))
        if th:
            ssh('import json; from pathlib import Path; Path(' + repr(THEME_PATH) + ').unlink(); print(json.dumps({"removed":True}))')
            assert theme_hash() is None
            h.service('frontend', 'reload_themes')
        after = snapshot(h)
        unchanged(before, after)
        assert after['themes'] == before['themes'] and after['dashboards'] == before['dashboards']
    store('rollback-check.json', plan)
    print(json.dumps(plan, indent=2))


if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'rollback':
        rollback('--apply' in sys.argv[2:])
    else:
        {'prepare': prepare, 'publish': publish, 'verify': verify}[command]()
