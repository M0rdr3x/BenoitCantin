#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260820003500_sinjira_v24_4_81_dating_strict_safe_meet.sql'
JS=ROOT/'assets/js/sinjira-dating-safe-meet-v24-4-81.js'
CSS=ROOT/'assets/css/sinjira-dating-safe-meet-v24-4-81.css'
PROGRESS=ROOT/'assets/js/sinjira-dating-progress-v24-4-76.js'
TEST=ROOT/'supabase/tests/dating_strict_safe_meet_v24_4_81.test.sql'
errors=[]

def req(cond,msg):
    if not cond: errors.append(msg)

def read(path):
    if not path.exists():
        errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
        return ''
    return path.read_text('utf-8')

mig=read(MIG); js=read(JS); css=read(CSS); progress=read(PROGRESS); test=read(TEST)
compact=''.join(mig.lower().split())

for marker in (
    'create table if not exists public.dating_credit_accounts',
    'create table if not exists public.dating_credit_ledger',
    'create table if not exists public.dating_meet_requests',
    'alter table public.dating_credit_accounts enable row level security',
    'alter table public.dating_credit_ledger enable row level security',
    'alter table public.dating_meet_requests enable row level security',
    'create trigger dating_relationship_gate',
    'create or replace function public.dating_credit_status()',
    'create or replace function public.dating_safe_meet_status',
    'create or replace function public.dating_safe_meet_opt_in',
    'create or replace function public.dating_safe_meet_cancel',
): req(marker in mig, f'Migration: marqueur absent: {marker}')

confirm=mig[mig.find('create or replace function public.dating_confirm_single_and_serious()'):mig.find('create or replace function private.dating_enforce_relationship_gate()')]
req('update public.account_safety_profiles' not in confirm.lower(),'La confirmation Rencontres modifie encore le statut amoureux central.')
req("relationship_status='single'" in ''.join(confirm.split()),'La confirmation ne vérifie pas explicitement le statut single.')
req('serious_intent_confirmed=false' in compact,'Le changement de statut ne révoque pas l’activation Rencontres.')
req("status='closed'" in compact,'Le changement de statut ne ferme pas les connexions actives.')
req('single_confirmed_at=null' in compact,'Le changement de statut ne force pas une nouvelle confirmation.')
req('private.dating_is_eligible(pa.user_id)' in mig and 'private.dating_is_eligible(pb.user_id)' in mig,'Lecture de conversation insuffisamment verrouillée.')
req('not private.dating_is_eligible(v_a_user)' in mig and 'not private.dating_is_eligible(v_b_user)' in mig,'Dévoilement/safe-meet ne reverifie pas les deux participants.')

req('values(p_user_id,3,3' in compact,'Allocation initiale de 3 crédits absente.')
req("'monthly_free_credits',1" in compact,'Crédit gratuit mensuel absent.')
req("'cost_per_safe_meet',1" in compact,'Coût de 1 crédit absent.')
req("'purchases_enabled',false" in compact,'Achat de crédits pas explicitement désactivé.')
req("values(v_payer_user,-1,'safe_meet_recommendation'" in compact,'Débit atomique de 1 crédit absent.')
req('dating_credit_one_safe_meet_debit_idx' in mig,'Protection anti-double-débit absente.')
req('profile_a_consent' in mig and 'profile_b_consent' in mig,'Double consentement absent.')
req('dating_connection_identity_revealed' in mig,'Dévoilement mutuel non requis pour les suggestions.')
req("'waiting','generated','cancelled'" in mig,'Cycle de vie de demande de rencontre incomplet.')
req("'home'" not in compact and "'hotel'" not in compact and "'nightclub'" not in compact,'Une catégorie de lieu privé/risqué est proposée par le moteur.')
req('lieu public' in mig.lower() and 'propre moyen de retour' in mig.lower(),'Checklist de sécurité publique insuffisante.')
req('external_paid_provider_used' in mig and 'false' in mig,'Le résultat ne déclare pas explicitement l’absence de fournisseur payant.')

for banned in ('stripe','paypal','google places','places api','mapbox','openai_api_key','navigator.geolocation','getcurrentposition'):
    req(banned not in (mig+'\n'+js).lower(),f'Intégration interdite/payante détectée: {banned}')

req("import './sinjira-dating-safe-meet-v24-4-81.js';" in progress,'Le module Safe Meet V24.4.81 n’est pas chargé par Rencontres.')
req('dating_credit_status' in js,'Interface: solde de crédits absent.')
req('dating_safe_meet_opt_in' in js,'Interface: double consentement Safe Meet absent.')
req('dating_safe_meet_cancel' in js,'Interface: annulation sans débit absente.')
req('openstreetmap.org/search?query=' in js,'Interface: recherche cartographique gratuite OpenStreetMap absente.')
req('encodeURIComponent' in js,'Interface: requête cartographique non encodée.')
req('Aucun achat activé' in js,'Interface: absence d’achat non expliquée.')
req('3 crédits gratuits au départ' in js and '+1 gratuit par mois' in js,'Interface: allocation gratuite non expliquée.')
req('domicile' in js.lower() and 'hôtel' in js.lower(),'Interface: consignes contre lieu privé insuffisantes.')
req('@media(max-width:820px)' in css,'CSS Safe Meet non responsive.')
req('@media(prefers-reduced-motion:reduce)' in css,'CSS Safe Meet sans garde reduced-motion.')
req('select plan(32);' in test,'pgTAP V24.4.81 incomplet.')

if errors:
    print(f'ECHEC Rencontres V24.4.81: {len(errors)} problème(s)')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK Rencontres V24.4.81: célibat strict + Crédit Rencontre + suggestions publiques gratuites et consenties.')
