#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase/migrations/20260916210000_sinjira_v25_child_guardian_signup.sql'
TEST = ROOT / 'supabase/tests/child_guardian_signup_v25.test.sql'
YOUTH_BASE = ROOT / 'supabase/migrations/20260816140000_sinjira_v24_4_12_youth_safety.sql'
SIGNUP_JS = ROOT / 'assets/js/v24-signup.js'
BACKEND_JS = ROOT / 'assets/js/sinjira-supabase.js'
RELATIONS_JS = ROOT / 'assets/js/v24-relations.js'
SIGNUP_HTML = ROOT / 'compte/inscription.html'
RELATIONS_HTML = ROOT / 'compte/relations.html'
BROWSER_TEST = ROOT / 'tests/e2e/test_public_site.py'

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
backend_js = read(BACKEND_JS)
relations_js = read(RELATIONS_JS)
signup_html = read(SIGNUP_HTML)
relations_html = read(RELATIONS_HTML)
browser_test = read(BROWSER_TEST)

m = compact(mig)
t = compact(test)
y = compact(youth_base)
j = compact(signup_js)
b = compact(backend_js)
r = compact(relations_js)
h = signup_html.lower()
rh = relations_html.lower()
bt = compact(browser_test)

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
req("g.status='verified'andg.revoked_atisnull" in m,
    "La bande supervisée ne vérifie pas revoked_at en plus du statut verified.")
req('revokeallonfunctionpublic.sinjira_age_band(uuid)frompublic,anon,authenticated' in m and 'grantexecuteonfunctionpublic.sinjira_age_band(uuid)toservice_role' in m,
    "La cohorte UUID arbitraire est réexposée aux comptes authentifiés.")
req('revokeallonfunctionpublic.sinjira_my_age_band()frompublic,anon,authenticated' in m and 'grantexecuteonfunctionpublic.sinjira_my_age_band()toanon,authenticated,service_role' in m,
    "Le wrapper de cohorte self-only n est pas borné aux rôles API sans UUID arbitraire.")
req('revokeallonfunctionpublic.sinjira_parent_can_supervise(uuid,uuid)frompublic,anon,authenticated' in m,
    "La relation parent/enfant arbitraire reste sondable par authenticated.")
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
req('constguardianrequired=number.isinteger(age)&&age>=min_account_age&&age<14;' in j,
    "Le client ne calcule pas explicitement l'autorisation parentale obligatoire de 11 à 13 ans.")
req('guardianinput.required=guardianrequired;' in j,
    "Le client n'exige pas le code parental de 11 à 13 ans.")
req('constchild=age<13;' in j and "account_age_band:child?'child_11_12'" in j,
    "Le client ne marque pas distinctement le compte enfant 11–12.")
req("constcontributor=!child&&d.get('initial_contributor_opt_in')==='yes';" in j,
    "Le client pourrait encore activer le Programme Contributeur pour un enfant.")
req('contributorpanel.hidden=child;' in j,
    "Le formulaire continue d'exposer le Programme Contributeur à un compte enfant 11–12.")
req('age<18&&!iscanada(residencecountry)' in j,
    "La porte Canada jeunesse n'est plus appliquée côté client.")

# Frontière de session : aucune création de compte enfant ne doit réutiliser implicitement
# la session du parent ou d'un autre compte déjà connecté dans le navigateur.
req("getsupabase().auth.getsession()" in j and "sessionboundarystate=data?.session?.user?'active':'clear';" in j,
    "Le client ne détecte plus une session déjà active avant l'inscription.")
req("getsupabase().auth.signout({scope:'local'})" in j,
    "Le parcours d'inscription ne permet plus de séparer localement la session parent/enfant.")
req("if(boundary==='active')" in j and 'éviterdemélangerlecompteduparentetlenouveaucompte' in j,
    "La soumission n'est plus bloquée lorsqu'un autre compte est déjà connecté.")
req("if(boundary==='error')" in j and 'parsécurité,lacréationd’unnouveaucompteestbloquée' in j,
    "La vérification de session n'est plus fail-closed.")
req("submit.disabled=busystate||sessionboundarystate!=='clear';" in j,
    "Le bouton de création n'est plus verrouillé tant que la frontière de session n'est pas claire.")

# Les messages communs doivent refléter 11 ans et détecter explicitement un serveur encore ancien.
req("guardian_authorization_required_under_14" in b and '11à13ans' in b,
    "Le message commun d'autorisation parentale n'est pas aligné sur 11–13 ans.")
req('sinjira_minimum_age_11' in b and 'àpartirde11ans' in b,
    "Le message commun du seuil minimum 11 ans est absent.")
req('sinjira_minimum_age_(?:12|13)' in b and 'ancianerègled’âge' not in b,
    "Le détecteur de règle serveur héritée 12/13 ans est absent.")
req('synchronisationdumoduleenfant11ans' in b,
    "Le diagnostic d'un serveur encore ancien n'est pas explicite.")

# Parcours parent : le code doit être générable avant l'inscription, et child_pending doit être reconnu.
req("s.rpc('create_guardian_signup_invite')" in r,
    "L'interface parent ne génère plus le code d'inscription.")
req("['child_pending','youth_pending'].includes(ageband)" in r,
    "L'interface de supervision ne reconnaît pas child_pending.")
req('data-create-guardian-code' in rh and 'de 11 à 13 ans' in rh,
    "La page Relations n'explique pas le code parental obligatoire de 11 à 13 ans.")
req('ouvrir l’inscription' in rh and 'v24-relations.js?v=25.0.2&amp;rev=junior-community' in rh,
    "Le parcours parent vers l'inscription ou son invalidation de cache est incomplet.")

