"""Tests données synthétiques explicitement locales, sans accès HA."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from build_dashboard import Builder
from visual_design import HELPERS, FAMILY_HELPERS
from build_visual_assets import CROPS, build_sportage_full


def walk(value):
    if isinstance(value,dict):
        yield value
        for item in value.values():yield from walk(item)
    elif isinstance(value,list):
        for item in value:yield from walk(item)


class FamilyVehicleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards=list(walk(Builder().build()['views'][0]))
        cls.family=next(x for x in cls.cards if x.get('name')=='Famille regroupée')
        cls.car=next(x for x in cls.cards if x.get('name')=='Sportage photographique')

    def evaluate(self,states,expression):
        states={id:{'state':value,'attributes':{}} for id,value in states.items()}
        script='const states='+json.dumps(states)+';\n'+HELPERS+FAMILY_HELPERS+'\nconsole.log(JSON.stringify('+expression+'));'
        out=subprocess.run(['node','-e',script],text=True,capture_output=True,check=True)
        return json.loads(out.stdout)

    def test_network_generations(self):
        for generation,expected in [('GPRS','2G'),('EDGE','2G'),('UMTS','3G'),('HSPA','3G'),('HSPAP','3G'),('WCDMA','3G'),('LTE','4G'),('LTE_CA','4G'),('NR','5G'),('NR_NSA','5G'),('NR_SA','5G'),('unknown','Mobile')]:
            with self.subTest(generation=generation):
                result=self.evaluate({'w':'old-wifi','n':'cellular','m':generation},"connection('w','n','m')")
                self.assertIn('>'+expected+'</span>',result)
                self.assertNotIn('>Wi-Fi</span>',result)

    def test_wifi_fallback_and_missing(self):
        for wifi,network,expected in [('Dsm972','wifi','Wi-Fi'),('Freebox-1C0F52','unavailable','Wi-Fi'),('<not connected>','unavailable','Non renseignée'),('unknown','unknown','Non renseignée'),('','none','Sans connexion'),('old-wifi','none','Sans connexion')]:
            with self.subTest(wifi=wifi,network=network):
                self.assertIn('>'+expected+'</span>',self.evaluate({'w':wifi,'n':network},"connection('w','n',null)"))

    def test_escape_ssid(self):
        result=self.evaluate({'w':'\"><img src=x onerror=alert(1)>','n':'wifi'},"connection('w','n',null)")
        self.assertNotIn('<img',result)
        self.assertIn('&lt;img',result)
        self.assertIn('&quot;',result)

    def test_battery_edges(self):
        for value,expected in [('0','0 %'),('100','100 %'),('41','41 %'),('unknown','Indisponible'),('unavailable','Indisponible'),('','Indisponible'),('-1','Indisponible'),('101','Indisponible')]:
            with self.subTest(value=value):
                result=self.evaluate({'b':value},"batteryDetail('b')")
                self.assertIn('>'+expected+'</span>',result)
                self.assertIn('mdi:battery',result)

    def test_full_template_and_presence_independent(self):
        source=self.family['custom_fields']['body'][4:-4]
        states={'person.emile':{'state':'not_home','attributes':{}},'sensor.emile_wi_fi_connection':{'state':'Distant','attributes':{}},'sensor.emile_battery_level':{'state':'0','attributes':{}}}
        script='const states='+json.dumps(states)+';const fn=new Function("states",'+json.dumps(source)+');console.log(fn(states));'
        html=subprocess.run(['node','-e',script],text=True,capture_output=True,check=True).stdout
        self.assertIn('Absent',html)
        self.assertIn('Distant',html)
        self.assertIn('0 %',html)
        self.assertEqual(html.count('class="person"'),4)

    def test_nested_templates_are_evaluated_by_child(self):
        for card in (self.family, self.car):
            source=card['custom_fields']['body']
            self.assertTrue(source.startswith('[[[['),card['name'])
            self.assertTrue(source.endswith(']]]]'),card['name'])
            self.assertTrue(source[1:-1].startswith('[[['))

    def test_triggers_complete(self):
        mapping=json.loads((ROOT/'data/entities_map.json').read_text())
        for name in ('denis','laura','emile','maddy'):
            for suffix in ('','_bat','_wifi','_network','_mobile'):
                key=name+suffix
                if mapping.get(key):self.assertIn(mapping[key],self.family['triggers_update'])
        self.assertEqual(len(self.family['triggers_update']),16)

    def test_vehicle_contain_and_crop(self):
        html=self.car['custom_fields']['body']
        self.assertIn('sportage-full.webp',html)
        self.assertIn('object-fit:contain',html)
        self.assertNotIn('object-fit:cover" src=',html)
        self.assertEqual(CROPS['sportage-full'],(774,806,950,889))

    def test_asset_isolated(self):
        source=Path('/root/.hermes/webui/attachments/838f6e7e7697/tableau_de_bord_domotique_ai_nexus_avec_sportage-1.png')
        if not source.is_file():
            self.skipTest('référence photographique absente de cette copie')
        with tempfile.TemporaryDirectory(dir=ROOT/'evidence') as tmp:
            dest=Path(tmp);(dest/'sportage.webp').write_bytes(b'rollback')
            entry=build_sportage_full(source,dest)
            self.assertEqual((dest/'sportage.webp').read_bytes(),b'rollback')
            self.assertEqual(entry['size'],[176,83])
            self.assertEqual(json.loads((dest/'manifest.json').read_text())['assets'][0]['file'],'sportage-full.webp')

if __name__=='__main__':unittest.main()
