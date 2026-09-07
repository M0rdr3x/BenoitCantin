#!/usr/bin/env python3
"""Valide la frontière V25 du hub Bibliothèque React Native."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "mobile-native" / "NativeLibraryHub.tsx"
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
ROUTER = ROOT / "mobile-native" / "NativeModuleRouter.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_LIBRARY_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-library-hub-v25.yml"


def fail(message: str) -> None:
    print(f"ECHEC hub Bibliothèque natif V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def main() -> int:
    for path in (HUB, HOME, ROUTER, DOC, WORKFLOW):
        require(path.is_file(), f"fichier manquant: {path.relative_to(ROOT)}")

    hub = HUB.read_text("utf-8")
    home = HOME.read_text("utf-8")
    router = ROUTER.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeLibraryHub({ onOpenPath, onBack }: Props)" in hub,
            "signature minimale du hub absente")
    props = hub.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in ("user", "role", "entitlement", "license", "progress", "project", "document", "request", "count", "token", "session"):
        forbid(props, marker, f"donnée utilisateur interdite dans les props: {marker}")

    for marker in (
        "WebView", "SecureStore", "AsyncStorage", "LocalAuthentication", "Notifications", "expo-",
        "supabase", "fetch(", "XMLHttpRequest", "rpc(", "/rest/v1/", "/functions/v1/", "localStorage",
        "service_role", "SERVICE_ROLE", "access_token", "refresh_token", "FormData",
    ):
        forbid(hub, marker, f"capacité interdite dans le hub: {marker}")

    for path in (
        "/compte/bibliotheque.html?surface=web",
        "/compte/mes-lectures.html?surface=web",
        "/compte/licences.html?surface=web",
        "/compte/documents.html?surface=web",
    ):
        require(path in hub, f"destination Web attendue absente: {path}")

    for marker in (
        "aucun rôle, droit d’accès, licence, progression de lecture, demande testeur, document privé ni inventaire de projet",
        "La progression de lecture n’est pas copiée",
        "Aucune demande testeur depuis le natif",
        "Aucun cache d’inventaire privé",
        "Votre bibliothèque n’est pas un profil comportemental",
        "L’HUMAIN AVANT TOUT",
        "PROTÉGER SANS SURVEILLER",
    ):
        require(marker in hub, f"frontière explicite absente du hub: {marker}")

    require("import { NativeLibraryHub } from './NativeLibraryHub';" in home,
            "Bibliothèque non importée dans l'accueil")
    require("path: '/compte/bibliotheque.html'" in home and "setLibraryHubOpen(true);" in home,
            "Accueil ne route pas Bibliothèque vers le hub")
    require("import { NativeLibraryHub } from './NativeLibraryHub';" in router,
            "Bibliothèque non importée dans le routeur")
    require("'/compte/bibliotheque.html'" in router and "<NativeLibraryHub" in router,
            "route Bibliothèque native absente")

    for marker in (
        "rôle propriétaire ou administrateur", "progression de lecture", "demande testeur",
        "ne doit pas devenir un profil comportemental", "L’HUMAIN AVANT TOUT", "Protéger sans surveiller",
    ):
        require(marker in doc, f"preuve documentaire manquante: {marker}")

    required_workflow = (
        "python3 scripts/validate_mobile_native_library_hub_v25.py",
        "python3 scripts/validate_mobile_native_route_dispatch_v25.py",
        "python3 scripts/validate_mobile_native_home_hub_v25.py",
        "python3 scripts/validate_mobile_navigation_boundary_v25.py",
        "python3 scripts/validate_mobile_safe_share_v25.py",
        "python3 scripts/validate_device_challenge_client_boundary.py",
        "python3 scripts/validate_no_committed_secrets.py",
        "npm run validate:vault",
        "npm run typecheck",
    )
    for marker in required_workflow:
        require(marker in workflow, f"preuve CI manquante: {marker}")

    for marker in ("environment: production", "SUPABASE_ACCESS_TOKEN", "${{ secrets.", "supabase start", "supabase db"):
        forbid(workflow, marker, f"production/secret interdit dans ce workflow: {marker}")

    print("OK hub Bibliothèque natif V25: navigation seulement, aucun droit, rôle, progrès, licence ou demande locale.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
