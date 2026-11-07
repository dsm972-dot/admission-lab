# Rapport QA AI Nexus V4

Le rapport de référence est [AI_NEXUS_V4_FINAL_REPORT.md](AI_NEXUS_V4_FINAL_REPORT.md).

Vérification Hermes initiale : 26 tests passent ; 17 vues et 109 entités vérifiées. Dashboards existants et ressources inchangés. Ressources : 31 déclarations HTTP 200, 2 HTTP 404 préexistantes non utilisées par V4, doublon card-mod conservé.

PENDING_BROWSER_QA : navigateur HA non authentifié et coffre indisponible pour ce site. PENDING_PHYSICAL_CONFIRMATION et PENDING_CANARY restent ouverts. Aucun test navigateur du dashboard connecté ni déploiement effectué. Nouvelle phase locale : 32 tests passent et 85 rendus Chromium isolés ont été capturés ; voir AI_NEXUS_V4_LOCAL_BROWSER_QA.md. Ce banc utilise les vraies cartes avec un layout approximatif et ne valide pas les gates production. Une suite locale verte ne démontre ni le rendu Bubble/YAMP/Navimower ni l’absence d’erreur JavaScript dans HA.
