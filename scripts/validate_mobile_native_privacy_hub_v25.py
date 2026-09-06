#!/usr/bin/env python3
"""Valide la frontière V25 du hub Vie privée React Native sans données ni actions locales."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "mobile-native" / "NativeProfileHub.tsx"
PRIVACY = ROOT / "mobile-native" / "NativePrivacyHub.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_PRIVACY_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-privacy-hub-v25.yml"
PROFILE_GUARD = ROOT / "scripts" / "validate_mobile_native_profile_hub_v25.py"
HOME_GUARD = ROOT / "scripts" / "validate_mobile_native_home_hub_v25.py"
SECURITY_GUARD = ROOT / "scripts" / "validate_mobile_native_security_hub_v25.py"
NAV_GUARD = ROOT / "scripts" / "validate_mobile_navigation_boundary_v25.py"
SHARE_GUARD = ROOT / "scripts" / "validate_mobile_safe_share_v25.py"
CHALLENGE_GUARD = ROOT / "scripts" / "validate_device_challenge_client_boundary.py"
SECRET_GUARD = ROOT / "scripts" / "validate_no_committed_secrets.py"
VAULT_GUARD = ROOT / "mobile-native" / "scripts" / "validate-vault-mobile.mjs"


def fail(message: str) -> None:
    print(f"ECHEC hub Vie privée natif V25: {message}", file=sys.stderr)
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
        DOC,
        WORKFLOW,
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
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativePrivacyHub({ onOpenPath, onBack }: Props)" in privacy,
            "signature minimale NativePrivacyHub absente")
    require("onOpenPath: (path: string) => void;" in privacy and "onBack: () => void;" in privacy,
            "le hub Vie privée doit avoir seulement navigation et retour comme capacités")

    forbidden_privacy = (
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
        "localStorage",
        "FormData",
    )
    for marker in forbidden_privacy:
        forbid(privacy, marker, f"capacité interdite dans le hub Vie privée: {marker}")

    props_block = privacy.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in ("user", "privacy", "request", "profile", "email", "identity", "token", "content", "history"):
        forbid(props_block, marker, f"donnée utilisateur interdite dans les props: {marker}")

    required_paths = (
        "/compte/vie-privee.html?surface=web",
        "/confidentialite.html",
        "/compte/securite.html",
        "/compte/parametres.html",
    )
    for path in required_paths:
        require(path in privacy, f"destination Vie privée manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in privacy, "principe humain absent du hub Vie privée")
    require("Aucune demande n’est traitée localement" in privacy,
            "la frontière des demandes doit être explicite")
    require("Il ne lit aucune demande Vie privée, aucun renseignement personnel" in privacy,
            "la non-lecture des données privées doit être explicite")
    require("Aucun GPS, aucune adresse IP brute, aucun secret, aucune pièce d’identité" in privacy,
            "les données interdites doivent être explicites")

    require("import { NativePrivacyHub } from './NativePrivacyHub';" in profile,
            "NativePrivacyHub non relié au hub Profil")
    require("const [privacyHubOpen, setPrivacyHubOpen] = useState(false);" in profile,
            "état local Vie privée absent")
    require("if (path === '/compte/vie-privee.html')" in profile and "setPrivacyHubOpen(true);" in profile,
            "la destination Vie privée doit ouvrir le hub natif")
    require("<NativePrivacyHub" in profile and "onBack={() => setPrivacyHubOpen(false)}" in profile,
            "retour Vie privée vers Profil absent")
    require("onOpenPath={onOpenPath}" in profile,
            "les sorties Vie privée doivent réutiliser la navigation historique")

    require("ne lit aucune demande Vie privée existante" in doc,
            "documentation de non-lecture des demandes absente")
    require("n’appelle ni Supabase, ni Edge Function, ni RPC" in doc,
            "documentation de la frontière serveur absente")
    require("L’HUMAIN AVANT TOUT" in doc and "Protéger sans surveiller" in doc,
            "principes de sécurité absents de la documentation")

    required_workflow_markers = (
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
        "OK hub Vie privée natif V25: navigation seulement, aucune demande ni donnée copiée, "
        "source de vérité Web/serveur conservée et gardes mobiles historiques rechaînées."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
