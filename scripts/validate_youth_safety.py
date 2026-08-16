#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'
SIGNUP=ROOT/'assets'/'js'/'v24-signup.js'
HTML=ROOT/'compte'/'inscription.html'


def latest_sql()->str:
    return '\n'.join(p.read_text('utf-8',errors='ignore') for p in sorted(MIG.glob('*.sql')))


def main()->int:
    errors=[]
    sql=latest_sql()
    low=re.sub(r'\s+',' ',sql.lower())
    compact=re.sub(r'\s+','',sql.lower())
    signup=SIGNUP.read_text('utf-8',errors='ignore')
    html=HTML.read_text('utf-8',errors='ignore')

    required_functions=[
        'sinjira_age_band','sinjira_social_compatible','sinjira_parent_can_supervise',
        'get_guardian_youth_contacts','respond_family_relationship'
    ]
    for name in required_functions:
        if f'function public.{name}' not in low:
            errors.append(f'Fonction jeunesse absente: {name}')

    for band in ['under_12','youth_12_17','adult_18_plus']:
        if band not in sql:
            errors.append(f'Cohorte jeunesse/adulte absente: {band}')

    # Les deux types de messagerie doivent refuser les échanges inter-cohortes.
    for policy in ['real_messages_insert','char_messages_insert']:
        start=low.rfind(f'create policy {policy}')
        if start<0:
            errors.append(f'Politique sociale absente: {policy}')
            continue
        block=low[start:start+1800]
        if 'sinjira_social_compatible(sender_user_id,recipient_user_id)' not in block:
            errors.append(f'Politique {policy} ne bloque pas les échanges jeunesse/adulte.')

    for policy in ['real_posts_read','char_posts_read','real_comments_read','char_comments_read']:
        start=low.rfind(f'create policy {policy}')
        if start<0:
            errors.append(f'Politique de lecture absente: {policy}')
            continue
        block=low[start:start+1800]
        if 'sinjira_social_compatible' not in block:
            errors.append(f'Politique {policy} ne limite pas la visibilité à la cohorte compatible.')

    # Guardian overview may expose contact metadata, but not the body of private messages.
    m=re.search(r'create\s+or\s+replace\s+function\s+public\.get_guardian_youth_contacts\([^)]*\).*?\$\$.*?\$\$\s*;',sql,re.I|re.S)
    if not m:
        errors.append('RPC de supervision parentale absente.')
    else:
        block=m.group(0).lower()
        if 'sinjira_parent_can_supervise' not in block:
            errors.append('RPC de supervision parentale sans vérification du lien parent/tuteur.')
        if "'body'" in block or 'body,' in block or '.body' in block:
            errors.append('RPC de supervision parentale expose potentiellement le contenu des messages.')

    # A linked relationship can only start pending and must be accepted by the related account via RPC.
    if 'respond_family_relationship' not in sql:
        errors.append('Acceptation bilatérale des relations familiales absente.')
    if "related_user_id is not null and related_user_id<>owner_user_id and status='pending'" not in compact:
        errors.append('Une relation familiale liée peut être créée sans statut pending.')

    # Signup contract.
    for marker in ["if(age<12)","if(age>120)","['Femme','Homme'].includes(gender)"]:
        if marker not in signup:
            errors.append(f'Validation inscription absente: {marker}')

    # Backend gender constraint must only accept the two configured values (or null for legacy/unfinished records).
    if "gender is null or gender in ('Homme','Femme')" not in sql:
        errors.append('Contrainte backend Homme/Femme absente de private_profiles.')

    # The current HTML must at least keep the required date and gender controls. Extra values are rejected by JS/DB,
    # but we still warn here so the UI can be cleaned if a stale option remains.
    if 'name="birth_date"' not in html or 'required' not in html:
        errors.append('Date de naissance obligatoire absente de l’inscription.')
    if 'name="gender"' not in html:
        errors.append('Champ sexe/genre absent de l’inscription.')
    stale=[x for x in ['Non binaire','Autre','Préfère ne pas répondre'] if x in html]
    if stale:
        errors.append('Options d’interface non conformes encore visibles: '+', '.join(stale))

    if errors:
        print(f'ECHEC sécurité jeunesse: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK jeunesse: 12+ à l’inscription, cohortes 12–17/18+ isolées au backend, relations parentales confirmées et supervision sans contenu privé.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
