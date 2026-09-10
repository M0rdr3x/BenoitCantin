#!/usr/bin/env python3
"""Contrat fail-closed pour la réassociation de session d'un appareil SINJIRA V25."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / 'supabase' / 'migrations' / '20260910150000_sinjira_v25_device_session_rebind_security_hardening.sql'
SMOKE = ROOT / 'scripts' / 'smoke_device_challenge_continuity_local.py'


def fail(message: str) -> None:
    raise SystemExit(f'ERREUR réassociation session appareil V25: {message}')


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def validate_text(migration: str, smoke: str) -> None:
    required_migration = (
        'create or replace function sinjira_security_internal.security_register_device(',
        'security definer',
        'set search_path = pg_catalog, public, auth',
        'v_session_changed boolean := false;',
        'v_trust_dropped boolean := false;',
        'where user_id=v_user and device_key=p_device_key\n  for update;',
        'v_session_changed := v_session is null or v_row.last_session_id is distinct from v_session;',
        'v_trust_dropped := v_session_changed and (v_row.is_trusted or v_row.is_primary);',
        'is_trusted=case when v_session_changed then false else is_trusted end,',
        'is_primary=case when v_session_changed then false else is_primary end',
        'if v_trust_dropped then',
        "'device_session_rebind_trust_reset'",
        "'La confiance de cet appareil a été retirée après un changement de session.'",
        'revoke all on function sinjira_security_internal.security_register_device(text,text,text,text) from public, anon;',
        'grant execute on function sinjira_security_internal.security_register_device(text,text,text,text) to authenticated, service_role;',
        "'is_current',(v_session is not null and v_row.last_session_id=v_session)",
    )
    for marker in required_migration:
        require(marker in migration, f'invariant SQL absent: {marker}')

    forbidden_migration = (
        'create or replace function public.security_register_device(',
        "'device_key',v_row.device_key",
        "'last_session_id',v_row.last_session_id",
        'is_trusted=true',
        'is_primary=true',
    )
    for marker in forbidden_migration:
        require(marker not in migration, f'capacité ou secret interdit dans la migration: {marker}')

    event_start = migration.find('if v_trust_dropped then')
    event_end = migration.find('end if;', event_start)
    require(event_start >= 0 and event_end > event_start, 'bloc audit réassociation introuvable')
    event_block = migration[event_start:event_end]
    for secret_marker in ('p_device_key', 'device_key', 'v_session', 'last_session_id'):
        require(secret_marker not in event_block, f'audit de réassociation expose un secret: {secret_marker}')

    required_smoke = (
        'rebound_a = register_device(aal1_c, DEVICE_A,',
        'rebound_a.get("id") == device_a.get("id")',
        'rebound_a.get("is_trusted") is False',
        'rebound_a.get("is_primary") is False',
        'retrust_rebound = rpc_response("security_set_device_trust", aal1_c, {',
        'expect_rpc_refused(retrust_rebound, "AAL2_REQUIRED",',
    )
    for marker in required_smoke:
        require(marker in smoke, f'preuve HTTP de réassociation absente: {marker}')

    blocked_index = smoke.find('blocked_c = vault_open(')
    rebind_index = smoke.find('rebound_a = register_device(aal1_c, DEVICE_A,')
    cleanup_index = smoke.find('cleanup_b = request(')
    require(blocked_index >= 0 and blocked_index < rebind_index < cleanup_index,
            'le test de réassociation doit se produire après le scénario C et avant le nettoyage final')

    require('aal2_c, DEVICE_A' not in smoke[rebind_index:cleanup_index],
            'la preuve de réassociation doit utiliser la session AAL1 copiée, pas une session AAL2')


def self_test(migration: str, smoke: str) -> None:
    mutations: dict[str, tuple[str, str]] = {
        'session absente non fail-closed': (
            migration.replace(
                'v_session is null or v_row.last_session_id is distinct from v_session',
                'v_row.last_session_id is distinct from v_session',
                1,
            ),
            smoke,
        ),
        'comparaison de session inversée': (
            migration.replace(
                'v_row.last_session_id is distinct from v_session',
                'v_row.last_session_id is not distinct from v_session',
                1,
            ),
            smoke,
        ),
        'verrou de ligne retiré': (
            migration.replace('\n  for update;', '', 1),
            smoke,
        ),
        'confiance conservée au rebind': (
            migration.replace(
                'is_trusted=case when v_session_changed then false else is_trusted end,',
                'is_trusted=is_trusted,',
                1,
            ),
            smoke,
        ),
        'primaire conservé au rebind': (
            migration.replace(
                'is_primary=case when v_session_changed then false else is_primary end',
                'is_primary=is_primary',
                1,
            ),
            smoke,
        ),
        'confiance toujours supprimée': (
            migration.replace(
                'is_trusted=case when v_session_changed then false else is_trusted end,',
                'is_trusted=false,',
                1,
            ),
            smoke,
        ),
        'primaire toujours supprimé': (
            migration.replace(
                'is_primary=case when v_session_changed then false else is_primary end',
                'is_primary=false',
                1,
            ),
            smoke,
        ),
        'audit non borné au retrait de confiance': (
            migration.replace('if v_trust_dropped then', 'if v_session_changed then', 1),
            smoke,
        ),
        'audit expose la clé': (
            migration.replace(
                "'La confiance de cet appareil a été retirée après un changement de session.'",
                "'Clé appareil: ' || p_device_key",
                1,
            ),
            smoke,
        ),
        'implémentation privilégiée recréée dans public': (
            migration.replace(
                'create or replace function sinjira_security_internal.security_register_device(',
                'create or replace function public.security_register_device(',
                1,
            ),
            smoke,
        ),
        'device_key renvoyée': (
            migration.replace(
                "'id',v_row.id,",
                "'device_key',v_row.device_key,\n      'id',v_row.id,",
                1,
            ),
            smoke,
        ),
        'session renvoyée': (
            migration.replace(
                "'id',v_row.id,",
                "'last_session_id',v_row.last_session_id,\n      'id',v_row.id,",
                1,
            ),
            smoke,
        ),
        'rebind HTTP retiré': (
            migration,
            smoke.replace('rebound_a = register_device(aal1_c, DEVICE_A,', 'rebound_removed = register_device(aal1_c, DEVICE_A,', 1),
        ),
        'rebind testé en AAL2': (
            migration,
            smoke.replace('rebound_a = register_device(aal1_c, DEVICE_A,', 'rebound_a = register_device(aal2_c, DEVICE_A,', 1),
        ),
        'identité stable non vérifiée': (
            migration,
            smoke.replace('rebound_a.get("id") == device_a.get("id")', 'True', 1),
        ),
        'confiance tombée non vérifiée': (
            migration,
            smoke.replace('rebound_a.get("is_trusted") is False', 'True', 1),
        ),
        'primaire tombé non vérifié': (
            migration,
            smoke.replace('rebound_a.get("is_primary") is False', 'True', 1),
        ),
        'AAL2 après rebind non vérifié': (
            migration,
            smoke.replace('expect_rpc_refused(retrust_rebound, "AAL2_REQUIRED",', 'expect_rpc_refused(retrust_rebound, "OTHER",', 1),
        ),
    }

    for label, (mutated_migration, mutated_smoke) in mutations.items():
        if mutated_migration == migration and mutated_smoke == smoke:
            fail(f'auto-test invalide, mutation sans effet: {label}')
        try:
            validate_text(mutated_migration, mutated_smoke)
        except SystemExit:
            continue
        fail(f'auto-test non détecté: {label}')

    print(f'OK: {len(mutations)}/{len(mutations)} mutations critiques de réassociation détectées')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()

    require(MIGRATION.is_file(), f'migration absente: {MIGRATION.relative_to(ROOT)}')
    require(SMOKE.is_file(), f'smoke absent: {SMOKE.relative_to(ROOT)}')
    migration = MIGRATION.read_text('utf-8')
    smoke = SMOKE.read_text('utf-8')

    if args.self_test:
        self_test(migration, smoke)
    else:
        validate_text(migration, smoke)
        print('OK réassociation session appareil V25: changement de session => confiance retirée, preuve AAL2 requise.')


if __name__ == '__main__':
    main()
