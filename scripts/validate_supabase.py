#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'
FUN=ROOT/'supabase'/'functions'
CONFIG=ROOT/'supabase'/'config.toml'
FRONTEND=ROOT/'assets'/'js'/'sinjira-supabase-config.js'
WORKFLOW=ROOT/'.github'/'workflows'/'supabase-production-preflight.yml'
EXPECTED='24.4.13'
PROJECT='gpvivleexywljowcqkru'

def read(p:Path)->str:return p.read_text('utf-8',errors='ignore')
def fail(errors:list[str],msg:str):errors.append(msg)

def latest_function(files:list[Path],name:str)->tuple[Path|None,str]:
    rx=re.compile(rf"create\s+(?:or\s+replace\s+)?function\s+(?:public\.)?{re.escape(name)}\s*\([^)]*\).*?\$\$.*?\$\$\s*;",re.I|re.S)
    for p in reversed(files):
        matches=list(rx.finditer(read(p)))
        if matches:return p,matches[-1].group(0)
    return None,''

def main()->int:
    errors=[]
    files=sorted(MIG.glob('*.sql'))
    if not files:fail(errors,'Aucune migration Supabase.')
    versions=[]
    for p in files:
        m=re.match(r'^(\d{14})_[a-z0-9_]+\.sql$',p.name)
        if not m:fail(errors,f'Migration mal nommée: {p.name}')
        else:versions.append(m.group(1))
    if len(set(versions))!=len(versions):fail(errors,'Timestamps de migration dupliqués.')
    if versions!=sorted(versions):fail(errors,'Migrations hors ordre chronologique.')

    sql='\n'.join(read(p) for p in files)
    compact=re.sub(r'\s+','',sql.lower())
    funcs={x.lower() for x in re.findall(r'\bcreate\s+(?:or\s+replace\s+)?function\s+(?:public\.)?([a-z_][a-z0-9_]*)\s*\(',sql,re.I)}
    tables={x.lower() for x in re.findall(r'\bcreate\s+table\s+(?:if\s+not\s+exists\s+)?(?:public\.)?([a-z_][a-z0-9_]*)',sql,re.I)}
    required_funcs={
      'get_sinjira_server_version','get_sinjira_runtime_health','get_sinjira_account_capabilities',
      'is_sinjira_owner','ensure_sinjira_owner_character','has_sinjira_product',
      'create_guardian_signup_invite','sinjira_age_band','sinjira_can_social_interact',
      'fracture_engine_health','fracture_engine_get_state','fracture_engine_start','fracture_engine_submit_accusation',
      'create_fracture_party','join_fracture_party','is_fracture_party_member','sinjira_content_allowed','sinjira_cycle_allowed'
    }
    for name in sorted(required_funcs-funcs):fail(errors,f'RPC critique absente: {name}')

    vp,vb=latest_function(files,'get_sinjira_server_version')
    if not vp or f"select'{EXPECTED}'::text" not in re.sub(r'\s+','',vb.lower()):fail(errors,f'Version serveur finale différente de {EXPECTED}.')
    hp,hb=latest_function(files,'get_sinjira_runtime_health')
    if not hp or f"'platform_version','{EXPECTED}'" not in re.sub(r'\s+','',hb.lower()):fail(errors,f'Runtime health ne déclare pas {EXPECTED}.')

    for table in ('admin_notifications','guardian_signup_invites','products','user_entitlements','character_submissions','characters'):
        if table not in tables:fail(errors,f'Table contractuelle absente des migrations: {table}')
    for table in tables:
        if not re.search(rf'alter\s+table\s+(?:if\s+exists\s+)?(?:public\.)?{re.escape(table)}\s+enable\s+row\s+level\s+security',sql,re.I):
            fail(errors,f'RLS non activée sur {table}')

    source=[]
    for root in (ROOT/'assets'/'js',FUN):
        if root.exists():source.extend(p for p in root.rglob('*') if p.is_file() and p.suffix in {'.js','.ts'})
    source_text='\n'.join(read(p) for p in source)
    called={x.lower() for x in re.findall(r"\.rpc\(\s*['\"]([a-zA-Z_][a-zA-Z0-9_]*)['\"]",source_text)}
    for name in sorted(called-funcs):fail(errors,f'RPC appelée par le code mais absente des migrations: {name}')

    function_dirs={p.name for p in FUN.iterdir() if p.is_dir() and not p.name.startswith('_')} if FUN.exists() else set()
    invoked=set(re.findall(r"\.functions\.invoke\(\s*['\"]([a-zA-Z0-9_-]+)['\"]",source_text))
    for name in sorted(invoked-function_dirs):fail(errors,f'Edge Function invoquée mais absente du dépôt: {name}')
    registry=FUN/'submit-character-questionnaire'/'index.ts'
    if not registry.exists():fail(errors,'Edge Function du Registre absente.')
    else:
        t=read(registry)
        for needle in ("persisted:true","version:VERSION","admin_notification_created","admin_email_sent","participant_email_sent","body?.health===true"):
            if needle not in t:fail(errors,f'Contrat Registre incomplet: {needle}')
        if f"const VERSION='{EXPECTED}'" not in t:fail(errors,f'Version Edge Registre différente de {EXPECTED}.')

    config=read(CONFIG) if CONFIG.exists() else ''
    if f'project_id = "{PROJECT}"' not in config:fail(errors,'config.toml pointe vers le mauvais projet.')
    browser=read(FRONTEND) if FRONTEND.exists() else ''
    if f'https://{PROJECT}.supabase.co' not in browser:fail(errors,'Frontend Supabase: mauvais projet.')
    if 'sb_publishable_' not in browser:fail(errors,'Frontend Supabase: clé publiable moderne absente.')
    if 'service_role' in browser.lower() or 'sb_secret_' in browser.lower():fail(errors,'Clé serveur détectée côté navigateur.')

    workflow=read(WORKFLOW) if WORKFLOW.exists() else ''
    for needle in ('SUPABASE_ACCESS_TOKEN','SUPABASE_DB_PASSWORD','db push --linked --dry-run','inputs.apply == true','ÉTAT PRODUCTION'):
        if needle not in workflow:fail(errors,f'Workflow production incomplet: {needle}')
    if 'migration repair' in workflow.lower():fail(errors,'Le workflow ne doit jamais réparer automatiquement l’historique.')

    trigger_only=('assign_parallel_world_membership','enforce_one_character_per_user','enforce_one_character_submission_per_user','protect_parallel_character_life','sync_character_social_profile','sync_social_profile_from_profile')
    for fn in trigger_only:
        if f'revokeallonfunctionpublic.{fn}()frompublic,anon,authenticated;' not in compact:fail(errors,f'Fonction trigger encore exposée: {fn}')

    definers=re.findall(r'(create\s+(?:or\s+replace\s+)?function\s+.*?\$\$;)',sql,re.I|re.S)
    for block in definers:
        if 'security definer' in block.lower() and 'set search_path' not in block.lower():
            m=re.search(r'function\s+(?:public\.)?([a-z_][a-z0-9_]*)',block,re.I);fail(errors,f'SECURITY DEFINER sans search_path: {m.group(1) if m else "inconnue"}')

    print(f'Validation Supabase V{EXPECTED}: {len(files)} migrations, {len(tables)} tables, {len(funcs)} RPC, {len(function_dirs)} Edge Functions.')
    if errors:
        print(f'ECHEC: {len(errors)} problème(s).')
        for e in errors:print('- '+e)
        return 1
    print('OK: dépôt, runtime, Registre, RLS, propriétaire, jeunesse et déploiement cohérents.')
    return 0

if __name__=='__main__':raise SystemExit(main())
