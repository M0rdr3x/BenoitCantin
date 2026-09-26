#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase/migrations/20260916210000_sinjira_v25_child_guardian_signup.sql'
TEST = ROOT / 'supabase/tests/child_guardian_signup_v25.test.sql'
PRIVATE_PROFILE_CHILD_TEST = ROOT / 'supabase/tests/private_profile_child_age_v25.test.sql'
REDEEM_MIG = ROOT / 'supabase/migrations/20260919013000_sinjira_v25_child_pending_guardian_redeem.sql'
GUARDIAN_AAL2_MIG = ROOT / 'supabase/migrations/20260919023000_sinjira_v25_guardian_invite_aal2.sql'
GUARDIAN_SECRET_MIN_MIG = ROOT / 'supabase/migrations/20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql'
GUARDIAN_READ_AAL2_MIG = ROOT / 'supabase/migrations/20260919033000_sinjira_v25_guardian_invite_read_aal2.sql'
GUARDIAN_REVOKE_AAL2_MIG = ROOT / 'supabase/migrations/20260919043000_sinjira_v25_guardian_revoke_aal2.sql'
GUARDIAN_ADULT_VIS_MIG = ROOT / 'supabase/migrations/20260919050000_sinjira_v25_guardian_majority_visibility.sql'
GUARDIAN_INVITE_ADULT_VIS_MIG = ROOT / 'supabase/migrations/20260919053000_sinjira_v25_guardian_invite_majority_visibility.sql'
GUARDIAN_CONTACTS_AAL2_MIG = ROOT / 'supabase/migrations/20260919060000_sinjira_v25_guardian_contacts_consent_aal2.sql'
GUARDIAN_CONTACT_CONSENT_MIG = ROOT / 'supabase/migrations/20260919063000_sinjira_v25_guardian_contact_metadata_opt_in.sql'
GUARDIAN_CONTACT_MIN_MIG = ROOT / 'supabase/migrations/20260919070000_sinjira_v25_guardian_contacts_minimization.sql'
GUARDIAN_CHARACTER_ISOLATION_MIG = ROOT / 'supabase/migrations/20260919080000_sinjira_v25_guardian_character_identity_isolation.sql'
SOCIAL_PSEUDO_PRIVACY_MIG = ROOT / 'supabase/migrations/20260919110000_sinjira_v25_social_public_pseudo_privacy.sql'
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
private_profile_child_test = read(PRIVATE_PROFILE_CHILD_TEST)
redeem_mig = read(REDEEM_MIG)
guardian_aal2_mig = read(GUARDIAN_AAL2_MIG)
guardian_secret_min_mig = read(GUARDIAN_SECRET_MIN_MIG)
guardian_read_aal2_mig = read(GUARDIAN_READ_AAL2_MIG)
guardian_revoke_aal2_mig = read(GUARDIAN_REVOKE_AAL2_MIG)
guardian_adult_vis_mig = read(GUARDIAN_ADULT_VIS_MIG)
guardian_invite_adult_vis_mig = read(GUARDIAN_INVITE_ADULT_VIS_MIG)
guardian_contacts_aal2_mig = read(GUARDIAN_CONTACTS_AAL2_MIG)
guardian_contact_consent_mig = read(GUARDIAN_CONTACT_CONSENT_MIG)
guardian_contact_min_mig = read(GUARDIAN_CONTACT_MIN_MIG)
guardian_character_isolation_mig = read(GUARDIAN_CHARACTER_ISOLATION_MIG)
social_pseudo_privacy_mig = read(SOCIAL_PSEUDO_PRIVACY_MIG)
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
ppct = compact(private_profile_child_test)
rm = compact(redeem_mig)
gm = compact(guardian_aal2_mig)
gsm = compact(guardian_secret_min_mig)
grm = compact(guardian_read_aal2_mig)
grv = compact(guardian_revoke_aal2_mig)
gav = compact(guardian_adult_vis_mig)
giav = compact(guardian_invite_adult_vis_mig)
gca = compact(guardian_contacts_aal2_mig)
gcc = compact(guardian_contact_consent_mig)
gcm = compact(guardian_contact_min_mig)
gci = compact(guardian_character_isolation_mig)
spp = compact(social_pseudo_privacy_mig)
y = compact(youth_base)
j = compact(signup_js)
b = compact(backend_js)
r = compact(relations_js)
h = signup_html.lower()
rh = relations_html.lower()
bt = compact(browser_test)
cbt = compact(child_browser_test)

