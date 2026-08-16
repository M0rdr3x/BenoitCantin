#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'

EXPECTED_TABLES={
'access_requests','account_legacy_preferences','account_safety_profiles','admin_notifications',
'character_generation_runs','character_social_profiles','character_submissions','characters',
'community_rule_acceptances','contribution_receipts','documents','endgame_sheets','extensions',
'family_link_invites','family_relationship_events','fictional_relationships','fracture_endgame_reports',
'fracture_engine_actions','fracture_engine_cards','fracture_engine_events','fracture_engine_games',
'fracture_engine_rounds','fracture_engine_seats','fracture_engine_votes','fracture_parties',
'fracture_party_members','fracture_player_documents','game_sessions','guardian_links',
'guardian_signup_invites','internal_admin_users','internal_contribution_ownership',
'internal_gameplay_contributions','legacy_directives','memorial_records','memorial_requests',
'novel_comments','novels','order_items','orders','parallel_character_state',
'parallel_cycle_responses','parallel_group_members','parallel_groups','parallel_story_installments',
'parallel_world_cycles','parallel_world_memberships','player_reports','player_sheets',
'playtest_participants','playtests','private_family_links','private_life_events','products','profiles',
'project_access','projects','reader_character_submissions','reader_characters','reader_comments',
'reader_library','reader_works','registry_account_links','research_consents','session_feedback',
'sinjira_canon_context','sinjira_character_applications','sinjira_characters','sinjira_novel_comments',
'sinjira_novels','sinjira_reader_library','sinjira_security_settings','social_blocks',
'social_character_comments','social_character_likes','social_character_messages',
'social_character_posts','social_profiles','social_real_comments','social_real_likes',
'social_real_messages','social_real_posts','social_reports','social_suspensions','user_entitlements'
}

CREATE_RE=re.compile(r'create\s+table\s+(?:if\s+not\s+exists\s+)?(?:public\.)?([a-zA-Z_][a-zA-Z0-9_]*)',re.I)


def main()->int:
    sql='\n'.join(p.read_text('utf-8',errors='ignore') for p in sorted(MIG.glob('*.sql')))
    local={m.group(1).lower() for m in CREATE_RE.finditer(sql)}
    missing=sorted(EXPECTED_TABLES-local)
    extra=sorted(local-EXPECTED_TABLES)
    print(f'Manifeste production: {len(EXPECTED_TABLES)} tables attendues; reconstruction locale: {len(local)} tables créées.')
    if missing:
        print(f'ECHEC reconstruction: {len(missing)} table(s) de production absente(s) des migrations locales:')
        for name in missing: print('- MISSING '+name)
    if extra:
        print(f'INFO: {len(extra)} table(s) locale(s) non présente(s) dans le manifeste production courant:')
        for name in extra: print('- EXTRA '+name)
    if missing:return 1
    print('OK reconstruction: toutes les tables de production sont créées par l’historique GitHub.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
