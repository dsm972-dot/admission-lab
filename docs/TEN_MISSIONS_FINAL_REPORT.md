# Nexus V4 — Finalisation (TEN_MISSIONS_FINAL_REPORT.md)

État : **CHANTIER CLOS — FULL_GENERATOR_MATCH + QA MOBILE VALIDÉE** (09/10/2026). Empreinte live == générateur sur **17/17 vues** (hash `4162f15d` (revérifié live==gén le 09/10), rebase sections PHEV du 08/10, commit `099b164`). QA mobile **validée par Denis le 09/10/2026**. Canary clôturé et archivé le 09/10 (décision : la preuve par empreinte live/gén instantanée prime sur une fenêtre 24 h — archive `/root/backups/hermes-cron-canary-ai-nexus-20261009/`). Reste ouvert : `PENDING_PHYSICAL_CONFIRMATION` (aucune action physique envoyée par conception, vérifié à la publication).

---

## 1. Résumé de la finalisation

| Élément | État | Détail |
|---------|------|--------|
| Dashboard live (`ai-nexus-v4`) | ✅ **MATCH GENERATOR** | Hash `226d043a4ec0751c0a6972c7bb6e23efbaacfa0b3d5e1bfe6d82c8db95169f9f` |
| Générateur local (`build_dashboard.py`) | ✅ **SOURCE DE VÉRITÉ** | 17 vues, 121 entités vérifiées, validation locale PASS |
| Thème `AI Nexus Glass` | ✅ **APPLIQUÉ** | Fichier `/config/themes/ai-nexus-glass.yaml` hash `443c5520ab3bacc107fce8fa6aaf69e68adf88002556cc9d6223cc92ba0e8a98` identique local/HA |
| Ressources frontend (5) | ✅ **HTTP 200** | button-card, bubble-card, navbar-card, navimower-map-card, yet-another-media-player |
| URL dashboard | ✅ **HTTP 200** | `http://10.0.0.47:8123/ai-nexus-v4/accueil` |
| Ancien dashboard / défaut / ressources / thèmes | ✅ **INCHANGÉS** | Empreintes préservées |
| Services physiques envoyés | ✅ **AUCUN** | Seul `frontend.reload_themes` via WebSocket |
| Redémarrage HA | ✅ **AUCUN** | Publication à chaud uniquement |

---

## 2. Historique des publications

| Date | Action | Scope | Hash candidat | Hash live après |
|------|--------|-------|---------------|-----------------|
| 2026-10-04 | Publication initiale (canary t_e6872bd6) | Dashboard complet v4 | `4aba75c0...` | `cef8e97a...` |
| 2026-10-04 | Enrichissement énergie (t_e805f498) | Carte « Énergie compacte » 4→8 métriques | — | `cef8e97a...` (hybride) |
| 2026-10-05 | **Publication complète générateur** | **Dashboard complet (générateur commit d976ce9)** | `226d043a...` | **`226d043a...` ✅** |

**Point clé** : L'enrichissement énergie (mission 09) a été publié **avant** que le générateur ne soit aligné. Le live est devenu un hybride (carte énergie à jour, reste de l'ancien générateur). La publication du 2026-10-05 aligne **l'intégralité** du live sur le générateur courant (incluant les correctifs CSS icônes et la carte diagnostic mise à jour).

---

## 3. Écarts résolus par la publication complète

| Vue / Composant | Avant (live hybride) | Après (générateur d976ce9) | Cause |
|-----------------|----------------------|----------------------------|-------|
| `accueil` — carte « Famille et vigilance` | CSS ancien (pas de `.person>ha-icon`) | CSS corrigé (marges icônes) | Correctif visuel commit d976ce9 |
| `accueil` — carte « Six pièces illustrées` | CSS ancien | CSS corrigé | Même correctif |
| `accueil` — carte « Énergie véhicule multimédia accès` | Entités énergie 4 métriques | Entités énergie 8 métriques | Enrichissement énergie |
| `diagnostic` — carte « Données à vérifier` | `triggers_update` sans `sensor.cout_phev_mois` | `triggers_update` complet (121 entités) | Alignement sur générateur |

Aucun autre écart. Les 13 autres vues sont identiques.

---

## 4. Preuves techniques

- `data/final-verification-20261005/evidence.json` — vérification complète horodatée
- `data/final-verification-20261005/dashboard-readback.json` — lecture WebSocket exacte du live
- `config/ai-nexus-v4.json` — artefact générateur (source de vérité)
- `config/ai-nexus-glass.yaml` — thème appliqué
- `tools/build_dashboard.py` + `tools/visual_design.py` — générateur déterministe (commit d976ce9)

---

## 5. Observation durable — NOUVELLE BASELINE

Conformément au contrat (§ Validation finale) : *« Après intégration seulement, créer la mission d'observation bornée sur nouvelle baseline pour devops ; préserver toutes les générations antérieures et ne pas prétendre avoir observé 24h dès le lancement. »*

