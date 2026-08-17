from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "assets/js/sinjira-assistant.js"
CSS = ROOT / "assets/css/sinjira-assistant.css"
SITE = ROOT / "assets/js/site.js"

errors = []

def require(condition, message):
    if not condition:
        errors.append(message)

require(JS.exists(), "assets/js/sinjira-assistant.js est absent")
require(CSS.exists(), "assets/css/sinjira-assistant.css est absent")
require(SITE.exists(), "assets/js/site.js est absent")

js = JS.read_text(encoding="utf-8") if JS.exists() else ""
css = CSS.read_text(encoding="utf-8") if CSS.exists() else ""
site = SITE.read_text(encoding="utf-8") if SITE.exists() else ""

# Contrat de version et fournisseur: V24.4.39 fonctionne intégralement côté navigateur.
require("ASSISTANT_VERSION = '24.4.39'" in js, "version assistant attendue 24.4.39 absente")
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

# Chargement global via le runtime commun, sans devoir dupliquer le widget dans chaque page.
require("/assets/css/sinjira-assistant.css?v=24.4.39" in site, "site.js ne charge pas le CSS de l’assistant V24.4.39")
require("/assets/js/sinjira-assistant.js?v=24.4.39" in site, "site.js ne charge pas le JS de l’assistant V24.4.39")
require("data-disable-sinjira-assistant" in site, "l’opt-out technique explicite est absent")

critical_pages = [
    ROOT / "index.html",
    ROOT / "a-propos.html",
    ROOT / "contact.html",
    ROOT / "projets/sinjira/index.html",
    ROOT / "projets/sinjira/registre/index.html",
    ROOT / "projets/projet-nova/index.html",
    ROOT / "compte/index.html",
    ROOT / "compte/connexion.html",
    ROOT / "compte/mon-personnage.html",
]
for page in critical_pages:
    require(page.exists(), f"page critique absente: {page.relative_to(ROOT)}")
    if page.exists():
        html = page.read_text(encoding="utf-8")
        require("assets/js/site.js" in html, f"assistant non chargé via site.js sur {page.relative_to(ROOT)}")

if errors:
    print("ERREUR — contrat Assistant SINJIRA V24.4.39")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print("OK — Assistant SINJIRA V24.4.39: local, éphémère, accessible, jeunesse-safe et chargé sur les parcours critiques.")