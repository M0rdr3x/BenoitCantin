#!/usr/bin/env python3
"""Valide la frontière V25 du hub Histoire de vie React Native sans données ni opérations posthumes locales."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "mobile-native" / "NativeHomeHub.tsx"
ROUTER = ROOT / "mobile-native" / "NativeModuleRouter.tsx"
LIFE_STORY = ROOT / "mobile-native" / "NativeLifeStoryHub.tsx"
DOC = ROOT / "mobile-native" / "NATIVE_LIFE_STORY_HUB_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-native-life-story-hub-v25.yml"
LIFE_STORY_CONTRACT = ROOT / "scripts" / "validate_life_story_legacy_v24_5_2.py"
LIFE_STORY_FK_GUARD = ROOT / "scripts" / "validate_life_story_fk_indexes_v24_5_2.py"
LEDGER_GUARD = ROOT / "scripts" / "validate_production_migration_ledger.py"
ROUTE_GUARD = ROOT / "scripts" / "validate_mobile_native_route_dispatch_v25.py"
PERSONAL_AI_GUARD = ROOT / "scripts" / "validate_mobile_native_personal_ai_hub_v25.py"
HOME_GUARD = ROOT / "scripts" / "validate_mobile_native_home_hub_v25.py"
SECURITY_GUARD = ROOT / "scripts" / "validate_mobile_native_security_hub_v25.py"
NAV_GUARD = ROOT / "scripts" / "validate_mobile_navigation_boundary_v25.py"
SHARE_GUARD = ROOT / "scripts" / "validate_mobile_safe_share_v25.py"
CHALLENGE_GUARD = ROOT / "scripts" / "validate_device_challenge_client_boundary.py"
SECRET_GUARD = ROOT / "scripts" / "validate_no_committed_secrets.py"
VAULT_GUARD = ROOT / "mobile-native" / "scripts" / "validate-vault-mobile.mjs"


def fail(message: str) -> None:
    print(f"ECHEC hub Histoire de vie natif V25: {message}", file=sys.stderr)
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
        LIFE_STORY,
        DOC,
        WORKFLOW,
        LIFE_STORY_CONTRACT,
        LIFE_STORY_FK_GUARD,
        LEDGER_GUARD,
        ROUTE_GUARD,
        PERSONAL_AI_GUARD,
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
    life_story = LIFE_STORY.read_text("utf-8")
    doc = DOC.read_text("utf-8")
    workflow = WORKFLOW.read_text("utf-8")

    require("export function NativeLifeStoryHub({ onOpenPath, onBack }: Props)" in life_story,
            "signature minimale NativeLifeStoryHub absente")
    require("onOpenPath: (path: string) => void;" in life_story and "onBack: () => void;" in life_story,
            "le hub Histoire de vie doit avoir seulement navigation et retour comme capacités")

    forbidden_life_story = (
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
        "life_story_entries",
        "life_story_versions",
        "life_story_version_entries",
        "life_story_recipients",
        "life_story_legacy_settings",
        "life_story_my_posthumous_case",
        "life_story_create_report_code",
        "life_story_list_report_codes",
        "life_story_revoke_report_code",
        "life_story_contest_death_verification",
        "navigator.clipboard",
        "writeText(",
        "access_token",
        "refresh_token",
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "FormData",
    )
    for marker in forbidden_life_story:
        forbid(life_story, marker, f"capacité ou donnée interdite dans le hub Histoire de vie: {marker}")

    props_block = life_story.split("type Props = {", 1)[1].split("};", 1)[0].lower()
    for marker in (
        "user", "entry", "story", "memory", "version", "recipient", "email", "directive",
        "death", "case", "report", "code", "preview", "pdf", "mfa", "risk", "device", "token"
    ):
        forbid(props_block, marker, f"donnée utilisateur interdite dans les props: {marker}")

    required_paths = (
        "/compte/histoire-de-vie.html?surface=web",
        "/compte/securite.html",
        "/compte/vie-privee.html?surface=web",
        "/compte/mon-ia.html?surface=web",
    )
    for path in required_paths:
        require(path in life_story, f"destination Histoire de vie manquante: {path}")

    require("L’HUMAIN AVANT TOUT" in life_story, "principe humain absent du hub Histoire de vie")
    require("PROTÉGER SANS SURVEILLER" in life_story, "principe de protection absent du hub Histoire de vie")
    require("ne lit aucun souvenir, récit, titre, date, version, destinataire, courriel, directive, dossier posthume, code privé ou aperçu" in life_story,
            "la non-lecture des données Histoire de vie doit être explicite")
    require("Le natif ne crée, ne modifie, n’autorise, ne classe et ne supprime aucun élément Histoire de vie" in life_story,
            "la frontière des mutations Histoire de vie doit être explicite")
    require("Enregistrer un souvenir, l’autoriser pour une œuvre et choisir une version restent trois décisions distinctes" in life_story,
            "les trois décisions de consentement doivent rester distinctes")
    require("Le hub ne signale ni ne valide un décès, ne choisit aucun destinataire et ne prépare aucun PDF" in life_story,
            "les opérations posthumes doivent rester hors du natif")
    require("un délai de sécurité de 30 jours sans contestation et une deuxième validation humaine" in life_story,
            "le délai de 30 jours et la deuxième validation humaine doivent être explicites")
    require("Ce composant ne lit aucun état de procédure et n’enregistre aucune contestation" in life_story,
            "la contestation doit rester hors du natif")
    require("suspend la suite du processus jusqu’à révision humaine" in life_story,
            "l'effet bloquant d'une contestation doit rester explicite")
    require("ne crée, n’affiche, ne copie ni ne révoque de code privé de signalement de décès" in life_story,
            "les codes privés de signalement doivent rester hors du natif")
    require("ne lit ni ne stocke le nom, la description ou le courriel d’un proche" in life_story,
            "les coordonnées des proches doivent rester hors du natif")
    require("Le Registre personnel n’entre jamais dans Histoire de vie automatiquement" in life_story,
            "la séparation du Registre doit être explicite")
    require("AUCUN CLONE IA" in life_story and "ne crée aucun clone IA" in life_story,
            "l'absence de clone IA doit être explicite")

    require("import { NativeLifeStoryHub } from './NativeLifeStoryHub';" in home,
            "NativeLifeStoryHub non relié à l'accueil natif")
    require("const [lifeStoryHubOpen, setLifeStoryHubOpen] = useState(false);" in home,
            "état local Histoire de vie absent de l'accueil")
    require("if (path === '/compte/histoire-de-vie.html')" in home and "setLifeStoryHubOpen(true);" in home,
            "la destination Histoire de vie doit ouvrir le hub natif")
    require("<NativeLifeStoryHub" in home and "onBack={() => setLifeStoryHubOpen(false)}" in home,
            "retour du hub Histoire de vie vers Accueil absent")
    require("sans souvenir, destinataire ni directive" in home,
            "la carte Accueil doit expliciter l'absence de données Histoire de vie")

    require("import { NativeLifeStoryHub } from './NativeLifeStoryHub';" in router,
            "NativeLifeStoryHub non relié au routeur natif central")
    require("'/compte/histoire-de-vie.html'," in router,
            "route Histoire de vie absente de la liste fermée")
    require("case '/compte/histoire-de-vie.html':" in router and "return <NativeLifeStoryHub" in router,
            "dispatch Histoire de vie absent du routeur")

    require("ne reçoit aucune donnée utilisateur Histoire de vie" in doc,
            "documentation de la frontière sans données absente")
    require("n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau" in doc,
            "documentation de la frontière serveur absente")
    require("enregistrer un élément, qui reste privé par défaut" in doc,
            "documentation du caractère privé par défaut absente")
    require("Ouvrir le hub natif ne réalise aucune de ces décisions et ne vaut jamais consentement" in doc,
            "documentation du consentement explicite absente")
    require("La surface Web existante conserve son exigence AAL2" in doc,
            "documentation AAL2 absente")
    require("délai de sécurité de **30 jours**" in doc and "**deuxième validation humaine**" in doc,
            "documentation du protocole posthume absente")
    require("Une contestation suspend la suite du processus" in doc,
            "documentation de la contestation bloquante absente")
    require("Registre personnel des consciences" in doc and "jamais inclus automatiquement" in doc,
            "documentation de la séparation Registre absente")
    require("aucun clone IA après décès" in doc,
            "documentation de l'absence de clone IA absente")
    require("L’HUMAIN AVANT TOUT" in doc and "Protéger sans surveiller" in doc,
            "principes de sécurité absents de la documentation")

    required_workflow_markers = (
        "python3 scripts/validate_mobile_native_life_story_hub_v25.py",
        "python3 scripts/validate_life_story_legacy_v24_5_2.py",
        "python3 scripts/validate_life_story_fk_indexes_v24_5_2.py",
        "python3 scripts/validate_production_migration_ledger.py",
        "python3 scripts/validate_mobile_native_route_dispatch_v25.py",
        "python3 scripts/validate_mobile_native_personal_ai_hub_v25.py",
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
        "OK hub Histoire de vie natif V25: navigation seulement, aucune donnée/coordonnée/code privé local, "
        "AAL2 et consentements conservés côté Web/serveur, protocole posthume humain inchangé."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
