#!/usr/bin/env python3
"""Valide la frontière V25 du hub Emploi React Native sans données professionnelles privées."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
EMPLOYMENT = ROOT / "mobile-native" / "NativeEmploymentHub.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_EMPLOYMENT_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-employment-hub-v25.yml"
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
    print(f"ECHEC hub Emploi natif V25: {message}", file=sys.stderr)
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
        EMPLOYMENT,
        DOC,
        WORKFLOW,
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
    employment = EMPLOYMENT.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeEmploymentHub({ onOpenPath, onBack }: Props)" in employment,
            "signature minimale NativeEmploymentHub absente")
    require("onOpenPath: (path: string) => void;" in employment and "onBack: () => void;" in employment,
            "le hub Emploi doit avoir seulement navigation et retour comme capacités")

    forbidden_employment = (
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
        "employment_profiles",
        "employment_applications",
        "service_role",
        "SERVICE_ROLE",
        "access_token",
        "refresh_token",
        "localStorage",
        "FormData",
    )
    for marker in forbidden_employment:
        forbid(employment, marker, f"capacité interdite dans le hub Emploi: {marker}")

    props_block = employment.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in ("user", "profile", "application", "candidate", "job", "skill", "status", "location", "note", "token"):
        forbid(props_block, marker, f"donnée utilisateur interdite dans les props: {marker}")

    required_paths = (
        "/compte/emploi.html?surface=web",
        "/compte/vie-privee.html?surface=web",
        "/compte/securite.html",
        "/compte/parametres.html?surface=web",
    )
    for path in required_paths:
        require(path in employment, f"destination Emploi manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in employment, "principe humain absent du hub Emploi")
    require("PROTÉGER SANS SURVEILLER" in employment, "principe de protection absent du hub Emploi")
    require("ne lit aucun profil professionnel, aucune candidature, aucune note privée, aucun statut ni aucune date" in employment,
            "la non-lecture des données Emploi privées doit être explicite")
    require("Le natif ne crée, ne modifie, ne supprime et ne classe aucune candidature" in employment,
            "la frontière de mutation et de classement doit être explicite")
    require("Aucun formulaire Emploi n’est reproduit dans le natif" in employment,
            "la non-reproduction des formulaires doit être explicite")
    require("Registre personnel" in employment and "Rencontres" in employment and "Histoire de vie" in employment and "Mode Voyage" in employment,
            "la séparation des autres espaces sensibles doit être explicite")
    require("Les renseignements de sécurité ne servent pas à classer une candidature" in employment,
            "la séparation sécurité/emploi doit être explicite")

    require("import { NativeEmploymentHub } from './NativeEmploymentHub';" in home,
            "NativeEmploymentHub non relié à l'accueil natif")
    require("const [employmentHubOpen, setEmploymentHubOpen] = useState(false);" in home,
            "état local Emploi absent de l'accueil")
    require("if (path === '/compte/emploi.html')" in home and "setEmploymentHubOpen(true);" in home,
            "la destination Emploi doit ouvrir le hub natif")
    require("<NativeEmploymentHub" in home and "onBack={() => setEmploymentHubOpen(false)}" in home,
            "retour du hub Emploi vers Accueil absent")
    require("onOpenPath={onOpenPath}" in home,
            "les sorties Emploi doivent réutiliser la navigation historique")

    require("ne reçoit aucune donnée utilisateur" in doc.lower(),
            "documentation de la frontière sans données absente")
    require("n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau" in doc,
            "documentation de la frontière serveur absente")
    require("Il ne crée, ne modifie, ne supprime et ne classe aucune candidature" in doc,
            "documentation de la frontière de mutation absente")
    require("Il ne reproduit aucun formulaire Emploi dans le natif" in doc,
            "documentation de la non-reproduction des formulaires absente")
    require("Les renseignements de sécurité servent à protéger le compte, jamais à classer une candidature" in doc,
            "documentation de la séparation sécurité/emploi absente")
    require("L’HUMAIN AVANT TOUT" in doc and "Protéger sans surveiller" in doc,
            "principes de sécurité absents de la documentation")

    required_workflow_markers = (
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
        "OK hub Emploi natif V25: navigation seulement, aucune donnée professionnelle copiée, "
        "aucune mutation/classement local et séparation des espaces sensibles préservée."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