# Interface et invalidation de cache.
req('compte disponible à partir de 11 ans' in h,
    "L'interface n'explique pas le seuil de 11 ans.")
req('moins de 11 ans' in h and '11–12 ans' in h and '13 ans' in h and '14–17 ans' in h,
    "L'interface n'explique pas clairement les bandes d'âge.")
req('comptes de 11 à 17 ans' in h and 'canada' in h,
    "L'interface n'explique pas la porte Canada pour les comptes jeunesse.")
req('data-child-guardian-guide' in h and 'parent / tuteur : générer le code' in h,
    "Le formulaire enfant n'offre pas de chemin clair vers la génération du code parental.")
req('connexion.html?next=%2fcompte%2frelations.html' in h,
    "Le raccourci parent ne revient pas vers les outils de supervision.")
req('déconnectez le compte parent' in h,
    "Le formulaire n'explique pas la séparation de session parent/enfant.")
req('data-signup-session-warning' in h and 'data-signup-session-signout' in h and 'déconnecter la session active' in h,
    "L'interface n'affiche plus la frontière de session lorsqu'un compte est déjà connecté.")
req('data-contributor-panel' in h,
    "Le panneau Contributeur ne peut pas être masqué pour un compte enfant.")
req('v24-signup.js?v=25.0.1&amp;rev=child-11-flow-session' in h,
    "La version du client d'inscription enfant n'est pas invalidée après le durcissement de session.")
req('réservés aux personnes de 13 ans et plus' not in h,
    "Un ancien message 13+ global subsiste dans l'interface.")

# Régression navigateur : avant toute promotion, Playwright doit vérifier le comportement visible
# qui avait échoué dans le vrai parcours utilisateur, pas seulement la présence du code source.
req("d.setfullyear(d.getfullyear()-11)" in bt and "locator('#signup-birth-date').fill(child_birth)" in bt,
    "Le test navigateur ne simule plus une date donnant exactement 11 ans.")
req("[data-child-guardian-guide]" in bt and "[data-guardian-code-wrap]" in bt,
    "Le test navigateur ne vérifie plus l'ouverture du parcours parental à 11 ans.")
req("code.required===true" in bt,
    "Le test navigateur ne prouve plus que le code parental devient obligatoire.")
req("contributor&&contributor.hidden" in bt and "[data-contributor-panel]" in bt,
    "Le test navigateur ne prouve plus que le Programme Contributeur disparaît à 11 ans.")
req("[data-signup-session-warning]" in bt and "[data-signup-session-signout]" in bt,
    "Le test navigateur ne protège plus la séparation de session parent/enfant.")

# Le pgTAP crée un vrai parent, un code et un enfant de 11 ans, puis vérifie aussi
# la transition automatique child -> youth à la frontière exacte du 13e anniversaire.
req('selectplan(26);' in t,
    "Le plan pgTAP comportemental enfant supervisé et frontière 13 ans est inattendu.")
for marker, message in (
    ("insertintoauth.users", "Le test ne crée pas de comptes Auth réels dans la transaction."),
    ("youth-abcd123456", "Le test ne crée pas de code parental déterministe."),
    ("interval'11years'", "Le test ne couvre pas une date donnant exactement 11 ans."),
    ("public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),'child'", "Le test ne vérifie pas la bande child."),
    ("public.sinjira_parent_can_supervise", "Le test ne vérifie pas la supervision parentale."),
    ("notpublic.sinjira_can_social_interact", "Le test ne vérifie pas la coupure sociale avant 13 ans."),
    ("participate=falseandshare_free_text=false", "Le test ne vérifie pas la neutralisation du Programme Contributeur."),
    ("interval'13years'+interval'1day'", "Le test ne vérifie pas la veille du 13e anniversaire."),
    ("lejourdes13anslaclassificationdevientyouthautomatiquement", "Le test ne vérifie pas la bascule automatique vers youth à 13 ans."),
    ("lecontratsocialjeunessepeutsappliquerautomatiquementàpartirde13ans", "Le test ne vérifie pas la réouverture contrôlée du contrat social à 13 ans."),
    ("sinjira_minimum_age_11", "Le test ne prouve pas le refus des moins de 11 ans."),
    ("guardian_authorization_required_under_14", "Le test ne prouve pas le refus à 11 ans sans code parental."),
    ("youth_jurisdiction_not_enabled", "Le test ne prouve pas la porte Canada jeunesse."),
    ("authenticatednepeutpassonderlabandeâgedunuuidarbitraire", "Le test ne prouve pas la fermeture de sinjira_age_band(uuid)."),
    ("authenticatedpeutlireuniquementsaproprebandeâge", "Le test ne prouve pas le wrapper self-only de cohorte."),
    ("anonpeutévalueruniquementsaproprebandeself-onlypourlesrlspubliques", "Le test ne prouve pas l'accès anon borné au wrapper self-only requis par les RLS publiques."),
    ("authenticatednepeutpassonderunerelationparent/enfantarbitraire", "Le test ne prouve pas la confidentialité du helper de supervision."),
    ("revoked_atseulsuffitàretirerlabandesuperviséemêmesistatusestencoreverified", "Le test ne prouve pas le fail-closed sur revoked_at pour la bande âge."),
    ("revoked_atseulsuffitàretirerl supervisionparentale".replace(" ",""), "Le test ne prouve pas le fail-closed sur revoked_at pour la supervision."),
):
    req(marker in t, message)

if errors:
    print(f'ECHEC compte enfant supervisé V25: {len(errors)} problème(s).')
    for error in errors:
        print('- ' + error)
    raise SystemExit(1)

print('OK V25: compte enfant 11 ans, parcours parent, séparation de session, minimisation, régression navigateur et transition automatique child -> youth à 13 ans sont verrouillés par le contrat et les tests.')
