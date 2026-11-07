"""Accueil photographique V4 : cartes existantes, données HA, aucun actionneur.

Les composites utilisent le CSS de button-card lui-même, pas celui du banc QA.
"""
import json

PREFIX = '/local/ai-nexus-v4/visual/'

# Utilitaires communs aux templates JS button-card ; toutes les données HA sont
# échappées avant insertion HTML. Une donnée absente n'est jamais convertie en 0.
HELPERS = r'''
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const get = id => states[id];
const ok = id => !!get(id) && !['unknown','unavailable',''].includes(get(id).state);
const number = id => ok(id) && Number.isFinite(Number(get(id).state)) ? Number(get(id).state) : null;
const value = (id, unit = '') => ok(id) ? esc(get(id).state) + (unit ? ' ' + esc(unit) : '') : 'Indisponible';
const unitValue = id => value(id, get(id)?.attributes?.unit_of_measurement || '');
const translated = (id, map = {}) => ok(id) ? esc(map[get(id).state] ?? get(id).state) : 'Indisponible';
const icon = name => `<ha-icon icon="${esc(name)}"></ha-icon>`;
const label = (name, text, ico = '') => `<div class="metric">${ico ? icon(ico) : ''}<div><small>${esc(name)}</small><strong>${text}</strong></div></div>`;
const progress = id => {const n = number(id); return n === null ? '' : `<div class="bar"><i style="width:${Math.max(0,Math.min(100,n))}%"></i></div>`;};
'''
# Classification du téléphone indépendante de person.*. Pas de déduction mobile
# à partir d'un SSID manquant ni de la seule activation de la radio Wi-Fi.
FAMILY_HELPERS = r'''
const normalized = id => String(get(id)?.state ?? '').trim().toLowerCase();
const noData = new Set(['', 'unknown', 'unavailable', 'null', 'undefined', 'none', 'not connected', '<not connected>', 'disconnected']);
const connection = (wifiId, networkId, mobileId) => {
  const net = normalized(networkId);
  const ssid = String(get(wifiId)?.state ?? '').trim();
  const connectedSSID = !noData.has(ssid.toLowerCase());
  let text = 'Non renseignée', ico = 'mdi:help-network-outline';
  if (['wifi', 'wi-fi', 'wi_fi'].includes(net)) { text = 'Wi-Fi'; ico = 'mdi:wifi'; }
  else if (['cellular', 'mobile', 'mobile data'].includes(net)) {
    const generation = normalized(mobileId).replace(/[ _-]/g, '');
    const types = {gprs:'2G',edge:'2G',gsm:'2G',cdma:'2G','1xrtt':'2G',umts:'3G',hspa:'3G',hsdpa:'3G',hsupa:'3G',hspap:'3G',wcdma:'3G',evdo0:'3G',evdoa:'3G',evdob:'3G',tdscdma:'3G',lte:'4G',lteca:'4G',nr:'5G',nrnsa:'5G',nrsa:'5G','2g':'2G','3g':'3G','4g':'4G','5g':'5G'};
    text = types[generation] || 'Mobile'; ico = 'mdi:signal-cellular-3';
  } else if (['none', 'offline', 'not connected', 'disconnected'].includes(net)) { text = 'Sans connexion'; ico = 'mdi:network-off-outline'; }
  else if (net === 'ethernet') { text = 'Ethernet'; ico = 'mdi:ethernet'; }
  else if (connectedSSID) { text = 'Wi-Fi'; ico = 'mdi:wifi'; }
  const title = text === 'Wi-Fi' && connectedSSID ? ssid : text;
  return `<small class="person-detail connection">${icon(ico)}<span title="${esc(title)}">${esc(text)}</span></small>`;
};
const batteryDetail = id => {
  const raw = String(get(id)?.state ?? '').trim();
  const n = raw !== '' ? Number(raw) : NaN;
  const valid = Number.isFinite(n) && n >= 0 && n <= 100;
  const step = valid ? Math.floor(n / 10) * 10 : null;
  const ico = !valid ? 'mdi:battery-unknown' : step === 100 ? 'mdi:battery' : step === 0 ? 'mdi:battery-outline' : `mdi:battery-${step}`;
  const text = valid ? n.toLocaleString('fr-FR',{maximumFractionDigits:0}) + ' %' : 'Indisponible';
  return `<small class="person-detail battery">${icon(ico)}<span>${esc(text)}</span></small>`;
};
'''
CSS = r'''
<style>
*{box-sizing:border-box}.panel{text-align:left;color:var(--primary-text-color);font-family:var(--paper-font-body1_-_font-family,system-ui);width:100%;min-width:0;overflow-wrap:anywhere}
.panel ha-icon{width:20px;height:20px;--mdc-icon-size:20px;display:inline-flex}h2,h3,p{margin:0}h2{font-size:17px;letter-spacing:-.3px}h3{font-size:15px}small{font-size:12px;color:var(--secondary-text-color);display:block}strong{font-size:14px;display:block;overflow-wrap:anywhere;word-break:keep-all}.muted{color:var(--secondary-text-color);font-size:12px}.head{display:flex;align-items:center;gap:8px;margin-bottom:12px}.head>ha-icon{color:#378ec8;width:21px}.head .arrow{margin-left:auto;opacity:.5}.metric{display:flex;align-items:center;gap:8px;min-width:0;white-space:normal}.metric>div{min-width:0}.head h2{min-width:0;overflow-wrap:anywhere}.metric>ha-icon{width:18px;height:18px;color:#478fae;flex-shrink:0}
/* button-card injecte :not(ha-state-icon) ha-icon{margin:auto} : en flex cela
   pousse l'icone au centre de l'espace libre et l'ejecte de son libelle.
   Specificite .panel .x>ha-icon (0,2,1) > regle button-card (0,1,1). */
.panel .metric>ha-icon,.panel .head>ha-icon,.panel .person>ha-icon,.panel .person-detail>ha-icon,.nexus07 .n7-row>ha-icon,.nexus07 h2>ha-icon{margin-left:0!important;margin-right:0!important}.metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 12px}.bar{height:6px;background:rgba(62,133,170,.14);border-radius:9px;overflow:hidden;margin-top:8px}.bar i{display:block;height:100%;background:#3ca59b;border-radius:9px}.pill{padding:6px 12px;border-radius:20px;background:rgba(73,168,140,.13);font-size:12px;white-space:normal;overflow-wrap:anywhere}.photo{width:100%;object-fit:cover;border-radius:12px;display:block}.product{height:82px;object-fit:contain;margin:10px 0;width:100%;border-radius:12px}.footer{font-size:11px;color:var(--secondary-text-color);margin-top:14px;opacity:.8}.room .photo{height:110px;border-radius:15px 15px 0 0}.room .room-info{padding:14px}.room .head{margin-bottom:10px}.room .metrics{gap:10px}.room .metric strong{font-size:13px}.room .metric small{font-size:10px}.room .footer{margin-top:10px}.coverline{font-size:11px;margin-top:9px;color:var(--secondary-text-color)}
/* Mobile first responsive */
@container(max-width:480px){.metrics{grid-template-columns:1fr;gap:10px}.metric{justify-content:flex-start}.room .photo{height:120px}.room .metrics{gap:8px}.pill{font-size:11px;padding:5px 10px}.head{gap:6px}.head>ha-icon{width:19px}}
@container(max-width:600px){.room .photo{height:105px}.metrics{gap:10px}.head{margin-bottom:10px}}
</style>
'''


