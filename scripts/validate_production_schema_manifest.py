#!/usr/bin/env python3
from pathlib import Path
import os,re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'

EXPECTED_TABLES={
'access_requests','account_identities','account_legacy_preferences','account_safety_profiles','admin_notifications',
'character_generation_runs','character_social_profiles','character_submissions','characters',
'community_rule_acceptances','contribution_receipts','documents','endgame_sheets','extensions',
'family_link_invites','family_relationship_events','fictional_relationships','fracture_endgame_reports',
'fracture_engine_actions','fracture_engine_cards','fracture_engine_events','fracture_engine_games',
'fracture_engine_rounds','fracture_engine_seats','fracture_engine_votes','fracture_parties',
'fracture_party_members','fracture_player_documents','game_sessions','guardian_links',
'guardian_signup_invites','internal_admin_users','internal_contribution_ownership',
'internal_gameplay_contributions','legacy_directives','memorial_records','memorial_requests',
'moderation_appeals','moderation_decisions','novel_comments','novels','order_items','orders','parallel_character_state','parallel_identities',
'parallel_cycle_responses','parallel_group_members','parallel_groups','parallel_story_installments',
'parallel_world_cycles','parallel_world_memberships','player_reports','player_sheets',
'playtest_participants','playtests','private_family_links','private_life_events','products','profiles',
'project_access','projects','reader_character_submissions','reader_characters','reader_comments',
'reader_library','reader_works','registry_account_links','research_consents','session_feedback',
'sinjira_canon_context','sinjira_character_applications','sinjira_characters','sinjira_novel_comments',
'sinjira_novels','sinjira_reader_library','sinjira_security_settings','social_blocks',
'social_character_comments','social_character_likes','social_character_messages',
'social_character_posts','social_profiles','social_real_comments','social_real_likes',
'social_real_messages','social_real_posts','social_reports','social_suspensions','user_entitlements',
'user_notifications','license_batches','activation_codes','license_redemptions','admin_audit_log',
'character_status_events','privacy_settings','notification_preferences',
'dating_profiles','dating_preferences','dating_connections','dating_messages',
'sinjira_points_accounts','sinjira_points_ledger','dating_meet_requests',
'security_user_settings','security_devices','security_travel_plans','security_connection_events',
'security_events','security_connection_challenges','security_push_endpoints'
}

PLANNED_LOCAL_TABLES={
'private_profiles','family_relationships','character_questionnaire_drafts',
'parallel_cycles','parallel_missions','parallel_responses',
'market_listings','market_favorites','token_ledger',
'codex_entities','codex_relationships','content_versions',
'privacy_incident_register','privacy_requests','privacy_legal_holds','safety_escalation_cases'
}

CREATE_RE=re.compile(r'create\s+table\s+(?:if\s+not\s+exists\s+)?(?:(?:public|private)\.)?([a-zA-Z_][a-zA-Z0-9_]*)',re.I)

def annotate(level:str,message:str):
    if os.getenv('GITHUB_ACTIONS')=='true':
        safe=message.replace('%','%25').replace('\r','%0D').replace('\n','%0A')
        print(f'::{level} file=scripts/validate_production_schema_manifest.py::{safe}')

def main()->int:
    sql='\n'.join(p.read_text('utf-8',errors='ignore') for p in sorted(MIG.glob('*.sql')))
    local={m.group(1).lower() for m in CREATE_RE.finditer(sql)}
    missing=sorted(EXPECTED_TABLES-local)
    planned=sorted((local-EXPECTED_TABLES)&PLANNED_LOCAL_TABLES)
    unexpected=sorted(local-EXPECTED_TABLES-PLANNED_LOCAL_TABLES)
    stale_planned=sorted(PLANNED_LOCAL_TABLES-local)

    print(f'Manifeste production: {len(EXPECTED_TABLES)} tables; reconstruction locale: {len(local)} tables; modules planifiés présents: {len(planned)}.')
    if missing:
        print(f'ECHEC reconstruction: {len(missing)} table(s) de production absente(s) des migrations locales:')
        for name in missing:
            print('- MISSING '+name);annotate('error',f'Table de production absente des migrations locales: {name}')
    if unexpected:
        print(f'ECHEC classification: {len(unexpected)} table(s) locale(s) non déclarée(s):')
        for name in unexpected:
            print('- UNCLASSIFIED '+name);annotate('error',f'Table locale non classifiée production/planifiée: {name}')
    if stale_planned:
        print(f'ECHEC classification: {len(stale_planned)} table(s) déclarée(s) planifiée(s) sans DDL local:')
        for name in stale_planned:
            print('- STALE-PLANNED '+name);annotate('error',f'Table planifiée déclarée mais absente des migrations: {name}')
    if planned:
        print('INFO modules locaux explicitement planifiés, non revendiqués comme production:')
        for name in planned:print('- PLANNED '+name)
    if missing or unexpected or stale_planned:return 1
    print('OK reconstruction: production entièrement reconstructible; aucune table locale non classifiée.')
    return 0

if __name__=='__main__':raise SystemExit(main())
