#!/usr/bin/env python3
"""Structure réelle de la carte « Énergie » : où est l'icône décalée ?

Repère la carte par son titre (et non par un simple .metrics) puis descend
jusqu'aux ha-icon en documentant pour chacun : la cascade qui s'applique et
les valeurs calculées. Sert à distinguer les icônes OK des icônes décalées.
"""
import json
import sys

from playwright.sync_api import sync_playwright

from ha_client import HA, HA_URL

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

PROBE = r'''() => {
  const res = [];
  (function walk(r) {
    for (const e of r.querySelectorAll('*')) {
      if (e.shadowRoot) walk(e.shadowRoot);
      if (!e.classList) continue;
      const titre = (e.querySelector('.head h2, .head h3, h2') || {}).textContent || '';
      if (!e.classList.contains('panel')) continue;
      if (!/Énergie/i.test(titre)) continue;
      const dump = (n, depth) => {
        if (depth > 6) return;
        for (const c of n.children) {
          const cs = getComputedStyle(c);
          if (c.tagName === 'HA-ICON' || c.tagName === 'MDI-ICON') {
            res.push({panel: titre.trim().slice(0, 30),
                      chemin: c.tagName.toLowerCase() + '.' + (c.className || '?'),
                      parent: c.parentElement.className,
                      ml: cs.marginLeft, mr: cs.marginRight, w: cs.width,
                      disp: cs.display,
                      matchOverride: c.matches('.panel .metric > ha-icon')});
            continue;
          }
          dump(c, depth + 1);
        }
      };
      dump(e, 0);
    }
  })(document);
  return res;
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
    b.close()