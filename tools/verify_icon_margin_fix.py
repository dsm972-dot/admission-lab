from playwright.sync_api import sync_playwright
from ha_client import HA, HA_URL
import json, sys

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375
h = HA()

MEASURE = """() => {
  const out = [];
  const walk = (root) => {
    for (const el of root.querySelectorAll('*')) {
      const cs = getComputedStyle(el);
      if (cs.display !== 'flex') continue;
      for (const ch of el.children) {
        if (ch.tagName !== 'HA-ICON') continue;
        const s = getComputedStyle(ch);
        const p = getComputedStyle(el);
        const px = n => Math.round(parseFloat(n) || 0);
        const gap = px(p.columnGap === 'normal' ? 0 : p.columnGap);
        const wIcon = Math.round(ch.getBoundingClientRect().width);
        const free = Math.round(el.getBoundingClientRect().width - wIcon - gap);
        const ml = px(s.marginLeft), mr = px(s.marginRight);
        out.push({
          parent: el.className || el.tagName,
          grandParent: (el.parentElement && el.parentElement.className) || '',
          marginLeft: ml, marginRight: mr,
          freeSpace: free, suspect: (ml > 2 || mr > 2) ? 'DISPLACED' : 'ok',
        });
      }
    }
  };
  walk(document);
  return out;
}"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    ctx = b.new_context(viewport={'width': VW, 'height': 1200})
    tk = {'hassUrl': HA_URL, 'access_token': h.token, 'token_type': 'Bearer',
          'expires_in': 315360000, 'expires': 4102444800000, 'refresh_token': ''}
    ctx.add_init_script('localStorage.setItem("hassTokens",' + json.dumps(json.dumps(tk)) + ');')
    pg = ctx.new_page()
    pg.goto(HA_URL + '/lovelace/0', wait_until='networkidle')
    pg.wait_for_timeout(6000)
    pg.evaluate("""() => {
      const s = document.createElement('style');
      s.id = 'v4-fix-probe';
      s.textContent = '.panel ha-icon{margin:0}';
      document.head.appendChild(s);
    }""")
    pg.wait_for_timeout(900)
    rows = pg.evaluate(MEASURE)
    seen, uniq = set(), []
    for r in rows:
        k = (r['parent'], r['grandParent'])
        if k in seen: continue
        seen.add(k); uniq.append(r)
    print(json.dumps({'vw': VW, 'withFix': uniq}, ensure_ascii=False, indent=2))
    pg.screenshot(path=f'/tmp/fix_{VW}.png', full_page=True)
    ctx.close(); b.close()