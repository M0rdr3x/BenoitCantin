#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT_DIR = ROOT / "compte"

FILES = {
    "migration": ROOT / "supabase/migrations/20260919090000_sinjira_v25_account_content_hub.sql",
    "project_owner_migration": ROOT / "supabase/migrations/20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql",
    "public_rpc_boundary_migration": ROOT / "supabase/migrations/20260919123000_sinjira_v25_public_rpc_boundary.sql",
    "browser_privileges_migration": ROOT / "supabase/migrations/20260919130000_sinjira_v25_account_catalog_browser_privileges.sql",
    "browser_helper_hardening_migration": ROOT / "supabase/migrations/20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql",
    "paid_access_migration": ROOT / "supabase/migrations/20260922023000_sinjira_v25_paid_order_product_access.sql",
    "age_boundary_migration": ROOT / "supabase/migrations/20260922031500_sinjira_v25_catalog_age_helper_boundary.sql",
    "project_product_migration": ROOT / "supabase/migrations/20260922033000_sinjira_v25_project_product_access.sql",
    "library_html": ROOT / "compte/bibliotheque.html",
    "library_js": ROOT / "assets/js/sinjira-library-v24-4-61.js",
    "licenses_html": ROOT / "compte/licences.html",
    "licenses_js": ROOT / "assets/js/v24-licenses.js",
    "secondary_library_js": ROOT / "assets/js/sinjira-library.js",
    "purchases_html": ROOT / "compte/mes-achats.html",
    "purchases_js": ROOT / "assets/js/sinjira-purchases-v25.js",
    "profile_html": ROOT / "compte/profil.html",
    "private_profile_js": ROOT / "assets/js/sinjira-private-profile-v24-5-23.js",
    "account_js": ROOT / "assets/js/sinjira-account.js",
    "data_control_js": ROOT / "assets/js/v24-data-control.js",
    "preferences_js": ROOT / "assets/js/v24-preferences.js",
    "privacy_center_js": ROOT / "assets/js/sinjira-privacy-center-v24-4-83.js",
    "dashboard_js": ROOT / "assets/js/sinjira-account-dashboard-v24-4-60.js",
    "account_css": ROOT / "assets/css/sinjira-player-account.css",
    "recovery_js": ROOT / "assets/js/sinjira-recovery-v24-4-99.js",
    "signup_html": ROOT / "compte/inscription.html",
    "login_html": ROOT / "compte/connexion.html",
    "forgot_html": ROOT / "compte/mot-de-passe-oublie.html",
    "reset_html": ROOT / "compte/reinitialiser-mot-de-passe.html",
    "mfa_html": ROOT / "compte/mfa.html",
    "workflow": ROOT / ".github/workflows/sinjira-account-content-hub-v25.yml",
    "supabase_config": ROOT / "supabase/config.toml",
    "reader_js": ROOT / "assets/js/sinjira-reader.js",
    "comments_js": ROOT / "assets/js/sinjira-account-v18.js",
    "comments_html": ROOT / "compte/mes-commentaires.html",
    "literature_html": ROOT / "projets/sinjira/romans/index.html",
    "demo_html": ROOT / "projets/sinjira/romans/lire-demo.html",
    "literature_js": ROOT / "assets/js/sinjira-literature-catalog-v25.js",
    "test": ROOT / "supabase/tests/account_content_hub_v25.test.sql",
    "child_content_test": ROOT / "supabase/tests/child_content_rating_v25.test.sql",
    "secondary_mes_lectures": ROOT / "compte/mes-lectures.html",
    "secondary_documents": ROOT / "compte/documents.html",
    "secondary_playtests": ROOT / "compte/playtests.html",
    "secondary_contributions": ROOT / "compte/contributions.html",
    "secondary_messages_reels": ROOT / "compte/messages-reels.html",
    "secondary_messages_personnage": ROOT / "compte/messages-personnage.html",
    "secondary_privacy": ROOT / "compte/vie-privee.html",
    "secondary_blocks": ROOT / "compte/blocages.html",
    "secondary_junior": ROOT / "compte/communaute-junior.html",
    "secondary_project": ROOT / "compte/projet.html",
    "secondary_death_report": ROOT / "compte/signaler-deces.html",
    "privacy_information": ROOT / "compte/confidentialite-joueur.html",
}

def fail(message: str) -> None:
    raise ValueError(message)

def compact(value: str) -> str:
    return "".join(value.lower().split())

