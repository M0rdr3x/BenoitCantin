#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
CLIENT=ROOT/'assets/js/sinjira-admin-v18.js'
SERVER=ROOT/'supabase/functions/admin-sinjira-v18/index.ts'
MIG=ROOT/'supabase/migrations/20260817234217_sinjira_v24_4_50_admin_workflow_production.sql'
errors=[]

def need(cond,msg):
    if not cond: errors.append(msg)

client=CLIENT.read_text('utf-8')
server=SERVER.read_text('utf-8')
called=set(re.findall(r"call\('([a-z0-9_]+)'",client))
handled=set(re.findall(r"a==='([a-z0-9_]+)'",server))
missing=sorted(called-handled)
extra_required={'dashboard','list_comments','moderate_comment','list_submissions','create_manual_character','generate_character','audit_log','purge_submission_source','list_characters','canon_overview','save_character'}
need(not missing,'actions appelées par le client mais absentes du serveur: '+', '.join(missing))
need(extra_required <= handled,'actions administrateur critiques absentes: '+', '.join(sorted(extra_required-handled)))
need("source_payload,photo_path" in server,'list_submissions ne charge pas les réponses/photo confidentielles')
need("createSignedUrl" in server and "sinjira-character-sources" in server,'photo confidentielle sans URL signée temporaire')
need("s.from('admin_audit_log')" in server,'journal administrateur non branché')
need("s.from('character_status_events')" in server,'historique des statuts personnage non branché')
need(MIG.exists(),'migration V24.4.50 absente')
if MIG.exists():
    sql=MIG.read_text('utf-8')
    for marker in ('admin_audit_log','character_status_events','sinjira_admin_workflow_health','revoke all on public.admin_audit_log','grant select on public.character_status_events to authenticated'):
        need(marker in sql,'contrat migration admin incomplet: '+marker)

if errors:
    print(f'ECHEC contrat admin V24.4.50: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print(f'OK contrat admin V24.4.50: {len(called)} actions client couvertes; journal, suivi personnage et photo signée alignés.')