# Le workflow exécute aussi le coffre privé enfant : sa preuve SQL doit rester syntaxiquement ciblée.
req("$age_review$selectpublic.private_profile_save(" in ppct
    and ")$age_review$," in ppct,
    "Le pgTAP du coffre privé enfant ne protège plus correctement le scénario de revue de date de naissance.")

# Autorité serveur et seuil minimal.
req("ifyears<11thenraiseexception'sinjira_minimum_age_11'" in m,
    "La migration V25 n'impose pas le minimum serveur de 11 ans.")
for marker,message in (
    ("createorreplacefunctionpublic.enforce_sinjira_account_safety_age()returnstriggerlanguageplpgsqlsecuritydefinersetsearch_path=pg_catalog,public","search_path du garde âge"),
    ("createorreplacefunctionpublic.sinjira_age_band(p_user_iduuiddefaultauth.uid())returnstextlanguagesqlstablesecuritydefinersetsearch_path=pg_catalog,public,auth","search_path de la classification âge"),
    ("createorreplacefunctionpublic.sinjira_parent_can_supervise(p_parentuuid,p_childuuid)returnsbooleanlanguagesqlstablesecuritydefinersetsearch_path=pg_catalog,public","search_path supervision parentale"),
    ("createorreplacefunctionpublic.handle_new_sinjira_user()returnstriggerlanguageplpgsqlsecuritydefinersetsearch_path=pg_catalog,public,auth","search_path du hook Auth"),
):
    req(marker in m,f"La migration d'introduction enfant ne borne pas {message}.")

age_band_start=m.find("createorreplacefunctionpublic.sinjira_age_band")
age_band_end=m.find("revokeallonfunctionpublic.sinjira_age_band(uuid)",age_band_start)
req(age_band_start>=0 and age_band_end>age_band_start,
    "La définition de sinjira_age_band ne peut pas être isolée pour la revue.")
age_band_section=m[age_band_start:age_band_end]
req("frompublic.internal_admin_usersa" in age_band_section
    and "a.user_id=p_user_id" in age_band_section
    and "a.role='owner'" in age_band_section,
    "Le créateur n'est pas résolu par l'autorité serveur owner dans la classification d'âge.")
req("@gmail.com" not in age_band_section and "@outlook.com" not in age_band_section,
    "La classification d'âge ne doit contenir aucune adresse personnelle gravée dans le SQL.")
req("createorreplacefunctionpublic.enforce_sinjira_single_admin()" in m
    and "wherea.user_idisdistinctfromnew.user_id" in m
    and "sinjira_single_admin_account_only" in m
    and "createtriggerenforce_sinjira_single_admin_trigger" in m,
    "Le verrou owner/admin n'est pas convergé vers un invariant structurel sans identité personnelle.")
owner_guard_start=m.find("createorreplacefunctionpublic.enforce_sinjira_single_admin()")
owner_guard_end=m.find("commentonfunctionpublic.enforce_sinjira_single_admin()",owner_guard_start)
req(owner_guard_start>=0 and owner_guard_end>owner_guard_start
    and "@gmail.com" not in m[owner_guard_start:owner_guard_end]
    and "@outlook.com" not in m[owner_guard_start:owner_guard_end],
    "Le verrou owner/admin conserve une adresse personnelle.")

req("ifyears<14then" in m and 'guardian_authorization_required_under_14' in m,
    "L'autorisation parentale obligatoire de 11 à 13 ans n'est pas imposée côté serveur.")
req("years<18andresidence_countrynotin('canada','ca','can')" in m and 'youth_jurisdiction_not_enabled' in m,
    "La porte de juridiction jeunesse Canada n'est pas conservée côté serveur.")
req("ifinv.idisnotnullandyears<18then" in m and "'verified','parent'" in m,
    "Le lien parent/enfant vérifié n'est pas créé après validation du code.")
req("'verified','parent',false,inv.consented_at" in m,
    "Le lien parent/enfant initial n'est pas privacy-by-default pour les métadonnées de contacts.")
req("createorreplacefunctionpublic.sync_guardian_signup_invite_link()" in m
    and "can_view_contact_metadata,consented_at,revoked_at" in m
    and "false,new.consented_at,null" in m
    and "can_view_contact_metadata=false" in m,
    "Le trigger historique de synchronisation d invitation peut encore réactiver les métadonnées parentales.")
