#!/usr/bin/env python3
from __future__ import annotations

import argparse,json,re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'projets/sinjira/codex/livre-i-delivery-contract.json'
SQL_TEST=ROOT/'supabase/tests/livre_i_entitlements_read_only_a1.test.sql'
FRONTEND=ROOT/'assets/js'
PRIVATE_EDGE=ROOT/'supabase/functions/get-private-book-url/index.ts'
PRIVATE_READER_EDGE=ROOT/'supabase/functions/get-private-book-reading-url/index.ts'
ACCESS_HELPER=ROOT/'supabase/functions/_shared/privateBook.ts'
TABLE='user_entitlements'


def read(path:Path)->str:return path.read_text('utf-8',errors='ignore')


def validate(root:Path,contract_path:Path,sql_test_path:Path,frontend_path:Path,private_edge_path:Path,reader_edge_path:Path,helper_path:Path)->list[str]:
    errors=[]
    try:contract=json.loads(read(contract_path))
    except Exception as exc:return [f'Contrat Livre I illisible: {exc}']
    full=contract.get('full_edition') or {}
    for key,value in {
        'entitlement_table':TABLE,
        'entitlement_client_mutation_allowed':False,
        'entitlement_anonymous_read_allowed':False,
        'owner_role_creates_entitlement':False,
        'family_access_creates_entitlement':False,
        'child_full_edition_access_allowed':False,
        'client_role_assertion_allowed':False,
    }.items():
        if full.get(key)!=value:errors.append(f'Contrat entitlement inattendu: {key}={full.get(key)!r}, attendu {value!r}.')
    if full.get('access_sources')!=[
        'canonical_product_right','server_verified_owner_role','server_verified_creator_family'
    ]:
        errors.append('Contrat Livre I: sources d accès V25 canoniques inattendues.')
    if full.get('canonical_product_right_sources')!=['active_product_entitlement','paid_order']:
        errors.append('Contrat Livre I: le droit produit canonique doit couvrir entitlement actif + commande paid.')
    try:sql_test=read(sql_test_path)
    except OSError as exc:errors.append(f'Test SQL entitlement absent ou illisible: {exc}');sql_test=''
    for label,marker in {
        'RLS active':'relrowsecurity','SELECT authenticated':"has_table_privilege('authenticated','public.user_entitlements','select')",
        'INSERT interdit':"not has_table_privilege('authenticated','public.user_entitlements','insert')",
        'UPDATE interdit':"not has_table_privilege('authenticated','public.user_entitlements','update')",
        'DELETE interdit':"not has_table_privilege('authenticated','public.user_entitlements','delete')",
        'lecture anonyme interdite':"not has_table_privilege('anon','public.user_entitlements','select')",
        'absence politique de mutation':"cmd in ('INSERT','UPDATE','DELETE','ALL')",
        'liaison auth.uid':"ilike '%auth.uid()%'",'liaison user_id':"ilike '%user_id%'",
    }.items():
        if marker not in sql_test:errors.append(f'Test SQL entitlement incomplet: {label}.')
    try:
        edge=read(private_edge_path);reader=read(reader_edge_path);helper=read(helper_path)
    except OSError as exc:return errors+[f'Porte privée Livre I illisible: {exc}']
    for source_name,source in (('téléchargement',edge),('lecture',reader)):
        for marker in ('serviceClient()','requirePrivateBookAccess(service,user.id)'):
            if marker not in source:errors.append(f'Porte privée {source_name}: contrôle d’accès absent ({marker}).')
    for marker in (
        "service.rpc('is_sinjira_owner',{p_user_id:userId})",
        "if(isOwner===true)return 'owner'",
        "'sinjira_has_full_catalog_access'",
        "if(fullCatalog===true)return 'family'",
        "'has_sinjira_product'",
        "{p_product_slug:LIVRE_I_PRODUCT_SLUG,p_user_id:userId}",
        "if(hasProduct===true)return 'product'",
    ):
        if marker not in helper:errors.append(f'Helper accès Livre I: contrôle absent ({marker}).')
    if ".from('user_entitlements')" in helper:
        errors.append('Helper accès Livre I: lecture directe user_entitlements interdite; utiliser le droit produit canonique.')
    if ".insert(" in helper or ".update(" in helper or ".upsert(" in helper or ".delete(" in helper:
        errors.append('Le helper d’accès ne doit jamais muter user_entitlements ni un rôle.')
    write_rx=re.compile(r"\.from\(\s*['\"]user_entitlements['\"]\s*\)(?:(?!\.from\().){0,600}?\.(?:insert|update|delete|upsert)\s*\(",re.I|re.S)
    if frontend_path.exists():
        for path in sorted(frontend_path.rglob('*')):
            if path.is_file() and path.suffix.lower() in {'.js','.mjs','.ts'} and write_rx.search(read(path)):
                errors.append(f'Écriture client interdite vers user_entitlements: {path.relative_to(root)}')
    return errors


