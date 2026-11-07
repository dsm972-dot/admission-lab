#!/usr/bin/env python3
"""Publication ciblée Accueil + QA HA natif. Jamais d'appel à un actionneur."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
from ha_client import HA, HA_URL
from build_dashboard import Builder, validate, service_names
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('backup',type=Path)
parser.add_argument('--publish',action='store_true')
parser.add_argument('--verify-current',action='store_true',help='Contrôler la cible déjà publiée, sans écriture')
args=parser.parse_args()
assert not(args.publish and args.verify_current), 'Modes exclusifs'
OUT=args.backup/'native';OUT.mkdir(exist_ok=True)
h=HA()
backup=json.loads((args.backup/'dashboard-before.json').read_text())
legacy=json.loads((args.backup/'legacy-before.json').read_text())
default=json.loads((args.backup/'default-before.json').read_text())
current=h.read_dashboard('ai-nexus-v4',force=True)
if not args.verify_current:
 assert current==backup, 'V4 a changé depuis la sauvegarde : fusion/revue requise'
built=Builder().build()
source=next(v for v in built['views'] if v['path']=='accueil')
# Préserver exactement toutes les autres vues, options, boutons et réglages existants.
cfg=copy.deepcopy(backup)
idx=next(i for i,v in enumerate(cfg['views']) if v['path']=='accueil')
cfg['views'][idx]=source

def without_target_templates(config):
 cleaned=copy.deepcopy(config)
 def walk(node):
  if isinstance(node,dict):
   if node.get('name') in ('Famille regroupée','Sportage photographique'):
    node['custom_fields']['body']='TARGET_TEMPLATE'
   for value in node.values():walk(value)
  elif isinstance(node,list):
   for value in node:walk(value)
 walk(cleaned)
 return cleaned

only_target_templates_changed=without_target_templates(cfg)==without_target_templates(backup)
assert only_target_templates_changed, 'Modification hors des deux templates ciblés'
if args.verify_current:
 assert current==cfg, 'La cible publiée ne correspond pas exactement au candidat'
live={s['entity_id']:s for s in h.states()}
validate(cfg,live,h.resources(),service_names(h.services()))
(OUT/'candidate.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2))
if not(args.publish or args.verify_current):
 print(json.dumps({'candidate_valid':True,'views':len(cfg['views']),'changed_views':['accueil'],'only_target_templates_changed':only_target_templates_changed,'published':False}));raise SystemExit(0)
if args.publish:
 h.save_dashboard('ai-nexus-v4',cfg,force=True)
assert h.read_dashboard('ai-nexus-v4',force=True)==cfg
assert all(h.read_dashboard(slug,force=True)==value for slug,value in legacy.items())
assert h.read_dashboard(None,force=True)==default
assert h.dashboards()==json.loads((args.backup/'dashboards-before.json').read_text())
assert h.resources()==json.loads((args.backup/'resources-before.json').read_text())
(OUT/'dashboard-readback.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2))
measure=r'''() => {
 const nodes=[];function walk(root){for(const e of root.querySelectorAll('*')){nodes.push(e);if(e.shadowRoot)walk(e.shadowRoot)}}walk(document);
 const rect=e=>{let r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}};
 const panels=nodes.filter(e=>e.classList?.contains('panel')&&e.getBoundingClientRect().width>0);
 const family=panels.find(e=>e.querySelector('h2')?.textContent==='Famille');
 const sportage=panels.find(e=>e.querySelector('h2')?.textContent==='Sportage');
 const img=sportage?.querySelector('img');
 const over=panels.flatMap(p=>[p,...p.querySelectorAll('*')]).filter(e=>e.clientWidth>0&&e.scrollWidth>e.clientWidth+3&&e.tagName!=='STYLE').map(e=>({cls:e.className,text:e.textContent.slice(0,70),...rect(e)}));
 const imgs=nodes.filter(e=>e.tagName==='IMG'&&e.src.includes('/visual/'));
 const members=family?[...family.querySelectorAll('.person')]:[];
 const overlap=members.flatMap((a,i)=>members.slice(i+1).filter(b=>{let A=a.getBoundingClientRect(),B=b.getBoundingClientRect();return Math.min(A.right,B.right)-Math.max(A.left,B.left)>1&&Math.min(A.bottom,B.bottom)-Math.max(A.top,B.top)>1}).map(b=>[a.innerText,b.innerText]));
 return {panels:panels.map(e=>({cls:e.className,...rect(e)})),overflow:over,images:imgs.length,images_loaded:imgs.every(e=>e.complete&&e.naturalWidth>0),family:family?.innerText,members:members.map(e=>({text:e.innerText,...rect(e)})),member_overlap:overlap,sportage:{text:sportage?.innerText,image:img?{src:img.getAttribute('src'),naturalWidth:img.naturalWidth,naturalHeight:img.naturalHeight,fit:getComputedStyle(img).objectFit,...rect(img)}:null},errors:nodes.filter(e=>e.tagName==='HUI-ERROR-CARD').map(e=>e.textContent)};
}'''
get_panel=r'''title => {const nodes=[];function walk(root){for(const e of root.querySelectorAll('*')){nodes.push(e);if(e.shadowRoot)walk(e.shadowRoot)}}walk(document);return nodes.find(e=>e.classList?.contains('panel')&&e.querySelector('h2')?.textContent===title)}'''
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'],headless=True)
 context=browser.new_context(viewport={'width':1842,'height':1000})
 tokens={'hassUrl':HA_URL,'access_token':h.token,'token_type':'Bearer','expires_in':315360000,'expires':4102444800000,'refresh_token':''}
 context.add_init_script('localStorage.setItem("hassTokens",'+json.dumps(json.dumps(tokens))+');')
 page=context.new_page();errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(HA_URL+'/ai-nexus-v4/accueil',wait_until='networkidle',timeout=90000)
 page.wait_for_timeout(7000)
 samples=[]
 for width,height in [(1842,1000),(1280,900),(768,1000),(412,915),(375,812),(320,800)]:
  page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(1500)
  data=page.evaluate(measure)
  page.screenshot(path=str(OUT/f'ha-{width}.png'),full_page=True)
  for title in ['Famille','Sportage']:
   node=page.evaluate_handle(get_panel,title).as_element()
   assert node, f'Panneau {title} absent'
   node.screenshot(path=str(OUT/f'{title.lower()}-{width}.png'))
  samples.append({'width':width,'height':height,**data})
 # Test synthétique explicite : changements uniquement dans la copie hass du composant.
 # Aucun événement, service, état ou action n'est écrit dans HA.
 page.set_viewport_size({'width':1842,'height':1000});page.wait_for_timeout(1000)
 family=page.evaluate_handle(get_panel,'Famille').as_element()
 original=family.evaluate('e=>{let host=e.getRootNode().host;window.__familyTest={host,hass:host._hass||host.hass};return {host:host.tagName,hasHass:!!window.__familyTest.hass}}')
 assert original['hasHass'], 'Copie hass du button-card inaccessible'
 cases=[]
 for name,network,generation,wifi,expected in [
  ('mobile_5g','Cellular','NR','<not connected>','5G'),
  ('mobile_4g','Cellular','LTE','<not connected>','4G'),
  ('mobile_3g','Cellular','UMTS','<not connected>','3G'),
  ('mobile_2g','Cellular','EDGE','<not connected>','2G'),
  ('mobile_prioritaire_ssid_perime','Cellular','NR','Maison','5G'),
  ('wifi_ssid_sans_type','unknown','NR','Maison','Wi-Fi'),
  ('mobile_sans_generation','Cellular','unknown','<not connected>','Mobile'),
  ('connexion_inconnue','unknown','NR','<not connected>','Non renseignée'),
  ('wifi','Wi-Fi','NR','Maison','Wi-Fi')
 ]:
  case=page.evaluate(r'''async input=>{const {host,hass}=window.__familyTest;const next={...hass,states:{...hass.states}};const change=(id,state)=>{next.states[id]={...hass.states[id],entity_id:id,state,last_changed:new Date().toISOString()}};change('sensor.s25_denis_network_type',input.network);change('sensor.s25_denis_data_network_type_sim_1',input.generation);change('sensor.s25_denis_wi_fi_connection',input.wifi);change('sensor.s25_denis_battery_level','17');host.hass=next;await host.updateComplete;const person=host.shadowRoot.querySelector('.person');return {synthetic:true,server_write:false,text:person?.innerText,monitored:host._monitoredEntities}}''',{'network':network,'generation':generation,'wifi':wifi})
  case.update(name=name,expected=expected,passed=expected in (case['text'] or '') and '17 %' in (case['text'] or ''))
  cases.append(case)
 scenario={'synthetic':True,'server_write':False,'cases':cases,'passed':all(case['passed'] for case in cases)}
 page.evaluate('async ()=>{window.__familyTest.host.hass=window.__familyTest.hass;await window.__familyTest.host.updateComplete;delete window.__familyTest}')
 page.wait_for_timeout(1200)
 restored=page.evaluate(measure)['family']
 browser.close()
report={'checked_at':datetime.now(timezone.utc).isoformat(),'readback_exact':True,'legacy_unchanged':True,'default_unchanged':True,'only_accueil_changed':all(a==b for i,(a,b) in enumerate(zip(cfg['views'],backup['views'])) if i!=idx),'samples':samples,'page_errors':errors,'synthetic_component_reactivity':scenario,'family_after_restore':restored,'scope':'Aucune commande physique, aucun capteur activé, aucune modification du défaut.'}
report.update(published=True,publication_write=args.publish,reverified_only=args.verify_current,only_target_templates_changed=only_target_templates_changed,views=len(cfg['views']),dashboard_registry_unchanged=True,resources_unchanged=True,physical_action_executed=False,native_ha=True,human_visual_acceptance='PENDING')
report['passed']=not errors and report['only_accueil_changed'] and scenario['passed'] and all(s['family'] and s['images_loaded'] and not s['overflow'] and not s['errors'] and not s['member_overlap'] and s['sportage']['image'] and s['sportage']['image']['fit']=='contain' for s in samples)
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({**{k:v for k,v in report.items() if k!='samples'},'samples':[{'width':s['width'],'family':s['family'],'overflow':len(s['overflow']),'images_loaded':s['images_loaded'],'sportage_image':s['sportage']['image'],'errors':s['errors']} for s in samples]},ensure_ascii=False,indent=2))
assert report['passed'], 'Un contrôle natif a échoué : voir report.json'
