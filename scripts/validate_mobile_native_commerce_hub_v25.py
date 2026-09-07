#!/usr/bin/env python3
"""Valide la frontière V25 du hub Commerce React Native."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "mobile-native" / "NativeCommerceHub.tsx"
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
ROUTER = ROOT / "mobile-native" / "NativeModuleRouter.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_COMMERCE_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-commerce-hub-v25.yml"


def fail(message: str) -> None:
    print(f"ECHEC hub Commerce natif V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def main() -> int:
    for path in (HUB, HOME, ROUTER, DOC, WORKFLOW):
        require(path.is_file(), f"fichier manquant: {path.relative_to(ROOT)}")

    hub = HUB.read_text("utf-8")
    home = HOME.read_text("utf-8")
    router = ROUTER.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeCommerceHub({ onOpenPath, onBack }: Props)" in hub,
            "signature minimale du hub absente")
    props = hub.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in (
        "user", "balance", "ledger", "token", "purchase", "order", "preorder", "listing", "price",
        "location", "license", "entitlement", "payment", "card", "address", "receipt", "count", "role",
    ):
        forbid(props, marker, f"donnée commerciale interdite dans les props: {marker}")

    for marker in (
        "WebView", "SecureStore", "AsyncStorage", "LocalAuthentication", "Notifications", "Clipboard", "expo-",
        "supabase", "fetch(", "XMLHttpRequest", "rpc(", "/rest/v1/", "/functions/v1/", "localStorage",
        "service_role", "SERVICE_ROLE", "access_token", "refresh_token", "FormData", "Stripe", "PaymentSheet",
    ):
        forbid(hub, marker, f"capacité interdite dans le hub: {marker}")

    for path in (
        "/compte/mes-achats.html?surface=web",
        "/compte/marche.html?surface=web",
        "/compte/jetons.html?surface=web",
        "/compte/licences.html?surface=web",
    ):
        require(path in hub, f"destination attendue absente: {path}")

    for marker in (
        "aucun solde de jetons, mouvement, achat, précommande, préférence de réception, annonce, prix, localisation, licence ou droit numérique",
        "Aucun profil d’achat local",
        "Aucun checkout ni moyen de paiement dans ce sas",
        "Le grand livre reste côté serveur",
        "Les brouillons et la localisation restent privés",
        "Vos choix commerciaux ne définissent pas votre valeur",
        "L’HUMAIN AVANT TOUT",
        "PROTÉGER SANS SURVEILLER",
    ):
        require(marker in hub, f"frontière explicite absente du hub: {marker}")

    require("import { NativeCommerceHub } from './NativeCommerceHub';" in home,
            "Commerce non importé dans l'accueil")
    require("path: '/compte/mes-achats.html'" in home and "setCommerceHubOpen(true);" in home,
            "Accueil ne route pas Commerce vers le hub")
    require("import { NativeCommerceHub } from './NativeCommerceHub';" in router,
            "Commerce non importé dans le routeur")
    require("'/compte/mes-achats.html'" in router and "<NativeCommerceHub" in router,
            "route Commerce native absente")
    for alias in (
        "/compte/marche.html",
        "/compte/jetons.html",
        "/compte/licences.html",
    ):
        require(f"case '{alias}':" in router,
                f"alias Commerce absent du routeur natif: {alias}")
    require(router.count("return <NativeCommerceHub") == 1,
            "les alias Commerce doivent converger vers une seule implémentation du hub")

    doc_fold = doc.casefold()
    for marker in (
        "ne devient jamais un portefeuille, un checkout, un grand livre, une boutique",
        "une réservation n’est pas une commande",
        "ne crédite, débite ou transfère aucun Jeton",
        "ne conserve jamais sa localisation approximative",
        "Pas de profil commercial",
        "L’HUMAIN AVANT TOUT",
        "Protéger sans surveiller",
    ):
        require(marker.casefold() in doc_fold, f"preuve documentaire manquante: {marker}")

    required_workflow = (
        "python3 scripts/validate_mobile_native_commerce_hub_v25.py",
        "python3 scripts/validate_mobile_native_route_dispatch_v25.py",
        "python3 scripts/validate_mobile_native_home_hub_v25.py",
        "python3 scripts/validate_mobile_native_library_hub_v25.py",
        "python3 scripts/validate_mobile_navigation_boundary_v25.py",
        "python3 scripts/validate_mobile_safe_share_v25.py",
        "python3 scripts/validate_device_challenge_client_boundary.py",
        "python3 scripts/validate_no_committed_secrets.py",
        "npm run validate:vault",
        "npm run typecheck",
    )
    for marker in required_workflow:
        require(marker in workflow, f"preuve CI manquante: {marker}")

    for marker in ("environment: production", "SUPABASE_ACCESS_TOKEN", "${{ secrets.", "supabase start", "supabase db", "stripe"):
        forbid(workflow.lower(), marker.lower(), f"production/paiement interdit dans ce workflow: {marker}")

    print("OK hub Commerce natif V25: navigation seulement, aucune donnée ou opération commerciale locale.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
