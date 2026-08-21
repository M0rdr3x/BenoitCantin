#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260819235435_sinjira_v24_4_78_dating_moderation.sql'
MODERATION_V90=ROOT/'supabase/migrations/20260821005919_sinjira_v24_4_90_moderation_decisions_appeals.sql'
TEST=ROOT/'supabase/tests/dating_moderation_v24_4_78.test.sql'
JS=ROOT/'assets/js/sinjira-dating-safety-v24-4-78.js'
PROGRESS=ROOT/'assets/js/sinjira-dating-progress-v24-4-76.js'
ADMIN_EDGE=ROOT/'supabase/functions/admin-social-v20/index.ts'
ADMIN_JS=ROOT/'assets/js/sinjira-admin-social-v20.js'
CSS=ROOT/'assets/css/sinjira-dating-v24-4-76.css'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
PRODUCTION_VERSION='20260819235435'
PRODUCTION_NAME='sinjira_v24_4_78_dating_moderation'


def require(text,markers,label):
    missing=[m for m in markers if m.lower() not in text.lower()]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text,markers,label):
    found=[m for m in markers if m.lower() in text.lower()]
    if found: raise AssertionError(f'{label}: marqueurs interdits: {found}')


def main():
    mig=MIG.read_text('utf-8',errors='ignore')
    moderation_v90=MODERATION_V90.read_text('utf-8',errors='ignore') if MODERATION_V90.exists() else ''
    test=TEST.read_text('utf-8',errors='ignore')
    js=JS.read_text('utf-8',errors='ignore')
    progress=PROGRESS.read_text('utf-8',errors='ignore')
    admin_edge=ADMIN_EDGE.read_text('utf-8',errors='ignore')
    admin_js=ADMIN_JS.read_text('utf-8',errors='ignore')
    css=CSS.read_text('utf-8',errors='ignore')
    ledger=LEDGER.read_text('utf-8',errors='ignore')

    # V24.4.78 reste le contrat de signalement et de blocage immédiat au moment du signalement.
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

    # Depuis V24.4.90, une sanction administrative doit rester réversible. L'éligibilité
    # Rencontres est déjà refusée par private.dating_is_eligible() lorsqu'une social_suspension
    # active existe : il n'est donc plus nécessaire de désactiver le profil ni de fermer les
    # conversations pour faire respecter la suspension.
    require(admin_edge,[
        "snap.source==='dating'",'canonicalUser',"'dating_profiles','id','user_id'",
        "'social_real_comments','id','user_id'","'social_real_messages','id','sender_user_id'",
        "'social_character_comments','id','user_id'","'social_character_messages','id','sender_user_id'",
        'moderation_decisions','moderation_decision_id','restrict_reported_content','review_appeal',
        'DATING_REPORT_HAS_NO_REMOVABLE_PUBLIC_CONTENT'
    ],'Edge admin-social-v20')
    forbid(admin_edge,[
        'suspendDatingForUser',"update({enabled:false})",'a_photo_consent:false','b_photo_consent:false',
        "dating_connections').update({status:'closed'",
        'if(snap.user_id)','if(snap.sender_user_id)','return snap.user_id','return snap.sender_user_id'
    ],'Edge admin-social-v20 réversible')

    if moderation_v90:
        require(moderation_v90,[
            'private.moderation_decisions','private.moderation_appeals','moderation_decision_id',
            "action in ('no_action','hide_content','suspend_social','disable_dating')",
            "appeal_deadline>=decided_at+interval '6 months'"
        ],'migration V24.4.90')

    require(admin_js,[
        'Rencontres SINJIRA™','Personne signalée','Extrait de preuve',"snapshot?.source==='dating'",
        'réversible','review_appeal','Renverser la décision'
    ],'console admin sociale')
    require(test,['select plan(14)','DATING_REPORT_ALREADY_OPEN','social_suspensions','limit 30'],'pgTAP V24.4.78')
    require(ledger,[f'{PRODUCTION_VERSION} {PRODUCTION_NAME}'],'ledger production V24.4.78')
    if MODERATION_V90.exists():
        require(ledger,['20260821005919 sinjira_v24_4_90_moderation_decisions_appeals'],'ledger production V24.4.90')
    if '20260819234500_sinjira_v24_4_78_dating_moderation.sql' in {p.name for p in (ROOT/'supabase/migrations').glob('*.sql')}:
        raise AssertionError('ancien timestamp local V24.4.78 encore présent')

    print(
        f'OK V24.4.78 production {PRODUCTION_VERSION}: signalement Rencontres, preuve bornée, blocage atomique, '
        'suspension appliquée via social_suspensions et modération administrative réversible V24.4.90 sans confiance au snapshot.'
    )
    return 0

if __name__=='__main__':
    raise SystemExit(main())
