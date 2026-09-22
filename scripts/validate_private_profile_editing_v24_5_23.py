#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'compte/profil.html'
JS=ROOT/'assets/js/sinjira-private-profile-v24-5-23.js'
MIG1=ROOT/'supabase/migrations/20260823035659_sinjira_v24_5_14_private_profile_editing.sql'
MIG2=ROOT/'supabase/migrations/20260823040936_sinjira_v24_5_23_private_profile_schema_convergence.sql'
MIG3=ROOT/'supabase/migrations/20260919100000_sinjira_v25_private_profile_age_11.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'PRIVATE_PROFILE_EDITING_V24_5_23.md'
TEST=ROOT/'supabase/tests/private_profile_editing_v24_5_23.test.sql'
TEST_CHILD=ROOT/'supabase/tests/private_profile_child_age_v25.test.sql'


def read(p): return p.read_text('utf-8',errors='ignore') if p.exists() else ''
def compact(s): return re.sub(r'\s+',' ',s.lower()).strip()


def main():
    errors=[]
    for p in [PAGE,JS,MIG1,MIG2,MIG3,LEDGER,DOC,TEST,TEST_CHILD]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1

    page=read(PAGE); js=read(JS); sql1=read(MIG1); sql2=read(MIG2); sql3=read(MIG3); sql=sql1+'\n'+sql2; ledger=read(LEDGER); doc=read(DOC).lower(); test=read(TEST); test_child=read(TEST_CHILD)
    pl=page.lower(); jl=js.lower(); sl=compact(sql); sl3=compact(sql3)

    for marker in [
        'enregistrer mes informations personnelles','annuler les modifications',
        'value="woman"','value="man"','value="non_binary"','value="other"','value="prefer_not_to_say"',
        'value="single"','value="partnered"','value="engaged"','value="married"','value="separated"','value="divorced"','value="widowed"',
        'sinjira-private-profile-v24-5-23.js?v=25.1.1'
    ]:
        if marker not in pl: errors.append(f'Page Profil incomplète: {marker}')
    if re.search(r'<fieldset[^>]*\bdisabled\b',pl): errors.append('Le coffre privé ne doit plus être enfermé dans un fieldset disabled.')
    if 'v24-private-profile.js' in pl: errors.append('L’ancien contrôleur lecture seule ne doit plus être chargé.')
    if 'ils ne peuvent pas être modifiés' in pl or 'lecture seule' in pl: errors.append('Le texte de l’ancien mode lecture seule ne doit plus être affiché.')

    for marker in [
        "rpc('private_profile_get'","rpc('private_profile_save'",'dating_reconfirmation_required',
        'youth_jurisdiction_not_enabled','guardian_authorization_required_under_14','mfa_required',
        'setbusy(true);','await loadprofile();','setbusy(false);','if(!loadedsnapshot)',
        'le formulaire reste verrouillé tant que vos données n’ont pas été chargées',
        'aucune modification n’est envoyée'
    ]:
        if marker not in jl: errors.append(f'Contrôleur V24.5.23 incomplet: {marker}')
    if re.search(r"\.from\(['\"]private_profiles['\"]\)",jl): errors.append('Le navigateur ne doit jamais accéder directement à private_profiles.')
    if re.search(r'\.\s*(?:insert|update|upsert|delete)\s*\(',jl): errors.append('Le contrôleur privé ne doit effectuer aucune écriture table directe.')

    for marker in [
        'alter table public.private_profiles enable row level security',
        'revoke all on table public.private_profiles from public, anon, authenticated',
        'create schema if not exists sinjira_profile_internal',
        'security invoker',
        'sinjira_mfa_access_allowed',
        'sinjira_minimum_age_13',
        'youth_jurisdiction_not_enabled',
        'guardian_authorization_required_under_14',
        'sinjira_birth_date_change_guard',
        'enabled=false',
        'a_photo_consent=false',
        'b_photo_consent=false'
    ]:
        if marker not in sl: errors.append(f'Migrations Profil privées incomplètes: {marker}')

    for marker in [
        'create or replace function sinjira_profile_internal.private_profile_get()',
        'sinjira_minimum_age_11',
        'guardian_authorization_required_under_14',
        'g.revoked_at is null',
        'sinjira_mfa_access_allowed',
        'security definer'
    ]:
        if marker not in sl3: errors.append(f'Migration V25 Profil enfant incomplète: {marker}')
    if 'sinjira_minimum_age_13' in sl3:
        errors.append('La migration effective V25 ne doit pas réintroduire la limite 13 ans.')
    if re.search(r'grant\s+.*on\s+table\s+public\.private_profiles\s+to\s+(?:anon|authenticated)',sl): errors.append('private_profiles ne doit recevoir aucun accès table direct client.')

    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    expected=[
        '20260823035659 sinjira_v24_5_14_private_profile_editing',
        '20260823040936 sinjira_v24_5_23_private_profile_schema_convergence'
    ]
    if len(rows)<155: errors.append(f'Ledger historique tronqué: {len(rows)} migrations, au moins 155 attendues.')
    for row in expected:
        if rows.count(row)!=1: errors.append(f'Ledger doit contenir exactement une fois: {row}')
    if all(row in rows for row in expected) and rows.index(expected[0]) >= rows.index(expected[1]):
        errors.append('Les deux migrations Profil V24.5.23 doivent conserver leur ordre historique.')

    for marker in ['l’humain avant tout','security invoker','sinjira_profile_internal','155 migrations','pas copiés automatiquement dans le registre','moins de 14 ans']:
        if marker not in doc: errors.append(f'Document V24.5.23 incomplet: {marker}')

    for marker in ['private_profiles','security invoker','sinjira_mfa_access_allowed','youth_jurisdiction_not_enabled','sinjira_birth_date_change_guard']:
        if marker not in test.lower(): errors.append(f'pgTAP V24.5.23 incomplet: {marker}')

    for marker in [
        'select plan(11);',
        'sinjira_minimum_age_11',
        'guardian_authorization_required_under_14',
        'revoked_at is null',
        '$read$ select public.private_profile_get() $read$',
        'un enfant de 11 ans avec tuteur actif peut relire son coffre privé',
        'un enfant de 11 ans sans tuteur actif ne peut pas relire son coffre',
        'un lien tuteur révoqué bloque aussi la lecture du coffre'
    ]:
        if marker not in test_child.lower(): errors.append(f'pgTAP V25 Profil enfant incomplet: {marker}')

    forbidden=['stripe','paypal','twilio','api.resend.com','openai.com','shippo','easypost','fedex','purolator']
    for token in forbidden:
        if token in jl or token in sl: errors.append(f'Intégration externe interdite dans V24.5.23: {token}')

    if errors:
        print(f'ECHEC V24.5.23 profil privé modifiable: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK Profil privé: historique immuable, coffre self-only, MFA conservé et compatibilité enfant 11+ forward-only validée.')
    return 0

if __name__=='__main__': raise SystemExit(main())
,
        'un enfant de 11 ans avec tuteur actif peut relire son coffre privé',
        'un enfant de 11 ans sans tuteur actif ne peut pas relire son coffre',
        'un lien tuteur révoqué bloque aussi la lecture du coffre'
    ]:
        if marker not in test_child.lower(): errors.append(f'pgTAP V25 Profil enfant incomplet: {marker}')

    forbidden=['stripe','paypal','twilio','api.resend.com','openai.com','shippo','easypost','fedex','purolator']
    for token in forbidden:
        if token in jl or token in sl: errors.append(f'Intégration externe interdite dans V24.5.23: {token}')

    if errors:
        print(f'ECHEC V24.5.23 profil privé modifiable: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK Profil privé: historique immuable, coffre self-only, MFA conservé et compatibilité enfant 11+ forward-only validée.')
    return 0

if __name__=='__main__': raise SystemExit(main())
