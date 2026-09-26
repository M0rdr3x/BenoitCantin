#!/usr/bin/env python3
"""Valide la frontière V25 de l'accueil React Native, y compris le mode Junior fail-closed."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "mobile-native" / "App.tsx"
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
SECURITY = ROOT / "mobile-native" / "NativeSecurityHub.tsx"
README = ROOT / "mobile-native" / "README.md"
ACCOUNT = ROOT / "assets" / "js" / "sinjira-account.js"
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
    for path in (APP, HOME, SECURITY, README, ACCOUNT, VAULT_GUARD, NAV_GUARD, SHARE_GUARD, WORKFLOW):
        require(path.is_file(), f"fichier manquant: {path.relative_to(ROOT)}")

    app = APP.read_text("utf-8")
    home = HOME.read_text("utf-8")
    security = SECURITY.read_text("utf-8")
    readme = README.read_text("utf-8")
    account = ACCOUNT.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeHomeHub({ onOpenPath, onOpenSecurity, accountMode }: Props)" in home,
            "signature NativeHomeHub avec état d'accès minimal absente")
    require("accountMode: 'unknown' | 'child' | 'nonchild';" in home,
            "accountMode doit rester borné à unknown/child/nonchild")
    require("onOpenPath: (path: string) => void;" in home and "onOpenSecurity: () => void;" in home,
            "capacités navigation/sécurité absentes")

    forbidden_home = (
        "WebView", "SecureStore", "LocalAuthentication", "Notifications", "expo-", "supabase",
        "fetch(", "XMLHttpRequest", "rpc(", "/rest/v1/", "/functions/v1/", "service_role",
        "SERVICE_ROLE", "device_key", "access_token", "refresh_token", "pushToken",
        "nativeDeviceKey", "localStorage", "AsyncStorage",
    )
    for marker in forbidden_home:
        forbid(home, marker, f"capacité interdite dans l'accueil natif: {marker}")

    props_block = home.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in ("user", "profile", "message", "application", "match", "entry", "content", "token", "device", "birth", "email", "uuid"):
        forbid(props_block, marker, f"donnée personnelle interdite dans les props: {marker}")

    require("if (accountMode !== 'nonchild')" in home,
            "unknown/child ne sont pas fail-closed avant les hubs généraux")
    require("const childDestinations = [" in home and "const unverifiedDestinations = [" in home,
            "destinations Junior/inconnues distinctes absentes")
    for marker in ("Communauté Junior", "Bibliothèque Junior", "Relations et famille"):
        require(marker in home, f"destination Junior sûre absente: {marker}")
    require("Messages, Rencontres, Emploi, Monde parallèle, Mon IA, commerce et playtests" in home,
            "liste explicite des destinations non Junior absente")
    require("aucun âge exact, courriel ou identifiant utilisateur" in home.lower(),
            "minimisation de l'état Junior non expliquée")

    required_paths = (
        "/compte/messages.html", "/compte/rencontres.html", "/compte/emploi.html",
        "/compte/monde-parallele.html", "/compte/mon-ia.html", "/compte/notifications.html",
        "/compte/profil.html", "/compte/securite.html#travel-title", "/compte/registre-personnel.html",
    )
    for path in required_paths:
        require(path in home, f"destination native générale manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in home, "principe humain absent de l'accueil")
    require("Zone extrêmement sensible" in home, "Registre non présenté comme zone extrêmement sensible")

    require("const [nativeHomeOpen, setNativeHomeOpen] = useState(true);" in app,
            "l'accueil natif doit rester l'écran initial")
    require("const [childAccess, setChildAccess] = useState<ChildAccessState>('unknown');" in app,
            "le shell ne démarre pas fail-closed")
    require("const visibleTabs = childAccess === 'child' ? childTabs : childAccess === 'nonchild' ? adultTabs : unverifiedTabs;" in app,
            "onglets non adaptés à child/unknown")
    require("if (childAccess !== 'nonchild') return false;" in app,
            "un hub natif général peut s'ouvrir avant preuve non-Junior")
    require("accountMode={childAccess}" in app, "NativeHomeHub ne reçoit pas l'état coarse")
    require("onMessage={onWebMessage}" in app, "pont Web→natif absent")
    require("message?.type !== 'sinjira:child-access'" in app, "type de message natif non borné")
    require("!source.pathname.startsWith('/compte/')" in app, "message accepté hors /compte/")
    require("parsed.pathname === '/compte/connexion.html' || parsed.pathname === '/compte/inscription.html'" in app,
            "connexion/inscription ne réinitialisent pas l'état en inconnu")
    require("const CHILD_ACCOUNT_REDIRECTS = new Map<string, string>([" in app,
            "redirections Junior natives absentes")
    require("const CHILD_RESTRICTED_ACCOUNT_PATHS = new Set([" in app,
            "liste native des routes child restreintes absente")
    for path in (
        "/compte/messages.html", "/compte/rencontres.html", "/compte/emploi.html",
        "/compte/playtests.html", "/compte/mon-ia.html", "/compte/monde-parallele.html",
        "/compte/mes-achats.html", "/compte/licences.html",
    ):
        require(path in app, f"route restreinte child absente du shell natif: {path}")
    require("safeRedirect" in app and "'junior'" in app and "await navigateToUrl" in app,
            "les deep links child connus ne sont pas redirigés avant chargement")
    require("const safeRedirect = childAccountRedirect(parsed.pathname);" in app,
            "les liens Web child ne sont pas filtrés par shouldStart")

    require("function postNativeChildAccess(state)" in account, "pont compte→mobile absent")
    require("type:'sinjira:child-access'" in account and "state:normalized" in account,
            "message coarse compte→mobile absent")
    require("const accountMode=String(capabilities.account_mode||'restricted');" in account,
            "le pont natif ne lit pas account_mode")
    require("postNativeChildAccess(childAccount?'child':accountMode==='standard'?'nonchild':'unknown')" in account,
            "restricted/pending/unverified pourraient être publiés comme nonchild")
    bridge = account.split("function postNativeChildAccess(state)", 1)[1].split("async function initAgeAccessNavigation", 1)[0].lower()
    for marker in ("birth_date", "date_of_birth", "email", "user.id", "uuid"):
        forbid(bridge, marker, f"donnée personnelle transmise dans le pont natif: {marker}")

    require("if (isVaultUrl(url) && Date.now() >= vaultLocalGateUntilRef.current)" in app,
            "gate local Registre absent")
    require("const approved = await requestVaultLocalGate();" in app and "if (!approved) return;" in app,
            "échec du gate Registre non bloquant")
    require("promptMessage: 'Ouvrir mon Registre personnel'" in app,
            "vérification locale ponctuelle du Registre absente")

    for marker in ("WebView", "SecureStore", "supabase", "fetch(", "rpc(", "device_key"):
        forbid(security, marker, f"régression du hub sécurité: {marker}")

    require("### Accueil natif minimal" in readme, "documentation accueil natif absente")
    require("aucune donnée personnelle" in readme.lower(), "README n'explicite pas la minimisation")
    require("`unknown`, `child` ou `nonchild`" in readme, "README ne documente pas l'état coarse")

    required_workflow_markers = (
        "python3 scripts/validate_mobile_native_home_hub_v25.py",
        "python3 scripts/validate_mobile_native_security_hub_v25.py",
        "python3 scripts/validate_mobile_navigation_boundary_v25.py",
        "python3 scripts/validate_mobile_safe_share_v25.py",
        "python3 scripts/validate_device_challenge_client_boundary.py",
        "python3 scripts/validate_no_committed_secrets.py",
        "npm run validate:vault", "npm run typecheck",
    )
    for marker in required_workflow_markers:
        require(marker in workflow, f"preuve CI manquante: {marker}")
    for marker in ("environment: production", "SUPABASE_ACCESS_TOKEN", "${{ secrets.", "supabase start", "supabase db"):
        forbid(workflow, marker, f"production/secret interdit dans ce workflow: {marker}")

    print("OK accueil natif V25: unknown/child fail-closed, état coarse sans identité, hubs généraux réservés à nonchild et Registre toujours protégé.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