def template(body):
    return '[[[\n' + HELPERS + '\nreturn `' + CSS + body + '`;\n]]]'


def card(name, body, entities, path=None, padding='16px'):
    cfg = {'type': 'custom:button-card', 'name': name, 'show_name': False, 'show_icon': False,
           'tap_action': {'action': 'navigate', 'navigation_path': path} if path else {'action': 'none'},
           'hold_action': {'action': 'none'}, 'double_tap_action': {'action': 'none'},
           'triggers_update': [entity for entity in dict.fromkeys(entities) if entity], 'custom_fields': {'body': template(body)},
           'styles': {'card': [{'padding': padding}, {'border-radius': '20px'},
                               {'background': 'var(--ha-card-background)'},
                               {'border': '1px solid var(--divider-color)'},
                               {'box-shadow': '0 4px 18px rgba(30,65,91,.08)'},
                               {'overflow': 'hidden'}, {'container-type': 'inline-size'}],
                      'grid': [{'grid-template-areas': '"body"'}, {'grid-template-columns': 'minmax(0,1fr)'},
                               {'grid-template-rows': '1fr'}],
                      'custom_fields': {'body': [{'width': '100%'}, {'min-width': '0'}, {'white-space': 'normal'}]}}}
    return cfg


def group(name, children, columns, title=None, tablet=2, mobile=1):
    keys = list(children)
    areas = ' '.join(keys)
    grid_areas = (('"' + ' '.join(['heading'] * len(keys)) + '" ') if title else '') + '"' + areas + '"'
    fields = {key: {'card': value} for key, value in children.items()}
    if title:
        fields['heading'] = '<div style="text-align:left;font-size:16px;font-weight:600;padding:4px 2px 10px">' + title + '</div>'
    def responsive(count):
        rows = [keys[i:i + count] for i in range(0, len(keys), count)]
        if title:
            rows.insert(0, ['heading'] * count)
        return ' '.join('"' + ' '.join(row + ['.'] * (count - len(row))) + '"' for row in rows)
    return {'type': 'custom:button-card', 'name': name, 'show_name': False, 'show_icon': False,
            'tap_action': {'action': 'none'}, 'hold_action': {'action': 'none'},
            'double_tap_action': {'action': 'none'}, 'custom_fields': fields,
            'section_mode': True,
            'grid_options': {'columns': 'full', 'rows': 'auto'},
            'styles': {'card': [{'background': 'transparent'}, {'border': '0'}, {'box-shadow': 'none'}, {'padding': '0'}, {'overflow': 'visible'}, {'container-type': 'inline-size'}],
                       'grid': [{'grid-template-areas': grid_areas}, {'grid-template-columns': columns},
                                {'gap': '12px'}, {'align-items': 'stretch'}],
                       'custom_fields': {key: [{'min-width': '0'}, {'width': '100%'}, {'height': '100%'}, {'white-space': 'normal'}] for key in keys}},
            'extra_styles': '@container(max-width:1250px){#container{grid-template-columns:repeat(' + str(tablet) + ',minmax(0,1fr))!important;grid-template-areas:' + responsive(tablet) + '!important}}@container(max-width:650px){#container{grid-template-columns:repeat(' + str(mobile) + ',minmax(0,1fr))!important;grid-template-areas:' + responsive(mobile) + '!important}}'}


def head(title, icon):
    return '<div class="head">${icon(' + json.dumps(icon) + ')}<h2>' + title + '</h2><span class="arrow">›</span></div>'



