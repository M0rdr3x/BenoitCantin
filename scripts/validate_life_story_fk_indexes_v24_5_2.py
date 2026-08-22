#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260822161058_sinjira_v24_5_2_life_story_fk_indexes.sql'
REQUIRED=(
'life_story_cleanup_tasks_subject_fkey_idx',
'life_story_cleanup_tasks_completed_by_fkey_idx',
'life_story_exports_case_subject_fkey_idx',
'life_story_exports_version_fkey_idx',
'life_story_posthumous_cases_first_verified_by_fkey_idx',
'life_story_posthumous_cases_second_confirmed_by_fkey_idx',
'life_story_contests_case_subject_fkey_idx',
'life_story_contests_resolved_by_fkey_idx',
'life_story_recipients_version_owner_fkey_idx',
'life_story_version_entries_entry_owner_fkey_idx',
'life_story_version_entries_version_owner_fkey_idx',
)

def main():
    if not MIG.exists():
        print('ECHEC index FK V24.5.2: migration absente.')
        return 1
    text=MIG.read_text('utf-8',errors='ignore')
    missing=[name for name in REQUIRED if name not in text]
    if missing:
        print('ECHEC index FK V24.5.2: '+', '.join(missing))
        return 1
    print(f'OK index FK V24.5.2: {len(REQUIRED)} index couvrants contractuels présents.')
    return 0

if __name__=='__main__': raise SystemExit(main())
