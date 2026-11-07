# AI Nexus Home V4

Tableau de bord Home Assistant généré. Le fichier publié n’est pas édité à la main :
`tools/build_dashboard.py` produit `config/ai-nexus-v4.json`.

## Ce que fait un appui

- Une tuile d’équipement **commande** au toucher : `light.toggle`, `switch.toggle`,
  `cover.toggle`, `climate.set_hvac_mode`, `media_player.toggle`, `vacuum.start`,
  `lawn_mower.start_mowing`, `button.press`, `script.turn_on`.
- Le maintien ouvre la fiche. Les volets, la serrure, les vitres et la détresse
  demandent une confirmation.
- Une entité `unavailable` ou `unknown` s’affiche **Hors ligne** et ne se commande pas.
- Les capteurs (Sportage inclus) sont en lecture seule. Les commandes Kia réelles
  — charge, climatisation, vitres, actualisation — sont sur la vue Sportage.
- Alarmo ne s’arme pas depuis ce tableau : le code reste dans son interface.

## Entités recâblées (7 novembre 2026)

| Avant | Après |
|---|---|
| `light.lumiere_du_salon` | `light.salon_projecteur` |
| `light.cuisine` | `light.ampoule_cuisine` |
| `light.chambre_emile` | `light.ampoule_emile` |
| `light.chambre_maddy` | `light.ampoule_maddy` |
| `light.chambre_parentale` | `light.ampoule_chambre_parentale_1` |
| `light.lumiere_bureau` | `switch.interrupteur_bureau` |
| `cover.volet_de_la_cuisine_rideau` | `cover.volet_cuisine_etat` |
| `cover.volet_de_la_chambre_de_emile_rideau` | `cover.volet_emile_etat` |
| `cover.curtain_switch_rideau` | `cover.volet_maddy_etat` (l’ancien module reste à diagnostiquer) |
| `media_player.sound_bar_5` | `media_player.sound_bar_lg` |

L’ambilight du bureau et les lecteurs Meghann sont hors ligne : ils ne sont pas présentés comme pilotables. Le détail est sur la vue Diagnostic.

## Régénérer

```sh
python3 tools/build_entity_map.py
python3 tools/build_dashboard.py
python3 -m unittest discover -s tests -v
```

L’instantané utilisé est `data/states.json` (états du 7 novembre 2026, secrets retirés).

## Aperçu local

```sh
python3 tools/preview_server.py
```

Puis ouvrir `http://127.0.0.1:8765`. Les commandes y sont **simulées** : rien n’est envoyé à la maison. La publication dans Home Assistant se fait ensuite, avec l’outil habituel, à partir de `config/ai-nexus-v4.json`.

## Sécurité

Aucun jeton n’est dans ce dépôt. `tools/ha_client.py` refuse toujours les services physiques avant tout appel réseau. Les ressources Lovelace en 404 (webrtc-camera, mushroom-cards, doublon card-mod, modules bubble) sont retirées de `data/resources.json` ; il reste à les désenregistrer dans Home Assistant.

## Sécurité / secrets

Tout secret est exclu du versionnement (voir `.gitignore`) :
`.env`, tokens, clés SSH/privées, archives de backups `*.tar(.gz)`, répertoire
`backups/`. Les identifiants HA sont lus via SSH/vault à l'exécution, jamais
committés.

## Historique

Les commits sont organisés **par phase** du projet (préflight, génération,
QA locale, corrections visuelles, canary, clôture…). Voir `docs/` pour les
rapports de phase (`AI_NEXUS_V4_*`).

## Structure

    config/     générateur + artefacts (vues Lovelace, thème, registration)
    data/       exports d'états/entités HA (données réelles, non committées en JSON)
    docs/       rapports et documentation du projet (AI_NEXUS_V4_*)
    evidence/   captures et preuves QA
    missions/   propositions isolées par mission
    tests/      suite de tests (unittest)
    tools/      clients HA (REST/WS) et utilitaires
    assets/     ressources statiques du projet

## Workspace

- Chemin : `/root/workspace/maison/ai-nexus-home-v4`
- Le dépôt parent `/root/workspace` n'est jamais modifié depuis ce projet.
