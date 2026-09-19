#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase/migrations/20260916210000_sinjira_v25_child_guardian_signup.sql'
TEST = ROOT / 'supabase/tests/child_guardian_signup_v25.test.sql'
REDEEM_MIG = ROOT / 'supabase/migrations/20260919013000_sinjira_v25_child_pending_guardian_redeem.sql'
GUARDIAN_AAL2_MIG = ROOT / 'supabase/migrations/20260919023000_sinjira_v25_guardian_invite_aal2.sql'
GUARDIAN_SECRET_MIN_MIG = ROOT / 'supabase/migrations/20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql'
GUARDIAN_READ_AAL2_MIG = ROOT / 'supabase/migrations/20260919033000_sinjira_v25_guardian_invite_read_aal2.sql'
GUARDIAN_REVOKE_AAL2_MIG = ROOT / 'supabase/migrations/20260919043000_sinjira_v25_guardian_revoke_aal2.sql'
GUARDIAN_ADULT_VIS_MIG = ROOT / 'supabase/migrations/20260919050000_sinjira_v25_guardian_majority_visibility.sql'
YOUTH_BASE = ROOT / 'supabase/migrations/20260816140000_sinjira_v24_4_12_youth_safety.sql'
SIGNUP_JS = ROOT / 'assets/js/v24-signup.js'
BACKEND_JS = ROOT / 'assets/js/sinjira-supabase.js'
RELATIONS_JS = ROOT / 'assets/js/v24-relations.js'
SIGNUP_HTML = ROOT / 'compte/inscription.html'
RELATIONS_HTML = ROOT / 'compte/relations.html'
BROWSER_TEST = ROOT / 'tests/e2e/test_public_site.py'
CHILD_BROWSER_TEST = ROOT / 'tests/e2e/test_child_signup.py'

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
redeem_mig = read(REDEEM_MIG)
guardian_aal2_mig = read(GUARDIAN_AAL2_MIG)
guardian_secret_min_mig = read(GUARDIAN_SECRET_MIN_MIG)
guardian_read_aal2_mig = read(GUARDIAN_READ_AAL2_MIG)
guardian_revoke_aal2_mig = read(GUARDIAN_REVOKE_AAL2_MIG)
guardian_adult_vis_mig = read(GUARDIAN_ADULT_VIS_MIG)
youth_base = read(YOUTH_BASE)
signup_js = read(SIGNUP_JS)
backend_js = read(BACKEND_JS)
relations_js = read(RELATIONS_JS)
signup_html = read(SIGNUP_HTML)
relations_html = read(RELATIONS_HTML)
browser_test = read(BROWSER_TEST)
child_browser_test = read(CHILD_BROWSER_TEST)

m = compact(mig)
t = compact(test)
rm = compact(redeem_mig)
gm = compact(guardian_aal2_mig)
gsm = compact(guardian_secret_min_mig)
grm = compact(guardian_read_aal2_mig)
grv = compact(guardian_revoke_aal2_mig)
gav = compact(guardian_adult_vis_mig)
y = compact(youth_base)
j = compact(signup_js)
b = compact(backend_js)
r = compact(relations_js)
h = signup_html.lower()
rh = relations_html.lower()
bt = compact(browser_test)
cbt = compact(child_browser_test)

# Autorité serveur et seuil minimal.
req("ifyears<11thenraiseexception'sinjira_minimum_age_11'" in m,
    "La migration V25 n'impose pas le minimum serveur de 11 ans.")
req("ifyears<14then" in m and 'guardian_authorization_required_under_14' in m,
    "L'autorisation parentale obligatoire de 11 à 13 ans n'est pas imposée côté serveur.")
req("years<18andresidence_countrynotin('canada','ca','can')" in m and 'youth_jurisdiction_not_enabled' in m,
    "La porte de juridiction jeunesse Canada n'est pas conservée côté serveur.")
req("ifinv.idisnotnullandyears<18then" in m and "'verified','parent'" in m,
    "Le lien parent/enfant vérifié n'est pas créé après validation du code.")
req("bandnotin('child_pending','youth_pending','youth')" in rm,
    "Le RPC de rétablissement ne reconnaît pas child_pending.")