def self_test()->None:
    with TemporaryDirectory() as raw:
        root=Path(raw);frontend=root/'assets/js';frontend.mkdir(parents=True)
        contract=root/'contract.json';sql=root/'test.sql';edge=root/'download.ts';reader=root/'reader.ts';helper=root/'helper.ts'
        contract.write_text(json.dumps({'full_edition':{
            'entitlement_table':TABLE,
            'entitlement_client_mutation_allowed':False,
            'entitlement_anonymous_read_allowed':False,
            'owner_role_creates_entitlement':False,
            'family_access_creates_entitlement':False,
            'child_full_edition_access_allowed':False,
            'client_role_assertion_allowed':False,
            'access_sources':['canonical_product_right','server_verified_owner_role','server_verified_creator_family'],
            'canonical_product_right_sources':['active_product_entitlement','paid_order'],
        }}),encoding='utf-8')
        sql.write_text("relrowsecurity has_table_privilege('authenticated','public.user_entitlements','select') not has_table_privilege('authenticated','public.user_entitlements','insert') not has_table_privilege('authenticated','public.user_entitlements','update') not has_table_privilege('authenticated','public.user_entitlements','delete') not has_table_privilege('anon','public.user_entitlements','select') cmd in ('INSERT','UPDATE','DELETE','ALL') ilike '%auth.uid()%' ilike '%user_id%'",encoding='utf-8')
        edge.write_text('serviceClient(); requirePrivateBookAccess(service,user.id);',encoding='utf-8');reader.write_text('serviceClient(); requirePrivateBookAccess(service,user.id);',encoding='utf-8')
        helper.write_text(
            "service.rpc('is_sinjira_owner',{p_user_id:userId}); if(isOwner===true)return 'owner'; "
            "service.rpc('sinjira_has_full_catalog_access',{p_user_id:userId}); if(fullCatalog===true)return 'family'; "
            "service.rpc('has_sinjira_product',{p_product_slug:LIVRE_I_PRODUCT_SLUG,p_user_id:userId}); "
            "if(hasProduct===true)return 'product';",
            encoding='utf-8'
        )
        (frontend/'library.js').write_text("s.from('user_entitlements').select('product_id')",encoding='utf-8')
        clean=validate(root,contract,sql,frontend,edge,reader,helper)
        if clean:raise AssertionError('Le cas sain doit passer: '+' | '.join(clean))
        (frontend/'library.js').write_text("s.from('user_entitlements').insert({product_id:'x'})",encoding='utf-8')
        if not any('Écriture client interdite' in e for e in validate(root,contract,sql,frontend,edge,reader,helper)):raise AssertionError('Écriture client non détectée')
        (frontend/'library.js').write_text("s.from('user_entitlements').select('product_id')",encoding='utf-8')
        helper.write_text(read(helper)+"\nservice.from('user_entitlements').insert({});",encoding='utf-8')
        if not any('ne doit jamais muter' in e for e in validate(root,contract,sql,frontend,edge,reader,helper)):raise AssertionError('Mutation helper non détectée')
        helper.write_text(read(helper).replace("'has_sinjira_product'","'missing_product_right'",1),encoding='utf-8')
        if not any('has_sinjira_product' in e for e in validate(root,contract,sql,frontend,edge,reader,helper)):raise AssertionError('Retrait du droit produit canonique non détecté')


def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:self_test();print('OK auto-test entitlement Livre I.');return 0
    errors=validate(ROOT,CONTRACT,SQL_TEST,FRONTEND,PRIVATE_EDGE,PRIVATE_READER_EDGE,ACCESS_HELPER)
    if errors:
        print(f'ÉCHEC entitlement Livre I: {len(errors)} problème(s).');[print('- '+e) for e in errors];return 1
    print('OK entitlement Livre I: table commerciale lecture seule, aucune auto-attribution, serveur via owner/famille/droit produit canonique entitlement+paid.')
    return 0

if __name__=='__main__':raise SystemExit(main())
