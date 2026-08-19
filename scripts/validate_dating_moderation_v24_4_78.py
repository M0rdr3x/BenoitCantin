#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260819234500_sinjira_v24_4_78_dating_moderation.sql'
TEST=ROOT/'supabase/tests/dating_moderation_v24_4_78.test.sql'
JS=ROOT/'assets/js/sinjira-dating-safety-v24-4-78.js'
PROGRESS=ROOT/'assets/js/sinjira-dating-progress-v24-4-76.js'
ADMIN_EDGE=ROOT/'supabase/functions/admin-social-v20/index.ts'
ADMIN_JS=ROOT/'assets/js/sinjira-admin-social-v20.js'
CSS=ROOT/'assets/css/sinjira-dating-v24-4-76.css'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'


def require(text,markers,label):
    missing=[m for m in markers if m.lower() not in text.lower()]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text,markers,label):
    found=[m for m in markers if m.lower() in text.lower()]
    if found: raise AssertionError(f'{label}: marqueurs interdits: {found}')


def main():
    mig=MIG.read_text('utf-8',errors='ignore')
    test=TEST.read_text('utf-8',errors='ignore')
    js=JS.read_text('utf-8',errors='ignore')
    progress=PROGRESS.read_text('utf-8',errors='ignore')
    admin_edge=ADMIN_EDGE.read_text('utf-8',errors='ignore')
    admin_js=ADMIN_JS.read_text('utf-8',errors='ignore')
    css=CSS.read_text('utf-8',errors='ignore')
    ledger=LEDGER.read_text('utf-8',errors='ignore')

    require(mig,[
        'private.dating_is_eligible','public.social_suspensions','public.dating_report_connection',
        "'harassment'","'sexual_content'","'pressure'","'scam'","'hate'","'threats'","'impersonation'",
        'DATING_REPORT_ALREADY_OPEN','DATING_REPORT_RATE_LIMIT','limit 30',
        "'source','dating'","'identity_data_included',false",'insert into public.social_reports',
        'insert into public.social_blocks',"status='closed'",'a_photo_consent=false','b_photo_consent=false',
        'revoke all on function public.dating_report_connection(uuid,text,text,boolean) from public,anon',
        'grant execute on function public.dating_report_connection(uuid,text,text,boolean) to authenticated'
    ],'migration V24.4.78')
    forbid(mig,['openai','anthropic','stripe','twilio','pg_net','http_post'],'migration V24.4.78')

    require(js,[
        "s.rpc('dating_report_connection'",'Signaler cette rencontre','maxlength="1200"','Bloquer aussi cette personne',
        'DATING_REPORT_ALREADY_OPEN','DATING_REPORT_RATE_LIMIT','MutationObserver'
    ],'runtime sécurité Rencontres')
    forbid(js,['openai','anthropic','stripe','twilio','.from(\'social_reports\')','.from("social_reports")','.storage.upload('],'runtime sécurité Rencontres')
    require(progress,["import './sinjira-dating-safety-v24-4-78.js'"],'branchement V24.4.78')
    require(css,['.dating-report-panel','.dating-report-block'],'styles V24.4.78')

    require(admin_edge,[
        "snap.source==='dating'",'canonicalUser',"'dating_profiles','id','user_id'",
        "'social_real_comments','id','user_id'","'social_real_messages','id','sender_user_id'",
        "'social_character_comments','id','user_id'","'social_character_messages','id','sender_user_id'",
        'suspendDatingForUser',"update({enabled:false})",'a_photo_consent:false','b_photo_consent:false',
        'DATING_REPORT_HAS_NO_REMOVABLE_PUBLIC_CONTENT'
    ],'Edge admin-social-v20')
    forbid(admin_edge,['if(snap.user_id)','if(snap.sender_user_id)','return snap.user_id','return snap.sender_user_id'],'Edge admin-social-v20')

    require(admin_js,['Rencontres SINJIRA™','Personne signalée','Extrait de preuve','snapshot?.source===\'dating\'','désactive aussi Rencontres'],'console admin sociale')
    require(test,['select plan(14)','DATING_REPORT_ALREADY_OPEN','social_suspensions','limit 30'],'pgTAP V24.4.78')

    if '20260819234500 sinjira_v24_4_78_dating_moderation' in ledger:
        raise AssertionError('la migration V24.4.78 est future sur cette branche et ne doit pas être déclarée production avant application réelle')

    print('OK V24.4.78: signalement Rencontres, preuve bornée, blocage atomique, suspension dating et résolution admin canonique sans confiance au snapshot.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())