req("g.status='verified'andg.revoked_atisnull" in rm,
    "Le RPC de rétablissement ne distingue pas un lien réellement actif d'un lien révoqué.")
req("updatepublic.guardian_signup_invitessetused_at=now(),minor_user_id=uid" in rm,
    "Le RPC de rétablissement ne consomme pas atomiquement le code parental.")
req("revokeallonfunctionpublic.redeem_guardian_signup_invite(text)frompublic,anon" in rm
    and "grantexecuteonfunctionpublic.redeem_guardian_signup_invite(text)toauthenticated" in rm,
    "Les ACL du RPC de rétablissement parental ne sont pas bornées.")
req("coalesce(auth.jwt()->>'aal','aal1')<>'aal2'" in gm and "mfa_aal2_required" in gm,
    "La création d'un code parental n'exige pas explicitement AAL2 côté serveur.")
req("notpublic.sinjira_mfa_access_allowed(uid)" in gm and "mfa_required" in gm,
    "Le durcissement AAL2 a supprimé les gardes MFA historiques additionnelles.")
req("deletefrompublic.guardian_signup_inviteswhereguardian_user_id=uidandused_atisnull" in gm,
    "Un nouveau code AAL2 n'invalide plus les anciens codes ouverts.")
req("revokeallonfunctionpublic.create_guardian_signup_invite()frompublic,anon" in gm
    and "grantexecuteonfunctionpublic.create_guardian_signup_invite()toauthenticated" in gm,
    "Les ACL de création du code parental AAL2 ne sont pas bornées.")
req("createorreplacefunctionprivate.sinjira_strip_guardian_signup_secret()" in gsm,
    "La fonction de minimisation du secret parental est absente.")
req("createtriggerzz_sinjira_strip_guardian_signup_secretafterinsertonauth.users" in gsm,
    "Le nettoyage du guardian_code n'est pas garanti après le trigger de création utilisateur.")
req("raw_user_meta_data=coalesce(raw_user_meta_data,'{}'::jsonb)-'guardian_code'" in gsm,
    "La migration de minimisation ne retire pas réellement guardian_code des métadonnées Auth.")
req("revokeallonfunctionprivate.sinjira_strip_guardian_signup_secret()frompublic,anon,authenticated" in gsm,
    "La fonction privée de minimisation du secret parental est exposée aux rôles API.")
req("createpolicyguardian_signup_invites_own_aal2" in grm
    and "coalesce(auth.jwt()->>'aal','aal1')='aal2'" in grm
    and "(selectauth.uid())=guardian_user_id" in grm,
    "La lecture des codes parentaux n'est pas bornée self-only + AAL2 par RLS.")
req("droppolicyifexistsguardian_signup_invites_ownonpublic.guardian_signup_invites" in grm,
    "L'ancienne policy AAL1 de lecture des codes parentaux n'est pas retirée.")
req("createorreplacefunctionpublic.revoke_guardian_link(p_link_iduuid)" in grv,
    "Le RPC de révocation tuteur V25 est absent.")
req("ifuid=r.guardian_user_idandcoalesce(auth.jwt()->>'aal','aal1')<>'aal2'" in grv
    and "mfa_aal2_required" in grv,
    "La révocation initiée par le tuteur n'exige pas AAL2.")
req("uidnotin(r.guardian_user_id,r.minor_user_id)" in grv,
    "Le RPC de révocation ne borne plus l'action aux deux parties du lien.")
req("ifuid=r.guardian_user_id" in grv and "uid=r.minor_user_id" not in grv,
    "Le contrat ne préserve pas clairement la sortie immédiate du mineur.")
req("r.status='revoked'orr.revoked_atisnotnull" in grv,
    "La révocation n'est pas idempotente sur status/revoked_at.")
req("createorreplacefunctionpublic.sinjira_can_read_guardian_link(p_link_iduuid)" in gav,
    "Le helper de visibilité de majorité guardian_links est absent.")
req("whenauth.uid()=g.minor_user_idthentrue" in gav,
    "La personne concernée ne conserve pas l'accès à son propre historique de supervision.")