req("setsearch_path=pg_catalog,public" in m,
    "Le trigger SECURITY DEFINER de synchronisation parentale n'a pas un search_path borné.")

# Aucun intervalle moins sûr entre l'ouverture 11 ans et les migrations de convergence ultérieures.
req("createorreplacefunctionpublic.create_guardian_signup_invite()" in m
    and "coalesce(auth.jwt()->>'aal','aal1')<>'aal2'" in m
    and "mfa_aal2_required" in m
    and "notpublic.sinjira_mfa_access_allowed(uid)" in m,
    "La migration d'introduction enfant n'exige pas AAL2 + garde MFA historique pour émettre un code parental.")
req("createpolicyguardian_signup_invites_own_aal2" in m
    and "(selectauth.uid())=guardian_user_id" in m
    and "coalesce(auth.jwt()->>'aal','aal1')='aal2'" in m,
    "La migration d'introduction enfant permet encore de relire un code parental hors AAL2.")
req("createorreplacefunctionpublic.sinjira_can_read_guardian_link(p_link_iduuid)" in m
    and "whenauth.uid()=g.minor_user_idthentrue" in m
    and "whenauth.uid()=g.guardian_user_idthenpublic.sinjira_age_band(g.minor_user_id)in('child','child_pending','youth','youth_pending')" in m
    and "createpolicyguardian_read_parties_age_bounded" in m,
    "La migration d'introduction enfant conserve encore la visibilité tuteur après majorité.")
req("minor_user_idisnullorexists(select1frompublic.guardian_linksg" in m
    and "g.guardian_user_id=(selectauth.uid())" in m
    and "g.minor_user_id=guardian_signup_invites.minor_user_id" in m,
    "La migration d'introduction enfant conserve encore une invitation consommée visible après majorité.")
req("createorreplacefunctionpublic.revoke_guardian_link(p_link_iduuid)" in m
    and "uidnotin(r.guardian_user_id,r.minor_user_id)" in m
    and "ifuid=r.guardian_user_idandcoalesce(auth.jwt()->>'aal','aal1')<>'aal2'" in m
    and "uid=r.minor_user_id" not in m,
    "La migration d'introduction enfant ne préserve pas révocation tuteur AAL2 + sortie mineur immédiate.")
req("altercolumncan_view_contact_metadatasetdefaultfalse" in m
    and "createtriggerguardian_contact_metadata_default_off" in m
    and "updatepublic.guardian_linkssetcan_view_contact_metadata=false" in m,
    "La migration d'introduction enfant n'impose pas privacy-by-default sur tous les guardian_links actifs.")
req("createorreplacefunctionpublic.get_guardian_youth_contacts(p_child_user_iduuid)" in m
    and "guardian_contact_metadata_not_allowed" in m
    and "mfa_aal2_required" in m
    and "'contact_label'" in m
    and "'last_contact_date'" in m
    and "'display_name'" not in m[m.find("createorreplacefunctionpublic.get_guardian_youth_contacts"):m.find("commentonfunctionpublic.get_guardian_youth_contacts")],
    "La migration d'introduction enfant laisse le RPC historique de contacts exposer trop de métadonnées avant B5.")
req("createorreplacefunctionprivate.sinjira_strip_guardian_signup_secret()" in m
    and "createtriggerzz_sinjira_strip_guardian_signup_secret" in m
    and "raw_user_meta_data=coalesce(raw_user_meta_data,'{}'::jsonb)-'guardian_code'" in m,
    "La migration d'introduction enfant conserve encore guardian_code dans les métadonnées Auth.")
req("updateauth.userssetraw_user_meta_data=coalesce(raw_user_meta_data,'{}'::jsonb)-'guardian_code'" in m,
    "La migration d'introduction enfant ne purge pas les guardian_code historiques résiduels.")
req("createorreplacefunctionprivate.sinjira_child_sensitive_write_guard()" in m
    and "child_action_not_available_11_12" in m
    and "account_action_not_available_restricted" in m,
    "La migration d'introduction enfant n'installe pas la frontière de mutations sensibles avant le premier compte 11–12.")
req("createorreplacefunctionprivate.sinjira_child_research_consent_guard()" in m
    and "new.participate:=false" in m
    and "new.share_free_text:=false" in m,
    "La migration d'introduction enfant ne force pas les consentements recherche à OFF côté base.")
