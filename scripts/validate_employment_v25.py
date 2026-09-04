#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / 'supabase' / 'migrations' / '20260904225000_sinjira_v25_employment_foundation.sql'
TEST = ROOT / 'supabase' / 'tests' / 'employment_v25.test.sql'
PAGE = ROOT / 'compte' / 'emploi.html'
DASHBOARD = ROOT / 'compte' / 'index.html'
JS = ROOT / 'assets' / 'js' / 'sinjira-employment-v25.js'
MANIFEST = ROOT / 'scripts' / 'validate_production_schema_manifest.py'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f'ECHEC emploi V25: {message}')


def main() -> int:
    for path in (MIGRATION, TEST, PAGE, DASHBOARD, JS, MANIFEST):
        require(path.is_file(), f'fichier manquant: {path.relative_to(ROOT)}')

    migration = MIGRATION.read_text('utf-8')
    test = TEST.read_text('utf-8')
    page = PAGE.read_text('utf-8')
    dashboard = DASHBOARD.read_text('utf-8')
    js = JS.read_text('utf-8')
    manifest = MANIFEST.read_text('utf-8')

    require('create table if not exists public.employment_profiles' in migration, 'table employment_profiles absente')
    require('create table if not exists public.employment_applications' in migration, 'table employment_applications absente')
    require('force row level security' in migration.lower(), 'RLS forcé absent')
    require(migration.lower().count('(select auth.uid()) = user_id') >= 8, 'politiques propriétaire insuffisantes')
    require('revoke all on table public.employment_profiles from public, anon' in migration, 'anon doit être révoqué des profils')
    require('revoke all on table public.employment_applications from public, anon' in migration, 'anon doit être révoqué des candidatures')

    forbidden_sql_links = (
        'references public.dating_', 'references public.security_',
        'references private.conscience_', 'references public.life_story_',
        'references public.security_travel_plans',
    )
    for needle in forbidden_sql_links:
        require(needle not in migration.lower(), f'couplage SQL interdit détecté: {needle}')

    require('employment_job_listings' not in migration, 'aucune table d’offres fictives ne doit être créée')
    require("'employment_profiles','employment_applications'" in manifest.replace('\n', ''), 'tables Emploi non classées comme planifiées')

    require('data-account-page="employment"' in page, 'route Emploi non identifiée')
    require('sinjira-employment-v25.js' in page, 'module JS Emploi non chargé')
    require('Aucune offre n’est affichée' in page, 'la limite sur les offres réelles doit être visible')
    require('Registre personnel' in page and 'Rencontres' in page and 'Mode Voyage' in page, 'séparation des usages insuffisamment expliquée')
    require('href="emploi.html"' in dashboard, 'Emploi doit être accessible depuis Mon espace uniquement une fois la route créée')
    require('<h2>Emploi</h2>' in dashboard, 'la carte Emploi du tableau de bord est absente')

    require('localStorage' not in js and 'sessionStorage' not in js, 'les données Emploi ne doivent pas être persistées dans le navigateur')
    require('.innerHTML' not in js, 'les données utilisateur doivent être rendues sans innerHTML')
    require(".from('employment_profiles')" in js, 'profil Emploi non utilisé')
    require(".from('employment_applications')" in js, 'suivi de candidatures non utilisé')
    for table in ('dating_', 'security_', 'conscience_', 'life_story_', 'registry_'):
        require(f".from('{table}" not in js.lower(), f'lecture inter-module interdite depuis {table}')
    require('supabase.auth.getUser()' in js, 'identité utilisateur non dérivée de la session')
    require('user_id: user.id' in js, 'écritures non liées à l’utilisateur courant')
    require("rel = 'noopener noreferrer'" in js, 'liens externes non durcis')
    require('select * from finish()' in test.lower(), 'test pgTAP incomplet')

    print('OK emploi V25: RLS propriétaire, séparation des usages, zéro fausse offre et zéro persistance navigateur.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
