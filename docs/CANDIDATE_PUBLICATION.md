# Publication candidate V4 — périmètre et rollback

Tâche t_dc479850. La nouvelle instruction de Denis « Continue je valide sur Home assistant » autorise la publication parallèle et transfère la recette visuelle native à Denis. Elle ne constitue pas un résultat de recette et n'autorise ni bascule par défaut ni action physique. Les anciennes gates visuelles restent PENDING, pas PASS.

## Avant write

- Artefacts existants `config/ai-nexus-v4.{json,yaml}` utilisés sans régénération.
- Snapshot `data/candidate-publication/before.json` : ressources complètes, inscriptions dashboards, thèmes existants, hashes des anciennes configs et du défaut, hashes configuration.yaml et préférences frontend, version Core, hashes candidate/theme.
- Archive full `d2150955` réutilisée : inventaire TAR distant et métadonnées comparés à `data/backup_verified.json`, taille/mtime inchangés, récence inférieure à 24 h. Le gzip Core avait été vérifié ; pas de restauration ni de vérification intégrale des autres archives prétendue.
- 109 références d'entités validées sur états/services/capacités live ; 5 ressources utilisées accessibles HTTP 200 JavaScript.

## Writes strictement limités

1. Créer le nouveau fichier `/config/themes/ai-nexus-glass.yaml`, refus d'écraser un fichier existant.
2. Recharger les thèmes par `frontend.reload_themes` uniquement.
3. Créer le dashboard storage séparé `ai-nexus-v4`, admin uniquement, visible dans la barre latérale.
4. Sauvegarder le JSON candidate exact par WebSocket officiel.
5. Relire la cible et vérifier inscription, JSON, thème, ressources, anciens hashes et préférences.

Aucun package, addon, resource frontend ou ancien dashboard modifié. Aucun redémarrage, commande lumière/volet/serrure/alarme/véhicule, helper ni abonnement global state_changed. Aucun nouveau backup massif. Aucun commit/reset/clean automatique dans le dépôt partagé.

## Rollback ciblé prêt avant publication

Depuis `/root/workspace/maison/ai-nexus-home-v4` :

    python3 tools/publish_candidate.py rollback

Ce dry-run vérifie avant toute suppression les hashes candidate/thème, l'inscription créée et les anciennes empreintes. Il affiche les cibles sans modification.

Uniquement sur décision explicite de rollback ou instabilité démontrée conforme au mandat :

    python3 tools/publish_candidate.py rollback --apply

Retire seulement l'inscription candidate identifiée dans `data/candidate-publication/created.json` et le fichier de thème ajouté, puis recharge les thèmes et relit toutes les invariantes. Toute modification concurrente détectée fait refuser le rollback automatisé. Ne supprime aucun autre fichier, thème, ressource, cron ou dashboard. Si publication interrompue après création d'une inscription vide, ne pas relancer publish à l'aveugle : identifier la cible via created.json, puis inspecter et retirer uniquement cette candidate si nécessaire.

## États ouverts

Rendu HA natif, mobile/tablette, popups, console, reconnexion, performance : PENDING_DENIS. Canary d'usage 24–48 h : PENDING (t_e6872bd6). Actions physiques : PENDING_PHYSICAL_CONFIRMATION. Ces limites ne bloquent pas la publication candidate demandée ; elles interdisent une clôture globale et une bascule par défaut.

Les résultats réels de publication seront dans `data/candidate-publication/readback.json` et `dashboard-readback.json`. Les rapports antérieurs de construction non déployée sont historiques, pas preuve de l'état actuel.
