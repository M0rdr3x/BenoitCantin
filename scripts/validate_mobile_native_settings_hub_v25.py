#!/usr/bin/env python3
"""Valide la frontière V25 du hub Paramètres React Native sans données ni actions sensibles locales."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "mobile-native" / "NativeProfileHub.tsx"
PRIVACY = ROOT / "mobile-native" / "NativePrivacyHub.tsx"
SETTINGS = ROOT / "mobile-native" / "NativeSettingsHub.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_SETTINGS_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-settings-hub-v25.yml"
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
    print(f"ECHEC hub Paramètres natif V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def main() -> int:
    for path in (
        PROFILE,
        PRIVACY,
        SETTINGS,
        DOC,
        WORKFLOW,
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

    profile = PROFILE.read_text("utf-8")
    privacy = PRIVACY.read_text("utf-8")
    settings = SETTINGS.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeSettingsHub({ onOpenPath, onBack }: Props)" in settings,
            "signature minimale NativeSettingsHub absente")
    require("onOpenPath: (path: string) => void;" in settings and "onBack: () => void;" in settings,
            "le hub Paramètres doit avoir seulement navigation et retour comme capacités")

    forbidden_settings = (
        "WebView",
        "SecureStore",
        "AsyncStorage",
        "LocalAuthentication",
        "Notifications",
        "expo-",
        "FileSystem",
        "Sharing",
        "DocumentPicker",
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
        "localStorage",
        "FormData",
    )
    for marker in forbidden_settings:
        forbid(settings, marker, f"capacité interdite dans le hub Paramètres: {marker}")

    props_block = settings.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in ("user", "setting", "preference", "privacy", "notification", "export", "delete", "token", "content", "profile"):
        forbid(props_block, marker, f"donnée utilisateur interdite dans les props: {marker}")

    required_paths = (
        "/compte/parametres.html?surface=web",
        "/compte/vie-privee.html?surface=web",
        "/compte/securite.html",
        "/compte/profil.html?surface=web",
    )
    for path in required_paths:
        require(path in settings, f"destination Paramètres manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in settings, "principe humain absent du hub Paramètres")
    require("PROTÉGER SANS SURVEILLER" in settings, "principe de protection absent du hub Paramètres")
    require("ne lit, ne copie et ne modifie aucune préférence du compte" in settings,
            "la non-lecture des préférences doit être explicite")
    require("ne prépare aucun export et ne peut jamais supprimer votre compte" in settings,
            "la frontière export/suppression doit être explicite")
    require("Les actions sensibles restent côté serveur" in settings,
            "la source de vérité serveur doit être explicitée")
    require("Pas de copie locale des réglages" in settings,
            "l'absence de copie locale doit être explicite")

    # Profil -> Paramètres natif.
    require("import { NativeSettingsHub } from './NativeSettingsHub';" in profile,
            "NativeSettingsHub non relié au hub Profil")
    require("const [settingsHubOpen, setSettingsHubOpen] = useState(false);" in profile,
            "état local Paramètres absent du hub Profil")
    require("if (path === '/compte/parametres.html')" in profile and "setSettingsHubOpen(true);" in profile,
            "la destination Paramètres du Profil doit ouvrir le hub natif")
    require("<NativeSettingsHub" in profile and "onBack={() => setSettingsHubOpen(false)}" in profile,
            "retour Paramètres vers Profil absent")

    # Vie privée -> même Paramètres natif, sans second comportement incohérent.
    require("import { NativeSettingsHub } from './NativeSettingsHub';" in privacy,
            "NativeSettingsHub non relié au hub Vie privée")
    require("const [settingsHubOpen, setSettingsHubOpen] = useState(false);" in privacy,
            "état local Paramètres absent du hub Vie privée")
    require("if (path === '/compte/parametres.html')" in privacy and "setSettingsHubOpen(true);" in privacy,
            "la destination Paramètres de Vie privée doit ouvrir le hub natif")
    require("<NativeSettingsHub" in privacy and "onBack={() => setSettingsHubOpen(false)}" in privacy,
            "retour Paramètres vers Vie privée absent")

    require("ne reçoit aucune donnée utilisateur" in doc.lower(),
            "documentation de la frontière sans données absente")
    require("n’appelle ni Supabase, ni Edge Function, ni RPC" in doc,
            "documentation de la frontière serveur absente")
    require("ne déclenche jamais la suppression du compte" in doc,
            "documentation de la suppression côté serveur absente")
    require("ne prépare, ne télécharge et ne conserve aucun export JSON" in doc,
            "documentation de l'export côté serveur absente")
    require("L’HUMAIN AVANT TOUT" in doc and "Protéger sans surveiller" in doc,
            "principes de sécurité absents de la documentation")

    required_workflow_markers = (
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
        "OK hub Paramètres natif V25: navigation seulement, aucune préférence copiée, "
        "aucun export/suppression local et gardes mobiles historiques rechaînées."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