req("whenauth.uid()=g.guardian_user_idthenpublic.sinjira_age_band(g.minor_user_id)in('child','child_pending','youth','youth_pending')" in gav,
    "La visibilité de l'ancien tuteur n'est pas bornée aux comptes sous 18 ans.")
req("createpolicyguardian_read_parties_age_bounded" in gav
    and "using(public.sinjira_can_read_guardian_link(id))" in gav,
    "La RLS guardian_links n'utilise pas le garde de majorité self-only.")
req("droppolicyifexistsguardian_read_partiesonpublic.guardian_links" in gav,
    "L'ancienne policy guardian_links sans borne d'âge n'est pas supprimée.")

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
req('guardian_code:guardiancode' in j,
    "Le contrôleur actif ne transmet pas le code parental dans les métadonnées Auth.")
req('date_of_birth:birthdate' in j and "account_age_band:child?'child_11_12'" in j,
    "Le payload Auth enfant n'est pas aligné sur la date et la bande V25.")

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
req("s.auth.mfa.getauthenticatorassurancelevel()" in r
    and "aal?.currentlevel!=='aal2'" in r
    and "aal?.nextlevel==='aal2'" in r,
    "Le parcours parent ne vérifie pas le niveau AAL avant d'émettre un code.")
req("/compte/mfa.html?next=" in r and "encodeuricomponent('/compte/relations.html')" in r,
    "Le parcours parent ne redirige plus vers la vérification MFA avec retour à Relations.")
req("mfa_aal2_required|mfa_required" in r,
    "L'interface parent ne traite plus explicitement un refus MFA serveur.")
req("codesparentauxmasqués" in r and "unesessionaal2estrequisepourrelireuncodeparental" in r,
    "L'interface n'explique plus que la relecture d'un code exige AAL2.")
req("data-revoke-as-guardian" in r and "constasguardian=button.dataset.revokeasguardian==='true'" in r,
    "L'interface ne distingue plus révocation tuteur et sortie du mineur.")
req("révoquerunliencommetuteurexigeunsecondfacteur" in r and "mfa_aal2_required" in r,
    "L'interface ne protège plus la révocation initiée par le tuteur.")
req("vousavezquittécelien" in r,
    "L'interface ne préserve plus le parcours de sortie immédiate du mineur.")
req("constactive=x.status==='verified'&&!x.revoked_at" in r,
    "L'interface pourrait encore afficher un lien revoked_at comme actif.")
req(
    r.find("s.auth.mfa.getauthenticatorassurancelevel()") >= 0
    and r.find("s.from('guardian_signup_invites')") > r.find("s.auth.mfa.getauthenticatorassurancelevel()"),
    "Le navigateur pourrait lire guardian_signup_invites avant de vérifier AAL2."
)
req('data-create-guardian-code' in rh and 'de 11 à 13 ans' in rh,
    "La page Relations n'explique pas le code parental obligatoire de 11 à 13 ans.")
req('ouvrir l’inscription' in rh and 'v24-relations.js?v=25.0.6&amp;rev=guardian-revoke-aal2' in rh,
    "Le parcours parent vers l'inscription ou son invalidation de cache est incomplet.")
req('session aal2 avec second facteur' in rh and 'securite.html#mfa-active-title' in rh,
    "La page Relations n'explique pas la vérification AAL2 ni le chemin de configuration MFA.")

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
req('__sinjira_test_signup_payload' in cbt and 'signup_payload=page.evaluate' in cbt,
    "La preuve navigateur dédiée n'intercepte plus le payload Auth réel.")
req('metadata.get("guardian_code")=="youth-abcd123456"' in cbt,
    "La preuve navigateur ne vérifie plus la transmission normalisée du code parental.")
req('metadata.get("account_age_band")=="child_11_12"' in cbt,
    "La preuve navigateur ne vérifie plus la bande child_11_12 envoyée à Auth.")
req('metadata.get("initial_contributor_opt_in")isfalse' in cbt
    and 'metadata.get("initial_share_free_text")isfalse' in cbt,
    "La preuve navigateur ne vérifie plus la neutralisation des contributions dans le payload.")

