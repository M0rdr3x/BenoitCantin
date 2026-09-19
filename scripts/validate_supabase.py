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
ADMIN_HTML=ROOT/'admin'/'sinjira'/'index.html'
ADMIN_JS=ROOT/'assets'/'js'/'sinjira-admin-v18.js'
EXPECTED='24.4.13'
REGISTRY_EXPECTED='25.1.0'
PROJECT='gpvivleexywljowcqkru'

def read(p:Path)->str:return p.read_text('utf-8',errors='ignore')
def fail(errors:list[str],msg:str):errors.append(msg)

def latest_function(files:list[Path],name:str)->tuple[Path|None,str]:
    rx=re.compile(rf"create\s+(?:or\s+replace\s+)?function\s+(?:(?:public|private)\.)?{re.escape(name)}\s*\([^)]*\).*?\$\$.*?\$\$\s*;",re.I|re.S)
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
    funcs={x.lower() for x in re.findall(r'\bcreate\s+(?:or\s+replace\s+)?function\s+(?:(?:public|private)\.)?([a-z_][a-z0-9_]*)\s*\(',sql,re.I)}
    tables={x.lower() for x in re.findall(r'\bcreate\s+table\s+(?:if\s+not\s+exists\s+)?(?:(?:public|private)\.)?([a-z_][a-z0-9_]*)',sql,re.I)}
    required_funcs={
      'get_sinjira_server_version','get_sinjira_runtime_health','get_sinjira_account_capabilities',
      'is_sinjira_owner','ensure_sinjira_owner_character','has_sinjira_product',
      'create_guardian_signup_invite','sinjira_age_band','sinjira_can_social_interact',
      'fracture_engine_health','fracture_engine_get_state','fracture_engine_start','fracture_engine_submit_accusation',
      'create_fracture_party','join_fracture_party','is_fracture_party_member','sinjira_content_allowed','sinjira_cycle_allowed',
      'admin_sinjira_story_continuity_check','admin_sinjira_promote_extended_story',
      'admin_sinjira_publish_extended_story','admin_sinjira_unpublish_extended_story',
      'admin_sinjira_story_validation_check'
    }
    for name in sorted(required_funcs-funcs):fail(errors,f'RPC critique absente: {name}')

    vp,vb=latest_function(files,'get_sinjira_server_version')
    if not vp or f"select'{EXPECTED}'::text" not in re.sub(r'\s+','',vb.lower()):fail(errors,f'Version serveur finale différente de {EXPECTED}.')
    hp,hb=latest_function(files,'get_sinjira_runtime_health')
    if not hp or f"'platform_version','{EXPECTED}'" not in re.sub(r'\s+','',hb.lower()):fail(errors,f'Runtime health ne déclare pas {EXPECTED}.')

    for table in ('admin_notifications','guardian_signup_invites','products','user_entitlements','character_submissions','characters',
                  'sinjira_extended_stories','sinjira_story_character_presence','sinjira_world_locations',
                  'sinjira_world_travel_rules','sinjira_canon_events','sinjira_canon_event_characters',
                  'sinjira_canon_sources','sinjira_story_claims'):
        if table not in tables:fail(errors,f'Table contractuelle absente des migrations: {table}')
    for table in tables:
        if not re.search(rf'alter\s+table\s+(?:if\s+exists\s+)?(?:(?:public|private)\.)?{re.escape(table)}\s+enable\s+row\s+level\s+security',sql,re.I):
            fail(errors,f'RLS non activée sur {table}')

    extended_contract = {
      'sinjira_effective_story_presence',
      'STORY_CONTINUITY_CONFLICT',
      'STORY_CONTINUITY_INCOMPLETE',
      'SECRET_AUTEUR',
      'bidirectional boolean not null default true',
      "segment_key text not null default 'primary'",
      "status <> 'published'",
      "published_at is null or status='published'",
      'STORY_PUBLIC_AUDIENCE_REQUIRED',
      'STORY_NOT_CANON_EXTENDED',
      'sinjira_extended_stories_published_metadata_check',
      'sinjira_guard_published_story_update',
      'sinjira_guard_published_story_presence',
      'sinjira_invalidate_published_extended_stories',
      'sinjira_world_locations_invalidate_extended_update',
      'sinjira_world_locations_invalidate_extended_delete',
      'sinjira_world_travel_invalidate_extended',
      'sinjira_canon_events_invalidate_extended_insert_delete',
      'sinjira_canon_events_invalidate_extended_update',
      'sinjira_canon_event_characters_invalidate_extended',
      'sinjira_canon_context_invalidate_extended',
      'STORY_LOCATION_NOT_CANON',
      'location_not_canon',
      'central_presence_uncertain',
      "cp.certainty='confirmed'",
      'sinjira_canon_sources',
      'sinjira_story_claims',
      'sinjira_source_is_verified',
      'sinjira_require_verified_provenance',
      'sinjira_require_verified_story_claim',
      'sinjira_guard_published_story_claim',
      'STORY_PROVENANCE_REQUIRED',
      'STORY_PROVENANCE_INCOMPLETE',
      "source_kind in ('roman','bible','author_decision','archive')",
      'CANON_SOURCE_SCOPE_MISMATCH',
      'CANON_PRESENCE_SOURCE_SCOPE_MISMATCH',
      'CLAIM_SOURCE_SCOPE_MISMATCH',
      'STORY_PROVENANCE_SCOPE_MISMATCH',
      'CANON_SOURCE_LOCATOR_REQUIRED',
      'sinjira_canon_events_guard_source_scope',
      'sinjira_canon_events_scope_invalidate_extended',
      'sinjira_prevent_source_supersedes_cycle',
      'sinjira_guard_canon_source_in_use',
      'CANON_SOURCE_KEY_IMMUTABLE',
      'CANON_SOURCE_IN_USE',
      'CANON_SOURCE_SUPERSEDES_CYCLE',
      'CANON_SOURCE_SUPERSEDES_NOT_FOUND',
      'CANON_SOURCE_SUPERSEDES_SCOPE_MISMATCH',
      'CANON_SOURCE_SUPERSEDES_BOOK_MISMATCH',
      'CANON_SOURCE_SUPERSEDES_ALREADY_EXISTS',
      'CANON_SOURCE_CREATE_RETIRED_FORBIDDEN',
      'CANON_SOURCE_RETIRED_FINAL',
      'CANON_SOURCE_SUPERSEDES_KIND_INVALID',
      'sinjira_guard_canon_source_lifecycle',
      'sinjira_canon_sources_guard_lifecycle',
      'sinjira_canon_sources_one_successor_idx',
      'before insert or update of supersedes_source_id,scope,source_kind,book_number on public.sinjira_canon_sources',
      'sinjira_story_provenance_report',
      'admin_sinjira_story_validation_check',
      'sinjira_prevent_canon_source_delete',
      'CANON_SOURCE_DELETE_FORBIDDEN',
      'CANON_SOURCE_RETIRE_REPLACEMENT_REQUIRED',
      'CANON_SOURCE_RETIRE_REFERENCES_REMAIN',
      'verification_status,supersedes_source_id on public.sinjira_canon_sources',
      'sinjira_demote_extended_story_on_edit',
      'sinjira_demote_story_from_child_change',
      'sinjira_extended_stories_demote_on_edit',
      'sinjira_story_presence_demote_canon',
      'sinjira_story_claims_demote_canon',
      "canon_status='PROVISOIRE'",
      'sinjira_story_readiness_report',
      'sinjira_require_story_canon_transition',
      'sinjira_extended_stories_canon_transition_guard',
      'sinjira_extended_stories_canon_workflow_check',
      'STORY_CANON_INSERT_FORBIDDEN',
      'STORY_SAVE_BEFORE_CANON_TRANSITION',
      'STORY_PROMOTION_REQUIRED',
      'admin_sinjira_migrate_canon_source_references',
            'CANON_SOURCE_MIGRATION_REPLACEMENT_INVALID',
      'CANON_SOURCE_MIGRATION_SCOPE_MISMATCH',
      'CANON_SOURCE_MIGRATION_BOOK_MISMATCH',
      'CANON_SOURCE_MIGRATION_REPLACEMENT_NOT_VERIFIED',
      'CANON_SOURCE_MIGRATION_INCOMPLETE',
      "set verification_status='RETIRED'",
      "'source_status','RETIRED'",
      'STORY_PUBLICATION_TIMESTAMP_REQUIRED',
    }
    for needle in sorted(extended_contract):
        if needle.lower() not in sql.lower():
            fail(errors,f'Contrat Canon étendu V25 incomplet: {needle}')

    source=[]
    for root in (ROOT/'assets'/'js',FUN):
        if root.exists():source.extend(p for p in root.rglob('*') if p.is_file() and p.suffix in {'.js','.ts'})
    source_text='\n'.join(read(p) for p in source)
    called={x.lower() for x in re.findall(r"\.rpc\(\s*['\"]([a-zA-Z_][a-zA-Z0-9_]*)['\"]",source_text)}
    for name in sorted(called-funcs):fail(errors,f'RPC appelée par le code mais absente des migrations: {name}')

    function_dirs={p.name for p in FUN.iterdir() if p.is_dir() and not p.name.startswith('_')} if FUN.exists() else set()
    invoked=set(re.findall(r"\.functions\.invoke\(\s*['\"]([a-zA-Z0-9_-]+)['\"]",source_text))
    for name in sorted(invoked-function_dirs):fail(errors,f'Edge Function invoquée mais absente du dépôt: {name}')
    admin_edge=FUN/'admin-sinjira-v18'/'index.ts'
    if not admin_edge.exists():fail(errors,'Edge Function administration SINJIRA V18 absente.')
    else:
        admin_text=read(admin_edge)
        for needle in ("admin_sinjira_story_validation_check","status:requestedCanon==='CANON_ETENDU'?'author_review':status","STORY_VALIDATION_INCOMPLETE"):
            if needle not in admin_text:fail(errors,f'Contrat administration Canon étendu incomplet: {needle}')

    admin_html=read(ADMIN_HTML) if ADMIN_HTML.exists() else ''
    admin_js=read(ADMIN_JS) if ADMIN_JS.exists() else ''
    if not admin_html:fail(errors,'Page administration SINJIRA absente.')
    else:
        m=re.search(r'data-canon-source-form.*?</form>',admin_html,re.I|re.S)
        if not m:fail(errors,'Formulaire source canonique introuvable dans l administration.')
        elif 'value="RETIRED"' in m.group(0):
            fail(errors,'Formulaire source admin: RETIRED ne doit pas être proposé à la création.')
    for needle in ("setCanonSourceAuthorityLock(null);syncCanonSourceScope()","src.scope===scope","replacementKind==='roman'","src.source_kind==='roman'","isAuthoritativeCanonSource","authoritativeOnly","verification_status?.value==='VERIFIED'","classification?.value","canon_status?.value==='CANON'","allowMetaScope","sourceScope=story.anchor_scope","sourceScope=form.elements.source_scope","sourceScope=event?.source_scope"):
        if needle not in admin_js:fail(errors,f'Contrat UI sources canoniques incomplet: {needle}')

    registry=FUN/'submit-character-questionnaire'/'index.ts'
    if not registry.exists():fail(errors,'Edge Function du Registre absente.')
    else:
        t=read(registry)
        for needle in ("persisted:true","version:VERSION","admin_notification_created","admin_email_sent","participant_email_sent"):
            if needle not in t:fail(errors,f'Contrat Registre incomplet: {needle}')
        if "body.health===true" not in t and "body?.health===true" not in t:
            fail(errors,'Contrat Registre incomplet: endpoint health authentifié absent.')
        if f"const VERSION='{REGISTRY_EXPECTED}'" not in t:fail(errors,f'Version Edge Registre différente de {REGISTRY_EXPECTED}.')

    config=read(CONFIG) if CONFIG.exists() else ''
    if f'project_id = "{PROJECT}"' not in config:fail(errors,'config.toml pointe vers le mauvais projet.')
    auth_block=re.search(r'(?ms)^\[auth\]\s*(.*?)(?=^\[|\Z)',config)
    if not auth_block:
        fail(errors,'config.toml: bloc [auth] absent; la reconstruction locale ne garantit pas la politique de mot de passe.')
    else:
        auth=auth_block.group(1)
        if not re.search(r'(?m)^\s*enabled\s*=\s*true\s*(?:#.*)?$',auth):fail(errors,'config.toml: Auth local doit rester activé.')
        if not re.search(r'(?m)^\s*minimum_password_length\s*=\s*12\s*(?:#.*)?$',auth):fail(errors,'config.toml: minimum_password_length doit être 12 pour correspondre au frontend SINJIRA.')
        if not re.search(r'(?m)^\s*password_requirements\s*=\s*""\s*(?:#.*)?$',auth):fail(errors,'config.toml: password_requirements doit rester vide tant que le frontend impose seulement la longueur.')
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
            m=re.search(r'function\s+(?:(?:public|private)\.)?([a-z_][a-z0-9_]*)',block,re.I);fail(errors,f'SECURITY DEFINER sans search_path: {m.group(1) if m else "inconnue"}')

    print(f'Validation Supabase plateforme V{EXPECTED} / Registre V{REGISTRY_EXPECTED}: {len(files)} migrations, {len(tables)} tables, {len(funcs)} RPC, {len(function_dirs)} Edge Functions.')
    if errors:
        print(f'ECHEC: {len(errors)} problème(s).')
        for e in errors:print('- '+e)
        return 1
    print('OK: dépôt, runtime, Registre, RLS public/private, propriétaire, jeunesse, Auth local 12 caractères et déploiement cohérents.')
    return 0

if __name__=='__main__':raise SystemExit(main())
