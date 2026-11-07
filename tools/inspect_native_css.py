from playwright.sync_api import sync_playwright
from ha_client import HA, HA_URL
import json
h=HA()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':375,'height':900})
 t={'hassUrl':HA_URL,'access_token':h.token,'token_type':'Bearer','expires_in':315360000,'expires':4102444800000,'refresh_token':''}
 c.add_init_script('localStorage.setItem("hassTokens",'+json.dumps(json.dumps(t))+');')
 pg=c.new_page();pg.goto(HA_URL+'/ai-nexus-v4/accueil',wait_until='networkidle');pg.wait_for_timeout(7000)
 data=pg.evaluate('''()=>{let out=[];function walk(root){for(let e of root.querySelectorAll('*')){if(e.classList?.contains('panel')){let r=e.getRootNode();out.push({tag:r.host?.tagName,width:e.clientWidth,ancestors:[...r.querySelectorAll('*')].filter(x=>getComputedStyle(x).containerType!=='normal').map(x=>({id:x.id,tag:x.tagName,w:x.clientWidth,ct:getComputedStyle(x).containerType})),grids:[...r.querySelectorAll('*')].filter(x=>getComputedStyle(x).display==='grid').map(x=>({id:x.id,cls:x.className,cols:getComputedStyle(x).gridTemplateColumns})),styles:[...r.querySelectorAll('style')].map(x=>x.textContent.slice(0,2200))})}if(e.shadowRoot)walk(e.shadowRoot)}}walk(document);return out}''')
 print(json.dumps(data[:5],ensure_ascii=False,indent=2));b.close()
