from playwright.sync_api import sync_playwright
from ha_client import HA, HA_URL
import json, sys

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

JS = r'''()=>{
  let card=null;
  function walk(root){
    for(let e of root.querySelectorAll('*')){
      if(e.classList && e.classList.contains('panel')){
        if(/nergie/.test(e.textContent||'') && e.querySelector('.metrics')) card=e;
      }
      if(e.shadowRoot) walk(e.shadowRoot);
    }
  }
  walk(document);
  if(!card) return {err:'card introuvable'};
  const box=card.querySelector('.metrics');
  const m0=box.children[0];
  const kids=[...m0.children].map(k=>{
    const c=getComputedStyle(k);
    const r=k.getBoundingClientRect();
    return {tag:k.tagName, cls:k.className&&k.className.toString(), txt:(k.textContent||'').slice(0,18),
            x:Math.round(r.x), w:Math.round(r.width),
            display:c.display, margin:c.margin, flex:c.flex, minW:c.minWidth, order:c.order, position:c.position};
  });
  const mc=getComputedStyle(m0);
  // toutes les regles CSS qui ciblent ha-icon dans cette shadow root
  const root=card.getRootNode();
  const hits=[];
  for(const ss of root.querySelectorAll('style')){
    for(const sheet of ss.sheet? [ss.sheet]:[]){
      let rules; try{rules=ss.sheet.cssRules}catch(e){continue}
      if(!rules) continue;
      const walkRules=(rl,ctx)=>{for(const r of rl){
        if(r.cssRules){walkRules(r.cssRules,(ctx||'')+'@'+r.conditionText+' ');continue}
        if(r.selectorText&&/ha-icon|\.metric|metrics/.test(r.selectorText))
          hits.push({sel:r.selectorText, ctx:ctx, css:r.style.cssText.slice(0,180)});
      }};
      walkRules(rules,'');
    }
  }
  return {metricHTML:m0.innerHTML.slice(0,900), nkids:m0.children.length, kids:kids,
          metricBox:{x:Math.round(m0.getBoundingClientRect().x), w:Math.round(m0.getBoundingClientRect().width)},
          metricStyle:{display:mc.display,gap:mc.gap,justify:mc.justifyContent,padding:mc.padding,align:mc.alignItems},
          cssHits:hits};
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
    print('VIEWPORT', VW)
    print(json.dumps(pg.evaluate(JS), ensure_ascii=False, indent=1)[:8000])
    b.close()