from playwright.sync_api import sync_playwright
from ha_client import HA, HA_URL
import json, sys

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

JS = r'''()=>{
  // trouver la carte Energie (texte 'Energie'/'Énergie' dans un h2 .head)
  let card=null;
  function walk(root){
    for(let e of root.querySelectorAll('*')){
      if(e.classList && e.classList.contains('panel')){
        let t=(e.textContent||'');
        if(/nergie/.test(t) && e.querySelector('.metrics')){ card=e; }
      }
      if(e.shadowRoot) walk(e.shadowRoot);
    }
  }
  walk(document);
  if(!card) return {err:'card energie introuvable'};
  const box=card.querySelector('.metrics');
  const cs=getComputedStyle(box);
  const rows=[...box.children].map(m=>{
    const kic=m.querySelector('ha-icon');
    const kt=m.querySelector('div');
    const r=(x)=>x?{x:Math.round(x.getBoundingClientRect().x),w:Math.round(x.getBoundingClientRect().width),y:Math.round(x.getBoundingClientRect().y)}:null;
    const cm=getComputedStyle(m);
    return {txt:(m.textContent||'').slice(0,22), display:cm.display, cols:cm.gridTemplateColumns,
            gap:cm.gap, justify:cm.justifyContent, metric:r(m), icon:r(kic), text:r(kt)};
  });
  const ci=k=>{const e=card.querySelector(k); if(!e) return null; const c=getComputedStyle(e); return {display:c.display,flexBasis:c.flexBasis,flexGrow:c.flexGrow,width:c.width,flexShrink:c.flexShrink};};
  // feuille de style du card root
  const root=card.getRootNode();
  const styles=[...root.querySelectorAll('style')].map(s=>s.textContent);
  // ancetre container-type
  const anc=[];
  let n=(root.host&&root.host.nodeType===1)?root.host:null;
  while(n){ const c=getComputedStyle(n); if(c.containerType!=='normal') anc.push({tag:n.tagName,id:n.id,w:n.clientWidth,ct:c.containerType});
            const p=n.parentElement||(n.parentNode&&n.parentNode.host&&n.parentNode.host.nodeType===1?n.parentNode.host:null); if(p===n)break; n=p; }
  const head=card.querySelector('.head');
  return {metrics:{display:cs.display,cols:cs.gridTemplateColumns,gap:cs.gap,w:box.clientWidth},
          rows:rows, metricCls:ci('.metric'), iconCls:ci('.metric>ha-icon'), textCls:ci('.metric>div'),
          headCls:ci('.head'), headBox:head?{w:head.clientWidth}:null,
          containers:anc, styles:styles};
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
    data = pg.evaluate(JS)
    print('VIEWPORT', VW)
    print(json.dumps(data, ensure_ascii=False, indent=1)[:6000])
    b.close()