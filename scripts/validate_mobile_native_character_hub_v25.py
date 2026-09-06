#!/usr/bin/env python3
"""Valide la frontière V25 du hub Mon personnage React Native sans fiche humaine ni données narratives locales."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
ROUTER = ROOT / "mobile-native" / "NativeModuleRouter.tsx"
CHARACTER = ROOT / "mobile-native" / "NativeCharacterHub.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_CHARACTER_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-character-hub-v25.yml"
OWNER_GUARD = ROOT / "scripts" / "validate_owner_character_rpc_v24_5_20.py"
LEDGER_GUARD = ROOT / "scripts" / "validate_production_migration_ledger.py"
ROUTE_GUARD = ROOT / "scripts" / "validate_mobile_native_route_dispatch_v25.py"
PARALLEL_GUARD = ROOT / "scripts" / "validate_mobile_native_parallel_world_hub_v25.py"
LIFE_STORY_GUARD = ROOT / "scripts" / "validate_mobile_native_life_story_hub_v25.py"
HOME_GUARD = ROOT / "scripts" / "validate_mobile_native_home_hub_v25.py"
SECURITY_GUARD = ROOT / "scripts" / "validate_mobile_native_security_hub_v25.py"
NAV_GUARD = ROOT / "scripts" / "validate_mobile_navigation_boundary_v25.py"
SHARE_GUARD = ROOT / "scripts" / "validate_mobile_safe_share_v25.py"
CHALLENGE_GUARD = ROOT / "scripts" / "validate_device_challenge_client_boundary.py"
SECRET_GUARD = ROOT / "scripts" / "validate_no_committed_secrets.py"
VAULT_GUARD = ROOT / "mobile-native" / "scripts" / "validate-vault-mobile.mjs"


def fail(message: str) -> None:
    print(f"ECHEC hub Mon personnage natif V25: {message}", file=sys.stderr)
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
        ROUTER,
        CHARACTER,
        DOC,
        WORKFLOW,
        OWNER_GUARD,
        LEDGER_GUARD,
        ROUTE_GUARD,
        PARALLEL_GUARD,
        LIFE_STORY_GUARD,
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
    router = ROUTER.read_text("utf-8")
    character = CHARACTER.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeCharacterHub({ onOpenPath, onBack }: Props)" in character,
            "signature minimale NativeCharacterHub absente")
    require("onOpenPath: (path: string) => void;" in character and "onBack: () => void;" in character,
            "le hub personnage doit avoir seulement navigation et retour comme capacités")

    forbidden_character = (
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
        "character_submissions",
        "s.from('characters')",
        's.from("characters")',
        "ensure_sinjira_owner_character",
        "access_token",
        "refresh_token",
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "FormData",
    )
    for marker in forbidden_character:
        forbid(character, marker, f"capacité ou donnée interdite dans le hub personnage: {marker}")

    props_block = character.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in (
        "user", "character", "personnage", "submission", "portrait", "bible", "psychology", "status",
        "canon", "novel", "name", "description", "registre", "owner", "repair", "token", "device"
    ):
        forbid(props_block, marker, f"donnée utilisateur interdite dans les props: {marker}")

    required_paths = (
        "/compte/mon-personnage.html?surface=web",
        "/compte/monde-parallele.html?surface=web",
        "/compte/securite.html",
        "/compte/vie-privee.html?surface=web",
    )
    for path in required_paths:
        require(path in character, f"destination Mon personnage manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in character, "principe humain absent du hub personnage")
    require("PROTÉGER SANS SURVEILLER" in character, "principe de protection absent du hub personnage")
    require("ne lit aucun nom public, portrait, description, bible narrative, psychologie, statut, canon, roman, soumission ni fiche humaine source" in character,
            "la non-lecture des données personnage doit être explicite")
    require("La fiche humaine source reste privée" in character,
            "la séparation avec la fiche humaine source doit être explicite")
    require("le questionnaire humain et ses réponses privées ne sont pas copiés dans ce hub" in character,
            "la non-copie du questionnaire humain doit être explicite")
    require("Le natif ne transforme personne en personnage" in character,
            "la frontière humaine de création doit être explicite")
    require("ne crée, n’approuve, ne refuse, n’archive et n’attribue aucun personnage à un roman" in character,
            "les mutations narratives doivent rester hors du natif")
    require("Il ne décide jamais du canon, de la psychologie narrative ou de la visibilité d’une fiche" in character,
            "les décisions narratives doivent rester humaines")
    require("Le natif n’appelle aucune réparation propriétaire" in character,
            "la réparation propriétaire doit rester serveur")
    require("Les vérifications authentifiées et la persistance restent dans les mécanismes Web et serveur existants" in character,
            "la source de vérité serveur doit être explicite")
    require("Compte, personnage et continuité restent distincts" in character,
            "le cloisonnement des identités doit être explicite")
    require("Ce hub ne reçoit aucune clé interne permettant de relier ces couches" in character,
            "la non-corrélation native doit être explicite")
    require("Votre personne n’est pas votre fiche narrative" in character,
            "la séparation personne/représentation narrative doit être explicite")

    require("import { NativeCharacterHub } from './NativeCharacterHub';" in home,
            "NativeCharacterHub non relié à l'accueil natif")
    require("const [characterHubOpen, setCharacterHubOpen] = useState(false);" in home,
            "état local du hub personnage absent de l'accueil")
    require("if (path === '/compte/mon-personnage.html')" in home and "setCharacterHubOpen(true);" in home,
            "la destination Mon personnage doit ouvrir le hub natif")
    require("<NativeCharacterHub" in home and "onBack={() => setCharacterHubOpen(false)}" in home,
            "retour du hub personnage vers Accueil absent")
    require("sans fiche humaine, portrait, bible narrative ni statut" in home,
            "la carte Accueil doit expliciter l'absence de données personnage")

    require("import { NativeCharacterHub } from './NativeCharacterHub';" in router,
            "NativeCharacterHub non relié au routeur central")
    require("'/compte/mon-personnage.html'," in router,
            "route Mon personnage absente de la liste fermée")
    require("case '/compte/mon-personnage.html':" in router and "return <NativeCharacterHub" in router,
            "dispatch Mon personnage absent du routeur")

    require("ne reçoit aucune donnée de personnage" in doc,
            "documentation de la frontière sans données absente")
    require("n’appelle ni Supabase, ni RPC, ni Edge Function, ni API réseau" in doc,
            "documentation de la frontière serveur absente")
    require("fiche humaine source issue du Registre reste privée" in doc,
            "documentation de la source humaine privée absente")
    require("ne remplit ni n’envoie le questionnaire du Registre" in doc,
            "documentation de la non-soumission native absente")
    require("ensure_sinjira_owner_character" in doc and "frontière serveur authentifiée" in doc,
            "documentation de la réparation propriétaire absente")
    require("ne l’appelle pas, ne reproduit pas sa logique" in doc,
            "documentation de l'absence de réparation native absente")
    require("Registre personnel des consciences reste soumis à son propre gate sensible" in doc,
            "documentation du gate Registre absente")
    require("compte humain, le personnage public/narratif et les identifiants techniques privés restent des couches distinctes" in doc,
            "documentation du cloisonnement des identités absente")
    require("L’HUMAIN AVANT TOUT" in doc and "Protéger sans surveiller" in doc,
            "principes de sécurité absents de la documentation")

    required_workflow_markers = (
        "python3 scripts/validate_mobile_native_character_hub_v25.py",
        "python3 scripts/validate_owner_character_rpc_v24_5_20.py",
        "python3 scripts/validate_production_migration_ledger.py",
        "python3 scripts/validate_mobile_native_route_dispatch_v25.py",
        "python3 scripts/validate_mobile_native_parallel_world_hub_v25.py",
        "python3 scripts/validate_mobile_native_life_story_hub_v25.py",
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

    for marker in ("environment: production", "SUPABASE_ACCESS_TOKEN", "${{ secrets.", "supabase start", "supabase db push"):
        forbid(workflow, marker, f"production/secret interdit dans ce workflow: {marker}")

    print(
        "OK hub Mon personnage natif V25: navigation seulement, fiche humaine et représentation narrative absentes du natif, "
        "réparation authentifiée conservée côté serveur et identités cloisonnées."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
