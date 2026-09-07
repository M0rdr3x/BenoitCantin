#!/usr/bin/env python3
"""Valide la frontière V25 du hub Réseau personnage React Native."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "mobile-native" / "NativeCharacterNetworkHub.tsx"
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
ROUTER = ROOT / "mobile-native" / "NativeModuleRouter.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_CHARACTER_NETWORK_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-character-network-hub-v25.yml"
ROUTE_GUARD = ROOT / "scripts" / "validate_mobile_native_route_dispatch_v25.py"
PRIVACY_GUARD = ROOT / "scripts" / "validate_character_network_owner_privacy_v25.py"


def fail(message: str) -> None:
    print(f"ECHEC hub Réseau personnage natif V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def main() -> int:
    for path in (HUB, HOME, ROUTER, DOC, WORKFLOW, ROUTE_GUARD, PRIVACY_GUARD):
        require(path.is_file(), f"fichier manquant: {path.relative_to(ROOT)}")

    hub = HUB.read_text("utf-8")
    home = HOME.read_text("utf-8")
    router = ROUTER.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")
    route_guard = ROUTE_GUARD.read_text("utf-8")

    require("export function NativeCharacterNetworkHub({ onOpenPath, onBack }: Props)" in hub,
            "signature minimale du hub absente")
    props = hub.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in (
        "user", "email", "account", "profile", "character", "identity", "owner", "role", "post",
        "comment", "like", "follow", "group", "member", "block", "report", "moderation", "content",
        "count", "history", "token", "payload",
    ):
        forbid(props, marker, f"donnée sociale interdite dans les props: {marker}")

    for marker in (
        "WebView", "SecureStore", "AsyncStorage", "LocalAuthentication", "Notifications", "expo-",
        "supabase", "fetch(", "XMLHttpRequest", "rpc(", "/rest/v1/", "/functions/v1/", "localStorage",
        "service_role", "SERVICE_ROLE", "access_token", "refresh_token", "FormData",
        "is_sinjira_owner", "ensure_sinjira_owner_character", "character_social_profiles",
        "social_character_posts", "social_character_comments", "social_character_likes",
    ):
        forbid(hub, marker, f"capacité ou donnée interdite dans le hub: {marker}")

    for path in (
        "/compte/reseau-personnage.html?surface=web",
        "/compte/communaute.html?surface=web",
        "/compte/mon-personnage.html?surface=web",
        "/compte/securite.html",
    ):
        require(path in hub, f"destination attendue absente: {path}")

    for marker in (
        "aucune identité réelle, identité de personnage, publication, commentaire, réaction, relation sociale, groupe, blocage, signalement ni rôle propriétaire",
        "Aucun graphe social dans le natif",
        "Le compte réel reste distinct du personnage",
        "Aucune décision narrative locale",
        "Aucun signalement ou blocage reconstruit ici",
        "L’HUMAIN AVANT TOUT",
        "PROTÉGER SANS SURVEILLER",
    ):
        require(marker in hub, f"frontière explicite absente du hub: {marker}")

    require("import { NativeCharacterNetworkHub } from './NativeCharacterNetworkHub';" in home,
            "Réseau personnage non importé dans l'accueil")
    require("path: '/compte/reseau-personnage.html'" in home and "setCharacterNetworkHubOpen(true);" in home,
            "Accueil ne route pas Réseau personnage vers le hub")
    require("const [characterNetworkHubOpen, setCharacterNetworkHubOpen] = useState(false);" in home,
            "état du hub Réseau personnage absent de l'accueil")
    require("<NativeCharacterNetworkHub" in home and "onBack={() => setCharacterNetworkHubOpen(false)}" in home,
            "rendu local Réseau personnage absent de l'accueil")

    require("import { NativeCharacterNetworkHub } from './NativeCharacterNetworkHub';" in router,
            "Réseau personnage non importé dans le routeur")
    require("'/compte/reseau-personnage.html'" in router and "<NativeCharacterNetworkHub" in router,
            "route Réseau personnage native absente")

    doc_fold = doc.casefold()
    for marker in (
        "aucun graphe social",
        "aucune adresse courriel réelle",
        "n’appelle ni `is_sinjira_owner` ni `ensure_sinjira_owner_character`",
        "rôle-play",
        "source de vérité",
        "aucune écriture supabase",
        "protéger sans surveiller",
        "l’humain avant tout",
    ):
        require(marker in doc_fold, f"preuve documentaire manquante: {marker}")

    require("CHARACTER_NETWORK_GUARD" in route_guard and '"/compte/reseau-personnage.html"' in route_guard,
            "garde central non étendu à Réseau personnage")
    require('"NativeCharacterNetworkHub"' in route_guard,
            "composant Réseau personnage absent du garde central")
    require("validate_mobile_native_character_network_hub_v25.py" in route_guard,
            "preuve CI Réseau personnage absente du garde central")

    required_workflow = (
        "python3 scripts/validate_mobile_native_character_network_hub_v25.py",
        "python3 scripts/validate_character_network_owner_privacy_v25.py",
        "python3 scripts/validate_mobile_native_route_dispatch_v25.py",
        "python3 scripts/validate_mobile_native_home_hub_v25.py",
        "python3 scripts/validate_mobile_native_community_hub_v25.py",
        "python3 scripts/validate_mobile_native_character_hub_v25.py",
        "python3 scripts/validate_mobile_navigation_boundary_v25.py",
        "python3 scripts/validate_mobile_safe_share_v25.py",
        "python3 scripts/validate_device_challenge_client_boundary.py",
        "python3 scripts/validate_no_committed_secrets.py",
        "npm run validate:vault",
        "npm run typecheck",
    )
    for marker in required_workflow:
        require(marker in workflow, f"preuve CI manquante: {marker}")

    workflow_lower = workflow.lower()
    for marker in ("environment: production", "supabase_access_token", "${{ secrets.", "supabase start", "supabase db"):
        forbid(workflow_lower, marker.lower(), f"production/secret interdit dans ce workflow: {marker}")

    print("OK hub Réseau personnage natif V25: navigation seulement, aucune identité réelle ni donnée sociale locale.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
