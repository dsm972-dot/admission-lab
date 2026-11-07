"""Tests hors ligne : aucune connexion Home Assistant, JavaScript exécuté par Node."""
import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_dashboard as build


def unwrap(template):
    """Retire les enveloppes equilibrees successives autour du code JS.

    button-card accepte qu'un template soit lui-meme une liste : une carte
    enfant peut etre ['[[[ ... ]]]']. Le stripping fixe [3:-3] cassait alors.
    """
    assert template.startswith('[[[') and template.endswith(']]]'), template[:40]
    lead = len(template) - len(template.lstrip('['))
    trail = len(template) - len(template.rstrip(']'))
    template = template[lead - 3:len(template) - (trail - 3)]
    assert template.startswith('[[[') and template.endswith(']]]'), template[:40]
    return template[3:-3]


def evaluate(template, **context):
    program='const c='+json.dumps(context)+'; const f=new Function("entity","states","variables","hass",'+json.dumps(unwrap(template))+'); process.stdout.write(JSON.stringify(f(c.entity,c.states||{},c.variables||{},c.hass||{})));'
    return json.loads(subprocess.check_output(['node','-e',program],text=True))


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=build.Builder()
        cls.dashboard=cls.b.build()
        cls.resources=build.load('resources')

    def test_validation(self):
        build.validate(self.dashboard,self.b.states,self.resources,build.service_names(build.load('services')))

    def test_all_views_sections(self):
        self.assertEqual([v['path'] for v in self.dashboard['views']],[v[0] for v in build.VIEWS])
        self.assertTrue(all(v['type']=='sections' for v in self.dashboard['views']))

    def test_all_entities_exist(self):
        self.assertFalse(build.references(self.dashboard)-self.b.states.keys())

    def test_title_views_only_export_rejected(self):
        truncated = {key: self.dashboard[key] for key in ('title', 'views')}
        with self.assertRaisesRegex(ValueError, 'Template button-card absent'):
            build.validate(truncated, self.b.states, self.resources)

    def test_unknown_entity_rejected(self):
        d=copy.deepcopy(self.dashboard); d['views'][0]['sections'][0]['cards'].append({'entity':'sensor.invented'})
        with self.assertRaisesRegex(ValueError,'Entités absentes'):build.validate(d,self.b.states,self.resources)

    def test_six_popups_same_view(self):
        for view in self.dashboard['views'][:2]:
            nodes=list(build.walk(view))
            hashes={n['hash'] for n in nodes if 'hash' in n}
            self.assertEqual(hashes,{'#piece-'+r[0] for r in build.ROOMS})
            self.assertEqual({n['navigation_path'] for n in nodes if n.get('navigation_path','').startswith('#')},hashes)

    def test_bad_hash_rejected(self):
        d=copy.deepcopy(self.dashboard); d['views'][0]['sections'][0]['cards'].append({'tap_action':{'navigation_path':'#absent'}})
        with self.assertRaisesRegex(ValueError,'Hash absent'):build.validate(d,self.b.states,self.resources)

    def test_bad_route_rejected(self):
        d=copy.deepcopy(self.dashboard); d['views'][0]['sections'][0]['cards'].append({'url':'/ai-nexus-v4/absent'})
        with self.assertRaisesRegex(ValueError,'Vue absente'):build.validate(d,self.b.states,self.resources)

    def test_missing_resource_rejected(self):
        with self.assertRaisesRegex(ValueError,'Ressource inconnue'):build.validate(self.dashboard,self.b.states,[])

    def test_sensitive_commands_confirmed(self):
        commands=[n['tap_action'] for n in build.walk(self.dashboard) if n.get('tap_action',{}).get('action') in ('call-service','toggle')]
        self.assertGreater(len(commands),10)
        confirmed=[n['tap_action'] for n in build.walk(self.dashboard) if (n.get('tap_action') or {}).get('confirmation',{}).get('text')]
        self.assertGreater(len(confirmed),10)
        for node in build.walk(self.dashboard):
            entity=node.get('entity') or ''
            if not isinstance(entity,str) or not entity.startswith(('cover.','lock.','alarm_control_panel.')):
                continue
            tap=(node.get('tap_action') or {}).get('action')
            self.assertNotEqual(tap,'more-info',entity)
            if entity.startswith('alarm_control_panel.'):
                self.assertIn(tap,['none','navigate'])
            elif tap in ('toggle','call-service'):
                self.assertTrue((node['tap_action'].get('confirmation') or {}).get('text'), entity)

    def test_unsafe_action_rejected(self):
        for key in ('tap_action','hold_action','double_tap_action'):
            d=copy.deepcopy(self.dashboard);d['views'][0]['sections'][0]['cards'].append({key:{'action':'call-service','service':'lock.unlock'}})
            with self.assertRaisesRegex(ValueError,'confirmation'):build.validate(d,self.b.states,self.resources)

    def test_unlisted_service_rejected(self):
        with self.assertRaisesRegex(ValueError,'Service absent'):build.validate(self.dashboard,self.b.states,self.resources,set())

    def test_feature_guard(self):
        b=build.Builder();b.states[b.mapping['garage_cover']]['attributes']['supported_features']=0
        self.assertNotIn('hold_action',b.command('garage_cover','Ouvrir','cover.open_cover',1))

    def test_no_kitchen_or_office_fake_temperature(self):
        for key in ('cuisine','bureau'):
            c=self.b.room(key,key,'home')
            self.assertEqual(c['triggers_update'],[])
            self.assertEqual(evaluate(c['label']),'Éclairage et équipements')
        self.assertNotIn('cuisine_temp',self.b.mapping)
        self.assertNotIn('cuisine_hum',self.b.mapping)

    def test_state_matrix(self):
        matrix={'on':'Allumé','off':'Éteint','unknown':'Donnée non disponible','unavailable':'Donnée non disponible','open':'Ouvert','closed':'Fermé','locked':'Verrouillée','unlocked':'Déverrouillée','armed_away':'Armée — absence','disarmed':'Désarmée','home':'À la maison','not_home':'Absent','playing':'Lecture','paused':'En pause','cleaning':'Nettoyage','docked':'À la station','mowing':'Tonte','error':'À vérifier'}
        for state,expected in matrix.items():
            with self.subTest(state=state):self.assertEqual(evaluate(build.STATE_JS,entity={'state':state,'attributes':{}}),expected)
        self.assertEqual(evaluate(build.STATE_JS,variables={'sleep':True},entity={'state':'unavailable'}),'En veille')
        kitchen=self.b.card('light.ampoule_cuisine','Cuisine')
        self.assertTrue(kitchen['variables']['sleep'])
        self.assertEqual(evaluate(kitchen['state_display'],variables=kitchen['variables'],entity={'state':'unavailable'}),'En veille')
        self.assertEqual(evaluate(build.STATE_JS),'Donnée non disponible')

    def test_binary_sensor_meanings(self):
        for device,on,off in [('door','Ouverte','Fermée'),('plug','Branché','Débranché'),('battery_charging','En charge','Pas de charge')]:
            for state,expected in [('on',on),('off',off)]:
                self.assertEqual(evaluate(build.STATE_JS,entity={'entity_id':'binary_sensor.example','state':state,'attributes':{'device_class':device}}),expected)

    def test_invalid_command_capability_rejected(self):
        states=copy.deepcopy(self.b.states)
        states[self.b.mapping['garage_cover']]['attributes']['supported_features']=0
        with self.assertRaisesRegex(ValueError,'Capacité de commande absente'):
            build.validate(self.dashboard,states,self.resources)

    def test_wrong_service_domain_rejected(self):
        d=copy.deepcopy(self.dashboard)
        command=next(n['tap_action'] for n in build.walk(d) if n.get('tap_action',{}).get('service')=='lock.unlock')
        command['service']='cover.open_cover'
        with self.assertRaisesRegex(ValueError,'Domaine de service incompatible'):
            build.validate(d,self.b.states,self.resources)

    def test_numbers_real_and_invalid(self):
        self.assertEqual(evaluate(build.STATE_JS,entity={'state':'21.7','attributes':{'unit_of_measurement':'°C'}}),'21,7 °C')
        for state in ('NaN','unknown','unavailable','Infinity'):
            self.assertEqual(evaluate(build.STATE_JS,entity={'state':state,'attributes':{'unit_of_measurement':'°C'}}),'Donnée non disponible')

    def test_average_excludes_missing_and_zero_is_valid(self):
        card=next(n for n in build.walk(self.dashboard) if n.get('name')=='Température maison')
        ids=card['triggers_update']
        states={key:{'state':state} for key,state in zip(ids,['20','22','unavailable','unknown','0','NaN'])}
        self.assertEqual(evaluate(card['label'],states=states),'14 °C · 3 pièces mesurées')
        self.assertEqual(evaluate(card['label']),'Donnée non disponible')

    def test_alert_changes_with_presence(self):
        c=next(n for n in build.walk(self.dashboard) if n.get('name')=='Vigilance maison')
        states={self.b.mapping[k]:{'state':v} for k,v in [('denis','home'),('mode_maison','Absent'),('alarme','armed_away')]}
        self.assertIn('Présence détectée',evaluate(c['label'],states=states))
        states[self.b.mapping['denis']]['state']='not_home'
        self.assertIn('Présence partiellement non disponible',evaluate(c['label'],states=states))
        for key in ('laura','emile','maddy'):
            states[self.b.mapping[key]]={'state':'not_home'}
        self.assertIn('Aucune incohérence',evaluate(c['label'],states=states))
        states[self.b.mapping['alarme']]['state']='triggered'
        self.assertEqual(evaluate(c['label'],states=states),'Alarme déclenchée')
        # Libelle mission 02/07 : distingue alarme et mode absents de la maison,
        # au lieu du libelle unique "Donnee non disponible".
        self.assertEqual(evaluate(c['label']),'Sécurité / mode non disponibles')

    def test_all_js_compiles_and_missing_states_render(self):
        for node in build.walk(self.dashboard):
            for key in ('name','label','state_display'):
                value=node.get(key)
                if isinstance(value,str) and value.startswith('[[['):
                    # custom:button-card fournit entity/states aux templates [[[ ]]] :
                    # on reproduit ce contexte avec l'état réel de l'entité déclarée.
                    # On ne charge que les entités littéralement référencées par le
                    # programme (argv node limité à 128 Ko — E2BIG sinon).
                    prog=unwrap(value)
                    ids=set(re.findall(r"[\"']([a-z_]+\.[a-z0-9_]+)[\"']",prog))
                    mini={i:{'state':self.b.states[i].get('state','unknown'),
                            'attributes':{k:v for k,v in (self.b.states[i].get('attributes') or {}).items()
                                          if k in ('unit_of_measurement','friendly_name')}}
                          for i in ids if i in self.b.states}
                    ent=node.get('entity')
                    ed=self.b.states.get(ent) if ent else None
                    result=evaluate(value,
                        hass={'user':{'name':'Test'},'config':{'time_zone':'Europe/Paris'}},
                        entity={'state':ed.get('state','0'),
                                'attributes':{k:v for k,v in (ed.get('attributes') or {}).items()
                                              if k in ('unit_of_measurement','friendly_name')}} if ed else {'state':'0'},
                        states=mini)
                    self.assertIsInstance(result,str)
                    self.assertNotIn('NaN',result)

    def test_legacy_cards_exact(self):
        for typ in ('custom:navimower-map-card','custom:yet-another-media-player'):
            actual=next(n for n in build.walk(self.dashboard) if n.get('type')==typ)
            self.assertTrue(any(actual==n for source in self.b.legacy for n in build.walk(source)))
        self.assertFalse(any(n.get('type')=='custom:xiaomi-vacuum-map-card' for n in build.walk(self.dashboard)))

    def test_no_home_camera_or_heavy_graph(self):
        types=[n.get('type','') for n in build.walk(self.dashboard['views'][0])]
        self.assertFalse(any('camera' in t or t=='picture-entity' for t in types))
        self.assertLessEqual(sum('graph' in t for t in types),1)

    def test_theme_modes(self):
        self.assertEqual(set(build.theme()['AI Nexus Glass']['modes']),{'light','dark'})

    def test_command_tiles_call_real_services(self):
        dead={'light.chambre_emile','light.chambre_maddy','light.cuisine','light.lumiere_du_salon','light.lumiere_bureau','light.lumiere_bureau_ambilight','media_player.sound_bar_5','media_player.meghann','cover.curtain_switch_rideau','cover.volet_de_la_chambre_de_emile_rideau','cover.volet_de_la_cuisine_rideau'}
        wired=set()
        for node in build.walk(self.dashboard):
            if isinstance(node.get('entity'), str):
                wired.add(node['entity'])
            data=node.get('service_data') or {}
            if isinstance(data, dict) and isinstance(data.get('entity_id'), str):
                wired.add(data['entity_id'])
        self.assertFalse(wired&dead)
        services=set()
        for node in build.walk(self.dashboard):
            if node.get('type')!='custom:button-card' or not node.get('entity'):
                continue
            action=node.get('tap_action') or {}
            domain=node['entity'].split('.')[0]
            if domain in build.COMMAND_DOMAINS and not (node.get('variables') or {}).get('offline') and not (node.get('variables') or {}).get('readonly'):
                self.assertIn(action.get('action'), ('toggle','call-service','perform-action'), node['entity'])
                self.assertNotEqual(action.get('action'),'more-info', node['entity'])
            if action.get('service'):
                services.add(action['service'])
            elif action.get('action')=='toggle':
                services.add(domain+'.toggle')
        for expected in ('light.toggle','cover.open_cover','cover.close_cover','lock.unlock','climate.set_hvac_mode','vacuum.start','lawn_mower.start_mowing','media_player.toggle','switch.toggle'):
            self.assertIn(expected, services)

    def test_exports_and_determinism(self):
        with tempfile.TemporaryDirectory() as tmp:
            cmd=[sys.executable,str(ROOT/'tools/build_dashboard.py'),'--output-dir',tmp]
            subprocess.run(cmd,check=True,capture_output=True)
            first={p.name:p.read_bytes() for p in Path(tmp).iterdir()}
            subprocess.run(cmd,check=True,capture_output=True)
            self.assertEqual(first,{p.name:p.read_bytes() for p in Path(tmp).iterdir()})
            self.assertEqual(json.loads(first['ai-nexus-v4.json']),yaml.safe_load(first['ai-nexus-v4.yaml']))
            self.assertEqual(json.loads(first['ai-nexus-v4.json']),self.dashboard)
            self.assertIn('glass', json.loads(first['ai-nexus-v4.json'])['button_card_templates'])
            registration=json.loads(first['ai-nexus-v4-registration.json'])
            self.assertTrue(registration['require_admin']);self.assertEqual(registration['mode'],'storage')

if __name__=='__main__':unittest.main()
