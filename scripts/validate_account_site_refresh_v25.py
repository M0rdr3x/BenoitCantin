#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT_DIR = ROOT / "compte"

FILES = {
    "migration": ROOT / "supabase/migrations/20260919090000_sinjira_v25_account_content_hub.sql",
    "project_owner_migration": ROOT / "supabase/migrations/20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql",
    "library_html": ROOT / "compte/bibliotheque.html",
    "library_js": ROOT / "assets/js/sinjira-library-v24-4-61.js",
    "secondary_library_js": ROOT / "assets/js/sinjira-library.js",
    "purchases_html": ROOT / "compte/mes-achats.html",
    "purchases_js": ROOT / "assets/js/sinjira-purchases-v25.js",
    "profile_html": ROOT / "compte/profil.html",
    "account_js": ROOT / "assets/js/sinjira-account.js",
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
    libh = compact(contents["library_html"])
    libj = compact(contents["library_js"])
    secondary_library = compact(contents["secondary_library_js"])
    ph = compact(contents["purchases_html"])
    pj = compact(contents["purchases_js"])
    prof = compact(contents["profile_html"])
    acc = compact(contents["account_js"])
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

    for marker in ("data-library-games", "data-library-novels", "data-library-other"):
        if marker not in libh:
            fail(f"bibliothèque: séparation manquante: {marker}")
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
    if "issinjiraowner" in secondary_library:
        fail("bibliothèque secondaire: rôle créateur encore déduit côté navigateur")
    if "s.rpc('is_sinjira_owner',{p_user_id:user.id})" not in contents["secondary_library_js"]:
        fail("bibliothèque secondaire: RPC serveur is_sinjira_owner absent")
    if "assets/js/sinjira-library.js" not in workflow:
        fail("CI compte: module bibliothèque secondaire non surveillé")

    for marker in ("data-purchase-history", "data-purchase-entitlements", "data-creator-portfolio"):
        if marker not in ph:
            fail(f"achats: section manquante: {marker}")
    if ".eq('user_id',user.id)" not in contents["purchases_js"]:
        fail("achats: lectures propres au compte non bornées")
    if "rendercreatorportfolio" not in pj:
        fail("achats: séparation portefeuille créateur absente")

    if 'name="pseudo"required' not in prof or 'name="email"requiredtype="email"' not in prof:
        fail("profil: pseudo/courriel ne sont pas éditables")
    if "auth.updateuser({email}" not in acc:
        fail("profil: mise à jour sécurisée du courriel absente")
    if "pw.length<12" not in acc or "a.length<12" not in acc:
        fail("authentification: helpers Compte doivent conserver le minimum de 12 caractères")
    if "a.length<10" in acc or "au moins 10 caractères" in acc:
        fail("authentification: ancien minimum 10 caractères encore présent dans le helper Compte")
    if "password.length<12" not in recovery or "au moins12caractères" not in recovery:
        fail("récupération active: minimum 12 caractères absent du script sécurisé")
    if 'minlength="12"' not in contents["reset_html"] or "aumoins12caractères" not in reset_html:
        fail("récupération active: HTML non aligné sur le minimum 12 caractères")
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
    if "appendgroup('bibliothèque',['bibliotheque.html','projet.html','mes-lectures.html','mes-commentaires.html'" not in acc:
        fail("navigation Bibliothèque: routes projet/commentaires non classées")
    if "'regles-communaute.html','regles-communaute-junior.html','moderation.html'" not in acc:
        fail("navigation Communauté: règles/modération non classées")

    for name, content in contents.items():
        if not name.startswith("secondary_"):
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

    if "data-literature-catalog" not in lith or "sinjira-literature-catalog-v25.js?v=25.1.0" not in lith:
        fail("littérature: catalogue dynamique V25 absent")
    if "sinjira_my_novel_catalog" not in contents["literature_js"] or "is_sinjira_owner" not in contents["literature_js"]:
        fail("littérature: catalogue self-only/créateur absent")
    if "from('sinjira_novels')" not in contents["literature_js"]:
        fail("littérature: fallback public anonyme canonique absent")

    if "selectplan(12);" not in test:
        fail("pgTAP contenu: plan(12) absent")
    for marker in (
        "lapolicyprojetsowner-onlyv25existe",
        "unmembrenevoitpasunromanbrouilloncréateur",
        "unmembrenevoitpasunprojetinternecréateur",
        "lecréateurvoit sonprojetinternesansfauxachat".replace(" ", ""),
        "unmembrevoitencoreunproduitinactifliéàsonentitlement",
        "unmembrevoitencoreunproduitinactifprésentdanssapropcommande".replace("propcommande", "proprecommande"),
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
            "policy projets créateur retirée":("project_owner_migration","projects_owner_catalog_read_v25","projects_owner_catalog_missing"),
            "migration projets créateur hors paths CI":("workflow","supabase/migrations/20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql","supabase/migrations/projects-owner-missing.sql"),
            "full_access roman privé contourné":("library_js","const fullAccess=Boolean(novel.full_access);","const fullAccess=true;"),
            "ancien module bibliothèque rechargé":("library_html","<script src=\"../assets/js/sinjira-library-v24-4-61.js?v=25.1.0\" type=\"module\"></script>","<script src=\"../assets/js/sinjira-library.js?v=24.1\" type=\"module\"></script>"),
            "rôle créateur secondaire revenu côté client":("secondary_library_js","s.rpc('is_sinjira_owner',{p_user_id:user.id})","Promise.resolve({data:false,error:null})"),
            "module bibliothèque secondaire hors paths CI":("workflow","assets/js/sinjira-library.js","assets/js/sinjira-library-missing.js"),
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
