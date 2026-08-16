#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'/'20260816149000_sinjira_v24_4_12_parallel_character_convergence.sql'
OWNER_REPAIR_MIG=ROOT/'supabase'/'migrations'/'20260816194000_sinjira_v24_4_20_owner_character_resilience.sql'
JS=ROOT/'assets'/'js'/'v24-parallel.js'
HTML=ROOT/'compte'/'monde-parallele.html'
UI_VERSION='24.4.20'


def compact(value:str)->str:
    return re.sub(r'\s+','',value.lower())


def main()->int:
    errors=[]
    if not MIG.exists(): errors.append('Migration de convergence Monde parallèle absente.')
    if not OWNER_REPAIR_MIG.exists(): errors.append('Migration de résilience propriétaire V24.4.20 absente.')
    if not JS.exists(): errors.append('Client Monde parallèle absent.')
    if not HTML.exists(): errors.append('Page compte Monde parallèle absente.')
    if errors:
        print(f'ECHEC Monde parallèle canonique: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1

    sql=MIG.read_text('utf-8',errors='ignore')
    owner_sql=OWNER_REPAIR_MIG.read_text('utf-8',errors='ignore')
    js=JS.read_text('utf-8',errors='ignore')
    html=HTML.read_text('utf-8',errors='ignore')
    low=compact(sql)
    owner_low=compact(owner_sql)
    js_low=compact(js)

    affected=[
      'fictional_relationships','memorial_records','parallel_character_state',
      'parallel_cycle_responses','parallel_group_members','parallel_story_installments',
      'parallel_world_memberships'
    ]
    for table in affected:
        if f'altertablepublic.{table}' not in low or 'referencespublic.characters(id)' not in low:
            errors.append(f'{table}: FK canonique vers public.characters non garantie.')

    for marker in [
      'private.ensure_parallel_world_membership',
      'pg_advisory_xact_lock(24412026)',
      'generate_series(1,40)',
      "statusin('approved','assigned','future','published')",
      "pioneer_number,main_canon_eligible,parallel_world_only",
      "v_pioneerisnotnull",
      "v_pioneerisnull",
      'sync_parallel_membership_from_character_trigger',
      'insertintopublic.parallel_character_state'
    ]:
        if marker not in low:
            errors.append(f'Invariant Monde parallèle absent: {marker}')

    if "lower(coalesce(u.email,''))='kingtyrano@gmail.com'" not in low:
        errors.append('Exception propriétaire AbyssTime absente de l’adhésion parallèle.')
    if 'values(c.id,c.user_id,null,true,false' not in low:
        errors.append('Le propriétaire pourrait consommer un numéro pionnier fan.')
    if "'provisoire','legacy-v22'" not in low:
        errors.append('La migration V22 ne garantit pas une importation PROVISOIRE.')

    # V24.4.20 renforce la résilience du propriétaire : un lien parallèle supprimé
    # accidentellement doit être recréé par la même réparation qu'utilisent les pages compte.
    for marker in [
      'insertintopublic.parallel_character_state(character_id,user_id)',
      'insertintopublic.parallel_world_memberships(',
      'main_canon_eligible=true',
      'parallel_world_only=false',
      "'repair_version','24.4.20'",
      'sinjira_owner_character_health'
    ]:
        if marker not in owner_low:
            errors.append(f'Résilience propriétaire V24.4.20 absente: {marker}')

    stale=['parallel_missions','parallel_responses','parallel_cycles']
    for name in stale:
        if name in js:
            errors.append(f'Ancienne table encore utilisée dans le frontend: {name}')
    for name in ['parallel_world_memberships','parallel_character_state','parallel_world_cycles','parallel_cycle_responses','parallel_story_installments']:
        if name not in js:
            errors.append(f'Table V24 absente du frontend Monde parallèle: {name}')
    if "response_kind:'solo'" not in js_low:
        errors.append('Les réponses individuelles ne sont pas enregistrées avec response_kind=solo.')
    if "onconflict:'cycle_id,user_id'" not in js_low:
        errors.append('Upsert mensuel non verrouillé sur cycle_id,user_id.')
    if 'ensure_sinjira_owner_character' not in js:
        errors.append('Le Monde parallèle ne déclenche plus la réparation propriétaire lorsque nécessaire.')

    if 'data-parallel-history' not in html:
        errors.append('Historique narratif absent de la page Monde parallèle.')
    if f'?v={UI_VERSION}' not in html:
        errors.append(f'Cache-busting {UI_VERSION} absent de la page Monde parallèle.')
    if f'Univers persistant V{UI_VERSION}' not in html:
        errors.append(f'Version visible Monde parallèle différente de V{UI_VERSION}.')

    if errors:
        print(f'ECHEC Monde parallèle canonique: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print(
        'OK Monde parallèle: public.characters canonique, adhésion à l’approbation, '
        'pionniers 1–40, Chronique/cycles V24 et résilience propriétaire '
        f'{UI_VERSION} vérifiés.'
    )
    return 0

if __name__=='__main__':
    raise SystemExit(main())