def validate(contents: dict[str, str]) -> None:
    m = compact(contents["migration"])
    project_owner_migration = compact(contents["project_owner_migration"])
    supabase_config_raw = contents["supabase_config"]
    api_start = supabase_config_raw.find("[api]")
    api_end = supabase_config_raw.find("[edge_runtime]", api_start)
    if api_start < 0 or api_end < 0:
        fail("frontière Data API Supabase: section [api] introuvable ou non bornée")
    api_effective = "\n".join(
        line.split("#", 1)[0]
        for line in supabase_config_raw[api_start:api_end].splitlines()
    )
    api_section = compact(api_effective)

    for marker in (
        '[api]',
        'schemas=["public","storage","graphql_public"]',
        'extra_search_path=["public","extensions"]',
    ):
        if marker not in api_section:
            fail(f"frontière Data API Supabase: configuration explicite absente: {marker}")
    for forbidden_schema in ('sinjira_v25_internal','sinjira_catalog_internal','private'):
        if forbidden_schema in api_section:
            fail(f"frontière Data API Supabase: schéma interne exposé: {forbidden_schema}")
    public_rpc_boundary = compact(contents["public_rpc_boundary_migration"])
    browser_privileges = compact(contents["browser_privileges_migration"])
    browser_helper_hardening = compact(contents["browser_helper_hardening_migration"])
    paid_access_migration = compact(contents["paid_access_migration"])
    age_boundary_migration = compact(contents["age_boundary_migration"])
    project_product_migration = compact(contents["project_product_migration"])
    libh = compact(contents["library_html"])
    libj = compact(contents["library_js"])
    licenses_html = compact(contents["licenses_html"])
    licenses_js = compact(contents["licenses_js"])
    secondary_library = compact(contents["secondary_library_js"])
    ph = compact(contents["purchases_html"])
    pj = compact(contents["purchases_js"])
    prof = compact(contents["profile_html"])
    private_profile = compact(contents["private_profile_js"])
    acc = compact(contents["account_js"])
    data_control = compact(contents["data_control_js"])
    preferences = compact(contents["preferences_js"])
    privacy_center = compact(contents["privacy_center_js"])
    dashboard = compact(contents["dashboard_js"])
    account_css = compact(contents["account_css"])
    recovery = compact(contents["recovery_js"])
    signup_html = compact(contents["signup_html"])
    login_html = compact(contents["login_html"])
    forgot_html = compact(contents["forgot_html"])
    reset_html = compact(contents["reset_html"])
    mfa_html = compact(contents["mfa_html"])
    workflow = contents["workflow"]
    if "paths:" not in workflow or "workflow_dispatch:" not in workflow:
        fail("CI compte: section pull_request.paths introuvable")
    workflow_paths = workflow.split("paths:", 1)[1].split("workflow_dispatch:", 1)[0]
    reader = compact(contents["reader_js"])
    comments = compact(contents["comments_js"])
    comment_html = compact(contents["comments_html"])
    lith = compact(contents["literature_html"])
    litj = compact(contents["literature_js"])
    test = compact(contents["test"])
    child_content_test = compact(contents["child_content_test"])

    required_migration = (
        "createpolicysinjira_novels_owner_read",
        "createpolicyproducts_entitled_read",
        "createpolicyproducts_ordered_read",
        "createpolicyproducts_owner_read",
        "public.is_sinjira_owner((selectauth.uid()))",
        "insertintopublic.sinjira_novels",
        "'le-sang-du-sauveur'",
    )
    for marker in required_migration:
        if marker not in m:
            fail(f"migration contenu: garde absente: {marker}")

    for marker in (
        "altertablepublic.projectsenablerowlevelsecurity",
        "createpolicyprojects_owner_catalog_read_v25",
        "public.is_sinjira_owner((selectauth.uid()))",
    ):
        if marker not in project_owner_migration:
            fail(f"migration projets créateur: garde absente: {marker}")

    if "supabase/migrations/20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql" not in workflow_paths:
        fail("CI compte: migration visibilité projets créateur non surveillée")
    if "supabase/migrations/20260919123000_sinjira_v25_public_rpc_boundary.sql" not in workflow_paths:
        fail("CI compte: frontière RPC V25 finale non surveillée")

    for marker in (
        "ifarray_length(v_targets,1)<>23then",
        "fromunnest(v_targets)ast(name)",
        "fromunnest(v_anon_targets)ast(name)",
        "'alterfunctionpublic.%i(%s)setschemasinjira_v25_internal'",
        "'revokeallonfunctionsinjira_v25_internal.%i(%s)frompublic,anon,authenticated'",
        "'grantexecuteonfunctionsinjira_v25_internal.%i(%s)toauthenticated,service_role'",
        "'createfunctionpublic.%i(%s)returns%slanguagesqlsecurityinvokersetsearch_path=''''as%l'",
        "'revokeallonfunctionpublic.%i(%s)frompublic,anon,authenticated'",
        "'grantexecuteonfunctionpublic.%i(%s)toauthenticated,service_role'",
        "ifr.proname=any(v_anon_targets)then",
    ):
        if marker not in public_rpc_boundary:
            fail(f"frontière RPC V25: invariant absent: {marker}")
    if public_rpc_boundary.count("havingcount(candidate.oid)<>1") != 2:
        fail("frontière RPC V25: unicité par nom absente pour les cibles générales ou anon")

    if "supabase/migrations/20260919130000_sinjira_v25_account_catalog_browser_privileges.sql" not in workflow_paths:
        fail("CI compte: convergence des privilèges catalogue navigateur non surveillée")
    if "supabase/migrations/20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql" not in workflow_paths:
        fail("CI compte: durcissement self-only des helpers navigateur non surveillé")
    if "supabase/migrations/20260922023000_sinjira_v25_paid_order_product_access.sql" not in workflow_paths:
        fail("CI compte: droits produit paid non surveillés")
    if "supabase/migrations/20260922033000_sinjira_v25_project_product_access.sql" not in workflow_paths:
        fail("CI compte: accès produit générique des projets non surveillé")
    if "assets/js/v24-licenses.js" not in workflow_paths:
        fail("CI compte: page Licences non surveillée")
    if "supabase/tests/child_content_rating_v25.test.sql" not in workflow_paths:
        fail("CI compte: pgTAP classement 11–12 non surveillé")
    if "supabase test db supabase/tests/child_content_rating_v25.test.sql" not in workflow:
        fail("CI compte: pgTAP classement 11–12 non exécuté")

    for marker in (
        "createorreplacefunctionsinjira_catalog_internal.project_access_rank(",
        "coalesce(auth.jwt()->>'role','')<>'service_role'",
        "p_user_idisdistinctfromauth.uid()then0",
        "grantexecuteonfunctionsinjira_catalog_internal.project_access_rank(uuid,uuid)toanon,authenticated,service_role",
    ):
        if marker not in browser_helper_hardening:
            fail(f"migration helpers navigateur: garde project_access_rank absente: {marker}")

    for marker in (
        "createschemaifnotexistssinjira_catalog_internal",
        "alterfunctionpublic.project_access_rank(uuid,uuid)setschemasinjira_catalog_internal",
        "createorreplacefunctionsinjira_catalog_internal.project_access_rank(",
        "coalesce(auth.jwt()->>'role','')<>'service_role'",
        "p_user_idisdistinctfromauth.uid()then0",
        "grantexecuteonfunctionsinjira_catalog_internal.project_access_rank(uuid,uuid)toanon,authenticated,service_role",
        "createfunctionpublic.project_access_rank(",
        "securityinvoker",
        "revokeallonfunctionpublic.project_access_rank(uuid,uuid)frompublic,anon,authenticated",
        "grantexecuteonfunctionpublic.project_access_rank(uuid,uuid)toservice_role",
    ):
        if marker not in browser_privileges:
            fail(f"migration privilèges catalogue: frontière project_access_rank absente: {marker}")

    for marker in (
        "revokeallontablepublic.projectsfromanon,authenticated",
        "grantselectontablepublic.projectstoanon,authenticated",
        "revokeallontablepublic.project_accessfromanon,authenticated",
        "grantselectontablepublic.project_accesstoauthenticated",
        "revokeallontablepublic.access_requestsfromanon,authenticated",
        "grantselect,insertontablepublic.access_requeststoauthenticated",
        "revokeallontablepublic.documentsfromanon,authenticated",
        "grantselectontablepublic.documentstoanon,authenticated",
        "revokeallontablepublic.playtestsfromanon,authenticated",
        "grantselectontablepublic.playteststoauthenticated",
        "revokeallontablepublic.playtest_participantsfromanon,authenticated",
        "grantselect,insertontablepublic.playtest_participantstoauthenticated",
        "revokeallontablepublic.extensionsfromanon,authenticated",
        "grantselectontablepublic.extensionstoanon,authenticated",
    ):
        if marker not in browser_privileges:
            fail(f"migration privilèges catalogue: garde absente: {marker}")

    for marker in (
        "createpolicyproducts_ordered_read",
        "public.sinjira_my_age_band()in('adult','youth')",
        "o.status='paid'",
        "createorreplacefunctionsinjira_v25_internal.sinjira_my_product_rights()",
        "selectauth.uid()asuid",
        "'paid_order'::textassource",
        "public.sinjira_age_band(auth.uid())",
        "a.bandin('adult','youth')",
        "distincton(product_id)",
        "revokeallonfunctionsinjira_v25_internal.sinjira_my_product_rights()frompublic,anon,authenticated",
        "createorreplacefunctionpublic.sinjira_my_product_rights()",
        "securityinvoker",
        "selectsinjira_v25_internal.sinjira_my_product_rights()",
        "revokeallonfunctionpublic.sinjira_my_product_rights()frompublic,anon",
        "grantexecuteonfunctionpublic.sinjira_my_product_rights()toauthenticated,service_role",
    ):
        if marker not in paid_access_migration:
            fail(f"migration droits produit effectifs: invariant absent: {marker}")
    rights_start=paid_access_migration.find("createorreplacefunctionsinjira_v25_internal.sinjira_my_product_rights()")
    rights_end=paid_access_migration.find("$rights$;",rights_start)
    if rights_start < 0 or rights_end < 0 or "p_user_id" in paid_access_migration[rights_start:rights_end]:
        fail("migration droits produit effectifs: implémentation self-only invalide")
    rights_segment=paid_access_migration[rights_start:rights_end]
    if rights_segment.count("a.bandin('adult','youth')") < 2:
        fail("migration droits produit effectifs: les deux sources commerciales doivent rester masquées à 11–12")
    wrapper_start=paid_access_migration.find("createorreplacefunctionpublic.sinjira_my_product_rights()")
    wrapper_end=paid_access_migration.find("$wrapper$;",wrapper_start)
    if wrapper_start < 0 or wrapper_end < 0:
        fail("migration droits produit effectifs: wrapper public absent")
    wrapper_segment=paid_access_migration[wrapper_start:wrapper_end]
    if "securityinvoker" not in wrapper_segment or "securitydefiner" in wrapper_segment:
        fail("migration droits produit effectifs: wrapper public doit rester SECURITY INVOKER")

    for marker in (
        "createpolicyproducts_active_readonpublic.productsforselecttoauthenticatedusing(active=trueandpublic.sinjira_my_age_band()in('adult','youth'))",
        "createpolicyorders_own_readonpublic.ordersforselecttoauthenticatedusing((selectauth.uid())=user_idandpublic.sinjira_my_age_band()in('adult','youth'))",
        "createpolicyorder_items_own_readonpublic.order_itemsforselecttoauthenticatedusing(public.sinjira_my_age_band()in('adult','youth')andexists(select1frompublic.ordersowhereo.id=order_items.order_idando.user_id=(selectauth.uid())))",
        "createpolicyentitlements_own_readonpublic.user_entitlementsforselecttoauthenticatedusing((selectauth.uid())=user_idandpublic.sinjira_my_age_band()in('adult','youth'))",
        "whencoalesce(auth.jwt()->>'role','')='service_role'thensinjira_v25_internal.has_sinjira_product(p_product_slug,p_user_id)",
        "orp_user_idisdistinctfromauth.uid()orpublic.sinjira_my_age_band()notin('adult','youth')thenfalse",
    ):
        if marker not in age_boundary_migration:
            fail(f"frontière commerce Junior: policy finale absente ou non bornée: {marker[:80]}")

    for marker in (
        "altertablepublic.projectsaddcolumnifnotexistsproduct_slugtext",
        "projects_product_slug_fkey",
        "createpolicyprojects_purchased_read_v25",
        "status<>'draft'andproduct_slugisnotnull",
        "status<>'draft'andvisibility='public'andproduct_slugisnulland(",
        "(status<>'draft'andvisibility='account'andproduct_slugisnull)orsinjira_catalog_internal.project_access_rank(id,(selectauth.uid()))>=20",
        "public.has_sinjira_product(product_slug,(selectauth.uid()))",
        "createorreplacefunctionsinjira_v25_internal.sinjira_my_project_catalog()",
        "p.product_slugisnull",
        "sinjira_v25_internal.has_sinjira_product(p.product_slug,uid)",
        "then'product'",
        "else'free'",
        "parent_project.product_slugisnotnull",
    ):
        if marker not in project_product_migration:
            fail(f"migration accès produit projet: invariant absent: {marker}")

    for marker in ("data-library-games", "data-library-novels", "data-library-other", "data-library-extensions", "data-library-extension-count"):
        if marker not in libh:
            fail(f"bibliothèque: séparation manquante: {marker}")
    if libj.count("projects.filter(project=>project.type==='game')") < 2:
        fail("bibliothèque: filtre Jeux absent d'une branche adulte/Junior")
    if libj.count("projects.filter(project=>project.type!=='game')") < 2:
        fail("bibliothèque: filtre Autres créations absent d'une branche adulte/Junior")
    if 'href="mes-achats.html"><strong>mesachats</strong>' not in libh:
        fail("bibliothèque: raccourci Mes achats absent")
    if "commandesetachatsenregistrésrestentconsultablesséparémentdans«mesachats»" not in libh:
        fail("bibliothèque: acquisitions encore confondues avec les accès affichés")
    if "sinjira-library.js?v=24.1" in contents["library_html"]:
        fail("bibliothèque: ancien module générique encore chargé en parallèle")
    if "lesachats,licencesetdroitsnumériquessontvérifiésseloncecompte" not in libh:
        fail("bibliothèque: résumé acquisition neutre et exact absent")
    if "aucunachatouservicepayantn’estactivéactuellement" in libh:
        fail("bibliothèque: ancien résumé commerce absolu encore publié")
    if "ressourcesgratuitesactivéesseulement" in libh:
        fail("bibliothèque: ancien pied de page gratuit-only encore publié")
    if "sinjira_my_novel_catalog" not in contents["library_js"]:
        fail("bibliothèque: catalogue roman self-only canonique absent")
    if "sinjira_my_extension_catalog" not in contents["library_js"]:
        fail("bibliothèque: catalogue extensions self-only canonique absent")
    if "functionrenderextensions" not in libj:
        fail("bibliothèque: rendu extensions absent")
    if "source===\'product\'" not in libj or "acheté/droitnumérique" not in libj:
        fail("bibliothèque: extension privée achetée non distinguée du catalogue public")
    if "functionrendernovels" not in libj:
        fail("bibliothèque: rendu romans absent")
    if "constfullaccess=boolean(novel.full_access);" not in libj or "fullaccess?" not in libj:
        fail("bibliothèque: intégrale privée non liée au full_access canonique")
    if "data-private-book-download" in libj or "functionbookactions" in libj or "functiondownloadprivatebook" in libj:
        fail("bibliothèque: action privée dupliquée hors catalogue roman")
    if "accèsauteur" in libj:
        fail("bibliothèque: rôle créateur encore présenté comme droit numérique privé")
    for marker in (
        "constprojectquery=s.rpc('sinjira_my_project_catalog')",
        "s.rpc('is_sinjira_admin',{p_user_id:user.id}),s.rpc('is_sinjira_owner',{p_user_id:user.id}),s.rpc('sinjira_my_project_catalog'),s.from('project_access')",
        "constsource=string(project.access_source||'free')",
        "source==='product'",
        "acheté/droitnumérique",
        "project.product_slug&&source==='product'",
        "project.play_path&&childapproved",
        "source==='entitlement'||source==='product'",
        "s.rpc('sinjira_my_product_rights')",
    ):
        if marker not in libj:
            fail(f"bibliothèque: catalogue projet générique mal lié aux droits réels: {marker}")
    for forbidden in ("s.from('orders')","s.from('order_items')","s.from('user_entitlements')"):
        if forbidden in libj:
            fail(f"bibliothèque: lecture commerciale directe interdite: {forbidden}")
    for marker in (
        "functionrenderunavailable(selector,title,message)",
        "juniorresolved=!projectsresult.error&&!documentsresult.error",
        "extensionsresult.error",
        "roleresolved=ownerresolved&&(isowner||adminresolved)",
        "projectresolved=!projectsresult.error&&!accessresult.error&&!documentsresult.error&&!pendingresult.error",
        "readsresolved=!readsresult.error,entitlementsresolved=!entitlementsresult.error,novelsresolved=!novelsresult.error,extensionsresolved=!extensionsresult.error",
        "projectresolved?projects.length:'—'",
        "novelsresolved?novels.length:'—'",
        "extensionsresolved?extensions.length:'—'",
        "entitlementsresolved?entitlements.length:'—'",
        "projetstemporairementindisponibles",
        "romanstemporairementindisponibles",
        "extensionstemporairementindisponibles",
        "progressiontemporairementindisponible",
        "droitsnumériquestemporairementindisponibles",
        "bibliothèquejuniortemporairementindisponible",
    ):
        if marker not in libj:
            fail(f"bibliothèque: dégradation fail-closed absente: {marker}")
    if "sinjira-library-v24-4-61.js?v=25.1.8" not in contents["library_html"]:
        fail("bibliothèque: cache module principal V25.1.8 absent")
    for marker in (
        "s.rpc('sinjira_my_product_rights')",
        "row.source==='paid_order'?'achatpayé'",
        "droitnumériquereconnu",
        "sinjira_my_account_capabilities",
        "constchildmode=capabilitiesresolved&&capabilitiesresult.data.library_mode==='reviewed_11_12'",
        "asyncfunctioninit(){",
        "if(!form||!list)return;",
        "init().catch(error=>",
        "form.hidden=true",
        "licencesprotégéespourlescomptes11–12ans",
    ):
        if marker not in licenses_js:
            fail(f"licences: droit produit effectif absent: {marker}")
    for forbidden in ("s.from('orders')","s.from('order_items')","s.from('user_entitlements')"):
        if forbidden in licenses_js:
            fail(f"licences: lecture commerciale directe interdite: {forbidden}")
    if "if(form&&list){" in licenses_js:
        fail("licences: ancien bloc top-level avec return hors fonction interdit")
    if "v24-licenses.js?v=25.1.2" not in contents["licenses_html"]:
        fail("licences: cache V25.1.2 non forcé")
    if "licencessinjira™—modegratuit." in licenses_html:
        fail("licences: ancien pied de page mode gratuit encore publié")

    if "issinjiraowner" in secondary_library:
        fail("bibliothèque secondaire: rôle créateur encore déduit côté navigateur")
    if "s.rpc('is_sinjira_owner',{p_user_id:user.id})" not in contents["secondary_library_js"]:
        fail("bibliothèque secondaire: RPC serveur is_sinjira_owner absent")
    for marker in (
        "s.rpc('sinjira_my_project_catalog')",
        "constsource=string(p.access_source||'free')",
        "p.product_slug&&source==='product'",
        "p.visibility==='account'?'inclusaveclecompte':'pagepublique'",
        "constvisibility=childmode?(available?'contenuvérifié11–12ans':'contenuprotégéselonl’âge'):p.product_slug&&source==='product'?'droitnumériqueactif':p.visibility==='restricted'?'accèsrestreint':p.visibility==='account'?'inclusaveclecompte':'pagepublique';",
        "owner?'propriétaire·cataloguecomplet':a?.access_level==='tester'?'testeurapprouvé':explicitaccess?'accèsprivéautorisé':p.visibility==='restricted'?'accèsprivéautorisé':p.visibility==='account'?'inclusaveclecompte':'pagepublique';",
        "constlicensedproject=boolean(p.product_slug)",
        "p_product_slug:p.product_slug",
        "constexplicitaccess=boolean(",
        "constcanplay=!licensedproject||owner||productright||explicitaccess",
        "licenseaction=!childmode&&licensedproject&&!owner&&!productright&&!explicitaccess",
        "droitdeprojetnonvérifié",
        "droitnumériqueactif",
        "droitproduitrequis",
        "if(error)throwerror;",
        "if(pr.error||dr.error||rr.error)",
        "bibliothèquetemporairementindisponible",
        "if(accesserror&&!childmode)",
        "if(docserror)",
        "if(playtesterror)",
        "if(pr.error||mr.error)",
        "aucunenouvelleactionn’estproposée",
    ):
        if marker not in secondary_library:
            fail(f"bibliothèque secondaire: sémantique projet incohérente: {marker}")
    if "assets/js/sinjira-library.js" not in workflow_paths:
        fail("CI compte: module bibliothèque secondaire non surveillé")
    for name in ("secondary_project","secondary_documents"):
        if "sinjira-library.js?v=25.1.3" not in contents[name]:
            fail(f"bibliothèque secondaire: cache V25 absent dans {name}")

    for marker in ("data-purchase-history", "data-purchase-entitlements", "data-creator-portfolio"):
        if marker not in ph:
            fail(f"achats: section manquante: {marker}")
    if "commandesenregistrées" not in ph or "commandespayées/enregistrées" in ph:
        fail("achats: compteur commandes encore ambigu sur le statut de paiement")
    if "aucunecommandeenregistrée" not in pj or "aucunachatpayéenregistré" in pj:
        fail("achats: état vide confond encore commande enregistrée et achat payé")
    if ".eq('user_id',user.id)" not in contents["purchases_js"]:
        fail("achats: lectures propres au compte non bornées")
    for marker in (
        "sinjira_my_account_capabilities",
        "constchildmode=capabilitiesresolved&&capabilitiesresult.data.library_mode==='reviewed_11_12'",
        "constcommerceallowed=capabilitiesresolved&&capabilitiesresult.data.commerce===true",
        "constrole=document.queryselector('[data-purchase-account-role]')",
        "conststatus=document.queryselector('[data-purchases-v25-status]')",
        "if(!capabilitiesresolved)",
        "if(!commerceallowed)",
        "achatsprotégéspourlescomptes11–12ans",
        "droitsnumériquesprotégéspourlescomptes11–12ans",
        "informationscommercialesrestentmasquées",
    ):
        if marker not in pj:
            fail(f"achats Junior: garde fail-closed absente: {marker}")
    purchase_capability_pos=pj.find("sinjira_my_account_capabilities")
    purchase_role_pos=pj.find("constrole=document.queryselector('[data-purchase-account-role]')")
    purchase_status_pos=pj.find("conststatus=document.queryselector('[data-purchases-v25-status]')")
    purchase_capabilities_fail_pos=pj.find("if(!capabilitiesresolved)")
    purchase_gate_pos=pj.find("if(!commerceallowed)")
    purchase_orders_pos=pj.find("s.from('orders')")
    purchase_entitlements_pos=pj.find("s.from('user_entitlements')")
    if not (
        0 <= purchase_capability_pos < purchase_role_pos < purchase_capabilities_fail_pos
        and purchase_capability_pos < purchase_status_pos < purchase_capabilities_fail_pos
        and purchase_capabilities_fail_pos < purchase_gate_pos < purchase_orders_pos
        and purchase_gate_pos < purchase_entitlements_pos
    ):
        fail("achats Junior: nœuds statut/rôle et gardes commerce doivent précéder toute branche fail-closed et lecture commerciale")
    if "rendercreatorportfolio" not in pj:
        fail("achats: séparation portefeuille créateur absente")
    for marker in (
        "cataloguedesprojetstemporairementindisponible",
        "cataloguedesromanstemporairementindisponible",
        "cataloguedesproduitstemporairementindisponible",
        "consterrors=[ownerresult,ordersresult,entitlementsresult,...creatorresults]",
    ):
        if marker not in pj:
            fail(f"achats: échec partiel du portefeuille créateur non signalé: {marker}")
    if "rôleducomptenonconfirmé" not in libj or "rôleducomptenonconfirmé" not in pj:
        fail("rôle créateur: échec de résolution encore masqué comme compte membre")
    if "consterrors=[ownerresult,adminresult,projectsresult" not in libj:
        fail("bibliothèque: erreurs de rôle owner/admin non remontées")
    if "consterrors=[ownerresult,ordersresult,entitlementsresult,...creatorresults]" not in pj:
        fail("achats: erreur de rôle owner ou portefeuille créateur non remontée")
    for marker in (
        "constordersresolved=!ordersresult.error,entitlementsresolved=!entitlementsresult.error",
        "renderorders(orders,ordersresolved)",
        "renderentitlements(entitlements,entitlementsresolved)",
        "historiquetemporairementindisponible",
        "droitsnumériquestemporairementindisponibles",
        "ordercount.textcontent=ordersresolved?string(orders.length):'—'",
        "rightscount.textcontent=entitlementsresolved?string(entitlements.length):'—'",
    ):
        if marker not in pj:
            fail(f"achats: faux état vide encore possible: {marker}")
    if "sinjira-purchases-v25.js?v=25.0.5" not in contents["purchases_html"]:
        fail("achats: cache module V25.0.5 absent")

    if 'name="pseudo"required' not in prof or 'name="email"requiredtype="email"' not in prof:
        fail("profil: pseudo/courriel ne sont pas éditables")
    for marker in (
        "pseudonymepublic",
        "nomaffichéprivé",
        "n’estjamaiscopiédansleprofilsocialpublic",
    ):
        if marker not in prof:
            fail(f"profil: séparation identité publique/privée non expliquée: {marker}")
    if "auth.updateuser({email}" not in acc:
        fail("profil: mise à jour sécurisée du courriel absente")
    for marker in (
        "from('profiles').select('*').eq('user_id',user.id).maybesingle();if(error)throwerror;",
        "from('research_consents').select('*').eq('user_id',user.id).maybesingle();if(error)throwerror;",
        "functionsetformenabled(form,enabled)",
        "sessionsresolved=!rs.error,requestsresolved=!rr.error",
        "requestsresolved?reqs.length:'—'",
        "partiesrécentestemporairementindisponibles",
        "constform=document.queryselector('[data-profile-form]');if(!form)return;setformenabled(form,false);constuser=awaitrequireuser();",
        "impossibledechargerleprofil.leformulaireresteverrouillé",
        "constform=document.queryselector('[data-contribution-form]');if(!form)return;setformenabled(form,false);constuser=awaitrequireuser();",
        "impossibledevérifiervoschoixdecontribution.leformulaireresteverrouillé",
        "if(sheets.error||endgame.error)",
        "aucunfichierincompletn’aétégénéré",
        "constimportedsheets=(payload.player_sheets||[]).map(",
        "from('player_sheets').insert(importedsheets)",
        "aucunsuccèscompletn’estannoncé",
    ):
        if marker not in acc:
            fail(f"compte générique: dégradation fail-closed absente: {marker}")
    for key in ("account_page:index.html","profile_html","secondary_contributions","account_page:mes-parties.html"):
        if "sinjira-account.js?v=25.0.2" not in contents[key]:
            fail(f"compte générique: cache V25.0.2 absent dans {key}")
    if "sinjira-account.js?v=25.0.3" not in contents["account_page:parametres.html"]:
        fail("paramètres: cache Compte V25.0.3 absent après suppression des handlers dupliqués")
    if "data-export-data" in acc or "data-delete-account" in acc or "delete-player-account" in acc:
        fail("paramètres: export/suppression encore dupliqués dans le module Compte générique")
    for marker in (
        "constexportbutton=document.queryselector('[data-export-data]')",
        "constdeletebutton=document.queryselector('[data-delete-account]')",
        "['extended_private','privacy_export_my_extended_data']",
        "['private_profile','private_profile_get']",
        "consttotalsteps=entries.length+rpcexports.length",
        "label.endswith('_legacy')",
        "complete:errors.length===0",
        "exportpartieltéléchargé",
        "phrase!=='supprimermoncompte'",
        "functions.invoke('delete-player-account',{body:{confirm:'supprimermoncompte'}})",
        "asyncfunctionedgeerrordata(error)",
        "constresponsedata=error?(awaitedgeerrordata(error)):(data||null)",
        "if(error&&!responsedata)throwerror",
        "if(!responsedata?.ok)",
    ):
        if marker not in data_control:
            fail(f"paramètres: contrôleur canonique export/suppression incomplet: {marker}")
    if "from('private_profiles')" in data_control:
        fail("export compte: accès direct au coffre private_profiles interdit")
    if "v24-data-control.js?v=25.0.2" not in contents["account_page:parametres.html"]:
        fail("paramètres: cache contrôleur données V25.0.2 absent")
    for marker in (
        "functioncreateformlock(form)",
        "constpermanentlydisabled=newset([...form.elements].filter(el=>el.disabled))",
        "if(permanentlydisabled.has(el)){el.disabled=true;continue}",
        "constsetlocked=createformlock(form);setlocked(true);const{data,error}=awaits.from(table)",
        "setlocked(false)",
        "if(save&&tablemissing(save)){ready=false;setlocked(true)}",
        "if(table==='privacy_settings'&&form.elements.allow_ai_personal_data)",
        "form.elements.allow_ai_personal_data.checked=false",
        "if(table==='privacy_settings')payload.allow_ai_personal_data=false",
    ):
        if marker not in preferences:
            fail(f"paramètres: verrou de chargement préférences absent: {marker}")
    if "v24-preferences.js?v=25.0.2" not in contents["account_page:parametres.html"]:
        fail("paramètres: cache préférences V25.0.2 absent")
    for marker in (
        "setformlocked(true)",
        "authenticated=true",
        "setformlocked(false)",
        "if(!authenticated)",
        "votredemandeabienétéenregistrée,maislesuivinepeutpasêtrerafraîchi",
        "vouspouveztoutdemêmecréerunenouvelledemande",
    ):
        if marker not in privacy_center:
            fail(f"vie privée: état demande/chargement incohérent: {marker}")
    if "sinjira-privacy-center-v24-4-83.js?v=25.0.1" not in contents["secondary_privacy"]:
        fail("vie privée: cache centre V25.0.1 absent")
    for marker in (
        "if(form){setbusy(true);awaitrequireuser();try{awaitloadprofile();setbusy(false);",
        "leformulaireresteverrouillétantquevosdonnéesn’ontpasétéchargées",
        "form.addeventlistener('submit',asyncevent=>{event.preventdefault();if(!loadedsnapshot){",
        "aucunemodificationn’estenvoyée",
    ):
        if marker not in private_profile:
            fail(f"profil privé: verrou de chargement absent: {marker}")
    if "sinjira-private-profile-v24-5-23.js?v=25.1.2" not in contents["profile_html"]:
        fail("profil privé: cache module V25.1.2 absent")
    if "data-stat-reader" in contents["account_js"] or "data-account-role" in contents["account_js"] or "data-project-access-summary" in contents["account_js"]:
        fail("tableau de bord: données privées dupliquées dans le module Compte générique")
    if "from('sinjira_reader_library').select('novel_id,last_opened_at,progress_percent').eq('user_id',user.id)" not in contents["dashboard_js"]:
        fail("tableau de bord: source self-only des romans suivis absente")
    if "settext('[data-stat-reader]',count)" not in dashboard:
        fail("tableau de bord: compteur Romans suivis non alimenté")
    if "s.rpc('is_sinjira_owner',{p_user_id:user.id})" not in contents["dashboard_js"] or "s.rpc('is_sinjira_admin',{p_user_id:user.id})" not in contents["dashboard_js"]:
        fail("tableau de bord: rôle du compte non résolu côté serveur")
    if "roleresolved=ownerresolved&&(isowner||adminresolved)" not in dashboard:
        fail("tableau de bord: owner confirmé dépend encore inutilement du RPC admin")
    if "roleresolved&&(isadmin||isowner)" not in dashboard:
        fail("tableau de bord: catalogue complet owner/admin non chargé")
    if "rôleducomptenonconfirmé" not in dashboard:
        fail("tableau de bord: état fail-closed du rôle non confirmé absent")
    if dashboard.count("catalogresolved=!all.error") != 2 or "cataloguecomplettemporairementindisponible" not in dashboard:
        fail("tableau de bord: échec du catalogue complet owner/admin ou famille non signalé")
    for marker in (
        "constaccessresolved=!accessresult.error",
        "letcatalogresolved=false",
        "renderaccess(projects,isowner,isadmin,roleresolved,catalogresolved,accessresolved)",
        "renderlibrary(libraryresult.data||[],!libraryresult.error)",
        "accèsprojetstemporairementindisponibles",
        "bibliothèquedelecturetemporairementindisponible",
    ):
        if marker not in dashboard:
            fail(f"tableau de bord: dégradation fail-closed absente: {marker}")
    for watched in (
        "assets/js/sinjira-account-dashboard-v24-4-60.js",
        "assets/js/v24-data-control.js",
        "assets/js/v24-preferences.js",
        "assets/js/sinjira-privacy-center-v24-4-83.js",
        "projets/sinjira/romans/lire-demo.html",
    ):
        if watched not in workflow_paths:
            fail(f"CI compte: fichier critique non surveillé: {watched}")
    if "sinjira-account-dashboard-v24-4-60.js?v=25.0.3" not in contents["account_page:index.html"]:
        fail("tableau de bord: cache V25 du module dédié absent")
    if "pw.length<12" not in acc or "a.length<12" not in acc:
        fail("authentification: helpers Compte doivent conserver le minimum de 12 caractères")
    if "a.length<10" in acc or "au moins 10 caractères" in acc:
        fail("authentification: ancien minimum 10 caractères encore présent dans le helper Compte")
    if "password.length<12" not in recovery or "aumoins12caractères" not in recovery:
        fail("récupération active: minimum 12 caractères absent du script sécurisé")
    for marker in (
        'id="reset-password"autocomplete="new-password"minlength="12"name="password"',
        'id="reset-password-confirm"autocomplete="new-password"minlength="12"name="password_confirm"',
        "aumoins12caractères",
    ):
        if marker not in reset_html:
            fail(f"récupération active: HTML non aligné sur le minimum 12 caractères: {marker}")
    for auth_name,auth_page in (
        ("inscription",signup_html),
        ("connexion",login_html),
        ("mot de passe oublié",forgot_html),
        ("réinitialisation",reset_html),
        ("MFA",mfa_html),
    ):
        if "sinjira-player-account.css?v=25.0.1" not in auth_page:
            fail(f"authentification: cache CSS Compte V25 absent sur {auth_name}")
    if "security_after_password_recovery" not in recovery or "signout({scope:'global'})" not in recovery:
        fail("récupération active: nettoyage sécurité ou fermeture globale des sessions absent")
    if "assets/js/sinjira-recovery-v24-4-99.js" not in workflow_paths:
        fail("CI compte: le script de récupération sécurisé n'est pas surveillé par le workflow")

    for marker in ("appendgroup('bibliothèque'", "appendgroup('univers'", "appendgroup('communauté'", "appendgroup('compte'"):
        if marker not in acc:
            fail(f"navigation groupée absente: {marker}")
    for marker in (
        "functionnormalizeaccountheadernavigation()",
        "universe.href='/projets/sinjira/'",
        "universe.textcontent='universsinjira™'",
        "nav.replacechildren(universe)",
    ):
        if marker not in acc:
            fail(f"navigation supérieure Compte non normalisée: {marker}")
    if "appendgroup('bibliothèque',['bibliotheque.html','projet.html','mes-lectures.html','mes-commentaires.html'" not in acc:
        fail("navigation Bibliothèque: routes projet/commentaires non classées")
    if "'regles-communaute.html','regles-communaute-junior.html','moderation.html'" not in acc:
        fail("navigation Communauté: règles/modération non classées")
    if "details.open=true" not in acc:
        fail("navigation Compte: la famille de la page courante ne s'ouvre pas automatiquement")
    if ".account-nav-group[open]{grid-column:1/-1}" not in account_css:
        fail("navigation mobile: groupe ouvert ne prend pas toute la largeur")
    if ".account-nav-panel{position:static;width:100%;max-width:none;margin-top:6px}" not in account_css:
        fail("navigation mobile: panneau regroupé risque encore de déborder")

    for name, content in contents.items():
        if not name.startswith("secondary_") or not name.endswith(("_lectures","_documents","_playtests","_contributions","_reels","_personnage","_privacy","_blocks","_junior","_project","_report")):
            continue
        if not any(v in content for v in ("sinjira-account.js?v=25.0.1","sinjira-account.js?v=25.0.2","sinjira-account.js?v=25.0.3")):
            fail(f"navigation secondaire: cache JS V25 absent dans {name}")
        if "sinjira-player-account.css?v=25.0.1" not in content:
            fail(f"navigation secondaire: cache CSS V25 absent dans {name}")

    for name, content in contents.items():
        if not name.startswith("account_page:"):
            continue
        page_compact=compact(content)
        if 'class="account-nav"' not in page_compact:
            continue
        if not any(v in content for v in ("sinjira-account.js?v=25.0.1","sinjira-account.js?v=25.0.2","sinjira-account.js?v=25.0.3")):
            fail(f"navigation compte globale: JS V25 absent dans {name}")
        if "sinjira-player-account.css?v=25.0.1" not in content:
            fail(f"navigation compte globale: CSS V25 absent dans {name}")

    privacy_info = compact(contents["privacy_information"])
    if '<navclass="main-nav"aria-label="navigationprincipale"><ahref="/compte/vie-privee.html">centrevieprivée</a><ahref="/compte/inscription.html">créeruncompte</a></nav>' not in privacy_info:
        fail("confidentialité: barre supérieure publique non simplifiée")
    if "àpartirde11ans" not in privacy_info or "11–13ans" not in privacy_info:
        fail("confidentialité: seuil jeunesse actuel 11–13 absent")
    if "l’inscriptionlibre-serviceest13+" in privacy_info:
        fail("confidentialité: ancien seuil 13+ encore publié")

    if "from('novel_comments')" in reader or "from('novel_comments')" in comments:
        fail("commentaires: ancien modèle novel_comments encore utilisé")
    if "list_sinjira_novel_comments" not in contents["reader_js"]:
        fail("commentaires publics: RPC canonique absent")
    if "from('sinjira_novel_comments')" not in contents["reader_js"] or "from('sinjira_novel_comments')" not in contents["comments_js"]:
        fail("commentaires: table canonique sinjira_novel_comments absente")
    if "sinjira-account-v18.js?v=25.0.2" not in contents["comments_html"]:
        fail("commentaires: cache client V25 non forcé")
    for marker in (
        "from('sinjira_novels').select('id,title,subtitle,description,status,public_path,demo_path,sort_order')",
        "from('sinjira_reader_library').select('novel_id,last_opened_at,last_page,progress_percent').eq('user_id',user.id)",
        "n.subtitle||'sinjira'",
    ):
        if marker not in comments:
            fail(f"mes lectures: source canonique absente: {marker}")
    if "from('novels')" in comments or "from('reader_library')" in comments:
        fail("mes lectures: ancienne table novels/reader_library encore utilisée")
    if "sinjira-account-v18.js?v=25.0.2" not in contents["secondary_mes_lectures"]:
        fail("mes lectures: cache module V25.0.2 absent")

    if "data-literature-catalog" not in lith or "sinjira-literature-catalog-v25.js?v=25.1.2" not in lith:
        fail("littérature: catalogue dynamique V25 absent")
    if "sinjira_my_novel_catalog" not in contents["literature_js"] or "is_sinjira_owner" not in contents["literature_js"]:
        fail("littérature: catalogue self-only/créateur absent")
    if "from('sinjira_novels')" not in contents["literature_js"]:
        fail("littérature: fallback public anonyme canonique absent")
    for marker in (
        "ownerresolved=!ownerresult.error",
        "rôleducomptenonconfirmé",
        "aucunaccèssupplémentairen’estsupposé",
        "cataloguetemporairementindisponible",
    ):
        if marker not in litj:
            fail(f"littérature: dégradation fail-closed absente: {marker}")

    if "from('reader_library')" in reader:
        fail("lecteur démo: ancienne table reader_library encore utilisée")
    if "from('sinjira_reader_library').select('last_page')" not in contents["reader_js"]:
        fail("lecteur démo: reprise canonique sinjira_reader_library absente")
    for marker in (
        "const{error}=awaitgetsupabase().from('sinjira_reader_library').upsert(",
        "return{synced:!error,error:error||null}",
        "resume.textcontent=sync.synced?",
        "sauvegardéesurcetappareiletsynchroniséeavecvotrecompte",
        "synchronisationducompteindisponible",
        "if(!resumesyncavailable||!initialsync.synced)",
    ):
        if marker not in reader:
            fail(f"lecteur démo: état de synchronisation non vérifié: {marker}")
    if "sinjira-reader.js?v=25.0.3" not in contents["literature_html"]:
        fail("littérature: cache lecteur V25.0.3 absent")
    if "sinjira-reader.js?v=25.0.3" not in contents["demo_html"]:
        fail("lecteur démo: cache lecteur V25.0.3 absent")

    if "selectplan(51);" not in test:
        fail("pgTAP contenu: plan(51) absent")
    if "selectplan(26);" not in child_content_test:
        fail("pgTAP classement 11–12: plan(26) absent")
    for marker in (
        "anonnepeutpassonderunprojetaccountapprouvé11–12paruuid",
        "anonnepeutpassonderundocumentaccountapprouvé11–12paruuid",
        "unprojetaccountactifexplicitementapprouvédevientdisponible",
        "document+projetdoublementapprouvésdeviennentdisponibles",
        "lapolicyprojetachetéresteinterditeauxcomptes11–12etexigeundroitproduitréel",
        "unprojetpayantresteindisponible11–12mêmeavecapprobationhumaine",
        "undocumentdunprojetpayantresteindisponible11–12mêmedoublementapprouvé",
    ):
        if marker not in child_content_test:
            fail(f"pgTAP classement 11–12: preuve navigateur absente: {marker}")
    for marker in (
        "lapolicyprojetsowner-onlyv25existe",
        "authenticatedpeutlireprojectssousrls",
        "anonnepeutpaslireproject_access",
        "authenticatednepeutpassauto-attribuerproject_accessparinsert",
        "authenticatedpeutcréerunedemandesousrls",
        "authenticatednepeutpasdéciderunedemandedirectement",
        "authenticatedpeutcandidateràunplaytest",
        "authenticatednepeutpasapprouverunecandidaturedirectement",
        "policyname='requestsowninsert'",
        "insertaccess_requestsresteself-only,adulte/youthetpending",
        "policyname='participantsownapply'",
        "insertplaytest_participantsresteself-only,adulte/youthetapplied",
        "anonpeutlirelesextensionspubliquessousrls",
        "unmembrenevoitpasunromanbrouilloncréateur",
        "unmembrenevoitpasunprojetinternecréateur",
        "lecréateurvoit sonprojetinternesansfauxachat".replace(" ", ""),
        "lecataloguecompletducréateurnefabriqueaucundroitproduitcommercial",
        "unmembrevoitencoreunproduitinactifliéàsonentitlement",
        "unmembrevoitencoreunproduitinactifprésentdanssapropcommande".replace("propcommande", "proprecommande"),
        "unentitlementréelconserveledroitproduitmêmesileproduitdevientinactif",
        "unecommandepaidconserveledroitproduitmêmesileproduitdevientinactif",
        "unecommandependingnerendpasleproduitprivévisiblecommeachat",
        "unecommandependingnesatisfaitjamaisledroitproduit",
        "schémainternecatalogueexiste",
        "project_access_rankpublicestunwrappersecurityinvoker",
        "authenticatednepeutpassonderdirectementlerangprojet",
        "unmembrenepeutpassonderlerangprojetd’unautrecompte",
        "service_roleconserveexecutesurlehelperinternederangprojet",
        "service_rolepeutencorecalculerlerangd’unuuidexplicitedifférentducomptejwt",
        "lecomptecourantconservesonproprerangadminvialehelperinterne",
        "lespoliciesprojects/documentsconserventloiddhelperdéplacé".replace("dhelper","duhelper"),
        "lecréateurvoitsonromanbrouillon",
        "lesangdusauveurestprésentdanslecatalogueromancanonique",
    ):
        if marker not in test:
            fail(f"pgTAP contenu: preuve absente: {marker}")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    contents = {name: path.read_text(encoding="utf-8") for name, path in FILES.items()}
    for path in sorted(ACCOUNT_DIR.glob("*.html")):
        contents[f"account_page:{path.name}"]=path.read_text(encoding="utf-8")
    validate(contents)
    if args.self_test:
        mutations={
            "retour à novel_comments":("reader_js","sinjira_novel_comments","novel_comments"),
            "mes lectures revenue à reader_library":("comments_js","from('sinjira_reader_library').select('novel_id,last_opened_at,last_page,progress_percent')","from('reader_library').select('novel_id,last_opened_at,last_page,progress_percent')"),
            "mes lectures revenue à novels":("comments_js","from('sinjira_novels').select('id,title,subtitle,description,status,public_path,demo_path,sort_order')","from('novels').select('*')"),
            "cache mes lectures revenu V24":("secondary_mes_lectures","sinjira-account-v18.js?v=25.0.2","sinjira-account-v18.js?v=24.4.61"),
            "cache mes commentaires revenu V25.0.1":("comments_html","sinjira-account-v18.js?v=25.0.2","sinjira-account-v18.js?v=25.0.1"),
            "page compte sans JS V25":("account_page:index.html","sinjira-account.js?v=25.0.2","sinjira-account.js?v=24.1"),
            "profil générique masque erreur lecture":("account_js","const {data,error}=await getSupabase().from('profiles').select('*').eq('user_id',user.id).maybeSingle();\n  if(error)throw error;\n  return data||{};","const {data,error}=await getSupabase().from('profiles').select('*').eq('user_id',user.id).maybeSingle();\n  if(error)console.warn(error);\n  return data||{};"),
            "consentement générique masque erreur lecture":("account_js","const {data,error}=await getSupabase().from('research_consents').select('*').eq('user_id',user.id).maybeSingle();\n  if(error)throw error;\n  return data||{participate:false,share_free_text:false};","const {data,error}=await getSupabase().from('research_consents').select('*').eq('user_id',user.id).maybeSingle();\n  if(error)console.warn(error);\n  return data||{participate:false,share_free_text:false};"),
            "dashboard historique masque erreurs en zéro":("account_js","const sessionsResolved=!rs.error,requestsResolved=!rr.error","const sessionsResolved=true,requestsResolved=true"),
            "profil générique non verrouillé avant auth":("account_js","const form=document.querySelector('[data-profile-form]');if(!form)return;\n  setFormEnabled(form,false);\n  const user=await requireUser();","const form=document.querySelector('[data-profile-form]');if(!form)return;\n  const user=await requireUser();"),
            "contributions non verrouillées avant auth":("account_js","const form=document.querySelector('[data-contribution-form]');if(!form)return;\n  setFormEnabled(form,false);\n  const user=await requireUser();","const form=document.querySelector('[data-contribution-form]');if(!form)return;\n  const user=await requireUser();"),
            "cache compte profil revenu V25.0.1":("profile_html","sinjira-account.js?v=25.0.2","sinjira-account.js?v=25.0.1"),
            "cache compte contributions revenu V25.0.1":("secondary_contributions","sinjira-account.js?v=25.0.2","sinjira-account.js?v=25.0.1"),
            "contrôleur données réintroduit en double":("account_js","async function settings(){\n  await requireUser();\n}","async function settings(){\n  document.querySelector('[data-export-data]')?.addEventListener('click',()=>{});\n}"),
            "export coffre revenu en accès table direct":("data_control_js","['private_profile','private_profile_get']","['private_profile','private_profiles']"),
            "export privé étendu retiré":("data_control_js","['extended_private','privacy_export_my_extended_data']","['extended_private','missing_export_rpc']"),
            "export ancien schéma absent devient erreur":("data_control_js","const legacyMissing=label.endsWith('_legacy')&&/relation .* does not exist|schema cache|could not find/i.test(message);","const legacyMissing=false;"),
            "cache contrôleur données revenu V24":("account_page:parametres.html","v24-data-control.js?v=25.0.2","v24-data-control.js?v=24.4.83"),
            "préférences réactivées avant chargement":("preferences_js","const setLocked=createFormLock(form);\n  setLocked(true);\n  const {data,error}=await s.from(table)","const setLocked=createFormLock(form);\n  setLocked(false);\n  const {data,error}=await s.from(table)"),
            "préférences réactivent les champs permanents":("preferences_js","if(permanentlyDisabled.has(el)){el.disabled=true;continue}","if(permanentlyDisabled.has(el)){el.disabled=false;continue}"),
            "préférence IA personnelle réactivée":("preferences_js","if(table==='privacy_settings')payload.allow_ai_personal_data=false;","if(table==='privacy_settings')payload.allow_ai_personal_data=true;"),
            "cache préférences revenu V24":("account_page:parametres.html","v24-preferences.js?v=25.0.2","v24-preferences.js?v=24.4.70"),
            "centre vie privée actif avant auth":("privacy_center_js","setFormLocked(true);","setFormLocked(false);"),
            "centre vie privée confond création et refresh":("privacy_center_js","showStatus('Votre demande a bien été enregistrée, mais le suivi ne peut pas être rafraîchi pour le moment.','info');","showStatus('Impossible d’enregistrer la demande pour le moment.','error');"),
            "cache centre vie privée revenu V24":("secondary_privacy","sinjira-privacy-center-v24-4-83.js?v=25.0.1","sinjira-privacy-center-v24-4-83.js?v=24.4.83"),
            "cache paramètres revenu V25.0.2":("account_page:parametres.html","sinjira-account.js?v=25.0.3","sinjira-account.js?v=25.0.2"),
            "suppression compte revenue à ancienne phrase":("data_control_js","phrase!=='SUPPRIMER MON COMPTE'","phrase!=='SUPPRIMER'"),
            "suppression compte envoie ancienne phrase":("data_control_js","body:{confirm:'SUPPRIMER MON COMPTE'}","body:{confirm:'SUPPRIMER'}"),
            "suppression compte ignore corps d'erreur HTTP":("data_control_js","const responseData=error?(await edgeErrorData(error)):(data||null);","const responseData=data||null;"),
            "suppression compte ignore ok serveur":("data_control_js","if(!responseData?.ok)","if(false)"),
            "export partie masque erreur de fiches":("account_js","if(sheets.error||endgame.error)","if(false)"),
            "import partie ignore erreur de fiches":("account_js","if(sheetError){setStatus(status,'La partie a été créée, mais ses fiches n’ont pas pu être importées. Aucun succès complet n’est annoncé.','error');return}","if(sheetError)console.warn(sheetError)"),
            "cache mes parties revenu V25.0.1":("account_page:mes-parties.html","sinjira-account.js?v=25.0.2","sinjira-account.js?v=25.0.1"),
            "modération renvoyée vers Plus":("account_js","'regles-communaute.html','regles-communaute-junior.html','moderation.html'","'regles-communaute.html','regles-communaute-junior.html'"),
            "reset mot de passe revenu à 10":("account_js","a.length<12","a.length<10"),
            "récupération active revenue à 10":("recovery_js","password.length<12","password.length<10"),
            "HTML reset revenu à 10":("reset_html",'minlength="12"','minlength="10"'),
            "script récupération hors paths CI":("workflow","assets/js/sinjira-recovery-v24-4-99.js","assets/js/sinjira-recovery-missing.js"),
            "inscription avec ancien cache CSS":("signup_html","sinjira-player-account.css?v=25.0.1","sinjira-player-account.css?v=24.4.12"),
            "MFA avec ancien cache CSS":("mfa_html","sinjira-player-account.css?v=25.0.1","sinjira-player-account.css?v=24.4.66"),
            "schéma interne exposé Data API":("supabase_config",'schemas = ["public", "storage", "graphql_public"]','schemas = ["public", "storage", "graphql_public", "sinjira_v25_internal"]'),
            "policy projets créateur retirée":("project_owner_migration","create policy projects_owner_catalog_read_v25","create policy projects_owner_catalog_missing"),
            "migration projets créateur hors paths CI":("workflow","supabase/migrations/20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql","supabase/migrations/projects-owner-missing.sql"),
            "migration privilèges catalogue hors paths CI":("workflow","supabase/migrations/20260919130000_sinjira_v25_account_catalog_browser_privileges.sql","supabase/migrations/catalog-browser-privileges-missing.sql"),
            "frontière RPC masque cible manquante par overload":("public_rpc_boundary_migration","from unnest(v_targets) as t(name)","from unnest(array[]::text[]) as t(name)"),
            "frontière RPC anon masque cible manquante":("public_rpc_boundary_migration","from unnest(v_anon_targets) as t(name)","from unnest(array[]::text[]) as t(name)"),
            "wrapper RPC V25 redevient SECURITY DEFINER":("public_rpc_boundary_migration","language sql security invoker set search_path = '''' as %L","language sql security definer set search_path = '''' as %L"),
            "migration helpers navigateur hors paths CI":("workflow","supabase/migrations/20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql","supabase/migrations/browser-helper-hardening-missing.sql"),
            "migration produit projet hors paths CI":("workflow","supabase/migrations/20260922033000_sinjira_v25_project_product_access.sql","supabase/migrations/project-product-access-missing.sql"),
            "projet payant sans droit canonique":("project_product_migration","public.has_sinjira_product(product_slug,(select auth.uid()))","true"),
            "projet public payant réexposé":("project_product_migration","status<>'draft'\n    and visibility='public'\n    and product_slug is null","visibility='public'\n    and product_slug is null"),
            "achat projet révèle brouillon":("project_product_migration","status<>'draft'\n  and product_slug is not null","product_slug is not null"),
            "accès player draft retiré":("project_product_migration","or sinjira_catalog_internal.project_access_rank(id,(select auth.uid()))>=20",""),
            "pgTAP 11–12 hors paths CI":("workflow","supabase/tests/child_content_rating_v25.test.sql","supabase/tests/child-content-rating-missing.sql"),
            "pgTAP 11–12 non exécuté":("workflow","supabase test db supabase/tests/child_content_rating_v25.test.sql","echo child-content-rating-skipped"),
            "oracle anon projet 11–12 non prouvé":("child_content_test","anon ne peut pas sonder un projet account approuvé 11–12 par UUID","anon oracle projet preuve retirée"),
            "écriture projet navigateur réouverte":("browser_privileges_migration","grant select on table public.projects to anon, authenticated;","grant select, insert on table public.projects to anon, authenticated;"),
            "rang projet C2 rouvre sonde tiers":("browser_privileges_migration","p_user_id is distinct from auth.uid() then 0","false then 0"),
            "preuve RLS access_requests self-only retirée":("test","policyname='requests own insert'","policyname='requests missing insert'"),
            "preuve RLS playtest self-only retirée":("test","policyname='participants own apply'","policyname='participants missing apply'"),
            "full_access roman privé contourné":("library_js","const fullAccess=Boolean(novel.full_access);","const fullAccess=true;"),
            "projet principal jouable sans catalogue canonique":("library_js","project.play_path&&childApproved","project.play_path"),
            "catalogue projet principal retiré":("library_js","s.rpc('is_sinjira_admin',{p_user_id:user.id}),s.rpc('is_sinjira_owner',{p_user_id:user.id}),s.rpc('sinjira_my_project_catalog'),s.from('project_access')","s.rpc('is_sinjira_admin',{p_user_id:user.id}),s.rpc('is_sinjira_owner',{p_user_id:user.id}),s.from('projects').select('*'),s.from('project_access')"),
            "droits produit bibliothèque relus directement":("library_js","s.rpc('sinjira_my_product_rights')","s.from('user_entitlements')"),
            "droits produit licences relus directement":("licenses_js","s.rpc('sinjira_my_product_rights')","s.from('orders')"),
            "licences redevient bloc top-level invalide":("licenses_js","async function init(){\n  if(!form||!list)return;","if(form&&list){"),
            "policy produit paid rouverte enfant":("paid_access_migration","public.sinjira_my_age_band() in ('adult','youth')\n  and exists(","exists("),
            "catalogue commercial actif rouvert enfant":("age_boundary_migration","active=true\n  and public.sinjira_my_age_band() in ('adult','youth')","active=true"),
            "historique commandes brut rouvert enfant":("age_boundary_migration","(select auth.uid())=user_id\n  and public.sinjira_my_age_band() in ('adult','youth')","(select auth.uid())=user_id"),
            "oracle droit produit réouvert enfant":("age_boundary_migration","or public.sinjira_my_age_band() not in ('adult','youth')\n      then false","or false\n      then false"),
            "page achats contourne garde commerce":("purchases_js","if(!commerceAllowed){","if(false){"),
            "nœuds achats fail-closed retirés":("purchases_js","  const role=document.querySelector('[data-purchase-account-role]');\n  const status=document.querySelector('[data-purchases-v25-status]');\n",""),
            "cache licences revenu ancien":("licenses_html","v24-licenses.js?v=25.1.2","v24-licenses.js?v=24.4.62"),
            "pied licences revenu mode gratuit":("licenses_html","Licences SINJIRA™ — droits associés au compte.","Licences SINJIRA™ — mode gratuit."),
            "pied bibliothèque revenu gratuit-only":("library_html","Compte SINJIRA™ — accès selon votre compte et vos droits numériques.","Compte SINJIRA™ — ressources gratuites activées seulement."),
            "licences enfant sans garde capacités":("licenses_js","const childMode=capabilitiesResolved&&capabilitiesResult.data.library_mode==='reviewed_11_12';","const childMode=false;"),
            "ancien module bibliothèque rechargé":("library_html","<script src=\"../assets/js/sinjira-library-v24-4-61.js?v=25.1.8\" type=\"module\"></script>","<script src=\"../assets/js/sinjira-library.js?v=24.1\" type=\"module\"></script>"),
            "bibliothèque principale masque erreur projets":("library_js","const projectResolved=!projectsResult.error&&!accessResult.error&&!documentsResult.error&&!pendingResult.error;","const projectResolved=true;"),
            "bibliothèque principale masque erreur romans/extensions":("library_js","const readsResolved=!readsResult.error,entitlementsResolved=!entitlementsResult.error,novelsResolved=!novelsResult.error,extensionsResolved=!extensionsResult.error;","const readsResolved=true,entitlementsResolved=true,novelsResolved=true,extensionsResolved=true;"),
            "bibliothèque principale suppose rôle membre":("library_js","const roleResolved=ownerResolved&&(isOwner||adminResolved);","const roleResolved=true;"),
            "bibliothèque Junior masque erreur":("library_js","juniorResolved=!projectsResult.error&&!documentsResult.error","juniorResolved=true"),
            "cache bibliothèque principale revenu V25.1.0":("library_html","sinjira-library-v24-4-61.js?v=25.1.8","sinjira-library-v24-4-61.js?v=25.1.0"),
            "raccourci Mes achats retiré":("library_html",'<a href="mes-achats.html"><strong>Mes achats</strong>','<a href="licences.html"><strong>Mes achats</strong>'),
            "jeux remélangés avec tous les projets":("library_js","projects.filter(project=>project.type==='game')","projects"),
            "autres créations remélangées avec jeux":("library_js","projects.filter(project=>project.type!=='game')","projects"),
            "rôle créateur secondaire revenu côté client":("secondary_library_js","s.rpc('is_sinjira_owner',{p_user_id:user.id})","Promise.resolve({data:false,error:null})"),
            "projet public secondaire présenté comme compte":("secondary_library_js","const visibility=childMode?(available?'Contenu vérifié 11–12 ans':'Contenu protégé selon l’âge'):p.product_slug&&source==='product'?'Droit numérique actif':p.visibility==='restricted'?'Accès restreint':p.visibility==='account'?'Inclus avec le compte':'Page publique';","const visibility=childMode?(available?'Contenu vérifié 11–12 ans':'Contenu protégé selon l’âge'):p.product_slug&&source==='product'?'Droit numérique actif':p.visibility==='restricted'?'Accès restreint':'Inclus avec le compte';"),
            "détail projet public secondaire présenté comme compte":("secondary_library_js","owner?'Propriétaire · catalogue complet':a?.access_level==='tester'?'Testeur approuvé':explicitAccess?'Accès privé autorisé':p.visibility==='restricted'?'Accès privé autorisé':p.visibility==='account'?'Inclus avec le compte':'Page publique';","owner?'Propriétaire · catalogue complet':a?.access_level==='tester'?'Testeur approuvé':explicitAccess?'Accès privé autorisé':p.visibility==='restricted'?'Accès privé autorisé':'Inclus avec le compte';"),
            "catalogue projet secondaire retiré":("secondary_library_js","s.rpc('sinjira_my_project_catalog')","s.from('projects').select('*')"),
            "projet payant secondaire redevient spécial Fracture":("secondary_library_js","const licensedProject=Boolean(p.product_slug);","const licensedProject=p.slug==='fracture-du-reseau-mere';"),
            "erreur project_access secondaire ignorée":("secondary_library_js","if(error)throw error;","if(error)console.warn(error);"),
            "échec catalogue secondaire masqué":("secondary_library_js","if(pr.error||dr.error||rr.error){","if(false){"),
            "échec candidatures playtest masqué":("secondary_library_js","if(pr.error||mr.error){","if(false){"),
            "projet payant secondaire jouable sans droit":("secondary_library_js","const canPlay=!licensedProject||owner||productRight||explicitAccess;","const canPlay=true;"),
            "contrôle produit secondaire retiré":("secondary_library_js","s.rpc('has_sinjira_product',{p_product_slug:p.product_slug})","Promise.resolve({data:true,error:null})"),
            "module bibliothèque secondaire hors paths CI":("workflow","assets/js/sinjira-library.js","assets/js/sinjira-library-missing.js"),
            "cache Projet bibliothèque revenu V24":("secondary_project","sinjira-library.js?v=25.1.3","sinjira-library.js?v=24.1"),
            "navigation mobile redevenue absolue":("account_css",".account-nav-panel{position:static;width:100%;max-width:none;margin-top:6px}",".account-nav-panel{position:absolute;width:min(88vw,320px)}"),
            "barre supérieure Compte redevenue multiple":("account_js","nav.replaceChildren(universe);","nav.append(universe);"),
            "famille courante refermée":("account_js","details.open=true;","details.open=false;"),
            "barre confidentialité redevenue multiple":("privacy_information",'<nav class="main-nav" aria-label="Navigation principale"><a href="/compte/vie-privee.html">Centre Vie privée</a><a href="/compte/inscription.html">Créer un compte</a></nav>','<nav class="main-nav" aria-label="Navigation principale"><a href="/confidentialite.html">Politique générale</a><a href="/compte/vie-privee.html">Centre Vie privée</a><a href="/compte/inscription.html">Créer un compte</a></nav>'),
            "compteur commandes redevenu ambigu":("purchases_html","Commandes enregistrées","Commandes payées / enregistrées"),
            "échec rôle créateur masqué en bibliothèque":("library_js","Rôle du compte non confirmé","Compte SINJIRA™"),
            "échec rôle créateur masqué dans achats":("purchases_js","Rôle du compte non confirmé","Compte membre SINJIRA™"),
            "échec portefeuille créateur masqué":("purchases_js","Catalogue des projets temporairement indisponible.","Aucun projet enregistré."),
            "échec commandes masqué en zéro":("purchases_js","const ordersResolved=!ordersResult.error,entitlementsResolved=!entitlementsResult.error;","const ordersResolved=true,entitlementsResolved=!entitlementsResult.error;"),
            "échec droits masqué en zéro":("purchases_js","renderEntitlements(entitlements,entitlementsResolved);","renderEntitlements(entitlements,true);"),
            "cache achats revenu V25.0.1":("purchases_html","sinjira-purchases-v25.js?v=25.0.5","sinjira-purchases-v25.js?v=25.0.1"),
            "nom affiché redevenu ambigu":("profile_html","Nom affiché privé","Nom affiché"),
            "profil privé sauvegarde sans chargement":("private_profile_js","if(!loadedSnapshot){","if(false){"),
            "profil privé réactivé après échec de chargement":("private_profile_js","setStatus(status,userMessage(error)+' Le formulaire reste verrouillé tant que vos données n’ont pas été chargées. Rechargez la page pour réessayer.','error');","setBusy(false); setStatus(status,userMessage(error),'error');"),
            "cache profil privé revenu V25.1.1":("profile_html","sinjira-private-profile-v24-5-23.js?v=25.1.2","sinjira-private-profile-v24-5-23.js?v=25.1.1"),
            "compteur romans suivis retiré":("dashboard_js","setText('[data-stat-reader]',count)","setText('[data-stat-reader]',0)"),
            "rôle dashboard supposé côté client":("dashboard_js","s.rpc('is_sinjira_owner',{p_user_id:user.id})","Promise.resolve({data:false,error:null})"),
            "owner retiré du catalogue dashboard":("dashboard_js","if(roleResolved&&(isAdmin||isOwner)){","if(roleResolved&&isAdmin){"),
            "owner rendu dépendant du RPC admin":("dashboard_js","const roleResolved=ownerResolved&&(isOwner||adminResolved);","const roleResolved=ownerResolved&&adminResolved;"),
            "catalogue dashboard déclaré sain à tort":("dashboard_js","catalogResolved=!all.error;","catalogResolved=true;"),
            "erreur accès dashboard masquée":("dashboard_js","const accessResolved=!accessResult.error;","const accessResolved=true;"),
            "bibliothèque dashboard erreur masquée":("dashboard_js","renderLibrary(libraryResult.data||[],!libraryResult.error);","renderLibrary(libraryResult.data||[],true);"),
            "résumé accès dashboard retiré":("dashboard_js","renderAccess(projects,isOwner,isAdmin,roleResolved,catalogResolved,accessResolved);","renderAccess(projects,false,false,true,true,true);"),
            "module Dashboard hors paths CI":("workflow","assets/js/sinjira-account-dashboard-v24-4-60.js","assets/js/sinjira-account-dashboard-missing.js"),
            "contrôleur données hors paths CI":("workflow","assets/js/v24-data-control.js","assets/js/v24-data-control-missing.js"),
            "préférences hors paths CI":("workflow","assets/js/v24-preferences.js","assets/js/v24-preferences-missing.js"),
            "centre vie privée hors paths CI":("workflow","assets/js/sinjira-privacy-center-v24-4-83.js","assets/js/privacy-center-missing.js"),
            "lecteur démo HTML hors paths CI":("workflow","projets/sinjira/romans/lire-demo.html","projets/sinjira/romans/lire-demo-missing.html"),
            "cache Dashboard revenu V24":("account_page:index.html","sinjira-account-dashboard-v24-4-60.js?v=25.0.3","sinjira-account-dashboard-v24-4-60.js?v=24.4.60"),
            "catalogue littérature masque rôle non résolu":("literature_js","ownerResolved=!ownerResult.error","ownerResolved=true"),
            "lecteur démo revenu à reader_library":("reader_js","from('sinjira_reader_library').select('last_page')","from('reader_library').select('last_page')"),
            "lecteur démo ignore erreur upsert":("reader_js","return {synced:!error,error:error||null}","return {synced:true,error:null}"),
            "lecteur démo annonce toujours synchronisé":("reader_js","sync.synced?`Page ${current} sauvegardée sur cet appareil et synchronisée avec votre compte.`:`Page ${current} sauvegardée sur cet appareil · synchronisation du compte indisponible.`","`Page ${current} sauvegardée sur cet appareil et synchronisée avec votre compte.`"),
            "cache catalogue littérature revenu V25.1.0":("literature_html","sinjira-literature-catalog-v25.js?v=25.1.2","sinjira-literature-catalog-v25.js?v=25.1.0"),
            "cache lecteur démo revenu V19":("demo_html","sinjira-reader.js?v=25.0.3","sinjira-reader.js?v=19.0"),
        }
        for label,(key,old,new) in mutations.items():
            broken=dict(contents)
            if old not in broken.get(key,""):
                fail(f"auto-test: marqueur source absent pour {label}")
            broken[key]=broken[key].replace(old,new,1)
            try:
                validate(broken)
            except ValueError:
                continue
            fail(f"auto-test: dérive non détectée: {label}")
        print(f"OK auto-test compte V25: {len(mutations)}/{len(mutations)} dérives critiques détectées")
        return
    print("OK V25 compte: navigation regroupée sur toutes les pages du compte, achats propres, catalogue créateur et commentaires canoniques validés.")

if __name__ == "__main__":
    main()
