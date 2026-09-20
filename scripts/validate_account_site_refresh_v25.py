#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT_DIR = ROOT / "compte"

FILES = {
    "migration": ROOT / "supabase/migrations/20260919090000_sinjira_v25_account_content_hub.sql",
    "project_owner_migration": ROOT / "supabase/migrations/20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql",
    "browser_privileges_migration": ROOT / "supabase/migrations/20260919130000_sinjira_v25_account_catalog_browser_privileges.sql",
    "library_html": ROOT / "compte/bibliotheque.html",
    "library_js": ROOT / "assets/js/sinjira-library-v24-4-61.js",
    "secondary_library_js": ROOT / "assets/js/sinjira-library.js",
    "purchases_html": ROOT / "compte/mes-achats.html",
    "purchases_js": ROOT / "assets/js/sinjira-purchases-v25.js",
    "profile_html": ROOT / "compte/profil.html",
    "account_js": ROOT / "assets/js/sinjira-account.js",
    "dashboard_js": ROOT / "assets/js/sinjira-account-dashboard-v24-4-60.js",
    "account_css": ROOT / "assets/css/sinjira-player-account.css",
    "recovery_js": ROOT / "assets/js/sinjira-recovery-v24-4-99.js",
    "signup_html": ROOT / "compte/inscription.html",
    "login_html": ROOT / "compte/connexion.html",
    "forgot_html": ROOT / "compte/mot-de-passe-oublie.html",
    "reset_html": ROOT / "compte/reinitialiser-mot-de-passe.html",
    "mfa_html": ROOT / "compte/mfa.html",
    "workflow": ROOT / ".github/workflows/sinjira-account-content-hub-v25.yml",
    "reader_js": ROOT / "assets/js/sinjira-reader.js",
    "comments_js": ROOT / "assets/js/sinjira-account-v18.js",
    "comments_html": ROOT / "compte/mes-commentaires.html",
    "literature_html": ROOT / "projets/sinjira/romans/index.html",
    "demo_html": ROOT / "projets/sinjira/romans/lire-demo.html",
    "literature_js": ROOT / "assets/js/sinjira-literature-catalog-v25.js",
    "test": ROOT / "supabase/tests/account_content_hub_v25.test.sql",
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
    browser_privileges = compact(contents["browser_privileges_migration"])
    libh = compact(contents["library_html"])
    libj = compact(contents["library_js"])
    secondary_library = compact(contents["secondary_library_js"])
    ph = compact(contents["purchases_html"])
    pj = compact(contents["purchases_js"])
    prof = compact(contents["profile_html"])
    acc = compact(contents["account_js"])
    dashboard = compact(contents["dashboard_js"])
    account_css = compact(contents["account_css"])
    recovery = compact(contents["recovery_js"])
    signup_html = compact(contents["signup_html"])
    login_html = compact(contents["login_html"])
    forgot_html = compact(contents["forgot_html"])
    reset_html = compact(contents["reset_html"])
    mfa_html = compact(contents["mfa_html"])
    workflow = contents["workflow"]
    reader = compact(contents["reader_js"])
    comments = compact(contents["comments_js"])
    comment_html = compact(contents["comments_html"])
    lith = compact(contents["literature_html"])
    litj = compact(contents["literature_js"])
    test = compact(contents["test"])

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

    if "supabase/migrations/20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql" not in contents["workflow"]:
        fail("CI compte: migration visibilité projets créateur non surveillée")
    if "supabase/migrations/20260919123000_sinjira_v25_public_rpc_boundary.sql" not in contents["workflow"]:
        fail("CI compte: frontière RPC V25 finale non surveillée")
    if "supabase/migrations/20260919130000_sinjira_v25_account_catalog_browser_privileges.sql" not in contents["workflow"]:
        fail("CI compte: convergence des privilèges catalogue navigateur non surveillée")

    for marker in (
        "createschemaifnotexistssinjira_catalog_internal",
        "alterfunctionpublic.project_access_rank(uuid,uuid)setschemasinjira_catalog_internal",
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

    for marker in ("data-library-games", "data-library-novels", "data-library-other"):
        if marker not in libh:
            fail(f"bibliothèque: séparation manquante: {marker}")
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
    if "sinjira_my_novel_catalog" not in contents["library_js"]:
        fail("bibliothèque: catalogue roman self-only canonique absent")
    if "functionrendernovels" not in libj:
        fail("bibliothèque: rendu romans absent")
    if "constfullaccess=boolean(novel.full_access);" not in libj or "fullaccess?" not in libj:
        fail("bibliothèque: intégrale privée non liée au full_access canonique")
    if "data-private-book-download" in libj or "functionbookactions" in libj or "functiondownloadprivatebook" in libj:
        fail("bibliothèque: action privée dupliquée hors catalogue roman")
    if "accèsauteur" in libj:
        fail("bibliothèque: rôle créateur encore présenté comme droit numérique privé")
    for marker in (
        "constrequiresproductright=project.slug==='fracture-du-reseau-mere';",
        "constproductright=isowner||entitledproductslugs.has(project.slug);",
        "droitnumériqueactif",
        "droitdejeurequis",
        "droitdejeunonvérifié",
        "project.play_path&&canplay",
        "entitlements,!entitlementsresult.error",
        "activerunelicence",
        "vérifiermeslicences",
    ):
        if marker not in libj:
            fail(f"bibliothèque: droit de jeu Fracture mal distingué de la visibilité projet: {marker}")
    if "issinjiraowner" in secondary_library:
        fail("bibliothèque secondaire: rôle créateur encore déduit côté navigateur")
    if "s.rpc('is_sinjira_owner',{p_user_id:user.id})" not in contents["secondary_library_js"]:
        fail("bibliothèque secondaire: RPC serveur is_sinjira_owner absent")
    for marker in (
        "p.visibility==='restricted'?'accèsrestreint':p.visibility==='account'?'inclusaveclecompte':'pagepublique'",
        "rolechip=owner?'propriétaire':a?.access_level==='tester'?'testeur':''",
        "propriétaire·cataloguecomplet",
        "lerôlepropriétairen’apaspuêtreconfirmé.aucunaccèspropriétairesupplémentairen’estsupposé.",
        "asyncfunctionresolvefractureright(projects,s)",
        "constfractureright=awaitresolvefractureright(projects,s);",
        "constresult=awaits.rpc('has_sinjira_product',{p_product_slug:'fracture-du-reseau-mere'});",
        "return{active:!result.error&&result.data===true,verified:!result.error};",
        "if(error)throwerror;",
        "if(pr.error||dr.error||rr.error)",
        "bibliothèquetemporairementindisponible",
        "if(accesserror&&!childmode)",
        "if(docserror)",
        "if(playtesterror)",
        "if(pr.error||mr.error)",
        "aucunenouvelleactionn’estproposée",
        "constcanplay=!licensedgame||owner||(fractureright.verified&&fractureright.active);",
        "licenseaction=licensedgame&&!owner&&!fractureright.active",
        "licensedgame=p.slug==='fracture-du-reseau-mere'",
        "s.rpc('has_sinjira_product',{p_product_slug:p.slug})",
        "droitdejeunonvérifié",
        "droitnumériqueactif",
        "droitdejeurequis",
        "p.play_path&&canplay",
    ):
        if marker not in secondary_library:
            fail(f"bibliothèque secondaire: sémantique projet incohérente: {marker}")
    if "assets/js/sinjira-library.js" not in workflow:
        fail("CI compte: module bibliothèque secondaire non surveillé")
    for name in ("secondary_project","secondary_documents"):
        if "sinjira-library.js?v=25.1.1" not in contents[name]:
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
    if "sinjira-purchases-v25.js?v=25.0.2" not in contents["purchases_html"]:
        fail("achats: cache module V25.0.2 absent")

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
    if "catalogresolved=!all.error" not in dashboard or "cataloguecomplettemporairementindisponible" not in dashboard:
        fail("tableau de bord: échec du catalogue complet owner/admin non signalé")
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
    if "assets/js/sinjira-account-dashboard-v24-4-60.js" not in workflow:
        fail("CI compte: module Dashboard dédié non surveillé")
    if "sinjira-account-dashboard-v24-4-60.js?v=25.0.2" not in contents["account_page:index.html"]:
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
    if "assets/js/sinjira-recovery-v24-4-99.js" not in workflow:
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
        if "sinjira-account.js?v=25.0.1" not in content:
            fail(f"navigation secondaire: cache JS V25 absent dans {name}")
        if "sinjira-player-account.css?v=25.0.1" not in content:
            fail(f"navigation secondaire: cache CSS V25 absent dans {name}")

    for name, content in contents.items():
        if not name.startswith("account_page:"):
            continue
        page_compact=compact(content)
        if 'class="account-nav"' not in page_compact:
            continue
        if "sinjira-account.js?v=25.0.1" not in content:
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
    if "sinjira-account-v18.js?v=25.0.1" not in contents["comments_html"]:
        fail("commentaires: cache client V25 non forcé")

    if "data-literature-catalog" not in lith or "sinjira-literature-catalog-v25.js?v=25.1.1" not in lith:
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
    if "sinjira-reader.js?v=25.0.2" not in contents["literature_html"]:
        fail("littérature: cache lecteur V25.0.2 absent")
    if "sinjira-reader.js?v=25.0.2" not in contents["demo_html"]:
        fail("lecteur démo: cache lecteur V25.0.2 absent")

    if "selectplan(41);" not in test:
        fail("pgTAP contenu: plan(41) absent")
    for marker in (
        "lapolicyprojetsowner-onlyv25existe",
        "authenticatedpeutlireprojectssousrls",
        "anonnepeutpaslireproject_access",
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
        "unmembrevoitencoreunproduitinactifliéàsonentitlement",
        "unmembrevoitencoreunproduitinactifprésentdanssapropcommande".replace("propcommande", "proprecommande"),
        "schémainternecatalogueexiste",
        "project_access_rankpublicestunwrappersecurityinvoker",
        "authenticatednepeutpassonderdirectementlerangprojet",
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
            "page compte sans JS V25":("account_page:index.html","sinjira-account.js?v=25.0.1","sinjira-account.js?v=24.1"),
            "modération renvoyée vers Plus":("account_js","'regles-communaute.html','regles-communaute-junior.html','moderation.html'","'regles-communaute.html','regles-communaute-junior.html'"),
            "reset mot de passe revenu à 10":("account_js","a.length<12","a.length<10"),
            "récupération active revenue à 10":("recovery_js","password.length<12","password.length<10"),
            "HTML reset revenu à 10":("reset_html",'minlength="12"','minlength="10"'),
            "script récupération hors paths CI":("workflow","assets/js/sinjira-recovery-v24-4-99.js","assets/js/sinjira-recovery-missing.js"),
            "inscription avec ancien cache CSS":("signup_html","sinjira-player-account.css?v=25.0.1","sinjira-player-account.css?v=24.4.12"),
            "MFA avec ancien cache CSS":("mfa_html","sinjira-player-account.css?v=25.0.1","sinjira-player-account.css?v=24.4.66"),
            "policy projets créateur retirée":("project_owner_migration","create policy projects_owner_catalog_read_v25","create policy projects_owner_catalog_missing"),
            "migration projets créateur hors paths CI":("workflow","supabase/migrations/20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql","supabase/migrations/projects-owner-missing.sql"),
            "migration privilèges catalogue hors paths CI":("workflow","supabase/migrations/20260919130000_sinjira_v25_account_catalog_browser_privileges.sql","supabase/migrations/catalog-browser-privileges-missing.sql"),
            "écriture projet navigateur réouverte":("browser_privileges_migration","grant select on table public.projects to anon, authenticated;","grant select, insert on table public.projects to anon, authenticated;"),
            "preuve RLS access_requests self-only retirée":("test","policyname='requests own insert'","policyname='requests missing insert'"),
            "preuve RLS playtest self-only retirée":("test","policyname='participants own apply'","policyname='participants missing apply'"),
            "full_access roman privé contourné":("library_js","const fullAccess=Boolean(novel.full_access);","const fullAccess=true;"),
            "Fracture jouable sans droit produit":("library_js","project.play_path&&canPlay","project.play_path"),
            "Fracture droit produit forcé":("library_js","const productRight=isOwner||entitledProductSlugs.has(project.slug);","const productRight=true;"),
            "ancien module bibliothèque rechargé":("library_html","<script src=\"../assets/js/sinjira-library-v24-4-61.js?v=25.1.0\" type=\"module\"></script>","<script src=\"../assets/js/sinjira-library.js?v=24.1\" type=\"module\"></script>"),
            "raccourci Mes achats retiré":("library_html",'<a href="mes-achats.html"><strong>Mes achats</strong>','<a href="licences.html"><strong>Mes achats</strong>'),
            "rôle créateur secondaire revenu côté client":("secondary_library_js","s.rpc('is_sinjira_owner',{p_user_id:user.id})","Promise.resolve({data:false,error:null})"),
            "projet public secondaire présenté comme compte":("secondary_library_js","p.visibility==='restricted'?'Accès restreint':p.visibility==='account'?'Inclus avec le compte':'Page publique'","p.visibility==='restricted'?'Accès restreint':'Inclus avec le compte'"),
            "Fracture liste secondaire sans vérification produit":("secondary_library_js","const fractureRight=await resolveFractureRight(projects,s);","const fractureRight={active:true,verified:true};"),
            "RPC Fracture liste secondaire retiré":("secondary_library_js","const result=await s.rpc('has_sinjira_product',{p_product_slug:'fracture-du-reseau-mere'});","const result={data:true,error:null};"),
            "erreur project_access secondaire ignorée":("secondary_library_js","if(error)throw error;","if(error)console.warn(error);"),
            "échec catalogue secondaire masqué":("secondary_library_js","if(pr.error||dr.error||rr.error){","if(false){"),
            "échec candidatures playtest masqué":("secondary_library_js","if(pr.error||mr.error){","if(false){"),
            "Fracture secondaire jouable sans droit":("secondary_library_js","const canPlay=!licensedGame||owner||(fractureRight.verified&&fractureRight.active);","const canPlay=true;"),
            "contrôle Fracture secondaire retiré":("secondary_library_js","s.rpc('has_sinjira_product',{p_product_slug:p.slug})","Promise.resolve({data:true,error:null})"),
            "module bibliothèque secondaire hors paths CI":("workflow","assets/js/sinjira-library.js","assets/js/sinjira-library-missing.js"),
            "cache Projet bibliothèque revenu V24":("secondary_project","sinjira-library.js?v=25.1.1","sinjira-library.js?v=24.1"),
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
            "cache achats revenu V25.0.1":("purchases_html","sinjira-purchases-v25.js?v=25.0.2","sinjira-purchases-v25.js?v=25.0.1"),
            "nom affiché redevenu ambigu":("profile_html","Nom affiché privé","Nom affiché"),
            "compteur romans suivis retiré":("dashboard_js","setText('[data-stat-reader]',count)","setText('[data-stat-reader]',0)"),
            "rôle dashboard supposé côté client":("dashboard_js","s.rpc('is_sinjira_owner',{p_user_id:user.id})","Promise.resolve({data:false,error:null})"),
            "owner retiré du catalogue dashboard":("dashboard_js","if(roleResolved&&(isAdmin||isOwner)){","if(roleResolved&&isAdmin){"),
            "owner rendu dépendant du RPC admin":("dashboard_js","const roleResolved=ownerResolved&&(isOwner||adminResolved);","const roleResolved=ownerResolved&&adminResolved;"),
            "catalogue dashboard déclaré sain à tort":("dashboard_js","catalogResolved=!all.error;","catalogResolved=true;"),
            "erreur accès dashboard masquée":("dashboard_js","const accessResolved=!accessResult.error;","const accessResolved=true;"),
            "bibliothèque dashboard erreur masquée":("dashboard_js","renderLibrary(libraryResult.data||[],!libraryResult.error);","renderLibrary(libraryResult.data||[],true);"),
            "résumé accès dashboard retiré":("dashboard_js","renderAccess(projects,isOwner,isAdmin,roleResolved,catalogResolved,accessResolved);","renderAccess(projects,false,false,true,true,true);"),
            "module Dashboard hors paths CI":("workflow","assets/js/sinjira-account-dashboard-v24-4-60.js","assets/js/sinjira-account-dashboard-missing.js"),
            "cache Dashboard revenu V24":("account_page:index.html","sinjira-account-dashboard-v24-4-60.js?v=25.0.2","sinjira-account-dashboard-v24-4-60.js?v=24.4.60"),
            "catalogue littérature masque rôle non résolu":("literature_js","ownerResolved=!ownerResult.error","ownerResolved=true"),
            "lecteur démo revenu à reader_library":("reader_js","from('sinjira_reader_library').select('last_page')","from('reader_library').select('last_page')"),
            "cache catalogue littérature revenu V25.1.0":("literature_html","sinjira-literature-catalog-v25.js?v=25.1.1","sinjira-literature-catalog-v25.js?v=25.1.0"),
            "cache lecteur démo revenu V19":("demo_html","sinjira-reader.js?v=25.0.2","sinjira-reader.js?v=19.0"),
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
