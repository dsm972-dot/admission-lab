"""Proposition mission 03 : bandeau isolé, prévisions natives sans service."""
import json


def improve_hero(hero, people_ids, mode_id, weather_id):
    """Ne modifie que la carte hero reçue ; routes et autres cartes inchangées."""
    from copy import deepcopy
    result = deepcopy(hero)
    ids = [i for i in people_ids if i]
    js = r'''
const esc = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const usable = s => s && !['unknown','unavailable',''].includes(s.state);
const people = PEOPLE;
const known = people.filter(id=>usable(states[id]));
const count = known.filter(id=>states[id].state==='home').length;
const presence = known.length===people.length && people.length ? `${count}/${people.length} présents` : `${count} présence(s) confirmée(s) · ${people.length-known.length} non renseignée(s)`;
const mode = states[MODE];
const wx = states[WEATHER];
const raw = wx?.attributes?.temperature;
const numeric = raw !== null && raw !== undefined && String(raw).trim() !== '' && Number.isFinite(Number(raw));
const unit = wx?.attributes?.temperature_unit;
const temperature = usable(wx) && numeric && unit ? `${Number(raw).toLocaleString('fr-FR')} ${esc(unit)}` : 'Température indisponible';
const names = {sunny:'Ensoleillé',partlycloudy:'Quelques nuages',cloudy:'Nuageux',rainy:'Pluie','clear-night':'Nuit claire',pouring:'Forte pluie',fog:'Brouillard',snowy:'Neige','snowy-rainy':'Pluie et neige',lightning:'Orage','lightning-rainy':'Pluie orageuse',windy:'Vent','windy-variant':'Vent et nuages',exceptional:'Conditions exceptionnelles',hail:'Grêle'};
const condition = usable(wx) ? names[wx.state] || esc(wx.state) : 'Météo indisponible';
const date = new Date().toLocaleDateString('fr-FR',{weekday:'long',day:'numeric',month:'long',timeZone:(typeof hass !== 'undefined' && hass?.config?.time_zone) || 'Europe/Paris'});
return `<style>
.nexus03{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:center;text-align:left;min-width:0;color:var(--primary-text-color);overflow-wrap:anywhere}
.nexus03 h2{margin:0;font-size:clamp(24px,2.7cqi,40px);line-height:1.1}.nexus03 p{margin:6px 0;font-size:13px}.nexus03 .chips{display:flex;flex-wrap:wrap;gap:6px}.nexus03 .chip{border-radius:16px;padding:5px 9px;background:rgba(90,160,180,.13);font-size:12px}.nexus03 .current{text-align:right;min-width:0}.nexus03 strong{font-size:24px}.nexus03 small{display:block;font-size:12px}
@container(max-width:650px){.nexus03{grid-template-columns:1fr}.nexus03 .current{text-align:left}.nexus03 h2{font-size:24px}}
</style><div class="nexus03"><div><h2>Bonjour Denis</h2><p>${esc(date)}</p><div class="chips"><span class="chip">${presence}</span><span class="chip">Mode ${usable(mode)?esc(mode.state):'indisponible'}</span></div></div><div class="current"><strong>${temperature}</strong><small>${condition}</small><small>Prévisions HA : si absentes, données indisponibles.</small></div></div>`;
'''
    js = js.replace('PEOPLE', json.dumps(ids)).replace('MODE', json.dumps(mode_id)).replace('WEATHER', json.dumps(weather_id))
    result['custom_fields'] = {
        'body': '[[[\n' + js + '\n]]]',
        'forecast': {'card': {'type': 'weather-forecast', 'entity': weather_id,
                             'show_current': False, 'show_forecast': True,
                             'forecast_type': 'daily',
                             'tap_action': {'action': 'more-info'}}},
    }
    result['triggers_update'] = list(dict.fromkeys(ids + [mode_id, weather_id]))
    # Ne pas fixer update_timer : en v7 il remplace les mises à jour événementielles.
    result.pop('update_timer', None)
    result['styles']['card'] = [item for item in result['styles']['card'] if 'padding' not in item] + [{'padding': '12px 16px'}]
    result['styles']['grid'] = [{'grid-template-areas': '"body forecast"'}, {'grid-template-columns': 'minmax(0,1fr) minmax(280px,360px)'}, {'gap': '12px'}, {'align-items': 'center'}]
    result['styles']['custom_fields'] = {key: [{'width': '100%'}, {'min-width': '0'}, {'white-space': 'normal'}] for key in ('body','forecast')}
    result['extra_styles'] = '@container(max-width:760px){#container{grid-template-columns:minmax(0,1fr)!important;grid-template-areas:"body" "forecast"!important}}'
    result['section_mode'] = True
    result['grid_options'] = {'columns': 'full', 'rows': 'auto'}
    return result
