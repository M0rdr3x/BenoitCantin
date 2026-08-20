#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260820000500_sinjira_v24_4_79_community_safety_center.sql'
TEST=ROOT/'supabase/tests/community_safety_v24_4_79.test.sql'
COMMON=ROOT/'assets/js/sinjira-social-common.js'
SAFETY=ROOT/'assets/js/sinjira-social-safety-v24-4-79.js'
CENTER=ROOT/'assets/js/sinjira-social-safety-center-v24-4-79.js'
REAL=ROOT/'assets/js/sinjira-community-real.js'
CHAR=ROOT/'assets/js/sinjira-community-character.js'
SECURITY=ROOT/'compte/securite.html'
COMMUNITY=ROOT/'compte/communaute.html'
CHAR_PAGE=ROOT/'compte/reseau-personnage.html'
CSS=ROOT/'assets/css/sinjira-social-safety-v24-4-79.css'
ADMIN_EDGE=ROOT/'supabase/functions/admin-social-v20/index.ts'
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
    common=COMMON.read_text('utf-8',errors='ignore')
    safety=SAFETY.read_text('utf-8',errors='ignore')
    center=CENTER.read_text('utf-8',errors='ignore')
    real=REAL.read_text('utf-8',errors='ignore')
    char=CHAR.read_text('utf-8',errors='ignore')
    security=SECURITY.read_text('utf-8',errors='ignore')
    community=COMMUNITY.read_text('utf-8',errors='ignore')
    char_page=CHAR_PAGE.read_text('utf-8',errors='ignore')
    css=CSS.read_text('utf-8',errors='ignore')
    admin=ADMIN_EDGE.read_text('utf-8',errors='ignore')
    ledger=LEDGER.read_text('utf-8',errors='ignore')

    require(mig,[
        'public.social_report_content','public.social_my_blocks','public.social_unblock_user','public.social_my_reports',
        "'snapshot_source','server'","'identity_data_included',false",'social_real_posts','social_real_comments',
        'social_character_posts','social_character_comments','social_real_messages','social_character_messages',
        'SOCIAL_REPORT_SELF_FORBIDDEN','SOCIAL_REPORT_ALREADY_OPEN','SOCIAL_REPORT_RATE_LIMIT',"interval '1 hour'",
        'public.sinjira_can_social_interact','public.social_is_blocked','insert into public.social_blocks',
        'where b.blocker_user_id=auth.uid()','where r.reporter_user_id=auth.uid()',
        'revoke all on function public.social_report_content','grant execute on function public.social_report_content'
    ],'migration V24.4.79')
    forbid(mig,['openai','anthropic','stripe','twilio','pg_net','http_post','snapshot jsonb'],'migration V24.4.79')

    require(common,["rpc('social_report_content'",'SOCIAL_RUNTIME_VERSION=\'24.4.79\''],'helper social commun')
    forbid(common,[".from('social_reports').insert",'.from("social_reports").insert'],'helper social commun')
    require(safety,['Sécurité communautaire','snapshot utilisé comme preuve',"rpc('social_report_content'",'p_block:block'],'dialogue signalement')
    require(real,['data-report-comment','openSocialReport','UI_VERSION=\'24.4.79\''],'Communauté réelle')
    require(char,['data-report-comment','openSocialReport','UI_VERSION=\'24.4.79\''],'Réseau personnage')
    require(center,["rpc('social_my_blocks'","rpc('social_unblock_user'","rpc('social_my_reports'",'Débloquer'],'centre sécurité client')
    require(security,['Blocages et signalements','data-social-blocks','data-social-reports','sinjira-social-safety-center-v24-4-79.js'],'page Sécurité')
    require(community,['data-social-runtime="24.4.79"','sinjira-social-safety-v24-4-79.css','Gérer mes blocages et signalements'],'page Communauté')
    require(char_page,['data-social-runtime="24.4.79"','sinjira-social-safety-v24-4-79.css','Mes blocages et signalements'],'page Réseau personnage')
    require(css,['.social-report-dialog','.social-safety-grid','.social-report-status'],'styles V24.4.79')
    require(test,['select plan(20)','snapshot_source','social_my_blocks','social_my_reports'],'pgTAP V24.4.79')
    require(admin,['canonicalUser','reportTargetUser'],'admin social canonique')
    forbid(admin,['if(snap.user_id)','if(snap.sender_user_id)','return snap.user_id','return snap.sender_user_id'],'admin social canonique')

    if '20260820000500 sinjira_v24_4_79_community_safety_center' in ledger:
        raise AssertionError('la migration V24.4.79 est future et ne doit pas être déclarée production avant application réelle')

    print('OK V24.4.79: signalements communautaires canoniques, commentaires signalables, blocage unifié et centre self-only sans snapshot client arbitraire.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())