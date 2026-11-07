#!/usr/bin/env python3
"""Lance la creation d'un backup complet HA en DETACHE (docker exec -d) puis rend la main.

Le POST /backups/new/full bloque cote Supervisor pendant toute la creation (~15-30 min) :
le lancer via une commande ssh synchrone se fait tuer par le timeout client.
On ecrit donc le programme dans le conteneur core, on l'execute en -d, et on lit le resultat
dans /tmp/ai_nexus_backup_result.json.

usage: backup_new.py "<nom du backup>"
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys

PROG = r'''
import base64, json, os, urllib.request, traceback
try:
    tok = os.environ["SUPERVISOR_TOKEN"]
    body = base64.b64decode(os.environ["SUP_BODY"])
    req = urllib.request.Request(
        "http://supervisor/backups/new/full",
        data=body, method="POST",
        headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=7200) as r:
        out = r.read().decode()
except Exception:
    out = json.dumps({"error": traceback.format_exc()})
with open("/tmp/ai_nexus_backup_result.json", "w") as f:
    f.write(out)
'''


def sh(remote_cmd: str, timeout: int = 120):
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "ha", remote_cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def main() -> int:
    name = sys.argv[1]
    b64prog = base64.b64encode(PROG.encode()).decode()
    b64body = base64.b64encode(json.dumps({"name": name}).encode()).decode()
    # 1. deposer le programme dans le conteneur
    r = sh(f"echo {b64prog} | base64 -d | sudo docker exec -i homeassistant sh -c 'cat > /tmp/ai_nexus_backup.py'")
    if r.returncode != 0:
        print("upload KO:", r.stderr[:300])
        return 1
    sh("sudo docker exec homeassistant sh -c 'rm -f /tmp/ai_nexus_backup_result.json'")
    # 2. lancer detache
    r = sh(
        "sudo docker exec -d -e SUP_BODY=" + b64body + " homeassistant "
        "sh -c 'python3 /tmp/ai_nexus_backup.py'"
    )
    if r.returncode != 0:
        print("lancement KO:", r.stderr[:300])
        return 1
    print("BACKUP_LAUNCHED", name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
