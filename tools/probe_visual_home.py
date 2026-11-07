#!/usr/bin/env python3
"""QA Accueil uniquement : cartes HA réelles, coque locale approximative."""
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence/visual-correction-home-final'
OUT.mkdir(parents=True, exist_ok=True)
server = subprocess.Popen([sys.executable, 'tools/local_qa_server.py', '--port', '8779'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(80):
        try:
            urlopen('http://127.0.0.1:8779/qa/states', timeout=2).close()
            break
        except OSError:
            if server.poll() is not None:
                raise RuntimeError('Serveur QA arrêté')
            time.sleep(.25)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width':1920,'height':1080})
        errors, mutations = [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('request', lambda r: mutations.append(r.method) if r.method not in ('GET','HEAD') else None)
        page.goto('http://127.0.0.1:8779/local_qa/', wait_until='networkidle', timeout=90000)
        page.wait_for_function("window.qa?.renderer === 'real-cards-css-layout-approximation'", timeout=90000)
        page.wait_for_timeout(1500)
        # Éviter que la barre sticky du banc masque les captures de l'Accueil.
        page.add_style_tag(content='body > header { position: static !important; }')
        samples = []
        for width, height in [(1920,1080),(2560,1440),(412,915),(480,960),(600,960),(1280,800)]:
            page.set_viewport_size({'width':width,'height':height})
            page.wait_for_timeout(400)
            geometry = page.evaluate("""() => {
              function all(root) {
                let nodes=[];
                for (const n of root.querySelectorAll('*')) {nodes.push(n);if(n.shadowRoot) nodes.push(...all(n.shadowRoot));}
                return nodes;
              }
              const nodes=all(document.querySelector('#view-host'));
              const hero=nodes.find(n=>n.classList?.contains('hero'));
              const panel=hero?.getBoundingClientRect();
              const hero_boxes = hero ? [hero,...hero.querySelectorAll('*')].map(n=>({tag:n.tagName,cls:n.className,text:n.children.length?'':n.textContent.slice(0,80),box:{x:n.getBoundingClientRect().x,y:n.getBoundingClientRect().y,w:n.getBoundingClientRect().width,h:n.getBoundingClientRect().height},overflow:getComputedStyle(n).overflow})) : [];
              const hero_chain=[];let ancestor=hero;while(ancestor){const b=ancestor.getBoundingClientRect();hero_chain.push({tag:ancestor.tagName,id:ancestor.id,cls:ancestor.className,x:b.x,y:b.y,w:b.width,h:b.height,overflow:getComputedStyle(ancestor).overflow});ancestor=ancestor.parentElement || ancestor.getRootNode().host;}
              const imgs=nodes.filter(n=>n.tagName==='IMG' && n.src.includes('/visual/'));
              return {hero_chain,hero_boxes,overflow:document.documentElement.scrollWidth>innerWidth,hero_height:panel?.height,images:imgs.length,images_loaded:imgs.every(n=>n.complete&&n.naturalWidth>0),cards:nodes.filter(n=>n.tagName==='BUTTON-CARD').length,errors:[...qa.errors],limitations:[...new Set(qa.limitations)]};
            }""")
            filename = f'accueil-{width}.png'
            page.locator('#view-host').screenshot(path=str(OUT/filename))
            samples.append({'width':width,'height':height,'screenshot':filename,**geometry})
        page.set_viewport_size({'width':1920,'height':1080})
        page.locator('#theme-toggle').click()
        page.wait_for_timeout(500)
        page.locator('#view-host').screenshot(path=str(OUT/'accueil-dark-1920.png'))
        result = {'qualification':'LOCAL_REAL_CARDS_NOT_NATIVE_HA','samples':samples,'sample_count':len(samples),'page_errors':errors,'mutation_requests':mutations}
        (OUT/'matrix.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        print(json.dumps(result,ensure_ascii=False,indent=2))
        browser.close()
finally:
    server.terminate()
    try:
        server.wait(5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(5)
