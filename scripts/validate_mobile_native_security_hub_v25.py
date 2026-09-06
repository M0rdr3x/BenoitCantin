#!/usr/bin/env python3
"""Valide le hub Sécurité natif V25 sans duplication des données ou privilèges serveur."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "mobile-native" / "App.tsx"
HUB = ROOT / "mobile-native" / "NativeSecurityHub.tsx"
SECURITY_PAGE = ROOT / "compte" / "securite.html"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"ERREUR hub sécurité natif V25: {message}")


def main() -> int:
    require(HUB.is_file(), "NativeSecurityHub.tsx doit exister")
    app = APP.read_text(encoding="utf-8")
    hub = HUB.read_text(encoding="utf-8")
    security_page = SECURITY_PAGE.read_text(encoding="utf-8")
    hub_lower = hub.lower()

    # Le hub est une surface locale d'orchestration, jamais un second client de données.
    for forbidden in (
        "webview",
        "expo-secure-store",
        "securestore",
        "supabase",
        "fetch(",
        "xmlhttprequest",
        "axios",
        "/rest/v1/",
        "/functions/v1/",
        "security_resolve_connection_challenge",
        "security_resolve_connection_challenge_mfa",
        "service_",
        "private.",
        "device_key",
        "last_session_id",
        "vault_session_id",
        "content_payload",
        "access_token",
        "refresh_token",
        "gpvivleexywljowcqkru",
        "expo-location",
        "getcurrentposition",
        "watchposition",
    ):
        require(forbidden not in hub_lower,
                f"le hub ne doit contenir aucun accès privilégié/donnée/API: {forbidden}")

    for marker in (
        "biometricEnabled",
        "pushEnabled",
        "onToggleBiometric",
        "onTogglePush",
        "onOpenPath",
        "onClose",
        "Ce hub natif ne copie aucune donnée du compte",
        "Ce hub ne demande aucun GPS",
        "aucune adresse IP",
        "aucune confidence",
        "ni visage ni empreinte",
        "une seule source de vérité",
        "AAL2/RPC",
    ):
        require(marker in hub, f"contrat explicite absent du hub: {marker}")

    destinations = (
        ("Mes appareils", "/compte/securite.html#devices-title", "devices-title"),
        ("Connexions récentes", "/compte/securite.html#recent-title", "recent-title"),
        ("Mode Voyage", "/compte/securite.html#travel-title", "travel-title"),
        ("Connexions à confirmer", "/compte/securite.html#quick-title", "quick-title"),
        ("Préférences de sécurité", "/compte/securite.html#preferences-title", "preferences-title"),
    )
    for label, path, anchor in destinations:
        require(label in hub, f"destination native absente: {label}")
        require(path in hub, f"destination Web bornée absente: {path}")
        require(f'id="{anchor}"' in security_page,
                f"la destination {label} pointe vers un ancrage Web inexistant: {anchor}")

    # Le shell conserve une seule identité et toute opération réelle passe par la WebView existante.
    for marker in (
        "import { NativeSecurityHub } from './NativeSecurityHub';",
        "const [nativeSecurityOpen, setNativeSecurityOpen] = useState(false);",
        "if (item.label === 'Sécurité')",
        "setNativeSecurityOpen(true);",
        "setNativeSecurityOpen(false);\n    setCurrentUrl(url);",
        "if (nativeSecurityOpen)",
        "<NativeSecurityHub",
        "onToggleBiometric={() => void toggleBiometric()}",
        "onTogglePush={() => void (pushEnabled ? disableSecurityPush() : enableSecurityPush())}",
        "onOpenPath={(path) => void navigate(path)}",
        "onClose={() => setNativeSecurityOpen(false)}",
        ") : (\n        <WebView",
    ):
        require(marker in app, f"intégration shell absente: {marker}")

    back_block = app.split("BackHandler.addEventListener('hardwareBackPress'", 1)[1].split(
        "return () => subscription.remove();", 1
    )[0]
    require("if (nativeSecurityOpen)" in back_block and "setNativeSecurityOpen(false)" in back_block,
            "Android doit fermer le hub natif avant de remonter l'historique Web")

    top_actions = app.split("<View style={styles.topActions}>", 1)[1].split("</View>", 1)[0]
    require("!nativeSecurityOpen" in top_actions,
            "Partager/Recharger doivent être masqués pendant l'écran natif")

    # Les protections sensibles historiques restent obligatoires dans le shell.
    for marker in (
        "requestVaultLocalGate",
        "VAULT_LOCAL_GATE_MS",
        "thirdPartyCookiesEnabled={false}",
        "originWhitelist={['https://*']}",
        "SecureStore.getItemAsync(DEVICE_KEY_STORAGE)",
        "WEB_DEVICE_KEY_STORAGE",
        "sharePublicSinjiraUrl",
    ):
        require(marker in app, f"protection mobile historique perdue: {marker}")

    print(
        "OK hub sécurité natif V25: état local biométrie/push seulement, aucune donnée privée/API dupliquée, destinations Web existantes et protections mobiles historiques conservées."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
