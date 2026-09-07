#!/usr/bin/env python3
"""Valide la frontière V25 du hub Communauté React Native."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "mobile-native" / "NativeCommunityHub.tsx"
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
ROUTER = ROOT / "mobile-native" / "NativeModuleRouter.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_COMMUNITY_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-community-hub-v25.yml"
COMMUNITY_GUARD = ROOT / "scripts" / "validate_community_safety_v24_4_79.py"
PUBLIC_COMMUNITY_GUARD = ROOT / "scripts" / "validate_public_community_v24_4_80.py"


def fail(message: str) -> None:
    print(f"ECHEC hub Communauté natif V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def main() -> int:
    for path in (HUB, HOME, ROUTER, DOC, WORKFLOW, COMMUNITY_GUARD, PUBLIC_COMMUNITY_GUARD):
        require(path.is_file(), f"fichier manquant: {path.relative_to(ROOT)}")

    hub = HUB.read_text("utf-8")
    home = HOME.read_text("utf-8")
    router = ROUTER.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeCommunityHub({ onOpenPath, onBack }: Props)" in hub,
            "signature minimale du hub absente")
    props = hub.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in (
        "user", "profile", "pseudo", "avatar", "post", "comment", "reaction", "like", "report",
        "block", "moderation", "rules", "identity", "character", "token", "session", "count", "content",
    ):
        forbid(props, marker, f"donnée sociale interdite dans les props: {marker}")

    for marker in (
        "WebView", "SecureStore", "AsyncStorage", "LocalAuthentication", "Notifications", "expo-",
        "supabase", "fetch(", "XMLHttpRequest", "rpc(", "/rest/v1/", "/functions/v1/", "localStorage",
        "service_role", "SERVICE_ROLE", "access_token", "refresh_token", "FormData",
    ):
        forbid(hub, marker, f"capacité interdite dans le hub: {marker}")

    for path in (
        "/compte/communaute.html?surface=web",
        "/compte/reseau-personnage.html?surface=web",
        "/compte/regles-communaute.html?surface=web",
        "/compte/securite.html",
    ):
        require(path in hub, f"destination Web attendue absente: {path}")

    for marker in (
        "aucun profil communautaire, pseudo, publication, commentaire, réaction, blocage, signalement, état de modération ni acceptation des règles",
        "Aucun fil social dans le natif",
        "Profil réel et personnage ne sont jamais fusionnés ici",
        "L’acceptation reste vérifiée côté Web",
        "Aucun signalement ni blocage n’est reconstruit localement",
        "Une communauté n’est pas un graphe à surveiller",
        "L’HUMAIN AVANT TOUT",
        "PROTÉGER SANS SURVEILLER",
    ):
        require(marker in hub, f"frontière explicite absente du hub: {marker}")

    require("import { NativeCommunityHub } from './NativeCommunityHub';" in home,
            "Communauté non importée dans l'accueil")
    require("path: '/compte/communaute.html'" in home and "setCommunityHubOpen(true);" in home,
            "Accueil ne route pas Communauté vers le hub")
    require("import { NativeCommunityHub } from './NativeCommunityHub';" in router,
            "Communauté non importée dans le routeur")
    require("'/compte/communaute.html'" in router and "<NativeCommunityHub" in router,
            "route Communauté native absente")

    for marker in (
        "Deux identités séparées", "Le hub ne sait pas si l’utilisateur a accepté", "ne peut pas enregistrer cette acceptation",
        "signaler ou bloquer", "Pas de graphe comportemental", "L’HUMAIN AVANT TOUT", "Protéger sans surveiller",
    ):
        require(marker in doc, f"preuve documentaire manquante: {marker}")

    required_workflow = (
        "python3 scripts/validate_mobile_native_community_hub_v25.py",
        "python3 scripts/validate_community_safety_v24_4_79.py",
        "python3 scripts/validate_public_community_v24_4_80.py",
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

    print("OK hub Communauté natif V25: navigation seulement, aucune identité, contenu, règle ou modération locale.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
