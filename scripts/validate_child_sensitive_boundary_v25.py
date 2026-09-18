#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260918010000_sinjira_v25_child_sensitive_boundary.sql'
TEST=ROOT/'supabase/tests/child_sensitive_boundary_v25.test.sql'
DOC_EDGE=ROOT/'supabase/functions/get-document-url/index.ts'
AI_EDGE=ROOT/'supabase/functions/personal-ai/index.ts'
LICENSE_EDGE=ROOT/'supabase/functions/redeem-license-code/index.ts'
BOOK_DOWNLOAD_EDGE=ROOT/'supabase/functions/get-private-book-url/index.ts'
BOOK_READ_EDGE=ROOT/'supabase/functions/get-private-book-reading-url/index.ts'
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
license_edge=read(LICENSE_EDGE); book_download=read(BOOK_DOWNLOAD_EDGE); book_read=read(BOOK_READ_EDGE)
m=compact(mig); t=compact(test); d=compact(doc); a=compact(ai)
l=compact(license_edge); bd=compact(book_download); br=compact(book_read)

req('createorreplacefunctionprivate.sinjira_child_sensitive_write_guard()' in m,'Garde serveur child absente.')
req("public.sinjira_age_band(uid)='child'" in m,'La garde sensible ne vérifie pas la bande child.')
req("raiseexception'child_action_not_available_11_12'" in m,'Code de refus child absent.')
for table in ('access_requests','playtest_participants','parallel_responses','parallel_character_state','market_listings','market_favorites','license_redemptions','product_preorders','orders','order_items','employment_profiles','employment_applications','game_sessions','player_sheets','endgame_sheets','novel_comments','reader_comments','sinjira_novel_comments'):
    req(f"'{table}'" in m,f'Table sensible non couverte: {table}')
req('createorreplacefunctionprivate.sinjira_child_research_consent_guard()' in m,'Garde contribution child absente.')
req('new.participate:=false' in m and 'new.share_free_text:=false' in m,'Contribution child non forcée à OFF.')
req('public.sinjira_age_band((selectauth.uid()))<>\'child\'' in m,'Politiques projet/document/playtest sans garde child.')
req('droppolicyifexistsplaytests_read_authorizedonpublic.playtests' in m and 'createpolicyplaytests_read_authorizedonpublic.playtestsforselecttoauthenticated' in m,'L ancienne politique SELECT Playtests n est pas remplacée canoniquement.')
req('droppolicyifexistsplaytest_participants_read_authorizedonpublic.playtest_participants' in m and 'createpolicyplaytest_participants_read_authorizedonpublic.playtest_participantsforselecttoauthenticated' in m,'La lecture des participations Playtests ne remplace pas la politique héritée.')
req('droppolicyifexists"participantsownselect"onpublic.playtest_participants' in m,'La politique historique "participants own select" n est pas retirée.')
req("public.sinjira_age_band((selectauth.uid()))<>'child'and(public.is_sinjira_admin" in m,'La politique Playtests canonique ne ferme pas child avant les exceptions admin/historique.')
req("access_level='public'" in m and "p.visibility='public'" in m,'Documents child ne sont pas limités aux documents publics de projets publics.')

req("service.rpc('sinjira_age_band',{p_user_id:user.id})" in d,'get-document-url ne vérifie pas l âge serveur.')
req("ageband==='child'" in d and "doc.child_access_status!=='approved_11_12'" in d and "doc.projects?.child_access_status!=='approved_11_12'" in d,'get-document-url ne revérifie pas le classement 11–12 document + projet.')
req("service.rpc('sinjira_age_band',{p_user_id:user.id})" in a,'Mon IA ne vérifie pas l âge serveur.')
req("ageband==='child'" in a and 'personal_ai_not_available_11_12' in a,'Mon IA n est pas bloqué pour child.')
req("ageband==='child'" in l and 'child_action_not_available_11_12' in l,'L activation de licence Edge n est pas refusée à 11–12 ans.')
for edge_name,edge_text in (('téléchargement Livre I',bd),('lecture Livre I',br)):
    req("service.rpc('sinjira_age_band',{p_user_id:user.id})" in edge_text,f'{edge_name}: vérification d âge serveur absente.')
    req("ageband==='child'" in edge_text and 'book_not_available_11_12' in edge_text,f'{edge_name}: contenu privé non classé encore ouvert aux 11–12 ans.')

req('selectplan(12);' in t,'Plan pgTAP frontière child inattendu.')
for marker in ('emploiportelagardechild','marchéportelagardechild','demandestesteurportentlagardechild','précommandesportentlagardechild','documentsprivéstiennentcomptedelabandeâge','playtestsrefusentchildcôtérls','uneseulepolitiqueselectplaytestsresteactive','lapolitiqueselectplaytestscanoniqueexclutexplicitementchild','uneseulepolitiqueselectparticipationsplaytestsresteactive','lalecturedesparticipationsplaytestsexclutexplicitementchild'):
    req(marker in t,f'Preuve pgTAP absente: {marker}')

if errors:
    print(f'ECHEC frontière serveur enfant V25: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK V25: modules non certifiés 11–12 refusés côté serveur; documents privés et Mon IA fermés fail-closed.')
