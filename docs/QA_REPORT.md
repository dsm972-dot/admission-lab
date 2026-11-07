# QA V4 — rapport provisoire

Les résultats locaux proviennent de `python3 -m unittest discover -s tests -v`
(journal : `logs/tests.log`) et de `python3 tools/build_dashboard.py`.
Les 25 tests exécutent notamment les templates JavaScript dans Node. Ce n’est pas
une session navigateur Home Assistant. Aucun état réel n’a été simulé sur HA.

| Test | Appareil / environnement | Résultat | Erreur / limite | Correction / suite | Validé |
|---|---|---|---|---|---|
| 17 vues, sections, entités | Python local | LOCAL_PASS | Instantanés uniquement | Comparer au HA cible avant déploiement | Local |
| Services, domaines, capacités | Python + services.json | LOCAL_PASS | Pas de commande exécutée | Vérifier paramètres et effets réels lors du parcours physique | Local |
| Maintien et confirmation | Analyse récursive | LOCAL_PASS | Contrôles internes cartes héritées hors preuve | Audit navigateur | Local |
| Hashes des 6 pièces | Python | LOCAL_PASS | 6 popups dans chacune des 2 vues | Vérifier ouverture/fermeture | Local |
| Navigation entre vues | Python | LOCAL_PASS | Routes internes existantes | Tester rail desktop et barre mobile | Local |
| Matrice on/off/unknown/unavailable | Node | LOCAL_PASS | Sans DOM | Rejouer dans le navigateur | Local |
| Contacts, branchement, charge | Node | LOCAL_PASS | Classes de capteur déclarées | Vérifier libellés sur appareil | Local |
| Moyenne, zéro, NaN, données absentes | Node | LOCAL_PASS | Six capteurs vérifiés | Aucun helper ajouté | Local |
| Présence / absence / alarme | Node | LOCAL_PASS | Cohérence partielle, pas audit global de sécurité | Revue famille | Local |
| JSON/YAML, reconstruction identique | Python | LOCAL_PASS | Comparaison octet par octet | Aucun | Local |
| Cartes Navimow et YAMP | Python | LOCAL_PASS | Copie exacte d’une config avec entités connues | Vérifier rendu et commandes internes | Local |
| Xiaomi Map | Sources locales | LOCAL_PASS | Aucune configuration trouvée | Repli affiché, intégration avancée en attente | Repli |
| Thème clair/sombre | Python | LOCAL_PASS | Deux modes présents seulement | Contraste et lisibilité à vérifier | Structure |
| Desktop 1920×1080 et 2560×1440 | Non exécuté | PENDING_BROWSER_QA | Pas de navigateur HA utilisé | Rendu, scroll, navigation, console | Non |
| Mobile S25 portrait/paysage | Non exécuté | PENDING_BROWSER_QA | Sept liens navbar à examiner | Lisibilité, débordement, cibles ≥44 px | Non |
| Tablette 1280×800 | Non exécuté | PENDING_BROWSER_QA | Responsive non observé | Vérifier les sections | Non |
| Popups | Non exécuté | PENDING_BROWSER_QA | Schéma historique ne prouve pas le fonctionnement | Ouvrir/fermer les 6, vérifier le scroll et l’actualisation | Non |
| Sami, Navimow, voiture | Non exécuté | PENDING_BROWSER_QA | Sommeil et reprise non observés | Disponibilité, télémétrie, cartes | Non |
| Sécurité, climat, énergie, multimédia | Non exécuté | PENDING_BROWSER_QA | Fonctionnement HA non observé | Plus de statut brut, interactions prévues | Non |
| Ressources HTTP et console | Non exécuté | PENDING_BROWSER_QA | Déclaration locale ≠ chargement réussi | Contrôler 404, JS, WebSocket | Non |
| Performance | Non exécuté | PENDING_BROWSER_QA | Aucun flux accueil, zéro graphe ; aucune mesure chronométrée | Comparer à l’ancien sur même réseau/appareil, seuil indicatif 15 % | Non |
| Reconnexion | Non exécuté | PENDING_BROWSER_QA | Aucune coupure Wi-Fi simulée | Rafraîchir, reconnecter, rouvrir l’app après plusieurs heures | Non |
| Actions et effets physiques | Non exécuté | PENDING_PHYSICAL_CONFIRMATION | Aucune commande HA envoyée | Une action à la fois, présence physique pour actions critiques | Non |
| Usage parallèle 24–48 h | Non exécuté | PENDING_CANARY | Aucun déploiement | Ancien reste par défaut ; validation explicite avant bascule | Non |

Écarts assumés : météo courante sans prévisions horaires, pas d’images de pièces ni de
jauge graphique ; pas de commande véhicule ni désarmement Alarmo ; Xiaomi Map en repli.
Les états textuels propres aux intégrations peuvent nécessiter des traductions après QA.
Diagnostic mesure uniquement l’indisponibilité des entités suivies ; il ne prétend pas
lire la console navigateur ou détecter les erreurs réseau.

L’export est prêt pour revue locale. La recette visuelle, fonctionnelle physique et
le canary restent ouverts ; ce rapport ne donne aucune autorisation de déploiement.
