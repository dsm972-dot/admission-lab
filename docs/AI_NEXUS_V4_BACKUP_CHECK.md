# AI Nexus V4 — vérification sauvegarde

Sauvegarde complète supplémentaire d2150955 « AI Nexus V4 pre-deploiement 20261003 » créée le 2026-10-03 à 14:21:39 UTC. Type Supervisor : full. Taille réellement stat() : 381062154240 octets, archive /data/backup/d2150955.tar dans hassio_supervisor. Aucune sauvegarde existante supprimée.

Vérifications exécutées (tools/check_backup.py, données privées dans data/backup_verified.json, non versionnées) :
- Archive tar ouverte, 32 membres inventoriés ; métadonnées backup.json lisibles.
- Home Assistant Core 2026.9.4 inclus, exclude_database=false.
- Configuration configuration.yaml, base SQLite home-assistant_v2.db, registre core.config_entries et configurations Lovelace retrouvés dans homeassistant.tar.gz.
- Archive gzip Home Assistant parcourue puis relue intégralement jusqu’à EOF : contrôle CRC gzip réussi, sans extraction ni affichage des secrets.
- 26 addons et dossiers share/ssl déclarés et leurs archives listées.

Limites honnêtes : pas de restauration production, pas de test SQLite integrity_check sur la base extraite, pas de contrôle CRC intégral des 26 archives addons. Le CRC vérifié concerne uniquement le composant Home Assistant ; ne pas présenter l’intégralité des 381 Go comme vérifiée octet par octet. Aucun test de restauration effectué.

Exports complémentaires : configurations Lovelace, ressources frontend et liste dashboards dans data/ (hors Git). Export séparé réellement créé de configuration.yaml et themes dans backups/frontend-baseline-config.tar (11264 octets, 8 membres, fichier 0600/dossier 0700, hors Git). Ne pas joindre cet export privé à une notification ni à un rapport public.

Aucun fichier HA modifié pour cette inspection. versions gelées, aucune mise à jour HA/HACS/cartes.
