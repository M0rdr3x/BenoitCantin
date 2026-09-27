#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / 'supabase' / 'production-reviewed-migration-batch.txt'
TRACE = ROOT / 'supabase' / 'production-reviewed-migration-decisions.txt'

BATCH_RE = re.compile(r'^(\d{14})\s+([A-Za-z0-9_]+)\s+([0-9a-f]{40})$')
TRACE_RE = re.compile(
    r'^(\d{14})\s+([A-Za-z0-9_]+)\s+([0-9a-f]{40})\s+issue#([1-9]\d*)\s+APPROVED$'
)


def parse_batch_text(text: str, source: str):
    rows = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        match = BATCH_RE.fullmatch(line)
        if not match:
            raise ValueError(f'Lot revu invalide {source} ligne {lineno}: {line}')
        rows.append(match.groups())
    return rows


def parse_trace_text(text: str, source: str):
    rows = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        match = TRACE_RE.fullmatch(line)
        if not match:
            raise ValueError(
                f'Trace de décision invalide {source} ligne {lineno}: {line}. '
                'Format attendu: <timestamp> <nom> <blob_sha> issue#<numero> APPROVED'
            )
        version, name, blob_sha, issue = match.groups()
        rows.append((version, name, blob_sha, int(issue), 'APPROVED'))
    return rows


def validate_static(errors, batch_rows, trace_rows):
    batch_versions = [version for version, _, _ in batch_rows]
    if len(batch_versions) != len(set(batch_versions)):
        errors.append('Lot revu: version dupliquée.')

    trace_keys = [(v, n, sha) for v, n, sha, _, _ in trace_rows]
    if len(trace_keys) != len(set(trace_keys)):
        errors.append('Registre de décisions: même blob de migration tracé plusieurs fois.')

    for _, _, _, issue, decision in trace_rows:
        if issue <= 0:
            errors.append('Registre de décisions: numéro d issue invalide.')
        if decision != 'APPROVED':
            errors.append('Registre de décisions: seule la décision APPROVED est autorisée dans ce fichier.')


def validate_transition(errors, base_batch, current_batch, base_trace, current_trace):
    validate_static(errors, current_batch, current_trace)

    if len(current_trace) < len(base_trace) or current_trace[:len(base_trace)] != base_trace:
        errors.append(
            'Registre de décisions non append-only: une trace historique a été supprimée, réordonnée ou réécrite.'
        )
        return

    base_batch_set = set(base_batch)
    current_batch_set = set(current_batch)
    added_batch = current_batch_set - base_batch_set

    added_trace = current_trace[len(base_trace):]
    added_trace_map = {}
    for version, name, blob_sha, issue, decision in added_trace:
        key = (version, name, blob_sha)
        added_trace_map.setdefault(key, []).append((issue, decision))

    for row in sorted(added_batch):
        matches = added_trace_map.get(row, [])
        if len(matches) != 1:
            errors.append(
                'Nouvelle migration marquée reviewed sans trace de décision ajoutée dans le même diff: '
                + ' '.join(row)
            )

    for key, matches in sorted(added_trace_map.items()):
        if key not in added_batch:
            errors.append(
                'Trace de décision pré-créée ou sans nouvelle ligne correspondante dans le reviewed batch: '
                + ' '.join(key)
            )
        if len(matches) > 1:
            errors.append(
                'Plusieurs nouvelles traces de décision pour le même blob dans un seul diff: '
                + ' '.join(key)
            )


def git_show(path: str, base_ref: str, allow_missing: bool = False):
    proc = subprocess.run(
        ['git', 'show', f'{base_ref}:{path}'],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode:
        if allow_missing:
            return ''
        raise RuntimeError((proc.stderr or proc.stdout).strip())
    return proc.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--base-ref',
        help='Commit Git de référence. Avec cette option, toute nouvelle ligne reviewed exige une trace ajoutée dans le même diff.',
    )
    args = parser.parse_args()

    errors = []

    if not BATCH.is_file():
        errors.append('Lot de migrations production revu absent.')
        current_batch = []
    else:
        try:
            current_batch = parse_batch_text(BATCH.read_text('utf-8'), 'courant')
        except ValueError as exc:
            errors.append(str(exc))
            current_batch = []

    if not TRACE.is_file():
        errors.append('Registre de traçabilité des décisions de migrations absent.')
        current_trace = []
    else:
        try:
            current_trace = parse_trace_text(TRACE.read_text('utf-8'), 'courant')
        except ValueError as exc:
            errors.append(str(exc))
            current_trace = []

    if args.base_ref:
        try:
            base_batch_text = git_show(
                'supabase/production-reviewed-migration-batch.txt',
                args.base_ref,
                allow_missing=False,
            )
            base_trace_text = git_show(
                'supabase/production-reviewed-migration-decisions.txt',
                args.base_ref,
                allow_missing=True,
            )
            base_batch = parse_batch_text(base_batch_text, f'base {args.base_ref}')
            base_trace = parse_trace_text(base_trace_text, f'base {args.base_ref}')
            validate_transition(errors, base_batch, current_batch, base_trace, current_trace)
        except (RuntimeError, ValueError) as exc:
            errors.append(f'Impossible de valider la transition de revue depuis {args.base_ref}: {exc}')
    else:
        validate_static(errors, current_batch, current_trace)

    if errors:
        print(f'ECHEC traçabilité reviewed batch: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    suffix = (
        f'; transition vérifiée depuis {args.base_ref}'
        if args.base_ref
        else '; syntaxe statique vérifiée'
    )
    print(
        f'OK traçabilité reviewed batch: {len(current_trace)} décision(s) future(s) tracée(s){suffix}. '
        'Le registre reste un pointeur d audit et ne remplace pas la décision humaine.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
