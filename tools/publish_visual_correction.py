#!/usr/bin/env python3
"""Correction de la candidate existante seulement. Aucun service ni restart.
prepare/publish/verify ; rollback est informatif sauf --apply explicite.
"""
import base64
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from ha_client import HA, HA_URL
from build_dashboard import validate, references, service_names
from publish_candidate import artifact, digest, snapshot, remote_hashes, theme_hash, ssh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/visual-correction-publication'
REMOTE = '/config/www/ai-nexus-v4/visual'
SLUG = 'ai-nexus-v4'


def save(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2))


def load(name):
    return json.loads((OUT / name).read_text())


def assets():
    directory = ROOT / 'assets/visual'
    manifest = json.loads((directory / 'manifest.json').read_text())
    expected = {entry['file']: entry['sha256'] for entry in manifest['assets']}
    files = sorted(directory.glob('*.webp'))
    assert len(expected) >= 10 and {p.name for p in files} == set(expected), 'Assets incomplets'
    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == expected[p.name] for p in files), 'Hash asset incorrect'
    return {p.name: base64.b64encode(p.read_bytes()).decode() for p in files}


def remote_assets():
    return ssh('''import json,base64
from pathlib import Path
p=Path(''' + repr(REMOTE) + ''')
assert not p.is_symlink()
files={}
if p.exists():
 for f in sorted(p.rglob('*')):
  assert not f.is_symlink(), 'Symlink interdit dans le périmètre assets'
  if f.is_file(): files[str(f.relative_to(p))]=base64.b64encode(f.read_bytes()).decode()
print(json.dumps({'existed':p.exists(),'files':files}))
''')


def install(files, replace=False, existed=True):
    # Le remplacement exclusif n'est utilisé que par rollback --apply.
    code = '''import json,base64,shutil
from pathlib import Path
p=Path(''' + repr(REMOTE) + ''')
assert not p.is_symlink()
files=''' + repr(files) + '''
replace=''' + repr(replace) + '''
existed=''' + repr(existed) + '''
if replace and p.exists(): shutil.rmtree(p)
if existed or files: p.mkdir(parents=True,exist_ok=True)
for name,encoded in files.items():
 relative=Path(name)
 assert not relative.is_absolute() and '..' not in relative.parts
 dest=p/relative
 assert not dest.is_symlink()
 dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_bytes(base64.b64decode(encoded))
print(json.dumps({'written':len(files)}))
'''
    ssh(code)


def invariant(before, h):
    assert snapshot(h) == before['snapshot'], 'Un état hors candidate a changé'
    assert remote_hashes() == before['file_hashes'], 'Configuration ou préférences modifiées'
    assert theme_hash() == before['theme_hash'], 'Thème modifié'


def prepare():
    assert not (OUT / 'before.json').exists(), 'Snapshot existant : ne pas écraser'
    h = HA()
    cfg, registration = artifact()
    current = h.read_dashboard(SLUG, force=True)
    state = snapshot(h)
    actual_registration = next(d for d in state['dashboards'] if d['url_path'] == SLUG)
    assert all(actual_registration[k] == v for k, v in registration.items())
    assert len(current['views']) == len(cfg['views']) == 17
    validate(cfg, {s['entity_id']: s for s in h.states()}, state['resources'], service_names(h.services()))
    files = assets()
    assert len(files) >= 10
    before = {'checked_at': datetime.now(timezone.utc).isoformat(), 'snapshot': state,
              'dashboard': current, 'candidate_hash': digest(cfg), 'file_hashes': remote_hashes(),
              'theme_hash': theme_hash(), 'assets': remote_assets(), 'new_assets': files}
    save('before.json', before)
    save('dashboard-before.json', current)
    (OUT / 'ROLLBACK.txt').write_text('Rollback limité à la candidate et /config/www/ai-nexus-v4/visual.\n'
        'Simulation : python3 tools/publish_visual_correction.py rollback\n'
        'Application (gate humain) : python3 tools/publish_visual_correction.py rollback --apply\n'
        'Ne supprime pas la candidate ; restaure son état exact avant correction.\n')
    print(json.dumps({'prepared': True, 'snapshot': str(OUT), 'images': len(files), 'views': len(cfg['views'])}))


def verify():
    before = load('before.json')
    h = HA()
    cfg, _ = artifact()
    assert digest(cfg) == before['candidate_hash']
    invariant(before, h)
    actual = h.read_dashboard(SLUG, force=True)
    assert actual == cfg, 'Readback dashboard différent'
    expected = {**before['assets']['files'], **before['new_assets']}
    assert remote_assets() == {'existed': True, 'files': expected}
    http = []
    for name, value in before['new_assets'].items():
        url = HA_URL + '/local/ai-nexus-v4/visual/' + name
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read()
            assert response.status == 200 and content == base64.b64decode(value)
            http.append({'file': name, 'status': response.status, 'sha256': hashlib.sha256(content).hexdigest()})
    validate(actual, {s['entity_id']: s for s in h.states()}, before['snapshot']['resources'], service_names(h.services()))
    save('dashboard-readback.json', actual)
    qa = json.loads((ROOT / 'evidence/visual-correction-home-final/matrix.json').read_text())
    assert qa['sample_count'] == 6 and not qa['page_errors'] and not qa['mutation_requests']
    assert all(not row['overflow'] and row['images_loaded'] and not row['errors'] for row in qa['samples'])
    local_qa = {k: v for k, v in qa.items() if k != 'samples'}
    local_qa['samples'] = [{k: row[k] for k in ('width', 'height', 'overflow', 'images', 'images_loaded', 'errors')} for row in qa['samples']]
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'status': 'VISUAL_CORRECTION_PUBLISHED_READBACK_VERIFIED',
              'url': HA_URL + '/' + SLUG + '/accueil', 'views': len(actual['views']), 'entities': len(references(actual)),
              'dashboard_hash': digest(actual), 'images_http': http, 'legacy_unchanged': True,
              'defaults_unchanged': True, 'resources_unchanged': True, 'themes_unchanged': True,
              'no_service_sent': True, 'no_restart_sent': True, 'human_visual_acceptance': 'PENDING',
              'native_ha_browser': 'NOT_VERIFIED',
              'local_browser': local_qa}
    save('readback.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def publish():
    before = load('before.json')
    h = HA()
    cfg, _ = artifact()
    assert digest(cfg) == before['candidate_hash']
    assert assets() == before['new_assets']
    invariant(before, h)
    assert h.read_dashboard(SLUG, force=True) == before['dashboard']
    assert remote_assets() == before['assets']
    install(before['new_assets'])
    h.save_dashboard(SLUG, cfg)
    verify()


def rollback(apply=False):
    before = load('before.json')
    print(json.dumps({'apply': apply, 'only_dashboard': SLUG, 'only_assets': REMOTE}))
    if apply:
        h = HA()
        invariant(before, h)
        assert digest(h.read_dashboard(SLUG, force=True)) == before['candidate_hash']
        h.save_dashboard(SLUG, before['dashboard'])
        install(before['assets']['files'], replace=True, existed=before['assets']['existed'])
        assert h.read_dashboard(SLUG, force=True) == before['dashboard']
        assert remote_assets() == before['assets']
        invariant(before, h)
        print('ROLLBACK_EXACT_VERIFIED')


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else 'verify'
    if command == 'rollback':
        rollback('--apply' in sys.argv)
    else:
        {'prepare': prepare, 'publish': publish, 'verify': verify}[command]()
