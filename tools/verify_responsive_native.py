#!/usr/bin/env python3
"""Publication candidate limitée et inspection native, aucune action physique."""
import json
from pathlib import Path
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
from ha_client import HA, HA_URL
from build_dashboard import Builder, validate, service_names
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/responsive-verified'
OUT.mkdir(parents=True,exist_ok=True)
h=HA()
old=h.read_dashboard('ai-nexus-v4',force=True)
backup=OUT/'dashboard-before.json'
assert not backup.exists(), 'Sauvegarde existante : ne pas écraser'
backup.write_text(json.dumps(old,ensure_ascii=False,indent=2))
legacy={d['url_path']:h.read_dashboard(d['url_path'],force=True) for d in h.dashboards() if d['url_path']!='ai-nexus-v4'}
(OUT/'legacy-before.json').write_text(json.dumps(legacy,ensure_ascii=False))
cfg=Builder().build()
validate(cfg,{s['entity_id']:s for s in h.states()},h.resources(),service_names(h.services()))
(OUT/'ROLLBACK.txt').write_text('Restaurer dashboard-before.json via HA.save_dashboard ai-nexus-v4 uniquement. Aucun changement de thème, ressources ou défaut.\n')
h.save_dashboard('ai-nexus-v4',cfg,force=True)
assert h.read_dashboard('ai-nexus-v4',force=True)==cfg
assert all(h.read_dashboard(slug,force=True)==value for slug,value in legacy.items())
(OUT/'dashboard-readback.json').write_text(json.dumps(cfg,ensure_ascii=False))
measure=r'''() => {
 const nodes=[];function walk(root){for(const e of root.querySelectorAll('*')){nodes.push(e);if(e.shadowRoot)walk(e.shadowRoot)}}walk(document);
 const rect=e=>{let r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}};
 const panels=nodes.filter(e=>e.classList?.contains('panel')&&e.getBoundingClientRect().width>0);
 const rooms=panels.filter(e=>e.classList.contains('room'));
 const over=panels.flatMap(p=>[p,...p.querySelectorAll('*')]).filter(e=>e.clientWidth>0&&e.scrollWidth>e.clientWidth+3&&e.tagName!=='STYLE').map(e=>({cls:e.className,text:e.textContent.slice(0,70),...rect(e)}));
 const imgs=nodes.filter(e=>e.tagName==='IMG'&&e.src.includes('/visual/'));
 return {panels:panels.map(e=>({cls:e.className,...rect(e)})),rooms:rooms.map(rect),overflow:over,images:imgs.length,images_loaded:imgs.every(e=>e.complete&&e.naturalWidth>0),body:document.body.innerText.slice(0,400),errors:nodes.filter(e=>e.tagName==='HUI-ERROR-CARD').map(e=>e.textContent)};
}'''
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'],headless=True)
 context=browser.new_context(viewport={'width':1842,'height':1000})
 # Existing API credential used in memory only, never saved in artifacts.
 tokens={'hassUrl':HA_URL,'access_token':h.token,'token_type':'Bearer','expires_in':315360000,'expires':4102444800000,'refresh_token':''}
 context.add_init_script('localStorage.setItem("hassTokens",'+json.dumps(json.dumps(tokens))+');')
 page=context.new_page();errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(HA_URL+'/ai-nexus-v4/accueil',wait_until='networkidle',timeout=90000)
 page.wait_for_timeout(8000)
 samples=[]
 for width,height in [(1842,1000),(1280,900),(768,1000),(412,915),(375,812),(320,800)]:
  page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(1800)
  data=page.evaluate(measure)
  page.screenshot(path=str(OUT/f'ha-{width}.png'),full_page=True)
  samples.append({'width':width,'height':height,**data})
 browser.close()
report={'checked_at':datetime.now(timezone.utc).isoformat(),'readback_exact':True,'legacy_unchanged':True,'samples':samples,'page_errors':errors}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({**{k:v for k,v in report.items() if k!='samples'},'samples':[{'width':s['width'],'panels':len(s['panels']),'rooms':len(s['rooms']),'overflow':len(s['overflow']),'images_loaded':s['images_loaded'],'errors':s['errors'],'body':s['body'] if not s['panels'] else ''} for s in samples]},ensure_ascii=False,indent=2))
