#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260819221038_sinjira_v24_4_74_compatibility_dating_private.sql'
PAGE=ROOT/'compte/rencontres.html'
JS=ROOT/'assets/js/sinjira-dating-v24-4-74.js'
COMMUNITY=ROOT/'compte/communaute.html'
NOTIFY=ROOT/'assets/js/sinjira-user-notifications-v24-4-63.js'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'


def require(text,markers,label):
    missing=[m for m in markers if m.lower() not in text.lower()]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text,markers,label):
    found=[m for m in markers if m.lower() in text.lower()]
    if found: raise AssertionError(f'{label}: marqueurs interdits: {found}')


def main():
    migration=MIG.read_text('utf-8',errors='ignore')
    page=PAGE.read_text('utf-8',errors='ignore')
    js=JS.read_text('utf-8',errors='ignore')
    community=COMMUNITY.read_text('utf-8',errors='ignore')
    notify=NOTIFY.read_text('utf-8',errors='ignore')
    ledger=LEDGER.read_text('utf-8',errors='ignore')

    require(migration,[
        'create table if not exists public.dating_profiles',
        'create table if not exists public.dating_preferences',
        'create table if not exists public.dating_connections',
        'create table if not exists public.dating_messages',
        'alter table public.dating_profiles enable row level security',
        'alter table public.dating_messages enable row level security',
        'revoke all on public.dating_profiles, public.dating_preferences, public.dating_connections, public.dating_messages from public, anon, authenticated',
        "private.dating_age(p_user_id) >= 18",
        "s.relationship_status='single'",
        'p.serious_intent_confirmed is true',
        "p.single_confirmed_at >= now()-interval '90 days'",
        'public.dating_compatibility_candidates',
        'public.dating_request_conversation',
        'public.dating_respond_connection',
        'public.dating_send_message',
        'public.dating_set_photo_consent',
        'v_my<10 or v_their<10',
        "notification_type,title,body",
        "'dating'",
        "'/compte/rencontres.html'",
        "array['core_value','conflict_style','decision_style','sociability','trust_style','natural_role']"
    ],'migration Rencontres')
    forbid(migration,[
        'photo_path text','image_path text','attachment','pg_net','http_post','send_email','twilio','stripe','openai','anthropic'
    ],'migration Rencontres')

    require(page,[
        '18+ · célibataires · relations sérieuses',
        'Rencontres par compatibilité',
        'aucune photo',
        '10 messages envoyés par chaque personne',
        'data-dating-profile-form','data-dating-candidates','data-dating-connections','data-dating-message-form',
        'sinjira-dating-v24-4-74.js?v=24.4.74',
        'Utiliser volontairement certains repères non sensibles de mon questionnaire du Registre'
    ],'page Rencontres')
    forbid(page,['type="file"','accept="image','data-like','data-swipe','Tinder','Bumble'],'page Rencontres')

    require(js,[
        'requireCommunityUser',
        "s.from('dating_profiles')",
        "s.from('dating_preferences')",
        "s.rpc('dating_self_status')",
        "s.rpc('dating_compatibility_candidates'",
        "s.rpc('dating_request_conversation'",
        "s.rpc('dating_respond_connection'",
        "s.rpc('dating_send_message'",
        "s.rpc('dating_set_photo_consent'",
        'photo_unlock_available',
        'identity_revealed',
        'avatarUrl(item.revealed_avatar_path)',
        'Vous : ${Number(item.my_message_count||0)}/10',
        'use_registry_answers'
    ],'runtime Rencontres')
    forbid(js,[
        ".from('dating_connections')", ".from('dating_messages')", '.storage.upload(', 'functions.invoke(', 'fetch("http', "fetch('http", 'openai', 'anthropic', 'stripe', 'data-like', 'swipe'
    ],'runtime Rencontres')

    require(community,['href="rencontres.html"','Rencontres par compatibilité'],'Communauté')
    require(notify,["dating:'Rencontres'"],'notifications')
    require(ledger,['20260819221038 sinjira_v24_4_74_compatibility_dating_private'],'ledger')

    print('OK V24.4.74: Rencontres 18+ privées, célibataire/serious-only, compatibilité explicable, Registre opt-in, aucune photo de sélection, messagerie texte et dévoilement mutuel après 10 messages chacun.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
