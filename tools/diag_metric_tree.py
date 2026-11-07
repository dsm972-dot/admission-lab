from playwright.sync_api import sync_playwright
from ha_client import HA, HA_URL
import json, sys

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

JS = r'''()=>{
  let panel=null;
  (function walk(r){ if(panel) return;
    for(const e of r.querySelectorAll('*')){
      if(panel) return;
      if(e.classList && e.classList.contains('panel') && /nergie/i.test(e.textContent||'') && e.querySelector('.metrics')){ panel=e; return; }
    }
    for(const e of r.querySelectorAll('*')){ if(panel) return; if(e.shadowRoot) walk(e.shadowRoot); }
  })(document);
  if(!panel) return {err:'no panel'};
  const R=e=>{const r=e.getBoundingClientRect();return {x:+r.x.toFixed(1),y:+r.y.toFixed(1),w:+r.width.toFixed(1),h:+r.height.toFixed(1)};};
  const mets=[...panel.querySelectorAll('.metric')];
  const m=mets[1]||mets[0];
  const dump=(e,d)=>{
    const c=getComputedStyle(e);
    return {d,tag:e.tagName.toLowerCase(),cls:(typeof e.className==='string'?e.className:''),rect:R(e),
      disp:c.display, pos:c.position, ml:c.marginLeft, mr:c.marginRight, flex:c.flex,
      order:c.order, float:c.cssFloat, bg:c.backgroundColor,
      bef:getComputedStyle(e,'::before').content, aft:getComputedStyle(e,'::after').content,
      kids:[...e.children].map(k=>dump(k,d+1))};
  };
  // elementFromPoint au centre de l'icone et du texte
  const ic=m.querySelector('ha-icon'), tx=m.querySelector('div');
  const probe=(e,lbl)=>{ if(!e)return [lbl,null]; const r=e.getBoundingClientRect();
    const el=document.elementFromPoint(r.x+r.width/2, r.y+r.height/2);
    return [lbl, el? el.tagName.toLowerCase()+'.'+(typeof el.className==='string'?el.className:'')+' @'+Math.round(r.x+r.width/2)+','+Math.round(r.y+r.height/2):'null']; };
  const cs=getComputedStyle(m);
  return {
    metricCount:mets.length,
    metricTree: dump(m,0),
    widthProbe:{clientW:m.clientWidth, scrollW:m.scrollWidth, offsetW:m.offsetWidth,
      padL:cs.paddingLeft, padR:cs.paddingRight, border:cs.borderLeftWidth,
      cs_width:cs.width, cs_maxWidth:cs.maxWidth, cs_box:cs.boxSizing},
    elementsAt:[probe(ic,'icon'),probe(tx,'texte')],
    // largeur de la boite .metrics et de ses parents
    chain:(()=>{const o=[];let n=mets[0];while(n&&n!==document.body){const c=getComputedStyle(n);
      o.push({tag:n.tagName.toLowerCase(),cls:(typeof n.className==='string'?n.className:'').slice(0,50),
        w:n.clientWidth,sw:n.scrollWidth,disp:c.display,ct:c.containerType,transform:c.transform,zoom:c.zoom});n=n.parentElement;}return o;})(),
    styleSheets:(()=>{const out=[];const walkR=r=>{for(const s of r.querySelectorAll('style')){const t=s.textContent||'';if(/\.metric\b/.test(t))out.push({owner:(r.host&&r.host.tagName)||'doc',len:t.length});}for(const e of r.querySelectorAll('*'))if(e.shadowRoot)walkR(e.shadowRoot);};
      walkR(document);return out;})()
  };
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