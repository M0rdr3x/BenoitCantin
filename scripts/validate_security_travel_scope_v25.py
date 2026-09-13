#!/usr/bin/env python3
"""Contrat fail-closed du Mode Voyage V25 : réduction limitée au risque géographique."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / 'supabase/migrations/20260913030500_sinjira_v25_travel_mode_geo_scope_hardening.sql'
TEST = ROOT / 'supabase/tests/security_travel_scope_v25.test.sql'
WORKFLOW = ROOT / '.github/workflows/sinjira-security-risk-v25.yml'
BATCH = ROOT / 'supabase/production-reviewed-migration-batch.txt'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'

MIGRATION_VERSION = '20260913030500'
MIGRATION_NAME = 'sinjira_v25_travel_mode_geo_scope_hardening'
SAFE_CONDITION = "if coalesce(p_travel_match,false) and coalesce(p_unexpected_region,false) then"
TEST_COMMAND = 'supabase test db supabase/tests/security_travel_scope_v25.test.sql --local'
SELF_TEST_COMMAND = 'run: python scripts/validate_security_travel_scope_v25.py --self-test'
VALIDATE_COMMAND = 'run: python scripts/validate_security_travel_scope_v25.py'


def fail(message: str) -> None:
    raise ValueError(message)


def git_blob_sha(text: str) -> str:
    data = text.encode('utf-8')
    return hashlib.sha1(f'blob {len(data)}\0'.encode('ascii') + data).hexdigest()


def validate_texts(migration: str, test: str, workflow: str, batch: str, ledger: str) -> None:
    required_migration = (
        'create or replace function private.security_risk_score_v25(',
        'immutable',
        'set search_path = pg_catalog, private',
        SAFE_CONDITION,
        "v_score := v_score - 15;",
        "v_reasons := array_append(v_reasons,'travel_match');",
        'from public, anon, authenticated;',
        ') to service_role;',
        "'model_version','v25.0'",
    )
    for needle in required_migration:
        if needle not in migration:
            fail(f'migration: invariant absent: {needle}')

    if "if coalesce(p_travel_match,false) then" in migration:
        fail('migration: réduction globale Mode Voyage interdite')
    if migration.count('v_score := v_score - 15;') != 2:
        fail('migration: seules les réductions appareil fiable et voyage géographique sont attendues')
    for forbidden in ('ip_address', 'raw_ip', 'latitude', 'longitude', 'gps_lat', 'gps_lon'):
        if forbidden in migration.lower():
            fail(f'migration: collecte de localisation interdite détectée: {forbidden}')

    required_test = (
        'select plan(8);',
        "50::integer,\n  'Mode Voyage ne réduit ni appareil inconnu ni action sensible'",
        "25::integer,\n  'Mode Voyage ne réduit pas une récupération récente'",
        "30::integer,\n  'Mode Voyage ne réduit pas le signal voyage impossible'",
        "v_unexpected_region := v_previous.country_code <> v_country and not v_travel_match",
        "v_force_challenge := true",
    )
    for needle in required_test:
        if needle not in test:
            fail(f'test pgTAP: preuve absente: {needle}')

    trigger_test = "      - 'supabase/tests/security_travel_scope_v25.test.sql'"
    trigger_guard = "      - 'scripts/validate_security_travel_scope_v25.py'"
    if workflow.count(trigger_test) != 2:
        fail('workflow: le test Mode Voyage doit déclencher PR + push main')
    if workflow.count(trigger_guard) != 2:
        fail('workflow: le garde Mode Voyage doit déclencher PR + push main')
    if workflow.count(TEST_COMMAND) != 1:
        fail('workflow: commande pgTAP Mode Voyage absente ou dupliquée')
    if workflow.count(SELF_TEST_COMMAND) != 1 or workflow.count(VALIDATE_COMMAND) != 1:
        fail('workflow: auto-test et validation Mode Voyage requis exactement une fois')

    expected_batch_line = f'{MIGRATION_VERSION} {MIGRATION_NAME} {git_blob_sha(migration)}'
    if batch.splitlines().count(expected_batch_line) != 1:
        fail(f'lot production revu: empreinte exacte absente: {expected_batch_line}')
    if any(line.startswith(MIGRATION_VERSION + ' ') for line in ledger.splitlines()):
        fail('registre production: la migration locale ne doit pas être marquée comme déployée')


def load() -> tuple[str, str, str, str, str]:
    return tuple(
        path.read_text(encoding='utf-8')
        for path in (MIGRATION, TEST, WORKFLOW, BATCH, LEDGER)
    )


def self_test(values: tuple[str, str, str, str, str]) -> None:
    migration, test, workflow, batch, ledger = values
    validate_texts(*values)
    mutations = {
        'réduction globale': (
            migration.replace(SAFE_CONDITION, 'if coalesce(p_travel_match,false) then', 1),
            test, workflow, batch, ledger,
        ),
        'preuve appareil/action supprimée': (
            migration,
            test.replace('50::integer,', '35::integer,', 1),
            workflow, batch, ledger,
        ),
        'pgTAP non exécuté': (
            migration, test,
            workflow.replace('          ' + TEST_COMMAND + '\n', '', 1),
            batch, ledger,
        ),
        'garde non déclenché': (
            migration, test,
            workflow.replace("      - 'scripts/validate_security_travel_scope_v25.py'\n", '', 1),
            batch, ledger,
        ),
        'empreinte migration falsifiée': (
            migration, test, workflow,
            batch.replace(git_blob_sha(migration), '0' * 40, 1),
            ledger,
        ),
        'faux déploiement production': (
            migration, test, workflow, batch,
            ledger + f'\n{MIGRATION_VERSION} {MIGRATION_NAME}\n',
        ),
    }
    for label, mutated in mutations.items():
        try:
            validate_texts(*mutated)
        except ValueError:
            continue
        fail(f'auto-test non détecté: {label}')
    print(f'OK Mode Voyage V25: {len(mutations)}/{len(mutations)} régressions critiques détectées')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    values = load()
    if args.self_test:
        self_test(values)
    else:
        validate_texts(*values)
        print('OK Mode Voyage V25: réduction strictement géographique, pgTAP branché, blob revu et production inchangée.')


if __name__ == '__main__':
    main()
