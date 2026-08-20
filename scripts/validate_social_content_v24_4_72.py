#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260819014532_sinjira_v24_4_72_social_content_self_management.sql'
HELPER=ROOT/'assets/js/sinjira-social-self-content.js'
REAL=ROOT/'assets/js/sinjira-community-real.js'
CHAR=ROOT/'assets/js/sinjira-community-character.js'
REAL_PAGE=ROOT/'compte/communaute.html'
CHAR_PAGE=ROOT/'compte/reseau-personnage.html'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'


def require(text,markers,label):
    missing=[m for m in markers if m not in text]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text,markers,label):
    found=[m for m in markers if m in text]
    if found: raise AssertionError(f'{label}: marqueurs interdits: {found}')


def version_tuple(value):
    return tuple(int(x) for x in value.split('.'))


def require_runtime_at_least(text,pattern,minimum,label):
    match=re.search(pattern,text)
    if not match or version_tuple(match.group(1)) < version_tuple(minimum):
        raise AssertionError(f'{label}: runtime antérieur à V{minimum}')


def main():
    migration=MIG.read_text('utf-8',errors='ignore')
    helper=HELPER.read_text('utf-8',errors='ignore')
    real=REAL.read_text('utf-8',errors='ignore')
    char=CHAR.read_text('utf-8',errors='ignore')
    real_page=REAL_PAGE.read_text('utf-8',errors='ignore')
    char_page=CHAR_PAGE.read_text('utf-8',errors='ignore')
    ledger=LEDGER.read_text('utf-8',errors='ignore')

    for table in ('social_real_posts','social_real_comments','social_character_posts','social_character_comments'):
        require(migration,[
            f'revoke all on table public.{table} from public, anon, authenticated',
            f'grant select on table public.{table} to authenticated',
            f'grant update (body) on table public.{table} to authenticated',
            f'grant delete on table public.{table} to authenticated'
        ],f'ACL {table}')
        forbid(migration,[f'grant update on table public.{table} to authenticated'],f'UPDATE table-wide {table}')

    require(migration,[
        'grant insert (user_id, body) on table public.social_real_posts to authenticated',
        'grant insert (post_id, user_id, body) on table public.social_real_comments to authenticated',
        'grant insert (user_id, character_id, body) on table public.social_character_posts to authenticated',
        'grant insert (post_id, user_id, character_id, body) on table public.social_character_comments to authenticated',
        'real_posts_update','real_comments_update','char_posts_update','char_comments_update',
        "sinjira_my_age_band() in ('youth','adult')",
        'has_accepted_community_rules((select auth.uid()))',
        'not social_is_suspended((select auth.uid()))',
        "lower(coalesce(c.status,'')) <> 'archived'",
        'sinjira_can_social_interact((select auth.uid()), p.user_id)'
    ],'migration self-only')

    require(helper,[
        'EDITABLE_TABLES',
        "'social_real_posts'",
        "'social_real_comments'",
        "'social_character_posts'",
        "'social_character_comments'",
        'export async function editOwnContent',
        'export async function deleteOwnContent',
        ".update({body}).eq('id',id)",
        ".delete().eq('id',id)",
        'editedSuffix'
    ],'helper social')
    forbid(helper,['.update({user_id', '.update({character_id', '.update({post_id'], 'helper social')

    for text,label,post_table,comment_table in (
        (real,'communauté réelle','social_real_posts','social_real_comments'),
        (char,'réseau personnage','social_character_posts','social_character_comments'),
    ):
        require(text,[
            'sinjira-social-self-content.js?v=24.4.72',
            'data-edit', 'data-delete', 'data-edit-comment', 'data-delete-comment',
            f"table:'{post_table}'",
            f"table:'{comment_table}'",
            'editedSuffix('
        ],label)
        require_runtime_at_least(text,r"const UI_VERSION='([0-9]+(?:\.[0-9]+)+)'",'24.4.72',label)

    require_runtime_at_least(real_page,r'sinjira-community-real\.js\?v=([0-9]+(?:\.[0-9]+)+)','24.4.72','page communauté script')
    require_runtime_at_least(real_page,r'data-social-runtime="([0-9]+(?:\.[0-9]+)+)"','24.4.72','page communauté runtime')
    require_runtime_at_least(char_page,r'sinjira-community-character\.js\?v=([0-9]+(?:\.[0-9]+)+)','24.4.72','page réseau personnage script')
    require_runtime_at_least(char_page,r'data-social-runtime="([0-9]+(?:\.[0-9]+)+)"','24.4.72','page réseau personnage runtime')
    require(ledger,['20260819014532 sinjira_v24_4_72_social_content_self_management'],'ledger production')

    print('OK V24.4.72+: édition/suppression self-only sur les deux réseaux, body seul modifiable, anon révoqué, règles communautaires et identité personnage préservées sur runtime courant.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
