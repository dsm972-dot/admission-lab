# BACKUP_CHECK — vérification archive existante & backup complet horodaté

- Date de vérification : 2026-10-11 (Europe/Paris)
- Auteur : agent devops (Hermes), tâche kanban `t_97522728`
- Accès : SSH `ha` (addon Advanced SSH & Web Terminal, host `a0d7b954-ssh`) + API Supervisor
  (`GET/POST http://supervisor/...` depuis les conteneurs `homeassistant`/`hassio_supervisor`).
- Preuve machine : `data/backup_verified_b8707049.json` (données privées, non versionnées).
- Aucune sauvegarde supprimée. Aucune modification HA.

> Remplace la version précédente du 2026-10-03 (conservée dans l'historique Git).

## 1. Archive demandée : `/backup/7a9b31df.tar` — ABSENTE (constat)

Vérifications :
- `find /backup /data /mnt -name '*7a9b31df*'` → **aucun résultat**.
- `GET /supervisor/backups` → 7 sauvegardes, **aucune de slug `7a9b31df`**.
- Référence résiduelle : `data/backups.json` (instantané du 2026-10-03) décrivait
  `7a9b31df` = « Automatic backup 2026.9.4 », **type=partial**, 26 182 912 000 octets,
  protected=true. Cette archive n'existe plus aujourd'hui.

Conséquence honnête : taille, intégrité et contenu de `/backup/7a9b31df.tar` **ne peuvent pas
être vérifiés** — l'archive est introuvable. Aucune suppression n'a été effectuée par cette tâche ;
la cause est une purge/non-présence antérieure (rotation des sauvegardes automatiques).

## 2. Nouveau backup complet horodaté (produit par cette tâche) — VALIDÉ

- Nom : **« AI Nexus V4 full 2026-10-11T1443Z »** — slug **`b8707049`** — **type=full**.
- Date de création (backup.json) : `2026-10-11T14:44:56Z` (16:44 CEST) ; fin d'écriture (mtime) :
  `2026-10-11T15:18:22Z` (17:18 CEST).
- Chemin Supervisor : `/data/backup/b8707049.tar` ; vue addon SSH : `/backup/b8707049.tar`.
- Taille réelle (`stat`) : **270 929 879 040 octets** (≈ 252,3 Gio).
- Créé via **`POST http://supervisor/backups/new/full`** (API Supervisor), avec nom horodaté,
  par le run 412 de cette même tâche (heartbeat « Backup full lancé via Supervisor API » cohérent
  avec le nom et l'horodatage).

### Contrôles d'intégrité exécutés

| Contrôle | Résultat |
|---|---|
| Lecture intégrale SHA-256 des 270,9 Go | **OK** — `be5851ff68c870d61a5016c23d3cbad38ebe308da4432868d4ddc1ca644b3690` (aucune erreur) |
| Ouverture / structure tar | **OK** — 32 membres réguliers |
| CRC gzip du core `homeassistant.tar.gz` (relu jusqu'à EOF) | **OK** — 22 415 923 200 octets décompressés |
| CRC gzip des 25 petits membres `.tar.gz` (< 100 Mo) | **25/25 OK** |
| Métadonnées `backup.json` lisibles | **OK** — HA 2026.10.1, `exclude_database=false`, 26 addons, dossiers `share`,`ssl`,`media` |

### Contenu (32 membres)

```
homeassistant.tar.gz                18 879 888 879
core_matter_server.tar.gz               11 707 344
core_samba.tar.gz                            2 976
core_configurator.tar.gz                     1 991
core_ssh.tar.gz                              7 080
a0d7b954_ssh.tar.gz                         14 651
d5369777_music_assistant.tar.gz         23 258 422
9074a9fa_cloudflared.tar.gz                  8 299
a0d7b954_spotify.tar.gz                      2 306
core_mariadb.tar.gz                      1 393 459
45df7312_zigbee2mqtt.tar.gz                  2 076
a0d7b954_ftp.tar.gz                          2 054
cb646a50_get.tar.gz                          1 333
a0d7b954_vscode.tar.gz               1 099 960 547
a0d7b954_nodered.tar.gz                    390 759
ccab4aaf_frigate-fa.tar.gz           5 573 470 048
db21ed7f_postgres_latest.tar.gz          5 308 711
db21ed7f_postgres.tar.gz               253 567 972
db21ed7f_immich_openvino.tar.gz          3 847 452
core_openthread_border_router.tar.gz         2 912
81f33d0f_ha_mcp.tar.gz                      78 118
core_piper.tar.gz                       58 470 184
db21ed7f_immich.tar.gz                   1 666 479
db21ed7f_immich_power_tools.tar.gz           2 677
core_mosquitto.tar.gz                      288 780
a0d7b954_tailscale.tar.gz                   11 157
5c53de3b_esphome.tar.gz                      1 884
share.tar.gz                           177 766 286
ssl.tar.gz                                  46 063
media.tar.gz                      244 838 644 830
supervisor.tar.gz                              328
./backup.json                                3 005
```

### Limites honnêtes
- Le sha256 couvre l'intégrité **octet à octet du conteneur tar complet**. Le CRC unitaire
  n'a été poussé à EOF que pour le core HA et les 25 petits membres ; les gros membres
  `media.tar.gz` (244,8 Go), `ccab4aaf_frigate-fa` (5,57 Go) et `a0d7b954_vscode` (1,1 Go)
  n'ont pas eu de contrôle CRC décompressé séparé.
- **Aucun test de restauration** n'a été effectué.

## 3. Inventaire de toutes les sauvegardes présentes (API Supervisor)

| Slug | Nom | Type | Date (UTC) | Taille (o) | Protégée |
|---|---|---|---|---|---|
| 5b08ab90 | OpenThread Border Router 3.1.2 | partial | 2026-09-16T04:58:47Z | 10 240 | oui |
| 4bc0759e | Advanced SSH & Web Terminal 24.1.5 | partial | 2026-09-29T04:59:20Z | 30 720 | oui |
| 85bc8806 | Zigbee2MQTT 2.14.1-1 | partial | 2026-10-03T03:42:46Z | 10 240 | oui |
| badc100d | Automatic backup 2026.10.0 | partial | 2026-10-10T03:18:18Z | 26 101 985 280 | oui |
| b4a06937 | Automatic backup 2026.10.1 | partial | 2026-10-11T03:30:30Z | 25 999 431 680 | oui |
| 24b99abc | Automatic backup 2026.10.1 | partial | 2026-10-11T03:35:28Z | 25 999 882 240 | oui |
| **b8707049** | **AI Nexus V4 full 2026-10-11T1443Z** | **full** | **2026-10-11T14:44:56Z** | **270 929 879 040** | non |

## 4. Espace disque (contexte de décision)

- Support `/backup` = `/dev/nvme0n1p8` : **938,2 G** total, **677,5 G** utilisés, **222,5 G** libres (75 %).
- Un **second** backup full (≈ 270 Go) ne tient **pas** dans les 222,5 Go libres : le relancer
  échouerait (échec garanti = HARD STOP). Le backup complet horodaté requis par la tâche est donc
  bien **`b8707049`**, déjà produit par cette tâche ; il a été validé plutôt que dupliqué.

## Verdict

- Archive existante `7a9b31df` : **introuvable** (constat documenté).
- Backup complet horodaté `b8707049` (« AI Nexus V4 full 2026-10-11T1443Z ») : **VALIDÉ**
  (taille, sha256, inventaire 32 membres, CRC core + 25 petits membres).
- Aucune suppression, aucune modification HA, aucune restauration testée.
