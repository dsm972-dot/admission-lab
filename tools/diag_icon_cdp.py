#!/usr/bin/env python3
"""Source exacte de la marge de l'icône via CDP CSS.getMatchedStylesForNode.

Les feuilles construites (button-card) ne sont pas listables de façon fiable
par adoptedStyleSheets ; la cascade CDP est la seule source de vérité.
"""
import json
import sys

from playwright.sync_api import sync_playwright

from ha_client import HA, HA_URL

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

FIND = r'''() => {
  let icon = null, panel = null;
  (function walk(r) {
    if (icon) return;
    for (const e of r.querySelectorAll('*')) {
      if (e.shadowRoot) walk(e.shadowRoot);
      if (icon) return;
      if (e.classList && e.classList.contains('panel') && e.querySelector('.metrics')) {
        const c = e.querySelector('.metric');
        if (c) { panel = e; icon = c.querySelector('ha-icon'); }
      }
    }
  })(document);
  if (!icon) return null;
  window.__diagIcon = icon;
  const cs = getComputedStyle(icon);
  return {icon, panel,
          ml: cs.marginLeft, mr: cs.marginRight,
          panelClass: panel.className, metricClass: icon.parentElement.className};
}'''


def pick(rules):
    out = []
    for r in rules or []:
        st = r.get('style')
        if not st:
            continue
        props = {p['name']: p.get('value') for p in st.get('cssProperties', [])
                 if p.get('name', '').startswith('margin')
                 or p.get('name') in ('justify-content', 'align-self',
                                      'justify-self', 'flex', 'width')}
        if props:
            out.append({'sel': r.get('selectorList', {}).get('text'),
                        'origin': r.get('origin'), 'props': props})
    return out


with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    c = b.new_context(viewport={'width': VW, 'height': 1200})
    t = {'hassUrl': HA_URL, 'access_token': h.token, 'token_type': 'Bearer',
         'expires_in': 315360000, 'expires': 4102444800000, 'refresh_token': ''}
    c.add_init_script('localStorage.setItem("hassTokens",' + json.dumps(json.dumps(t)) + ');')
    pg = c.new_page()
    pg.goto(HA_URL + '/ai-nexus-v4/accueil', wait_until='networkidle')
    pg.wait_for_timeout(8000)

    handle = pg.evaluate(FIND)
    if not handle:
        print('ICONE INTROUVABLE')
        b.close()
        sys.exit(1)
    info = {k: v for k, v in handle.items() if k not in ('icon', 'panel')}
    print('CIBLE:', json.dumps(info, ensure_ascii=False))

    cdp = c.new_cdp_session(pg)
    cdp.send('DOM.enable')
    cdp.send('CSS.enable')
    cdp.send('Runtime.enable')
    res = cdp.send('Runtime.evaluate', {
        'expression': 'window.__diagIcon', 'objectGroup': 'diag'})
    cdp.send('DOM.getDocument', {'depth': -1, 'pierce': True})
    node_id = cdp.send('DOM.requestNode', {'objectId': res['result']['objectId']})['nodeId']
    m = cdp.send('CSS.getMatchedStylesForNode', {'nodeId': node_id})
    raw = m.get('matchedCSSRules', [])
    print('clesRegle:', json.dumps([sorted(r.keys()) for r in raw[:2]], ensure_ascii=False))
    print(json.dumps(raw, ensure_ascii=False)[:6000])
    print(json.dumps({'inherited': pick(m.get('inherited', [])),
                      'matched': pick(m.get('matchedCSSRules', []))},
                     ensure_ascii=False, indent=1)[:8000])
    b.close()
