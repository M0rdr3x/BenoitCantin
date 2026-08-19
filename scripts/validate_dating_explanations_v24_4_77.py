#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260819233500_sinjira_v24_4_77_dating_explanations.sql'
TEST=ROOT/'supabase/tests/dating_explanations_v24_4_77.test.sql'
JS=ROOT/'assets/js/sinjira-dating-explain-v24-4-77.js'
PROGRESS=ROOT/'assets/js/sinjira-dating-progress-v24-4-76.js'
CSS=ROOT/'assets/css/sinjira-dating-v24-4-76.css'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'


def require(text, markers, label):
    missing=[m for m in markers if m.lower() not in text.lower()]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text, markers, label):
    found=[m for m in markers if m.lower() in text.lower()]
    if found: raise AssertionError(f'{label}: marqueurs interdits: {found}')


def main():
    mig=MIG.read_text('utf-8',errors='ignore')
    test=TEST.read_text('utf-8',errors='ignore')
    js=JS.read_text('utf-8',errors='ignore')
    progress=PROGRESS.read_text('utf-8',errors='ignore')
    css=CSS.read_text('utf-8',errors='ignore')
    ledger=LEDGER.read_text('utf-8',errors='ignore')

    require(mig,[
        'public.dating_import_registry_traits','public.dating_compatibility_detail',
        'dating_compatibility_candidates(20)','remote_ai_used',"'method','local_explainable_v24_4_77'",
        'raw_profile_data_returned','raw_registry_answers_returned',
        'danger_style','pressure_style','archetype','main_strength','main_weakness',
        'revoke all on function public.dating_compatibility_detail(uuid) from public,anon',
        'grant execute on function public.dating_compatibility_detail(uuid) to authenticated'
    ],'migration V24.4.77')
    forbid(mig,['compte_courriel','compte_pseudo','personality_notes','social_group','openai','anthropic','stripe','twilio','pg_net','http_post'],'migration V24.4.77')

    require(js,[
        "s.rpc('dating_compatibility_detail'",'Comprendre cette compatibilité','Aucune réponse brute du Registre',
        'Aucune IA distante','data-dating-detail-toggle','MutationObserver'
    ],'runtime explications V24.4.77')
    forbid(js,['openai','anthropic','stripe','twilio','.storage.upload(','.from(\'dating_preferences\')','.from("dating_preferences")'],'runtime explications V24.4.77')

    require(progress,["import './sinjira-dating-explain-v24-4-77.js'"],'branchement V24.4.77')
    require(css,['.dating-detail','.dating-dimension','.dating-registry-chip'],'styles V24.4.77')
    require(test,['select plan(12)','personality_notes','compte_courriel','raw_registry_answers_returned'],'pgTAP V24.4.77')

    if '20260819233500 sinjira_v24_4_77_dating_explanations' in ledger:
        raise AssertionError('la migration V24.4.77 est encore future sur cette branche et ne doit pas être déclarée production avant synchronisation réelle')

    print('OK V24.4.77: explications agrégées, Registre enrichi avec consentement, aucune donnée brute exposée et aucune IA distante active.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
