# Correction responsive AI Nexus V4 — 2026-10-04

## Diagnostic et références

Les deux images demandées ont été lues : `screenshot-1791114841961.png` montre les composites comprimés côte à côte ; `tableau_de_bord_domotique_ai_nexus_avec_sportage.png` donne la cible : bandeau, famille/vigilance, six pièces, climat/sécurité/robots, énergie/Sportage/multimédia/accès.

La vue native comporte `max_columns: 4`, la section `column_span: 4`. Home Assistant borne ce span au nombre de colonnes disponibles ; sa grille interne comporte **12 × span effectif** pistes. Sur desktop, les anciennes cartes de 12 colonnes occupaient donc chacune seulement un quart des 48 pistes. Les quatre premiers composites partageaient une ligne ; le cinquième commençait la suivante. Une coque locale mettant ces composites en bloc masquait ce défaut.

Sources consultées :

- [button-card v7 — Section Views](https://custom-cards.github.io/button-card/v7.0/advanced/section-views/) : `section_mode: true`, dimensionnement via `grid_options`, éviter les dimensions CSS explicites de la carte en mode section.
- [HA hui-grid-section.ts](https://github.com/home-assistant/frontend/blob/dev/src/panels/lovelace/sections/hui-grid-section.ts) : multiplication par 12, span borné, classe `full-width` utilisant `grid-column: 1 / -1`, hauteur fixe uniquement pour les lignes numériques.
- [HA hui-sections-view.ts](https://github.com/home-assistant/frontend/blob/dev/src/panels/lovelace/views/hui-sections-view.ts) : limitation du span à la largeur disponible. Sources `dev` consultées le 04/10/2026 ; version HA installée non interrogée.

## Modifications

Dans `tools/visual_design.py`, les cinq composites directs utilisent `section_mode: true`, `columns: full`, `rows: auto`. La section reste élargie sur quatre colonnes natives ; chaque composite remplit sa largeur effective, même lorsqu'elle est réduite sur mobile. Pas de hauteur ou largeur CSS forcée sur ces cartes.

Les requêtes CSS portent maintenant sur la largeur du conteneur de carte plutôt que sur celle de la fenêtre : elles prennent ainsi en compte une barre latérale. Les rangées passent à une disposition intermédiaire sous 1250 px et mobile sous 650 px. Les pièces sont disposées par six, puis trois, puis une. Les mesures, personnes, bandeau et climat se réorganisent à leur propre largeur ; textes longs et données indisponibles peuvent revenir à la ligne. Les hauteurs restent déterminées par le contenu.

Dans `tools/build_dashboard.py`, la validation refuse toute référence de template button-card absente du dictionnaire racine. Le retour et les exports restent complets (`title`, `button_card_templates`, `views`). Une régression supprime expressément les templates pour reproduire la perte observée lors de la publication précédente. Le script de publication est hors périmètre : il n'a pas été modifié et pourrait encore tronquer un export s'il était réutilisé tel quel.

## Preuves exécutées

Commandes locales :

```sh
python3 -m unittest discover -s tests -p 'test_build_dashboard.py' -v
python3 -m unittest discover -s tests -p 'test_visual_design.py' -v
python3 -m unittest discover -s tests -p 'test_native_sections.py' -v
python3 tools/build_dashboard.py --output-dir /tmp/ai-nexus-responsive-build
```

Résultats : **26 + 4 + 2 = 32 tests réussis**. La classe de tests navigateur est explicitement ignorée après échec du lancement Chromium : `sandbox_host_linux.cc:41`, `Operation not permitted`. Ce résultat ne constitue pas une validation visuelle.

- Tests natifs hors navigateur : spans effectifs 1, 2, 3 et 4 ; chaque composite occupe une ligne complète. Contre-exemple des anciens spans : positions `(ligne, colonne)` = `(0,0), (0,12), (0,24), (0,36), (1,0)`.
- Contrats : section_mode, lignes automatiques, absence de dimensions CSS imposées aux composites directs.
- Build : exports JSON/YAML identiques sémantiquement, deux générations déterministes, template `glass` conservé, export tronqué rejeté, validation entités/ressources/services et protections des commandes inchangées.
- Résultat CLI : `LOCAL_PASS: 17 vues, 110 entités vérifiées. Exports locaux uniquement.` Fichiers produits dans `/tmp/ai-nexus-responsive-build` ; aucun export du dossier `config` écrasé.

`tests/test_native_sections.py` contient aussi un banc Chromium indépendant de `local_qa` : équations CSS de la grille native, wrappers de cartes, shadow roots séparés, styles et HTML des cartes générées. Il prévoit 320, 375, 390, 600, 768, 1024, 1280, 1440 et 1842 px, avec les états locaux et avec toutes les données absentes. Il mesure largeur des rangées, ordre vertical, débordements, intersections des enfants et disposition des six pièces, et comporte un contre-test restaurant les anciens spans. Aucun accès réseau n'est autorisé par ce banc.

## Vérification finale par Hermes dans HA natif

Les limites du sandbox Codex ci-dessus ont été levées par une vérification Chromium du dashboard HA réellement publié, et non par la coque locale.

- Publication complète : `title`, `button_card_templates`, `views`, puis relecture exactement identique.
- Correction supplémentaire : button-card installé utilise `#container`, pas `#grid`. Les règles responsives pointent désormais vers ce conteneur réel. Le banc de tests a été corrigé pour ne plus masquer cette erreur.
- 67 tests exécutés, tous réussis, y compris les tests navigateur auparavant ignorés.
- Six largeurs natives : 1842, 1280, 768, 412, 375, 320 px. Dans chacune : 17 panneaux, six pièces, zéro débordement horizontal mesuré dans les panneaux, zéro intersection entre panneaux, zéro carte d'erreur, zéro erreur JavaScript ; toutes les images attendues chargées.
- Pièces : six sur une rangée à 1842 px, trois par rangée à 1280 px, une par rangée dans les formats plus étroits testés. Réorganisation selon la largeur utile, barre latérale comprise.
- Retrait des légendes de développement de l'Accueil ; les photographies restent des illustrations, les états proviennent de HA. Aucun état indisponible remplacé par une valeur inventée.
- Preuves actuelles : `evidence/responsive-verified/report.json`, `geometry-summary.json`, `dashboard-readback.json` et captures `ha-*.png`.
- Sauvegarde et procédure de retour arrière : `evidence/responsive-verified/dashboard-before.json` et `ROLLBACK.txt`. Autres dashboards relus et inchangés. Aucun changement de thème, de ressources ou de dashboard par défaut par ce script ; aucun service physique appelé.

La vérification géométrique confirme la résolution de la compression et des chevauchements, pas une fidélité pixel à pixel ni l'acceptation visuelle de Denis. Les barres natives de HA et l'absence de graphiques historiques sur l'Accueil restent des différences connues avec la maquette. L'analyse visuelle externe du montage a correctement identifié la disparition de la compression, mais a aussi fait des erreurs sur les données et les éléments : ses conclusions sémantiques ne sont pas utilisées comme preuve.

## Limites et périmètre actuels

Le banc Chromium et la vérification native ont maintenant tourné ; les résultats et captures sont listés ci-dessus. La géométrie, le chargement des images et la configuration publiée sont vérifiés. Les interactions de tous les pop-ups, la reconnexion en conditions réelles et la fidélité visuelle exacte à la maquette ne sont pas attestées par cette campagne responsive. Aucun accord humain ni PASS global du projet n'est déduit de ces tests.

La correction reprend l'ordre et les grandes rangées de la maquette avec les assets et données existants ; elle ne promet pas une copie pixel à pixel ni les graphiques/commandes illustratifs de la maquette.

Seuls les deux générateurs autorisés, les tests et ce rapport ont été modifiés par cette intervention. Les changements préexistants hors périmètre sont conservés. Aucun accès HA, secret, publication ou commit.