req("createpolicyplaytests_read_authorized" in m
    and "createpolicyplaytest_participants_read_authorized" in m
    and "public.sinjira_my_age_band()in('adult','youth')" in m,
    "La migration d'introduction enfant n'exclut pas immédiatement child des playtests.")
pre_rating_read_gate="(selectauth.uid())isnullorpublic.sinjira_my_age_band()in('adult','youth')"
req(m.count(pre_rating_read_gate)>=2,
    "La migration d'introduction enfant expose encore à child du contenu projet/document non classé avant approved_11_12.")

projects_gate_pos=m.find('createpolicy"projectsreadablewhenaccessible"')
documents_gate_pos=m.find('createpolicy"approveddocumentsvisiblebyaccess"')
for marker in (
    'droppolicyifexistsadmin_read_all_projectsonpublic.projects',
    'droppolicyifexistsprojects_readonpublic.projects',
    'droppolicyifexistsprojects_public_readonpublic.projects',
    'droppolicyifexistsprojects_authenticated_readonpublic.projects',
):
    req(0 <= m.find(marker) < projects_gate_pos,
        f"La migration d'introduction enfant laisse une ancienne policy projets permissive active avant le garde child: {marker}")
for marker in (
    'droppolicyifexistsdocuments_read_by_accessonpublic.documents',
    'droppolicyifexistsadmin_read_all_documentsonpublic.documents',
    'droppolicyifexistsdocuments_anon_readonpublic.documents',
    'droppolicyifexistsdocuments_authenticated_readonpublic.documents',
):
    req(0 <= m.find(marker) < documents_gate_pos,
        f"La migration d'introduction enfant laisse une ancienne policy documents permissive active avant le garde child: {marker}")
req('createpolicy"requestsowninsert"' in m
    and "status='pending'" in m,
    "La migration d'introduction enfant ne borne pas access_requests à self + adulte/youth + pending.")
req('createpolicy"participantsownapply"' in m
    and "status='applied'" in m,
    "La migration d'introduction enfant ne borne pas playtest_participants à self + adulte/youth + applied.")
req("createorreplacefunctionprivate.sinjira_content_policy_code(" in m
    and "v_youthboolean:=coalesce(v_actor_bandnotin('adult','memorial'),true)" in m
    and "coalesce(v_recipient_bandnotin('adult','memorial'),true)" in m,
    "La migration d'introduction enfant n'active pas le classifieur de contenu fail-closed pour child/pending/inconnu.")
req("minor_off_platform_contact" in m
    and "minor_sexual_solicitation" in m
    and "minor_financial_solicitation" in m,
    "La migration d'introduction enfant ne conserve pas les refus de sollicitations mineur côté serveur.")
req("createorreplacefunctionpublic.sync_social_profile_from_profile()" in m
    and "v_public_pseudotext:=coalesce(nullif(btrim(new.pseudo),''),'membresinjira')" in m
    and "values(new.user_id,v_public_pseudo,v_public_pseudo,new.avatar_path,now())" in m,
    "La migration d'introduction enfant peut encore copier le display_name privé vers le profil social.")
req("updatepublic.social_profilessp" in m
    and "display_name=l.public_pseudo" in m,
    "La migration d'introduction enfant ne neutralise pas immédiatement les profils sociaux historiques.")
req("bandnotin('child_pending','youth_pending','youth')" in rm,
    "Le RPC de rétablissement ne reconnaît pas child_pending.")
req("perform1frompublic.account_safety_profilesswheres.user_id=uidforupdate" in rm,
    "Le RPC de rétablissement ne sérialise pas les consommations concurrentes pour un même compte.")
req("g.status='verified'andg.revoked_atisnull" in rm,
    "Le RPC de rétablissement ne distingue pas un lien réellement actif d'un lien révoqué.")
req("updatepublic.guardian_signup_invitessetused_at=now(),minor_user_id=uid" in rm,
    "Le RPC de rétablissement ne consomme pas atomiquement le code parental.")
req("revokeallonfunctionpublic.redeem_guardian_signup_invite(text)frompublic,anon" in rm
    and "grantexecuteonfunctionpublic.redeem_guardian_signup_invite(text)toauthenticated" in rm,
    "Les ACL du RPC de rétablissement parental ne sont pas bornées.")
req("v_code!~'^youth-[a-z0-9]{10}([a-z0-9]{6})?$'" in rm,
    "Le RPC de rétablissement n'accepte pas exactement les formats parentaux historiques 10 et renforcés 16 caractères.")