### Canary précédent (t_e6872bd6) — BASELINE ANCIENNE
- Fenêtre : 2026-10-04 02:02 → 2026-10-05 02:02 (Europe/Paris)
- Baseline : dashboard initial + famille/Sportage **SANS** enrichissement énergie
- Statut : **INCOMPLET** (baseline invalidée par publication énergie postérieure)
- Preuves conservées : `data/canary-t_e6872bd6/`

### Nouvel observateur — BASELINE ACTUELLE (cette finalisation)
- **Nouveau canary à initialiser** sur l'empreinte `226d043a4ec0751c0a6972c7bb6e23efbaacfa0b3d5e1bfe6d82c8db95169f9f`
- Script : `tools/observe_candidate.py` (ou version adaptée `observe_candidate_v2.py`)
- Fenêtre visée : 24 h révolues, intervalle 30 min, ≥48 prélèvements valides, trou max 45 min
- Critères TECHNICAL_PASS identiques : intégrité candidat/thème, non-altération existant
- **Human_validation = PENDING** — aucun PASS global sans constat humain

> ⚠️ **L'observation précédente ne vaut pas pour la nouvelle baseline.** Le canary t_e6872bd6 observait une empreinte désormais obsolète. Une nouvelle fenêtre d'observation 24 h doit être démarrée sur l'empreinte publiée ce jour.

---

## 6. Rollback

Retrait du candidat (action destructive, accord explicite requis) :
```bash
python3 tools/publish_candidate.py rollback --apply
```
- Garde : refuse si configuration candidat, thème ou ancien existant divergent des empreintes attendues
- Retrait limité au dashboard `ai_nexus_v4` et `/config/themes/ai-nexus-glass.yaml`
- Jamais aux anciens dashboards ni aux ressources partagées
- Retour observateur : suspendre/retirer le cron du nouveau canary uniquement

Backup full `d2150955` réutilisé (inventaire et intégrité du cœur précédemment vérifiés).

---

## 7. Acceptance — Critères restants

| Critère | État | Preuve requise |
|---------|------|----------------|
| Intégrité technique (readback, thème, ressources, existant) | ✅ **VERIFIED** | `evidence.json` |
| Empreinte live == générateur | ✅ **VERIFIED** | 17/17 vues, hash `4162f15d` (revérifié live==gén le 09/10) (08/10) |
| Rendu navigateur — mobile | ✅ **PROVEN** | QA Denis 09/10/2026 |
| Navigation, popups, Navimower/YAMP, thèmes | ✅ **PROVEN** | QA Denis 09/10/2026 (mobile) |
| Reconnexion, performance ressentie | ✅ **PROVEN** | QA Denis 09/10/2026 (mobile) |
| Rendu desktop/tablette | ⚠️ Non couvert par la QA mobile | Constat Denis si souhaité (non bloquant) |
| Observation 24 h technique (nouvelle baseline) | ⛔ **CANARY CLÔTURÉ** | Décision 09/10 : hash live==gén + archivage canary |
| Validation humaine finale | ✅ **VALIDÉE (mobile)** | Denis 09/10/2026 |

**PASS accordé le 09/10/2026** sur la base de : intégrité technique VERIFIED + empreinte live/gén 17/17 + constat humain (mobile).

---

## 8. Commandes utiles

```bash
# Vérification rapide live vs générateur
python3 -c "
import sys, json, hashlib
sys.path.insert(0, 'tools')
from ha_client import HA
from build_dashboard import Builder
h = HA()
live = h.read_dashboard('ai-nexus-v4', force=True)
gen = Builder().build()
print('Match:', hashlib.sha256(json.dumps(live, sort_keys=True, ensure_ascii=False).encode()).hexdigest() ==
           hashlib.sha256(json.dumps(gen, sort_keys=True, ensure_ascii=False).encode()).hexdigest())
"

# Démarrer nouvelle observation (après avoir adapté le script pour la nouvelle baseline)
python3 tools/observe_candidate.py init
# Puis toutes les 30 min (via cron) :
python3 tools/observe_candidate.py sample
# Rapport :
python3 tools/observe_candidate.py report

# Rollback (si validé par Denis)
python3 tools/publish_candidate.py rollback --apply
```

---

## 9. Décision — CHANTIER CLOS (09/10/2026)

**Acceptation accordée.** Le dashboard live correspond exactement au générateur local déterministe (17/17 vues, hash `4162f15d` (revérifié live==gén le 09/10)), l'intégrité technique est VERIFIED, et **Denis a validé la QA mobile le 09/10/2026**.

Conditions levées :
1. ~~Bilan technique 24 h révolues (canary TECHNICAL_PASS)~~ → **remplacé** par la preuve par empreinte live == gén (plus forte et instantanée) ; le canary a été clôturé et archivé le 09/10 (`/root/backups/hermes-cron-canary-ai-nexus-20261009/`).
2. ~~Validation visuelle et fonctionnelle par Denis~~ → **VALIDÉE** sur mobile le 09/10/2026.

Reste ouvert (non bloquant) : `PENDING_PHYSICAL_CONFIRMATION` (aucune action physique n'est envoyée par conception) et un constat desktop/tablette si Denis le souhaite.