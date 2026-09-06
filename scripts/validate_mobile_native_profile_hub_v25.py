#!/usr/bin/env python3
"""Valide la frontière V25 du hub Profil React Native sans données utilisateur."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
PROFILE = ROOT / "mobile-native" / "NativeProfileHub.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_PROFILE_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-profile-hub-v25.yml"
HOME_GUARD = ROOT / "scripts" / "validate_mobile_native_home_hub_v25.py"
SECURITY_GUARD = ROOT / "scripts" / "validate_mobile_native_security_hub_v25.py"
NAV_GUARD = ROOT / "scripts" / "validate_mobile_navigation_boundary_v25.py"
SHARE_GUARD = ROOT / "scripts" / "validate_mobile_safe_share_v25.py"
CHALLENGE_GUARD = ROOT / "scripts" / "validate_device_challenge_client_boundary.py"
SECRET_GUARD = ROOT / "scripts" / "validate_no_committed_secrets.py"
VAULT_GUARD = ROOT / "mobile-native" / "scripts" / "validate-vault-mobile.mjs"


def fail(message: str) -> None:
    print(f"ECHEC hub Profil natif V25: {message}", file=sys.stderr)
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
        PROFILE,
        DOC,
        WORKFLOW,
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
    profile = PROFILE.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeProfileHub({ onOpenPath, onBack }: Props)" in profile,
            "signature minimale NativeProfileHub absente")
    require("onOpenPath: (path: string) => void;" in profile and "onBack: () => void;" in profile,
            "le hub Profil doit avoir seulement navigation et retour comme capacités")

    forbidden_profile = (
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
        "service_role",
        "SERVICE_ROLE",
        "access_token",
        "refresh_token",
        "device_key",
        "localStorage",
    )
    for marker in forbidden_profile:
        forbid(profile, marker, f"capacité interdite dans le hub Profil: {marker}")

    props_block = profile.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in ("user", "profile", "email", "avatar", "birth", "city", "country", "relationship", "token", "device"):
        forbid(props_block, marker, f"donnée utilisateur interdite dans les props: {marker}")

    required_paths = (
        "/compte/profil.html?surface=web",
        "/compte/vie-privee.html",
        "/compte/parametres.html",
        "/compte/securite.html",
    )
    for path in required_paths:
        require(path in profile, f"destination du hub Profil manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in profile, "principe humain absent du hub Profil")
    require("PROTÉGER SANS SURVEILLER" in profile, "principe de protection absent du hub Profil")
    require("ne lit, ne copie et ne conserve aucune donnée de profil" in profile,
            "la non-copie des données de profil doit être explicite")
    require("Aucune seconde copie du profil" in profile,
            "la source de vérité unique doit être explicitée")

    require("import { NativeProfileHub } from './NativeProfileHub';" in home,
            "NativeProfileHub non relié à l'accueil natif")
    require("const [profileHubOpen, setProfileHubOpen] = useState(false);" in home,
            "état local du hub Profil absent")
    require("if (path === '/compte/profil.html')" in home and "setProfileHubOpen(true);" in home,
            "la destination Profil doit ouvrir le hub natif")
    require("<NativeProfileHub" in home and "onBack={() => setProfileHubOpen(false)}" in home,
            "retour Profil vers Accueil absent")
    require("onOpenPath={onOpenPath}" in home,
            "les sorties du hub Profil doivent réutiliser la navigation historique")

    require("ne reçoit aucune donnée utilisateur" in doc.lower(),
            "documentation de la frontière sans données absente")
    require("n’appelle ni Supabase, ni Edge Function, ni RPC" in doc,
            "documentation de la frontière serveur absente")
    require("L’HUMAIN AVANT TOUT" in doc and "Protéger sans surveiller" in doc,
            "principes de sécurité absents de la documentation")

    required_workflow_markers = (
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
        "OK hub Profil natif V25: navigation seulement, aucune donnée de profil copiée, "
        "source de vérité Web/serveur conservée et gardes mobiles historiques rechaînées."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
