#!/usr/bin/env python3
"""Valide la frontière V25 du hub Messages React Native sans contenu privé ni identité implicite."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
ALERTS = ROOT / "mobile-native" / "NativeAlertsHub.tsx"
MESSAGES = ROOT / "mobile-native" / "NativeMessagesHub.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_MESSAGES_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-messages-hub-v25.yml"
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
    print(f"ECHEC hub Messages natif V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def validate_local_integration(surface: str, text: str) -> None:
    require("import { NativeMessagesHub } from './NativeMessagesHub';" in text,
            f"NativeMessagesHub non relié à {surface}")
    require("const [messagesHubOpen, setMessagesHubOpen] = useState(false);" in text,
            f"état local Messages absent de {surface}")
    require("if (path === '/compte/messages.html')" in text and "setMessagesHubOpen(true);" in text,
            f"la destination Messages doit ouvrir le hub natif depuis {surface}")
    require("<NativeMessagesHub" in text and "onBack={() => setMessagesHubOpen(false)}" in text,
            f"retour du hub Messages absent depuis {surface}")
    require("onOpenPath={onOpenPath}" in text,
            f"les sorties Messages doivent réutiliser la navigation historique depuis {surface}")


def main() -> int:
    for path in (
        HOME,
        ALERTS,
        MESSAGES,
        DOC,
        WORKFLOW,
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
    alerts = ALERTS.read_text("utf-8")
    messages = MESSAGES.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeMessagesHub({ onOpenPath, onBack }: Props)" in messages,
            "signature minimale NativeMessagesHub absente")
    require("onOpenPath: (path: string) => void;" in messages and "onBack: () => void;" in messages,
            "le hub Messages doit avoir seulement navigation et retour comme capacités")

    forbidden_messages = (
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
    for marker in forbidden_messages:
        forbid(messages, marker, f"capacité interdite dans le hub Messages: {marker}")

    props_block = messages.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in ("user", "message", "conversation", "participant", "count", "unread", "content", "identity", "token"):
        forbid(props_block, marker, f"donnée utilisateur interdite dans les props: {marker}")

    required_paths = (
        "/compte/messages.html?surface=web",
        "/compte/messages-reels.html?surface=web",
        "/compte/messages-personnage.html?surface=web",
        "/compte/blocages.html",
        "/compte/regles-communaute.html",
    )
    for path in required_paths:
        require(path in messages, f"destination Messages manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in messages, "principe humain absent du hub Messages")
    require("PROTÉGER SANS SURVEILLER" in messages, "principe de protection absent du hub Messages")
    require("ne lit aucun message privé, aucune conversation, aucun participant, aucun compteur non lu et aucun état lu/non lu" in messages,
            "la non-lecture des conversations privées doit être explicite")
    require("ne choisit jamais votre identité à votre place" in messages and "ne mémorise pas votre dernier choix" in messages,
            "le choix explicite d’identité doit être préservé")
    require("Le natif n’envoie, ne modifie, ne supprime et ne marque aucun message" in messages,
            "la frontière de mutation doit être explicite")
    require("Aucun aperçu de conversation n’est copié dans le natif" in messages,
            "la non-copie des aperçus doit être explicite")

    validate_local_integration("l'accueil natif", home)
    validate_local_integration("le hub Alertes", alerts)

    require("ne reçoit aucune donnée utilisateur" in doc.lower(),
            "documentation de la frontière sans données absente")
    require("n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau" in doc,
            "documentation de la frontière serveur absente")
    require("ne choisit jamais une identité à la place de l’utilisateur" in doc,
            "documentation du choix explicite d’identité absente")
    require("ne mémorise pas le dernier choix" in doc,
            "documentation de l'absence de persistance d’identité absente")
    require("Il n’envoie, ne modifie, ne supprime et ne marque aucun message" in doc,
            "documentation de la frontière de mutation absente")
    require("L’HUMAIN AVANT TOUT" in doc and "Protéger sans surveiller" in doc,
            "principes de sécurité absents de la documentation")

    required_workflow_markers = (
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
        "OK hub Messages natif V25: navigation seulement, identités réel/personnage séparées, "
        "aucun contenu privé ni compteur copié et aucune mutation locale."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
