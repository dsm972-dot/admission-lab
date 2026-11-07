# V4 — publication candidate vérifiée

Tâche : t_dc479850. Publication effectuée le 4 octobre 2026 à 01:36 heure de Paris ; seconde lecture le 4 octobre à 01:39.

URL réelle : http://10.0.0.47:8123/ai-nexus-v4/accueil
Inscription : ai_nexus_v4, mode storage, admin uniquement, visible dans la barre latérale.

## Résultats réellement exécutés

- 32 tests unittest PASS ; compilation Python du nouvel exécuteur PASS.
- Préflight live : 17 vues, 109 références d'entités, services et capacités contrôlés.
- Archive full d2150955 existante réutilisée, <24 h lors du préflight ; inventaire et métadonnées TAR distants identiques à la preuve précédente, taille/mtime inchangés. Gzip Core précédemment vérifié. Aucun nouveau backup massif ni restauration.
- Nouveau thème AI Nexus Glass ajouté et relu via filesystem et frontend/get_themes.
- Dashboard exact sauvegardé via WebSocket authentifié et relu : égalité JSON et empreinte SHA-256 b512344afd89ea2dca95c0b96e92e5701b7ffbde9be58a3988749a09a50ea233.
- 5 ressources effectivement utilisées : toutes HTTP 200 JavaScript. URL dédiée HTTP 200 HTML ; ce contrôle ne constitue pas un rendu navigateur.
- Anciennes inscriptions/configurations, ancien dashboard par défaut, ressources, thèmes existants, configuration.yaml, préférences frontend et version Core inchangés selon snapshot prépublication et seconde lecture.
- Seul service administratif envoyé : frontend.reload_themes. Aucun actionneur, redémarrage, helper, mise à jour ou bascule par défaut.
- Rollback ciblé dry-run exécuté : cible inscription ai_nexus_v4 + seul fichier thème ajouté, hashes et invariantes vérifiés. Suppression réelle NON exécutée.

## Attention au contrôle baseline historique

`tools/check_baseline.py` retourne `legacy_unchanged=false` après publication car il compare la liste TOTALE des dashboards/configurations à l'état sans V4. Ce n'est pas une preuve d'altération de l'ancien : comparaison supplémentaire exécutée, ancienne liste de configurations identique après exclusion exacte de ai-nexus-v4 ; hashes ressources et défaut identiques. Le script dédié vérifie séparément toutes les anciennes inscriptions, anciens hashes et préférences.

Deux 404 historiques restent inchangées : `/webrtc/webrtc-camera.js?v=v3.6.0` et `/hacsfiles/mushroom-cards/mushroom.js`. Double déclaration card-mod historique également conservée. Aucun de ces éléments n'est requis par les cinq cartes custom utilisées dans V4. Ne pas les nettoyer hors mandat.

## Ce qui reste en attente

Validation humaine et QA visuelle native Denis : PENDING_DENIS.
Usage parallèle 24–48 h, observations prolongées : PENDING_CANARY.
Effets des commandes physiques : PENDING_PHYSICAL_CONFIRMATION.
Rendu mobile/tablette, popups, console, performance et reconnexion ne sont pas attestés par la publication REST/WS. La totalité du projet n'est donc pas déclarée terminée et le défaut reste l'ancien dashboard.

Suite précréée : t_e6872bd6, libérée par clôture de cette phase de publication ; aucune nouvelle lane dupliquée.

## Preuves et rollback

- data/candidate-publication/before.json — snapshot avant write.
- data/candidate-publication/created.json — identité exacte créée.
- data/candidate-publication/readback.json — dernière vérification.
- data/candidate-publication/dashboard-readback.json — configuration effectivement relue.
- data/candidate-publication/rollback-check.json — dry-run sans suppression.
- docs/CANDIDATE_PUBLICATION.md — périmètre et procédure rollback.

Commande de vérification read-only : `python3 tools/publish_candidate.py verify`.
Commande de simulation rollback : `python3 tools/publish_candidate.py rollback`.
Rollback réel seulement si autorisé/instabilité démontrée : `python3 tools/publish_candidate.py rollback --apply`.

Aucun commit/reset/clean/stash effectué ; artefacts non suivis préexistants du dépôt dédié conservés. Les rapports locaux plus anciens indiquant « non déployé » restent historiques ; ce document décrit la publication sans modifier les travaux d'autres lanes.
