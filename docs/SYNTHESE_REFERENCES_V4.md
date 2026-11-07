# AI Nexus Home V4 — Note de synthèse des documents de référence

Tâche : `t_4c766a31` (lecture intégrale + synthèse).
Date : 11/10/2026. Workspace : `/root/workspace/maison/ai-nexus-home-v4`.

## 0. Sources lues (preuves)

| # | Document | Chemin |
|---|---|---|
| 1 | Mandat d'exécution autonome (PRIORITAIRE) | `/root/.hermes/webui/attachments/838f6e7e7697/prompt_hermes_execution_autonome_ai_nexus_v4.md` |
| 2 | Prompt construction V4 | `…/prompt_hermes_ai_nexus_home_v4.md` |
| 3 | Prompt construction V4 (copie) | `…/prompt_hermes_ai_nexus_home_v4-1.md` — **identique octet à octet** avec #2 (vérifié `cmp`) |
| 4 | Addendum sécurité & QA | `…/addendum_securite_qa_ai_nexus_v4.md` |
| 5 | Maquette validée (référence visuelle) | `…/tableau_de_bord_domotique_ai_nexus_avec_sportage.png` (analysée en vision) |
| — | AGENTS.md racine | `/root/workspace/AGENTS.md` |
| — | AGENTS.md domaine maison | `/root/workspace/maison/AGENTS.md` |
| — | Rapport préflight | chemin annoncé `/root/workspace/tmp/ai-nexus-v4-preflight/AI_NEXUS_V4_QA_REPORT.md` **n'existe plus (tmp purgé)**. Équivalents retrouvés dans le dépôt : `docs/QA_REPORT.md` (rapport QA provisoire, tableau des gates), `docs/AI_NEXUS_V4_QA_REPORT.md` (renvoi + état PENDING), `docs/AI_NEXUS_V4_BACKUP_CHECK.md` (vérification backup), `docs/CANDIDATE_PUBLICATION_RESULT.md` (« préflight live » 17 vues / 109 références). |

Ordre de priorité des documents en cas de contradiction :
**1. `prompt_hermes_execution_autonome…` (dernier mandat, lève les validations intermédiaires) → 2. `addendum_securite_qa…` (gates et procédures) → 3. `prompt_hermes_ai_nexus_home_v4` (spec de construction) → 4. AGENTS.md (règles maison/infra)**.

## 1. Exigences du projet (ce qu'il faut livrer)

- **Dashboard parallèle** `AI Nexus Home V4` (id `ai_nexus_v4`), en plus de l'existant, **jamais** en remplacement.
- **Thème dédié « AI Nexus Glass »** : glassmorphism léger, fond clair le jour / graphite-bleu la nuit, radius 18–24 px, ombres faibles, accent bleu-cyan, vert=OK, orange=attention, rouge=critique, violet=scènes/confort.
- **15 vues livrables** (contrat `t_ac30edc5`) : Accueil, Pièces (+ popups), Confort, Sécurité, Énergie, Sami, Navimow, Sportage, Multimédia, Bureau, Lecture Zen, Jardin, Recharge, Café, Diagnostic/Admin.
  Navigation maquette = rail gauche : Accueil · Pièces · Équipements · Confort · Sécurité · Énergie · Plus (sous-menu) — la publication live contient 17 vues (les 15 + Équipements + agrégat).
- **Accueil** : header (Bonjour Denis, date, météo, nb présents, Alarmo, serrure, mode maison) + détection d'incohérences (ex. 4 présents + mode Absent, Alarmo armé + porte déverrouillée), 4 cartes famille (Denis/Laura/Émile/Maddy : présence, batterie, Wi-Fi, avatar), 6 cartes pièces avec popups Bubble Card, climat (moyenne + 6 mini-cartes ApexCharts), sécurité, Sami, Navimow, Sportage, énergie, multimédia (YAMP), actions rapides.
- **Stack imposée (déjà installée, pas de nouvelle custom card sans nécessité)** : Bubble Card, Mushroom, Button Card, Card-mod, Auto-Entities, ApexCharts, Stack-in-card, Navbar Card, Yet Another Media Player, Advanced Camera Card, Xiaomi Vacuum Map Card, Navimower Map Card. Browser Mod / Layout Card exclus sauf blocage réel.
- **Données réelles uniquement** : la maquette est la référence graphique mais **les chiffres de l'image ne sont jamais recopiés** ; entités vérifiées via `/api/states`, `supported_features` compatible, aucun entity_id cassé repris de l'ancien Lovelace.
- **7 fichiers de documentation obligatoires** (préfixe exact `AI_NEXUS_V4_`) : ARCHITECTURE, CHANGELOG, ENTITY_MAPPING, DECISIONS, BACKUP_CHECK, QA_REPORT, FINAL_REPORT (tous présents dans `docs/`).

