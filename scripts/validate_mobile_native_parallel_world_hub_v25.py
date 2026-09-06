#!/usr/bin/env python3
"""Valide la frontière V25 du hub Monde parallèle React Native sans continuité privée locale."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
PARALLEL = ROOT / "mobile-native" / "NativeParallelWorldHub.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_PARALLEL_WORLD_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-parallel-world-hub-v25.yml"
DATING_GUARD = ROOT / "scripts" / "validate_mobile_native_dating_hub_v25.py"
EMPLOYMENT_GUARD = ROOT / "scripts" / "validate_mobile_native_employment_hub_v25.py"
MESSAGES_GUARD = ROOT / "scripts" / "validate_mobile_native_messages_hub_v25.py"
ALERTS_GUARD = ROOT / "scripts" / "validate_mobile_native_alerts_hub_v25.py"
SETTINGS_GUARD = ROOT / "scripts" / "validate_mobile_native_settings_hub_v25.py"
PRIVACY_GUARD = ROOT / "scripts" / "validate_mobile_native_privacy_hub_v25.py"
PROFILE_GUARD = ROOT / "scripts" / "validate_mobile_native_profile_hub_v25.py"
HOME_GUARD = ROOT / "scripts" / "validate_mobile_native_home_hub_v25.py"
SECURITY_GUARD = ROOT / "scripts" / "validate_mobile_native_security_hub_v25.py"
NAV_GUARD = ROOT / "scripts" / "validate_mobile_navigation_boundary_v25.py"
SHARE_GUARD = ROOT / "scripts" / "validate_mobile_safe_share_v25.py"
CHALLENGE_GUARD = ROOT / "scripts" / "validate_device_challenge_client_boundary.py"
SECRET_GUARD = ROOT / "scripts" / "validate_no_committed_secrets.py"
VAULT_GUARD = ROOT / "mobile-native" / "scripts" / "validate-vault-mobile.mjs"


def fail(message: str) -> None:
    print(f"ECHEC hub Monde parallèle natif V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def main() -> int:
    for path in (
        HOME,
        PARALLEL,
        DOC,
        WORKFLOW,
        DATING_GUARD,
        EMPLOYMENT_GUARD,
        MESSAGES_GUARD,
        ALERTS_GUARD,
        SETTINGS_GUARD,
        PRIVACY_GUARD,
        PROFILE_GUARD,
        HOME_GUARD,
        SECURITY_GUARD,
        NAV_GUARD,
        SHARE_GUARD,
        CHALLENGE_GUARD,
        SECRET_GUARD,
        VAULT_GUARD,
    ):
        require(path.is_file(), f"fichier manquant: {path.relative_to(ROOT)}")

    home = HOME.read_text("utf-8")
    parallel = PARALLEL.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeParallelWorldHub({ onOpenPath, onBack }: Props)" in parallel,
            "signature minimale NativeParallelWorldHub absente")
    require("onOpenPath: (path: string) => void;" in parallel and "onBack: () => void;" in parallel,
            "le hub Monde parallèle doit avoir seulement navigation et retour comme capacités")

    forbidden_parallel = (
        "WebView",
        "SecureStore",
        "AsyncStorage",
        "LocalAuthentication",
        "Notifications",
        "expo-",
        "supabase",
        "fetch(",
        "XMLHttpRequest",
        "rpc(",
        "/rest/v1/",
        "/functions/v1/",
        "parallel_my_context",
        "parallel_save_cycle_response",
        "response_text",
        "state_data",
        "character_id",
        "account_id",
        "service_role",
        "SERVICE_ROLE",
        "access_token",
        "refresh_token",
        "localStorage",
        "FormData",
    )
    for marker in forbidden_parallel:
        forbid(parallel, marker, f"capacité ou identifiant interdit dans le hub Monde parallèle: {marker}")

    props_block = parallel.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in (
        "user", "profile", "character", "identity", "membership", "pioneer", "reputation", "location",
        "faction", "state", "story", "history", "cycle", "response", "canon", "memorial", "token"
    ):
        forbid(props_block, marker, f"donnée utilisateur interdite dans les props: {marker}")

    required_paths = (
        "/compte/monde-parallele.html?surface=web",
        "/projets/sinjira/monde-parallele/",
        "/compte/mon-personnage.html",
        "/compte/securite.html",
    )
    for path in required_paths:
        require(path in parallel, f"destination Monde parallèle manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in parallel, "principe humain absent du hub Monde parallèle")
    require("PROTÉGER SANS SURVEILLER" in parallel, "principe de protection absent du hub Monde parallèle")
    require("ne lit aucune identité de personnage, adhésion, réputation, localisation narrative, faction, Chronique personnelle, réponse de cycle ni histoire liée à votre continuité" in parallel,
            "la non-lecture de la continuité privée doit être explicite")
    require("Le natif ne reçoit aucune clé interne permettant de relier ces identités" in parallel,
            "la séparation des identités techniques doit être explicite")
    require("Aucune mémoire narrative locale" in parallel,
            "l'absence de mémoire narrative locale doit être explicite")
    require("Le natif ne crée, ne modifie et n’enregistre aucune réponse de cycle, aucun état narratif et aucune histoire" in parallel,
            "la frontière de mutation narrative doit être explicite")
    require("Ce hub ne valide aucun canon, décès, mémorial ou changement irréversible du personnage" in parallel,
            "les décisions irréversibles doivent rester hors du natif")
    require("ne devient jamais la source de vérité de votre continuité" in parallel,
            "la source de vérité serveur doit être explicite")

    require("import { NativeParallelWorldHub } from './NativeParallelWorldHub';" in home,
            "NativeParallelWorldHub non relié à l'accueil natif")
    require("const [parallelWorldHubOpen, setParallelWorldHubOpen] = useState(false);" in home,
            "état local Monde parallèle absent de l'accueil")
    require("if (path === '/compte/monde-parallele.html')" in home and "setParallelWorldHubOpen(true);" in home,
            "la destination Monde parallèle doit ouvrir le hub natif")
    require("<NativeParallelWorldHub" in home and "onBack={() => setParallelWorldHubOpen(false)}" in home,
            "retour du hub Monde parallèle vers Accueil absent")
    require("onOpenPath={onOpenPath}" in home,
            "les sorties Monde parallèle doivent réutiliser la navigation historique")

    require("ne reçoit aucune donnée utilisateur" in doc.lower(),
            "documentation de la frontière sans données absente")
    require("n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau" in doc,
            "documentation de la frontière serveur absente")
    require("Le hub ne crée, ne modifie et n’enregistre aucune réponse de cycle" in doc,
            "documentation de la frontière de mutation absente")
    require("ne reçoit aucune clé interne" in doc,
            "documentation du cloisonnement des identités absente")
    require("Le canon reste une décision humaine" in doc,
            "documentation de la souveraineté humaine absente")
    require("Le hub ne valide aucun canon, décès, mémorial ou changement irréversible du personnage" in doc,
            "documentation des décisions irréversibles absente")
    require("L’HUMAIN AVANT TOUT" in doc and "Protéger sans surveiller" in doc,
            "principes de sécurité absents de la documentation")

    required_workflow_markers = (
        "python3 scripts/validate_mobile_native_parallel_world_hub_v25.py",
        "python3 scripts/validate_mobile_native_dating_hub_v25.py",
        "python3 scripts/validate_mobile_native_employment_hub_v25.py",
        "python3 scripts/validate_mobile_native_messages_hub_v25.py",
        "python3 scripts/validate_mobile_native_alerts_hub_v25.py",
        "python3 scripts/validate_mobile_native_settings_hub_v25.py",
        "python3 scripts/validate_mobile_native_privacy_hub_v25.py",
        "python3 scripts/validate_mobile_native_profile_hub_v25.py",
        "python3 scripts/validate_mobile_native_home_hub_v25.py",
        "python3 scripts/validate_mobile_native_security_hub_v25.py",
        "python3 scripts/validate_mobile_navigation_boundary_v25.py",
        "python3 scripts/validate_mobile_safe_share_v25.py",
        "python3 scripts/validate_device_challenge_client_boundary.py",
        "python3 scripts/validate_no_committed_secrets.py",
        "npm run validate:vault",
        "npm run typecheck",
    )
    for marker in required_workflow_markers:
        require(marker in workflow, f"preuve CI manquante: {marker}")

    for marker in ("environment: production", "SUPABASE_ACCESS_TOKEN", "${{ secrets.", "supabase start", "supabase db"):
        forbid(workflow, marker, f"production/secret interdit dans ce workflow: {marker}")

    print(
        "OK hub Monde parallèle natif V25: navigation seulement, aucune continuité privée copiée, "
        "aucune mémoire/mutation narrative locale et décisions canoniques humaines préservées."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
