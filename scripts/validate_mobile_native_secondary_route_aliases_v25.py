#!/usr/bin/env python3
"""Valide la convergence V25 des routes secondaires vers les hubs natifs existants."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "mobile-native" / "NativeModuleRouter.tsx"
LIBRARY = ROOT / "mobile-native" / "NativeLibraryHub.tsx"
GAMES = ROOT / "mobile-native" / "NativeGamesHub.tsx"
COMMUNITY = ROOT / "mobile-native" / "NativeCommunityHub.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_SECONDARY_ROUTE_ALIASES_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-secondary-route-aliases-v25.yml"
CENTRAL_WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-route-dispatch-v25.yml"


def fail(message: str) -> None:
    print(f"ECHEC alias secondaires natifs V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def require_aliases(router: str, aliases: tuple[str, ...], component: str) -> None:
    positions = []
    for path in aliases:
        require(f"'{path}'" in router, f"route secondaire absente de la liste fermée: {path}")
        case_marker = f"case '{path}':"
        require(case_marker in router, f"route secondaire non dispatchée: {path}")
        positions.append(router.index(case_marker))

    first_case = min(positions)
    expected_return = f"return <{component} onOpenPath={{onOpenPath}} onBack={{onBack}} />;"
    return_pos = router.find("return <", first_case)
    require(return_pos >= 0, f"aucun retour trouvé après les alias de {component}")
    require(router.startswith(expected_return, return_pos),
            f"les alias ne convergent pas directement vers {component}")


def main() -> int:
    for path in (ROUTER, LIBRARY, GAMES, COMMUNITY, DOC, WORKFLOW, CENTRAL_WORKFLOW):
        require(path.is_file(), f"fichier manquant: {path.relative_to(ROOT)}")

    router = ROUTER.read_text("utf-8")
    library = LIBRARY.read_text("utf-8")
    games = GAMES.read_text("utf-8")
    community = COMMUNITY.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")
    central_workflow = CENTRAL_WORKFLOW.read_text("utf-8")

    require("import { NativePrivacyHub } from './NativePrivacyHub';" in router,
            "hub Vie privée absent du routeur")
    require("import { NativeSettingsHub } from './NativeSettingsHub';" in router,
            "hub Paramètres absent du routeur")

    require_aliases(router, (
        "/compte/messages-reels.html",
        "/compte/messages-personnage.html",
    ), "NativeMessagesHub")
    require_aliases(router, (
        "/compte/mes-lectures.html",
        "/compte/documents.html",
        "/compte/playtests.html",
    ), "NativeLibraryHub")
    require_aliases(router, ("/compte/contributions.html",), "NativeGamesHub")
    require_aliases(router, ("/compte/mes-commentaires.html",), "NativeCommunityHub")
    require_aliases(router, ("/compte/mes-personnages.html",), "NativeCharacterHub")
    require_aliases(router, ("/compte/vie-privee.html",), "NativePrivacyHub")
    require_aliases(router, ("/compte/parametres.html",), "NativeSettingsHub")

    for destination in (
        "/compte/mes-lectures.html?surface=web",
        "/compte/documents.html?surface=web",
        "/compte/playtests.html?surface=web",
    ):
        require(destination in library, f"sortie Bibliothèque explicite absente: {destination}")
    require("Aucune admissibilité jeunesse ou invitation dans le natif" in library,
            "frontière playtest jeunesse absente du hub Bibliothèque")
    require("aucune donnée d’âge, de tuteur, de cohorte jeunesse" in library,
            "données jeunesse non explicitement exclues du hub Bibliothèque")

    require("/compte/contributions.html?surface=web" in games,
            "sortie Programme Contributeur explicite absente")
    require("Aucune contribution automatique" in games,
            "frontière de consentement Contributeur absente")
    require("n’active aucun consentement" in games and "commentaire libre" in games,
            "consentement/texte libre non explicitement exclus du hub Jeux")

    require("/compte/mes-commentaires.html?surface=web" in community,
            "sortie Mes commentaires explicite absente")
    require("état en attente, publié ou refusé" in community,
            "état de modération des commentaires non explicitement exclu")

    for text, label in ((router, "routeur"), (library, "Bibliothèque"), (games, "Jeux"), (community, "Communauté")):
        for marker in (
            "WebView", "SecureStore", "AsyncStorage", "LocalAuthentication", "Notifications", "expo-",
            "supabase", "fetch(", "XMLHttpRequest", "rpc(", "/rest/v1/", "/functions/v1/",
            "service_role", "SERVICE_ROLE", "access_token", "refresh_token", "localStorage",
        ):
            forbid(text, marker, f"capacité interdite dans {label}: {marker}")

    props = router.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in (
        "user", "session", "content", "payload", "consent", "comment", "moderation", "invite",
        "playtest", "age", "guardian", "progress", "document", "identity", "characterdata",
    ):
        forbid(props, marker, f"donnée secondaire interdite dans les props du routeur: {marker}")

    excluded = (
        "/compte/registre-personnel.html",
        "/compte/securite.html",
        "/compte/mfa.html",
        "/compte/connexion.html",
        "/compte/inscription.html",
        "/compte/mot-de-passe-oublie.html",
        "/compte/reinitialiser-mot-de-passe.html",
        "/compte/signaler-deces.html",
        "/compte/projet.html",
        "/compte/confidentialite-joueur.html",
    )
    for path in excluded:
        forbid(router, path, f"chemin volontairement Web/sensible ajouté au routeur: {path}")

    doc_fold = doc.casefold()
    for marker in (
        "intentions de navigation",
        "messages-reels.html",
        "messages-personnage.html",
        "playtests.html",
        "contributions.html",
        "mes-commentaires.html",
        "mes-personnages.html",
        "vie-privee.html",
        "parametres.html",
        "registre-personnel.html",
        "mfa.html",
        "signaler-deces.html",
        "projet.html",
        "protéger sans surveiller",
        "l’humain avant tout",
    ):
        require(marker in doc_fold, f"preuve documentaire manquante: {marker}")

    required_workflow = (
        "python3 scripts/validate_mobile_native_secondary_route_aliases_v25.py",
        "python3 scripts/validate_mobile_native_route_dispatch_v25.py",
        "python3 scripts/validate_mobile_native_library_hub_v25.py",
        "python3 scripts/validate_mobile_native_games_hub_v25.py",
        "python3 scripts/validate_mobile_native_community_hub_v25.py",
        "python3 scripts/validate_mobile_native_messages_hub_v25.py",
        "python3 scripts/validate_mobile_native_character_hub_v25.py",
        "python3 scripts/validate_mobile_native_settings_hub_v25.py",
        "python3 scripts/validate_mobile_native_privacy_hub_v25.py",
        "python3 scripts/validate_mobile_navigation_boundary_v25.py",
        "python3 scripts/validate_mobile_safe_share_v25.py",
        "python3 scripts/validate_device_challenge_client_boundary.py",
        "python3 scripts/validate_no_committed_secrets.py",
        "npm run validate:vault",
        "npm run typecheck",
    )
    for marker in required_workflow:
        require(marker in workflow, f"preuve CI manquante: {marker}")

    require("python3 scripts/validate_mobile_native_secondary_route_aliases_v25.py" in central_workflow,
            "le workflow central ne revalide pas les alias secondaires")
    require("mobile-native/NATIVE_SECONDARY_ROUTE_ALIASES_V25.md" in central_workflow,
            "la documentation des alias n’est pas surveillée par le workflow central")

    for checked_workflow, label in ((workflow, "dédié"), (central_workflow, "central")):
        workflow_lower = checked_workflow.lower()
        for marker in ("environment: production", "supabase_access_token", "${{ secrets.", "supabase start", "supabase db"):
            forbid(workflow_lower, marker.lower(), f"production/secret interdit dans le workflow {label}: {marker}")

    print("OK alias secondaires natifs V25: convergence exacte vers les hubs existants, aucune donnée secondaire locale et chemins sensibles exclus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
