#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PREFLIGHT=ROOT/'.github/workflows/supabase-production-preflight.yml'
SAFE=ROOT/'.github/workflows/supabase-production-safe.yml'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
BUILDER=ROOT/'scripts/build_supabase_production_workspace.py'


def low(path):
    return path.read_text('utf-8',errors='ignore').lower()


def main():
    errors=[]
    for p in [PREFLIGHT,SAFE,LEDGER,BUILDER]:
        if not p.exists(): errors.append(f'Fichier requis absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1

    pre=low(PREFLIGHT)
    safe=low(SAFE)

    # Le prévol peut exécuter uniquement un dry-run, jamais une écriture.
    if 'db push --linked --password' in pre and 'db push --linked --dry-run --password' not in pre:
        errors.append('Le prévol contient un db push réel.')
    # Détecter toute ligne db push non dry-run, même si un dry-run existe ailleurs.
    for line in pre.splitlines():
        s=line.strip()
        if 'supabase db push' in s and '--dry-run' not in s:
            errors.append('Le prévol contient une commande db push non dry-run.')
    for forbidden in ['functions deploy','secrets set','inputs.apply == true','appliquer les migrations de production']:
        if forbidden in pre:
            errors.append(f'Le prévol lecture seule contient une capacité d’écriture interdite: {forbidden}')
    if 'lecture seule' not in pre:
        errors.append('Le prévol ne se déclare pas explicitement en lecture seule.')

    required_safe=[
        'build_supabase_production_workspace.py',
        'validate_production_migration_ledger.py',
        'validate_production_schema_manifest.py',
        'working-directory: .prod-workspace',
        'supabase db push --linked --dry-run',
        'supabase db push --linked --password',
        'inputs.apply == true',
        'supabase functions deploy',
        'supabase db lint --linked'
    ]
    for marker in required_safe:
        if marker not in safe:
            errors.append(f'Workflow sécurisé incomplet: {marker}')

    # La commande d'écriture doit rester conditionnée à apply=true et le workspace protégé.
    apply_blocks=re.findall(r'- name:.*?(?=\n\s*- name:|\Z)',safe,re.S)
    write_blocks=[b for b in apply_blocks if 'supabase db push --linked --password' in b and '--dry-run' not in b]
    if len(write_blocks)!=1:
        errors.append(f'Le workflow sécurisé doit contenir exactement un bloc db push réel; trouvé: {len(write_blocks)}.')
    elif 'inputs.apply == true' not in write_blocks[0] or 'working-directory: .prod-workspace' not in write_blocks[0]:
        errors.append('Le db push réel n’est pas strictement conditionné à apply=true dans .prod-workspace.')

    if errors:
        print(f'ECHEC workflows Supabase: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK workflows Supabase: prévol lecture seule; application réelle uniquement via workspace ledger protégé et apply=true.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
