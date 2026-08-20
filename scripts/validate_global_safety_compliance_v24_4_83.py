#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260820022000_sinjira_v24_4_83_global_safety_compliance.sql'
V82=ROOT/'supabase/migrations/20260820020733_sinjira_v24_4_82_minor_exploitation_safety.sql'
TEST=ROOT/'supabase/tests/global_safety_compliance_v24_4_83.test.sql'
SIGNUP_JS=ROOT/'assets/js/v24-signup.js'
SIGNUP_HTML=ROOT/'compte/inscription.html'
PRIVACY=ROOT/'confidentialite.html'
ACCOUNT_PRIVACY=ROOT/'compte/confidentialite-joueur.html'
PRIVACY_CENTER=ROOT/'compte/vie-privee.html'
PRIVACY_JS=ROOT/'assets/js/sinjira-privacy-center-v24-4-83.js'
LEGAL=ROOT/'avis-legal.html'
DOCS=[
 ROOT/'docs/compliance/INTERNATIONAL_COMPLIANCE_MATRIX.md',
 ROOT/'docs/compliance/EFVP.md',
 ROOT/'docs/compliance/CHILD_SAFETY_RISK_ASSESSMENT.md',
 ROOT/'docs/compliance/ILLEGAL_CONTENT_RISK_ASSESSMENT.md',
 ROOT/'docs/compliance/DATA_RETENTION_SCHEDULE.md',
 ROOT/'docs/compliance/PRIVACY_INCIDENT_RESPONSE.md',
 ROOT/'docs/compliance/CHILD_SEXUAL_EXPLOITATION_REPORTING_PLAYBOOK.md',
 ROOT/'docs/compliance/COMMERCE_ACTIVATION_GATE.md',
]
errors=[]

def read(p):
    if not p.exists():
        errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
        return ''
    return p.read_text('utf-8')

def req(ok,msg):
    if not ok: errors.append(msg)

mig=read(MIG); v82=read(V82); test=read(TEST); signup_js=read(SIGNUP_JS); signup_html=read(SIGNUP_HTML)
privacy=read(PRIVACY); account_privacy=read(ACCOUNT_PRIVACY); privacy_center=read(PRIVACY_CENTER); privacy_js=read(PRIVACY_JS); legal=read(LEGAL)
docs='\n'.join(read(p) for p in DOCS)
compact=''.join(mig.lower().split())
alltext='\n'.join((mig,test,signup_js,signup_html,privacy,account_privacy,privacy_center,privacy_js,legal,docs)).lower()

for marker in (
 'create table if not exists private.privacy_incident_register',
 'create table if not exists private.privacy_requests',
 'create table if not exists private.privacy_legal_holds',
 'create table if not exists private.safety_escalation_cases',
 'create or replace function public.privacy_create_request',
 'create or replace function public.privacy_my_requests',
 'create or replace function public.privacy_admin_record_incident',
 'create trigger trg_safety_create_escalation_case',
 'sinjira_minimum_age_13',
): req(marker in mig.lower(),f'Migration V83 marqueur absent: {marker}')

req("years<13thenraiseexception'sinjira_minimum_age_13'" in compact,'Le serveur ne refuse pas explicitement les moins de 13 ans.')
req("ifyears<14then" in compact and 'guardian_authorization_required_under_14' in mig.lower(),'L’autorisation parentale à 13 ans n’est pas préservée.')
req("interval'5years'" in compact,'La rétention minimale de cinq ans des incidents est absente.')
req("interval'30days'" in compact,'L’échéance interne de 30 jours des demandes est absente.')
req('enable row level security' in mig.lower(),'RLS absent des registres V83.')
req('revoke all on private.privacy_incident_register from public,anon,authenticated' in mig.lower(),'Registre incidents exposé à un rôle navigateur.')
req('revoke all on private.privacy_requests from public,anon,authenticated' in mig.lower(),'Demandes vie privée exposées directement.')

req('age<13' in signup_js and '13 ans et plus' in signup_js,'JavaScript inscription pas aligné sur 13+.')
req('partir de 13 ans' in signup_html.lower() and 'moins de 13 ans' in signup_html.lower(),'Interface inscription pas alignée sur 13+.')
req('v24-signup.js?v=24.4.83' in signup_html,'Version du client inscription non invalidée.')

for phrase in ('registre interne','cinq ans','30 jours','13 ans','rencontres sinjira™ est strictement 18+','ia distante payante est désactivée','paiements en ligne'):
    req(phrase in privacy.lower(),f'Politique vie privée incomplète: {phrase}')
for phrase in ('accès à mes renseignements','suppression','retrait d’un consentement','plainte de vie privée'):
    req(phrase in privacy_center.lower(),f'Centre Vie privée incomplet: {phrase}')
req("rpc('privacy_my_requests'" in privacy_js and "rpc('privacy_create_request'" in privacy_js,'Centre Vie privée non relié aux RPC.')

for phrase in ('prostitution','proxénétisme','traite','vente de drogues','grooming','13+','18+ strict'):
    req(phrase in legal.lower(),f'Avis légal incomplet: {phrase}')

for phrase in ('québec','canada','rgpd','digital services act','royaume-uni','coppa'):
    req(phrase in docs.lower(),f'Matrice/gouvernance internationale incomplète: {phrase}')
for phrase in ('confidentialité élevée','efvp','legal holds','21 jours','fonction d\'achat'):
    req(phrase in docs.lower(),f'Gouvernance V83 marqueur absent: {phrase}')

req('paid_sexual_content' in v82.lower() and 'human_trafficking' in v82.lower() and 'dating_profiles_adult_only' in v82.lower(),'Le contrat V24.4.82 de sécurité n’est plus présent.')
req('select plan(30);' in test,'Plan pgTAP V83 inattendu.')
req("'sinjira_content_policy_guard'" in test and "'dating_profiles_adult_only'" in test,'Les tests V83 ne protègent pas les gardes V82.')

for paid in ('stripe','paypal','openai_api_key','paymentintent','google places api','mapbox token'):
    req(paid not in alltext,f'V83 introduit une intégration payante/interdite: {paid}')

if errors:
    print(f'ECHEC conformité V24.4.83: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK V24.4.83: 13+ + droits vie privée + incidents 5 ans + escalade sécurité + gouvernance internationale, sans service payant.')
