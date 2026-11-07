# AI Nexus Home V4 — architecture locale

Le constructeur `tools/build_dashboard.py` lit uniquement les instantanés du dépôt :
`states.json`, `entities_map.json`, les deux exports Lovelace historiques, `resources.json`
et, lorsqu’il existe, `services.json`. Il ne charge aucun client HA, secret ou fichier
.env et ne fait aucun appel réseau. Aucun script ou automation HA n’est modifié.

## Reproduction

Prérequis : Python 3, PyYAML (version locale utilisée : 6.0.3), Node.js pour les tests
JavaScript. Aucun paquet supplémentaire n’a été installé pendant cette construction.

```sh
python3 tools/build_dashboard.py
python3 -m unittest discover -s tests -v
```

Les sorties sont déterministes, sans date de génération ni valeurs de capteurs figées.
`--output-dir /tmp/ai-nexus-review` permet une reconstruction séparée.

## Exports

- `config/ai-nexus-v4.json` et `.yaml` : même configuration Lovelace, 17 vues.
- `config/ai-nexus-glass.yaml` : thème clair/sombre AI Nexus Glass.
- `config/ai-nexus-v4-registration.json` : métadonnées pour une future création
  storage, URL `ai-nexus-v4`, `require_admin: true`. Ce fichier n’enregistre rien.
- `config/ai-nexus-v4-validation.json` : entités utilisées, exclusions, adaptations
  héritées et résultats de validation structurelle.

Le JSON Lovelace ne contient pas l’enveloppe `.storage` de HA. Les métadonnées
administrateur doivent être appliquées séparément lors d’un éventuel déploiement
ultérieur. Aucune instruction de déploiement n’est exécutée ici.

## Interface

Vues sections natives, trois colonnes au maximum, cartes button-card homogènes,
verre bleu/cyan et rayon 22 px. Navbar : rail gauche desktop, comportement mobile
inférieur ; les sept routes et leur lisibilité restent à éprouver sur téléphone.
Les vues secondaires sont accessibles par Plus et Équipements. Diagnostic est une
subview ; ce n’est pas une protection d’accès. La restriction admin porte sur le
futur dashboard entier, sans identifiant utilisateur inventé.

L’accueil contient un salut lié à l’utilisateur, la date dans le fuseau HA, la météo,
la famille avec batteries, les incohérences présence/absence, six pièces, six
mesures de température, une moyenne frontend, énergie, sécurité et quatre raccourcis.
Aucune température cuisine ou bureau n’est inventée. La moyenne ignore les valeurs
absentes et non finies ; zéro reste une vraie mesure. Aucun helper n’est créé.
La date se réévalue lors des mises à jour HA ; pas de minuterie frontend ajoutée.

Les six popups Bubble reprennent le schéma `pop-up`/`cards` présent dans l’export
historique. Chaque lien hash possède son popup dans la même vue (Accueil et Pièces).
La présence historique du schéma n’est pas une preuve de rendu : QA navigateur requise.
Aucun graphe ou flux caméra n’est chargé sur l’accueil. Les caméras sont consultées
via more-info à la demande sur les détails.

## Commandes et cartes héritées

Serrure, garage et volets : statut sans more-info natif, boutons distincts avec
maintien et confirmation, capacités `supported_features` contrôlées. Pas de commande
Sportage ni de désarmement Alarmo exporté ; Alarmo renvoie textuellement à l’interface
habituelle avec code. Aucun PIN n’est copié. Les commandes Lecture Zen réutilisent
les scripts existants via maintien confirmé.

Navimower Map et YAMP sont copiés d’une configuration héritée dont toutes les entités
explicites existent. Navimower Map est masquée lorsque la tondeuse est indisponible ;
le résumé affiche En veille. Son option héritée `auto_entities` reste dynamique : les
entités découvertes par la carte et ses contrôles internes demandent un examen navigateur.
Aucun schéma Xiaomi Map n’a été trouvé : Sami propose ses statuts/maintenance et un
message de repli explicite, sans inventer de carte ou de coordonnées.

## Portée des validations

Validation des références dans les cartes et templates, ressources déclarées,
routes, hashes, services, cibles et capacités des commandes sensibles. Exécution
JavaScript avec Node, sans DOM ni HA. La disponibilité HTTP des ressources, le rendu,
les contrôles internes aux cartes héritées, les effets réels des scripts et les
performances restent hors preuve locale. Voir QA_REPORT.md.
