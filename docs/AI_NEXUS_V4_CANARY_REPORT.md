# AI Nexus V4 — canary t_e6872bd6

Statut technique : IN_PROGRESS.

Fenêtre UTC : 2026-10-04T00:02:45.537789Z → 2026-10-05T00:02:45.537789Z. Intervalle prévu : 30 min.

Prélèvements : 43 ; valides : 19 ; échecs : 24. Trou maximal, bornes incluses : 744.041 min (jusqu'à maintenant si en cours).

TECHNICAL_PASS exige 24 h révolues, au moins 48 prélèvements, aucun échec et aucun trou supérieur à 45 min.

human_validation=PENDING. Aucun PASS global. Rendu navigateur et usage réel : NON PROUVÉS. Le readback technique ne remplace pas la QA humaine.

## 2026-10-04 — canary 2 (t_61e35cc3)

Cause racine du statut TECHNIQUEURÉEL du canary 1 : `publish_candidate.py verify`
lit `data/candidate-publication/`, répertoire supprimé lors de la republication
Famille + Sportage du 2026-10-04. Résultat : `FileNotFoundError` converti en
`VERIFY_EXIT_NONZERO` à chaque échantillon (24 échecs consécutifs). Le défaut
n'était pas une dérive de dashboard mais une référence de ligne de base périmée.

Réponse : seconde génération d'observation, sans toucher au journal gen 1.
- `tools/verify_family_vehicle_light.py` : vérification LECTURE SEULE du readback
  famille/véhicule (candidat publié = accueil publié, ancien et défaut inchangés,
  ressources et registre inchangés, version core inchangée). Aucun navigateur,
  aucun rendu, ~0,2 s par exécution.
- `tools/observe_candidate_v2.py` : `FamilyVehicleObserver(Observer)`, fenêtre
  24 h, intervalle 30 min, statut `FAMILY_VEHICLE_PUBLISHED_READBACK_VERIFIED`.
- `observe_candidate.py` rendu générique (attributs de classe) + correction d'une
  erreur de concaténation f-string dans `markdown()` qui empêchait le rapport gen 1
  de s'exécuter.
- Cron : `a088250f4937` créé et validé par un run réel (échantillon écrit,
  `Last run ok`), puis `3d91e89a812f` retiré. Un seul cron Nexus actif, aucun orphelin.

Preuves : `data/canary-t_61e35cc3/` (state, observations.jsonl, rapport de clôture),
`data/canary-t_e6872bd6/cron-at-retirement.txt` et `final-report-at-retirement.md`.

Honnêteté du statut : rendu navigateur NON PROUVÉ, usage réel NON PROUVÉ,
validation humaine PENDING. TECHNICAL_PASS exige 24 h révolues, ≥ 48 prélèvements,
zéro échec et aucun trou > 45 min. Aucun PASS global n'est produit.
