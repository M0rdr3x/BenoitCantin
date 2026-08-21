#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260821012018_sinjira_v24_4_92_parallel_world_admin.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
UI=ROOT/'assets/js/sinjira-admin-parallel-v24.js'
LOADER=ROOT/'assets/js/sinjira-admin-social-v20.js'

errors=[]
def read(path):
    if not path.exists():
        errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
        return ''
    return path.read_text('utf-8',errors='ignore')
def compact(value): return re.sub(r'\s+','',value.lower())
def req(ok,msg):
    if not ok: errors.append(msg)

sql=read(MIG); ledger=read(LEDGER); ui=read(UI); loader=read(LOADER)
low=compact(sql); uilow=compact(ui)

req('20260821012018 sinjira_v24_4_92_parallel_world_admin' in ledger,'Ledger production V24.4.92 absent.')

functions=[
 'admin_parallel_list_cycles','admin_parallel_list_responses','admin_parallel_list_stories',
 'admin_parallel_save_cycle','admin_parallel_set_cycle_status','admin_parallel_publish_story','admin_parallel_retract_story'
]
for name in functions:
    req(f'createorreplacefunctionpublic.{name}' in low,f'RPC admin absente: {name}')
    req(f"rpc('{name}'" in uilow,f'Interface admin non reliée à {name}.')

req(low.count('private.require_sinjira_admin_aal2()')>=len(functions),'Toutes les RPC admin ne requièrent pas explicitement AAL2.')
req(low.count('securitydefiner')>=len(functions),'Toutes les RPC admin ne sont pas security definer.')
req('grant execute on function public.admin_parallel_list_cycles() to authenticated,service_role' in sql.lower(),'Grant contrôlé des RPC admin absent.')
req("status in ('closed','published')" in sql.lower(),'Publication de Chronique possible avant fermeture du cycle.')
req("v_kind not in ('collective','individual')" in sql.lower(),'Types de Chroniques non bornés.')
req("p_audience not in ('all','adult','youth')" in sql.lower(),'Audience des Chroniques non bornée.')
req("v_row.status='draft'" in sql.lower() and "v_row.status='open'" in sql.lower() and "v_row.status='closed'" in sql.lower(),'Machine de transitions des cycles incomplète.')
req('sinjira_content_allowed' in sql,'Garde de contenu absent des écritures éditoriales.')

for forbidden in [".from('parallel_world_cycles')",".from('parallel_cycle_responses')",".from('parallel_story_installments')"]:
    req(forbidden not in ui,f'Le navigateur admin écrit/lit directement une table canonique: {forbidden}')
req("import './sinjira-admin-parallel-v24.js'" in loader,'Le module Monde parallèle n’est pas chargé par la console admin.')
req("data.adminpanel!=='parallel-world'" not in uilow,'Contrat onglet dynamique inattendu.')
req("data-admin-panel=\"parallel-world\"" in ui,'Panneau admin Monde parallèle absent.')
req('validation humaine' in ui.lower(),'La publication humaine n’est pas explicitée dans l’interface.')
req('identifiant technique privé' in ui.lower(),'La protection de l’identité technique n’est pas explicitée dans l’interface admin.')

if errors:
    print(f'ECHEC Monde parallèle admin V24.4.92: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK V24.4.92: administration Monde parallèle AAL2, RPC-only, cycles contrôlés, Chroniques humaines et identité technique protégée.')
