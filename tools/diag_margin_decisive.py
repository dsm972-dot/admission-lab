#!/usr/bin/env python3
"""Test décisif : pourquoi l'icône garde-t-elle une marge de 120px ?

Trois mesures sur le même nœud :
  1. l'override du dépôt matche-t-il vraiment l'icône ?
  2. quelle règle CSS gagne réellement (CDP, ordre de cascade) ?
  3. que donne un reset injecté en style inline (validation du correctif) ?
"""
import json
import sys

from playwright.sync_api import sync_playwright

from ha_client import HA, HA_URL

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

PROBE = r'''() => {
  let icon = null;
  (function walk(r) {
    for (const e of r.querySelectorAll('*')) {
      if (icon) return;
      if (e.shadowRoot) walk(e.shadowRoot);
      if (icon) return;
      if (e.classList && e.classList.contains('panel') && e.querySelector('.metrics')) {
        const c = e.querySelector('.metric');
        if (c) icon = c.querySelector('ha-icon');
      }
    }
  })(document);
  if (!icon) return null;
  const lire = () => {
    const cs = getComputedStyle(icon);
    return {ml: cs.marginLeft, mr: cs.marginRight,
            w: cs.width, disp: cs.display,
            parent: icon.parentElement.className,
            classeIcone: icon.className};
  };
  const avant = lire();
  const matchDepot = icon.matches('.panel .metric > ha-icon');
  const matchPanelIcon = icon.matches('.panel ha-icon');
  // reset inline, la preuve absolue que margin est la cause
  icon.style.setProperty('margin-left', '0', 'important');
  icon.style.setProperty('margin-right', '0', 'important');
  const apres = lire();
  icon.style.removeProperty('margin-left');
  icon.style.removeProperty('margin-right');
  window.__diagIcon = icon;
  return {avant, apres, matchDepot, matchPanelIcon,
          ancetreMetric: !!icon.closest('.metric'),
          closestPanel: !!(icon.closest('.panel'))};
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
    print(json.dumps(pg.evaluate(PROBE), ensure_ascii=False, indent=1))

    cdp = c.new_cdp_session(pg)
    for d in ('DOM.enable', 'CSS.enable', 'Runtime.enable'):
        cdp.send(d)
    res = cdp.send('Runtime.evaluate', {'expression': 'window.__diagIcon', 'objectGroup': 'd'})
    cdp.send('DOM.getDocument', {'depth': -1, 'pierce': True})
    nid = cdp.send('DOM.requestNode', {'objectId': res['result']['objectId']})['nodeId']
    m = cdp.send('CSS.getMatchedStylesForNode', {'nodeId': nid})
    lignes = []
    for r in m.get('matchedCSSRules', []):
        ru = r['rule']
        lignes.append((ru['selectorList']['text'], ru['origin'],
                       ru['style'].get('cssText', '')[:200]))
    print('\nCASCADE pour l icone (ordre source -> gainant) :')
    for sel, org, txt in lignes:
        print('  -', sel, '|', org, '|', txt)
    b.close()