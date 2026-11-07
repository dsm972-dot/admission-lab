# Livraison locale V4 — rapport provisoire

LOCAL_PASS : constructeur effectif, 17 vues, 109 entités vérifiées, thème clair/sombre,
exports JSON/YAML déterministes et 25 tests unitaires. Les fichiers sont dans `config/`,
le générateur dans `tools/build_dashboard.py`, les tests dans `tests/test_build_dashboard.py`.

```sh
python3 tools/build_dashboard.py
python3 -m unittest discover -s tests -v
```

Le journal d’exécution est `logs/tests.log`. Le manifeste
`config/ai-nexus-v4-validation.json` détaille les références et les exclusions.
`ENTITY_MAPPING.md`, `AI_NEXUS_V4_ARCHITECTURE.md`, `DECISIONS.md`, `CHANGELOG.md`,
`BACKUP_CHECK.md` et `QA_REPORT.md` documentent la construction et ses limites.

Configurations Navimower et YAMP conservées depuis des sources valides. Xiaomi Map
absente des sources : repli explicite. Les températures cuisine/bureau ne sont pas
inventées. Les commandes serrure/garage/volets sont isolées et confirmées. Alarmo et
Sportage restent en statut ; aucun parcours sensible natif caché n’est ajouté.

PENDING_BROWSER_QA : rendu réel, responsive, popups, contrôles internes aux cartes,
ressources HTTP, reconnexion et performances. PENDING_PHYSICAL_CONFIRMATION : aucune
action réelle testée. PENDING_CANARY : aucun usage parallèle commencé.

Aucun déploiement HA, appel API de commande, modification de script/automation,
installation de ressource, mise à jour, commit ou changement hors du dépôt V4.
L’ancien dashboard n’a pas été touché. La future restriction admin est fournie dans
le fichier séparé d’enregistrement ; elle n’est pas encore appliquée sur HA.
