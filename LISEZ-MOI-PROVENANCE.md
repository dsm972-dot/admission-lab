# Provenance de cette copie de code

Cette arborescence est une **copie de travail**, pas un dépôt Git. Elle existe pour que la
refonte puisse être lue ligne par ligne et exécutée sans accès à la machine d'origine.

| Élément | Valeur |
|---|---|
| Dépôt source | `/root/workspace/maison/ai-nexus-home-v4` |
| Branche | `main` |
| Dernier commit | `7957865cc13a2f0a92caaa8cfd721c00c0cee123` (2026-10-11, « V4: README du dépôt dédié + durcissement .gitignore ») |
| Modifications locales non commitées | **6 fichiers modifiés, 11 fichiers non suivis** au moment de la copie — la copie reflète l'arbre de travail, pas le commit |
| Fichiers copiés | 104 |
| Date de copie | 7 novembre 2026 |

Fichiers modifiés par rapport au commit (l'arbre de travail est **en avance** sur Git) :

- `config/ai-nexus-v4.json`, `config/ai-nexus-v4.yaml`, `config/ai-nexus-v4-validation.json`
- `docs/BACKUP_CHECK.md`
- `tools/build_entity_map.py`, `tools/publish_full_update.py`

## Ce qui a été copié

| Dossier | Contenu | Pourquoi |
|---|---|---|
| `tools/` | 55 scripts Python : générateur (`build_dashboard.py`), design (`visual_design.py`), cartographie (`build_entity_map.py`), publication, diagnostic, captures | C'est ici que se trouvent les cinq lignes fautives citées dans le document `02` |
| `config/` | Dashboard généré en JSON et YAML, validation, enregistrement, thème glass | Le livrable réel produit par la chaîne |
| `themes/` | Thème(s) YAML | Rendu visuel |
| `docs/` | 29 documents de chantier (architecture, décisions, rapports QA) | Contexte historique des choix |
| `tests/` | 9 tests Python du dépôt | Comportement attendu du générateur |
| `data/states.json` | Instantané des états d'entités utilisé par la cartographie | **Source des noms d'entités morts** : c'est ce fichier qui réinjecte les noms périmés si `build_entity_map.py` est relancé. **Caviardé** : mot de passe, jetons d'accès et jetons d'URL remplacés par `[RETIRE]` (voir `00-LIRE-EN-PREMIER.md`) |
| `entities_map.json` | Cartographie logique → entité réelle | Table de correspondance utilisée par le générateur |

## Ce qui n'a **pas** été copié, volontairement

- `.venv/` (environnement virtuel, 300 Mo), `.git/`, `__pycache__/`
- `backups/`, `evidence/`, `missions/`, `logs/`, `local_qa/` — archives de chantier, sans valeur pour la refonte
- `data/` hors `states.json` — les dumps datés (énergie, vérifications) alourdissent sans éclairer
- **Aucun identifiant, token ou secret.** Le dépôt d'origine exclut les secrets par `.gitignore` ; cette copie ne les contient pas davantage.

## Pour exécuter

Aucun `requirements.txt` n'existe dans le dépôt. Les scripts utilisent la bibliothèque standard et
quelques paquets (client HTTP vers Home Assistant, `PyYAML`, `websocket-client`). Le point d'entrée
du générateur est `tools/build_dashboard.py` ; il lit `data/states.json` et `entities_map.json` et
écrit dans `config/`. Un `README.md` du dépôt d'origine est inclus à la racine de ce dossier.

## Avertissement de lecture

`tools/export_handoff.py` et les scripts `publish_*.py` écrivent sur l'instance réelle. Toute
exécution contre une instance Home Assistant doit être faite sur une copie, avec sauvegarde
préalable — voir le document `02`, §7 (procédure de sauvegarde et de retour arrière).
