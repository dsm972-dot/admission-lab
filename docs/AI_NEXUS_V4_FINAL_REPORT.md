# AI Nexus V4 — livraison candidate vérifiée, acceptation non clôturée

État : PUBLISHED_CANDIDATE_VERIFIED. Observation technique 24 h EN COURS ; QA humaine PENDING. Le projet n'est PAS déclaré entièrement terminé.

## Accès HA réel

http://10.0.0.47:8123/ai-nexus-v4/accueil

Dashboard parallèle storage « AI Nexus Home V4 », administrateur requis, visible dans la barre latérale. 17 vues. Thème AI Nexus Glass présent. La publication a déjà eu lieu : les mentions anciennes « déploiement non effectué » étaient périmées.

## Contrôles réellement exécutés le 4 octobre 2026

- Readback REST/WebSocket et lecture SSH : configuration du candidat exactement égale à l'artefact local, thème sur disque et thème chargé vérifiés.
- Empreintes ancien dashboard, enregistrements existants, ressources partagées, thèmes existants, préférences et configuration inchangées. Version HA inchangée.
- Les 5 ressources utilisées répondent HTTP 200 JavaScript ; URL HA HTTP 200 HTML. Cela ne prouve PAS le rendu ni le fonctionnement des cartes en navigateur.
- Mapping live : 109 références présentes, aucune référence manquante. Services et capacités contrôlés par validate() avec états et services HA actuels. Aucun service physique envoyé.
- 16 références sont actuellement unknown/unavailable : détail data/canary-t_e6872bd6/live-mapping.json. Ce n'est pas une disparition d'entité ni une preuve de défaut V4. Yeelight cuisine coupée au mur = état normal ; aucune correction hors périmètre.
- Suite complète : 57 tests, 0 échec, 0 erreur. Comprend garde des services, génération, serveur navigateur isolé, publication/rollback et observateur/runner.
- Rollback ciblé exécuté en DRY-RUN uniquement. Le candidat reste publié. Aucun actionneur, redémarrage ni bascule par défaut durant cette finalisation.

## Observation durable réelle

Fenêtre : 4 octobre 2026 02:02:45 → 5 octobre 2026 02:02:45, Europe/Paris (UTC : 00:02:45 → 00:02:45).

Cron 3d91e89a812f : toutes les 30 minutes, 49 exécutions au maximum, sans agent/LLM. Script ai_nexus_v4_canary_t_e6872bd6.py ; travail ancré dans le projet. Le scheduler a exécuté un premier passage réel : execution_success=true, last_status=ok. Succès intermédiaire silencieux ; anomalies et bilan final adressés à Telegram. Un succès silencieux n'est pas une preuve de livraison de message, et encore moins de lecture humaine.

TECHNICAL_PASS exige 24 h réellement révolues, au moins 48 prélèvements valides, zéro échec et aucun trou >45 minutes. Aucun PASS global n'est produit ; human_validation reste PENDING. Une fenêtre finie, une observation absente ou un délai dépassé ne sont jamais transformés artificiellement en succès.

Cet observateur couvre disponibilité des lectures, intégrité candidat/thème et non-altération de l'existant. Il ne mesure ni rendu/navigateur, ni latence visuelle, ni console frontend, ni usage utilisateur, ni effets physiques. Les horodatages n'attestent pas une observation humaine continue. Le rapport évolutif est docs/AI_NEXUS_V4_CANARY_REPORT.md ; traces dans data/canary-t_e6872bd6/.

## Nettoyage et rollback

Le vieux watchdog de processus 4b1844f19dd6 a été sauvegardé, suspendu puis retiré APRÈS remplacement testé. Script et état obsolètes retirés ; copies conservées dans data/canary-t_e6872bd6/retired-watchdog/ et inventaire cron-replacement-before.json. Le nouveau cron est borné, pas un surveillant permanent orphelin.

Retrait du candidat (action destructive, accord nécessaire) : python3 tools/publish_candidate.py rollback --apply. Le dry-run sans --apply ne supprime rien. Garde : refus si configuration du candidat, thème ou ancien existant divergent des empreintes attendues. Retrait limité au dashboard ai_nexus_v4 et /config/themes/ai-nexus-glass.yaml ; jamais aux anciens dashboards ni aux ressources partagées. Retour observateur : suspendre/retirer uniquement 3d91e89a812f via outil cron et retirer son wrapper ; conserver les traces. Recréation du vieux watchdog possible depuis les copies et l'inventaire si expressément nécessaire, déconseillée une fois le travail d'implémentation fini.

Backup full d2150955 réutilisé : inventaire et intégrité du cœur précédemment vérifiés, voir AI_NEXUS_V4_BACKUP_CHECK.md et CANDIDATE_PUBLICATION.md. Aucune nouvelle grosse sauvegarde ; aucune restauration intégrale ni intégrité de tous les addons prétendue.

## Anciennes lanes : aucun faux DONE

Les 12 lanes auto-décomposées ont été examinées : 2 blocked, 2 ready, 8 todo au contrôle du 4 octobre. Aucun statut de ces cartes n'a été artificiellement clôturé. Les preuves existantes sont consolidées ici, pas remplacées par 12 nouveaux travaux.

Les deux lanes devops dépôt/backup ont réellement planté deux fois avant le travail : le profil demandait une configuration fournisseur/modèle via assistant interactif indisponible au worker. Le profil existe aujourd'hui, mais une liste de profils ne prouve pas sa réparation. Les lanes local/jarvis suivantes restent dépendantes de ce graphe historique. Dépôt, backup, génération, docs et publication disposent déjà d'artefacts dans ce workspace ; cela ne valide pas leurs critères non mesurés (rendu réel, acceptation, historique de commits). Aucun profil tiers modifié et aucun nouveau commit effectué dans cette finalisation.

## Acceptation encore ouverte

Denis vérifie directement dans HA : rendu desktop/téléphone/tablette, navigation et popups, Navimower/YAMP, thèmes clair/sombre, reconnexion et performance ressentie. Sans son constat, PENDING_DENIS reste explicite. Une ancienne phrase « Je valide » antérieure à la publication ne vaut pas inspection post-publication. L'absence d'accès au coffre/navigateur de travail ne déclenche plus de blocage login répété.

Les erreurs critiques navigateur ne sont pas mesurées : jamais « zéro » par défaut. Les tests Chromium isolés (85 rendus, 17 vues, 5 tailles) sont documentés dans AI_NEXUS_V4_LOCAL_BROWSER_QA.md, mais ne constituent pas QA production ; limites YAMP/contexte/layout conservées. Xiaomi Map Sami sans source = repli explicite ; températures cuisine/bureau non inventées. Deux ressources HA existantes 404 et doublon card-mod documentés, non corrigés ; V4 ne dépend pas des ressources 404.

La livraison technique et l'installation de l'observation sont terminées. Leur acceptation reste en revue, conditionnée au bilan technique 24 h ET au constat humain. Aucun PASS total avant ces deux preuves.

## Preuves principales

- data/candidate-publication/readback.json, dashboard-readback.json, before.json, rollback-check.json.
- data/canary-t_e6872bd6/live-mapping.json, state.json, observations.jsonl, cron-replacement-before.json et copies retired-watchdog/.
- docs/AI_NEXUS_V4_CANARY_REPORT.md, CANDIDATE_PUBLICATION_RESULT.md, AI_NEXUS_V4_BACKUP_CHECK.md, AI_NEXUS_V4_LOCAL_BROWSER_QA.md.
- tools/observe_candidate.py, tools/canary_runner.py, tests/test_observe_candidate.py et tests/test_canary_runner.py.
