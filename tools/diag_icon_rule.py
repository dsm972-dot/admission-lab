#!/usr/bin/env python3
"""Identifie la règle CSS qui décale les ha-icon (marge horizontale).

Les adoptedStyleSheets (button-card, composants HA) n'apparaissent pas dans
element.styleSheets : il faut les parcourir explicitement, sinon la source du
décalage reste invisible.
"""
import json
import sys

from playwright.sync_api import sync_playwright

from ha_client import HA, HA_URL

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

JS = r'''(vw) => {
  const out = {target: null, rules: []};
  let host = null, icon = null;
  (function walk(r) {
    if (icon) return;
    for (const e of r.querySelectorAll('*')) {
      if (e.shadowRoot) walk(e.shadowRoot);
      if (icon) return;
      if (e.classList && e.classList.contains('panel') && e.querySelector('.metrics')) {
        const c = e.querySelector('.metric');
        if (c) { host = e; icon = c.querySelector('ha-icon'); }
      }
    }
  })(document);
  if (!icon) return {err: 'no icon'};
  const cs = getComputedStyle(icon);
  const hostCs = getComputedStyle(host);
  out.target = {hostClass: host.className, ml: cs.marginLeft, mr: cs.marginRight,
                hostDisplay: hostCs.display, hostJustify: hostCs.justifyContent,
                hostTextAlign: hostCs.textAlign, w: cs.width};
  const seen = new Set();
  const scanList = (list, where) => {
    for (const sh of list) {
      let rules; try { rules = sh.cssRules; } catch (e) { continue; }
      if (!rules) continue;
      walk(rules);
    }
    function walk(rs) {
      for (const r of rs) {
        if (r.cssRules) { walk(r.cssRules); continue; }
        if (!r.selectorText || !r.style) continue;
        const s = r.style;
        if (!s.margin && !s.marginLeft && !s.marginRight && !s['margin-inline']) continue;
        let m = false;
        try { if (icon.matches(r.selectorText)) m = true; } catch (e) {}
        if (!m) continue;
        const key = where + '|' + r.selectorText + '|' + s.cssText;
        if (seen.has(key)) continue; seen.add(key);
        out.rules.push({where, sel: r.selectorText, css: s.cssText.slice(0, 160)});
      }
    }
  };
  let node = icon;
  while (node) {
    const root = node.getRootNode && node.getRootNode();
    if (root && root.adoptedStyleSheets) scanList(root.adoptedStyleSheets, 'adopted:' + (root.host ? root.host.tagName : 'doc'));
    if (root && root.styleSheets) scanList(root.styleSheets, 'sheets:' + (root.host ? root.host.tagName : 'doc'));
    node = node.parentElement;
  }
  return out;
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
    print(json.dumps(pg.evaluate(JS, VW), ensure_ascii=False, indent=1)[:9000])
    b.close()
