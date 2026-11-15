#!/usr/bin/env python3
"""Refuser une rotation non atomique des jetons Histoire de vie.

Tests négatifs sur sources locales uniquement : zéro données personnelles,
zéro accès à la production, aucune exécution SQL privilégiée.
"""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SQL=ROOT/'supabase/migrations/20261115040500_sinjira_life_story_atomic_delivery_link_rotation.sql'
EDGE=ROOT/'supabase/functions/life-story-export/index.ts'
TEST=ROOT/'supabase/tests/life_story_delivery_rotation_v25.test.sql'
WORKFLOW=ROOT/'.github/workflows/sinjira-life-story-delivery-v24-5-50.yml'

SQL_MARKERS={
    'rôle serveur':"coalesce(auth.jwt()->>'role','') <> 'service_role'",
    'refus anon':'from public, anon, authenticated;',
    'permission serveur':'to service_role;',
    'security definer':'security definer',
    'search_path':'set search_path = \'\'',
    'verrou export':'for update;',
    'destinataires serveur':'jsonb_array_length(v_export.recipients_snapshot) <> v_count',
    'taille limite':'v_count is null or v_count < 1 or v_count > 128',
    'forme des empreintes':"hash.value #>> '{}' !~ '^[a-f0-9]{64}$'",
    'confidentialité source':"v_export.source_boundary <> 'life_story_only'",
    'jetons NULL refusés':"pg_catalog.jsonb_typeof(p_token_hashes) is distinct from 'array'",
    'snapshot NULL refusé':"pg_catalog.jsonb_typeof(v_export.recipients_snapshot) is distinct from 'array'",
    'séparation du registre':'v_export.registry_access_prohibited is distinct from true',
    'statut export':"v_export.status <> 'generated'",
    'bucket attendu':"v_export.storage_bucket is distinct from 'sinjira-life-story-exports'",
    'delete transactionnel':'delete from public.life_story_delivery_links as l',
    'insert transactionnel':'insert into public.life_story_delivery_links',
    'comptage strict':'if v_inserted <> v_count then',
    'expiration SQL':"v_expires_at := pg_catalog.clock_timestamp() + interval '30 days';",
}
EDGE_MARKERS={
    'identité admin':'await requiredAdmin(req)',
    'bucket privé':'await hasVerifiedPrivateLifeStoryBucket(service.storage)',
    'RPC atomique':"service.rpc('service_life_story_rotate_delivery_links'",
    'hashes uniquement':'p_export_id: exportId, p_token_hashes: tokenHashes',
    'erreur RPC':"if (rotationError || !rotation || rotation.link_count !== tokenHashes.length",
    'expiration authentique':'for (const item of responseLinks) item.expires_at = rotation.expires_at;',
    'création jeton':'crypto.getRandomValues(new Uint8Array(32))',
}
WORKFLOW_MARKERS=(
    "python scripts/validate_life_story_atomic_rotation.py --self-test",
    "python scripts/validate_life_story_atomic_rotation.py",
    "supabase/tests/life_story_delivery_rotation_v25.test.sql",
)

def check(sql: str, edge: str, test: str, workflow: str) -> list[str]:
    errors=[]
    for label, marker in SQL_MARKERS.items():
        if marker not in sql:
            errors.append("SQL: "+label)
    for label, marker in EDGE_MARKERS.items():
        if marker not in edge:
            errors.append("Edge: "+label)
    for forbidden in ("from('life_story_delivery_links').delete()",
                      "from('life_story_delivery_links').insert(",
                      "createSignedUrl(", "getPublicUrl("):
        if forbidden in edge:
            errors.append("Edge: ancien procédé non sécurisé "+forbidden)
    chunks=edge.split("if (action === 'create_delivery_links') {",1)
    if len(chunks)!=2:
        errors.append("Edge: branche de création de liens introuvable")
    else:
        chunk=chunks[1].split("if (action === 'revoke') {",1)[0]
        sequence=[
            "await hasVerifiedPrivateLifeStoryBucket(service.storage)",
            "crypto.getRandomValues(new Uint8Array(32))",
            "service.rpc('service_life_story_rotate_delivery_links'",
            "if (rotationError || !rotation || rotation.link_count !== tokenHashes.length",
            "for (const item of responseLinks) item.expires_at = rotation.expires_at;",
            "return privateJson({ ok: true,"
        ]
        positions=[chunk.find(marker) for marker in sequence]
        if any(p<0 for p in positions) or positions!=sorted(positions):
            errors.append("Edge: contrôle du bucket → jetons → RPC → succès")
    if sql.find("for update;") > sql.find("delete from public.life_story_delivery_links as l"):
        errors.append("SQL: le verrou doit précéder le DELETE")
    if sql.find("delete from public.life_story_delivery_links as l") > sql.find("insert into public.life_story_delivery_links"):
        errors.append("SQL: DELETE doit précéder INSERT")
    if "select plan(10);" not in test or "SERVICE_ROLE_REQUIRED" not in test or "pgtap" not in test:
        errors.append("pgtap: tests de rôle et de transaction absents")
    for marker in WORKFLOW_MARKERS:
        if marker not in workflow:
            errors.append("CI: contrôle manquant "+marker)
    return errors

def self_test(sql,edge,test,workflow):
    assert not check(sql,edge,test,workflow),check(sql,edge,test,workflow)
    mutants=[]
    for label,marker in SQL_MARKERS.items():
        if sql.count(marker)!=1:
            raise AssertionError("Mutation SQL impossible: "+label)
        mutants.append((label,check(sql.replace(marker,"/* interdit */",1),edge,test,workflow)))
    for label,marker in EDGE_MARKERS.items():
        if edge.count(marker)<1:
            raise AssertionError("Mutation Edge impossible: "+label)
        mutants.append((label,check(sql,edge.replace(marker,"/* interdit */",1),test,workflow)))
    mutants.append(("ancien DELETE",check(sql,edge+"\nfrom('life_story_delivery_links').delete()",test,workflow)))
    mutants.append(("ancien INSERT",check(sql,edge+"\nfrom('life_story_delivery_links').insert(",test,workflow)))
    mutants.append(("CI désactivée",check(sql,edge,test,workflow.replace(WORKFLOW_MARKERS[0],''))))
    mutants.append(("pgtap désactivé",check(sql,edge,test,workflow.replace(WORKFLOW_MARKERS[2],''))))
    for label,issues in mutants:
        if not issues:
            raise AssertionError("Régression non détectée : "+label)
    print(f"OK: {len(mutants)} mutations de sécurité atomique détectées")

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--self-test',action='store_true')
    args=p.parse_args()
    sources=(SQL.read_text('utf-8'),EDGE.read_text('utf-8'),TEST.read_text('utf-8'),WORKFLOW.read_text('utf-8'))
    if args.self_test:
        self_test(*sources)
    errors=check(*sources)
    if errors:
        print('\n'.join("ERREUR "+x for x in errors))
        return 1
    print('OK: transaction SQL unique, verrou, rôle serveur, hash et contrôles CI')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
