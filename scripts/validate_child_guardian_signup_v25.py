#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase/migrations/20260916210000_sinjira_v25_child_guardian_signup.sql'
TEST = ROOT / 'supabase/tests/child_guardian_signup_v25.test.sql'
YOUTH_BASE = ROOT / 'supabase/migrations/20260816140000_sinjira_v24_4_12_youth_safety.sql'
SIGNUP_JS = ROOT / 'assets/js/v24-signup.js'
SIGNUP_HTML = ROOT / 'compte/inscription.html'

errors = []

def read(path):
    if not path.exists():
        errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
        return ''
    return path.read_text('utf-8')

def req(condition, message):
    if not condition:
        errors.append(message)

def compact(text):
    return ''.join(text.lower().split())

mig = read(MIG)
test = read(TEST)
youth_base = read(YOUTH_BASE)
signup_js = read(SIGNUP_JS)
signup_html = read(SIGNUP_HTML)

m = compact(mig)
t = test.lower()
y = compact(youth_base)
j = compact(signup_js)
h = signup_html.lower()

# Autorité serveur et seuil minimal.
req("ifyears<11thenraiseexception'sinjira_minimum_age_11'" in m,
    "La migration V25 n'impose pas le minimum serveur de 11 ans.")
req("ifyears<14then" in m and 'guardian_authorization_required_under_14' in m,
    "L'autorisation parentale obligatoire de 11 à 13 ans n'est pas imposée côté serveur.")
req("years<18andresidence_countrynotin('canada','ca','can')" in m and 'youth_jurisdiction_not_enabled' in m,
    "La porte de juridiction jeunesse Canada n'est pas conservée côté serveur.")
req("ifinv.idisnotnullandyears<18then" in m and "'verified','parent'" in m,
    "Le lien parent/enfant vérifié n'est pas créé après validation du code.")

# Bande enfant distincte : elle ne doit pas hériter automatiquement des droits sociaux jeunesse.
req("interval'11years'then'under11'" in m,
    "La bande under11 est absente.")
req("interval'13years'then" in m and "then'child'" in m and "else'child_pending'" in m,
    "La bande enfant 11–12 ans n'est pas définie distinctement.")
req("public.sinjira_age_band(p_child)in('child','youth')" in m,
    "La supervision parentale ne couvre pas enfant + jeunesse.")
req('createorreplacefunctionpublic.sinjira_can_social_interact' not in m,
    "La migration enfant ne doit pas élargir elle-même la fonction d'interaction sociale.")
req("whenp_a=p_bthenpublic.sinjira_age_band(p_a)in('adult','youth')" in y,
    "Le contrat social historique n'exclut plus explicitement la bande child.")
req("public.sinjira_age_band(p_a)='youth'andpublic.sinjira_age_band(p_b)='youth'thentrue" in y,
    "L'isolation sociale jeunesse historique n'est plus prouvée.")

# Minimisation : pas de Programme Contributeur pour 11–12 ans.
req("ifyears<13then" in m and 'c:=false;' in mig.lower() and 'f:=false;' in mig.lower(),
    "Le serveur ne neutralise pas le Programme Contributeur pour les 11–12 ans.")
req('constmin_account_age=11;' in j and 'if(age<min_account_age)' in j,
    "Le client n'applique pas le seuil de 11 ans.")
req('guardianinput.required=number.isinteger(age)&&age>=min_account_age&&age<14;' in j,
    "Le client n'exige pas le code parental de 11 à 13 ans.")
req('constchild=age<13;' in j and "account_age_band:child?'child_11_12'" in j,
    "Le client ne marque pas distinctement le compte enfant 11–12.")
req("constcontributor=!child&&d.get('initial_contributor_opt_in')==='yes';" in j,
    "Le client pourrait encore activer le Programme Contributeur pour un enfant.")
req('age<18&&!iscanada(residencecountry)' in j,
    "La porte Canada jeunesse n'est plus appliquée côté client.")

# Interface et invalidation de cache.
req('compte disponible à partir de 11 ans' in h,
    "L'interface n'explique pas le seuil de 11 ans.")
req('moins de 11 ans' in h and '11–12 ans' in h and '13 ans' in h and '14–17 ans' in h,
    "L'interface n'explique pas clairement les bandes d'âge.")
req('comptes de 11 à 17 ans' in h and 'canada' in h,
    "L'interface n'explique pas la porte Canada pour les comptes jeunesse.")
req('v24-signup.js?v=25.0.1&amp;rev=child-11' in h,
    "La version du client d'inscription enfant n'est pas invalidée.")
req('réservés aux personnes de 13 ans et plus' not in h,
    "Un ancien message 13+ global subsiste dans l'interface.")

# Le pgTAP dédié doit couvrir les invariants clés.
req('select plan(12);' in t,
    "Le plan pgTAP enfant supervisé est inattendu.")
for marker in (
    'sinjira_minimum_age_11',
    'guardian_authorization_required_under_14',
    'youth_jurisdiction_not_enabled',
    "then 'child'",
    "in ('child', 'youth')",
):
    req(marker in t, f'Test pgTAP enfant incomplet: {marker}')

if errors:
    print(f'ECHEC compte enfant supervisé V25: {len(errors)} problème(s).')
    for error in errors:
        print('- ' + error)
    raise SystemExit(1)

print('OK V25: compte enfant 11–12 supervisé, code adulte obligatoire, Canada jeunesse, social désactivé avant 13 ans et contribution neutralisée.')
