#!/usr/bin/env python3
"""Fusion sequentielle des proposition.diff des missions 03..08.

Chaque mission edite tools/visual_design.py. On applique une proposition a la
fois ; si elle echoue, on tente un patch par blocs (decoupe des hunks) pour
isoler le conflit et l'appliquer sur le contexte le plus proche.

Usage: python3 tools/merge_proposals.py [--dry-run]
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "tools" / "visual_design.py"
MISSIONS = ["03-hero", "04-family", "05-rooms", "06-climate", "07-security", "08-robots"]


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


def hunks(diff_text: str) -> tuple[str, list[str]]:
    """Decoupe un diff unifie en hunks, en gardant l'entete du patch."""
    lines = diff_text.splitlines(keepends=True)
    header: list[str] = []
    hunks: list[str] = []
    current: list[str] = []
    in_hunk = False
    for line in lines:
        if line.startswith("@@"):
            if current:
                hunks.append("".join(current))
            current = [line]
            in_hunk = True
            continue
        if in_hunk:
            current.append(line)
        else:
            header.append(line)
    if current:
        hunks.append("".join(current))
    return "".join(header), hunks


def apply_mission(mission: str, dry_run: bool) -> tuple[bool, str]:
    diff_path = ROOT / "missions" / mission / "proposal.diff"
    if not diff_path.exists():
        return False, "proposal.diff absent"
    text = diff_path.read_text()
    header, hs = hunks(text)
    if dry_run:
        shutil.copy2(TARGET, ROOT / "tools" / "visual_design.py.bak")
    applied, skipped = 0, 0
    conflicts: list[str] = []
    for i, h in enumerate(hs, 1):
        patch = header + h
        proc = subprocess.run(
            ["git", "apply", "--recount", "--whitespace=nowarn", "-"],
            cwd=ROOT, input=patch, capture_output=True, text=True,
        )
        if proc.returncode == 0:
            applied += 1
        else:
            skipped += 1
            reasons = proc.stderr.strip().splitlines()
            conflicts.append(f"hunk {i}: {reasons[-1] if reasons else 'inconnu'}")
    return skipped == 0, f"appliques={applied} conflits={skipped} {'; '.join(conflicts)}"


def main() -> int:
    dry = "--dry-run" in sys.argv
    backup = TARGET.with_suffix(".py.premerge.bak")
    shutil.copy2(TARGET, backup)
    print(f"backup: {backup}")
    total_bad = 0
    for m in MISSIONS:
        ok, detail = apply_mission(m, dry)
        print(f"{'OK ' if ok else 'PARTIEL'} {m}: {detail}")
        total_bad += 0 if ok else 1
    print(f"\nmissions en conflit: {total_bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())