#!/usr/bin/env python3
"""Liste les feuilles CSS du dashboard et localise la règle de marge icône.

Sert à vérifier si la version déployée dans HA contient bien l'override
`.panel .metric>ha-icon{margin-left:0}` — sinon le décalage persiste malgré
la correction présente dans le dépôt.
"""
import json
import sys

from playwright.sync_api import sync_playwright

from ha_client import HA, HA_URL

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

FIND = r'''() => {
  const sheets = [];
  const seen = new Set();
  const scan = (root) => {
    const where = root.host ? root.host.tagName.toLowerCase() : 'document';
    const add = (sh) => {
      let rules; try { rules = sh.cssRules; } catch (e) { return; }
      if (!rules) return;
      let txt = '';
      for (const r of rules) txt += r.cssText + '\n';
      if (seen.has(sh)) return;
      seen.add(sh);
      sheets.push({where, n: rules.length,
                   marginIconRules: [...rules]
                     .filter(r => r.selectorText && r.selectorText.includes('ha-icon')
                                  && /margin/.test(r.style.cssText))
                     .map(r => r.selectorText + '{' + r.style.cssText + '}'),
                   taille: txt.length});
    };
    if (root.adoptedStyleSheets) for (const sh of root.adoptedStyleSheets) add(sh, where + ':adopted');
    if (root.styleSheets) for (const sh of root.styleSheets) add(sh, where + ':sheets');
  };
  (function walk(r) {
    scan(r, r.host ? r.host.tagName.toLowerCase() : 'document');
    for (const e of r.querySelectorAll('*')) if (e.shadowRoot) walk(e.shadowRoot);
  })(document);
  return sheets.filter(s => s.marginIconRules.length);
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
    out = pg.evaluate(FIND)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:8000])
    b.close()