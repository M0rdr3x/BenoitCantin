#!/usr/bin/env python3
"""Valide la frontière V25 du hub Rencontres React Native sans données relationnelles sensibles."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
DATING = ROOT / "mobile-native" / "NativeDatingHub.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_DATING_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-dating-hub-v25.yml"
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
    print(f"ECHEC hub Rencontres natif V25: {message}", file=sys.stderr)
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
        DATING,
        DOC,
        WORKFLOW,
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
    dating = DATING.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeDatingHub({ onOpenPath, onBack }: Props)" in dating,
            "signature minimale NativeDatingHub absente")
    require("onOpenPath: (path: string) => void;" in dating and "onBack: () => void;" in dating,
            "le hub Rencontres doit avoir seulement navigation et retour comme capacités")

    forbidden_dating = (
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
        "dating_profiles",
        "dating_preferences",
        "dating_connections",
        "dating_messages",
        "dating_compatibility",
        "dating_safe_meet",
        "dating_report",
        "sinjira_points",
        "service_role",
        "SERVICE_ROLE",
        "access_token",
        "refresh_token",
        "localStorage",
        "FormData",
    )
    for marker in forbidden_dating:
        forbid(dating, marker, f"capacité interdite dans le hub Rencontres: {marker}")

    props_block = dating.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in (
        "user", "profile", "preference", "candidate", "match", "gender", "age", "region", "location",
        "score", "connection", "message", "count", "reveal", "consent", "status", "registry", "point", "token"
    ):
        forbid(props_block, marker, f"donnée utilisateur interdite dans les props: {marker}")

    required_paths = (
        "/compte/rencontres.html?surface=web",
        "/compte/blocages.html",
        "/compte/regles-communaute.html",
        "/compte/securite.html",
    )
    for path in required_paths:
        require(path in dating, f"destination Rencontres manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in dating, "principe humain absent du hub Rencontres")
    require("PROTÉGER SANS SURVEILLER" in dating, "principe de protection absent du hub Rencontres")
    require("ne lit aucun profil Rencontres, aucune préférence, aucun score de compatibilité, aucune proposition, aucune conversation et aucun compteur de messages" in dating,
            "la non-lecture des données relationnelles privées doit être explicite")
    require("Le natif ne calcule, ne classe et ne recommande aucune personne" in dating,
            "la non-décision relationnelle doit être explicite")
    require("Le seuil 10 + 10 ne déclenche rien dans le natif" in dating,
            "le seuil de dévoilement ne doit rien déclencher nativement")
    require("Aucun consentement de dévoilement n’est enregistré ici" in dating,
            "la non-persistance du consentement doit être explicite")
    require("Aucune donnée du Registre personnel n’est importée dans ce hub" in dating,
            "la séparation du Registre doit être explicite")
    require("Le natif n’envoie aucun signalement, ne bloque aucun compte et ne prépare aucune rencontre publique" in dating,
            "signalement, blocage et rencontre publique doivent rester hors du natif")
    require("Ce hub ne vérifie ni l’âge, ni le statut célibataire, ni l’admissibilité" in dating,
            "l'admissibilité doit rester côté Web/serveur")

    require("import { NativeDatingHub } from './NativeDatingHub';" in home,
            "NativeDatingHub non relié à l'accueil natif")
    require("const [datingHubOpen, setDatingHubOpen] = useState(false);" in home,
            "état local Rencontres absent de l'accueil")
    require("if (path === '/compte/rencontres.html')" in home and "setDatingHubOpen(true);" in home,
            "la destination Rencontres doit ouvrir le hub natif")
    require("<NativeDatingHub" in home and "onBack={() => setDatingHubOpen(false)}" in home,
            "retour du hub Rencontres vers Accueil absent")
    require("onOpenPath={onOpenPath}" in home,
            "les sorties Rencontres doivent réutiliser la navigation historique")

    require("ne reçoit aucune donnée utilisateur" in doc.lower(),
            "documentation de la frontière sans données absente")
    require("n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau" in doc,
            "documentation de la frontière serveur absente")
    require("ne calcule, ne classe et ne recommande aucune personne" in doc,
            "documentation de la non-décision relationnelle absente")
    require("Il ne déclenche jamais un dévoilement automatique" in doc,
            "documentation du dévoilement non automatique absente")
    require("Aucune donnée du Registre personnel n’est importée dans le hub natif" in doc,
            "documentation de la séparation du Registre absente")
    require("Le hub n’envoie aucun signalement, ne bloque ou débloque aucun compte" in doc,
            "documentation de la frontière modération/blocage absente")
    require("Il ne crée, n’accepte, n’annule et ne génère aucune proposition de première rencontre" in doc,
            "documentation de la frontière première rencontre absente")
    require("L’HUMAIN AVANT TOUT" in doc and "Protéger sans surveiller" in doc,
            "principes de sécurité absents de la documentation")

    required_workflow_markers = (
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
        "OK hub Rencontres natif V25: navigation seulement, aucune donnée relationnelle copiée, "
        "aucune décision/compatibilité/consentement local et protections Web/serveur préservées."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