req("coalesce(auth.jwt()->>'aal','aal1')<>'aal2'" in gm and "mfa_aal2_required" in gm,
    "La création d'un code parental n'exige pas explicitement AAL2 côté serveur.")
req("notpublic.sinjira_mfa_access_allowed(uid)" in gm and "mfa_required" in gm,
    "Le durcissement AAL2 a supprimé les gardes MFA historiques additionnelles.")
req("deletefrompublic.guardian_signup_inviteswhereguardian_user_id=uidandused_atisnull" in gm,
    "Un nouveau code AAL2 n'invalide plus les anciens codes ouverts.")
req("dropconstraintifexistsguardian_signup_invites_code_format_check" in gm
    and "check(invite_code~'^youth-[a-z0-9]{10}([a-z0-9]{6})?$')" in gm,
    "La migration AAL2 ne conserve pas la compatibilité 10 caractères tout en autorisant le nouveau format 16.")
req("v_uuid_hex:=replace(gen_random_uuid()::text,'-','')" in gm
    and "substr(v_uuid_hex,1,12)" in gm
    and "substr(v_uuid_hex,14,3)" in gm
    and "substr(v_uuid_hex,18,1)" in gm,
    "Les nouveaux codes parentaux ne disposent pas encore de 16 nibbles aléatoires hors métadonnées UUID v4.")
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
req("minor_user_idisnullorexists(select1frompublic.guardian_linksg" in grm
    and "g.guardian_user_id=(selectauth.uid())" in grm
    and "g.minor_user_id=guardian_signup_invites.minor_user_id" in grm,
    "La migration AAL2 de lecture réouvre transitoirement les invitations consommées après majorité.")
req("droppolicyifexistsguardian_signup_invites_ownonpublic.guardian_signup_invites" in grm,
    "L'ancienne policy AAL1 de lecture des codes parentaux n'est pas retirée.")
req("createorreplacefunctionpublic.revoke_guardian_link(p_link_iduuid)" in grv,
    "Le RPC de révocation tuteur V25 est absent.")
req("ifuid=r.guardian_user_idandcoalesce(auth.jwt()->>'aal','aal1')<>'aal2'" in grv
    and "mfa_aal2_required" in grv,
    "La révocation initiée par le tuteur n'exige pas AAL2.")
req("whereid=p_link_idanduidin(guardian_user_id,minor_user_id)forupdate" in grv,
    "Le RPC de révocation doit autoriser la partie concernée avant tout verrou FOR UPDATE.")
req("ifr.idisnullthenraiseexception'guardian_link_unavailable'" in grv
    and "guardian_link_not_found" not in grv
    and "guardian_link_forbidden" not in grv,
    "La révocation réintroduit un oracle d'existence entre lien absent et lien tiers.")
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
req("createpolicyguardian_signup_invites_own_aal2" in giav
    and "coalesce(auth.jwt()->>'aal','aal1')='aal2'" in giav,
    "La policy des invitations parentales ne conserve pas la borne AAL2.")
req("minor_user_idisnullorexists(select1frompublic.guardian_linksg" in giav
    and "g.guardian_user_id=(selectauth.uid())" in giav
    and "g.minor_user_id=guardian_signup_invites.minor_user_id" in giav,
    "Les invitations consommées ne sont pas bornées par la visibilité du guardian_link.")
req("createorreplacefunctionpublic.get_guardian_youth_contacts(p_child_user_iduuid)" in gca,
    "Le RPC de métadonnées de contacts jeunesse V25 est absent.")
req("notpublic.sinjira_parent_can_supervise(uid,p_child_user_id)" in gca,
    "Le RPC contacts jeunesse ne vérifie plus la supervision active.")
req("g.can_view_contact_metadataistrue" in gca
    and "guardian_contact_metadata_not_allowed" in gca,
    "Le RPC contacts jeunesse n'exige pas le consentement can_view_contact_metadata=true.")
req("coalesce(auth.jwt()->>'aal','aal1')<>'aal2'" in gca
    and "mfa_aal2_required" in gca,
    "Le RPC contacts jeunesse n'exige pas AAL2.")
req("setsearch_path=pg_catalog,public,auth" in gca,
    "Le RPC contacts jeunesse n'a pas un search_path borné.")
req("revokeallonfunctionpublic.get_guardian_youth_contacts(uuid)frompublic,anon" in gca
    and "grantexecuteonfunctionpublic.get_guardian_youth_contacts(uuid)toauthenticated" in gca,
    "Les ACL du RPC contacts jeunesse ne sont pas bornées.")
