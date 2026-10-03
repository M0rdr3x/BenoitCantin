#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / 'supabase' / 'production-reviewed-migration-batch.txt'
TRACE = ROOT / 'supabase' / 'production-reviewed-migration-decisions.txt'
LEDGER = ROOT / 'supabase' / 'production-migration-ledger.txt'

LEGACY_REVIEWED_ROWS = (
    ('20260907145100', 'sinjira_v25_security_push_receipt_queue', '4c6a4726610aa80517abe420048c00f62feb492e'),
    ('20260908120000', 'sinjira_v25_live_social_foundation', '3c33b5e2cc294a80407a5889d91b9de4efea8f76'),
    ('20260908121000', 'sinjira_v25_live_social_realtime_eligibility', '772de5e4ceeeb0a6745efa6436d3977134abf918'),
    ('20260908122000', 'sinjira_v25_live_social_helper_invoker', 'a23e14bccd042baa3da957329a8c8368c9cfcb4a'),
    ('20260908130000', 'sinjira_v25_live_social_moderation', '21138a4bb307824c9ae454b0e317c74c6be5d2da'),
    ('20260908131000', 'sinjira_v25_live_social_private_invites', '56a4d456ffa5e88828ce2cfb519887ceeeec5f32'),
    ('20260908132000', 'sinjira_v25_live_social_safety_convergence', '3e62002a418fa26585507f98472e7b0da8b01073'),
    ('20260908140000', 'sinjira_v25_live_social_typed_commands', '96028abd8e5a34fd9b661a25b58270ea3fb721cf'),
    ('20260908150000', 'sinjira_v25_live_social_share_codes', '67e8cad4d3707fff084f6c2a3401407d5069e111'),
    ('20260910150000', 'sinjira_v25_device_session_rebind_security_hardening', '6fd2c0b70f5ffb48c38f0d134f54fc0cf041de5f'),
    ('20260910193000', 'sinjira_v25_device_challenge_session_binding', 'eaf3099c39374623c2c7d6de692a602244b09b9e'),
    ('20260910221500', 'sinjira_v25_device_challenge_denial_session_guard', '95965603903f8ee185a80a05fb33e1e0e5906838'),
    ('20260911001000', 'sinjira_v25_travel_mode_country_normalization', 'd84057e197b04c1821443ffca5deb6385694cc0f'),
    ('20260911225500', 'sinjira_v25_fracture_endgame_atomic_submit', 'c69d99f81fed4b606da1e93910adcedbf0ddfc31'),
)

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


def ledger_cutoff():
    if not LEDGER.is_file():
        raise ValueError('Ledger production absent.')
    versions = []
    for lineno, raw in enumerate(LEDGER.read_text('utf-8').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2 or not re.fullmatch(r'\d{14}', parts[0]):
            raise ValueError(f'Ledger production invalide ligne {lineno}: {line}')
        versions.append(parts[0])
    if not versions:
        raise ValueError('Ledger production vide.')
    return versions[-1]


def validate_static(errors, batch_rows, trace_rows, cutoff):
    batch_versions = [version for version, _, _ in batch_rows]
    if len(batch_versions) != len(set(batch_versions)):
        errors.append('Lot revu: version dupliquée.')

    trace_keys = [(v, n, sha) for v, n, sha, _, _ in trace_rows]
    if len(trace_keys) != len(set(trace_keys)):
        errors.append('Registre de décisions: même blob de migration tracé plusieurs fois.')

    trace_keys_set = set(trace_keys)
    legacy_set = set(LEGACY_REVIEWED_ROWS)
    current_batch_set = set(batch_rows)

    for row in batch_rows:
        if row not in legacy_set and row not in trace_keys_set:
            errors.append(
                'Migration reviewed hors baseline historique sans trace de décision active: '
                + ' '.join(row)
            )

    active_by_identity = {
        (version, name): (version, name, blob_sha)
        for version, name, blob_sha in batch_rows
    }

    for version, name, blob_sha, issue, decision in trace_rows:
        if issue <= 0:
            errors.append('Registre de décisions: numéro d issue invalide.')
        if decision != 'APPROVED':
            errors.append('Registre de décisions: seule la décision APPROVED est autorisée dans ce fichier.')
        key = (version, name, blob_sha)
        if key not in current_batch_set and version > cutoff:
            active = active_by_identity.get((version, name))
            active_is_traced = active is not None and active in trace_keys_set
            if not active_is_traced:
                errors.append(
                    'Trace de décision future sans ligne active correspondante ni blob de remplacement tracé: '
                    + ' '.join(key)
                )


def validate_transition(errors, base_batch, current_batch, base_trace, current_trace, cutoff):
    validate_static(errors, current_batch, current_trace, cutoff)

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
    try:
        cutoff = ledger_cutoff()
    except ValueError as exc:
        errors.append(str(exc))
        cutoff = '00000000000000'

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
            validate_transition(errors, base_batch, current_batch, base_trace, current_trace, cutoff)
        except (RuntimeError, ValueError) as exc:
            errors.append(f'Impossible de valider la transition de revue depuis {args.base_ref}: {exc}')
    else:
        validate_static(errors, current_batch, current_trace, cutoff)

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
        f'OK traçabilité reviewed batch: baseline historique={len(LEGACY_REVIEWED_ROWS)}, '
        f'{len(current_trace)} décision(s) future(s) tracée(s){suffix}. '
        'Le registre reste un pointeur d audit et ne remplace pas la décision humaine.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
