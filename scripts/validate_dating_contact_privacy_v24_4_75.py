#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260819223000_sinjira_v24_4_75_dating_contact_privacy.sql'
PAGE=ROOT/'compte/rencontres.html'
JS=ROOT/'assets/js/sinjira-dating-v24-4-75.js'


def require(text,markers,label):
    missing=[m for m in markers if m.lower() not in text.lower()]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text,markers,label):
    found=[m for m in markers if m.lower() in text.lower()]
    if found: raise AssertionError(f'{label}: marqueurs interdits: {found}')


def function_body(sql,name):
    pattern=re.compile(rf'create or replace function\s+{re.escape(name)}\b.*?\bas \$\$(.*?)\$\$;',re.I|re.S)
    match=pattern.search(sql)
    if not match: raise AssertionError(f'fonction SQL introuvable: {name}')
    return match.group(1)


def main():
    migration=MIG.read_text('utf-8',errors='ignore')
    page=PAGE.read_text('utf-8',errors='ignore')
    js=JS.read_text('utf-8',errors='ignore')

    require(migration,[
        'private.dating_contains_contact_info','private.dating_array_contains_contact_info',
        'DATING_CONTACT_INFO_FORBIDDEN','DATING_CONTACT_INFO_FORBIDDEN_BEFORE_REVEAL',
        'dating_profile_contact_guard','dating_preferences_contact_guard',
        'before insert or update on public.dating_profiles','before insert or update on public.dating_preferences',
        'private.dating_is_eligible','not private.dating_contains_contact_info(p.region)',
        'not private.dating_contains_contact_info(p.intro)',
        'public.dating_connections_overview','case when private.dating_contains_contact_info(o.intro)',
        'case when private.dating_contains_contact_info(o.region)',
        'public.dating_send_message','v_my_count>=10 and v_their_count>=10 and coalesce(v_a_consent,false) and coalesce(v_b_consent,false)',
        "interval '2 seconds'","interval '1 hour'",'v_recent>=120',
        'public.social_blocks','dating_social_block_guard',"status in('pending','accepted')",
        'a_photo_consent=false','b_photo_consent=false'
    ],'migration V24.4.75')
    forbid(migration,['openai','anthropic','stripe','twilio','pg_net','http_post'],'migration V24.4.75')

    detector=function_body(migration,'private.dating_contains_contact_info')
    require(detector,['https?://','www\\.','instagram|insta|snapchat','regexp_matches','>=7'],'détecteur coordonnées')

    sender=function_body(migration,'public.dating_send_message')
    require(sender,['social_blocks','DATING_CONTACT_INFO_FORBIDDEN_BEFORE_REVEAL','DATING_RATE_LIMIT','v_my_count>=10','v_their_count>=10','coalesce(v_a_consent,false)','coalesce(v_b_consent,false)'],'envoi chat V24.4.75')

    require(page,[
        'Moteur de compatibilité explicable V24.4.76','aucune coordonnée directe','Confidentialité de la phase anonyme',
        'N’inscrivez pas de courriel, numéro de téléphone, URL','aucune adresse, URL, téléphone ou identifiant social',
        'courriels, téléphones, URL et identifiants sociaux','sinjira-dating-v24-4-75.js?v=24.4.76',
        'sinjira-dating-progress-v24-4-76.js?v=24.4.76','Le seuil n’oblige jamais à se dévoiler'
    ],'page Rencontres V24.4.76')
    forbid(page,['sinjira-dating-v24-4-74.js?v=24.4.74'],'page Rencontres V24.4.76')

    require(js,[
        'function containsContactInfo','function profileContainsContactInfo',
        'DATING_CONTACT_INFO_FORBIDDEN_BEFORE_REVEAL','DATING_CONTACT_INFO_FORBIDDEN','DATING_RATE_LIMIT',
        'if(profileContainsContactInfo())throw new Error',
        '!info?.identity_revealed&&containsContactInfo(body)',
        "s.rpc('dating_send_message'","s.rpc('dating_connections_overview')"
    ],'runtime V24.4.75')
    forbid(js,['openai','anthropic','stripe','twilio','type="file"','storage.upload'],'runtime V24.4.75')

    print('OK V24.4.76: protections V24.4.75 conservées et nouvelle interface de progression branchée sans affaiblir la confidentialité.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())