req("altercolumncan_view_contact_metadatasetdefaultfalse" in gcc,
    "guardian_links ne désactive pas les métadonnées de contacts par défaut.")
req("createtriggerguardian_contact_metadata_default_offbeforeinsertorupdateofstatus,revoked_at" in gcc,
    "La création/réactivation d'un guardian_link ne remet pas la permission à false.")
req("updatepublic.guardian_linkssetcan_view_contact_metadata=false" in gcc,
    "Les permissions historiques implicites ne sont pas neutralisées.")
req("createorreplacefunctionpublic.set_my_guardian_contact_metadata(p_link_iduuid,p_allowedboolean)" in gcc,
    "Le RPC self-only de consentement aux métadonnées est absent.")
req("minor_user_id=uid" in gcc and "status='verified'" in gcc and "revoked_atisnull" in gcc,
    "Le RPC de consentement n'est pas borné au propre lien actif du compte jeunesse.")
req("bandnotin('child','youth')" in gcc,
    "Le RPC de consentement n'est pas limité aux comptes child/youth.")
req("revokeallonfunctionpublic.set_my_guardian_contact_metadata(uuid,boolean)frompublic,anon" in gcc
    and "grantexecuteonfunctionpublic.set_my_guardian_contact_metadata(uuid,boolean)toauthenticated" in gcc,
    "Les ACL du RPC de consentement contacts ne sont pas bornées.")
req("createorreplacefunctionpublic.get_guardian_youth_contacts(p_child_user_iduuid)" in gcm,
    "La migration de minimisation des contacts jeunesse est absente.")
for stage,label in (
    (gca,"première exposition 190600"),
    (gcm,"convergence 190700"),
    (gci,"isolation 190800"),
):
    req("leftjoinpublic.character_social_profilescsp" in stage
        and "recipient_character_id" in stage
        and "sender_character_id" in stage,
        f"Le résumé parental {label} ne cloisonne pas l'identité Personnage par character_id.")
    req("'contact_label',g.contact_label" in stage
        and "'network',g.network" in stage
        and "'last_contact_date',(timezone('utc',g.last_contact_at))::date" in stage,
        f"Le résumé parental {label} ne conserve pas exactement label/réseau/date.")
    req("'user_id'," not in stage
        and "'display_name'," not in stage
        and "'last_contact_at'," not in stage
        and "'networks'," not in stage,
        f"Le résumé parental {label} réintroduit UUID, display_name, timestamp précis ou agrégation de réseaux.")
    req("'pseudo'," not in stage,
        f"Le résumé parental {label} réintroduit une clé pseudo susceptible de recoller Compte et Personnage.")
req("createorreplacefunctionpublic.sync_social_profile_from_profile()" in spp
    and "v_public_pseudo" in spp
    and "coalesce(nullif(btrim(new.pseudo),''),'membresinjira')" in spp,
    "La synchronisation sociale V25 ne dérive pas du pseudonyme public.")
req("updatepublic.social_profilessp" in spp
    and "display_name=l.public_pseudo" in spp
    and "values(new.user_id,v_public_pseudo,v_public_pseudo,new.avatar_path,now())" in spp,
    "La synchronisation sociale V25 ne neutralise pas le nom affiché privé.")
req("nomaffichéprivé" in t
    and "sp.pseudo='contactjeunesse'" in t
    and "sp.display_name='contactjeunesse'" in t,
    "Le pgTAP enfant ne prouve pas le nettoyage du nom affiché privé.")
req("'pseudo',coalesce(sp.pseudo" not in gci
    and "'networks',g.networks" not in gci
    and "'user_id'" not in gci
    and "'display_name'" not in gci,
    "Le résumé cloisonné réexpose une ancienne forme corrélable.")
req("data-contact-metadata-toggle" in r
    and "set_my_guardian_contact_metadata" in r
    and "lecontenudevosmessagesresteprivé" in r,
    "L'interface Relations n'expose pas le contrôle self-only des métadonnées de contacts.")

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
req("constneutral=['child','youth'].includes(ageband)" in r and "guardianneutraltools.hidden=!neutral" in r,
    "L'interface Relations affiche encore un état neutre lorsque la bande du compte n'est pas confirmée.")
