# Finalisation maquette — contrat d'orchestration

Carte origine t_b61d8c4e. Référence fournie : /root/.hermes/webui/attachments/838f6e7e7697/tableau_de_bord_domotique_ai_nexus_avec_sportage-2.png.

## Décisions communes

Cible unique : dashboard storage ai-nexus-v4, route accueil. Conserver les routes existantes et les autres vues. Sections natives et button-card existants ; pas de nouvelle ressource/HACS, pas de modification de thème global. Utiliser les assets issus de la référence et les données HA vérifiées. Desktop fidèle à la disposition mesurée ; mobile adapté, non réplique miniature. Pas de valeur fictive, courbe décorative présentée comme historique, ni absence transformée en zéro. Les états et unités doivent provenir des entités vérifiées. Pas de service physique, activation de capteur, écriture d'état, redémarrage, modification sécurité/registre ou bascule par défaut.

Missions 01–09 : lecture HA uniquement et écriture exclusivement dans missions/NN-slug/. Ne jamais modifier tools/, config/, assets/, tests/ ou publier. Le livrable est une proposition intégrable, pas un changement en production. Chaque mission conserve REPORT.md, findings.json, et éventuellement proposal.diff et tests spécifiques. findings.json : objet {mission, scope, evidence:[{path,description}], root_causes:[], proposed_changes:[], entities:[], tests:[{command,result}], gaps:[], acceptance:"PENDING_DENIS"}. Aucun secret/token dans ces fichiers. Les scripts de diagnostic ne doivent pas imprimer d'authentification.

Mission 10 : intégrateur unique après toutes les missions et les deux cartes préexistantes. Modifications ciblées des fichiers communs, jamais écrasement de modifications tierces. Toute collision exige un commentaire hotspot. Lire la configuration live fraîche et sauvegarder dashboard cible, ancien, défaut et ressources avant publication ; préparer rollback explicite. Vérifier les empreintes avant écriture, préserver les changements live hors scope et arrêter en cas de conflit non expliqué. Sauvegarde officielle WebSocket seulement, sans .storage ni restart. Publication unique suivie d'une relecture exacte de la cible ; prouver ancien/défaut/ressources inchangés.

## Modèle et cadence

Profil default ou devops réellement disponible ; provider openai-codex, modèle gpt-6.1-sol vérifié par la session de contrôle existante 20261004_202147_eb7f78 et par le runtime parent. Aucun changement global de configuration. Pour codex exec, vérifier le slug disponible et la commande du skill ; ne pas deviner un équivalent. Blocage quota explicite, pas de relances coûteuses en boucle. Carte durable plutôt que délégation éphémère. Dix missions réparties en vagues de deux au maximum par dépendances : 01+02, 03+04, 05+06, 07+08, 09, 10. Ne pas déclarer dix agents simultanés.

## Validation finale obligatoire

Diagnostiquer avec documentation officielle button-card/Sections et DOM HA réel avant CSS. La grille interne peut être #container ; vérifier dans la version installée. Évaluer les templates imbriqués et leur réactivité (scénario synthétique local uniquement, états serveur inchangés). Les tests locaux ne prouvent pas le rendu HA. Exécuter tests unitaires/régression et navigateur HA authentifié aux six tailles 360x800, 390x844, 768x1024, 1024x768, 1366x768, 1920x1080. Captures natives, erreurs console/réseau, images, routes, unités, overflow et intersections. Comparer la capture desktop à la référence en alignant les zones et en distinguant contenu dynamique, image, typographie et géométrie ; livrer mesures et écarts, pas un score magique.

Rapport unique docs/TEN_MISSIONS_FINAL_REPORT.md : causes, choix, sources, risques, rollback, résultats réellement exécutés, écarts et acceptation Denis PENDING. Livrer captures et preuves par artifacts. Pas de copie parfaite ni PASS global sans preuve. Après intégration seulement, créer la mission d'observation bornée sur nouvelle baseline pour devops ; préserver toutes les générations antérieures et ne pas prétendre avoir observé 24h dès le lancement.

## Coordination existante

Énergie t_ded30fab : correcteur existant unique pour son template ; pas de second correcteur. Mission 09 prépare énergie/Sportage/média en lecture seule, en intégrant ses résultats. Intégrateur attend sa clôture et vérifie sa publication dans la configuration live fraîche.

Observation t_61e35cc3 : ne pas toucher ses fichiers/crons/baselines pendant les missions. Intégrateur attend sa mise en place, préserve les preuves et crée ensuite le suivi sur la nouvelle empreinte publiée. Ne pas clore les cartes historiques ou déduire une acceptation visuelle.
