# AI Nexus V4 — QA navigateur isolée, 4 octobre 2026

Statut : AVANCÉE LOCALE VÉRIFIÉE, PROJET NON TERMINÉ.

## Exécution réelle
- 32 tests unitaires passent ; syntaxe JavaScript validée par Node.
- Chromium exécuté sur les 17 vues, dans 5 tailles : 1920×1080, 2560×1440, 412×915, 915×412 et 1280×800.
- 85 échantillons et captures, plus une capture du thème sombre. Comptage attendu/réel vérifié dans matrix.json.
- Les 5 ressources V4 publiques sont chargées : button-card, Bubble Card, navbar-card, Navimower et YAMP.
- Aucun appel réseau de mutation. Les tests prouvent le refus des routes API/auth et des méthodes POST/PUT/DELETE/PATCH avant accès amont.
- Premier chargement isolé mesuré : 5,376 s, attente de stabilisation comprise ; ce n'est pas un benchmark HA connecté.

## Limites mesurées
Le moteur utilise les vraies cartes et les instantanés HA, mais le layout est une approximation CSS. Un adaptateur de démarrage local évite l'entrée d'authentification ; il ne crée aucune session HA. Un contexte Lovelace de compatibilité est fourni aux templates button-card.
Une erreur unique est observée : YAMP ne peut pas résoudre Music Assistant, car le contexte isolé ne fournit pas callApi. Ce résultat ne prouve pas une panne YAMP en production.
Navigation native, popups, reconnexion, comparaison à l'ancien dashboard et performances connectées restent PENDING_BROWSER_QA. Canary non commencé. Actions physiques PENDING_PHYSICAL_CONFIRMATION.
Les tailles téléphone sont des proxys CSS, pas un test du S25 Ultra physique.

## Sécurité et état HA
Relecture live à 23:09:29 UTC le 3 octobre : anciens dashboards et ressources inchangés, dashboard V4 absent. Aucun déploiement HA effectué.
Les paramètres des URL réseau sont supprimés avant écriture des preuves. Audit du JSON livré : zéro affectation de jeton dans les URL. Les instantanés privés ne sont pas inclus dans le ZIP.

## Blocage confirmé à nouveau
Le navigateur de travail arrive à la connexion HA. Aucun login de coffre ne correspond à http://10.0.0.47:8123 ; Bitwarden est indisponible dans cette session. La tentative de sauvegarde sécurisée du login retourne prompt_unavailable en mode headless.
Reprise nécessaire depuis une session interactive : connecter ce navigateur à HA, ou enregistrer un login pour cette origine exacte dans le coffre. Ne jamais fournir de mot de passe dans le chat.

## Reproduction et preuves
python3 -m unittest discover -s tests -v
python3 tools/probe_local_browser.py
Le probe démarre son serveur sur 127.0.0.1:8768 et l'arrête en fin d'exécution.
Preuves : evidence/local-browser/matrix.json et captures énumérées dans ses samples. Archive locale : evidence/local-browser/local-qa-evidence.zip.
Les 85 essais locaux ne sont pas déclarés PASS de QA production. Déploiement parallèle et clôture de la tâche restent interdits tant que les gates ne sont pas prouvés.
