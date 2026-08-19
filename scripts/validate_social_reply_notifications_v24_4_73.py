#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260819015843_sinjira_v24_4_73_social_reply_notifications.sql'
FOCUS=ROOT/'assets/js/sinjira-social-post-focus-v24-4-73.js'
NOTIFY=ROOT/'assets/js/sinjira-user-notifications-v24-4-63.js'
NOTIFY_PAGE=ROOT/'compte/notifications.html'
REAL_PAGE=ROOT/'compte/communaute.html'
CHAR_PAGE=ROOT/'compte/reseau-personnage.html'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'


def require(text,markers,label):
    missing=[m for m in markers if m not in text]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text,markers,label):
    found=[m for m in markers if m in text]
    if found: raise AssertionError(f'{label}: marqueurs interdits: {found}')


def main():
    migration=MIG.read_text('utf-8',errors='ignore')
    focus=FOCUS.read_text('utf-8',errors='ignore')
    notify=NOTIFY.read_text('utf-8',errors='ignore')
    notify_page=NOTIFY_PAGE.read_text('utf-8',errors='ignore')
    real_page=REAL_PAGE.read_text('utf-8',errors='ignore')
    char_page=CHAR_PAGE.read_text('utf-8',errors='ignore')
    ledger=LEDGER.read_text('utf-8',errors='ignore')

    require(migration,[
        'create or replace function private.notify_social_comment_reply()',
        'security definer',
        'set search_path = pg_catalog, public',
        'v_owner_user_id = new.user_id',
        'notification_preferences np',
        'np.community_activity',
        "v_type := 'social_real_reply'",
        "v_type := 'social_character_reply'",
        "'/compte/communaute.html?post='",
        "'/compte/reseau-personnage.html?post='",
        'insert into public.user_notifications',
        'revoke all on function private.notify_social_comment_reply() from public, anon, authenticated',
        'grant execute on function private.notify_social_comment_reply() to service_role',
        'trg_user_notify_social_real_reply',
        'trg_user_notify_social_character_reply'
    ],'migration avis sociaux')
    forbid(migration,['new.body','pg_net','http_post','send_email','twilio','stripe'],'migration avis sociaux')

    require(focus,[
        "new URLSearchParams(location.search).get('post')",
        'UUID_RE',
        "[data-post]",
        "data-real-feed],[data-character-feed]",
        'MutationObserver',
        "card.dataset.notificationTarget='true'",
        "card.scrollIntoView({behavior:'smooth',block:'center'})"
    ],'focus publication')
    forbid(focus,['innerHTML','eval(','location.href=targetId'],'focus publication')

    require(notify,[
        "social_real_reply:'Communauté'",
        "social_character_reply:'Rôle-play'",
        "path.startsWith('/compte/')"
    ],'centre notifications')
    require(notify_page,[
        'réponses de la Communauté',
        'sinjira-user-notifications-v24-4-63.js?v=24.4.73'
    ],'page notifications')
    require(real_page,['sinjira-social-post-focus-v24-4-73.js?v=24.4.73'],'page Communauté')
    require(char_page,['sinjira-social-post-focus-v24-4-73.js?v=24.4.73'],'page Réseau personnage')
    require(ledger,['20260819015843 sinjira_v24_4_73_social_reply_notifications'],'ledger production')

    print('OK V24.4.73: avis internes de réponse, préférence communauté respectée, auto-réponse ignorée, aucun texte libre copié et ouverture ciblée sécurisée.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
