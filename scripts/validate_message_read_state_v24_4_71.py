#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260819013259_sinjira_v24_4_71_message_read_state.sql'
HELPER=ROOT/'assets/js/sinjira-message-read-state.js'
REAL=ROOT/'assets/js/sinjira-messages-real.js'
CHAR=ROOT/'assets/js/sinjira-messages-character.js'
SUMMARY=ROOT/'assets/js/sinjira-messages-summary.js'
HUB=ROOT/'compte/messages.html'
REAL_PAGE=ROOT/'compte/messages-reels.html'
CHAR_PAGE=ROOT/'compte/messages-personnage.html'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'


def require(text,markers,label):
    missing=[m for m in markers if m not in text]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text,markers,label):
    found=[m for m in markers if m in text]
    if found: raise AssertionError(f'{label}: marqueurs interdits: {found}')


def main():
    migration=MIG.read_text('utf-8',errors='ignore')
    helper=HELPER.read_text('utf-8',errors='ignore')
    real=REAL.read_text('utf-8',errors='ignore')
    char=CHAR.read_text('utf-8',errors='ignore')
    summary=SUMMARY.read_text('utf-8',errors='ignore')
    hub=HUB.read_text('utf-8',errors='ignore')
    real_page=REAL_PAGE.read_text('utf-8',errors='ignore')
    char_page=CHAR_PAGE.read_text('utf-8',errors='ignore')
    ledger=LEDGER.read_text('utf-8',errors='ignore')

    require(migration,[
        'grant update (read_at) on table public.social_real_messages to authenticated',
        'grant update (read_at) on table public.social_character_messages to authenticated',
        'real_messages_mark_read','char_messages_mark_read',
        'read_at is not null',
        'social_real_messages_unread_recipient_idx',
        'social_character_messages_unread_recipient_idx',
        'where read_at is null'
    ],'migration état lu')
    forbid(migration,['grant update on table public.social_real_messages','grant update on table public.social_character_messages'],'ACL état lu')

    require(helper,[
        "export async function unreadCounts",
        "export async function unreadTotal",
        "export async function markConversationRead",
        ".update({read_at:new Date().toISOString()})",
        ".eq('recipient_user_id',userId)",
        ".is('read_at',null)"
    ],'helper état lu')

    require(real,[
        "const UI_VERSION='24.4.71'",
        "unreadCounts('social_real_messages',user.id,'sender_user_id')",
        "markConversationRead('social_real_messages',user.id,{sender_user_id:peer.user_id})",
        'non lu',
        "message.recipient_user_id===user.id"
    ],'messagerie réelle')
    require(char,[
        "const UI_VERSION='24.4.71'",
        "unreadCounts('social_character_messages',user.id,'sender_character_id')",
        "markConversationRead('social_character_messages',user.id,{sender_character_id:peer.character_id})",
        'non lu',
        "message.recipient_user_id===user.id"
    ],'messagerie personnage')

    require(summary,[
        "unreadTotal('social_real_messages',user.id)",
        "unreadTotal('social_character_messages',user.id)",
        "data-real-unread",
        "data-character-unread"
    ],'résumé non-lus')
    require(hub,['data-real-unread','data-character-unread','sinjira-messages-summary.js?v=24.4.71','data-social-runtime="24.4.71"'],'hub Messages')
    require(real_page,['sinjira-messages-real.js?v=24.4.71','data-social-runtime="24.4.71"'],'page messages réels')
    require(char_page,['sinjira-messages-character.js?v=24.4.71','data-social-runtime="24.4.71"'],'page messages personnage')
    require(ledger,['20260819013259 sinjira_v24_4_71_message_read_state'],'ledger production')

    print('OK V24.4.71: non-lus privés, marquage destinataire-only, compteurs par conversation, résumé global et aucune modification du contenu des messages.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