SLOTS = ('alarme','porte_entree','nuki_porte','serrure','garage_cover','cam_entree','cam_jardin','cam_garage','cam_cuisine','cam_doorbell')

def improve_security(card, mapping):
    ids = {k: mapping.get(k) for k in SLOTS}
    js = '''
const esc = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const missing = new Set(['','unknown','unavailable','none','null','undefined','restored']);
const valid = id => !!states[id] && !states[id].attributes?.restored && !missing.has(String(states[id].state ?? '').trim().toLowerCase());
const text = (id, map) => !valid(id) ? 'Indisponible' : esc(map[states[id].state] ?? states[id].state);
const row = (label,id,map,icon) => `<div class="n7-row"><ha-icon icon="${icon}"></ha-icon><span>${label}</span><strong>${text(id,map)}</strong></div>`;
'''
    js += 'const ids = '+json.dumps(ids)+';\n'
    js += '''const door = {on:'Ouverte',off:'Fermée'};
const alarm = {disarmed:'Désarmée',armed_home:'Présence',armed_away:'Absence',armed_night:'Nuit',armed_vacation:'Vacances',armed_custom_bypass:'Personnalisée',arming:'Armement en cours',pending:'Temporisation',disarming:'Désarmement en cours',triggered:'Déclenchée'};
const cams = ['cam_entree','cam_jardin','cam_garage','cam_cuisine','cam_doorbell'].map(k=>ids[k]);
const known = cams.filter(valid).length;
const conflict = valid(ids.porte_entree) && valid(ids.nuki_porte) && states[ids.porte_entree].state !== states[ids.nuki_porte].state;
return `<style>
.nexus07{width:100%;min-width:0;text-align:left;font-family:system-ui;color:var(--primary-text-color);overflow-wrap:anywhere}
.nexus07 *{box-sizing:border-box}.nexus07 h2{font-size:17px;margin:0 0 10px;display:flex;gap:8px;align-items:center}.nexus07 ha-icon{--mdc-icon-size:18px;width:18px;height:18px;color:#478fae;flex-shrink:0}
.nexus07 .n7-row{display:grid;grid-template-columns:18px minmax(0,1fr) minmax(0,1fr);gap:7px;align-items:center;margin:7px 0;font-size:12px}.nexus07 strong{font-size:12px;white-space:normal;overflow-wrap:anywhere;font-weight:600}.nexus07 .n7-note{font-size:11px;color:var(--secondary-text-color);margin:8px 0 0}.nexus07 .n7-warning{color:var(--primary-text-color);border-left:3px solid #bd781b;padding-left:7px}.nexus07 a{color:var(--primary-text-color);font-size:11px;text-decoration:none;display:block;margin-top:10px}
@container(max-width:260px){.nexus07 .n7-row{grid-template-columns:18px minmax(0,1fr)}.nexus07 strong{grid-column:2}}
</style><div class="nexus07"><h2><ha-icon icon="mdi:shield-check"></ha-icon>Sécurité</h2>
${row('Alarmo',ids.alarme,alarm,'mdi:shield-home')}
${row('Porte · contact',ids.porte_entree,door,'mdi:door')}
${row('Porte · Nuki',ids.nuki_porte,door,'mdi:door-closed')}
${row('Serrure',ids.serrure,{locked:'Verrouillée',unlocked:'Déverrouillée',locking:'Verrouillage en cours',unlocking:'Déverrouillage en cours',jammed:'Bloquée',open:'Ouverte',opening:'Ouverture en cours'},'mdi:lock')}
${row('Garage',ids.garage_cover,{open:'Ouvert',closed:'Fermé',opening:'En ouverture',closing:'En fermeture'},'mdi:garage')}
<div class="n7-note">Caméras : ${known}/5 états disponibles · pas une preuve de vidéo</div>
${conflict ? '<div class="n7-note n7-warning">Contacts porte divergents</div>' : ''}
<a href="/ai-nexus-v4/securite">Voir Sécurité ›</a></div>`;
'''
    card['name'] = 'Sécurité statuts uniquement'
    card['custom_fields'] = {'body':'[[[[\n'+js+'\n]]]]'}
    card['triggers_update'] = [v for v in ids.values() if v]
    for action in ('tap_action','hold_action','double_tap_action'):
        card[action] = {'action':'none'}
    card.pop('entity',None)
    card['styles']['card'] = [{'padding':'12px'},{'border-radius':'20px'},{'background':'var(--ha-card-background)'},{'border':'1px solid var(--divider-color)'},{'container-type':'inline-size'},{'overflow':'hidden'}]
    return card


def room_group(rooms):
    result = group('Six pièces illustrées',rooms,'repeat(6,minmax(0,1fr))',title='Pièces principales',tablet=3,mobile=1)
    keys = list(rooms)
    def areas(n):
        rows = ['"'+' '.join(['heading']*n)+'"']
        rows += ['"'+' '.join(keys[i:i+n])+ '"' for i in range(0,len(keys),n)]
        return ' '.join(rows)
    result['styles']['grid'][2] = {'gap':'8px'}
    result['extra_styles'] = ''.join('@container(max-width:'+str(width)+'px){#container{grid-template-columns:repeat('+str(n)+',minmax(0,1fr))!important;grid-template-areas:'+areas(n)+'!important}}' for width,n in [(1199,3),(759,2),(620,1)])
    return result



ROOMS = [('salon','Salon'), ('sam','Salle à manger'), ('entree','Entrée'),
         ('parents','Parents'), ('emile','Émile'), ('maddy','Maddy')]


