#!/usr/bin/env python3
"""Preuve native du correctif Energie (t_ded30fab).

Mesure la geometrie reelle de la carte Energie dans Chromium, en
parcourant les shadow roots (le contenu button-card vit en shadow DOM) :
  - marge calculee des icones .metric   (doit etre 0px)
  - ecart horizontal icone -> libelle    (colle au libelle)
  - position du titre de panneau          (a droite de l'icone)
  - valeurs et unites des metriques
Capture PNG en evidence.

Read-only : aucune ecriture HA.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from ha_client import HA, HA_URL  # noqa: E402

EVID = ROOT / "evidence" / "energy-fix-20261004"
EVID.mkdir(parents=True, exist_ok=True)

VW = int(sys.argv[1]) if len(sys.argv) > 1 else 375

JS = r'''()=>{
  let panel=null;
  (function walk(r){
    if(panel) return;
    for(const e of r.querySelectorAll('*')){
      if(panel) return;
      if(e.classList && e.classList.contains('panel')
         && /nergie/i.test(e.textContent||'') && e.querySelector('.metrics')){ panel=e; return; }
    }
    for(const e of r.querySelectorAll('*')){ if(panel) return; if(e.shadowRoot) walk(e.shadowRoot); }
  })(document);
  if(!panel) return {err:'no panel'};

  const R=el=>{const r=el.getBoundingClientRect();
    return{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),right:Math.round(r.right)};};

  const metrics=[...panel.querySelectorAll('.metric')].map(m=>{
    const ic=m.querySelector('ha-icon'); const tx=m.querySelector('div');
    const cs=ic?getComputedStyle(ic):null;
    return{
      label: tx?tx.textContent.trim().replace(/\s+/g,' '):null,
      marginLeft: cs?cs.marginLeft:null, marginRight: cs?cs.marginRight:null,
      icon: ic?R(ic):null, text: tx?R(tx):null,
      gap: (ic&&tx)? Math.round(tx.getBoundingClientRect().x - ic.getBoundingClientRect().right) : null,
    };
  });

  const head=panel.querySelector('.head');
  const hi=head&&head.querySelector('ha-icon'); const ht=head&&head.querySelector('h2');
  const hcs=hi?getComputedStyle(hi):null;
  return{
    panelRect:R(panel), metricsCount:metrics.length, metrics,
    head: head?{
      title: ht?ht.textContent.trim():null,
      iconMarginLeft: hcs?hcs.marginLeft:null,
      icon: hi?R(hi):null, title2: ht?R(ht):null,
      titleAfterIcon: (hi&&ht)? ht.getBoundingClientRect().x >= hi.getBoundingClientRect().right : null,
    }:null,
  };
}'''


def main():
    from playwright.sync_api import sync_playwright

    h = HA()
    result = {"viewport": VW}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        c = b.new_context(viewport={"width": VW, "height": 1200})
        tokens = {
            "hassUrl": HA_URL,
            "access_token": h.token,
            "token_type": "Bearer",
            "expires_in": 315360000,
            "expires": 4102444800000,
            "refresh_token": "",
        }
        c.add_init_script(
            "localStorage.setItem('hassTokens',"
            + json.dumps(json.dumps(tokens))
            + ");"
        )
        pg = c.new_page()
        pg.goto(HA_URL + "/ai-nexus-v4/accueil", wait_until="networkidle")
        pg.wait_for_timeout(8000)
        result["probe"] = pg.evaluate(JS)
        pg.screenshot(path=str(EVID / f"energy_{VW}_after.png"), full_page=True)
        b.close()

    (EVID / f"native_probe_{VW}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    probe = result["probe"]
    if probe.get("err"):
        print(f"[KO] {probe['err']}")
        return 1

    metrics = probe["metrics"]
    bad_margin = [m for m in metrics if m["marginLeft"] != "0px"]
    bad_gap = [m for m in metrics if (m["gap"] or 99) > 16]
    head = probe.get("head") or {}

    print(f"[ok] viewport {VW} - metriques : {probe['metricsCount']}")
    for m in metrics:
        print(
            f"  {str(m['label'])[:30]:<32} marge={m['marginLeft']:>5} "
            f"ecart={m['gap']}px"
        )
    print(f"[ok] titre : {head.get('title')!r}  apres icone = {head.get('titleAfterIcon')}")

    ok = (
        bool(metrics)
        and not bad_margin
        and not bad_gap
        and head.get("titleAfterIcon") is not False
    )
    print(f"\n[{'ok' if ok else 'KO'}] rendu natif conforme = {ok}")
    print(f"[ok] capture : {EVID / f'energy_{VW}_after.png'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())