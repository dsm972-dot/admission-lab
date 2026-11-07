#!/usr/bin/env python3
"""Codex borné : implémentation locale, aucun accès HA demandé."""
import subprocess
from pathlib import Path
root = Path(__file__).resolve().parents[1]
prompt = (root/'docs/FAMILY_VEHICLE_CODEX_BRIEF.md').read_text()
with (root/'evidence/family-vehicle-codex.log').open('w') as out:
    try:
        result = subprocess.run(['codex','exec','--approve-for-me','--skip-git-repo-check','-m','gpt-6.1-sol','-c','model_provider="openai"','-c','model_reasoning_effort="high"',prompt],cwd=root,stdout=out,stderr=subprocess.STDOUT,timeout=420)
        print('CODEX_EXIT',result.returncode)
        raise SystemExit(result.returncode)
    except subprocess.TimeoutExpired:
        print('CODEX_TIMEOUT: reprendre les résultats locaux sans relancer aveuglément.')
        raise SystemExit(124)
