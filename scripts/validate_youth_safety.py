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
    warnings=[]
    sql=latest_sql()
    low=re.sub(r'\s+',' ',sql.lower())
    compact=re.sub(r'\s+','',sql.lower())
    signup=SIGNUP.read_text('utf-8',errors='ignore')
    html=HTML.read_text('utf-8',errors='ignore')

    required_functions=[
        'sinjira_age_band','sinjira_social_compatible','sinjira_parent_can_supervise',
        'get_guardian_youth_contacts','respond_family_relationship','enforce_sinjira_private_profile_age'
    ]
    for name in required_functions:
        if f'function public.{name}' not in low:
            errors.append(f'Fonction jeunesse absente: {name}')

    for band in ['under_12','youth_12_17','adult_18_plus']:
        if band not in sql:
            errors.append(f'Cohorte jeunesse/adulte absente: {band}')

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

    m=re.search(r'create\s+or\s+replace\s+function\s+public\.get_guardian_youth_contacts\([^)]*\).*?\$\$.*?\$\$\s*;',sql,re.I|re.S)
    if not m:
        errors.append('RPC de supervision parentale absente.')
    else:
        block=m.group(0).lower()
        if 'sinjira_parent_can_supervise' not in block:
            errors.append('RPC de supervision parentale sans vérification du lien parent/tuteur.')
        if "'body'" in block or 'body,' in block or '.body' in block:
            errors.append('RPC de supervision parentale expose potentiellement le contenu des messages.')

    if 'respond_family_relationship' not in sql:
        errors.append('Acceptation bilatérale des relations familiales absente.')
    if "related_user_idisnotnullandrelated_user_id<>owner_user_idandstatus='pending'" not in compact:
        errors.append('Une relation familiale liée peut être créée sans statut pending.')

    for marker in ["if(age<12)","if(age>120)","['Femme','Homme'].includes(gender)","normalizeGenderControl()"]:
        if marker not in signup:
            errors.append(f'Validation inscription absente: {marker}')

    if "genderisnullorgenderin('homme','femme')" not in compact:
        errors.append('Contrainte backend Homme/Femme absente de private_profiles.')
    for marker in ['sinjira_minimum_age_12','profile_sex_required','beforeinsertorupdateofbirth_date,gender']:
        if marker not in compact:
            errors.append(f'Verrou serveur âge/sexe absent: {marker}')

    if 'name="birth_date"' not in html or 'required' not in html:
        errors.append('Date de naissance obligatoire absente de l’inscription.')
    if 'name="gender"' not in html:
        errors.append('Champ sexe/genre absent de l’inscription.')
    stale=[x for x in ['Non binaire','Autre','Préfère ne pas répondre'] if x in html]
    if stale:
        if 'option.remove()' not in signup or "new Set(['','Femme','Homme'])" not in signup:
            errors.append('Anciennes options d’interface encore visibles sans normalisation runtime sécurisée: '+', '.join(stale))
        else:
            warnings.append('Le HTML historique contient encore des options retirées immédiatement par v24-signup.js; nettoyage statique recommandé à la prochaine réécriture sûre de cette page.')

    for warning in warnings:
        print('AVERTISSEMENT: '+warning)
    if errors:
        print(f'ECHEC sécurité jeunesse: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK jeunesse: verrou serveur 12+, cohortes 12–17/18+ isolées, relations parentales confirmées et supervision sans contenu privé.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
