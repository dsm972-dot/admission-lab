# Mission ciblée : famille complète et Sportage entier

Réponds en français. Répertoire /root/workspace/maison/ai-nexus-home-v4. Lis AGENTS /root/workspace/maison/AGENTS.md et cette mission. Le dépôt est volontairement dirty : NE PAS toucher/revert les changements préexistants ni committer. Pas de réseau, pas de publication HA ni commandes physiques. Hermes fera tests et publication native.

Demande Denis : maquette fournie /root/.hermes/webui/attachments/838f6e7e7697/tableau_de_bord_domotique_ai_nexus_avec_sportage-1.png. Les cartes famille doivent avoir présence indépendante du réseau, batterie %, icône batterie, icône Wi-Fi OU réseau mobile et libellé explicite. Le Sportage doit être visible EN ENTIER sans recadrage. Pas de refonte globale : conserver le responsive Sections récent, toutes les autres vues et données.

Constats vérifiés : tools/visual_design.py build_home ne montre aujourd'hui que nom, présence, batterie texte. Sportage utilise une image 195x76 et style height:82px;object-fit:cover. tools/build_visual_assets.py crop sportage=(775,816,970,892), mal cadré (hauteur et bord droit). La source est 1672x941. La voiture entière dans la maquette se situe environ x775..950 y806..890 (à ajuster pour marge, pas inclure les chiffres à droite x>=970 ni boutons y>=893). Utiliser nouveau asset sportage-full.webp, object-fit:contain, object-position:center, aucun fond cover, hauteur adaptative avec ratio adéquat. Conserver l'ancien asset pour rollback/cache. Les photos sont illustratives, les valeurs restent HA live.

Données réseau HA EXISTANTES vérifiées exactement :
- denis_wifi: sensor.s25_denis_wi_fi_connection
- denis_network: sensor.s25_denis_network_type
- denis_mobile: sensor.s25_denis_data_network_type_sim_1
- laura_wifi: sensor.laura_wifi_connection
- laura_network: sensor.laura_network_type
- laura_mobile: sensor.laura_data_network_type_sim_1
- emile_wifi: sensor.emile_wi_fi_connection
- maddy_wifi: sensor.tel_maddy_wi_fi_connection
Emile/Maddy : aucun capteur network/mobile activé connu. Ne pas inventer d'ID ou supposer mobile d'après l'absence. Pas utiliser les trackers *_wifi legacy : pas fiables. Ne pas prendre binary_sensor.wifi_state (radio activée != connecté).
Exemple réel pendant collecte : Denis SSID Dsm972 network wifi, Laura SSID <not connected> network cellular et LTE (afficher 4G), Emile SSID Freebox-1C0F52 hors maison (Wi-Fi ailleurs, NE PAS transformer en présence maison), Maddy SSID Dsm972. Ces valeurs sont exemples de données réelles à un instant, PAS coder en dur.

Classification robuste :
- network_type téléphone wifi -> Wi-Fi, cellular/mobile -> génération via data_network_type SIM si valide (LTE=4G, NR=5G, UMTS/HSPA/WCDMA=3G, EDGE/GPRS=2G), sinon Mobile.
- network_type absent/invalide -> SSID valide -> Wi-Fi. <not connected>, unknown, unavailable, none, vide, etc. ne sont PAS un SSID connecté. Pas de SSID + aucun type réseau -> Connexion indisponible / Non renseignée, PAS déduction 3G/mobile.
- network_type none valid -> Hors ligne ou Sans connexion (distinguer inconnu).
- battery numérique 0..100 valide : icône et % ; sinon Indisponible, pas zéro inventé.
- présence basée exclusivement person.*, pas du SSID. Ne pas afficher tous les gens à la maison.
- escaper valeurs HA/SSID, aucune injection HTML.
- triggers_update inclut chaque capteur utilisé. Responsive : 4 cartes larges PC, 2 colonnes téléphone si la largeur le permet, 1 colonne très étroite ; petites icônes Wi-Fi/téléphone et batterie bien visibles. Conserver structure .person pour vérifications DOM.

Fichiers modifiables exclusivement : tools/visual_design.py, tools/build_visual_assets.py (corriger extraction Sportage, asset NOUVEAU), tools/build_entity_map.py (slots exacts permanents), data/entities_map.json (8 nouveaux slots exacts), tests/test_family_vehicle.py (nouveau), éventuellement tests/test_visual_design.py si contrat asset. Ne change pas tools/ha_client.py / tools/build_dashboard.py / anciens tests hors périmètre. Si lib manquante, NE PAS installer de paquets. Ne pas éditer images binaires à la main : Hermes exécutera le builder d'asset.

Tests demandés : Node évaluant le template avec états explicitement simulés uniquement en tests : Wi-Fi, 2G/3G/4G/5G/mobile générique, données indisponibles/incohérentes, SSID malveillant (HTML escaped), batterie 0, 100, unknown/out of range, présence séparée du réseau, triggers complets ; styles/image contain ; crop nouveau dans manifeste. Aucun vrai état HA substitué par fixture lors de publication.

Réduction risque : ciblage famille et Sportage uniquement. Garde les noms de carte Famille regroupée / Sportage photographique. N'ajoute pas d'actions à la carte famille (navigate plus existant) ni à véhicule (navigate voiture existant). Ne modifie pas les ressources/thèmes/défaut/dashboards anciens.

Livrables : code + tests + rapport docs/FAMILY_VEHICLE_CODEX_RESULT.md, listant exact fichiers modifiés, tests réellement exécutés et limites. Pas déclarer publié. Budget environ 6 minutes. Termine sans attendre un accès réseau. Si quota/auth bloquent, rapporte directement.