# Le pgTAP crée un vrai parent, un code et un enfant de 11 ans, puis vérifie aussi
# la transition automatique child -> youth à la frontière exacte du 13e anniversaire.
req('selectplan(45);' in t,
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
    ("revoked_atseulsuffitàretirerlasupervisionparentale", "Le test ne prouve pas le fail-closed sur revoked_at pour la supervision."),
    ("unenfantde11anssanslientuteuractifdevientchild_pending", "Le test ne prouve pas le passage 11–12 vers child_pending après révocation."),
    ("child_pendingpeutconsommerunnouveaucodeparentalvalide", "Le test ne prouve pas le rétablissement de supervision depuis child_pending."),
    ("laconsommationdunouveaucoderétablitimmédiatementlabandechild", "Le test ne prouve pas le retour immédiat à child."),
    ("lelientuteurrévoquéestréactivéproprementenverifiednonrévoqué", "Le test ne prouve pas la réactivation propre du lien tuteur."),
    ("lenouveaucodeestconsomméuneseulefoisparlecomptechild_pending", "Le test ne prouve pas la consommation unique du code de rétablissement."),
    ("mfa_aal2_required", "Le pgTAP ne prouve pas le refus AAL1 de création du code parental."),
    ("unesessionadulteaal2peutcréeruncodeparental", "Le pgTAP ne prouve pas la réussite de création sous AAL2."),
    ("request.jwt.claims", "Le pgTAP ne simule pas explicitement les niveaux AAL du JWT."),
    ("invite_code~'^youth-[a-z0-9]{10}$'", "Le pgTAP ne vérifie pas le format du code généré sous AAL2."),
    ("lecodeparentalconsomméestsupprimédesmétadonnéesauthdelenfant", "Le pgTAP ne prouve pas la suppression de guardian_code après consommation."),
    ("unesessiontuteuraal1nepeutpasrelireuncodeparental", "Le pgTAP ne prouve pas le masquage RLS des codes sous AAL1."),
    ("unesessiontuteuraal2peutreliresonproprecodeparental", "Le pgTAP ne prouve pas la relecture self-only sous AAL2."),
    ("setlocalroleauthenticated", "Le pgTAP ne teste pas la policy avec le rôle API authenticated."),
    ("untuteuraal1nepeutpasrévoquerleliendesupervision", "Le pgTAP ne prouve pas le refus de révocation tuteur en AAL1."),
    ("untuteuraal2peutrévoquerleliendesupervision", "Le pgTAP ne prouve pas la révocation tuteur en AAL2."),
    ("lenfantaal1peutquitterimmédiatementsonpropreliendesupervision", "Le pgTAP ne préserve pas la sortie fail-safe de l enfant."),
    ("quittersonlienremetimmédiatementlecompte11ansenchild_pending", "Le pgTAP ne prouve pas l'effet fail-closed de la sortie enfant."),
    ("lejourdes18anslecomptedevientadult", "Le pgTAP ne prouve pas la transition automatique vers adult à 18 ans."),
    ("à18anslancientuteurnepeutpluslireleliendesupervision", "Le pgTAP ne prouve pas la fin de visibilité tuteur à la majorité."),
    ("lapersonnedevenueadulteconservelaccèsàsonproprehistoriquedesupervision", "Le pgTAP ne préserve pas l'accès self-only de l'adulte à son historique."),
    ("untiersnepeutpasutiliserlehelperpoursonderunlienquineleconcernepas", "Le pgTAP ne prouve pas la fermeture du helper à un tiers."),
    ("$$,'p0001','youth_jurisdiction_not_enabled'", "Le délimiteur pgTAP du refus hors Canada est cassé."),
    ("$$selectpublic.redeem_guardian_signup_invite('youth-redeem1101')$$", "Le délimiteur pgTAP du rétablissement child_pending est cassé."),
):
    req(marker in t, message)

if errors:
    print(f'ECHEC compte enfant supervisé V25: {len(errors)} problème(s).')
    for error in errors:
        print('- ' + error)
    raise SystemExit(1)

print('OK V25: compte enfant 11 ans, parcours parent, séparation de session, minimisation, régression navigateur et transition automatique child -> youth à 13 ans sont verrouillés par le contrat et les tests.')
