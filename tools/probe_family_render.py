#!/usr/bin/env python3
"""Diagnostic DOM famille, aucune écriture serveur ni action physique."""
import json
from playwright.sync_api import sync_playwright
from ha_client import HA, HA_URL

h = HA()
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'], headless=True)
    context = browser.new_context(viewport={'width': 412, 'height': 915})
    tokens = {'hassUrl': HA_URL, 'access_token': h.token, 'token_type': 'Bearer', 'expires_in': 315360000, 'expires': 4102444800000, 'refresh_token': ''}
    context.add_init_script('localStorage.setItem("hassTokens",'+json.dumps(json.dumps(tokens))+');')
    page = context.new_page()
    page.goto(HA_URL+'/ai-nexus-v4/accueil', wait_until='networkidle', timeout=90000)
    page.wait_for_timeout(6000)
    print(json.dumps(page.evaluate(r'''() => {
      const nodes=[];function walk(root){for(const e of root.querySelectorAll('*')){nodes.push(e);if(e.shadowRoot)walk(e.shadowRoot)}}walk(document);
      const panel=nodes.find(e=>e.classList?.contains('panel')&&e.innerText?.startsWith('Famille'));
      const host=panel.getRootNode().host;
      const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}};
      const proto=[];for(let o=host;o&&proto.length<5;o=Object.getPrototypeOf(o))proto.push(Object.getOwnPropertyNames(o).filter(k=>/hass|update|trigg|should/i.test(k)));
      window.__familyHost=host; window.__familyHass=host._hass;
      return {host:host.tagName,proto,own_hass:!!host._hass,config:host._config?{entity:host._config.entity,triggers_update:host._config.triggers_update}:null,
      layout:[panel,...panel.querySelectorAll('.people,.person,.person>div,.presence,.conn,.pct')].map(e=>({tag:e.tagName,cls:e.className,text:e.innerText,...rect(e),scroll:e.scrollWidth,client:e.clientWidth,style:{overflow:getComputedStyle(e).overflow,columns:getComputedStyle(e).gridTemplateColumns}})),
      live:host._hass?Object.fromEntries(['sensor.s25_denis_network_type','sensor.s25_denis_data_network_type_sim_1','sensor.s25_denis_wi_fi_connection'].map(id=>[id,{state:host._hass.states[id]?.state,attributes:host._hass.states[id]?.attributes}])):{}};
    }'''),ensure_ascii=False,indent=2))
    print('METHODS',json.dumps(page.evaluate(r'''() => {
      const host=window.__familyHost, proto=Object.getPrototypeOf(host);
      const keys=['hass','_hass','shouldUpdate','_hasAnEntityChanged','_createStateProxy','_evalTemplate','_getTemplateOrValue','_finishSetup','_renderCustomFields'];
      return Object.fromEntries(keys.map(k=>{const d=Object.getOwnPropertyDescriptor(proto,k);return [k,d?{get:d.get?.toString().slice(0,3500),set:d.set?.toString().slice(0,3500),value:d.value?.toString().slice(0,3500)}:null]}));
    }'''),ensure_ascii=False))
    print('INJECT',json.dumps(page.evaluate(r'''async () => {
      const host=window.__familyHost, old=host._hass, states={...old.states};
      for(const [id,value] of Object.entries({'sensor.s25_denis_network_type':'cellular','sensor.s25_denis_data_network_type_sim_1':'NR','sensor.s25_denis_wi_fi_connection':'<not connected>'})){
        states[id]={...states[id],state:value,attributes:{...states[id]?.attributes},last_changed:new Date().toISOString(),last_updated:new Date().toISOString()};
      }
      host.hass={...old,states};host.requestUpdate();
      await host.updateComplete;
      const panel=host.shadowRoot.querySelector('.panel');
      return {after_network:host._hass.states['sensor.s25_denis_network_type'].state,changed:host._hass!==old,text:panel?.innerText,monitored:host._monitoredEntities,body_prefix:String(host._config.custom_fields.body).slice(0,35)};
    }''')))
    page.wait_for_timeout(300)
    print('AFTER',page.evaluate("window.__familyHost.shadowRoot.querySelector('.panel')?.innerText"))
    page.evaluate('window.__familyHost.hass=window.__familyHass; window.__familyHost.requestUpdate();')
    browser.close()
