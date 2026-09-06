#!/usr/bin/env python3
"""Valide la frontière V25 du hub Mon IA React Native sans données ni opérations privées locales."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
PERSONAL_AI = ROOT / "mobile-native" / "NativePersonalAiHub.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_PERSONAL_AI_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-personal-ai-hub-v25.yml"
PERSONAL_AI_CONTRACT = ROOT / "scripts" / "validate_personal_ai_v25.py"
PARALLEL_GUARD = ROOT / "scripts" / "validate_mobile_native_parallel_world_hub_v25.py"
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
    print(f"ECHEC hub Mon IA natif V25: {message}", file=sys.stderr)
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
        PERSONAL_AI,
        DOC,
        WORKFLOW,
        PERSONAL_AI_CONTRACT,
        PARALLEL_GUARD,
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
    personal_ai = PERSONAL_AI.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativePersonalAiHub({ onOpenPath, onBack }: Props)" in personal_ai,
            "signature minimale NativePersonalAiHub absente")
    require("onOpenPath: (path: string) => void;" in personal_ai and "onBack: () => void;" in personal_ai,
            "le hub Mon IA doit avoir seulement navigation et retour comme capacités")

    forbidden_personal_ai = (
        "WebView",
        "SecureStore",
        "AsyncStorage",
        "LocalAuthentication",
        "Notifications",
        "expo-",
        "supabase",
        "getSupabase",
        "functions.invoke",
        "fetch(",
        "XMLHttpRequest",
        "rpc(",
        "/rest/v1/",
        "/functions/v1/",
        "personal_ai_settings",
        "personal_ai_source_permissions",
        "personal_ai_audit",
        "update_settings",
        "set_source_permission",
        "delete_personal_ai_data",
        "get_state",
        "device_key",
        "display_code",
        "access_token",
        "refresh_token",
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "FormData",
    )
    for marker in forbidden_personal_ai:
        forbid(personal_ai, marker, f"capacité ou donnée interdite dans le hub Mon IA: {marker}")

    props_block = personal_ai.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in (
        "user", "setting", "enabled", "display", "language", "permission", "source", "audit", "mfa",
        "risk", "challenge", "device", "runtime", "memory", "conversation", "provider", "token"
    ):
        forbid(props_block, marker, f"donnée utilisateur interdite dans les props: {marker}")

    required_paths = (
        "/compte/mon-ia.html?surface=web",
        "/compte/securite.html",
        "/compte/histoire-de-vie.html",
        "/compte/emploi.html?surface=web",
    )
    for path in required_paths:
        require(path in personal_ai, f"destination Mon IA manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in personal_ai, "principe humain absent du hub Mon IA")
    require("PROTÉGER SANS SURVEILLER" in personal_ai, "principe de protection absent du hub Mon IA")
    require("ne lit aucun réglage Mon IA, aucun consentement de source, aucun nom d’affichage, aucune langue, aucun audit et aucun état de sécurité" in personal_ai,
            "la non-lecture des données Mon IA privées doit être explicite")
    require("Le natif n’ouvre pas vos réglages, ne change aucune préférence, n’accorde ou ne retire aucun consentement et ne supprime aucune donnée Mon IA" in personal_ai,
            "la frontière des mutations Mon IA doit être explicite")
    require("Ce composant n’évalue ni MFA, ni appareil, ni risque, ni challenge" in personal_ai,
            "la décision de sécurité doit rester hors du natif")
    require("L’exigence AAL2 et la ressource privée ai_private restent appliquées" in personal_ai,
            "AAL2/ai_private doivent rester explicitement côté mécanismes existants")
    require("Le runtime V25 reste non configuré" in personal_ai,
            "le runtime non configuré doit être explicite")
    require("ne lance aucun modèle, ne stocke aucune conversation ou mémoire, ne récupère aucun contenu Histoire de vie ou Emploi" in personal_ai,
            "chat/mémoire/récupération de source doivent rester absents")
    require("Le Registre personnel n’est pas une source Mon IA" in personal_ai,
            "la séparation du Registre doit être explicite")
    require("Aucun clone IA" in personal_ai,
            "l'absence de clone IA doit être explicite")
    require("Ouvrir Histoire de vie ou Emploi depuis cet écran ne vaut jamais consentement pour Mon IA" in personal_ai,
            "les navigations sources ne doivent jamais valoir consentement")

    require("import { NativePersonalAiHub } from './NativePersonalAiHub';" in home,
            "NativePersonalAiHub non relié à l'accueil natif")
    require("const [personalAiHubOpen, setPersonalAiHubOpen] = useState(false);" in home,
            "état local Mon IA absent de l'accueil")
    require("if (path === '/compte/mon-ia.html')" in home and "setPersonalAiHubOpen(true);" in home,
            "la destination Mon IA doit ouvrir le hub natif")
    require("<NativePersonalAiHub" in home and "onBack={() => setPersonalAiHubOpen(false)}" in home,
            "retour du hub Mon IA vers Accueil absent")
    require("onOpenPath={onOpenPath}" in home,
            "les sorties Mon IA doivent réutiliser la navigation historique")

    require("ne reçoit aucune donnée utilisateur" in doc.lower(),
            "documentation de la frontière sans données absente")
    require("n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau" in doc,
            "documentation de la frontière serveur absente")
    require("Le hub ne décide jamais si une personne est autorisée" in doc,
            "documentation de la décision AAL2 absente")
    require("ne crée, ne modifie et ne supprime aucun réglage Mon IA" in doc,
            "documentation de la frontière de mutation absente")
    require("Le runtime reste `not_configured`" in doc,
            "documentation du runtime non configuré absente")
    require("Registre personnel des consciences n’est pas une source Mon IA" in doc,
            "documentation de la séparation Registre absente")
    require("Ouvrir Histoire de vie ou Emploi depuis le hub natif ne vaut jamais consentement" in doc,
            "documentation du consentement explicite absente")
    require("aucun clone IA après décès" in doc,
            "documentation de l'absence de clone IA absente")
    require("L’HUMAIN AVANT TOUT" in doc and "Protéger sans surveiller" in doc,
            "principes de sécurité absents de la documentation")

    required_workflow_markers = (
        "python3 scripts/validate_mobile_native_personal_ai_hub_v25.py",
        "python3 scripts/validate_personal_ai_v25.py",
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
        "OK hub Mon IA natif V25: navigation seulement, aucun réglage/consentement/état privé local, "
        "AAL2/ai_private conservés côté Web/serveur et runtime IA toujours non configuré."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
