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
t = compact(test)
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
req("ifyears<13then" in m and 'c:=false;' in m and 'f:=false;' in m,
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

# Le pgTAP ne se contente plus d'inspecter les fonctions : il crée un vrai parent,
# un code, puis un compte ayant exactement 11 ans et vérifie les effets persistés.
req('selectplan(16);' in t,
    "Le plan pgTAP comportemental enfant supervisé est inattendu.")
for marker, message in (
    ("insertintoauth.users", "Le test ne crée pas de comptes Auth réels dans la transaction."),
    ("youth-abcd123456", "Le test ne crée pas de code parental déterministe."),
    ("interval'11years'", "Le test ne couvre pas une date donnant exactement 11 ans."),
    ("public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),'child'", "Le test ne vérifie pas la bande child."),
    ("public.sinjira_parent_can_supervise", "Le test ne vérifie pas la supervision parentale."),
    ("notpublic.sinjira_can_social_interact", "Le test ne vérifie pas la coupure sociale avant 13 ans."),
    ("participate=falseandshare_free_text=false", "Le test ne vérifie pas la neutralisation du Programme Contributeur."),
    ("sinjira_minimum_age_11", "Le test ne prouve pas le refus des moins de 11 ans."),
    ("guardian_authorization_required_under_14", "Le test ne prouve pas le refus à 11 ans sans code parental."),
    ("youth_jurisdiction_not_enabled", "Le test ne prouve pas la porte Canada jeunesse."),
):
    req(marker in t, message)

if errors:
    print(f'ECHEC compte enfant supervisé V25: {len(errors)} problème(s).')
    for error in errors:
        print('- ' + error)
    raise SystemExit(1)

print('OK V25: contrat et test comportemental présents pour un compte ayant exactement 11 ans, avec code adulte, lien vérifié, social désactivé et contribution neutralisée.')
