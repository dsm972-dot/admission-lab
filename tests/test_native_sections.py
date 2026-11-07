"""Offline Chromium regression: HA section grid equations, isolated card shadows.

Source: home-assistant/frontend src/panels/lovelace/sections/hui-grid-section.ts
and views/hui-sections-view.ts (consulted 2026-10-04). Not a full HA runtime.
No local_qa CSS and no network access.
"""
import copy
import json
from pathlib import Path
import sys
import unittest
from playwright.sync_api import sync_playwright, Error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_dashboard import Builder

RENDER = r'''({cards, span, states}) => {
 const section = document.createElement('div'); section.id='section';
 // Native effective column_span is clamped by the section view.
 section.style.cssText=`display:grid;--grid-column-count:${12*span};grid-template-columns:repeat(var(--grid-column-count),minmax(0,1fr));gap:8px`;
 document.body.append(section);
 const apply=(el,rules)=>{for(const rule of rules||[])for(const [k,v] of Object.entries(rule))el.style.setProperty(k,v)};
 // Cartes natives HA (weather-forecast, entities...) : pas de button-card,
 // pas de styles.card. On garde un conteneur mesure au meme niveau qu'une carte.
 function renderNative(spec){
  const host=document.createElement('div');host.className='native-leaf';
  host.style.cssText='min-width:0;height:100%';
  return host;
 }
 function render(c){
  const styles=c.styles||{};
  const host=document.createElement('button-card');host.style.cssText='display:block;min-width:0';
  const root=host.attachShadow({mode:'open'});
  root.innerHTML='<style>:host{display:block}*{box-sizing:border-box}#card{width:100%}#container{display:grid}ha-icon{flex-shrink:0}</style>';
  const card=document.createElement('div');card.id='card'; apply(card,styles.card);
  if(c.section_mode)card.style.height='100%';
  const grid=document.createElement('div');grid.id='container';apply(grid,styles.grid);card.append(grid);root.append(card);
  const style=document.createElement('style');style.textContent=c.extra_styles||'';root.append(style);
  for(const [key,value] of Object.entries(c.custom_fields||{})){
   const field=document.createElement('div');field.style.gridArea=key;apply(field,styles.custom_fields?.[key]);
   if(value&&typeof value==='object'&&!Array.isArray(value)&&value.card)field.append(render(value.card));
   else if(value&&typeof value==='object'&&!Array.isArray(value)&&value.type&&value.type!=='custom:button-card')field.append(renderNative(value));
   else {
    // Ici la feuille est évaluée directement, sans le parent button-card.
    // En HA réel, chaque parent retire un seul niveau de crochets.
    const depth=value.length-value.replace(/^\[+/, '').length;
    field.innerHTML=depth>=3?new Function('states',value.slice(depth,-depth))(states):value;
   }
   grid.append(field);
  }
  return host;
 }
 for(const c of cards){
  const wrap=document.createElement('div');wrap.className='native-card';
  wrap.style.cssText='min-width:0;grid-row:span 1;grid-column:'+ (c.grid_options.columns==='full'?'1 / -1':`span min(${c.grid_options.columns},var(--grid-column-count))`);
  wrap.append(render(c));section.append(wrap);
 }
}'''
MEASURE = r'''() => {
 const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,b:r.bottom}};
 const rows=[...document.querySelectorAll('.native-card')].map(rect);
 const overflow=[];const overlaps=[];const rooms=[];
 function visit(root){
  for(const e of root.querySelectorAll('*')){
   if(e.shadowRoot)visit(e.shadowRoot);
   if(e.matches('.room'))rooms.push(rect(e));
   if(e.clientWidth && e.scrollWidth>e.clientWidth+2 && !e.matches('style'))overflow.push(e.className||e.id||e.tagName);
   if(e.matches('#container,.metrics,.people,.climate-list')){
    const children=[...e.children].filter(x=>x.tagName!=='STYLE').map(rect);
    for(let i=0;i<children.length;i++)for(let j=i+1;j<children.length;j++){
     const a=children[i],b=children[j];if(Math.min(a.x+a.w,b.x+b.w)>Math.max(a.x,b.x)+1 && Math.min(a.b,b.b)>Math.max(a.y,b.y)+1)overlaps.push(e.className||e.id);
    }
   }
  }
 }visit(document);
 return {rows,overflow,overlaps,rooms,width:document.querySelector('#section').clientWidth};
}'''

class NativeSectionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = Builder()
        cls.cards = cls.builder.build()['views'][0]['sections'][0]['cards']
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch(args=['--no-sandbox'])
        except Error as exc:
            if 'Operation not permitted' in str(exc):
                cls.pw.stop()
                raise unittest.SkipTest('Chromium interdit par le sandbox : Operation not permitted') from exc
            chrome = '/usr/bin/google-chrome-stable'
            try:
                cls.browser = cls.pw.chromium.launch(executable_path=chrome, args=['--no-sandbox','--disable-dev-shm-usage'])
            except Error:
                cls.pw.stop()
                raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def measure(self, width, cards=None, missing=False):
        page = self.browser.new_page(viewport={'width': width, 'height': 1000})
        page.route('**/*', lambda route: route.abort())
        page.set_content('<style>body{margin:0;padding:16px;font-family:Arial;--ha-card-background:#fff;--primary-text-color:#20384f;--secondary-text-color:#496176}</style>')
        span = min(4, max(1, (width-32+16)//336))
        page.evaluate(RENDER, {'cards': cards or self.cards, 'span': span, 'states': {} if missing else self.builder.states})
        result = page.evaluate(MEASURE)
        page.close()
        return result

    def test_native_width_rows_and_no_collisions(self):
        for width in (320, 375, 390, 600, 768, 1024, 1280, 1440, 1842):
            for missing in (False, True):
                with self.subTest(width=width, missing=missing):
                    result = self.measure(width, missing=missing)
                    self.assertEqual(result['overflow'], [])
                    self.assertEqual(result['overlaps'], [])
                    for row in result['rows']:
                        self.assertAlmostEqual(row['w'], result['width'], delta=1)
                    for previous, row in zip(result['rows'], result['rows'][1:]):
                        self.assertGreaterEqual(row['y'], previous['b']+7)
                    rooms=result['rooms']
                    self.assertEqual(len(rooms),6)
                    if width>=1440:
                        self.assertEqual(len({round(r['y']) for r in rooms}),1)
                        self.assertGreater(min(r['w'] for r in rooms),200)
                    if width<=600:
                        self.assertEqual(len({round(r['y']) for r in rooms}),6)

    def test_old_12_column_spans_reproduce_compression(self):
        old=copy.deepcopy(self.cards)
        for card in old:card['grid_options']['columns']=12
        result=self.measure(1842, old)
        self.assertLess(result['rows'][0]['w'], result['width']/3)
        self.assertEqual(result['rows'][0]['y'], result['rows'][1]['y'])

    def test_section_mode_and_intrinsic_rows(self):
        for card in self.cards:
            self.assertTrue(card['section_mode'])
            self.assertEqual(card['grid_options'],{'columns':'full','rows':'auto'})
            self.assertFalse(any('height' in style or 'width' in style for style in card['styles']['card']))


class NativeGridContractTests(unittest.TestCase):
    def test_effective_spans_at_each_native_section_width(self):
        section = Builder().build()['views'][0]['sections'][0]
        for available in (1, 2, 3, 4):
            columns = 12 * min(section['column_span'], available)
            cursor = 0
            placements = []
            for card in section['cards']:
                options = card['grid_options']
                span = columns if options['columns'] == 'full' else min(options['columns'], columns)
                placements.append((cursor // columns, cursor % columns, span))
                cursor += span
                self.assertTrue(card['section_mode'])
                self.assertEqual(options['rows'], 'auto')
                self.assertFalse(any('height' in rule or 'width' in rule for rule in card['styles']['card']))
            self.assertEqual(placements, [(row, 0, columns) for row in range(5)])

    def test_previous_spans_pack_four_rows_side_by_side(self):
        columns = 12 * 4
        self.assertEqual([(i*12//columns, i*12%columns) for i in range(5)],
                         [(0,0), (0,12), (0,24), (0,36), (1,0)])
