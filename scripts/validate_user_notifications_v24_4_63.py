#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'/'20260818041444_sinjira_v24_4_63_user_notifications.sql'


def read(path:Path)->str:
    if not path.exists():
        raise AssertionError(f'Fichier absent: {path.relative_to(ROOT)}')
    return path.read_text('utf-8',errors='ignore')


def require(text:str,markers:list[str],label:str)->None:
    missing=[marker for marker in markers if marker.lower() not in text.lower()]
    if missing:
        raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text:str,markers:list[str],label:str)->None:
    found=[marker for marker in markers if marker.lower() in text.lower()]
    if found:
        raise AssertionError(f'{label}: marqueurs interdits présents: {found}')


def main()->int:
    migration=read(MIG)
    compact=re.sub(r'\s+',' ',migration.lower())
    page=read(ROOT/'compte'/'notifications.html')
    dashboard=read(ROOT/'compte'/'index.html')
    client=read(ROOT/'assets'/'js'/'sinjira-user-notifications-v24-4-63.js')
    ledger=read(ROOT/'supabase'/'production-migration-ledger.txt')

    require(migration,[
        'create table if not exists public.user_notifications',
        'alter table public.user_notifications enable row level security',
        'grant select on table public.user_notifications to authenticated',
        'grant update (read_at) on table public.user_notifications to authenticated',
        'user_notifications_read_own',
        'user_notifications_mark_own_read',
        'security definer',
        'set search_path = pg_catalog, public',
        'revoke all on function private.notify_user_status_change() from public, anon, authenticated',
        'trg_user_notify_access_request_status',
        'trg_user_notify_novel_comment_status',
        'trg_user_notify_character_submission_status',
        'trg_user_notify_character_status',
        'trg_user_notify_playtest_status'
    ],'migration notifications')

    forbid(migration,[
        'grant insert on table public.user_notifications to authenticated',
        'grant delete on table public.user_notifications to authenticated',
        'source_payload',
        'review_note',
        'application_message',
        'new.body',
        'new.message'
    ],'migration notifications')

    if "using ((select auth.uid()) = user_id)" not in compact:
        raise AssertionError('RLS notifications: lecture/écriture self-only non détectée.')

    require(page,[
        'noindex,nofollow',
        'data-notifications-list',
        'data-notifications-read-all',
        'sinjira-user-notifications-v24-4-63.js?v=24.4.63',
        'Aucun courriel, SMS ou service payant n’est nécessaire.'
    ],'page notifications')

    require(dashboard,[
        'href="notifications.html"',
        'data-notifications-dashboard-count',
        'data-notifications-preview',
        'sinjira-user-notifications-v24-4-63.js?v=24.4.63'
    ],'tableau de bord notifications')

    require(client,[
        "from('user_notifications')",
        '.update({read_at:',
        '.is(\'read_at\',null)',
        'safeActionPath',
        "path.startsWith('/compte/')",
        "path.startsWith('/projets/sinjira/')"
    ],'client notifications')
    forbid(client,[
        "from('user_notifications').insert",
        "from('user_notifications').delete",
        'subscribe(',
        '.channel('
    ],'client notifications')

    require(ledger,['20260818041444 sinjira_v24_4_63_user_notifications'],'ledger notifications')

    print('OK notifications V24.4.63: self-only, lecture + read_at seulement, déclencheurs privés sans texte sensible et interface interne gratuite.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
