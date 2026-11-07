#!/usr/bin/env python3
"""Entrée cron sans agent, bornée par la fenêtre de l'observateur.

Les lectures HA sont effectuées par publish_candidate.py verify, jamais par
un appel de service. Succès intermédiaires silencieux ; erreur ou bilan final
imprimé pour livraison native du scheduler. Aucun changement de board.
"""
import json
import os
from pathlib import Path
import sys

from observe_candidate import Observer, ROOT, markdown

REPORT = ROOT / 'docs/AI_NEXUS_V4_CANARY_REPORT.md'


def main():
    observer = Observer()
    row = observer.sample()
    report = observer.report()
    text = markdown(report)
    previous = REPORT.read_text() if REPORT.exists() else ''
    # Écriture locale atomique ; aucune donnée brute ni secret HA.
    temporary = REPORT.with_suffix('.md.new')
    temporary.write_text(text)
    os.replace(temporary, REPORT)
    if row['outcome'] in ('ERROR', 'TIMEOUT'):
        print('AI Nexus V4 : contrôle technique en échec. Aucune correction ni '
              'action physique exécutée. Diagnostic : ' + str(row['error']) + '.')
        return 1
    if report['status'] != 'IN_PROGRESS' and text != previous:
        print(text)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        print('AI Nexus V4 : observation indisponible. État local ou verrou à '
              'contrôler ; aucun PASS, aucune correction automatique.')
        sys.exit(2)
