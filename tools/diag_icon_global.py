#!/usr/bin/env python3
"""Balayage global : quelles icônes du dashboard ont encore une marge ?

Liste uniquement les icônes anormales (marge horizontale non nulle) avec le
titre de leur carte et la cascade qui s'applique. Un dashboard sain renvoie
une liste vide.
"""
import json
import sys

from playwright.sync_api import sync_playwright

from ha_client import HA, HA_URL

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

PROBE = r'''() => {
  const KO = [];
  let total = 0;
  (function walk(r) {
    for (const e of r.querySelectorAll('*')) {
      if (e.shadowRoot) walk(e.shadowRoot);
      if (e.tagName !== 'HA-ICON' && e.tagName !== 'MDI-ICON') continue;
      total++;
      const cs = getComputedStyle(e);
      const ml = parseFloat(cs.marginLeft) || 0;
      const mr = parseFloat(cs.marginRight) || 0;
      if (Math.abs(ml) < 1 && Math.abs(mr) < 1) continue;
      const panel = e.closest('.panel, .nexus07, .people') || null;
      let titre = '';
      if (panel) {
        const h2 = panel.querySelector('.head h2, .head h3, h2, h3');
        if (h2) titre = h2.textContent.trim();
      }
      KO.push({titre: titre.slice(0, 30),
               parent: e.parentElement.className,
               ml: cs.marginLeft, mr: cs.marginRight,
               w: cs.width, disp: cs.display,
               override: e.matches('.panel .metric > ha-icon, .panel .head > ha-icon')});
    }
  })(document);
  return {total, KO};
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
    print(json.dumps(pg.evaluate(PROBE), ensure_ascii=False, indent=1)[:6000])
    b.close()