req("constinitialageready=awaitrefreshageband()" in r and "lesoutilsparentauxrestentmasquésparsécurité" in r,
    "Le chargement initial Relations ne reste pas fail-closed si les capacités sont indisponibles.")
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
req('ouvrir l’inscription' in rh and 'v24-relations.js?v=25.' in rh and '&amp;rev=' in rh,
    "Le parcours parent vers l'inscription ou son invalidation de cache est incomplet.")
req('v24-relations.js?v=25.0.15&amp;rev=guardian-code-16' in rh,
    "La version Relations V25.0.15 n'est pas forcée après le renforcement du code parental.")
req("constcode_re=/^youth-[a-z0-9]{10}(?:[a-z0-9]{6})?$/" in r,
    "Relations n'accepte pas les anciens codes 10 caractères et les nouveaux codes 16 caractères.")
req('maxlength="22"' in rh and 'pattern="youth-[a-za-z0-9]{10}([a-za-z0-9]{6})?"' in rh,
    "Le champ Relations n'est pas dimensionné pour le nouveau code parental 16 caractères.")
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
req('v24-signup.js?v=25.0.3&amp;rev=guardian-code-16' in h,
    "La version du client d'inscription enfant n'est pas invalidée après le renforcement du code parental.")
req("constguardian_code_re=/^youth-[a-z0-9]{10}(?:[a-z0-9]{6})?$/" in j,
    "L'inscription n'accepte pas les anciens codes 10 caractères et les nouveaux codes 16 caractères.")
req('<button class="btn btn-primary" disabled type="submit">créer mon compte</button>' in h,
    "Le bouton Créer mon compte n'est pas fail-closed dans le HTML avant la vérification de session.")
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
req('awaitnewpromise(resolve=>settimeout(resolve,500))' in cbt,
    "Le test navigateur ne ralentit pas getSession pour prouver le verrou initial.")
req('submit.is_disabled()' in cbt and 'avantlavérificationdelafrontièredesession' in cbt,
    "Le test navigateur ne vérifie pas le bouton désactivé avant la réponse de session.")
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
req('selectplan(69);' in t,
    "Le plan pgTAP comportemental enfant supervisé et frontière 13 ans est inattendu.")
req(test.count('$revoke$') == 6,
    "Le pgTAP anti-oracle/révocation doit conserver trois blocs SQL nommés et équilibrés.")
