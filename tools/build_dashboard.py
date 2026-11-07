#!/usr/bin/env python3
"""Construction locale, déterministe et sans réseau des exports AI Nexus V4."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
VIEWS = [('accueil','Accueil','home'),('pieces','Pièces','floor-plan'),('equipements','Équipements','lightbulb'),('confort','Confort','thermometer'),('securite','Sécurité','shield-home'),('energie','Énergie','lightning-bolt'),('plus','Plus','dots-horizontal'),('sami','Sami','robot-vacuum'),('navimow','Navimow','robot-mower'),('voiture','Sportage','car'),('multimedia','Multimédia','play-circle'),('bureau','Bureau','desk'),('lecture-zen','Lecture Zen','book-open'),('jardin','Jardin','flower'),('recharge','Recharge','ev-station'),('cafe','Café','coffee'),('diagnostic','Diagnostic','stethoscope')]
ROOMS = [('salon','Salon','sofa'),('cuisine','Cuisine','stove'),('bureau','Bureau','desk'),('parents','Parents','bed-double'),('emile','Émile','bed'),('maddy','Maddy','bed')]
RESOURCE = {x: x+'.js' for x in ['button-card','bubble-card','navbar-card','navimower-map-card','yet-another-media-player']}
ENTITY_RE = re.compile(r'\b(?:sensor|binary_sensor|light|cover|lock|alarm_control_panel|person|weather|input_select|input_boolean|input_number|input_button|button|select|switch|script|timer|calendar|camera|media_player|vacuum|lawn_mower|climate|device_tracker|zone|number)\.[a-z0-9_]+\b')
MISSING = ['unknown','unavailable','none','']
OFFLINE_JS = '[[[ return "Hors ligne"; ]]]'
INFO_DOMAINS = {'sensor','binary_sensor','person','weather','device_tracker','camera','calendar','update','input_number','number','timer','image','event','zone','sun','counter','todo','text','time','stt','conversation','tts'}
COMMAND_DOMAINS = {'light','switch','fan','input_boolean','media_player','cover','lock','climate','vacuum','lawn_mower','button','input_button','script','scene','select','input_select','remote','siren','humidifier'}

STATE_JS = '''[[[
const s = entity?.state;
if (!s || ['unknown','unavailable','none'].includes(s)) return variables?.sleep ? 'En veille' : 'Donnée non disponible';
const labels = {on:'Allumé',off:'Éteint',home:'À la maison',not_home:'Absent',open:'Ouvert',closed:'Fermé',opening:'Ouverture',closing:'Fermeture',locked:'Verrouillée',unlocked:'Déverrouillée',armed_home:'Armée — présence',armed_away:'Armée — absence',armed_night:'Armée — nuit',disarmed:'Désarmée',pending:'Délai en cours',triggered:'Alerte',docked:'À la station',cleaning:'Nettoyage',mowing:'Tonte',paused:'En pause',idle:'En veille',returning:'Retour station',error:'À vérifier',playing:'Lecture',buffering:'Chargement',standby:'En veille',sunny:'Ensoleillé',cloudy:'Nuageux',partlycloudy:'Éclaircies',rainy:'Pluie',pouring:'Forte pluie',clear_night:'Nuit claire',snowy:'Neige',fog:'Brouillard',windy:'Vent'};
if (entity.entity_id?.startsWith('binary_sensor.') && ['on','off'].includes(s)) {
 const device = entity.attributes?.device_class;
 const labelsByClass = {door:['Fermée','Ouverte'],window:['Fermée','Ouverte'],opening:['Fermé','Ouvert'],moisture:['Sec','Humide'],battery:['Batterie normale','Batterie faible'],battery_charging:['Pas de charge','En charge'],plug:['Débranché','Branché'],connectivity:['Déconnecté','Connecté'],presence:['Absent','Présent'],problem:['Aucun problème','À vérifier']};
 return (labelsByClass[device] || ['Non','Oui'])[s==='on' ? 1 : 0];
}
const unit = entity.attributes?.unit_of_measurement;
if (unit) { const n = Number(s); return Number.isFinite(n) ? n.toLocaleString('fr-FR', {maximumFractionDigits:2}) + ' ' + unit : 'Donnée non disponible'; }
return labels[s] || s;
]]]'''

def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def references(value):
    if isinstance(value, dict):
        return set().union(*(references(v) for k,v in value.items() if k not in ('service','perform_action')))
    if isinstance(value, list):
        return set().union(*(references(v) for v in value))
    return set(ENTITY_RE.findall(value)) if isinstance(value,str) else set()


def load(name, root=ROOT):
    return json.loads((root / 'data' / (name+'.json')).read_text())


def js(body):
    return '[[[ '+body+' ]]]'


def section(title, cards):
    return {'type':'grid','cards':[{'type':'heading','heading':title}, *cards]}


def nav_card(path, title, icon):
    return {'type':'custom:button-card','template':'glass','name':title,'icon':'mdi:'+icon,'tap_action':{'action':'navigate','navigation_path':'/ai-nexus-v4/'+path},'hold_action':{'action':'none'},'double_tap_action':{'action':'none'}}


def entity_online(entity, state):
    value = state.get('state')
    if entity.split('.')[0] in ('button','input_button','scene'):
        return value != 'unavailable'
    return value not in (None,'unavailable','unknown','none','')


def needs_confirmation(service, entity):
    """Confirmation seulement pour ce qui bouge un accès, une vitre ou coupe une pièce."""
    entity = entity or ''
    service = service or ''
    if service.startswith(('cover.','lock.','alarm_control_panel.')):
        return True
    if service == 'button.press' and any(k in entity for k in ('hazard','horn','klaxon','valet','window')):
        return True
    if service == 'script.turn_on' and any(k in entity for k in ('eteindre','alarme','alarm')):
        return True
    return False


def confirmation(label):
    return {'text': label+' ? Vérifiez l’environnement avant de confirmer.'}


def assign_tap(entity, state, label):
    """Appui simple = commande. Maintien = détail. Hors ligne = rien."""
    domain = entity.split('.')[0]
    features = (state.get('attributes') or {}).get('supported_features') or 0
    if not entity_online(entity, state):
        return {'action':'none'}, {'action':'none'}, {'offline': True, 'kind':'offline'}
    if domain == 'alarm_control_panel' or (domain == 'lock' and not features & 1):
        return {'action':'none'}, {'action':'none'}, {'readonly': True, 'kind':'status'}
    if domain in INFO_DOMAINS:
        return {'action':'more-info'}, {'action':'none'}, {'readonly': True, 'kind':'info'}
    hold = {'action':'more-info'}
    flags = {'kind':'command'}
    data = {'entity_id': entity}
    if domain in ('light','switch','fan','input_boolean','media_player','remote','siren','humidifier'):
        return {'action':'toggle'}, hold, flags
    if domain == 'cover':
        return {'action':'toggle','confirmation':confirmation(label)}, hold, flags
    if domain == 'lock':
        return {'action':'call-service','service':'lock.unlock','service_data':data,'confirmation':confirmation(label)}, hold, flags
    if domain == 'climate':
        data = {'entity_id': entity, 'hvac_mode': '[[[ return entity.state === "off" ? "heat" : "off"; ]]]'}
        return {'action':'call-service','service':'climate.set_hvac_mode','service_data':data}, hold, flags
    if domain == 'vacuum':
        return {'action':'call-service','service':'vacuum.start','service_data':data}, hold, flags
    if domain == 'lawn_mower':
        return {'action':'call-service','service':'lawn_mower.start_mowing','service_data':data}, hold, flags
    if domain == 'button':
        action = {'action':'call-service','service':'button.press','service_data':data}
        if needs_confirmation('button.press', entity):
            action['confirmation'] = confirmation(label)
        return action, hold, flags
    if domain == 'input_button':
        return {'action':'call-service','service':'input_button.press','service_data':data}, hold, flags
    if domain == 'script':
        action = {'action':'call-service','service':'script.turn_on','service_data':data}
        if needs_confirmation('script.turn_on', entity):
            action['confirmation'] = confirmation(label)
        return action, hold, flags
    if domain == 'scene':
        return {'action':'call-service','service':'scene.turn_on','service_data':data}, hold, flags
    if domain == 'select':
        return {'action':'call-service','service':'select.select_next','service_data':data}, hold, flags
    if domain == 'input_select':
        return {'action':'call-service','service':'input_select.select_next','service_data':data}, hold, flags
    return {'action':'more-info'}, {'action':'none'}, {'readonly': True, 'kind':'info'}


def apply_action_policy(dashboard, states):
    """Toute tuile qui porte une entité reçoit la règle, y compris les sections héritées."""
    for node in walk(dashboard.get('views', [])):
        if node.get('type') != 'custom:button-card':
            continue
        entity = node.get('entity')
        if not isinstance(entity, str) or entity not in states:
            continue
        if (node.get('tap_action') or {}).get('action') == 'navigate':
            continue
        tap = (node.get('tap_action') or {}).get('action')
        if tap in (None, 'none') and (node.get('variables') or {}).get('offline'):
            continue
        label = node.get('name') if isinstance(node.get('name'), str) else entity
        hold = node.get('hold_action') or {}
        if tap in (None, 'none', 'more-info') and hold.get('action') in ('call-service','perform-action','toggle'):
            node['tap_action'] = hold
            node['hold_action'] = {'action':'more-info'}
            tap = hold.get('action')
        if tap in ('call-service','perform-action','toggle'):
            action = node['tap_action']
            service = action.get('service') or action.get('perform_action') or ''
            if tap == 'toggle' and entity.split('.')[0] in ('cover','lock') and not (action.get('confirmation') or {}).get('text'):
                action['confirmation'] = confirmation(label)
            elif needs_confirmation(service, entity) and not (action.get('confirmation') or {}).get('text'):
                action['confirmation'] = confirmation(label)
            if (node.get('hold_action') or {}).get('action') in (None, 'none'):
                node['hold_action'] = {'action':'more-info'}
            node.setdefault('variables', {}).setdefault('kind', 'command')
            continue
        new_tap, new_hold, flags = assign_tap(entity, states[entity], label)
        node['tap_action'] = new_tap
        node['hold_action'] = new_hold
        node.setdefault('variables', {}).update(flags)
        if flags.get('offline') and node.get('state_display') in (None, STATE_JS):
            node['state_display'] = OFFLINE_JS


class Builder:
    def __init__(self, root=ROOT):
        self.root = root
        self.states = {s['entity_id']:s for s in load('states', root)}
        self.mapping = load('entities_map', root)
        self.excluded = {k:v for k,v in self.mapping.items() if k in ('cuisine_temp','cuisine_hum') or v not in self.states}
        self.mapping = {k:v for k,v in self.mapping.items() if k not in self.excluded}
        self.legacy = [load(n,root) for n in ('legacy_lovelace','legacy_navimow_view')]
        self.notes = []

    def card(self, key, name, icon=None, path=None):
        entity = self.mapping.get(key, key)
        if entity not in self.states:
            raise ValueError('Entité non vérifiée: '+key)
        variables = {'sleep': 'navimow' in entity or 'yeelight' in entity or entity == 'light.ampoule_cuisine'}
        card = {'type':'custom:button-card','template':'glass','entity':entity,'name':name,'show_state':True,'state_display':STATE_JS,'variables':variables,'double_tap_action':{'action':'none'}}
        if icon:
            card['icon']='mdi:'+icon
        if path:
            card['tap_action']={'action':'navigate','navigation_path':path}
            card['hold_action']={'action':'none'}
            variables['kind']='nav'
            return card
        tap, hold, flags = assign_tap(entity, self.states[entity], name)
        variables.update(flags)
        card['tap_action']=tap
        card['hold_action']=hold
        if flags.get('offline'):
            card['state_display']=OFFLINE_JS
        return card

    def cards(self, pairs):
        return [self.card(k,n) for k,n in pairs if k in self.mapping or k in self.states]

    def command(self, key, name, service, feature=None):
        entity = self.mapping.get(key,key)
        features = (self.states[entity].get('attributes') or {}).get('supported_features') or 0
        if feature and not features & feature:
            self.notes.append('Commande omise, capacité absente : '+name)
            blocked = self.card(key, name+' — indisponible')
            blocked.pop('hold_action', None)
            blocked['tap_action']={'action':'none'}
            blocked.setdefault('variables', {})['offline']=True
            blocked['variables']['command_blocked']=True
            return blocked
        c=self.card(key,name)
        action={'action':'call-service','service':service,'service_data':{'entity_id':entity}}
        if needs_confirmation(service, entity):
            action['confirmation']=confirmation(name)
        c['tap_action']=action
        c['hold_action']={'action':'more-info'}
        c.setdefault('variables', {})['kind']='command'
        return c

    def room(self, key, title, icon):
        c=nav_card('pieces',title,icon)
        c['tap_action']['navigation_path']='#piece-'+key
        ids=[self.mapping[key+s] for s in ('_temp','_hum') if key+s in self.mapping]
        c.update(show_label=True,triggers_update=ids,label=js('const ids='+json.dumps(ids)+"; return ids.map(id => {const e=states[id]; const n=Number(e?.state); return e && !['unknown','unavailable',''].includes(e.state) && Number.isFinite(n) ? n.toLocaleString('fr-FR')+' '+(e.attributes.unit_of_measurement||'') : 'Donnée non disponible';}).join(' · ') || 'Éclairage et équipements';"))
        return c

    def popups(self):
        # Reprend le schéma pop-up/cards déjà présent dans legacy_lovelace.
        result=[]
        for key,title,icon in ROOMS:
            cards=self.cards([(key+'_temp','Température'),(key+'_hum','Humidité'),(key+'_light','Éclairage'),(key+'_light2','Éclairage secondaire')])
            if key+'_cover' in self.mapping:
                cards += [self.card(key+'_cover','Volet'),self.command(key+'_cover','Ouvrir le volet','cover.open_cover',1),self.command(key+'_cover','Fermer le volet','cover.close_cover',2)]
            if key=='bureau':cards+=self.cards([('bureau_contexte','Activité du bureau'),('bureau_presence','Probabilité de présence'),('bureau_camera','Caméra — ouvrir à la demande')])
            if key=='parents':cards.append(nav_card('lecture-zen','Lecture Zen','book-open'))
            result.append({'type':'custom:bubble-card','card_type':'pop-up','hash':'#piece-'+key,'name':title,'icon':'mdi:'+icon,'button_type':'name','show_header':True,'cards':cards})
        return result

    def legacy_card(self, typ):
        for source in self.legacy:
            for node in reversed(list(walk(source))):
                if node.get('type')==typ and not references(node)-self.states.keys():
                    self.notes.append('Configuration héritée réutilisée : '+typ)
                    return copy.deepcopy(node)
        self.notes.append('Configuration héritée absente ou entités obsolètes : '+typ)
        return {'type':'markdown','content':'Carte avancée non disponible dans les sources vérifiées. Les statuts restent accessibles ci-dessus.'}

    def build(self):
        templates={'glass':{'show_state':False,'tap_action':{'action':'none'},'hold_action':{'action':'none'},'double_tap_action':{'action':'none'},'state':[{'value':'on','styles':{'icon':[{'color':'#1f8fff'}],'card':[{'box-shadow':'inset 3px 0 0 #1f8fff, 0 10px 28px rgba(16,52,84,.08)'}]}},{'value':'open','styles':{'icon':[{'color':'#1f8fff'}],'card':[{'box-shadow':'inset 3px 0 0 #1f8fff, 0 10px 28px rgba(16,52,84,.08)'}]}},{'value':'heat','styles':{'icon':[{'color':'#e07a3d'}],'card':[{'box-shadow':'inset 3px 0 0 #e07a3d, 0 10px 28px rgba(16,52,84,.08)'}]}},{'value':'playing','styles':{'icon':[{'color':'#1f8fff'}]}},{'value':'off','styles':{'icon':[{'color':'#8aa0b4'}]}},{'value':'closed','styles':{'icon':[{'color':'#8aa0b4'}]}},{'value':'unavailable','styles':{'card':[{'opacity':'0.62'},{'border':'1px dashed rgba(90,112,130,.45)'}],'icon':[{'color':'#93a3b3'}]}},{'value':'unknown','styles':{'card':[{'opacity':'0.62'},{'border':'1px dashed rgba(90,112,130,.45)'}],'icon':[{'color':'#93a3b3'}]}}],'styles':{'card':[{'border-radius':'22px'},{'padding':'16px 18px'},{'min-height':'92px'},{'background':'var(--ha-card-background)'},{'border':'1px solid var(--divider-color)'},{'box-shadow':'0 10px 28px rgba(16,52,84,.08)'},{'backdrop-filter':'blur(16px)'}],'name':[{'white-space':'normal'},{'font-weight':'650'},{'font-size':'15px'},{'letter-spacing':'-0.01em'}],'state':[{'white-space':'normal'},{'font-size':'13px'},{'font-weight':'600'}],'label':[{'white-space':'normal'}],'icon':[{'color':'var(--primary-color)'},{'width':'26px'}]}}}
        nav={'type':'custom:navbar-card','desktop':{'position':'left','show_labels':True},'mobile':{'show_labels':True},'routes':[{'url':'/ai-nexus-v4/'+p,'label':t,'icon':'mdi:'+i} for p,t,i in VIEWS[:7]]}
        temps=[self.mapping[k+'_temp'] for k in ('salon','sam','entree','parents','emile','maddy')]
        avg={'type':'custom:button-card','template':'glass','name':'Température maison','icon':'mdi:home-thermometer','show_label':True,'triggers_update':temps,'label':js('const ids='+json.dumps(temps)+"; const values=ids.map(id=>states[id]?.state).filter(s=>s!=null && !['unknown','unavailable',''].includes(s)).map(Number).filter(Number.isFinite); return values.length ? (values.reduce((a,b)=>a+b,0)/values.length).toLocaleString('fr-FR',{maximumFractionDigits:1})+' °C · '+values.length+' pièces mesurées' : 'Donnée non disponible';")}
        people=[self.mapping[k] for k in ('denis','laura','emile','maddy')]
        mode=self.mapping['mode_maison']; alarm=self.mapping['alarme']
        header={'type':'custom:button-card','template':'glass','name':js("return 'Bonjour '+(hass.user?.name || 'à vous');"),'show_label':True,'triggers_update':'all','label':js("const date=new Date().toLocaleDateString('fr-FR',{timeZone:hass.config.time_zone,weekday:'long',day:'numeric',month:'long',year:'numeric'}); const people="+json.dumps(people)+"; return date+' · '+people.filter(id=>states[id]?.state==='home').length+' à la maison';")}
        alert={'type':'custom:button-card','template':'glass','name':'Vigilance maison','icon':'mdi:shield-check','show_label':True,'triggers_update':'all','label':js('const people='+json.dumps(people)+'; const mode=states['+json.dumps(mode)+']?.state; const alarm=states['+json.dumps(alarm)+"]?.state; const present=people.some(id=>states[id]?.state==='home'); if (!mode || !alarm || ['unknown','unavailable'].includes(mode) || ['unknown','unavailable'].includes(alarm)) return 'Donnée non disponible'; if (alarm==='triggered') return 'Alarme déclenchée'; if(present && (mode.toLowerCase()==='absent' || alarm==='armed_away')) return 'Présence détectée : vérifiez le mode maison et l’alarme'; if (people.some(id=>!states[id] || ['unknown','unavailable',''].includes(states[id].state))) return 'Présence partiellement non disponible : vérification nécessaire'; return 'Aucune incohérence présence / absence détectée';")}
        family=[]
        for key,name in [('denis','Denis'),('laura','Laura'),('emile','Émile'),('maddy','Maddy')]:
            c=self.card(key,name,'account'); bat=self.mapping[key+'_bat']; c.update(show_label=True,triggers_update=[bat],label=js('const e=states['+json.dumps(bat)+"]; const n=Number(e?.state); return e && !['unknown','unavailable',''].includes(e.state) && Number.isFinite(n) ? 'Téléphone : '+n+' %' : 'Batterie non disponible';")); family.append(c)
        content={}
        content['accueil']=[section('AI Nexus · Home V4',[header,self.card('meteo','Météo'),self.card('mode_maison','Mode maison'),alert]),section('Famille',family),section('Pièces principales',[self.room(*r) for r in ROOMS]),section('Climat',[avg]+self.cards([(k+'_temp',n) for k,n in [('salon','Salon'),('entree','Entrée'),('parents','Parents'),('emile','Émile'),('maddy','Maddy'),('sam','Salle à manger')]])),section('Énergie et sécurité',self.cards([('puissance','Puissance actuelle'),('conso_jour','Consommation du jour'),('serrure','Porte d’entrée'),('alarme','Alarme')])),section('Au quotidien',[self.card(k,n,path='/ai-nexus-v4/'+p) for k,n,p in [('sami','Sami','sami'),('navimow','Navimow','navimow'),('ev_level','Sportage','voiture'),('tv_salon','Multimédia','multimedia')]])]
        from visual_design import build_home
        content['accueil']=[{'type':'grid','column_span':4,'cards':build_home(self)}]
        content['pieces']=[section('Votre maison',[self.room(*r) for r in ROOMS])]
        content['equipements']=[section('Éclairages',self.cards([(k+'_light',n) for k,n,_ in ROOMS])),section('Équipements',[nav_card(p,t,i) for p,t,i in VIEWS[7:]])]
        climates=[self.card(e, self.states[e]['attributes'].get('friendly_name','Chauffage')) for e in sorted(self.states) if e.startswith('climate.') and 'sportage' not in e and 'tado' not in e and entity_online(e, self.states[e])]
        content['confort']=[section('Températures',[copy.deepcopy(avg)]+self.cards([(k+'_temp',n) for k,n in [('salon','Salon'),('sam','Salle à manger'),('entree','Entrée'),('parents','Parents'),('emile','Émile'),('maddy','Maddy')]])),section('Chauffage',climates)]
        security=self.cards([('serrure','Porte d’entrée'),('garage_cover','Garage'),('alarme','Alarmo'),('porte_entree','Contact porte d’entrée'),('fenetre_cuisine','Fenêtre cuisine'),('porte_salon_jardin','Porte jardin')])
        security += [self.command('serrure','Verrouiller la porte','lock.lock'),self.command('garage_cover','Ouvrir le garage','cover.open_cover',1),self.command('garage_cover','Fermer le garage','cover.close_cover',2)]
        # Le code Alarmo reste géré par son interface existante : pas de PIN exporté.
        security.append({'type':'markdown','content':'Alarmo : utilisez votre interface de sécurité habituelle pour armer ou désarmer avec votre code.'})
        content['securite']=[section('Accès et alarme',security),section('Caméras à la demande',self.cards([('cam_entree','Entrée'),('cam_jardin','Jardin'),('cam_garage','Garage'),('cam_doorbell','Sonnette')]))]
        content['energie']=[section('Consommation et production',self.cards([('puissance','Puissance'),('conso_jour','Aujourd’hui'),('conso_mois','Ce mois'),('cout_mois','Coût mensuel'),('tarif','Tarif en cours'),('solaire_jour','Solaire du jour'),('solaire_total','Production solaire cumulée')]))]
        content['plus']=[section('Maison',[self.card('mode_maison','Mode maison')]),section('Vos espaces',[nav_card(p,t,i) for p,t,i in VIEWS[7:]])]
        content['sami']=[section('Sami',self.cards([('sami','Aspirateur Sami'),('sensor.sami_surface_de_nettoyage','Surface nettoyée'),('sensor.sami_temps_restant_brosse_principale','Brosse principale'),('sensor.sami_temps_restant_brosse_laterale','Brosse latérale')])+[self.command('sami','Retour à la station','vacuum.return_to_base',16),self.command('sami','Mettre en pause','vacuum.pause',4),self.legacy_card('custom:xiaomi-vacuum-map-card')])]
        content['navimow']=[section('Navimow',self.cards([('navimow','Tondeuse'),('navimow_bat','Batterie'),('navimow_dock','Station'),('sensor.navimow_i206_awd_task_progress','Progression')])+[self.command('navimow','Pause','lawn_mower.pause',2),self.command('navimow','Retour station','lawn_mower.dock',4),{'type':'conditional','conditions':[{'entity':self.mapping['navimow'],'state_not':'unavailable'},{'entity':self.mapping['navimow'],'state_not':'unknown'}],'card':self.legacy_card('custom:navimower-map-card')}])]
        sportage_commands=[self.card(e,n) for e,n in [('switch.sportage_ev_charging','Charge EV'),('switch.sportage_climate','Climatisation rapide'),('climate.sportage_climate_control','Clim habitacle'),('button.sportage_force_refresh','Actualiser le véhicule'),('button.sportage_close_all_windows','Fermer les vitres'),('button.sportage_open_all_windows','Ouvrir les vitres'),('button.sportage_vent_all_windows','Entrouvrir les vitres'),('button.sportage_start_hazard_lights','Feux de détresse'),('lock.sportage_door_lock','Verrouillage')]]
        content['voiture']=[section('Sportage',self.cards([('ev_level','Batterie de traction'),('ev_range','Autonomie électrique'),('fuel_level','Carburant'),('fuel_range','Autonomie carburant'),('odo','Kilométrage'),('car_bat','Batterie 12 V'),('ev_charge','Charge en cours'),('ev_plug','Câble branché'),('sensor.sportage_last_updated_at','Dernière actualisation')])+sportage_commands)]
        content['multimedia']=[section('Musique et télévision',self.cards([('tv_salon','Télévision'),('soundbar','Barre de son'),('mp_bureau','Bureau'),('mp_sam','Salle à manger')])+[self.legacy_card('custom:yet-another-media-player')])]
        self.notes.append('Ambilight bureau masqué : light.lumiere_bureau_ambilight est indisponible, aucun équivalent vivant.')
        content['bureau']=[section('Bureau',self.cards([('bureau_light','Éclairage'),('bureau_contexte','Activité PC'),('bureau_presence','Probabilité de présence'),('bureau_lux','Luminosité'),('bureau_duree','Durée d’éclairage'),('bureau_camera','Caméra à la demande')]))]
        content['lecture-zen']=[section('Lecture Zen',self.cards([('zen_mode','Mode nuit'),('zen_notif','Notifications'),('zen_remaining','Temps restant'),('zen_light','Lampe de lecture')])+[self.command('zen_bouton','Démarrer la lecture','input_button.press'),self.command('zen_extend','Prolonger la lecture','script.turn_on'),self.command('zen_eteindre','Éteindre en douceur','script.turn_on')])]
        content['jardin']=[section('Jardin',self.cards([('plante_sol','Humidité du sol'),('plante_temp','Température de la plante'),('plante_bat','Batterie de la sonde'),('plante_dry','Besoin d’eau')])+[nav_card('navimow','Tondeuse','robot-mower')])]
        content['recharge']=[section('Recharge',[self.card('switch.prise_chargeur_kia','Prise du chargeur'),self.card('switch.sportage_ev_charging','Charge véhicule'),self.card('switch.sportage_scheduled_charging','Charge programmée'),self.card('switch.sportage_off_peak_charge_only','Heures creuses seulement')]+self.cards([('rv3_statut','État recharge'),('rv3_jour','Coût du jour'),('rv3_semaine','Coût de la semaine'),('rv3_mois','Coût du mois'),('rv3_budget','Budget mensuel'),('phev_conso_jour','Consommation du jour'),('ev_plug','Branchement')]))]
        content['cafe']=[section('Café',self.cards([('cafe_allumer','Allumer la machine'),('cafe_etat','Machine à café'),('cafe_boisson','Boisson'),('cafe_profil','Profil'),('cafe_temp','Température de l’eau'),('cafe_detartrage','Détartrage')]))]
        used=sorted(references(content))
        diagnostic={'type':'custom:button-card','template':'glass','name':'Données à vérifier','show_label':True,'triggers_update':used,'label':js('const ids='+json.dumps(used)+"; const missing=ids.filter(id=>!states[id] || ['unknown','unavailable'].includes(states[id].state)); return missing.length+' données non disponibles sur '+ids.length+' suivies. Navimow et lumières murales peuvent être en veille.';")}
        content['diagnostic']=[section('Diagnostic local',[diagnostic,{'type':'markdown','content':'**Hors ligne, laissés visibles seulement ici.** Ambilight bureau (`light.lumiere_bureau_ambilight`) indisponible : tuile masquée. Meghann : les trois lecteurs sont indisponibles, aucun remplacement. Rideau Maddy `cover.curtain_switch_rideau` : position inconnue, la commande passe par `cover.volet_maddy_etat`.\n\n**Remplacements du 7 novembre 2026.** Salon → `light.salon_projecteur` (le voyant `light.salon_led_d_etat` n’est pas une lampe). Cuisine → `light.ampoule_cuisine`. Émile → `light.ampoule_emile`. Maddy → `light.ampoule_maddy`. Parents → `light.ampoule_chambre_parentale_1`. Bureau → `switch.interrupteur_bureau`. Volets Émile et cuisine → entités `*_etat`. Barre de son → `media_player.sound_bar_lg`.\n\nLes capteurs Sportage restent en lecture seule. Les commandes Kia (charge, climatisation, vitres, détresse) sont sur la vue Sportage. Alarmo s’arme depuis son interface, avec le code : aucun PIN n’est exporté.'}])]
        # Rebase live (08/10) : sections PHEV publiées après le générateur sur
        # 'voiture' et 'recharge'. Source : config/live_sections_capture.json,
        # extraction lecture seule du live (voir docs/TEN_MISSIONS_FINAL_REPORT.md §7).
        _cap = __import__('pathlib').Path(__file__).resolve().parents[1] / 'config' / 'live_sections_capture.json'
        if _cap.is_file():
            for _key, _entry in json.loads(_cap.read_text(encoding='utf-8')).items():
                if _key in content and content[_key]:
                    content[_key] = content[_key][:1] + [_e['section'] for _e in _entry['sections']] + content[_key][1:]
        views=[]
        for path,title,icon in VIEWS:
            sections=content[path]
            sections.append(section('Navigation',[copy.deepcopy(nav)]))
            if path in ('accueil','pieces'):
                sections.append({'type':'grid','cards':self.popups()})
            view={'title':title,'path':path,'icon':'mdi:'+icon,'type':'sections','max_columns':4 if path=='accueil' else 3,'theme':'AI Nexus Glass','sections':sections}
            if path=='diagnostic':view['subview']=True
            views.append(view)
        dashboard={'title':'AI Nexus Home V4','button_card_templates':templates,'views':views}
        apply_action_policy(dashboard, self.states)
        return dashboard


def validate(dashboard, states, resources, services=None):
    errors=[]
    templates = dashboard.get('button_card_templates', {})
    for node in walk(dashboard.get('views', [])):
        if node.get('type') != 'custom:button-card':
            continue
        names = node.get('template', [])
        if isinstance(names, str):
            names = [names]
        for name in names:
            if name not in templates:
                errors.append('Template button-card absent : ' + name)
    missing=references(dashboard)-states.keys()
    if missing:errors.append('Entités absentes : '+', '.join(sorted(missing)))
    urls=[r['url'].split('?')[0] for r in resources]
    paths={v['path'] for v in dashboard['views']}
    for view in dashboard['views']:
        hashes=[n['hash'] for n in walk(view) if 'hash' in n]
        if len(hashes)!=len(set(hashes)):errors.append('Hash dupliqué : '+view['path'])
        for node in walk(view):
            typ=node.get('type','')
            if typ.startswith('custom:'):
                name=typ[7:]
                if name not in RESOURCE or not any(u.endswith('/'+RESOURCE[name]) for u in urls):errors.append('Ressource inconnue : '+typ)
            path=node.get('navigation_path',node.get('url',''))
            if path.startswith('#') and path not in hashes:errors.append('Hash absent : '+path)
            if path.startswith('/ai-nexus-v4/') and path.split('#',1)[0].rsplit('/',1)[1] not in paths:errors.append('Vue absente : '+path)
            for key in ('tap_action','hold_action','double_tap_action'):
                action=node.get(key) or {}
                act=action.get('action')
                if act in ('call-service','perform-action','toggle'):
                    service=action.get('service') or action.get('perform_action') or ''
                    target=action.get('service_data',{}).get('entity_id') if isinstance(action.get('service_data'), dict) else None
                    entity_for_rule=target or node.get('entity') or ''
                    physical=act=='toggle' and str(entity_for_rule).startswith(('cover.','lock.')) or needs_confirmation(service, str(entity_for_rule))
                    if physical and not (action.get('confirmation') or {}).get('text'):
                        errors.append('Commande physique sans confirmation')
                    if services is not None and service and not str(service).startswith('[[[') and service not in services:
                        errors.append('Service absent : '+service)
                    if service and isinstance(target, str) and not target.startswith('[[['):
                        if target not in states:errors.append('Cible de service absente')
                        elif service.split('.')[0] != target.split('.')[0]:errors.append('Domaine de service incompatible')
                        else:
                            required={'cover.open_cover':1,'cover.close_cover':2,'cover.stop_cover':8,'lock.unlock':1,'lock.open':1}.get(service)
                            if required and not (states[target].get('attributes') or {}).get('supported_features',0) & required:errors.append('Capacité de commande absente')
            entity=node.get('entity') or ''
            if isinstance(entity, str) and entity.startswith(('lock.','cover.','alarm_control_panel.')):
                if typ!='custom:button-card' and typ:errors.append('Contrôle sensible natif : '+typ)
                if (node.get('tap_action') or {}).get('action')=='more-info':errors.append('Accès sensible sans confirmation')
            if typ=='custom:button-card' and isinstance(entity, str) and entity:
                tap=(node.get('tap_action') or {}).get('action')
                flags=node.get('variables') or {}
                domain=entity.split('.')[0]
                if not tap:errors.append('Tuile sans action : '+entity)
                if tap in (None,'none') and not flags.get('offline') and not flags.get('readonly'):
                    errors.append('Tuile d’équipement inerte : '+entity)
                if tap=='more-info' and domain in COMMAND_DOMAINS:errors.append('Fiche info sur une commande : '+entity)
                if flags.get('offline') and tap not in ('none', None):errors.append('Entité hors ligne encore pilotable : '+entity)
                if domain=='alarm_control_panel' and tap in ('more-info','toggle','call-service','perform-action'):
                    errors.append('Alarme pilotée hors de son interface : '+entity)
    if errors:raise ValueError('\n'.join(sorted(set(errors))))


def theme():
    return {'AI Nexus Glass':{'primary-color':'#1f8fff','accent-color':'#0f9d8a','ha-card-border-radius':'22px','ha-card-border-width':'1px','ha-card-box-shadow':'0 10px 28px rgba(16,52,84,.08)','modes':{'light':{'primary-background-color':'#e7f1f8','secondary-background-color':'#dceaf4','ha-card-background':'rgba(255,255,255,.9)','primary-text-color':'#16324a','secondary-text-color':'#3d5870','divider-color':'rgba(32,72,104,.16)'},'dark':{'primary-background-color':'#0e1926','secondary-background-color':'#15283a','ha-card-background':'rgba(22,40,58,.94)','primary-text-color':'#f2f7fc','secondary-text-color':'#c5d6e6','divider-color':'rgba(160,198,224,.24)'}}}}


def service_names(data):
    """Accepte l'export /api/services, ou une liste de noms domain.service."""
    if all(isinstance(x,str) for x in data):return set(data)
    return {row['domain']+'.'+name for row in data for name in row['services']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'config')
    args=parser.parse_args()
    b=Builder(); dashboard=b.build()
    service_file=ROOT/'data/services.json'
    services=service_names(json.loads(service_file.read_text())) if service_file.exists() else None
    validate(dashboard,b.states,load('resources'),services)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    exports={'ai-nexus-v4.json':json.dumps(dashboard,ensure_ascii=False,indent=2)+'\n','ai-nexus-v4.yaml':yaml.safe_dump(dashboard,allow_unicode=True,sort_keys=False),'ai-nexus-glass.yaml':yaml.safe_dump(theme(),allow_unicode=True,sort_keys=False),'ai-nexus-v4-registration.json':json.dumps({'url_path':'ai-nexus-v4','title':'AI Nexus Home V4','icon':'mdi:home-assistant','mode':'storage','require_admin':True,'show_in_sidebar':True},ensure_ascii=False,indent=2)+'\n'}
    manifest={'status':'LOCAL_PASS','views':len(dashboard['views']),'entities':sorted(references(dashboard)),'excluded_mapping':b.excluded,'notes':b.notes,'action_model':'tap-commande, maintien-detail, hors-ligne non pilotable','service_validation':'LOCAL_PASS' if services is not None else 'PENDING_SERVICE_CATALOG','pending':['PENDING_PHYSICAL_CONFIRMATION'],'resources_removed':['/webrtc/webrtc-camera.js','/local/community/mushroom-cards/mushroom.js','/local/bubble/bubble-modules.yaml','/local/community/lovelace-card-mod/card-mod.js (doublon css)'],'decisions':['salon_light=light.salon_projecteur','cuisine_light=light.ampoule_cuisine','emile_light=light.ampoule_emile','maddy_light=light.ampoule_maddy','parents_light=light.ampoule_chambre_parentale_1','bureau_light=switch.interrupteur_bureau','soundbar=media_player.sound_bar_lg']}
    exports['ai-nexus-v4-validation.json']=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    for filename,body in exports.items():(args.output_dir/filename).write_text(body)
    print(f'LOCAL_PASS: {len(dashboard["views"])} vues, {len(manifest["entities"])} entités vérifiées. Exports locaux uniquement.')

if __name__=='__main__':main()
