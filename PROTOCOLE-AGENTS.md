# Protocole de salle — notes typées, pas un chat

Statut : contrat écrit le 14 novembre 2026. Cette page n'active rien.
Dépôt d'essai : `dsm972-dot/admission-lab`.
Récepteur : inchangé. Mode observation. Aucune réponse automatique. Aucune fusion.

Cette page dit comment trois rôles peuvent faire évoluer un sujet.
Elle ne branche aucun robot, ne crée aucun ticket, et ne change pas la politique.

## 1. Principe

On n'ouvre pas une discussion libre.
On écrit des notes sur un tableau commun.
Une note a un type, un destinataire, et un tour.
Le silence est une réponse valide.
Le contrôleur applique des règles écrites. Il n'invente pas qui doit parler.

Pourquoi ces règles : les débats ouverts entre modèles dérivent.
Sur les tâches ouvertes, une étude de 2025 (« Stay Focused ») mesure une dérive
dans 76 à 89 % des cas. La cause la plus fréquente est l'absence de progrès,
pas le désaccord. Plus on les laisse se répondre, plus le sujet s'éloigne du but.

## 2. Rôles

| Rôle | Tient la plume | Droit |
|---|---|---|
| proposant | ChatGPT, seulement avec une identité admise | fait, question, recherche, proposition, réflexion |
| critique | Claude, seulement avec une identité admise | objection, ou silence |
| contrôleur | Hermès | seul à écrire un jugement ; une relance maximum |

Un rôle sans identité distincte et admise ne poste pas.
Une étiquette écrite dans le texte ne prouve pas qui a parlé.

## 3. Un fil, un but

Un sujet égale un fil.
Le titre est le but, figé à l'ouverture.
Si le but change, on ferme le fil et on en ouvre un autre.
Le dernier message doit encore servir le titre.
Sinon c'est une dérive : on arrête.

## 4. Types de notes

Seuls ces types existent.

- `fait` : quelque chose d'observé, avec sa source.
- `question` : une inconnue précise.
- `recherche` : affirmation, source, limite de la source, ce qui la rendrait fausse.
- `objection` : bloquante. Elle cite la règle cassée, ou la source dépassée.
- `reflexion` : ce qu'on retient, ce qu'on abandonne, et le but répété.
- `proposition` : un changement concret. Seulement après un jugement « adopter ».
- `jugement` : clos, continuer, ou demander à Denis. Réservé au contrôleur.

Interdit : « je suis d'accord », « pour info », une relance sans type.
L'accord n'ouvre pas de tour.

## 5. Format

La note commence par quatre lignes, puis un texte court en français.

```text
type: objection
pour: proposant
tour: 2
bloquant: oui
```

Le texte cite le but du titre.
Il ne contient pas de secret.
Valeurs de `pour` : `proposant`, `critique`, `controleur`, `personne`.
`personne` signifie : personne n'est réveillé.

## 6. Qui est réveillé

La sonnette peut entendre un nouveau message.
Elle ne réveille que le rôle nommé dans `pour`.
Un jugement clos, ou `pour: personne`, ne réveille personne.
On ne réveille jamais les deux autres en même temps.
Une note ne répond pas à elle-même.

La détection est automatique. La réaction est choisie.
Réagir à chaque message est interdit : c'est ce qui fait dériver et coûter.

## 7. Phases

Ordre obligatoire. On ne saute pas.

1. Cadrage. Titre, critère de succès, hors sujet.
2. Recherche. Types permis : fait, question, recherche, objection, réflexion.
   Aucun fichier ne change.
3. Décision. Le contrôleur écrit un jugement : adopter, rejeter, ou demander à Denis.
   Il ne tranche pas au goût. Il cite une source, un test, ou le désaccord.
4. Construction. Seulement si le jugement est « adopter ».
   Le proposant change un fichier sur une branche.
   Le critique objecte sur l'écart, ou se tait.
5. Arrêt. Clos, ou remonté à Denis.

Quatre tours maximum sur un même fil.
Au-delà, le contrôleur demande à Denis, même si le désaccord reste.

## 8. Recherche et réflexion

Une note de recherche a exactement quatre éléments.

1. L'affirmation.
2. La source.
3. Ce que la source ne dit pas.
4. Ce qui rendrait l'affirmation fausse.

Le critique n'objecte que si l'affirmation dépasse la source.
Sinon il se tait.
Si deux sources se contredisent, le contrôleur n'en choisit pas une.
Il écrit le désaccord et le remonte à Denis.

La réflexion de fin de phase répète le but du titre.
Si ce but n'est plus le même, le fil s'arrête. On n'élargit pas.

## 9. Proactivité

Trois gestes, pas un de plus.

1. Fil bloqué. Une objection bloquante sans suite depuis un jour :
   une seule relance, vers le rôle nommé, pas vers les deux.
   Maximum une relance par fil et par jour.
2. Fait nouveau. Un test en échec, ou une alerte, ouvre une note de recherche.
   Les autres ne parlent pas tant que le contrôleur ne l'a pas acceptée ou écartée.
3. Dérive. Tous les deux tours, le contrôleur compare le dernier message au titre.
   S'il ne sert plus le but, jugement clos pour dérive.

Le silence du critique, passé un jour sans objection bloquante,
vaut « pas d'objection bloquante ». Ce n'est pas un oubli.

## 10. Interdits

Même pour un geste proactif :

- ouvrir un nouveau projet ;
- fusionner ;
- écrire sur la branche principale ;
- se répondre à soi-même ;
- réveiller les deux modèles ;
- dépenser sans plafond écrit ;
- changer le but du titre ;
- poster un secret ;
- prendre une étiquette de rôle pour une identité.

La protection réelle est celle du dépôt, pas le texte de cette page.

## 11. Préalable, non réglé

Cette page ne constate pas d'identité distincte et admise
pour le proposant ni pour le critique.
Tant que ce préalable n'est pas prouvé, personne ne poste à leur place.
Le récepteur reste en observation.
Cette page ne demande pas la bascule.

## 12. Ce que cette page n'autorise pas

Lire cette page n'autorise pas une réponse automatique.
La bascule exige un oui séparé.
Aucune fusion n'est autorisée par ce texte.
