#!/usr/bin/env python3
"""Non-destructive backup inspection; never extract secret contents."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REMOTE = '''import tarfile,json,os,time
p="/data/backup/d2150955.tar"
t=tarfile.open(p)
meta=json.load(t.extractfile("./backup.json"))
result={"path":p,"size":os.stat(p).st_size,"mtime":os.stat(p).st_mtime,"metadata":meta,"members":[{"name":m.name,"size":m.size} for m in t],"core_members":[],"core_gzip_verified":False}
h=tarfile.open(fileobj=t.extractfile("homeassistant.tar.gz"),mode="r|gz")
for m in h:
 if any(s in m.name for s in ["configuration.yaml","home-assistant_v2.db",".storage/core.config_entries",".storage/lovelace"]):
  result["core_members"].append({"name":m.name,"size":m.size})
h.close()
# Read gzip through EOF to check its checksum, without storing any payload.
import gzip
f=gzip.GzipFile(fileobj=t.extractfile("homeassistant.tar.gz"))
while f.read(8*1024*1024): pass
result["core_gzip_verified"]=True
print(json.dumps(result))
'''
p = subprocess.run(['ssh','-o','BatchMode=yes','ha','sudo docker exec -i hassio_supervisor python3 -'],input=REMOTE,text=True,capture_output=True,timeout=1800)
if p.returncode:
    raise SystemExit(p.stderr)
result=json.loads(p.stdout)
(ROOT/'data'/'backup_verified.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:result[k] for k in ['path','size','core_members','core_gzip_verified']},indent=2))
