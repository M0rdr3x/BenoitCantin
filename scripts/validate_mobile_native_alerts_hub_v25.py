#!/usr/bin/env python3
"""Valide la frontière V25 du hub Alertes React Native sans contenu privé ni mutations locales."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
ALERTS = ROOT / "mobile-native" / "NativeAlertsHub.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_ALERTS_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-alerts-hub-v25.yml"
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
    print(f"ECHEC hub Alertes natif V25: {message}", file=sys.stderr)
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
        ALERTS,
        DOC,
        WORKFLOW,
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
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeAlertsHub({ onOpenPath, onBack }: Props)" in alerts,
            "signature minimale NativeAlertsHub absente")
    require("onOpenPath: (path: string) => void;" in alerts and "onBack: () => void;" in alerts,
            "le hub Alertes doit avoir seulement navigation et retour comme capacités")

    forbidden_alerts = (
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
    for marker in forbidden_alerts:
        forbid(alerts, marker, f"capacité interdite dans le hub Alertes: {marker}")

    props_block = alerts.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in ("user", "alert", "notification", "count", "unread", "message", "content", "event", "token"):
        forbid(props_block, marker, f"donnée utilisateur interdite dans les props: {marker}")

    required_paths = (
        "/compte/notifications.html?surface=web",
        "/compte/securite.html",
        "/compte/messages.html",
        "/compte/parametres.html?surface=web",
    )
    for path in required_paths:
        require(path in alerts, f"destination Alertes manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in alerts, "principe humain absent du hub Alertes")
    require("PROTÉGER SANS SURVEILLER" in alerts, "principe de protection absent du hub Alertes")
    require("ne lit aucune notification privée, aucun compteur et aucun état lu/non lu" in alerts,
            "la non-lecture des avis privés doit être explicite")
    require("Aucun contenu d’avis n’est copié dans le natif" in alerts,
            "la non-copie du contenu doit être explicite")
    require("Le natif ne marque, ne crée et ne supprime aucun avis" in alerts,
            "la frontière de mutation doit être explicite")
    require("Pas de résumé local de votre activité" in alerts,
            "l'absence de résumé local doit être explicite")

    require("import { NativeAlertsHub } from './NativeAlertsHub';" in home,
            "NativeAlertsHub non relié à l'accueil natif")
    require("const [alertsHubOpen, setAlertsHubOpen] = useState(false);" in home,
            "état local Alertes absent")
    require("if (path === '/compte/notifications.html')" in home and "setAlertsHubOpen(true);" in home,
            "la destination Alertes doit ouvrir le hub natif")
    require("<NativeAlertsHub" in home and "onBack={() => setAlertsHubOpen(false)}" in home,
            "retour Alertes vers Accueil absent")
    require("onOpenPath={onOpenPath}" in home,
            "les sorties du hub Alertes doivent réutiliser la navigation historique")

    require("ne reçoit aucune donnée utilisateur" in doc.lower(),
            "documentation de la frontière sans données absente")
    require("n’appelle ni Supabase, ni Edge Function, ni RPC" in doc,
            "documentation de la frontière serveur absente")
    require("ne marque aucun avis comme lu ou non lu" in doc,
            "documentation de la frontière lu/non lu absente")
    require("ne crée et ne supprime aucune notification" in doc,
            "documentation de la frontière de mutation absente")
    require("L’HUMAIN AVANT TOUT" in doc and "Protéger sans surveiller" in doc,
            "principes de sécurité absents de la documentation")

    required_workflow_markers = (
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
        "OK hub Alertes natif V25: navigation seulement, aucun avis privé copié, "
        "aucune mutation locale et gardes mobiles historiques rechaînées."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