def improve_climate(cfg, mapping):
    ids = list(dict.fromkeys(mapping[k+'_temp'] for k, _ in ROOMS if mapping.get(k+'_temp')))
    rows = [(name, mapping.get(k+'_temp')) for k, name in ROOMS]
    calc = '''
const climateNumber = id => {
 const e=states[id], raw=e?.state;
 if (!e || e.attributes?.restored || raw == null || String(raw).trim()==='' ||
     e.attributes?.unit_of_measurement!=='°C' || e.attributes?.device_class!=='temperature') return null;
 const n=Number(raw); return Number.isFinite(n)?n:null;
};
const ids=IDS;
const values=ids.map(climateNumber).filter(v=>v!==null);
const mean=values.length?values.reduce((a,b)=>a+b,0)/values.length:null;
const fmt=n=>n===null?'Indisponible':n.toLocaleString('fr-FR',{maximumFractionDigits:1})+' °C';
'''.replace('IDS', json.dumps(ids))
    body = '''<style>.nexus06{display:grid;grid-template-columns:minmax(72px,100px) minmax(0,1fr);gap:10px;align-items:center;min-width:0}.nexus06 .dial{width:min(96px,100%);aspect-ratio:1;height:auto;box-sizing:border-box;min-width:0;border-radius:50%;border:8px solid #51a9bb;text-align:center;display:flex;flex-direction:column;justify-content:center}.nexus06 strong{font-size:clamp(12px,4cqi,22px);overflow-wrap:anywhere;line-height:1.15}.nexus06 .rooms{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;min-width:0}.nexus06 .rooms strong{font-size:13px}@container(max-width:350px){.nexus06{grid-template-columns:1fr}.nexus06 .dial{margin:auto}}</style><div class="panel"><div class="head"><h2>Climat</h2></div><div class="nexus06"><div class="dial"><strong>${fmt(mean)}</strong><small>Moyenne actuelle</small></div><div class="rooms">'''
    for name, eid in rows:
        body += '<div><small>'+name+'</small><strong>${fmt(climateNumber('+json.dumps(eid)+'))}</strong></div>'
    body += '''</div></div><div class="footer">${values.length}/${ids.length} capteurs °C valides · moyenne non pondérée<br>Cuisine et bureau : capteurs dédiés non disponibles<br>Historique réel 24 h : ouvrir Confort ›</div></div>'''
    # One surrounding composite button-card consumes one extra [] pair.
    cfg['custom_fields']['body']='[[[[\n'+calc+'return `'+body+'`;\n]]]]'
    cfg['triggers_update']=ids
    cfg['tap_action']={'action':'navigate','navigation_path':'/ai-nexus-v4/confort'}
    return cfg


def climate_history(mapping):
    """Insert in Confort, not another nested template; no baked snapshot curve."""
    return {'type':'history-graph','title':'Températures réelles · 24 h · °C',
            'hours_to_show':24,'entities':[{'entity':mapping[k+'_temp'],'name':name}
            for k,name in ROOMS if mapping.get(k+'_temp')], 'expand_legend':True}



ROBOTS = [('sami','Sami','vacuum.sami','sensor.sami_batterie','sami.webp'),('navimow','Navimow','lawn_mower.navimow_i206_awd','sensor.navimow_i206_awd_battery','navimow.webp')]

def improve_robots(sami, navimow):
    """Le résumé d'accueil ouvre la vue du robot, où se trouvent les commandes."""
    for cfg, (slug,title,entity,battery,image) in zip((sami,navimow), ROBOTS):
        cfg['tap_action']={'action':'navigate','navigation_path':'/ai-nexus-v4/'+slug}
        cfg['hold_action']={'action':'none'}
        cfg['double_tap_action']={'action':'none'}
        cfg['triggers_update']=[entity,battery]
        battery_expr = 'states['+json.dumps(battery)+']'
        cfg['triggers_update']=[entity,battery]
        cfg['custom_fields']['body']='[[[[\n'+r'''
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
'''+ 'const robot=states['+json.dumps(entity)+']; const battery='+battery_expr+';\n'+r'''
const raw=String(robot?.state??'').trim().toLowerCase();
const missing=!raw||['unknown','unavailable'].includes(raw)||robot?.attributes?.restored;
const labels={docked:'À la base',cleaning:'Nettoyage',mowing:'Tonte',returning:'Retour',paused:'En pause',idle:'Au repos',error:'Erreur'};
const status=missing?'Robot indisponible':(labels[raw]||'État non reconnu');
const bs=String(battery?.state??'').trim(); const n=bs?Number(bs):NaN;
const valid=!missing&&!battery?.attributes?.restored&&battery?.attributes?.unit_of_measurement==='%'&&Number.isFinite(n)&&n>=0&&n<=100;
const bat=valid?n.toLocaleString('fr-FR',{maximumFractionDigits:0})+' %':'Indisponible';
return `<style>.robot{width:100%;min-width:0;text-align:left;white-space:normal;overflow-wrap:anywhere}.robot h2{font-size:16px;margin:0 0 8px}.robot strong{font-size:13px}.robot img{display:block;width:100%;height:78px;object-fit:contain;margin:8px 0}.robot small{display:block;font-size:12px}.robot .note{font-size:10px;opacity:.7;margin-top:7px}@container(max-width:180px){.robot img{height:64px}.robot h2{font-size:14px}}</style>
'''+ '<div class="robot"><h2>'+title+'</h2><strong>${esc(status)}</strong><img src="/local/ai-nexus-v4/visual/'+image+'" alt="Illustration '+title+'"><small>Batterie ${esc(bat)}</small><div class="note">Statut seulement · illustration</div></div>`;\n]]]]'
    return sami,navimow


