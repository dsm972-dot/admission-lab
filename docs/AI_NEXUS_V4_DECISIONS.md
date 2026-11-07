# Décisions V4

1. Mandat local `CODEX_BRIEF.md` et instruction utilisateur prioritaires : construction
   de toutes les vues, sans déploiement, sans commit. Les gates navigateur des prompts
   initiaux restent ouverts ; aucune validation humaine n’est présumée.
2. Dashboard parallèle storage `ai-nexus-v4`, require_admin=true. Ancien dashboard
   intact, aucune nouvelle ressource ni mise à jour HACS/HA.
3. Sections natives et templates button-card ; Bubble pour les pièces, navbar existante.
4. Suppression des alias cuisine_temp/cuisine_hum : ils désignaient le salon. Bureau
   sans température. Moyenne des six capteurs vérifiés, calculée dans le navigateur.
5. Les états inconnus ne deviennent jamais zéro. Navimow indisponible est En veille.
   Les cartes ordinaires affichent Donnée non disponible ; valeurs numériques réelles
   conservées et formatées en français. Les états non standards textuels restent fournis
   par l’intégration, sans traduction spéculative.
6. Pas de carte native de commande pour serrure, garage, volets, Alarmo ou véhicule.
   Les commandes exportées exigent maintien et confirmation ; le statut reste inerte.
7. Alarmo : aucune commande de désarmement sans parcours de code vérifié. Sportage :
   télémétrie seulement. Café : réglages et état, aucun lancement automatique.
8. Navimower Map et YAMP issus des sources valides. Xiaomi Map absent : repli documenté.
9. Pas d’image de pièce fabriquée, prévisions horaires ni min/max météo inventés.
   L’accueil présente la météo courante et non la composition graphique exacte de la
   maquette. Pas de jauge circulaire ni graphe décoratif. Fidélité visuelle à approuver.
10. Diagnostic subview pour limiter l’exposition dans la barre de vues ; la sécurité
    repose sur l’enregistrement admin du dashboard, pas sur la subview.
11. Les anomalies de ressources héritées (card-mod déclaré deux fois et chemin Mushroom
    supplémentaire) restent intactes. La validation locale prouve leur déclaration,
    jamais l’absence de 404. V4 n’utilise ni Mushroom ni card-mod.
12. `services.json` est présent et vérifié. Si absent à l’avenir, le manifeste affichera
    PENDING_SERVICE_CATALOG ; aucun service ne sera appelé par le constructeur.
