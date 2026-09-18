#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260918010000_sinjira_v25_child_sensitive_boundary.sql'
TEST=ROOT/'supabase/tests/child_sensitive_boundary_v25.test.sql'
DOC_EDGE=ROOT/'supabase/functions/get-document-url/index.ts'
AI_EDGE=ROOT/'supabase/functions/personal-ai/index.ts'
errors=[]

def read(path):
    if not path.exists():
        errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
        return ''
    return path.read_text('utf-8')

def compact(text): return ''.join(text.lower().split())
def req(cond,msg):
    if not cond: errors.append(msg)

mig=read(MIG); test=read(TEST); doc=read(DOC_EDGE); ai=read(AI_EDGE)
m=compact(mig); t=compact(test); d=compact(doc); a=compact(ai)

req('createorreplacefunctionprivate.sinjira_child_sensitive_write_guard()' in m,'Garde serveur child absente.')
req("public.sinjira_age_band(uid)='child'" in m,'La garde sensible ne vérifie pas la bande child.')
req("raiseexception'child_action_not_available_11_12'" in m,'Code de refus child absent.')
for table in ('access_requests','playtest_participants','parallel_responses','parallel_character_state','market_listings','market_favorites','license_redemptions','product_preorders','orders','order_items','employment_profiles','employment_applications','game_sessions','player_sheets','endgame_sheets','novel_comments','reader_comments','sinjira_novel_comments'):
    req(f"'{table}'" in m,f'Table sensible non couverte: {table}')
req('createorreplacefunctionprivate.sinjira_child_research_consent_guard()' in m,'Garde contribution child absente.')
req('new.participate:=false' in m and 'new.share_free_text:=false' in m,'Contribution child non forcée à OFF.')
req('public.sinjira_age_band((selectauth.uid()))<>\'child\'' in m,'Politiques projet/document/playtest sans garde child.')
req("access_level='public'" in m and "p.visibility='public'" in m,'Documents child ne sont pas limités aux documents publics de projets publics.')

req("service.rpc('sinjira_age_band',{p_user_id:user.id})" in d,'get-document-url ne vérifie pas l âge serveur.')
req("ageband==='child'&&(doc.access_level!=='public'||doc.projects?.visibility!=='public')" in d,'get-document-url ne bloque pas les documents/projets privés pour child.')
req("service.rpc('sinjira_age_band',{p_user_id:user.id})" in a,'Mon IA ne vérifie pas l âge serveur.')
req("ageband==='child'" in a and 'personal_ai_not_available_11_12' in a,'Mon IA n est pas bloqué pour child.')

req('selectplan(8);' in t,'Plan pgTAP frontière child inattendu.')
for marker in ('emploiportelagardechild','marchéportelagardechild','demandestesteurportentlagardechild','précommandesportentlagardechild','documentsprivéstiennentcomptedelabandeâge','playtestsrefusentchildcôtérls'):
    req(marker in t,f'Preuve pgTAP absente: {marker}')

if errors:
    print(f'ECHEC frontière serveur enfant V25: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK V25: modules non certifiés 11–12 refusés côté serveur; documents privés et Mon IA fermés fail-closed.')
