#!/usr/bin/env python3
"""Contrat fail-closed A1 du Mode Voyage V25 : effet limité au signal géographique."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / 'supabase/migrations/20260913030500_sinjira_v25_travel_mode_geo_scope_hardening.sql'
RISK_TEST = ROOT / 'supabase/tests/security_risk_model_v25.test.sql'
TRAVEL_TEST = ROOT / 'supabase/tests/security_travel_scope_v25.test.sql'
WORKFLOW = ROOT / '.github/workflows/sinjira-security-risk-v25.yml'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'

MIGRATION_VERSION = '20260913030500'
MIGRATION_BLOB_SHA = '7285d1e30ea288004d17c1dbfbf9f01662b36bb7'
TRAVEL_TEST_TRIGGER = "- 'supabase/tests/security_travel_scope_v25.test.sql'"
GUARD_TRIGGER = "- 'scripts/validate_security_travel_scope_v25.py'"
TRAVEL_TEST_COMMAND = 'supabase test db supabase/tests/security_travel_scope_v25.test.sql --local'
SELF_TEST_COMMAND = 'run: python scripts/validate_security_travel_scope_v25.py --self-test'
VALIDATE_COMMAND = 'run: python scripts/validate_security_travel_scope_v25.py'


def fail(message: str) -> None:
    raise ValueError(message)


def lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines()]


def git_blob_sha(text: str) -> str:
    data = text.encode('utf-8')
    return hashlib.sha1(f'blob {len(data)}\0'.encode('ascii') + data).hexdigest()


def validate_texts(migration: str, risk_test: str, travel_test: str, workflow: str, ledger: str) -> None:
    required_migration = (
        'create or replace function private.security_risk_score_v25(',
        'immutable',
        'set search_path = pg_catalog, private',
        "v_score := v_score - 15;",
        "v_reasons := array_append(v_reasons,'trusted_device');",
        'perform p_travel_match;',
        'from public, anon, authenticated;',
        ') to service_role;',
        "'model_version','v25.0'",
    )
    for needle in required_migration:
        if needle not in migration:
            fail(f'migration: invariant absent: {needle}')

    if git_blob_sha(migration) != MIGRATION_BLOB_SHA:
        fail('migration: empreinte A1 inattendue; toute modification doit être revue explicitement')
    if migration.count('v_score := v_score - 15;') != 1:
        fail('migration: seule la réduction appareil fiable (-15) est autorisée dans le scoreur')
    if "v_reasons := array_append(v_reasons,'travel_match');" in migration:
        fail('migration: travel_match ne doit plus modifier les raisons de score')
    if 'if coalesce(p_travel_match,false)' in migration:
        fail('migration: travel_match ne doit plus commander une réduction du scoreur')
    for forbidden in ('ip_address', 'raw_ip', 'gps_lat', 'gps_lon', 'latitude numeric', 'longitude numeric'):
        if forbidden in migration.lower():
            fail(f'migration: collecte précise interdite détectée: {forbidden}')

    for needle in (
        "70::integer,\n  'Mode Voyage ne réduit directement aucun signal dans le scoreur'",
        "'score 70 reste high'",
        "'appareil principal et fiable restent bornés à 0, sans bonus voyage'",
    ):
        if needle not in risk_test:
            fail(f'contrat risque V25: preuve geo-only absente: {needle}')

    for needle in (
        'select plan(8);',
        "50::integer,\n  'Mode Voyage ne réduit ni appareil inconnu ni action sensible'",
        "25::integer,\n  'Mode Voyage ne réduit pas une récupération récente'",
        "30::integer,\n  'Mode Voyage ne réduit pas le signal voyage impossible'",
        "20::integer,\n  'travel_match ne réduit pas directement le composant géographique dans le scoreur'",
        "v_unexpected_region := v_previous.country_code <> v_country and not v_travel_match",
        "position('if v_impossible_travel then' in body)>0",
        "position(\n        'v_force_challenge := true;'",
        ") < position(\n        'end if;'",
        "v_force_challenge := true",
    ):
        if needle not in travel_test:
            fail(f'pgTAP Mode Voyage: preuve absente: {needle}')

    workflow_lines = lines(workflow)
    if workflow_lines.count(TRAVEL_TEST_TRIGGER) != 2:
        fail('workflow: le test Mode Voyage doit déclencher PR + push main')
    if workflow_lines.count(GUARD_TRIGGER) != 2:
        fail('workflow: le garde Mode Voyage doit déclencher PR + push main')
    if workflow_lines.count(TRAVEL_TEST_COMMAND) != 1:
        fail('workflow: commande pgTAP Mode Voyage absente ou dupliquée')
    if workflow_lines.count(SELF_TEST_COMMAND) != 1:
        fail('workflow: auto-test Mode Voyage requis exactement une fois')
    if workflow_lines.count(VALIDATE_COMMAND) != 1:
        fail('workflow: validation Mode Voyage requise exactement une fois')

    if any(line.startswith(MIGRATION_VERSION + ' ') for line in ledger.splitlines()):
        fail('registre production: la migration locale ne doit pas être marquée comme déployée')


def load() -> tuple[str, str, str, str, str]:
    return tuple(path.read_text(encoding='utf-8') for path in (MIGRATION, RISK_TEST, TRAVEL_TEST, WORKFLOW, LEDGER))


def self_test(values: tuple[str, str, str, str, str]) -> None:
    migration, risk_test, travel_test, workflow, ledger = values
    validate_texts(*values)
    global_bonus = migration.replace(
        '  perform p_travel_match;\n',
        "  if coalesce(p_travel_match,false) then\n    v_score := v_score - 15;\n    v_reasons := array_append(v_reasons,'travel_match');\n  end if;\n",
        1,
    )
    mutations = {
        'bonus voyage global': (global_bonus, risk_test, travel_test, workflow, ledger),
        'ancien contrat score 55': (migration, risk_test.replace('70::integer,', '55::integer,', 1), travel_test, workflow, ledger),
        'preuve appareil/action affaiblie': (migration, risk_test, travel_test.replace('50::integer,', '35::integer,', 1), workflow, ledger),
        'preuve challenge impossible découplée': (
            migration,
            risk_test,
            travel_test.replace("      ) < position(\n        'end if;'", "      ) > position(\n        'end if;'", 1),
            workflow,
            ledger,
        ),
        'pgTAP Mode Voyage non exécuté': (migration, risk_test, travel_test, workflow.replace('          ' + TRAVEL_TEST_COMMAND + '\n', '', 1), ledger),
        'garde non déclenché': (migration, risk_test, travel_test, workflow.replace("      - 'scripts/validate_security_travel_scope_v25.py'\n", '', 1), ledger),
        'empreinte migration changée': (migration + '\n-- mutation non revue\n', risk_test, travel_test, workflow, ledger),
        'faux déploiement production': (migration, risk_test, travel_test, workflow, ledger + f'\n{MIGRATION_VERSION} sinjira_v25_travel_mode_geo_scope_hardening\n'),
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
        print('OK Mode Voyage V25: aucun bonus global, migration locale verrouillée, production non déployée.')


if __name__ == '__main__':
    main()
