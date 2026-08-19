#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260819221500_sinjira_v24_4_74_dating_compatibility.sql'
LIFECYCLE=ROOT/'supabase/migrations/20260819221600_sinjira_v24_4_74_dating_lifecycle_guard.sql'
PAGE=ROOT/'compte/rencontres.html'
JS=ROOT/'assets/js/sinjira-dating-v24-4-74.js'
CSS=ROOT/'assets/css/sinjira-dating-v24-4-74.css'
COMMUNITY=ROOT/'compte/communaute.html'


def require(text,markers,label):
    missing=[m for m in markers if m not in text]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text,markers,label):
    found=[m for m in markers if m in text]
    if found: raise AssertionError(f'{label}: marqueurs interdits: {found}')


def function_body(sql,name):
    pattern=re.compile(rf'create or replace function\s+{re.escape(name)}\b.*?\bas \$\$(.*?)\$\$;',re.I|re.S)
    match=pattern.search(sql)
    if not match: raise AssertionError(f'fonction SQL introuvable: {name}')
    return match.group(1)


def main():
    migration=MIG.read_text('utf-8',errors='ignore')
    lifecycle=LIFECYCLE.read_text('utf-8',errors='ignore')
    page=PAGE.read_text('utf-8',errors='ignore')
    js=JS.read_text('utf-8',errors='ignore')
    css=CSS.read_text('utf-8',errors='ignore')
    community=COMMUNITY.read_text('utf-8',errors='ignore')

    require(migration,[
        'create table if not exists public.dating_profiles',
        'create table if not exists public.dating_introductions',
        'create table if not exists public.dating_photo_reveal_consents',
        "public.sinjira_age_band(p_user_id)='adult'",
        "array['Célibataire','Divorcé(e)','Veuf / veuve']",
        'public.social_is_blocked(p_a,p_b)',
        'public.has_accepted_community_rules(p_user_id)',
        'not public.social_is_suspended(p_user_id)',
        'private.dating_safe_questionnaire_traits',
        'source_purged_at is null',
        "'scale_reserved_social'",
        "'scale_flexible_rigid'",
        'create or replace function public.dating_recommendations',
        'create or replace function public.dating_request_introduction',
        'create or replace function public.dating_respond_introduction',
        'create or replace function public.dating_photo_reveal_status',
        'create or replace function public.dating_request_photo_reveal',
        'sent_n>=10 and received_n>=10 and mine and theirs',
        "'threshold',10",
        'dating_private_profile_guard',
        'dating_safety_profile_guard',
        'revoke all on table public.dating_photo_reveal_consents from public,anon,authenticated',
        'grant execute on function public.dating_recommendations(integer) to authenticated'
    ],'migration Rencontres')

    require(lifecycle,[
        'private.dating_close_active_for_user',
        "status in('requested','accepted')",
        'perform private.dating_close_active_for_user(new.user_id)',
        'private.dating_close_on_social_block',
        'dating_social_block_guard',
        'new.blocker_user_id',
        'new.blocked_user_id'
    ],'cycle de vie Rencontres')

    rec=function_body(migration,'public.dating_recommendations')
    forbid(rec,['avatar_path','account_email','email','source_payload','questionnaire_traits','birth_date','date_of_birth','relationship_partner_label'],'sortie recommandations')
    require(rec,["'user_id'","'pseudo'","'compatibility_score'","'strengths'","'explore'"],'sortie recommandations')

    safe_traits=function_body(migration,'private.dating_safe_questionnaire_traits')
    forbid(safe_traits,['account_email','photo_path','appearance_','parent_','free_text','relationship_partner_label'],'traits questionnaire autorisés')

    require(page,[
        '<meta content="noindex,nofollow" name="robots"',
        'Rencontres par compatibilité',
        '18+ uniquement',
        'Pas de swipe',
        'Aucune photo dans la découverte',
        '10 messages de chaque côté',
        'data-dating-form',
        'data-dating-recommendations',
        'data-dating-introductions',
        'data-dating-delete',
        'sinjira-dating-v24-4-74.js?v=24.4.74'
    ],'page Rencontres')
    forbid(page,['OnlyFans','Tinder','Bumble'],'page Rencontres')

    require(js,[
        "rpc('dating_my_eligibility')",
        "from('dating_profiles').select('*').eq('user_id',user.id)",
        "rpc('dating_save_profile'",
        "rpc('dating_recommendations'",
        "rpc('dating_request_introduction'",
        "rpc('dating_respond_introduction'",
        "rpc('dating_photo_reveal_status'",
        "rpc('dating_request_photo_reveal'",
        "rpc('dating_revoke_photo_reveal'",
        "rpc('dating_delete_my_profile')",
        'messages-reels.html?user=',
        'Aucune photo n’est utilisée dans cette proposition.',
        'avatarUrl(data.other_avatar_path)',
        'escapeHtml(row.pseudo',
    ],'runtime Rencontres')
    forbid(js,['fetch(','openai','stripe','paypal','innerHTML=row','eval('],'runtime Rencontres')

    avatar_uses=[m.start() for m in re.finditer(r'avatarUrl\(',js)]
    if len(avatar_uses)!=1:
        raise AssertionError(f'runtime Rencontres: avatarUrl doit être utilisé exactement une fois après déverrouillage, trouvé {len(avatar_uses)}')
    reveal_pos=js.find("rpc('dating_photo_reveal_status'")
    if reveal_pos<0 or avatar_uses[0]<reveal_pos:
        raise AssertionError('runtime Rencontres: avatar rendu avant vérification de révélation')

    require(community,['href="rencontres.html">Rencontres 18+</a>','Rencontres par compatibilité · 18+','sans swipe ni catalogue de photos'],'portail Communauté')
    require(css,['.dating-recommendations','.dating-photo-gate','@media(max-width:640px)'],'CSS Rencontres')

    print('OK V24.4.74: Rencontres 18+ opt-in, sans swipe/photo de découverte, questionnaire minimisé, blocages respectés, présentations invalidées au besoin et photo après 10+10 messages + double consentement.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
