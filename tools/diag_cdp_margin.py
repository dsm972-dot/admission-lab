from playwright.sync_api import sync_playwright
from ha_client import HA, HA_URL
import json, sys

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    c = b.new_context(viewport={'width': VW, 'height': 1200})
    t = {'hassUrl': HA_URL, 'access_token': h.token, 'token_type': 'Bearer',
         'expires_in': 315360000, 'expires': 4102444800000, 'refresh_token': ''}
    c.add_init_script('localStorage.setItem("hassTokens",' + json.dumps(json.dumps(t)) + ');')
    pg = c.new_page()
    cdp = c.new_cdp_session(pg)
    cdp.send('DOM.enable')
    cdp.send('CSS.enable')
    pg.goto(HA_URL + '/ai-nexus-v4/accueil', wait_until='networkidle')
    pg.wait_for_timeout(8000)

    # localiser le ha-icon de la carte Energie + son noeud CDP
    loc = pg.evaluate(r'''()=>{
      let panel=null;
      (function walk(r){ if(panel) return;
        for(const e of r.querySelectorAll('*')){ if(panel) return;
          if(e.classList && e.classList.contains('panel') && /nergie/i.test(e.textContent||'') && e.querySelector('.metrics')){ panel=e; return; } }
        for(const e of r.querySelectorAll('*')){ if(panel) return; if(e.shadowRoot) walk(e.shadowRoot); }
      })(document);
      if(!panel) return null;
      const icon=panel.querySelector('.metric ha-icon');
      if(!icon) return null;
      icon.setAttribute('data-diag-probe','1');
      return {metricCount:panel.querySelectorAll('.metric').length,
              inlineAttr:icon.getAttribute('style')||'',
              inlineProp:icon.style.cssText,
              outer:icon.outerHTML.slice(0,300)};
    }''')
    print("== locate ==")
    print(json.dumps(loc, ensure_ascii=False, indent=1))

    if loc:
        doc = cdp.send('DOM.getDocument', {'depth': -1, 'pierce': True})
        nid = cdp.send('DOM.querySelector', {'nodeId': doc['root']['nodeId'],
                                             'selector': '[data-diag-probe="1"]'})
        # querySelector ne pierce pas le shadow : on cherche via DOM.getFlattenedDocument
        found = None
        if not nid.get('nodeId'):
            for nd in cdp.send('DOM.getDocument', {'depth': -1, 'pierce': True}) and []:
                pass
        flat = cdp.send('DOM.getDocument', {'depth': -1, 'pierce': True})
        box = []
        def find(node):
            if box: return
            attrs = node.get('attributes', [])
            for i in range(0, len(attrs), 2):
                if attrs[i] == 'data-diag-probe' and attrs[i+1] == '1':
                    box.append(node['nodeId']); return
            for ch in node.get('children', []) or []:
                find(ch)
            for ch in node.get('shadowRoots', []) or []:
                find(ch)
            cd = node.get('contentDocument')
            if cd: find(cd)
        find(flat['root'])
        found = box[0] if box else None
        print("== nodeId ==", found)
        if found:
            ms = cdp.send('CSS.getMatchedStylesForNode', {'nodeId': found})
            rows = []
            for m in ms.get('matchedCSSRules', []):
                rule = m['rule']
                sel = rule.get('selectorList', {}).get('text', '')
                txt = rule.get('style', {}).get('cssText', '')
                if 'margin' in txt or 'auto' in txt:
                    rows.append({'origin': rule.get('origin'), 'sel': sel,
                                 'style': txt[:300], 'href': (rule.get('style', {}).get('stylesheet', {}) or {}).get('href', '')[:90]})
            print("== rules mentioning margin/auto ==")
            print(json.dumps(rows, ensure_ascii=False, indent=1)[:6000])
            inl = ms.get('inlineStyle', {})
            print("== inlineStyle ==", json.dumps(inl, ensure_ascii=False)[:800])
    b.close()