#!/usr/bin/env python3
"""Valide la frontière V25 du hub Mes parties React Native."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "mobile-native" / "NativeGamesHub.tsx"
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
ROUTER = ROOT / "mobile-native" / "NativeModuleRouter.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_GAMES_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-games-hub-v25.yml"
ROUTE_GUARD = ROOT / "scripts" / "validate_mobile_native_route_dispatch_v25.py"


def fail(message: str) -> None:
    print(f"ECHEC hub Mes parties natif V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def main() -> int:
    for path in (HUB, HOME, ROUTER, DOC, WORKFLOW, ROUTE_GUARD):
        require(path.is_file(), f"fichier manquant: {path.relative_to(ROOT)}")

    hub = HUB.read_text("utf-8")
    home = HOME.read_text("utf-8")
    router = ROUTER.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")
    route_guard = ROUTE_GUARD.read_text("utf-8")

    require("export function NativeGamesHub({ onOpenPath, onBack }: Props)" in hub,
            "signature minimale du hub absente")
    props = hub.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in (
        "user", "session", "game", "party", "code", "status", "player", "sheet", "endgame",
        "save", "file", "import", "export", "mode", "duration", "history", "count", "payload",
    ):
        forbid(props, marker, f"donnée de partie interdite dans les props: {marker}")

    for marker in (
        "WebView", "SecureStore", "AsyncStorage", "LocalAuthentication", "Notifications",
        "DocumentPicker", "expo-document-picker", "FileSystem", "expo-file-system", "Clipboard",
        "Share", "supabase", "fetch(", "XMLHttpRequest", "rpc(", "/rest/v1/", "/functions/v1/",
        "localStorage", "service_role", "SERVICE_ROLE", "access_token", "refresh_token", "FormData",
        "JSON.parse", "new Blob", "URL.createObjectURL",
    ):
        forbid(hub, marker, f"capacité interdite dans le hub: {marker}")

    for path in (
        "/compte/mes-parties.html?surface=web",
        "/compte/bibliotheque.html?surface=web",
        "/projets/sinjira/jeux/",
        "/compte/securite.html",
    ):
        require(path in hub, f"destination attendue absente: {path}")

    for marker in (
        "aucune partie, sauvegarde, code de partie, feuille de joueur, résultat de fin de partie ni fichier JSON",
        "Aucun état de partie local",
        "Les exports volontaires restent Web",
        "Aucune création de partie depuis un fichier natif",
        "Les feuilles de joueur restent hors du natif",
        "Pas de profil de jeu",
        "L’HUMAIN AVANT TOUT",
        "PROTÉGER SANS SURVEILLER",
    ):
        require(marker in hub, f"frontière explicite absente du hub: {marker}")

    require("import { NativeGamesHub } from './NativeGamesHub';" in home,
            "Mes parties non importé dans l'accueil")
    require("path: '/compte/mes-parties.html'" in home and "setGamesHubOpen(true);" in home,
            "Accueil ne route pas Mes parties vers le hub")
    require("const [gamesHubOpen, setGamesHubOpen] = useState(false);" in home,
            "état du hub Mes parties absent de l'accueil")
    require("<NativeGamesHub" in home and "onBack={() => setGamesHubOpen(false)}" in home,
            "rendu local Mes parties absent de l'accueil")

    require("import { NativeGamesHub } from './NativeGamesHub';" in router,
            "Mes parties non importé dans le routeur")
    require("'/compte/mes-parties.html'" in router and "<NativeGamesHub" in router,
            "route Mes parties native absente")

    doc_fold = doc.casefold()
    for marker in (
        "aucune donnée de partie locale",
        "sinjira_game_save_v1",
        "ne crée aucun blob",
        "l’import reste une action web explicite",
        "pas de profil de jeu",
        "protéger sans surveiller",
        "l’humain avant tout",
    ):
        require(marker in doc_fold, f"preuve documentaire manquante: {marker}")

    require("GAMES_GUARD" in route_guard and '"/compte/mes-parties.html"' in route_guard,
            "garde central non étendu à Mes parties")
    require('"NativeGamesHub"' in route_guard,
            "composant Mes parties absent du garde central")
    require("validate_mobile_native_games_hub_v25.py" in route_guard,
            "preuve CI Mes parties absente du garde central")

    required_workflow = (
        "python3 scripts/validate_mobile_native_games_hub_v25.py",
        "python3 scripts/validate_mobile_native_route_dispatch_v25.py",
        "python3 scripts/validate_mobile_native_home_hub_v25.py",
        "python3 scripts/validate_mobile_native_library_hub_v25.py",
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

    print("OK hub Mes parties natif V25: navigation seulement, aucune sauvegarde ou feuille privée locale.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
