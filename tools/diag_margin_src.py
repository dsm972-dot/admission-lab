from playwright.sync_api import sync_playwright
from ha_client import HA, HA_URL
import json, sys

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

JS = r'''()=>{
  const out={matched:[],sheets:[]};
  let icon=null,panel=null;
  (function walk(r){
    if(icon) return;
    for(const e of r.querySelectorAll('*')){
      if(icon) return;
      if(e.classList && e.classList.contains('panel') && /nergie/i.test(e.textContent||'') && e.querySelector('.metrics')){ panel=e; icon=e.querySelector('.metric ha-icon')||e.querySelector('ha-icon'); }
      if(e.shadowRoot) walk(e.shadowRoot);
    }
  })(document);
  if(!icon && panel) icon=panel.querySelector('ha-icon');
  if(!icon) return {err:'no icon'};
  const ic=getComputedStyle(icon);
  out.computed={ml:ic.marginLeft,mr:ic.marginRight,w:ic.width,disp:ic.display};
  const seen=new Set();
  const scanSheets=(root,where)=>{
    for(const sh of root.styleSheets){
      let rules; try{rules=sh.cssRules}catch(e){continue}
      const walk=(rs)=>{
        for(const r of rs){
          if(r.styleSheet){walk(r.styleSheet.cssRules||[]);continue}
          if(r.cssRules){walk(r.cssRules);continue}
          if(!r.selectorText) continue;
          if(!r.style || !r.style.margin && !r.style.marginLeft && !r.style.marginRight) continue;
          let m=false;
          try{ if(icon.matches(r.selectorText)) m=true }catch(e){}
          if(!m) continue;
          const key=where+'|'+r.selectorText+'|'+r.style.cssText;
          if(seen.has(key)) continue; seen.add(key);
          out.matched.push({where,sel:r.selectorText,margin:r.style.margin,ml:r.style.marginLeft,mr:r.style.marginRight,all:r.style.cssText.slice(0,200)});
        }
      };
      walk(rules);
    }
  };
  scanSheets(document,'document');
  let node=icon;
  while(node){
    const sr=(node.nodeType===1)?(node.getRootNode()&&node.getRootNode().host?node.getRootNode():null):null;
    if(sr&&sr.styleSheets) scanSheets(sr,'shadow:'+(sr.host?sr.host.tagName:'?'));
    node=(node.nodeType===1)?(node.parentElement||null):null;
  }
  return out;
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
    print(json.dumps(pg.evaluate(JS), ensure_ascii=False, indent=1)[:9000])
    b.close()