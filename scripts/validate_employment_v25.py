#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIGRATION=ROOT/'supabase'/'migrations'/'20260904225000_sinjira_v25_employment_foundation.sql'
TEST=ROOT/'supabase'/'tests'/'employment_v25.test.sql'
SMOKE=ROOT/'scripts'/'smoke_employment_auth_local.py'
WORKFLOW=ROOT/'.github'/'workflows'/'sinjira-employment-v25.yml'
PAGE=ROOT/'compte'/'emploi.html'
DASHBOARD=ROOT/'compte'/'index.html'
JS=ROOT/'assets'/'js'/'sinjira-employment-v25.js'
MANIFEST=ROOT/'scripts/validate_production_schema_manifest.py'


def require(condition: bool,message: str)->None:
    if not condition:raise SystemExit(f'ECHEC emploi V25: {message}')


def main()->int:
    for path in (MIGRATION,TEST,SMOKE,WORKFLOW,PAGE,DASHBOARD,JS,MANIFEST):
        require(path.is_file(),f'fichier manquant: {path.relative_to(ROOT)}')

    migration=MIGRATION.read_text('utf-8')
    test=TEST.read_text('utf-8')
    smoke=SMOKE.read_text('utf-8')
    workflow=WORKFLOW.read_text('utf-8')
    page=PAGE.read_text('utf-8')
    dashboard=DASHBOARD.read_text('utf-8')
    js=JS.read_text('utf-8')
    manifest=MANIFEST.read_text('utf-8')

    require('create table if not exists public.employment_profiles' in migration,'table employment_profiles absente')
    require('create table if not exists public.employment_applications' in migration,'table employment_applications absente')
    require('force row level security' in migration.lower(),'RLS forcé absent')
    require(migration.lower().count('(select auth.uid()) = user_id')>=8,'politiques propriétaire insuffisantes')
    require('revoke all on table public.employment_profiles from public, anon' in migration,'anon doit être révoqué des profils')
    require('revoke all on table public.employment_applications from public, anon' in migration,'anon doit être révoqué des candidatures')

    forbidden_sql_links=(
        'references public.dating_','references public.security_',
        'references private.conscience_','references public.life_story_',
        'references public.security_travel_plans',
    )
    for needle in forbidden_sql_links:
        require(needle not in migration.lower(),f'couplage SQL interdit détecté: {needle}')

    require('employment_job_listings' not in migration,'aucune table d’offres fictives ne doit être créée')

    require('PLANNED_LOCAL_TABLES={' in manifest,'bloc des modules planifiés absent du manifeste')
    expected_block,planned_block=manifest.split('PLANNED_LOCAL_TABLES={',1)
    for table in ('employment_profiles','employment_applications'):
        require(f"'{table}'" in expected_block,f'{table} doit être classée production')
        require(f"'{table}'" not in planned_block,f'{table} ne doit plus être classée planifiée')
    for table in ('personal_ai_settings','personal_ai_source_permissions','personal_ai_audit'):
        require(f"'{table}'" in expected_block,f'{table} Mon IA doit maintenant être classée production')
        require(f"'{table}'" not in planned_block,f'{table} Mon IA ne doit plus être classée planifiée')

    require('data-account-page="employment"' in page,'route Emploi non identifiée')
    require('sinjira-employment-v25.js' in page,'module JS Emploi non chargé')
    require('Aucune offre n’est affichée' in page,'la limite sur les offres réelles doit être visible')
    require('Registre personnel' in page and 'Rencontres' in page and 'Mode Voyage' in page,'séparation des usages insuffisamment expliquée')
    require('href="emploi.html"' in dashboard,'Emploi doit être accessible depuis Mon espace uniquement une fois la route créée')
    require('<h2>Emploi</h2>' in dashboard,'la carte Emploi du tableau de bord est absente')

    require('localStorage' not in js and 'sessionStorage' not in js,'les données Emploi ne doivent pas être persistées dans le navigateur')
    require('.innerHTML' not in js,'les données utilisateur doivent être rendues sans innerHTML')
    require(".from('employment_profiles')" in js,'profil Emploi non utilisé')
    require(".from('employment_applications')" in js,'suivi de candidatures non utilisé')
    for table in ('dating_','security_','conscience_','life_story_','registry_'):
        require(f".from('{table}" not in js.lower(),f'lecture inter-module interdite depuis {table}')
    require('supabase.auth.getUser()' in js,'identité utilisateur non dérivée de la session')
    require('user_id: user.id' in js,'écritures non liées à l’utilisateur courant')
    require("rel = 'noopener noreferrer'" in js,'liens externes non durcis')
    require('select plan(31);' in test.lower(),'plan pgTAP Emploi doit rester à 31 assertions')
    require('select * from finish()' in test.lower(),'test pgTAP incomplet')

    # Intégration locale réelle : Auth -> JWT -> PostgREST -> RLS.
    require('supabase start' in workflow,'le smoke HTTP exige la pile Supabase locale complète')
    require('supabase db start' not in workflow,'db start seul ne suffit pas au smoke Auth/PostgREST')
    require('supabase test db supabase/tests/employment_v25.test.sql --local' in workflow,'31 pgTAP Emploi non exécutés')
    require('python3 scripts/smoke_employment_auth_local.py' in workflow,'smoke Auth/RLS local non exécuté en CI')
    require("SINJIRA_LOCAL_API_URL=\"$API_URL\"" in workflow,'API locale non injectée au smoke')
    require("SINJIRA_LOCAL_ANON_KEY=\"$ANON_KEY\"" in workflow,'clé anon locale non injectée au smoke')
    require('SERVICE_ROLE' not in workflow and 'service_role' not in workflow.lower(),'le smoke ne doit jamais recevoir de service_role')
    require('SUPABASE_ACCESS_TOKEN' not in workflow,'le smoke Emploi local ne doit utiliser aucun PAT production')

    require('/auth/v1/signup' in smoke,'le smoke doit traverser Supabase Auth réel')
    require('/rest/v1/employment_profiles' in smoke,'le smoke doit traverser PostgREST pour les profils')
    require('/rest/v1/employment_applications' in smoke,'le smoke doit traverser PostgREST pour les candidatures')
    require('SINJIRA_LOCAL_API_URL' in smoke and 'SINJIRA_LOCAL_ANON_KEY' in smoke,'variables locales du smoke absentes')
    require('127.0.0.1' in smoke and 'localhost' in smoke,'le smoke doit refuser une API non locale')
    for privileged_marker in ('SERVICE_ROLE_KEY','SINJIRA_LOCAL_SERVICE_ROLE','SUPABASE_SERVICE_ROLE','sb_secret_','SUPABASE_ACCESS_TOKEN','/auth/v1/admin/'):
        require(privileged_marker not in smoke,f'le smoke contient une surface privilégiée interdite: {privileged_marker}')
    require('gpvivleexywljowcqkru' not in smoke,'le smoke ne doit pas cibler le projet production')
    require('psql ' not in smoke and 'execute_sql' not in smoke,'le smoke ne doit pas contourner PostgREST avec SQL direct')
    require('employment_job_listings' not in smoke,'le smoke ne doit pas inventer de catalogue d’offres')

    # Deux comptes doivent chacun posséder un profil et une candidature synthétiques.
    require('token_a, user_a = signup("a")' in smoke and 'token_b, user_b = signup("b")' in smoke,
            'deux comptes Auth synthétiques distincts sont requis')
    require('create_profile(token_a, user_a, "a")' in smoke and 'create_profile(token_b, user_b, "b")' in smoke,
            'A et B doivent chacun créer leur profil')
    require('create_application(token_a, user_a, "a")' in smoke and 'create_application(token_b, user_b, "b")' in smoke,
            'A et B doivent chacun créer leur candidature')
    require('Profil synthétique local A' in smoke and 'Profil synthétique local B' in smoke,
            'profils synthétiques explicites absents')
    require('Employeur synthétique local A' in smoke and 'Employeur synthétique local B' in smoke,
            'employeurs synthétiques explicites absents')
    require('example.invalid' in smoke,'les liens de test doivent utiliser le domaine réservé .invalid')
    require('aucune donnée personnelle réelle' in smoke.lower() and 'aucune candidature réelle' in smoke.lower(),
            'le caractère strictement synthétique des données doit être explicite')

    # La visibilité non filtrée doit être bornée au propriétaire dans les deux sens.
    require('liste propriétaire profil A' in smoke and 'liste propriétaire profil B' in smoke,
            'preuve de visibilité propriétaire des profils incomplète')
    require('liste propriétaire candidature A' in smoke and 'liste propriétaire candidature B' in smoke,
            'preuve de visibilité propriétaire des candidatures incomplète')

    # SELECT/UPDATE/DELETE cross-user bidirectionnels.
    for marker in (
        'isolation SELECT profil autre depuis A','isolation SELECT profil autre depuis B',
        'isolation UPDATE profil autre depuis A','isolation UPDATE profil autre depuis B',
        'isolation DELETE profil autre depuis A','isolation DELETE profil autre depuis B',
        'isolation SELECT candidature autre depuis A','isolation SELECT candidature autre depuis B',
        'isolation UPDATE candidature autre depuis A','isolation UPDATE candidature autre depuis B',
        'isolation DELETE candidature autre depuis A','isolation DELETE candidature autre depuis B',
    ):
        require(marker in smoke,f'preuve RLS bidirectionnelle manquante: {marker}')

    # INSERT cross-user profil doit être tenté avant les lignes légitimes pour que le rejet
    # ne puisse pas être attribué à la clé primaire existante; candidatures dans les deux sens aussi.
    require('B ne peut pas créer le profil de A' in smoke and 'A ne peut pas créer le profil de B' in smoke,
            'INSERT cross-user profil non testé dans les deux sens')
    require(smoke.index('B ne peut pas créer le profil de A') < smoke.index('create_profile(token_a, user_a, "a")'),
            'le test INSERT B->A doit précéder la création légitime du profil A')
    require(smoke.index('A ne peut pas créer le profil de B') < smoke.index('create_profile(token_b, user_b, "b")'),
            'le test INSERT A->B doit précéder la création légitime du profil B')
    require('B ne peut pas créer une candidature pour A' in smoke and 'A ne peut pas créer une candidature pour B' in smoke,
            'INSERT cross-user candidature non testé dans les deux sens')

    # Chaque propriétaire doit conserver UPDATE/DELETE et le nettoyage doit finir vide.
    for marker in (
        'UPDATE candidature A par A','UPDATE candidature B par B',
        'UPDATE profil A par A','UPDATE profil B par B',
        'DELETE candidature A par A','DELETE candidature B par B',
        'DELETE profil A par A','DELETE profil B par B',
        'nettoyage profils A','nettoyage profils B','nettoyage candidatures A','nettoyage candidatures B',
    ):
        require(marker in smoke,f'preuve propriétaire/nettoyage manquante: {marker}')

    print('OK emploi V25: production classifiée, RLS propriétaire forcée, zéro fausse offre et smoke Auth→PostgREST bidirectionnel A/B verrouillé sur profils+candidatures.')
    return 0


if __name__=='__main__':raise SystemExit(main())
