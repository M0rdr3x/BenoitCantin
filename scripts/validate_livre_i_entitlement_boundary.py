#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'projets/sinjira/codex/livre-i-delivery-contract.json'
SQL_TEST = ROOT / 'supabase/tests/livre_i_entitlements_read_only_a1.test.sql'
FRONTEND = ROOT / 'assets/js'
PRIVATE_EDGE = ROOT / 'supabase/functions/get-private-book-url/index.ts'

TABLE = 'user_entitlements'


def read(path: Path) -> str:
    return path.read_text('utf-8', errors='ignore')


def validate(root: Path, contract_path: Path, sql_test_path: Path, frontend_path: Path, private_edge_path: Path) -> list[str]:
    errors: list[str] = []

    try:
        contract = json.loads(read(contract_path))
    except Exception as exc:
        return [f'Contrat Livre I illisible: {exc}']

    full = contract.get('full_edition') or {}
    expected = {
        'entitlement_table': TABLE,
        'entitlement_client_mutation_allowed': False,
        'entitlement_anonymous_read_allowed': False,
    }
    for key, value in expected.items():
        if full.get(key) != value:
            errors.append(f'Contrat entitlement inattendu: {key}={full.get(key)!r}, attendu {value!r}.')

    try:
        sql_test = read(sql_test_path)
    except OSError as exc:
        errors.append(f'Test SQL entitlement absent ou illisible: {exc}')
        sql_test = ''

    required_sql = {
        'RLS active': "relrowsecurity",
        'SELECT authenticated': "has_table_privilege('authenticated','public.user_entitlements','select')",
        'INSERT interdit': "not has_table_privilege('authenticated','public.user_entitlements','insert')",
        'UPDATE interdit': "not has_table_privilege('authenticated','public.user_entitlements','update')",
        'DELETE interdit': "not has_table_privilege('authenticated','public.user_entitlements','delete')",
        'lecture anonyme interdite': "not has_table_privilege('anon','public.user_entitlements','select')",
        'absence politique de mutation': "cmd in ('INSERT','UPDATE','DELETE','ALL')",
        'liaison auth.uid': "ilike '%auth.uid()%'","+
"        'liaison user_id': "ilike '%user_id%'",
    }
    for label, marker in required_sql.items():
        if marker not in sql_test:
            errors.append(f'Test SQL entitlement incomplet: {label}.')

    try:
        private_edge = read(private_edge_path)
    except OSError as exc:
        errors.append(f'Porte privée Livre I illisible: {exc}')
        private_edge = ''
    for marker in ("serviceClient()", ".from('user_entitlements')", ".eq('user_id',user.id)", ".eq('product_id',product.id)"):
        if marker not in private_edge:
            errors.append(f'Porte privée Livre I: contrôle entitlement absent ({marker}).')

    write_rx = re.compile(
        r"\.from\(\s*['\"]user_entitlements['\"]\s*\)(?:(?!\.from\().){0,600}?\.(?:insert|update|delete|upsert)\s*\(",
        re.I | re.S,
    )
    if frontend_path.exists():
        for path in sorted(frontend_path.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in {'.js', '.mjs', '.ts'}:
                continue
            if write_rx.search(read(path)):
                errors.append(f'Écriture client interdite vers user_entitlements: {path.relative_to(root)}')

    return errors


def self_test() -> None:
    with TemporaryDirectory() as raw:
        root = Path(raw)
        contract = root / 'contract.json'
        sql_test = root / 'test.sql'
        frontend = root / 'assets/js'
        edge = root / 'edge.ts'
        frontend.mkdir(parents=True)

        contract.write_text(json.dumps({
            'full_edition': {
                'entitlement_table': TABLE,
                'entitlement_client_mutation_allowed': False,
                'entitlement_anonymous_read_allowed': False,
            }
        }), encoding='utf-8')
        sql_test.write_text("""
select ok((select relrowsecurity from pg_class where oid='public.user_entitlements'::regclass),'RLS active');
select ok(has_table_privilege('authenticated','public.user_entitlements','select'),'select');
select ok(not has_table_privilege('authenticated','public.user_entitlements','insert'),'insert');
select ok(not has_table_privilege('authenticated','public.user_entitlements','update'),'update');
select ok(not has_table_privilege('authenticated','public.user_entitlements','delete'),'delete');
select ok(not has_table_privilege('anon','public.user_entitlements','select'),'anon');
select is((select count(*) from pg_policies where cmd in ('INSERT','UPDATE','DELETE','ALL')),0,'mutations');
select ok(coalesce(qual,'') ilike '%auth.uid()%' and coalesce(qual,'') ilike '%user_id%','own read');
""", encoding='utf-8')
        edge.write_text("serviceClient(); service.from('user_entitlements').eq('user_id',user.id).eq('product_id',product.id);", encoding='utf-8')
        (frontend / 'library.js').write_text("s.from('user_entitlements').select('product_id')", encoding='utf-8')

        clean = validate(root, contract, sql_test, frontend, edge)
        if clean:
            raise AssertionError('Le cas sain doit passer: ' + ' | '.join(clean))

        (frontend / 'library.js').write_text("s.from('user_entitlements').insert({product_id:'x'})", encoding='utf-8')
        writes = validate(root, contract, sql_test, frontend, edge)
        if not any('Écriture client interdite' in item for item in writes):
            raise AssertionError('Une écriture frontend vers user_entitlements doit être bloquée.')

        (frontend / 'library.js').write_text("s.from('user_entitlements').select('product_id')", encoding='utf-8')
        payload = json.loads(read(contract))
        payload['full_edition']['entitlement_client_mutation_allowed'] = True
        contract.write_text(json.dumps(payload), encoding='utf-8')
        weakened = validate(root, contract, sql_test, frontend, edge)
        if not any('entitlement_client_mutation_allowed' in item for item in weakened):
            raise AssertionError('Le contrat ne doit jamais autoriser la mutation client.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la frontière lecture seule des droits numériques du Livre I.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print('OK auto-test entitlement Livre I.')
        return 0

    errors = validate(ROOT, CONTRACT, SQL_TEST, FRONTEND, PRIVATE_EDGE)
    if errors:
        print(f'ÉCHEC entitlement Livre I: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK entitlement Livre I: lecture propre uniquement côté client, aucune auto-attribution, porte privée liée au droit produit.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
