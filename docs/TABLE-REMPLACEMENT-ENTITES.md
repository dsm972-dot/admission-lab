# 03 — Entités mortes ou muettes : table de remplacement vérifiée

**Méthode.** Chaque entité citée ici a été confrontée aux états réels de l'instance le **7 novembre 2026**. Les remplacements proposés sont des entités **présentes et vivantes** ce jour-là, avec leur état au moment du relevé. Aucun remplacement n'est déduit du nom : ceux qui demandent un arbitrage sont signalés comme tels.

---

## 1. Vue d'ensemble

| Situation | Nombre | Conséquence à l'écran |
|---|---|---|
| Entités **absentes** de l'instance (l'ancien nom n'existe plus) | **4** | Tuile vide ou « entité introuvable » |
| Entités **présentes mais indisponibles ou inconnues** | **7** | Tuile affichée mais valeur `indisponible` / `inconnu` |
| **Total** | **11** | — |

Distinction importante, et elle change la correction à faire :

- **Absente** = le nom a changé ou l'équipement a été retiré de Home Assistant → il faut **remplacer la référence**.
- **Indisponible / inconnue** = l'entité existe, l'équipement ne répond pas → il faut **diagnostiquer l'équipement**, pas changer la tuile. Un remplacement masquerait une panne réelle.

---

## 2. Les 4 entités absentes

| Emplacement | Tuile concernée | Entité câblée (morte) | Remplacement vivant proposé | État live 07/11 | Verdict |
|---|---|---|---|---|---|
| `salon_light` | Lumière du salon | `light.lumiere_du_salon` | `light.salon_projecteur` | `off` | **Arbitrage requis** (voir §4) |
| `cuisine_light` | Lumière de la cuisine | `light.cuisine` | `light.ampoule_cuisine` | `on` | ✅ Direct, aucun doute |
| `emile_light` | Lumière chambre Émile | `light.chambre_emile` | `light.ampoule_emile` | `off` | ✅ Direct, aucun doute |
| `maddy_light` | Lumière chambre Maddy | `light.chambre_maddy` | `light.ampoule_maddy` | `off` | ✅ Direct (`light.ampoule_chevet_maddy` existe mais est `indisponible`) |

Le remplacement est mécanique : même pièce, même fonction, nom `ampoule_*` au lieu de `chambre_*`. À appliquer dans `data/entities_map.json` (clés `salon_light`, `cuisine_light`, `emile_light`, `maddy_light`), puis à **régénérer**.

---

## 3. Les 7 entités indisponibles ou inconnues

| Emplacement / tuile | Entité câblée | État live 07/11 | Diagnostic | Action recommandée |
|---|---|---|---|---|
| `maddy_cover` | `cover.curtain_switch_rideau` | `unknown` | Le module existe (`switch.curtain_switch_reverse_motor_direction` est `on`) mais la position n'est pas remontée | **Diagnostiquer le module**, ne pas remplacer. Repli : `cover.volet_maddy_etat` (`open`) |
| `emile_cover` | `cover.volet_de_la_chambre_de_emile_rideau` | `unavailable` | Doublon : `cover.volet_de_la_chambre_de_emile_local_rideau` est aussi `unavailable`, mais `cover.volet_emile_etat` est `open` | **Remplacer** par `cover.volet_emile_etat` |
| `cuisine_cover` | `cover.volet_de_la_cuisine_rideau` | `unknown` | `cover.volet_cuisine_etat` est `open` et `cover.cuisine_volet_cuisine` est `unknown` | **Remplacer** par `cover.volet_cuisine_etat` |
| `bureau_light` | `light.lumiere_bureau` | `unavailable` | Aucune lampe `light.*` vivante dans le bureau | **Utiliser l'interrupteur** `switch.interrupteur_bureau` (`off`) |
| `bureau_ambilight` | `light.lumiere_bureau_ambilight` | `unavailable` | Aucun équivalent | **Masquer la tuile** tant que l'ambilight n'est pas rétabli |
| (multimédia) | `media_player.meghann` | `unavailable` | `meghann_2` et `meghann_3` sont **aussi** `unavailable` : l'appareil est éteint ou hors réseau | **Ne pas remplacer** — panne d'équipement, pas défaut d'UI |
| (multimédia) | `media_player.sound_bar_5` | `unavailable` | Doublon d'intégration | **Remplacer** par `media_player.sound_bar_lg` (`on`) — c'est la barre réellement pilotable (LG SK10Y) |

### Le cas des doublons d'intégration

`sound_bar` existe en **six** exemplaires (`sound_bar`, `_3`, `_4`, `_5`, `_6`, `_lg`) dont cinq `indisponibles`. Même schéma pour `meghann` (3), `home_bureau` (3), `shield` (4), `freebox_player` (2). C'est la signature d'**entrées d'intégration recréées plusieurs fois** sans supprimer les anciennes. Ce n'est pas au dashboard de trancher : il doit viser l'entité vivante, et le ménage des intégrations est un chantier séparé.

---

## 4. Le seul vrai arbitrage : la lumière du salon

Deux lampes vivantes portent un nom plausible :

| Entité | État | Interprétation |
|---|---|---|
| `light.salon_projecteur` | `off` | Éclairage principal du salon (recommandé) |
| `light.salon_led_d_etat` | `off` | Bandeau ou voyant lumineux |

**Recommandation : `light.salon_projecteur`.** Raison : `led_d_etat` désigne dans cette installation un voyant d'état (cf. `volet_bureau_backlight_mode`), pas un éclairage de pièce. Si Denis confirme que la « lumière du salon » désigne autre chose, une seule ligne à changer.

---

## 5. Ce que cette table ne prétend pas

- Elle ne prouve pas que les 4 lampes ont été **supprimées** : elles peuvent avoir été renommées. La cause exacte n'est pas dans le dépôt, qui ne contient qu'un instantané du 24 octobre.
- Les états `on` / `off` sont ceux du **7 novembre 2026** : ce sont des valeurs instantanées, pas des garanties.
- Les remplacements proposés n'ont **pas été testés en appui réel** : ils sont valides comme cibles d'entité, ce qui reste à vérifier est qu'un appui produit bien l'effet attendu. C'est un travail de la refonte, pas de ce constat.