## 2. Contraintes (les interdits)

1. **⛔ Contrôle physique HA INTERDIT** (règle AGENTS.md maison, confirmée par le mandat) : aucune commande lumières/volets/switches/TTS/notifs/serrures/garage/alarme/véhicule. WebSocket + sensors **lecture seule**. Seule exception écrite : écriture configuration dashboard/thème, backup complet supplémentaire, déploiement V4 parallèle.
   → toute action sensible : configurée avec confirmation (`hold_action`/double étape), test arrêté au point avant l'action et marqué **`PENDING_PHYSICAL_CONFIRMATION`** ; on poursuit le reste.
2. **Ancien dashboard intact** : pas de stash/commit/reset/clean/suppression dans le dépôt HA existant, pas de modification des 19 vues de `lovelace`, pas de suppression de ressource HACS, **aucune bascule automatique** du dashboard par défaut (bascule = décision manuelle de Denis après QA + canary).
3. **Secrets** : jamais exposés (tokens, mots de passe, clés) ; `.gitignore` durci (`.env*`, `*.pem`, `*.key`, credentials…) — vérifié aucun secret versionné.
4. **Gel des versions** pendant toute la construction V4 : pas de maj HA Core / HACS / custom cards / thèmes / intégrations.
5. **Pas de redémarrage HA** sans nécessité absolue + impact évalué.
6. **États dégradés traités élégamment** : `unknown`/`unavailable` jamais affichés bruts à la famille (masquage + alerte seulement si anormal + détails dans la vue Diagnostic). Cas normaux connus : Yeelight coupées au mur, Navimow en pause (dizaines d'entités `unavailable`), doublons media_player, 2×404 historiques (`/webrtc/webrtc-camera.js`, `/hacsfiles/mushroom-cards/mushroom.js`) et doublon card-mod **conservés hors périmètre**.
7. **Aucune validation intermédiaire requise** (mandat autonome) : appliquer la meilleure recommandation, JEV pour arbitrer (priorités : stabilité HA > sécurité > fidélité maquette > UX > perf > maintenabilité > simplicité > nb de dépendances), documenter dans `AI_NEXUS_V4_DECISIONS.md`.
8. **HARD STOP** (seuls motifs d'arrêt) : backup impossible/inexploitable ; risque irréversible sur l'existant ; secret à exposer ; action physique risquée indispensable ; instabilité HA non récupérable (→ rollback puis arrêt).

## 3. Critères de validation

### Gate 0 — autorisation de démarrer (auto-PASS si prouvé)
- Backup complet récent (< 24 h, lisible, non vide) — **vérifié en vrai** (metadata seule insuffisante) ;
- Dépôt Git V4 dédié + tag/commit `pre-ai-nexus-v4`, arbre propre ;
- Versions gelées ; mapping des entités validé ; maquette disponible ; secrets protégés ; ressources identifiées ; dashboard existant intact ; workspace prêt ;
- Aucune action réelle déclenchée pendant l'audit.

### Backup & rollback
- Backup supplémentaire **sans jamais supprimer** l'existant. Réalisé : full `d2150955` « AI Nexus V4 pre-deploiement 20261003 », 381 062 154 240 octets, gzip Core contrôlé jusqu'à EOF (CRC OK) ; limites honnêtes documentées dans `AI_NEXUS_V4_BACKUP_CHECK.md` (pas de restauration testée, pas de CRC des 26 addons).
- Export config préalable : `backups/frontend-baseline-config.tar` + exports Lovelace/ressources dans `data/` (hors git, privés).
- **Rollback** déclenché si : dashboard actuel modifié involontairement, instabilité HA, JS bloquant, navigation cassée, action critique non prévue, chute perf > ~15 %, ressource HACS cassée, perte d'accès. Procédure : retirer V4 uniquement → commit précédent → backups → vérifier l'ancien → documenter. Cible précise : `python3 tools/publish_candidate.py rollback [--apply]` (dry-run déjà exécuté, suppression réelle NON exécutée).

### Tests navigateur (QA)
- Desktop 1920×1080 (+2560×1440 si dispo), mobile S25 Ultra portrait/paysage, tablette ~1280×800 ;
- Zéro chevauchement, zéro scroll horizontal non voulu, cibles tactiles ≥ 44 px, popups dans l'écran, navigation utilisable ;
- Zéro erreur JS bloquante, zéro ressource 404 utilisée par V4, aucun entity_id inexistant, pas de carte « Unknown/Unavailable » brute ;
- Popups (ouverture/fermeture/scroll/état actualisé), reconnexion (refresh, Wi-Fi, WebSocket, app mobile, retour après plusieurs h) ;
- Performance : V4 pas sensiblement plus lent que l'existant (seuil indicatif 15 %, même appareil/réseau) ;
- Matrice d'états : jour/nuit, maison/absent, présent/absent, batterie, porte, garage, Alarmo, lumières, volets, média, Sami, Navimow, voiture, caméras ;
- Rapport QA tabulaire obligatoire `AI_NEXUS_V4_QA_REPORT.md` (Test | Appareil | Résultat | Erreur | Correction | Validé).

### Gates de phase (addendum)
- **GATE 1 — Isolation** : dashboard actuel identique avant/après, aucune vue/ressource modifiée, V4 accessible par URL dédiée, HA opérationnel.
- **GATE 2 — Accueil** : critères QA ci-dessus + validation visuelle Denis (le mandat autonome retire les validations intermédiaires, la validation finale Denis reste).
- **Phase 1 Isolation** : URL dédiée, pas de défaut, visibilité admin, suppression de V4 sans impact sur l'ancien.
- **Canary** : V4 en parallèle 24–48 h minimum, ancien reste par défaut, bascule = validation explicite Denis après contrôle visuel + QA + rollback confirmé.
- **Redémarrage d'une phase si gate échoué** : arrêter, documenter l'écart, revenir en arrière si besoin, demander validation avant correction risquée.

## 4. État actuel du projet (contexte pour les tâches filles)

- Dépôt Git dédié sain : `/root/workspace/maison/ai-nexus-home-v4` (commit README `7957865`, `.gitignore` durci, aucun secret tracké).
- **Publication candidate EFFECTUÉE** le 04/10 01:36 Paris : `http://10.0.0.47:8123/ai-nexus-v4/accueil`, inscription `ai_nexus_v4` admin only, thème AI Nexus Glass chargé, 17 vues / 109 références contrôlées, 5 ressources V4 HTTP 200, ancien dashboard + défaut + ressources inchangés (`docs/CANDIDATE_PUBLICATION_RESULT.md`, preuves `data/candidate-publication/`).
- Tests : 32 unittest PASS ; QA locale Chromium 85 rendus (17 vues × 5 tailles) **non équivalente** à une QA connectée (`docs/AI_NEXUS_V4_LOCAL_BROWSER_QA.md`).
- **Encore ouverts** : `PENDING_DENIS` (validation visuelle), `PENDING_BROWSER_QA` (QA navigateur connectée — bloquée : login HA absent du coffre, headless), `PENDING_CANARY` (24–48 h), `PENDING_PHYSICAL_CONFIRMATION`.
- Bug connu corrigé à ne pas régresser : marge des icônes (button-card `:not(ha-state-icon) ha-icon{margin:auto}`), bandeau hero + 6 pièces (commit `690e0d9`), sections PHEV voiture/recharge (`099b164`), énergie enrichie 4→8 métriques (`d976ce9`).
- Le preflight annoncé du mandat (« ne prouve pas l'intégrité de l'archive ») a été levé par la vérification réelle de `d2150955` (voir §3).

## 5. Points d'attention pour les tâches filles

- **`t_7d4f8f1e` (thème AI Nexus Glass)** : le thème existe déjà (`config/ai-nexus-glass.yaml`, publié et relu via `frontend/get_themes`). Repartir de l'existant, ne pas dupliquer ; valider couleurs/espacements contre la maquette, garder variables dark/light et variables unavailable/unknown.
- Respecter le périmètre d'écriture autorisé : **dashboard + thème uniquement**, tout le reste lecture seule.
- Skills à charger selon le mandat parent : `ha-dashboard-management`, `ha-websocket-econome`, `homeassistant`, `codex-orchestration`, `image-analysis` (maquette), `jev-system-one` (arbitrages), `hermes-audio-reports`.
- Brief `codex exec` systématique pour le dev (skill `codex-orchestration`), revue + tests Hermes avant commit.
