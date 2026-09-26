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
req("public.sinjira_age_band(uid)" in m and "coalesce(band,'unverified')notin('adult','youth')" in m,'La garde sensible ne ferme pas les bandes non standard.')
req("raiseexception'child_action_not_available_11_12'" in m,'Code de refus child absent.')
req("tg_table_name='playtest_participants'" in m and "public.sinjira_age_band(new.user_id)" in m and "account_target_not_available_restricted" in m,'Une invitation Playtest adulte/admin peut encore cibler une bande non standard.')
for table in ('access_requests','playtest_participants','parallel_responses','parallel_character_state','market_listings','market_favorites','license_redemptions','product_preorders','orders','order_items','employment_profiles','employment_applications','game_sessions','player_sheets','endgame_sheets','novel_comments','reader_comments','sinjira_novel_comments'):
    req(f"'{table}'" in m,f'Table sensible non couverte: {table}')
req('createorreplacefunctionprivate.sinjira_child_research_consent_guard()' in m,'Garde contribution child absente.')
req('new.participate:=false' in m and 'new.share_free_text:=false' in m and "coalesce(band,'unverified')notin('adult','youth')" in m,'Contribution des bandes non standard non forcée à OFF.')
req("public.sinjira_my_age_band()in('adult','youth')" in m,'Politiques sensibles sans garde fail-closed adult/youth.')
req('droppolicyifexistsplaytests_read_authorizedonpublic.playtests' in m and 'createpolicyplaytests_read_authorizedonpublic.playtestsforselecttoauthenticated' in m,'L ancienne politique SELECT Playtests n est pas remplacée canoniquement.')
req('droppolicyifexistsplaytest_participants_read_authorizedonpublic.playtest_participants' in m and 'createpolicyplaytest_participants_read_authorizedonpublic.playtest_participantsforselecttoauthenticated' in m,'La lecture des participations Playtests ne remplace pas la politique héritée.')
req('droppolicyifexists"participantsownselect"onpublic.playtest_participants' in m,'La politique historique "participants own select" n est pas retirée.')
req("public.sinjira_my_age_band()in('adult','youth')and(public.is_sinjira_admin" in m,'La politique Playtests canonique n exige pas une bande standard avant les exceptions admin/historique.')
projects_start=m.find('createpolicy"projectsreadablewhenaccessible"')
projects_end=m.find('droppolicyifexists"approveddocumentsvisiblebyaccess"',projects_start)
projects_policy=m[projects_start:projects_end] if projects_start>=0 and projects_end>projects_start else ''
documents_start=m.find('createpolicy"approveddocumentsvisiblebyaccess"')
documents_end=m.find('--uneseulepolitiqueselectplaytestsdoitresteractive',documents_start)
documents_policy=m[documents_start:documents_end] if documents_start>=0 and documents_end>documents_start else ''
req(projects_policy and "(selectauth.uid())isnullorpublic.sinjira_my_age_band()in('adult','youth')" in projects_policy,
    'Avant le classement 11–12, la policy projets ne ferme pas child tout en conservant anon public.')
req(documents_policy and "(selectauth.uid())isnullorpublic.sinjira_my_age_band()in('adult','youth')" in documents_policy and "sinjira_my_age_band()='child'" not in documents_policy,
    'Avant le classement 11–12, la policy documents expose encore du contenu non classé à child.')

for marker in (
    'droppolicyifexistsadmin_read_all_projectsonpublic.projects',
    'droppolicyifexistsprojects_readonpublic.projects',
    'droppolicyifexistsprojects_public_readonpublic.projects',
    'droppolicyifexistsprojects_authenticated_readonpublic.projects',
):
    req(0 <= m.find(marker) < projects_start,
        f'Une ancienne policy projets permissive peut encore contourner le garde child avant classement: {marker}')
for marker in (
    'droppolicyifexistsdocuments_read_by_accessonpublic.documents',
    'droppolicyifexistsadmin_read_all_documentsonpublic.documents',
    'droppolicyifexistsdocuments_anon_readonpublic.documents',
    'droppolicyifexistsdocuments_authenticated_readonpublic.documents',
):
    req(0 <= m.find(marker) < documents_start,
        f'Une ancienne policy documents permissive peut encore contourner le garde child avant classement: {marker}')

req("service.rpc('sinjira_age_band',{p_user_id:user.id})" in d,'get-document-url ne vérifie pas l âge serveur.')
req("ageband==='child'" in d and "doc.child_access_status!=='approved_11_12'" in d and "doc.projects?.child_access_status!=='approved_11_12'" in d,'get-document-url ne revérifie pas le classement 11–12 document + projet.')
req("!['adult','youth','child'].includes(ageband)" in d and 'account_access_restricted' in d,'get-document-url ne ferme pas les bandes authentifiées restreintes.')
req("service.rpc('sinjira_age_band',{p_user_id:user.id})" in a,'Mon IA ne vérifie pas l âge serveur.')
req("normalizedageband==='child'" in a and 'personal_ai_not_available_11_12' in a,'Mon IA n est pas bloqué pour child.')
req("!['adult','youth'].includes(normalizedageband)" in a and 'personal_ai_account_restricted' in a,'Mon IA ne ferme pas les bandes non standard.')
req("normalizedageband==='child'" in l and 'child_action_not_available_11_12' in l,'L activation de licence Edge n est pas refusée à 11–12 ans.')
req("!['adult','youth'].includes(normalizedageband)" in l and 'account_action_not_available_restricted' in l,'L activation de licence Edge ne ferme pas les bandes non standard.')
for edge_name,edge_text in (('téléchargement Livre I',bd),('lecture Livre I',br)):
    req("service.rpc('sinjira_age_band',{p_user_id:user.id})" in edge_text,f'{edge_name}: vérification d âge serveur absente.')
    req("normalizedageband==='child'" in edge_text and 'book_not_available_11_12' in edge_text,f'{edge_name}: contenu privé non classé encore ouvert aux 11–12 ans.')
    req("!['adult','youth'].includes(normalizedageband)" in edge_text and 'book_account_restricted' in edge_text,f'{edge_name}: bande non standard encore ouverte au contenu privé.')

req('selectplan(13);' in t,'Plan pgTAP frontière child inattendu.')
req("with_checkilike'%sinjira_my_age_band%'" in t,'Le pgTAP Playtests ne vérifie pas la cohorte self-only.')
for marker in ('emploiportelagardechild','marchéportelagardechild','demandestesteurportentlagardechild','précommandesportentlagardechild','documentsprivéstiennentcomptedelabandeâge','playtestsrestentréservésauxbandesstandardcôtérls','uneseulepolitiqueselectplaytestsresteactive','lapolitiqueselectplaytestscanoniqueexigeunebandestandard','uneseulepolitiqueselectparticipationsplaytestsresteactive','lalecturedesparticipationsplaytestsexigeunebandestandard','unadulte/adminnepeutpascibleruncomptechilddansuneparticipationplaytest'):
    req(marker in t,f'Preuve pgTAP absente: {marker}')

if errors:
    print(f'ECHEC frontière serveur enfant V25: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK V25: modules non certifiés 11–12 refusés côté serveur; documents privés et Mon IA fermés fail-closed.')
