#!/usr/bin/env python3
"""Valide la classification exhaustive V25 des pages compte/*.html."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT_DIR = ROOT / "compte"
APP = ROOT / "mobile-native" / "App.tsx"
ROUTER = ROOT / "mobile-native" / "NativeModuleRouter.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_ACCOUNT_ROUTE_CLASSIFICATION_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-account-route-classification-v25.yml"
CENTRAL_WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-route-dispatch-v25.yml"

NATIVE_MODULE = {
    "/compte/messages.html",
    "/compte/messages-reels.html",
    "/compte/messages-personnage.html",
    "/compte/rencontres.html",
    "/compte/emploi.html",
    "/compte/bibliotheque.html",
    "/compte/mes-lectures.html",
    "/compte/documents.html",
    "/compte/playtests.html",
    "/compte/mes-parties.html",
    "/compte/contributions.html",
    "/compte/communaute.html",
    "/compte/mes-commentaires.html",
    "/compte/blocages.html",
    "/compte/regles-communaute.html",
    "/compte/moderation.html",
    "/compte/reseau-personnage.html",
    "/compte/relations.html",
    "/compte/mes-achats.html",
    "/compte/marche.html",
    "/compte/jetons.html",
    "/compte/licences.html",
    "/compte/monde-parallele.html",
    "/compte/mon-ia.html",
    "/compte/histoire-de-vie.html",
    "/compte/mon-personnage.html",
    "/compte/mes-personnages.html",
    "/compte/notifications.html",
    "/compte/profil.html",
    "/compte/vie-privee.html",
    "/compte/parametres.html",
}

WEB_ACCOUNT_HOME = {"/compte/index.html"}
DEDICATED_SECURITY = {"/compte/securite.html"}
GUARDED_VAULT = {"/compte/registre-personnel.html"}
WEB_AUTH_MFA = {
    "/compte/connexion.html",
    "/compte/inscription.html",
    "/compte/mot-de-passe-oublie.html",
    "/compte/reinitialiser-mot-de-passe.html",
    "/compte/mfa.html",
}
WEB_DEATH_PROCEDURE = {"/compte/signaler-deces.html"}
WEB_CONTEXTUAL_INFO = {
    "/compte/projet.html",
    "/compte/confidentialite-joueur.html",
}

CATEGORIES = {
    "native_module": NATIVE_MODULE,
    "web_account_home": WEB_ACCOUNT_HOME,
    "dedicated_security": DEDICATED_SECURITY,
    "guarded_vault": GUARDED_VAULT,
    "web_auth_mfa": WEB_AUTH_MFA,
    "web_death_procedure": WEB_DEATH_PROCEDURE,
    "web_contextual_info": WEB_CONTEXTUAL_INFO,
}


def fail(message: str) -> None:
    print(f"ECHEC classification routes compte V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> int:
    for path in (ACCOUNT_DIR, APP, ROUTER, DOC, WORKFLOW, CENTRAL_WORKFLOW):
        require(path.exists(), f"élément manquant: {path.relative_to(ROOT)}")

    actual_pages = {f"/compte/{path.name}" for path in ACCOUNT_DIR.glob("*.html") if path.is_file()}
    require(len(actual_pages) == 42,
            f"inventaire compte attendu à 42 pages, trouvé {len(actual_pages)}; toute nouvelle page doit être classifiée explicitement")

    seen: dict[str, str] = {}
    for category, routes in CATEGORIES.items():
        for route in routes:
            previous = seen.get(route)
            require(previous is None, f"route classée deux fois: {route} ({previous}, {category})")
            seen[route] = category

    classified = set(seen)
    missing = sorted(actual_pages - classified)
    stale = sorted(classified - actual_pages)
    require(not missing, f"pages compte non classifiées: {', '.join(missing)}")
    require(not stale, f"routes classifiées sans fichier réel: {', '.join(stale)}")
    require(len(classified) == 42, f"classification attendue à 42 routes, trouvée {len(classified)}")
    require(len(NATIVE_MODULE) == 31, f"classification native attendue à 31 routes, trouvée {len(NATIVE_MODULE)}")

    router = ROUTER.read_text("utf-8")
    require("export const NATIVE_MODULE_PATHS = [" in router and "] as const;" in router,
            "bloc NATIVE_MODULE_PATHS introuvable")
    block = router.split("export const NATIVE_MODULE_PATHS = [", 1)[1].split("] as const;", 1)[0]
    router_paths = re.findall(r"'(/compte/[^']+\.html)'", block)
    require(len(router_paths) == len(set(router_paths)), "doublon dans NATIVE_MODULE_PATHS")
    router_set = set(router_paths)
    missing_native = sorted(NATIVE_MODULE - router_set)
    extra_native = sorted(router_set - NATIVE_MODULE)
    require(not missing_native, f"routes natives classifiées absentes du routeur: {', '.join(missing_native)}")
    require(not extra_native, f"routes du routeur non approuvées par la classification: {', '.join(extra_native)}")

    for category in (WEB_ACCOUNT_HOME, DEDICATED_SECURITY, GUARDED_VAULT, WEB_AUTH_MFA, WEB_DEATH_PROCEDURE, WEB_CONTEXTUAL_INFO):
        for route in category:
            require(route not in router_set, f"route volontairement hors module ajoutée au routeur: {route}")

    app = APP.read_text("utf-8")
    for marker in (
        "const ACCOUNT_HOME_PATH = '/compte/index.html';",
        "const VAULT_PATH = '/compte/registre-personnel.html';",
        "const VAULT_LOCAL_GATE_MS = 90_000;",
        "promptMessage: 'Ouvrir mon Registre personnel'",
        "if (isVaultUrl(url) && Date.now() >= vaultLocalGateUntilRef.current)",
        "const approved = await requestVaultLocalGate();",
        "{ label: 'Sécurité', path: '/compte/securite.html' }",
        "if (item.label === 'Sécurité')",
        "setNativeSecurityOpen(true);",
        "parsed.pathname === '/app/'",
        "<NativeHomeHub",
        "<NativeSecurityHub",
    ):
        require(marker in app, f"frontière spéciale App.tsx absente: {marker}")

    doc = DOC.read_text("utf-8")
    doc_fold = doc.casefold()
    for route in sorted(classified):
        require(route in doc, f"route absente de la documentation de classification: {route}")
    for marker in (
        "42 pages html",
        "31 routes de sas",
        "accueil web de repli",
        "sécurité dédiée hors routeur",
        "registre personnel web gardé",
        "authentification et mfa web",
        "procédure décès web sensible",
        "pages web contextuelles ou informatives",
        "révision humaine obligatoire",
        "aucune page n’est laissée",
        "protéger sans surveiller",
        "l’humain avant tout",
    ):
        require(marker in doc_fold, f"preuve documentaire manquante: {marker}")

    workflow = WORKFLOW.read_text("utf-8")
    central_workflow = CENTRAL_WORKFLOW.read_text("utf-8")
    required_workflow = (
        "compte/*.html",
        "python3 scripts/validate_mobile_native_account_route_classification_v25.py",
        "python3 scripts/validate_mobile_native_route_dispatch_v25.py",
        "python3 scripts/validate_mobile_native_secondary_route_aliases_v25.py",
        "python3 scripts/validate_mobile_native_home_hub_v25.py",
        "python3 scripts/validate_mobile_native_security_hub_v25.py",
        "python3 scripts/validate_mobile_navigation_boundary_v25.py",
        "python3 scripts/validate_mobile_safe_share_v25.py",
        "python3 scripts/validate_device_challenge_client_boundary.py",
        "python3 scripts/validate_no_committed_secrets.py",
        "npm run validate:vault",
        "npm run typecheck",
    )
    for marker in required_workflow:
        require(marker in workflow, f"preuve CI classification manquante: {marker}")

    for marker in (
        "compte/*.html",
        "mobile-native/NATIVE_ACCOUNT_ROUTE_CLASSIFICATION_V25.md",
        "scripts/validate_mobile_native_account_route_classification_v25.py",
        "python3 scripts/validate_mobile_native_account_route_classification_v25.py",
    ):
        require(marker in central_workflow, f"rechaînage central manquant: {marker}")

    for checked, label in ((workflow, "classification"), (central_workflow, "central")):
        lowered = checked.lower()
        for marker in ("environment: production", "supabase_access_token", "${{ secrets.", "supabase start", "supabase db"):
            require(marker.lower() not in lowered, f"production/secret interdit dans workflow {label}: {marker}")

    print("OK classification routes compte V25: 42/42 pages classifiées; 31 routes natives exactes; surfaces sensibles explicitement hors routeur.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
