from playwright.sync_api import sync_playwright
from ha_client import HA, HA_URL
import json, sys

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

JS = r'''()=>{
  let panel=null, icon=null;
  (function walk(r){ if(panel) return;
    for(const e of r.querySelectorAll('*')){
      if(panel) return;
      if(e.classList && e.classList.contains('panel') && /nergie/i.test(e.textContent||'') && e.querySelector('.metrics')){ panel=e; return; }
    }
    for(const e of r.querySelectorAll('*')){ if(panel) return; if(e.shadowRoot) walk(e.shadowRoot); }
  })(document);
  if(!panel) return {err:'no panel'};
  icon=panel.querySelector('.metric>ha-icon');
  icon.scrollIntoView({block:'center'});
  // toutes les feuilles accessibles : document + shadow roots, y compris adoptedStyleSheets
  const sheets=[];
  const pushSheets=(list,owner)=>{ for(const s of list) sheets.push({s,owner}); };
  const collect=(root,owner)=>{
    pushSheets(root.styleSheets||[], owner+'::styleSheets');
    for(const e of root.querySelectorAll('*')){
      if(e.shadowRoot){
        try{ pushSheets(e.shadowRoot.adoptedStyleSheets||[], e.tagName.toLowerCase()+'#adopted'); }catch(_){}
        collect(e.shadowRoot, e.tagName.toLowerCase());
      }
    }
  };
  collect(document,'doc');
  const hits=[];
  let total=0;
  for(const {s,owner} of sheets){
    let rules; try{ rules=s.cssRules; }catch(_){ continue; }
    if(!rules) continue;
    for(const r of rules){
      if(!r.selectorText) continue;
      total++;
      let m=false;
      try{ m=icon.matches(r.selectorText); }catch(_){ m=false; }
      if(!m) continue;
      const css=r.style;
      const props=[];
      for(let i=0;i<css.length;i++){ const p=css[i];
        if(/margin|justify|place-self|align-self|order|flex/.test(p)) props.push(p+':'+css.getPropertyValue(p)+(css.getPropertyPriority(p)?' !imp':'')); }
      if(props.length) hits.push({owner, sel:r.selectorText, props, media:(r.parentRule&&r.parentRule.conditionText)||''});
    }
  }
  const c=getComputedStyle(icon);
  return {iconRect:(()=>{const r=icon.getBoundingClientRect();return{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width)};})(),
    computed:{ml:c.marginLeft,mr:c.marginRight,justifySelf:c.justifySelf,alignSelf:c.alignSelf,flex:c.flex},
    sheetsScanned:sheets.length, rulesScanned:total, marginRules: hits};
}'''

with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    c = b.new_context(viewport={'width': VW, 'height': 1200})
    t = {'hassUrl': HA_URL, 'access_token': h.token, 'token_type': 'Bearer',
         'expires_in': 315360000, 'expires': 4102444800000, 'refresh_token': ''}
    c.add_init_script('localStorage.setItem("hassTokens",' + json.dumps(json.dumps(t)) + ');')
    pg = c.new_page()
    pg.goto(HA_URL + '/ai-nexus-v4/accueil', wait_until='networkidle')
    pg.wait_for_timeout(8000)
    print(json.dumps(pg.evaluate(JS), ensure_ascii=False, indent=1)[:8000])
    b.close()