req(
    t.find("request.jwt.claim.sub','20000000-0000-4000-8000-000000000011'") >= 0
    and t.find("request.jwt.claim.sub','20000000-0000-4000-8000-000000000011'")
        < t.find("lecontratsocialjeunessepeutsappliquerautomatiquementàpartirde13ans"),
    "Le pgTAP ne fixe pas l identité JWT enfant avant les helpers sociaux self-only."
)
for marker, message in (
    ("insertintoauth.users", "Le test ne crée pas de comptes Auth réels dans la transaction."),
    ("youth-abcd123456", "Le test ne crée pas de code parental déterministe."),
    ("youth-redeem1101", "Le test ne conserve pas une preuve de compatibilité avec un ancien code parental 10 caractères."),
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
    ("lerétablissementparentalsérialiselesconsommationsconcurrentespourunmêmecompte", "Le pgTAP ne prouve pas le verrou transactionnel du rétablissement parental."),
    ("laconsommationdunouveaucoderétablitimmédiatementlabandechild", "Le test ne prouve pas le retour immédiat à child."),
    ("lelientuteurrévoquéestréactivéproprementenverifiednonrévoqué", "Le test ne prouve pas la réactivation propre du lien tuteur."),
    ("lenouveaucodeestconsomméuneseulefoisparlecomptechild_pending", "Le test ne prouve pas la consommation unique du code de rétablissement."),
    ("mfa_aal2_required", "Le pgTAP ne prouve pas le refus AAL1 de création du code parental."),
    ("unesessionadulteaal2peutcréeruncodeparental", "Le pgTAP ne prouve pas la réussite de création sous AAL2."),
    ("request.jwt.claims", "Le pgTAP ne simule pas explicitement les niveaux AAL du JWT."),
    ("invite_code~'^youth-[a-z0-9]{16}$'", "Le pgTAP ne vérifie pas le nouveau format 16 caractères généré sous AAL2."),
    ("lecodeparentalconsomméestsupprimédesmétadonnéesauthdelenfant", "Le pgTAP ne prouve pas la suppression de guardian_code après consommation."),
    ("unesessiontuteuraal1nepeutpasrelireuncodeparental", "Le pgTAP ne prouve pas le masquage RLS des codes sous AAL1."),
    ("unesessiontuteuraal2peutreliresonproprecodeparental", "Le pgTAP ne prouve pas la relecture self-only sous AAL2."),
    ("setlocalroleauthenticated", "Le pgTAP ne teste pas la policy avec le rôle API authenticated."),
    ("uncomptetiersnepeutpasdistinguerunliendesupervisionexistant", "Le pgTAP ne prouve pas l'absence d'oracle sur un lien tiers existant."),
    ("unlieninexistantrenvoielamêmeerreurfail-closedquunlientiers", "Le pgTAP ne prouve pas l'indistinguabilité lien absent / lien tiers."),
    ("untuteuraal1nepeutpasrévoquerleliendesupervision", "Le pgTAP ne prouve pas le refus de révocation tuteur en AAL1."),
    ("untuteuraal2peutrévoquerleliendesupervision", "Le pgTAP ne prouve pas la révocation tuteur en AAL2."),
    ("lenfantaal1peutquitterimmédiatementsonpropreliendesupervision", "Le pgTAP ne préserve pas la sortie fail-safe de l enfant."),
    ("quittersonlienremetimmédiatementlecompte11ansenchild_pending", "Le pgTAP ne prouve pas l'effet fail-closed de la sortie enfant."),
    ("lejourdes18anslecomptedevientadult", "Le pgTAP ne prouve pas la transition automatique vers adult à 18 ans."),
    ("à18anslancientuteurnepeutpluslireleliendesupervision", "Le pgTAP ne prouve pas la fin de visibilité tuteur à la majorité."),
    ("à18anslancientuteurnepeutplusrelirelesinvitationsparentalesconsommées", "Le pgTAP ne prouve pas la fin de visibilité des invitations consommées à la majorité."),
    ("linscriptionnepréactivejamaislapublicationmémoriellepublique", "Le pgTAP ne prouve pas que memorial_public_opt_in reste désactivé par défaut."),
    ("linscriptionnepréactivejamaislessouhaitsanniversairenilesusagesprivésoptionnels", "Le pgTAP ne prouve pas que birthday_greeting_opt_in et les usages privés restent désactivés par défaut."),
    ("letuteurnepeutpaslirelesmétadonnéesdecontactssansconsentementexplicite", "Le pgTAP ne prouve pas le refus sans consentement contacts."),
    ("letuteuraal1nepeutpaslirelesmétadonnéesdecontactsjeunesse", "Le pgTAP ne prouve pas le step-up AAL2 pour les contacts jeunesse."),
    ("letuteuravecconsentementexpliciteetaal2peutlireuniquementlesmétadonnéesdecontactsjeunesse", "Le pgTAP ne prouve pas le parcours contacts autorisé sous consentement + AAL2."),
    ("unnouveauliendesupervisiondésactivelesmétadonnéesdecontacts pardéfaut".replace(" ",""), "Le pgTAP ne prouve pas privacy-by-default pour le nouveau lien."),
    ("lecomptejeunessepeutautoriserexplicitementsesmétadonnéesdecontacts", "Le pgTAP ne prouve pas l'opt-in self-only du compte jeunesse."),
    ("lecomptejeunessepeutretirerimmédiatementlapermissiondemétadonnées", "Le pgTAP ne prouve pas le retrait self-only de permission."),
    ("aprèsretraitletuteuraal2perdimmédiatementlaccèsauxmétadonnéesdecontacts", "Le pgTAP ne prouve pas l'effet immédiat du retrait."),
    ("lerésuméparentalnerévèleniuuid,display_name,ancienpseudobrutnitimestampprécis", "Le pgTAP ne prouve pas la minimisation finale UUID/display_name/timestamp."),
    ("leréseaucompteconserveuniquementlepseudopublicducontact", "Le pgTAP ne prouve pas le label public minimal du réseau Compte."),
    ("ladernièreinteractionpersonnageresteréduiteàunedatesansheureprécise", "Le pgTAP ne prouve pas la réduction temporelle Personnage à la journée."),
    ("leréseaupersonnageexposeuniquementlenompublicdupersonnage", "Le pgTAP ne prouve pas l'identité publique Personnage."),
    ("lerésuménerecollepaslepersonnageaupseudodesoncompteréel", "Le pgTAP ne prouve pas l'absence de recoupement Compte/Personnage."),
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
