#!/usr/bin/env python3
"""Construit data/entities_map.json : slots logiques -> entity_id reels, verifies
contre data/entities_index.json (dump live). Aucune supposition : tout slot non
resolu est signale MISSING et doit etre corrige avant deploiement."""
import json, re, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = json.load(open(os.path.join(BASE, "data/entities_index.json")))
# Tolérance de schéma : l'index a déjà contenu 19 entrées brutes /api/states
# mêlées au format compact {eid,...}, ce qui faisait planter ce script (KeyError).
IDS = set()
for e in IDX:
    eid = e.get("eid") or e.get("entity_id")
    if not eid:
        raise SystemExit("index invalide : entrée sans eid ni entity_id — relancer tools/dump_live.py")
    IDS.add(eid)

# slot -> liste de candidats (id exact ou regex), dans l'ordre de priorite
SLOTS = {
    # --- global / accueil
    "meteo":            ["weather.forecast_maison", "weather.orgeres"],
    "mode_maison":      ["input_select.house_mode"],
    "alarme":           ["alarm_control_panel.master"],
    "alarme_rdc":       ["alarm_control_panel.rdc"],
    "alarme_etage":     ["alarm_control_panel.etage"],
    "porte_entree":     ["binary_sensor.capteur_ouverture_porte_entree_contact"],
    "nuki_porte":       ["binary_sensor.porte_entree_nuki_proxy"],
    "serrure":          ["lock.nuki_porte_d_entree_principale_lock"],
    # --- energie
    "conso_jour":       ["sensor.conso_maison_jour"],
    "conso_mois":       ["sensor.conso_maison_mois"],
    "puissance":        ["sensor.linky_puissance_watts"],
    "cout_mois":        ["sensor.cout_total_mois_hp_hc"],
    "tarif":            ["sensor.linky_tarif_actuel"],
    "solaire_total":    [r"sensor\.garage_production_electricite.*solaire"],
    "solaire_jour":     ["sensor.ene01_pv_day_kwh", r"sensor\..*pv_day_kwh"],
    "phev_cout_mois":   ["sensor.rv3_mois_eur", "sensor.cout_phev_mois"],
    "phev_conso_jour":  ["sensor.rv3_jour_kwh", "sensor.conso_phev_jour"],
    # --- pieces : (temp, humidite, lumiere, volet)
    "salon_temp":       ["sensor.salon_temperature_2"],
    "salon_hum":        ["sensor.salon_humidite_2"],
    # salon_projecteur : éclairage de pièce. salon_led_d_etat est un voyant, pas une lampe.
    "salon_light":      ["light.salon_projecteur"],
    "salon_cover":      ["cover.salon_grand_volet_salon"],
    "sam_temp":         ["sensor.salle_a_manger_temperature_2"],
    "sam_hum":          ["sensor.salle_a_manger_humidite_2"],
    "sam_cover":        ["cover.p_v_salon_rideau"],
    "cuisine_temp":     [r"sensor\.cuisine_temperature", "sensor.salon_temperature_2"],
    "cuisine_hum":      [r"sensor\.cuisine_humidite", "sensor.salon_humidite_2"],
    "cuisine_light":    ["light.ampoule_cuisine"],
    "cuisine_cover":    ["cover.volet_cuisine_etat"],
    "entree_temp":      ["sensor.entree_temperature_2"],
    "entree_hum":       ["sensor.entree_humidite_2"],
    "entree_light":     ["light.ez_entree_lumiere", "light.entree_reo_entree_projecteur"],
    "bureau_light":     ["switch.interrupteur_bureau"],
    "bureau_ambilight": ["light.lumiere_bureau_ambilight"],
    "bureau_cover":     ["cover.volet_bureau"],
    "bureau_switch":    ["switch.interrupteur_bureau"],
    "bureau_camera":    ["camera.reo_bureau"],
    "bureau_script":    ["script.bureau_v2_commande"],
    "bureau_contexte":  ["sensor.bureau_contexte_pc"],
    "bureau_presence":  ["sensor.bureau_probabilite_presence"],
    "bureau_lux":       ["sensor.bureau_v2_lux_echantillon", "sensor.bureau_luminosite_retour"],
    "bureau_duree":     ["sensor.bureau_duree_allumage"],
    "parents_temp":     ["sensor.chambre_parentale_temperature_2"],
    "parents_hum":      ["sensor.chambre_parentale_humidite_2"],
    "parents_light":    ["light.ampoule_chambre_parentale_1"],
    "parents_light2":   ["light.bande_led_parents"],
    "parents_cover":    ["cover.volet_parent"],
    "emile_temp":       ["sensor.chambre_emile_temperature_2"],
    "emile_hum":        ["sensor.chambre_emile_humidite_2"],
    "emile_light":      ["light.ampoule_emile"],
    "emile_cover":      ["cover.volet_emile_etat"],
    "emile_fenetre":    ["binary_sensor.chambre_emile_fenetre_2"],
    "maddy_temp":       ["sensor.chambre_maddy_temperature_2"],
    "maddy_hum":        ["sensor.chambre_maddy_humidite_2"],
    "maddy_light":      ["light.ampoule_maddy"],
    "maddy_cover":      ["cover.volet_maddy_etat"],
    "maddy_fenetre":    ["binary_sensor.chambre_maddy_fenetre_2"],
    # --- famille
    "denis":            ["person.denis"],
    "denis_bat":        ["sensor.s25_denis_battery_level"],
    "denis_conf":       ["binary_sensor.presence_denis_confirmee"],
    "laura":            ["person.laura"],
    "laura_bat":        ["sensor.laura_battery_level"],
    "laura_conf":       ["binary_sensor.presence_laura_confirmee"],
    "emile":            ["person.emile"],
    "emile_bat":        ["sensor.emile_battery_level"],
    "emile_conf":       ["binary_sensor.presence_emile_confirmee"],
    "maddy":            ["person.maddy"],
    "maddy_bat":        ["sensor.tel_maddy_battery_level"],
    "maddy_conf":       ["binary_sensor.presence_maddy_confirmee"],
    # Connexion exacte du téléphone (person.* reste la source de présence).
    "denis_wifi":       ["sensor.s25_denis_wi_fi_connection"],
    "denis_network":    ["sensor.s25_denis_network_type"],
    "denis_mobile":     ["sensor.s25_denis_data_network_type_sim_1"],
    "laura_wifi":       ["sensor.laura_wifi_connection"],
    "laura_network":    ["sensor.laura_network_type"],
    "laura_mobile":     ["sensor.laura_data_network_type_sim_1"],
    "emile_wifi":       ["sensor.emile_wi_fi_connection"],
    "maddy_wifi":       ["sensor.tel_maddy_wi_fi_connection"],
    # --- securite / cameras
    "cam_entree":       ["camera.reo_entree"],
    "cam_entree_flu":   ["camera.entree_reo_entree_fluide_lentille_0"],
    "cam_jardin":       ["camera.reo_jardin"],
    "cam_garage":       ["camera.reo_garage"],
    "cam_cuisine":      ["camera.reo_ar_cuisine"],
    "cam_doorbell":     ["camera.reo_doorbell"],
    "garage_cover":     ["cover.porte_de_garage"],
    "porte_garage_sensor": [r"binary_sensor\..*porte.*garage.*contact"],
    "fenetre_cuisine":  [r"binary_sensor\..*fenetre_cuisine_contact"],
    "porte_salon_jardin": [r"binary_sensor\..*porte_salon_jardin_contact"],
    "porte_bureau":     [r"binary_sensor\..*porte_bureau_contact"],
    # --- entretien / jardin
    "sami":             ["vacuum.sami"],
    "navimow":          ["lawn_mower.navimow_i206_awd"],
    "navimow_bat":      ["sensor.navimow_i206_awd_battery"],
    "navimow_dock":     ["binary_sensor.navimow_i206_awd_docked"],
    "navimow_online":   ["binary_sensor.navimow_i206_awd_online"],
    "plante_sol":       ["sensor.sonde_plante_soil_moisture", r"sensor\.sonde_plante_(moisture|humidite)"],
    "plante_temp":      ["sensor.sonde_plante_temperature"],
    "plante_bat":       ["sensor.sonde_plante_battery"],
    "plante_dry":       ["binary_sensor.sonde_plante_dry"],
    # --- vehicule
    "ev_level":         ["sensor.sportage_ev_battery_level"],
    "ev_range":         ["sensor.sportage_ev_range"],
    "ev_charge":        ["binary_sensor.sportage_ev_battery_charge"],
    "ev_plug":          ["binary_sensor.sportage_ev_battery_plug"],
    "fuel_level":       ["sensor.sportage_fuel_level"],
    "fuel_range":       ["sensor.sportage_fuel_driving_range"],
    "odo":              ["sensor.sportage_odometer"],
    "car_bat":          ["sensor.sportage_car_battery_level"],
    "rv3_statut":       ["sensor.rv3_statut"],
    "rv3_jour":         ["sensor.rv3_jour_eur"],
    "rv3_semaine":      ["sensor.rv3_semaine_eur"],
    "rv3_mois":         ["sensor.rv3_mois_eur"],
    "rv3_budget":       ["input_number.rv3_budget_mensuel"],
    # --- media / bureau
    "tv_salon":         ["media_player.shield_4", "media_player.shield"],
    "soundbar":         ["media_player.sound_bar_lg"],
    "mp_bureau":        ["media_player.home_bureau_ha", "media_player.bureau_3"],
    "mp_sam":           ["media_player.salle_a_manger_2"],
    "freebox":          ["media_player.freebox_player"],
    # --- cafe / lecture / ecole
    "cafe_etat":        ["sensor.primadonna_elite_experience_etat_de_l_appareil"],
    "cafe_boisson":     ["select.primadonna_elite_experience_boisson"],
    "cafe_profil":      ["select.primadonna_elite_experience_profil"],
    "cafe_temp":        ["select.primadonna_elite_experience_temperature_de_l_eau"],
    "cafe_allumer":     ["button.primadonna_elite_experience_allumer"],
    "cafe_detartrage":  ["binary_sensor.primadonna_elite_experience_detartrage"],
    "zen_mode":         ["input_boolean.lecture_zen_mode_nuit"],
    "zen_notif":        ["input_boolean.lecture_zen_notifications"],
    "zen_bouton":       ["input_button.bouton_lecture_zen"],
    "zen_extend":       ["script.lecture_zen_extend_now"],
    "zen_remaining":    ["timer.lecture_zen_timer", "sensor.lecture_zen_timer_remaining_min"],
    "zen_eteindre":     ["script.lecture_zen_eteindre_en_douceur"],
    "zen_light":        ["light.ampoule_chambre_parentale_1"],
    "ecole":            ["binary_sensor.ecole"],
    "bus_emile":        ["sensor.emile_bus_info"],
    "bus_maddy":        ["sensor.maddy_bus_info"],
    "vacances_b":       ["calendar.vacances_zone_b"],
}

def resolve(slot, cands):
    for c in cands:
        if re.fullmatch(r"[a-z_]+\.[a-z0-9_]+", c) and c in IDS:
            return c, "exact"
    for c in cands:
        if c in IDS:
            return c, "exact"
    for c in cands:
        rx = re.compile(c)
        hit = sorted(i for i in IDS if rx.search(i))
        if hit:
            return hit[0], "regex"
    return None, "MISSING"

out, missing = {}, []
for slot, cands in SLOTS.items():
    eid, how = resolve(slot, cands)
    out[slot] = eid
    if eid is None:
        missing.append(slot)
    print("%-20s %-8s %s" % (slot, how, eid))

json.dump(out, open(os.path.join(BASE, "data/entities_map.json"), "w"), indent=1, ensure_ascii=False)
print("\n%d slots, %d resolus, %d MISSING" % (len(SLOTS), len(SLOTS) - len(missing), len(missing)))
if missing:
    print("MISSING: " + ", ".join(missing))
    sys.exit(1)
print("-> data/entities_map.json OK")
