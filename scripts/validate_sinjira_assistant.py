from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "assets/js/sinjira-assistant.js"
CSS = ROOT / "assets/css/sinjira-assistant.css"
SITE = ROOT / "assets/js/site.js"
NOVA_RUNTIME = ROOT / "projets/projet-nova/script.js"

errors = []


def require(condition, message):
    if not condition:
        errors.append(message)


require(JS.exists(), "assets/js/sinjira-assistant.js est absent")
require(CSS.exists(), "assets/css/sinjira-assistant.css est absent")
require(SITE.exists(), "assets/js/site.js est absent")
require(NOVA_RUNTIME.exists(), "projets/projet-nova/script.js est absent")

js = JS.read_text(encoding="utf-8") if JS.exists() else ""
css = CSS.read_text(encoding="utf-8") if CSS.exists() else ""
site = SITE.read_text(encoding="utf-8") if SITE.exists() else ""
nova_runtime = NOVA_RUNTIME.read_text(encoding="utf-8") if NOVA_RUNTIME.exists() else ""

# Contrat de version et fournisseur: V24.4.40 fonctionne intégralement côté navigateur.
require("ASSISTANT_VERSION = '24.4.40'" in js, "version assistant attendue 24.4.40 absente")
require("PROVIDER_MODE = 'local'" in js, "l’assistant doit rester en fournisseur local")
require("EXTERNAL_PROVIDER_ENABLED = false" in js, "un fournisseur externe ne doit pas être activé")
require("privacy: 'ephemeral-memory-only'" in js, "le contrat de mémoire éphémère est absent")

# Aucun message de visiteur ne doit quitter le navigateur ni être persisté par l’assistant.
for forbidden in (
    "fetch(", "XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon",
    "localStorage", "sessionStorage", "indexedDB", "document.cookie",
):
    require(forbidden not in js, f"API interdite dans l’assistant local: {forbidden}")
require("eval(" not in js and "new Function(" not in js, "exécution dynamique interdite dans l’assistant")
require("innerHTML" not in js and "insertAdjacentHTML" not in js, "les réponses doivent être construites avec textContent/DOM sûr")

# Accessibilité et garde-fous de saisie.
for marker in (
    "role', 'dialog'", "aria-labelledby", "aria-describedby", "role', 'log'",
    "aria-live", "aria-expanded", "aria-controls", "Votre question",
    "MAX_MESSAGE_LENGTH = 500", "event.key === 'Escape'",
):
    require(marker in js, f"marqueur accessibilité/sécurité manquant: {marker}")
require("prefers-reduced-motion" in css, "le style doit respecter prefers-reduced-motion")
require(":focus-visible" in css, "les contrôles de l’assistant doivent avoir un focus visible")
require("forced-colors" in css, "le style doit prévoir le mode forced-colors")

# L’assistant ne doit jamais recommander de routes d’administration ou de secrets.
require("'/admin/" not in js and '"/admin/' not in js, "l’assistant public ne doit pas proposer de route d’administration")
require("SUPABASE_SERVICE_ROLE" not in js and "OPENAI_API_KEY" not in js, "aucun secret/API key ne doit être présent")

# Séparation jeunesse: tous les sujets actuellement exposés sont explicitement sûrs.
require("function isYouthContext()" in js, "la détection du contexte jeunesse est absente")
require("if (youth && intent.youthSafe !== true) continue;" in js, "le filtre jeunesse est absent")
intent_blocks = re.findall(r"\{\s*id:\s*'[^']+'.*?youthSafe:\s*(true|false)\s*\}", js, flags=re.S)
require(intent_blocks and all(value == "true" for value in intent_blocks), "un sujet exposé n’est pas marqué youthSafe=true")

# V24.4.40: contexte déterminé uniquement par la route, sans lecture des champs privés.
require("var PAGE_CONTEXTS = [" in js, "base de contexte par page absente")
require("function currentPageContext()" in js, "résolution du contexte de page absente")
require("function isPageHelpQuery(query)" in js, "intention d’aide sur la page absente")
require("contextLabel: pageContext.label" in js, "diagnostic du contexte public absent")
require("input.value" in js and "querySelector('input')" not in js, "l’assistant ne doit pas parcourir les champs de la page")
for expected_context in (
    "Registre des Consciences", "Romans SINJIRA™", "Jeux SINJIRA™",
    "Fracture du Réseau-Mère", "Projet Nova", "Compte SINJIRA™",
):
    require(expected_context in js, f"contexte critique absent: {expected_context}")

# Chargement global via les runtimes communs. Site.js doit utiliser le cache-buster actuel;
# Projet Nova conserve son chargeur dédié et peut être mis à jour indépendamment.
require("/assets/css/sinjira-assistant.css?v=24.4.40" in site, "site.js ne charge pas le CSS assistant V24.4.40")
require("/assets/js/sinjira-assistant.js?v=24.4.40" in site, "site.js ne charge pas le JS assistant V24.4.40")
for runtime_name, runtime in (("site.js", site), ("Projet Nova/script.js", nova_runtime)):
    require("/assets/css/sinjira-assistant.css?v=" in runtime, f"{runtime_name} ne charge pas le CSS de l’assistant")
    require("/assets/js/sinjira-assistant.js?v=" in runtime, f"{runtime_name} ne charge pas le JS de l’assistant")
    require("data-disable-sinjira-assistant" in runtime, f"{runtime_name}: opt-out technique explicite absent")

site_runtime_pages = [
    ROOT / "index.html",
    ROOT / "a-propos.html",
    ROOT / "contact.html",
    ROOT / "projets/sinjira/index.html",
    ROOT / "projets/sinjira/registre/index.html",
    ROOT / "compte/index.html",
    ROOT / "compte/connexion.html",
    ROOT / "compte/mon-personnage.html",
]
for page in site_runtime_pages:
    require(page.exists(), f"page critique absente: {page.relative_to(ROOT)}")
    if page.exists():
        html = page.read_text(encoding="utf-8")
        require("assets/js/site.js" in html, f"assistant non chargé via site.js sur {page.relative_to(ROOT)}")

nova_page = ROOT / "projets/projet-nova/index.html"
require(nova_page.exists(), "page critique absente: projets/projet-nova/index.html")
if nova_page.exists():
    nova_html = nova_page.read_text(encoding="utf-8")
    require("script.js" in nova_html, "Projet Nova ne charge pas son runtime commun et donc pas l’assistant")

if errors:
    print("ERREUR — contrat Assistant SINJIRA V24.4.40")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print("OK — Assistant SINJIRA V24.4.40: local, éphémère, contextuel, accessible, jeunesse-safe et chargé sur les parcours critiques, incluant Projet Nova.")