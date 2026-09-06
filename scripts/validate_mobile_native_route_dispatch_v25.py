#!/usr/bin/env python3
"""Valide le routage V25 des entrées persistantes vers les hubs natifs sans données."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "mobile-native" / "App.tsx"
ROUTER = ROOT / "mobile-native" / "NativeModuleRouter.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_ROUTE_DISPATCH_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-route-dispatch-v25.yml"
PERSONAL_AI_GUARD = ROOT / "scripts" / "validate_mobile_native_personal_ai_hub_v25.py"
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
    print(f"ECHEC routage natif V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def main() -> int:
    for path in (
        APP, ROUTER, DOC, WORKFLOW,
        PERSONAL_AI_GUARD, PARALLEL_GUARD, DATING_GUARD, EMPLOYMENT_GUARD,
        MESSAGES_GUARD, ALERTS_GUARD, SETTINGS_GUARD, PRIVACY_GUARD,
        PROFILE_GUARD, HOME_GUARD, SECURITY_GUARD, NAV_GUARD, SHARE_GUARD,
        CHALLENGE_GUARD, SECRET_GUARD, VAULT_GUARD,
    ):
        require(path.is_file(), f"fichier manquant: {path.relative_to(ROOT)}")

    app = APP.read_text("utf-8")
    router = ROUTER.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    required_router_paths = (
        "/compte/messages.html",
        "/compte/rencontres.html",
        "/compte/emploi.html",
        "/compte/monde-parallele.html",
        "/compte/mon-ia.html",
        "/compte/notifications.html",
        "/compte/profil.html",
    )
    for path in required_router_paths:
        require(path in router, f"route native manquante: {path}")

    for marker in (
        "NativeMessagesHub", "NativeDatingHub", "NativeEmploymentHub", "NativeParallelWorldHub",
        "NativePersonalAiHub", "NativeAlertsHub", "NativeProfileHub",
        "export function isNativeModulePath(path: string): path is NativeModulePath",
        "export function NativeModuleRouter({ path, onOpenPath, onBack }: Props)",
    ):
        require(marker in router, f"contrat routeur manquant: {marker}")

    props_block = router.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in (
        "user", "profiledata", "messagecontent", "applicationdata", "matchdata", "identitydata",
        "settingdata", "token", "device", "session", "content", "payload"
    ):
        forbid(props_block, marker, f"donnée utilisateur interdite dans les props du routeur: {marker}")

    for marker in (
        "WebView", "SecureStore", "AsyncStorage", "LocalAuthentication", "Notifications", "expo-",
        "supabase", "fetch(", "XMLHttpRequest", "rpc(", "/rest/v1/", "/functions/v1/",
        "service_role", "SERVICE_ROLE", "access_token", "refresh_token", "localStorage", "FormData",
    ):
        forbid(router, marker, f"capacité interdite dans le routeur: {marker}")

    for excluded in (
        "/compte/registre-personnel.html",
        "/compte/securite.html",
        "/compte/securite.html#travel-title",
    ):
        forbid(router, excluded, f"chemin sensible volontairement exclu du routeur: {excluded}")

    require("import { NativeModuleRouter, isNativeModulePath } from './NativeModuleRouter';" in app,
            "routeur natif non importé dans App.tsx")
    require("const [nativeModulePath, setNativeModulePath] = useState<NativeModulePath | null>(null);" in app,
            "état de navigation native borné absent")
    require("const openNativeModule = (path: string, tab?: TabKey) =>" in app,
            "dispatcher d'entrée native absent")
    require("if (!isNativeModulePath(path)) return false;" in app and "setNativeModulePath(path);" in app,
            "le dispatcher doit refuser tout chemin hors liste fermée")
    require("if (openNativeModule(item.path)) return;" in app,
            "Alertes/Profil du rail doivent pouvoir ouvrir les hubs natifs")
    require("if (tab.key !== 'home' && openNativeModule(tab.path, tab.key)) return;" in app,
            "les onglets persistants doivent passer par le routeur natif")
    require("nativeSecurityOpen ? (" in app and ") : nativeModulePath ? (" in app and ") : nativeHomeOpen ? (" in app,
            "ordre de rendu Sécurité > module natif > Accueil > Web absent")
    require("<NativeModuleRouter" in app and "path={nativeModulePath}" in app,
            "NativeModuleRouter non rendu dans le shell")
    require("onOpenPath={(path) => void navigateFromNativeModule(path)}" in app and "onBack={closeNativeModule}" in app,
            "sortie Web et retour des hubs persistants non bornés")
    require("setNativeModulePath(null);" in app and "setNativeHomeOpen(false);" in app,
            "la navigation Web doit pouvoir fermer le routeur natif")
    require("!nativeSecurityOpen && !nativeHomeOpen && !nativeModulePath" in app,
            "Partager/Recharger doivent rester masqués sur les hubs natifs")
    require("if (nativeModulePath) {" in app and "closeNativeModule();" in app,
            "retour Android depuis un hub natif doit revenir à l'accueil")

    # Le coffre reste hors routeur et derrière son gate ponctuel existant.
    require("const VAULT_PATH = '/compte/registre-personnel.html';" in app,
            "chemin Registre historique absent")
    require("const VAULT_LOCAL_GATE_MS = 90_000;" in app,
            "fenêtre locale Registre modifiée")
    require("if (isVaultUrl(url) && Date.now() >= vaultLocalGateUntilRef.current)" in app,
            "gate Registre absent de navigateToUrl")
    require("const approved = await requestVaultLocalGate();" in app and "if (!approved) return;" in app,
            "échec du gate Registre doit rester bloquant")
    require("promptMessage: 'Ouvrir mon Registre personnel'" in app,
            "biométrie ponctuelle Registre absente")
    require("if (item.label === 'Sécurité')" in app and "setNativeSecurityOpen(true);" in app,
            "Sécurité doit conserver son hub dédié")
    require("{ label: 'Mode Voyage', path: '/compte/securite.html#travel-title' }" in app,
            "Mode Voyage doit rester sur son chemin Web/serveur")
    require("{ label: 'Registre perso', path: VAULT_PATH }" in app,
            "Registre doit rester dans le rail avec son gate historique")

    require("ne reçoit aucune donnée utilisateur" in doc.lower(),
            "documentation de la frontière sans données absente")
    require("Registre personnel" in doc and "n’est pas" in doc,
            "documentation de l'exclusion du Registre absente")
    require("Mode Voyage reste une fonctionnalité Web/serveur" in doc,
            "documentation de la frontière Mode Voyage absente")
    require("Le raccourci Sécurité continue d’ouvrir directement `NativeSecurityHub`" in doc,
            "documentation du hub Sécurité dédié absente")
    require("L’HUMAIN AVANT TOUT" in doc and "Protéger sans surveiller" in doc,
            "principes de sécurité absents de la documentation")

    required_workflow_markers = (
        "python3 scripts/validate_mobile_native_route_dispatch_v25.py",
        "python3 scripts/validate_mobile_native_personal_ai_hub_v25.py",
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
        "OK routage natif V25: onglets/raccourcis vers les hubs sans données, "
        "Registre et Mode Voyage hors routeur, Sécurité dédiée et sortie Web explicite."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
