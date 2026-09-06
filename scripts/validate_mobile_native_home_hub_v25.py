#!/usr/bin/env python3
"""Valide la frontière V25 de l'accueil React Native minimal."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "mobile-native" / "App.tsx"
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
SECURITY = ROOT / "mobile-native" / "NativeSecurityHub.tsx"
README = ROOT / "mobile-native" / "README.md"
VAULT_GUARD = ROOT / "mobile-native" / "scripts" / "validate-vault-mobile.mjs"
NAV_GUARD = ROOT / "scripts" / "validate_mobile_navigation_boundary_v25.py"
SHARE_GUARD = ROOT / "scripts" / "validate_mobile_safe_share_v25.py"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-home-hub-v25.yml"


def fail(message: str) -> None:
    print(f"ECHEC accueil natif V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def main() -> int:
    for path in (APP, HOME, SECURITY, README, VAULT_GUARD, NAV_GUARD, SHARE_GUARD, WORKFLOW):
        require(path.is_file(), f"fichier manquant: {path.relative_to(ROOT)}")

    app = APP.read_text("utf-8")
    home = HOME.read_text("utf-8")
    security = SECURITY.read_text("utf-8")
    readme = README.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    # L'accueil est une surface de navigation uniquement. Il ne possède aucune source de vérité.
    require("export function NativeHomeHub({ onOpenPath, onOpenSecurity }: Props)" in home,
            "signature minimale NativeHomeHub absente")
    require("onOpenPath: (path: string) => void;" in home and "onOpenSecurity: () => void;" in home,
            "les seules capacités attendues sont la navigation et l'ouverture du hub sécurité")

    forbidden_home = (
        "WebView",
        "SecureStore",
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
        "device_key",
        "access_token",
        "refresh_token",
        "pushToken",
        "nativeDeviceKey",
        "localStorage",
        "AsyncStorage",
    )
    for marker in forbidden_home:
        forbid(home, marker, f"capacité interdite dans l'accueil natif: {marker}")

    # Aucun contenu utilisateur n'est demandé en props ni synthétisé en compteur/flux local.
    props_block = home.split("type Props = {", 1)[1].split("};", 1)[0]
    for marker in ("user", "profile", "message", "count", "application", "match", "entry", "content", "token", "device"):
        forbid(props_block.lower(), marker, f"donnée utilisateur interdite dans les props: {marker}")

    required_paths = (
        "/compte/messages.html",
        "/compte/rencontres.html",
        "/compte/emploi.html",
        "/compte/monde-parallele.html",
        "/compte/mon-ia.html",
        "/compte/notifications.html",
        "/compte/profil.html",
        "/compte/securite.html#travel-title",
        "/compte/registre-personnel.html",
    )
    for path in required_paths:
        require(path in home, f"destination native manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in home, "principe humain absent de l'accueil")
    require("Zone extrêmement sensible" in home, "le Registre doit être présenté comme zone extrêmement sensible")
    require("aucun message, profil, candidature, rencontre, confidence ni contenu privé" in home,
            "la non-copie des données privées doit être explicite")

    # App.tsx garde l'orchestration sensible : l'accueil ne remplace ni le gate Registre ni le hub sécurité.
    require("import { NativeHomeHub } from './NativeHomeHub';" in app,
            "NativeHomeHub non importé dans le shell")
    require("const [nativeHomeOpen, setNativeHomeOpen] = useState(true);" in app,
            "l'accueil natif doit être l'écran initial")
    require("function isNativeHomeUrl(url: string)" in app,
            "détection bornée de /app/ absente")
    require("parsed.pathname === '/app/' && !parsed.search && !parsed.hash" in app,
            "seule la racine /app/ sans état doit être remplacée par le natif")
    require("if (isNativeHomeUrl(url))" in app and "setNativeHomeOpen(true);" in app,
            "la navigation vers /app/ doit ouvrir le hub natif")
    require("setNativeHomeOpen(false);" in app,
            "une vraie destination Web doit fermer l'accueil natif")
    require("!nativeSecurityOpen && !nativeHomeOpen" in app,
            "Partager/Recharger doivent rester masqués pendant les surfaces natives")
    require("nativeSecurityOpen ? (" in app and "nativeHomeOpen ? (" in app,
            "priorité de rendu sécurité > accueil > WebView absente")
    require("<NativeHomeHub" in app and "onOpenPath={(path) => void navigate(path)}" in app,
            "les destinations de l'accueil doivent passer par navigate()")
    require("onOpenSecurity={() => setNativeSecurityOpen(true)}" in app,
            "Ma sécurité doit ouvrir le hub natif existant")

    # Le Registre reste derrière le gate local existant; le natif n'a aucun chemin alternatif.
    require("if (isVaultUrl(url) && Date.now() >= vaultLocalGateUntilRef.current)" in app,
            "gate local Registre absent de navigateToUrl")
    require("const approved = await requestVaultLocalGate();" in app and "if (!approved) return;" in app,
            "échec du gate Registre doit rester bloquant")
    require("promptMessage: 'Ouvrir mon Registre personnel'" in app,
            "vérification locale ponctuelle du Registre absente")

    # Le hub sécurité déjà migré doit rester lui aussi sans source de vérité serveur locale.
    for marker in ("WebView", "SecureStore", "supabase", "fetch(", "rpc(", "device_key"):
        forbid(security, marker, f"régression du hub sécurité existant: {marker}")

    require("### Accueil natif minimal" in readme,
            "documentation de la nouvelle frontière native absente")
    require("aucune donnée utilisateur" in readme.lower(),
            "README doit expliciter l'absence de données utilisateur dans l'accueil natif")

    # La CI rechaîne toutes les frontières mobiles sensibles existantes.
    required_workflow_markers = (
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
        "OK accueil natif V25: navigation uniquement, aucune donnée utilisateur copiée, "
        "Registre toujours derrière son gate et frontières sécurité/navigation/partage rechaînées."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
