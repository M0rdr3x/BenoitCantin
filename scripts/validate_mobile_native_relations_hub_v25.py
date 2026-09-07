#!/usr/bin/env python3
"""Valide la frontière V25 du hub Relations React Native."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "mobile-native" / "NativeRelationsHub.tsx"
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
ROUTER = ROOT / "mobile-native" / "NativeModuleRouter.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_RELATIONS_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-relations-hub-v25.yml"


def fail(message: str) -> None:
    print(f"ECHEC hub Relations natif V25: {message}", file=sys.stderr)
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

    require("export function NativeRelationsHub({ onOpenPath, onBack }: Props)" in hub,
            "signature minimale du hub absente")
    props = hub.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in (
        "user", "age", "guardian", "minor", "parent", "relation", "family", "code", "contact",
        "metadata", "message", "role", "status", "link", "token", "session", "count", "note",
    ):
        forbid(props, marker, f"donnée sensible interdite dans les props: {marker}")

    for marker in (
        "WebView", "SecureStore", "AsyncStorage", "LocalAuthentication", "Notifications", "Clipboard", "expo-",
        "supabase", "fetch(", "XMLHttpRequest", "rpc(", "/rest/v1/", "/functions/v1/", "localStorage",
        "service_role", "SERVICE_ROLE", "access_token", "refresh_token", "FormData",
    ):
        forbid(hub, marker, f"capacité interdite dans le hub: {marker}")

    for path in (
        "/compte/relations.html?surface=web",
        "/compte/securite.html",
        "/compte/vie-privee.html",
    ):
        require(path in hub, f"destination attendue absente: {path}")

    for marker in (
        "aucune relation familiale, note privée, tranche d’âge, autorisation parentale, code à usage unique, lien de supervision ou métadonnée de contact",
        "Aucun graphe familial local",
        "Le serveur décide des outils disponibles",
        "Aucun code n’est créé, lu ou mémorisé ici",
        "Aucune relation tuteur–mineur n’est copiée",
        "La supervision protège sans ouvrir les messages",
        "L’HUMAIN AVANT TOUT",
        "PROTÉGER SANS SURVEILLER",
    ):
        require(marker in hub, f"frontière explicite absente du hub: {marker}")

    require("import { NativeRelationsHub } from './NativeRelationsHub';" in home,
            "Relations non importé dans l'accueil")
    require("path: '/compte/relations.html'" in home and "setRelationsHubOpen(true);" in home,
            "Accueil ne route pas Relations vers le hub")
    require("import { NativeRelationsHub } from './NativeRelationsHub';" in router,
            "Relations non importé dans le routeur")
    require("'/compte/relations.html'" in router and "<NativeRelationsHub" in router,
            "route Relations native absente")

    for marker in (
        "Le hub natif ne connaît pas la tranche d’âge",
        "ne peut pas :",
        "copier un code dans le presse-papiers",
        "ne liste aucun lien tuteur–mineur",
        "distinctes des liens de supervision vérifiés",
        "L’HUMAIN AVANT TOUT",
        "Protéger sans surveiller",
    ):
        require(marker in doc, f"preuve documentaire manquante: {marker}")

    required_workflow = (
        "python3 scripts/validate_mobile_native_relations_hub_v25.py",
        "python3 scripts/validate_global_safety_compliance_v24_4_83.py",
        "python3 scripts/validate_data_control_v24_4_69.py",
        "python3 scripts/validate_mobile_native_route_dispatch_v25.py",
        "python3 scripts/validate_mobile_native_home_hub_v25.py",
        "python3 scripts/validate_mobile_native_security_hub_v25.py",
        "python3 scripts/validate_mobile_native_privacy_hub_v25.py",
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

    print("OK hub Relations natif V25: navigation seulement, aucune relation, tranche d'âge, supervision ou code local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
