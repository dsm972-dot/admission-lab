#!/usr/bin/env python3
"""Collecte lecture seule et sauvegarde ciblée avant correction Famille/Sportage."""
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from ha_client import HA

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence' / ('family-sportage-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
OUT.mkdir(parents=True, exist_ok=False)
h = HA()
old = h.read_dashboard('ai-nexus-v4', force=True)
(OUT / 'dashboard-before.json').write_text(json.dumps(old, ensure_ascii=False, indent=2))
legacy = {d['url_path']: h.read_dashboard(d['url_path'], force=True) for d in h.dashboards() if d['url_path'] != 'ai-nexus-v4'}
(OUT / 'legacy-before.json').write_text(json.dumps(legacy, ensure_ascii=False, indent=2))
(OUT / 'default-before.json').write_text(json.dumps(h.read_dashboard(None, force=True), ensure_ascii=False, indent=2))
(OUT / 'dashboards-before.json').write_text(json.dumps(h.dashboards(), ensure_ascii=False, indent=2))
for file in ['tools/visual_design.py','tools/build_visual_assets.py','tools/build_entity_map.py','data/entities_map.json','assets/visual/sportage.webp','assets/visual/manifest.json']:
    target = OUT / 'source-before' / file
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / file, target)
rows = h.states()
network_ids = ['sensor.s25_denis_wi_fi_connection','sensor.s25_denis_network_type','sensor.s25_denis_data_network_type_sim_1','sensor.laura_wifi_connection','sensor.laura_network_type','sensor.laura_data_network_type_sim_1','sensor.emile_wi_fi_connection','sensor.tel_maddy_wi_fi_connection']
person_ids = ['person.denis','person.laura','person.emile','person.maddy','sensor.s25_denis_battery_level','sensor.laura_battery_level','sensor.emile_battery_level','sensor.tel_maddy_battery_level']
selected = [{k:r[k] for k in ('entity_id','state','last_updated')} for r in rows if r['entity_id'] in network_ids + person_ids]
(OUT/'family-live-inputs.json').write_text(json.dumps(selected, ensure_ascii=False, indent=2))
registry = h.ws_one({'type':'config/entity_registry/list'})
related = [{k:r.get(k) for k in ('entity_id','platform','disabled_by','original_name')} for r in registry.get('result', []) if any(p in r.get('entity_id','') for p in ('emile','maddy')) and any(s in r.get('entity_id','') for s in ('network','wifi','wi_fi','sim_'))]
(OUT/'optional-network-registry.json').write_text(json.dumps(related, ensure_ascii=False, indent=2))
(OUT/'ROLLBACK.md').write_text('# Retour arrière\n\nRestaurer uniquement dashboard-before.json par HA.save_dashboard("ai-nexus-v4", config, force=True), puis relecture exacte. Les autres dashboards, le défaut et les commandes physiques sont hors périmètre.\nRestaurer les fichiers ciblés depuis source-before si nécessaire ; aucun fichier voisin ne doit être revert. Le nouveau visuel Sportage aura un nom distinct et pourra rester inerte sans modifier les anciens assets.\n')
(ROOT/'data/family-vehicle-evidence-path.txt').write_text(str(OUT))
print(json.dumps({'evidence':str(OUT),'backup_views':len(old.get('views',[])),'legacy_dashboards':list(legacy),'network_sources':selected,'optional_registry':related}, ensure_ascii=False, indent=2))
