#!/usr/bin/env python3
"""Acces API Supervisor HA (backups) via ssh ha + docker exec, sans exposer le token.

usage:
  sup.py GET  /backups
  sup.py GET  /backups/<slug>/info
  sup.py POST /backups/new/full '{"name":"..."}'
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys

REMOTE = r'''
import base64, json, os, urllib.request
tok = os.environ["SUPERVISOR_TOKEN"]
req = urllib.request.Request(
    "http://supervisor" + os.environ["SUP_PATH"],
    data=base64.b64decode(os.environ.get("SUP_BODY", "") or b"") or None,
    method=os.environ["SUP_METHOD"],
    headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req, timeout=3600) as r:
        print(r.read().decode())
except urllib.error.HTTPError as e:
    print(json.dumps({"http_error": e.code, "body": e.read().decode()[:2000]}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"error": repr(e)}))
'''


def call(method: str, path: str, body: str = "", timeout: int = 300) -> dict | str:
    b64prog = base64.b64encode(REMOTE.encode()).decode()
    b64body = base64.b64encode(body.encode()).decode()
    cmd = (
        f"echo {b64prog} | base64 -d | sudo docker exec -i "
        f"-e SUP_METHOD={method.upper()} -e SUP_PATH={path} -e SUP_BODY={b64body} "
        f"homeassistant python3 -"
    )
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "ha", cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    out = (r.stdout or "").strip() or (r.stderr or "").strip()
    try:
        return json.loads(out)
    except Exception:
        return out


if __name__ == "__main__":
    method = sys.argv[1]
    path = sys.argv[2]
    body = sys.argv[3] if len(sys.argv) > 3 else ""
    print(json.dumps(call(method, path, body), indent=1, ensure_ascii=False))
