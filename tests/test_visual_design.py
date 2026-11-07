"""Contrat visuel, assets et templates JS de l'accueil."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_dashboard import Builder, walk, references


class VisualTests(unittest.TestCase):
    def setUp(self):
        self.builder = Builder()
        self.cfg = self.builder.build()
        self.home = self.cfg['views'][0]
        self.cards = list(walk(self.home))

    def named(self, name):
        return next(c for c in self.cards if c.get('name') == name)

    def render(self, card, states):
        template = card['custom_fields']['body']
        depth = len(template) - len(template.lstrip('['))
        assert depth >= 3 and template.endswith(']' * depth)
        body = template[depth:-depth]
        script = 'const states=JSON.parse(process.argv[1]);console.log((new Function("states",process.argv[2]))(states));'
        return subprocess.check_output(['node','-e',script,json.dumps(states),body], text=True)

    def test_layout(self):
        self.assertEqual(self.home['max_columns'], 4)
        self.assertEqual(self.home['sections'][0]['column_span'], 4)
        self.assertEqual(len(self.home['sections'][0]['cards']), 5)
        for name in ('Bandeau photographique','Famille regroupée','Climat compact avec jauge','Navimow i206 AWD visuel','Sportage photographique'):
            self.named(name)
        for name in ('Salon','Cuisine','Bureau','Parents','Émile','Maddy'):
            self.named(name+' photographique')

    def test_assets(self):
        manifest = json.loads((ROOT/'assets/visual/manifest.json').read_text())
        self.assertTrue(manifest['illustrative_only'])
        for asset in manifest['assets']:
            raw = (ROOT/'assets/visual'/asset['file']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), asset['sha256'])

    def test_templates_missing(self):
        for card in self.cards:
            if isinstance(card.get('custom_fields',{}).get('body'), str):
                html = self.render(card, {})
                self.assertNotIn('NaN', html)
                self.assertNotIn('undefined', html)
        html = self.render(self.named('Climat compact avec jauge'), {})
        self.assertIn('Indisponible', html)
        self.assertNotIn('<strong>0 °C</strong>', html)

    def test_exact_entities_and_safe_taps(self):
        self.assertFalse(None in references(self.cfg))
        for card in self.cards:
            if 'body' in card.get('custom_fields',{}):
                self.assertNotIn(None, card.get('triggers_update',[]))
                self.assertIn(card.get('tap_action',{}).get('action','none'), ('none','navigate'))
                self.assertEqual(card.get('hold_action',{}).get('action','none'), 'none')


if __name__ == '__main__':
    unittest.main()
