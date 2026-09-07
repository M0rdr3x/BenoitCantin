#!/usr/bin/env python3
"""Valide le graphe de destinations déclaré par les hubs React Native SINJIRA V25."""

from pathlib import Path
from urllib.parse import parse_qsl, urlsplit
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "mobile-native"
ACCOUNT_DIR = ROOT / "compte"
ROUTER = MOBILE / "NativeModuleRouter.tsx"
DOC = MOBILE / "NATIVE_HUB_DESTINATION_CONTRACT_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-hub-destinations-v25.yml"
CENTRAL_WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-route-dispatch-v25.yml"

SENSITIVE_WEB_ONLY = {
    "/compte/registre-personnel.html",
    "/compte/connexion.html",
    "/compte/inscription.html",
    "/compte/mot-de-passe-oublie.html",
    "/compte/reinitialiser-mot-de-passe.html",
    "/compte/mfa.html",
    "/compte/signaler-deces.html",
}

SECURITY_PATH = "/compte/securite.html"
APPROVED_SECURITY_FRAGMENTS = {
    "devices-title",
    "recent-title",
    "travel-title",
    "quick-title",
    "preferences-title",
}

ROUTE_LITERAL = re.compile(r"['\"](/[^'\"\n]+)['\"]")


def fail(message: str) -> None:
    print(f"ECHEC destinations hubs natifs V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def native_routes() -> set[str]:
    router = ROUTER.read_text(encoding="utf-8")
    require("export const NATIVE_MODULE_PATHS = [" in router, "NATIVE_MODULE_PATHS introuvable")
    block = router.split("export const NATIVE_MODULE_PATHS = [", 1)[1].split("] as const;", 1)[0]
    routes = re.findall(r"'(/compte/[^']+\.html)'", block)
    require(routes and len(routes) == len(set(routes)), "liste native vide ou dupliquée")
    return set(routes)


def validate_account_destination(source: str, literal: str, account_pages: set[str], natives: set[str]) -> str:
    parsed = urlsplit(literal)
    route = parsed.path
    require(route in account_pages, f"{source}: page compte inconnue: {literal}")
    require(route not in SENSITIVE_WEB_ONLY,
            f"{source}: surface sensible interdite dans un tableau de destinations natif: {literal}")

    pairs = parse_qsl(parsed.query, keep_blank_values=True)

    if route in natives:
        require(not parsed.fragment,
                f"{source}: une route de sas natif ne doit pas porter de fragment: {literal}")
        if pairs:
            require(pairs == [("surface", "web")],
                    f"{source}: seule la sortie explicite ?surface=web est permise sur une route native: {literal}")
            return "web-explicit"
        return "native"

    if route == SECURITY_PATH:
        require(not pairs, f"{source}: Sécurité n'accepte aucun paramètre de requête dans un hub: {literal}")
        if parsed.fragment:
            require(parsed.fragment in APPROVED_SECURITY_FRAGMENTS,
                    f"{source}: ancre Sécurité non approuvée: {literal}")
            return "security-web-fragment"
        return "security-native"

    fail(f"{source}: page compte hors routeur non approuvée comme destination native: {literal}")
    return "invalid"


def main() -> int:
    for path in (MOBILE, ACCOUNT_DIR, ROUTER, DOC, WORKFLOW, CENTRAL_WORKFLOW):
        require(path.exists(), f"élément manquant: {path.relative_to(ROOT)}")

    account_pages = {f"/compte/{path.name}" for path in ACCOUNT_DIR.glob("*.html") if path.is_file()}
    require(len(account_pages) == 42,
            f"inventaire compte attendu à 42 pages, trouvé {len(account_pages)}")
    natives = native_routes()
    require(len(natives) == 31, f"31 routes natives attendues, trouvé {len(natives)}")

    hub_files = sorted(MOBILE.glob("Native*Hub.tsx"))
    require(len(hub_files) >= 18, f"inventaire de hubs inattendu: {len(hub_files)}")

    counts = {
        "native": 0,
        "web-explicit": 0,
        "security-native": 0,
        "security-web-fragment": 0,
        "public-internal": 0,
    }
    unique_literals: set[tuple[str, str]] = set()

    for hub in hub_files:
        text = hub.read_text(encoding="utf-8")
        literals = ROUTE_LITERAL.findall(text)
        require(literals, f"{hub.name}: aucune destination interne littérale détectée")

        for literal in literals:
            key = (hub.name, literal)
            if key in unique_literals:
                continue
            unique_literals.add(key)

            require(not literal.startswith("//"), f"{hub.name}: chemin réseau/protocol-relative interdit: {literal}")
            require("\\" not in literal, f"{hub.name}: antislash interdit dans une destination: {literal}")

            if literal.startswith("/compte/"):
                category = validate_account_destination(hub.name, literal, account_pages, natives)
                counts[category] += 1
                continue

            parsed = urlsplit(literal)
            require(not parsed.scheme and not parsed.netloc,
                    f"{hub.name}: une destination de hub doit rester interne au site: {literal}")
            require(parsed.path.startswith("/"), f"{hub.name}: chemin interne absolu attendu: {literal}")
            counts["public-internal"] += 1

    require(counts["native"] > 0, "aucune transition de sas natif détectée")
    require(counts["web-explicit"] > 0, "aucune sortie Web explicite détectée")
    require(counts["security-native"] > 0, "aucune transition vers le hub Sécurité détectée")
    require(counts["security-web-fragment"] >= 5,
            "les cinq ancres Web Sécurité doivent rester visibles dans le graphe")

    docs = DOC.read_text(encoding="utf-8").casefold()
    for marker in (
        "l’humain avant tout",
        "protéger sans surveiller",
        "surface=web",
        "registre personnel",
        "authentification et mfa",
        "signalement de décès",
        "cinq ancres sécurité",
        "aucune destination externe",
        "42 pages",
        "31 routes natives",
    ):
        require(marker in docs, f"preuve documentaire manquante: {marker}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    central = CENTRAL_WORKFLOW.read_text(encoding="utf-8")
    for marker in (
        "mobile-native/Native*Hub.tsx",
        "python3 scripts/validate_mobile_native_hub_destinations_v25.py",
        "python3 scripts/validate_mobile_native_account_route_classification_v25.py",
        "python3 scripts/validate_mobile_native_intent_routing_v25.py",
        "python3 scripts/validate_mobile_navigation_boundary_v25.py",
        "python3 scripts/validate_no_committed_secrets.py",
        "npm run validate:vault",
        "npm run typecheck",
    ):
        require(marker in workflow, f"preuve CI dédiée manquante: {marker}")

    for marker in (
        "mobile-native/NATIVE_HUB_DESTINATION_CONTRACT_V25.md",
        "scripts/validate_mobile_native_hub_destinations_v25.py",
        "python3 scripts/validate_mobile_native_hub_destinations_v25.py",
        ".github/workflows/sinjira-mobile-native-hub-destinations-v25.yml",
    ):
        require(marker in central, f"rechaînage central manquant: {marker}")

    for checked, label in ((workflow, "dédié"), (central, "central")):
        lowered = checked.casefold()
        for marker in ("environment: production", "supabase_access_token", "${{ secrets.", "supabase start", "supabase db"):
            require(marker.casefold() not in lowered,
                    f"production/secret interdit dans workflow {label}: {marker}")

    print(
        "OK destinations hubs natifs V25: "
        f"{len(hub_files)} hubs contrôlés; "
        f"{counts['native']} transitions natives; "
        f"{counts['web-explicit']} sorties Web explicites; "
        f"{counts['security-web-fragment']} ancres Sécurité; "
        "surfaces Registre/auth/MFA/décès exclues."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
