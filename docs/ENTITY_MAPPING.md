# Mapping réellement utilisé

Source : `data/states.json`. Les états sont un instantané, pas une preuve de disponibilité actuelle.

Alias exclus : cuisine_temp et cuisine_hum (capteurs du salon). Aucun capteur de température bureau ajouté.

| Entité | Libellés / usage | État lors de la capture |
|---|---|---|
| alarm_control_panel.master | Alarme, Alarmo | armed_home |
| binary_sensor.capteur_ouverture_fenetre_cuisine_contact | Fenêtre cuisine | off |
| binary_sensor.capteur_ouverture_porte_entree_contact | Contact porte d’entrée | on |
| binary_sensor.capteur_ouverture_porte_salon_jardin_contact | Porte jardin | off |
| binary_sensor.navimow_i206_awd_docked | Station | off |
| binary_sensor.primadonna_elite_experience_detartrage | Détartrage | on |
| binary_sensor.sonde_plante_dry | Besoin d’eau | off |
| binary_sensor.sportage_ev_battery_charge | Charge en cours | off |
| binary_sensor.sportage_ev_battery_plug | Branchement, Câble branché | off |
| camera.reo_bureau | Caméra à la demande, Caméra — ouvrir à la demande | streaming |
| camera.reo_doorbell | Sonnette | recording |
| camera.reo_entree | Entrée | recording |
| camera.reo_garage | Garage | recording |
| camera.reo_jardin | Jardin | recording |
| climate.chambre_emile_2 | Chambre Emile | heat |
| climate.chambre_maddy_2 | chambre Maddy | heat |
| climate.chambre_parentale_2 | Chambre parentale | heat |
| climate.entree_2 | Entrée | heat |
| climate.salle_a_manger_2 | Salle à manger | heat |
| climate.salon_2 | salon | heat |
| cover.porte_de_garage | Garage, Maintenir : fermer le garage, Maintenir : ouvrir le garage | closed |
| cover.salon_grand_volet_salon | Maintenir : fermer le volet, Maintenir : ouvrir le volet, Volet | open |
| cover.volet_bureau | Maintenir : fermer le volet, Maintenir : ouvrir le volet, Volet | open |
| cover.volet_de_la_chambre_de_emile_rideau | Maintenir : fermer le volet, Maintenir : ouvrir le volet, Volet | unknown |
| cover.volet_de_la_chambre_de_maddy_rideau | Maintenir : fermer le volet, Maintenir : ouvrir le volet, Volet | unavailable |
| cover.volet_de_la_cuisine_rideau | Maintenir : fermer le volet, Maintenir : ouvrir le volet, Volet | unknown |
| cover.volet_parent | Maintenir : fermer le volet, Maintenir : ouvrir le volet, Volet | open |
| input_boolean.lecture_zen_mode_nuit | Mode nuit | on |
| input_boolean.lecture_zen_notifications | Notifications | on |
| input_button.bouton_lecture_zen | Maintenir : démarrer la lecture | 2026-08-29T21:26:25.744158+00:00 |
| input_number.rv3_budget_mensuel | Budget mensuel | 0.0 |
| input_select.house_mode | Mode maison | Absent |
| lawn_mower.navimow_i206_awd | Navimow, Tondeuse | paused |
| light.ampoule_chambre_parentale_1 | Lampe de lecture | off |
| light.ampoule_cuisine | Éclairage secondaire | unavailable |
| light.chambre_emile | Éclairage, Émile | unavailable |
| light.chambre_maddy | Maddy, Éclairage | unavailable |
| light.chambre_parentale | Parents, Éclairage | unavailable |
| light.cuisine | Cuisine, Éclairage | unavailable |
| light.lumiere_bureau | Bureau, Éclairage | unavailable |
| light.lumiere_bureau_ambilight | Ambiance | unavailable |
| light.lumiere_du_salon | Salon, Éclairage | unavailable |
| lock.nuki_porte_d_entree_principale_lock | Maintenir : déverrouiller la porte, Porte d’entrée | unlocked |
| media_player.bureau_3 | Template ou carte héritée | paused |
| media_player.home_bureau_ha | Bureau | idle |
| media_player.home_salle_de_bain_3 | Template ou carte héritée | idle |
| media_player.meghann | Template ou carte héritée | unavailable |
| media_player.salle_a_manger_2 | Salle à manger | unavailable |
| media_player.shield_4 | Multimédia, Télévision | paused |
| media_player.sound_bar_5 | Template ou carte héritée | unavailable |
| media_player.sound_bar_lg | Barre de son | on |
| person.denis | Denis | home |
| person.emile | Émile | home |
| person.laura | Laura | not_home |
| person.maddy | Maddy | not_home |
| script.lecture_zen_eteindre_en_douceur | Maintenir : éteindre en douceur | off |
| script.lecture_zen_extend_now | Maintenir : prolonger la lecture | off |
| select.primadonna_elite_experience_boisson | Boisson | none |
| select.primadonna_elite_experience_profil | Profil | Profile 1 |
| select.primadonna_elite_experience_temperature_de_l_eau | Température de l’eau | Highest |
| sensor.bureau_contexte_pc | Activité PC, Activité du bureau | intensif |
| sensor.bureau_duree_allumage | Durée d’éclairage | 0.0854687235090468 |
| sensor.bureau_probabilite_presence | Probabilité de présence | 100 |
| sensor.bureau_v2_lux_echantillon | Luminosité | 1924.0 |
| sensor.chambre_emile_humidite_2 | Humidité | 53.8 |
| sensor.chambre_emile_temperature_2 | Température, Émile | 22.26 |
| sensor.chambre_maddy_humidite_2 | Humidité | 51.6 |
| sensor.chambre_maddy_temperature_2 | Maddy, Température | 20.33 |
| sensor.chambre_parentale_humidite_2 | Humidité | 55.2 |
| sensor.chambre_parentale_temperature_2 | Parents, Température | 21.15 |
| sensor.conso_maison_jour | Aujourd’hui, Consommation du jour | 21.99 |
| sensor.conso_maison_mois | Ce mois | 51.14 |
| sensor.conso_phev_jour | Consommation du jour | 9.0 |
| sensor.cout_total_mois_hp_hc | Coût mensuel | 187 |
| sensor.emile_battery_level | Template ou carte héritée | 79 |
| sensor.ene01_pv_day_kwh | Solaire du jour | 0.0 |
| sensor.entree_temperature_2 | Entrée | 21.9 |
| sensor.garage_production_electricite_sensor_energie_solaire_produite | Production solaire cumulée | 1802.32 |
| sensor.laura_battery_level | Template ou carte héritée | 76 |
| sensor.linky_puissance_watts | Puissance, Puissance actuelle | 716 |
| sensor.linky_tarif_actuel | Tarif en cours | HEURE PLEINE |
| sensor.navimow_i206_awd_battery | Batterie | 80 |
| sensor.navimow_i206_awd_task_progress | Progression | 70 |
| sensor.primadonna_elite_experience_etat_de_l_appareil | Machine à café | Descaling needed |
| sensor.rv3_jour_eur | Coût du jour | 1.71 |
| sensor.rv3_mois_eur | Coût du mois | 1.75 |
| sensor.rv3_semaine_eur | Coût de la semaine | 4.48 |
| sensor.rv3_statut | État recharge | Suivi actif |
| sensor.s25_denis_battery_level | Template ou carte héritée | 43 |
| sensor.salle_a_manger_temperature_2 | Salle à manger | 21.17 |
| sensor.salon_humidite_2 | Humidité | 51.3 |
| sensor.salon_temperature_2 | Salon, Température | 22.3 |
| sensor.sami_surface_de_nettoyage | Surface nettoyée | 6.6 |
| sensor.sami_temps_restant_brosse_laterale | Brosse latérale | -88.4483333333333 |
| sensor.sami_temps_restant_brosse_principale | Brosse principale | 274.549444444444 |
| sensor.sonde_plante_battery | Batterie de la sonde | 100 |
| sensor.sonde_plante_soil_moisture | Humidité du sol | 100 |
| sensor.sonde_plante_temperature | Température de la plante | 20.9 |
| sensor.sportage_car_battery_level | Batterie 12 V | 83 |
| sensor.sportage_ev_battery_level | Batterie de traction, Sportage | 36 |
| sensor.sportage_ev_range | Autonomie électrique | 0.0 |
| sensor.sportage_fuel_driving_range | Autonomie carburant | 85 |
| sensor.sportage_fuel_level | Carburant | 13 |
| sensor.sportage_last_updated_at | Dernière actualisation | 2026-10-03T13:44:48+00:00 |
| sensor.sportage_odometer | Kilométrage | 72503.5 |
| sensor.tel_maddy_battery_level | Template ou carte héritée | 38 |
| timer.lecture_zen_timer | Temps restant | idle |
| vacuum.sami | Aspirateur Sami, Sami | cleaning |
| weather.forecast_maison | Météo | partlycloudy |
