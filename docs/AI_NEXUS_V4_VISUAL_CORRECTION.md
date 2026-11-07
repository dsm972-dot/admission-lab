# AI Nexus V4 — correction visuelle publiée, acceptation en attente

Tâche de correction : t_bba226c9, board ai-nexus-v4.

## Livraison réelle

La candidate corrigée est accessible à :
http://10.0.0.47:8123/ai-nexus-v4/accueil

Publication ciblée par `tools/publish_visual_correction.py publish`, puis nouvelle vérification indépendante par `verify`. Les résultats sont consignés dans `data/visual-correction-publication/readback.json` et `evidence/visual-correction-final-verify.log`. Statut technique : VISUAL_CORRECTION_PUBLISHED_READBACK_VERIFIED. La configuration HA relue correspond exactement à la configuration construite ; ses 17 vues sont conservées. L'ancien dashboard, le défaut, les préférences, les ressources et le thème existants ont les mêmes empreintes qu'avant cette correction. Aucune commande d'actionneur, aucun redémarrage et aucun changement d'authentification.

## Ce qui a changé

- Bandeau Accueil avec photographie illustrative de maison et jardin, informations issues d'entités HA.
- Six tuiles de pièces photographiques, légendes lisibles, navigation vers les vues existantes.
- Visuels Navimow et Kia Sportage, états dynamiques plutôt que chiffres figés de la maquette.
- Cartes compactes, fonds glass/translucides, espacements réduits et grilles adaptées aux écrans.
- Onze WebP locaux, provenant de recadrages ciblés de la référence fournie : pas une capture entière placée en fond. Les recadrages ne constituent pas des photos du domicile de Denis.
- Préservation des autres vues et de leurs données/actions de navigation ; aucune exécution de leurs actions physiques pendant le travail.

Les onze fichiers publiés ont été récupérés par HTTP et leurs SHA256 comparés au manifeste. Tous correspondent. La configuration relue porte l'empreinte :
`ef3e3d7e0e14883f4eae3b60f5f248885e8f333ce2bc30dd837ac375b745e5f3`.

## Vérifications rejouées

- Suite complète : 61 tests PASS et 46 sous-tests PASS.
- QA Accueil finale : 6 largeurs, 412 / 480 / 600 / 1280 / 1920 / 2560 px ; zéro débordement horizontal, zéro erreur de page et zéro requête de mutation.
- Neuf images effectivement présentes et chargées dans Accueil à chaque largeur ; couverture complète des onze fichiers via publication et tests d'assets.
- Capture des vraies cartes custom avec instantané d'états HA réels dans une coque locale approximative.
- La barre sticky de cette coque masquait le bandeau lors des captures d'éléments. Sa position a été rendue statique uniquement dans la sonde locale ; ce réglage n'est pas une modification du dashboard HA.
- Comparaison réelle référence/capture finale par Gemini vision, conservée dans `evidence/visual-correction-home-final/comparaison-vision-finale.txt`.
- Tentative Chromium directe sur l'URL HA : redirection vers le formulaire `/auth/authorize`. Aucun identifiant demandé ou modifié. Le rendu natif authentifié reste NON VÉRIFIÉ par cette session.

## Captures finales et limites honnêtes

Sous `evidence/visual-correction-home-final/` :
`accueil-412.png`, `accueil-480.png`, `accueil-600.png`, `accueil-1280.png`, `accueil-1920.png`, `accueil-2560.png`, et `comparaison-finale.jpg`.

Les captures sont celles du banc local, pas des captures de HA natif authentifié. Elles attestent le chargement des cartes et l'adaptation des grilles, pas une identité pixel à pixel avec la maquette.

Différences restantes identifiées par la comparaison visuelle : navigation locale différente de celle de la maquette ; photos de pièces moins hautes ; bandeau/traitement glass et hauteur des modules Navimow/Sportage non identiques ; disposition native et effet du thème à confirmer dans HA. Les informations montrent les vrais états disponibles et peuvent différer des exemples dessinés. Les photos sont illustratives et les recadrages ont une résolution limitée.

ACCEPTATION VISUELLE DENIS : PENDING. PROJET GLOBAL : NON CLÔTURÉ.

## Sauvegarde et rollback de cette correction

Snapshot exact pré-correction : `data/visual-correction-publication/before.json`, accompagné du plan `ROLLBACK.txt`. Il conserve la candidate précédemment en service et les fichiers spécifiques avant écriture. Il ne remplace pas les sauvegardes initiales du projet.

Exécution explicite du retour arrière, uniquement si demandé :
`python3 tools/publish_visual_correction.py rollback --apply`

Le mode sans `--apply` ne fait qu'émettre le plan. Un rollback exécuté contrôle l'empreinte de la candidate avant restauration et vérifie les invariants et les fichiers ensuite. Aucun rollback effectif n'a été demandé ni exécuté lors de cette livraison.

## Observation après publication

L'observation initiale vérifiait l'ancienne candidate via `tools/publish_candidate.py verify`. Ses preuves sont conservées et ne peuvent pas être revendiquées comme observation de cette nouvelle version. Suivi séquentiel distinct créé : t_61e35cc3, profil devops, dépendant de la fin de la correction. Il doit adapter l'observation bornée en lecture seule à cette version sans perdre les anciennes preuves. Aucun worker de correction concurrent lancé ; aucun cron modifié dans cette tâche.

La finalisation t_e6872bd6 reste bloquée pour observation et validation visuelle. La livraison de cette phase de correction n'est ni un PASS global ni un accord humain.