def build_home(b):
    from collections import defaultdict
    e = defaultdict(lambda: None, b.mapping)
    aliases = {'mode':'mode_maison','alarm':'alarme','lock':'serrure','porte_nuki':'nuki_porte',
               'energie_jour':'conso_jour','pv_power':'solaire_jour','cout_jour':'cout_mois'}
    for person in ('denis','laura','emile','maddy'):
        aliases['bat_'+person] = person+'_bat'
    for room in ('salon','cuisine','bureau','parents','emile','maddy'):
        aliases['light_'+room] = room+'_light'
        aliases['cover_'+room] = room+'_cover'
    for alias, key in aliases.items():
        e[alias] = b.mapping.get(key)
    j = lambda key: json.dumps(e[key])
    people_ids = [e[k] for k in ('denis','laura','emile','maddy')]
    temp_ids = [e[k+'_temp'] for k in ('salon','sam','entree','parents','emile','maddy') if e[k+'_temp']]
    presence_js = "const people=PEOPLE; const knownPresence=id=>ok(id) && get(id)?.attributes?.restored!==true && !['null','undefined','none'].includes(String(get(id).state).trim().toLowerCase()); const known=people.filter(knownPresence); const home=known.filter(id=>get(id).state==='home').length; const unknown=people.length-known.length; const presence=home+' présent'+(home>1?'s':'')+' / '+people.length+(unknown?' · '+unknown+' non renseigné'+(unknown>1?'s':''):'');".replace("PEOPLE", json.dumps(people_ids))
    mean_js = 'const measurements='+json.dumps(temp_ids)+'; const values=measurements.map(number).filter(v=>v!==null); const mean=values.length ? values.reduce((a,b)=>a+b,0)/values.length : null;'
    vigilance_js = "const alarm=get(ALARM)?.state; const mode=get(MODE)?.state; const present=home>0; const securityKnown=ok(ALARM) && ok(MODE) && get(ALARM)?.attributes?.restored!==true && get(MODE)?.attributes?.restored!==true; const vigilance=alarm==='triggered' ? 'Alarme déclenchée' : !securityKnown ? 'Sécurité / mode non disponibles' : present && (String(mode).toLowerCase()==='absent' || alarm==='armed_away') ? 'Présence détectée malgré mode absent / alarme absence' : unknown ? 'Présence partiellement non disponible' : 'Aucune incohérence détectée';".replace("ALARM", j("alarm")).replace("MODE", j("mode"))
    state = lambda key, unit='': '${value(' + j(key) + ',' + json.dumps(unit) + ')}'
    unit = lambda key: '${unitValue(' + j(key) + ')}'
    tr = lambda key, mapping: '${translated(' + j(key) + ',' + json.dumps(mapping, ensure_ascii=False) + ')}'
    metric = lambda title, text, ico='': '<div class="metric">' + ('${icon(' + json.dumps(ico) + ')}' if ico else '') + '<div><small>' + title + '</small><strong>' + text + '</strong></div></div>'
    path = '/ai-nexus-v4/'
    hero_body = '''<style>.hero{min-height:142px;display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:16px}.hero h2{font-size:30px;font-weight:650}.hero .weather{padding:14px 18px;border-radius:18px;background:var(--ha-card-background);min-width:190px}.hero .weather strong{font-size:26px}.hero .date{margin:7px 0 14px;font-size:13px}.hero .tags{display:flex;flex-wrap:wrap;gap:7px}.hero .weather small{margin-top:4px}@container(max-width:480px){.hero{grid-template-columns:1fr;min-height:0}.hero h2{font-size:24px}.hero .weather{display:flex;gap:12px;align-items:center;min-width:0;padding:12px 14px}.hero .weather strong{font-size:22px}.hero .date{font-size:12px}.hero .tags{gap:6px}.pill{font-size:11px;padding:5px 10px}}@container(max-width:600px){.hero{grid-template-columns:1fr;min-height:0}.hero h2{font-size:25px}.hero .weather{display:flex;gap:15px;align-items:center;min-width:0}.hero .weather strong{font-size:22px}}</style>
<div class="panel hero"><div><h2>Bonjour Denis</h2><p class="date">Maison · ${new Date().toLocaleDateString('fr-FR',{weekday:'long',day:'numeric',month:'long',timeZone:'Europe/Paris'})}</p><div class="tags"><span class="pill">${presence} · personnes présentes</span><span class="pill">Mode ''' + state('mode') + '''</span></div></div><div class="weather"><div>${icon('mdi:weather-partly-cloudy')}</div><div><strong>${ok(''' + j('meteo') + ''') && Number.isFinite(Number(get(''' + j('meteo') + ''').attributes.temperature)) ? esc(get(''' + j('meteo') + ''').attributes.temperature) + ' ' + esc(get(''' + j('meteo') + ''').attributes.temperature_unit || '°C') : 'Indisponible'}</strong><small>''' + tr('meteo', {'sunny':'Ensoleillé','partlycloudy':'Quelques nuages','cloudy':'Nuageux','rainy':'Pluie','clear-night':'Nuit claire','pouring':'Forte pluie','fog':'Brouillard','snowy':'Neige'}) + '''</small></div></div></div>'''
    hero = card('Bandeau photographique', hero_body, people_ids+[e[k] for k in ('mode','meteo')], padding='20px 26px')
    hero['styles']['card'] += [{'background': "linear-gradient(90deg,var(--ha-card-background) 8%,var(--ha-card-background) 40%,transparent 100%), url('" + PREFIX + "hero.webp') center/cover"}]
    # A four-section span exposes 48 native columns: 12 is only one quarter.
    # 'full' follows the effective section width, including mobile clamping.
    hero['section_mode'] = True
    hero['grid_options'] = {'columns': 'full', 'rows': 'auto'}
    from hero_design import improve_hero
    hero = improve_hero(hero, people_ids, e['mode'], e['meteo'])

    family_entities = []
    people = ''
    for person, name, battery, ico in [('denis','Denis','bat_denis','mdi:account'),('laura','Laura','bat_laura','mdi:account'),('emile','Émile','bat_emile','mdi:account-school'),('maddy','Maddy','bat_maddy','mdi:account-school')]:
        wifi, network, mobile = (person + '_' + suffix for suffix in ('wifi','network','mobile'))
        family_entities += [e[person], e[battery], e[wifi], e[network], e[mobile]]
        people += ('<div class="person">${icon(' + json.dumps(ico) + ')}<div><h3>' + name + '</h3><small class="presence">' + tr(person, {'home':'À la maison','not_home':'Absent'}) + '</small>'
                   + '${connection(' + j(wifi) + ',' + j(network) + ',' + j(mobile) + ')}'
                   + '${batteryDetail(' + j(battery) + ')}' + '</div></div>')
    family_body = '<style>.people{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.person{display:flex;align-items:center;gap:10px;min-width:0}.person>ha-icon{border-radius:50%;padding:8px;width:44px;height:44px;color:#3d8dae;background:rgba(89,159,190,.14);flex-shrink:0}.person>div{min-width:0;overflow-wrap:anywhere}.person small{margin-top:4px}.person .person-detail{display:flex;align-items:center;gap:5px;line-height:1.35}.person-detail>ha-icon{width:15px;height:15px;--mdc-icon-size:15px;flex-shrink:0;color:#478fae}.person-detail>span{min-width:0;white-space:normal}.person .battery{color:#53765b}@container(max-width:600px){.people{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 10px}.person>ha-icon{width:34px;height:34px;padding:5px}.person{gap:8px}.person h3{font-size:14px}.person small{font-size:11px}}@container(max-width:320px){.people{grid-template-columns:1fr;gap:12px}.person>ha-icon{width:40px;height:40px;padding:7px}.person small{font-size:12px}}</style><div class="panel">' + head('Famille','mdi:account-group') + '<div class="people">' + people + '</div></div>'
    family = card('Famille regroupée', family_body, family_entities, path+'plus')
    family['custom_fields']['body'] = family['custom_fields']['body'].replace('\nreturn `', '\n' + FAMILY_HELPERS + '\nreturn `', 1)
    # Un niveau de button-card parent : éviter son évaluation anticipée.
    # Les capteurs sont suivis par la carte enfant, qui doit rester réactive.
    family['custom_fields']['body'] = '[' + family['custom_fields']['body'] + ']'
    vigilance = card('Vigilance', '<div class="panel">' + head('Maison & vigilance','mdi:shield-home') + '<div class="metrics">' + metric('Présence', '${presence}') + metric('Mode',state('mode')) + metric('Alarme',tr('alarm', {'disarmed':'Désarmée','armed_home':'Présence','armed_away':'Absence','triggered':'Déclenchée'})) + metric('Vigilance','${vigilance}') + '</div></div>', people_ids+[e[k] for k in ('mode','alarm')],path+'securite')

    rooms = {}
    # Aucun emprunt des mesures salon pour cuisine/bureau.
    room_css = '<style>.room .photo{height:85px;border-radius:15px 15px 0 0;object-position:center}.room .room-info{padding:8px 10px}.room .head{margin-bottom:6px;gap:6px}.room .head h2{font-size:15px}.room .metrics{grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.room .metric small{font-size:12px}.room .metric strong{font-size:13px}.room .coverline{font-size:12px;margin-top:6px;line-height:1.35}.room .footer{font-size:12px;margin-top:6px}.room .missing{font-size:12px;line-height:1.4}.room .head .arrow{font-size:20px}</style>'
    for slug, title, icon_name in [('salon','Salon','mdi:sofa'),('cuisine','Cuisine','mdi:chef-hat'),('bureau','Bureau','mdi:desk'),('parents','Parents','mdi:bed-king'),('emile','Émile','mdi:bed'),('maddy','Maddy','mdi:bed')]:
        temp, hum, light, cover = (slug+'_temp',slug+'_hum','light_'+slug,'cover_'+slug)
        measured = slug not in ('cuisine','bureau')
        body = room_css + '<div class="panel room"><img class="photo" src="' + PREFIX + slug + '.webp" alt="Illustration de maquette : ' + title + '"><div class="room-info">' + head(title,icon_name)
        ids = [e[light]]
        if measured:
            body += '<div class="metrics">' + metric('Température',unit(temp),'mdi:thermometer') + metric('Humidité',unit(hum),'mdi:water-percent') + '</div>'
            ids += [e[temp],e[hum]]
        else:
            body += '<div class="missing">Température / humidité : capteur dédié non disponible</div>'
        body += '<div class="coverline">Éclairage : ' + tr(light, {'on':'allumé','off':'éteint'})
        if e[cover]:
            ids.append(e[cover])
            body += ' · Volet : ' + tr(cover, {'open':'ouvert','closed':'fermé','opening':'en ouverture','closing':'en fermeture'})
        body += '</div><div class="footer">Ouvrir la pièce ›</div></div></div>'
        rooms[slug] = card(title+' photographique',body,ids,'#piece-'+slug,padding='0')
        # Repli local explicite pour états invalides/restaurés, sans changer HELPERS global.
        rooms[slug]['custom_fields']['body'] = rooms[slug]['custom_fields']['body'].replace("!['unknown','unavailable',''].includes(get(id).state)", "!get(id).attributes?.restored && !['unknown','unavailable','','none','null','restored'].includes(String(get(id).state).trim().toLowerCase())")
        # Parent composite : évaluation et réactivité chez l'enfant.
        rooms[slug]['custom_fields']['body'] = '[' + rooms[slug]['custom_fields']['body'] + ']'

    climate_body = '<style>.climate{display:grid;grid-template-columns:minmax(72px,120px) minmax(0,1fr);gap:14px;align-items:center;min-width:0;container-type:inline-size}.climate-list{min-width:0}.dial{width:min(118px,100%);aspect-ratio:1;height:auto;box-sizing:border-box;min-width:0;border-radius:50%;display:grid;place-items:center;background:conic-gradient(from 210deg,#40b8af 0deg,#479ee1 var(--angle),rgba(90,145,178,.15) var(--angle) 300deg,transparent 300deg);padding:9px}.dial-inner{border-radius:50%;width:100%;height:100%;box-sizing:border-box;min-width:0;padding:0 4px;background:var(--ha-card-background);display:flex;flex-direction:column;justify-content:center;text-align:center}.dial strong{font-size:clamp(13px,4.5cqi,23px);overflow-wrap:anywhere;line-height:1.15}.climate-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;min-width:0}@container(max-width:400px){.climate{grid-template-columns:1fr}.climate-list{grid-template-columns:repeat(2,minmax(0,1fr))}.dial{width:98px;height:98px}.dial strong{font-size:clamp(12px,4cqi,20px)}}</style><div class="panel">' + head('Climat','mdi:home-thermometer') + '<div class="climate"><div class="dial" style="--angle:${mean === null ? 0 : Math.max(0,Math.min(300,mean/40*300))}deg"><div class="dial-inner"><strong>' + '${mean === null ? \'Indisponible\' : mean.toLocaleString(\'fr-FR\',{maximumFractionDigits:1})+\' °C\'}' + '</strong><small>Maison</small></div></div><div class="climate-list">' + ''.join(metric(title,unit(k)) for title,k in [('Salon','salon_temp'),('Cuisine','cuisine_temp'),('Bureau','bureau_temp'),('Parents','parents_temp'),('Émile','emile_temp'),('Maddy','maddy_temp')]) + '</div></div><div class="footer">Températures de la maison</div></div>'
    climate = card('Climat compact avec jauge',climate_body,temp_ids+[e[k] for k in ('salon_temp','cuisine_temp','bureau_temp','parents_temp','emile_temp','maddy_temp')],path+'confort')
    security = card('Sécurité compacte','<div class="panel">' + head('Sécurité','mdi:shield-check') + '<div class="metrics">' + metric('Alarme',tr('alarm', {'disarmed':'Désarmée','armed_home':'Présence','armed_away':'Absence','triggered':'Déclenchée'}),'mdi:shield-home') + metric('Porte d’entrée',tr('porte_nuki',{'on':'Ouverte','off':'Fermée'}),'mdi:door') + metric('Serrure',tr('lock',{'locked':'Verrouillée','unlocked':'Déverrouillée'}),'mdi:lock') + metric('Garage',tr('garage_cover',{'open':'Ouvert','closed':'Fermé'}),'mdi:garage') + '</div><div class="footer">Ouvrir sécurité et caméras ›</div></div>',[e[k] for k in ('alarm','porte_nuki','lock','garage_cover')],path+'securite')
    sami = card('Sami illustré','<div class="panel">'+head('Sami','mdi:robot-vacuum')+'<strong>'+tr('sami',{'docked':'À la base','cleaning':'Nettoyage','returning':'Retour','paused':'En pause','idle':'Au repos','error':'Erreur'})+'</strong><img class="product" src="'+PREFIX+'sami.webp" alt="Robot aspirateur illustratif"><small>Batterie ${ok('+j('sami')+') && Number.isFinite(Number(get('+j('sami')+').attributes.battery_level)) ? esc(get('+j('sami')+').attributes.battery_level)+" %" : "Indisponible"}</small><div class="footer">Détails du robot ›</div></div>',[e['sami']],path+'sami')
    navimow = card('Navimow i206 AWD visuel','<div class="panel">'+head('Navimow','mdi:robot-mower')+'<strong>'+tr('navimow',{'docked':'À la base','mowing':'Tonte','returning':'Retour','paused':'En pause','idle':'Au repos','error':'Erreur'})+'</strong><img class="product" style="height:90px" src="'+PREFIX+'navimow.webp" alt="Visuel constructeur Segway Navimow i2 AWD"><small>Batterie '+state('navimow_bat','%')+'</small>${progress('+j('navimow_bat')+')}<div class="footer">Segway · i206 AWD · détails ›</div></div>',[e['navimow'],e['navimow_bat']],path+'navimow')

    # Energie : 8 metriques reelles issues du mapping existant. Les cles de
    # mapping sont utilisees directement (plus les alias ambigus 'pv_power',
    # 'energie_jour', 'cout_jour') pour que chaque libelle annonce exactement
    # la grandeur qu'il affiche : jour vs mois, maison vs vehicule.
    energy = card('Énergie compacte','<div class="panel">'+head('Énergie','mdi:flash')+'<div class="metrics">'+metric('Puissance maison',unit('puissance'),'mdi:home-lightning-bolt')+metric('Tarif en cours',tr('tarif',{'HEURE CREUSE':'Heures creuses','HEURE PLEINE':'Heures pleines','HP':'Heures pleines','HC':'Heures creuses'}),'mdi:clock-time')+metric('Énergie du jour',unit('conso_jour'),'mdi:counter')+metric('Énergie du mois',unit('conso_mois'),'mdi:calendar-month')+metric('Solaire du jour',unit('solaire_jour'),'mdi:solar-power')+metric('Solaire cumulé',unit('solaire_total'),'mdi:solar-power-variant')+metric('Coût du mois',unit('cout_mois'),'mdi:currency-eur')+metric('Recharge VE',unit('phev_cout_mois'),'mdi:ev-station')+'</div><div class="footer">Ouvrir Énergie ›</div></div>',[e[k] for k in ('puissance','tarif','conso_jour','conso_mois','solaire_jour','solaire_total','cout_mois','phev_cout_mois')],path+'energie')
    sportage = card('Sportage photographique','<div class="panel">'+head('Sportage','mdi:car-electric')+'<img class="product" style="height:auto;aspect-ratio:176/83;max-height:150px;object-fit:contain;object-position:center" src="'+PREFIX+'sportage-full.webp" alt="SUV Sportage illustratif, véhicule entier"><div class="metrics">'+metric('Batterie EV',state('ev_level','%'))+metric('Autonomie EV',unit('ev_range'))+metric('Carburant',state('fuel_level','%'))+metric('Autonomie carburant',unit('fuel_range'))+'</div><div class="footer">Détails du véhicule ›</div></div>',[e[k] for k in ('ev_level','ev_range','fuel_level','fuel_range')],path+'voiture')
    sportage['custom_fields']['body'] = '[' + sportage['custom_fields']['body'] + ']'
    improve_robots(sami, navimow)
    media = card('Multimédia compact','<div class="panel">'+head('Multimédia','mdi:music')+'<div class="metrics">'+metric('Salon',tr('tv_salon',{'off':'Éteint','idle':'Au repos','playing':'Lecture','paused':'Pause'}),'mdi:television')+metric('Sound Bar',tr('soundbar',{'off':'Éteinte','idle':'Au repos','playing':'Lecture','paused':'Pause'}),'mdi:speaker')+'</div><p style="margin-top:14px;font-size:13px">${esc(get('+j('tv_salon')+')?.attributes?.media_title || get('+j('soundbar')+')?.attributes?.media_title || "Aucun titre communiqué")}</p><div class="footer">Ouvrir les lecteurs ›</div></div>',[e['tv_salon'],e['soundbar']],path+'multimedia')
    # Liens HTML ordinaires : aucun bouton apparent déclenchant une action physique.
    quick_links = [('Pièces',path+'pieces','mdi:floor-plan'),('Confort',path+'confort','mdi:thermometer'),('Sécurité',path+'securite','mdi:shield-home'),('Équipements',path+'equipements','mdi:devices')]
    quick_body = '<style>.shortcuts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.shortcuts a{text-decoration:none;color:var(--primary-text-color);background:rgba(62,140,188,.10);border-radius:12px;padding:10px 5px;text-align:center;font-size:11px}.shortcuts ha-icon{display:block;margin:0 auto 5px;color:#388caf}</style><div class="panel">'+head('Accès rapides','mdi:view-grid')+'<div class="shortcuts">'+''.join('<a href="'+link+'">${icon('+json.dumps(ico)+')}'+title+'</a>' for title,link,ico in quick_links)+'</div><div class="footer">Explorer la maison</div></div>'
    quick = card('Accès rapides navigation',quick_body,[])
    panels = [hero, group('Famille et vigilance',{'family':family,'vigilance':vigilance},'minmax(0,911fr) minmax(0,562fr)',tablet=1),
              room_group(rooms),
              group('Climat sécurité et robots',{'climate':climate,'security':security,'sami':sami,'navimow':navimow},'minmax(0,4fr) minmax(0,4fr) minmax(0,2fr) minmax(0,2fr)',tablet=2),
              group('Énergie véhicule multimédia accès',{'energy':energy,'sportage':sportage,'media':media,'quick':quick},'minmax(0,4fr) minmax(0,3fr) minmax(0,3fr) minmax(0,2fr)',tablet=2)]
    for target, calculations in ((vigilance,presence_js+vigilance_js),(climate,mean_js)):
        target['custom_fields']['body'] = target['custom_fields']['body'].replace('\nreturn `', '\n'+calculations+'\nreturn `',1)
    vigilance['name'] = 'Vigilance maison'
    vigilance['label'] = '[[[\n'+HELPERS+presence_js+vigilance_js+'\nreturn vigilance;\n]]]'
    vigilance['show_label'] = False
    # Chaque template dynamique de cette carte enfant attend son propre hass.
    vigilance['custom_fields']['body'] = '[' + vigilance['custom_fields']['body'] + ']'
    vigilance['label'] = '[' + vigilance['label'] + ']'
    # Les composites parent ne dépendent pas d'un état et ne doivent pas hériter
    # de la grille limitée des autres vues. Les pop-ups existants sont ajoutés
    # par Builder, une seule fois, et gardent leurs protections de commandes.
    improve_climate(climate, b.mapping)
    improve_security(security, b.mapping)
    return panels
