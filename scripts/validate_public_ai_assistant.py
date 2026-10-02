#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WIDGET = ROOT / "assets/js/ai-transparency.js"
SITE = ROOT / "assets/js/site.js"
INDEX = ROOT / "index.html"
ASSISTANT = ROOT / "assistant.html"
TRANSPARENCY = ROOT / "transparence-ia.html"

BUBBLAV_WIDGET_URL = "https://www.bubblav.com/widget.js"
BUBBLAV_SITE_ID = "ca77cd98-bd32-459c-ad55-fdad4fb85316"
FORMS_READY_MARKER = "var publicAssistantFormsMinimized = true;"
DOMAINS_READY_MARKER = "var publicAssistantDomainsRestricted = false;"
VENDOR_BLOCK_MARKER = "if (!publicAssistantFormsMinimized || !publicAssistantDomainsRestricted) return;"
LOADER_URL = "/assets/js/ai-transparency.js?v=1.4.0"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_widget(text: str) -> list[str]:
    errors: list[str] = []
    required = (
        "host === 'www.benoitcantin.com' || host === 'benoitcantin.com'",
        "path === '/compte'",
        "path.indexOf('/compte/') === 0",
        "path === '/admin'",
        "path.indexOf('/admin/') === 0",
        "path === '/app'",
        "path.indexOf('/app/') === 0",
        "meta[name=\"robots\"]",
        "noindex",
        "if (!isOfficialHost || isPrivateSurface || isNoindexSurface) return;",
        FORMS_READY_MARKER,
        DOMAINS_READY_MARKER,
        VENDOR_BLOCK_MARKER,
        "data-public-assistant-launcher",
        "launcher.addEventListener('click'",
        BUBBLAV_WIDGET_URL,
        f"data-site-id', '{BUBBLAV_SITE_ID}'",
        "data-bubblav-widget",
        "Chargé seulement après votre clic",
        "Le service n’a pas pu être chargé",
    )
    for marker in required:
        require(errors, marker in text, f"widget: marqueur obligatoire absent: {marker}")

    require(errors, text.count(BUBBLAV_WIDGET_URL) == 1, "widget: URL BubblaV doit apparaître exactement une fois")
    require(errors, text.count(BUBBLAV_SITE_ID) == 1, "widget: site-id BubblaV doit apparaître exactement une fois")

    vendor_block = text.find(VENDOR_BLOCK_MARKER)
    launcher_create = text.find("var launcher = document.createElement('button')")
    require(
        errors,
        vendor_block >= 0 and launcher_create > vendor_block,
        "widget: le verrou fournisseur doit précéder toute création du lanceur",
    )
    require(errors, "publicAssistantFormsMinimized = false" not in text, "widget: minimisation formulaires #443 doit rester confirmée")
    require(errors, "publicAssistantDomainsRestricted = true" not in text, "widget: réactivation domaines interdite tant que #444 reste ouvert")
    require(errors, "publicAssistantVendorReady" not in text, "widget: ancien verrou fournisseur unique interdit")

    click = text.find("launcher.addEventListener('click'")
    remote = text.find(BUBBLAV_WIDGET_URL)
    require(errors, click >= 0 and remote > click, "widget: le script BubblaV doit être créé uniquement après le gestionnaire de clic")

    forbidden = (
        "localStorage",
        "sessionStorage",
        "document.cookie",
        "navigator.geolocation",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "EventSource",
        "sendBeacon",
        "Authorization",
        "access_token",
        "refresh_token",
        "innerHTML = '<script",
    )
    for marker in forbidden:
        require(errors, marker not in text, f"widget: capacité interdite détectée: {marker}")

    return errors


def validate_site_loader(text: str) -> list[str]:
    errors: list[str] = []
    require(errors, LOADER_URL in text, "site.js: loader ai-transparency absent ou version obsolète")
    require(errors, "data-ai-transparency-script" in text, "site.js: marqueur de déduplication absent")
    require(errors, text.count("appendAiTransparencyAssets();") == 1, "site.js: appel du loader transparence doit rester unique")
    return errors


def validate_pages(index: str, assistant: str, transparency: str) -> list[str]:
    errors: list[str] = []
    require(errors, '<aside class="ai-transparency-banner" data-ai-transparency' in index, "index: bandeau transparence IA absent")
    require(errors, '/transparence-ia.html' in index, "index: lien transparence IA absent")
    require(errors, 'Assistant Nova × SINJIRA' in assistant, "assistant: identité publique absente")
    require(errors, 'sans décider à votre place' in assistant, "assistant: frontière de décision humaine absente")
    require(errors, 'Il ne doit pas dire aux visiteurs comment voter' in assistant, "assistant: neutralité civique absente")
    require(errors, 'le widget conversationnel BubblaV est temporairement désactivé' in assistant, "assistant: statut fournisseur désactivé absent")
    require(errors, 'Aucun script BubblaV n’est chargé par le site pendant cette période.' in assistant, "assistant: garantie réseau BubblaV absente")
    require(errors, '<code>/compte</code>' in assistant and '<code>/admin</code>' in assistant and '<code>/app</code>' in assistant, "assistant: exclusions privées absentes")
    require(errors, 'Transparence · Honnêteté · Intégrité' in transparency, "transparence: valeurs publiques absentes")
    require(errors, 'L’humain avant tout.' in transparency, "transparence: principe humain absent")
    require(
        errors,
        transparency.count('Validation finale et responsabilité du contenu : Benoit Cantin.') >= 2,
        "transparence: responsabilité humaine absente ou incomplète",
    )
    return errors


def validate_all(widget: str, site: str, index: str, assistant: str, transparency: str) -> list[str]:
    return [
        *validate_widget(widget),
        *validate_site_loader(site),
        *validate_pages(index, assistant, transparency),
    ]


def load() -> tuple[str, str, str, str, str]:
    paths = (WIDGET, SITE, INDEX, ASSISTANT, TRANSPARENCY)
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
    if missing:
        raise ValueError("fichiers assistant IA absents: " + ", ".join(missing))
    return tuple(path.read_text(encoding="utf-8", errors="strict") for path in paths)  # type: ignore[return-value]


def self_test() -> None:
    widget, site, index, assistant, transparency = load()
    fixtures = [
        ("preuve formulaires régressée", widget.replace(FORMS_READY_MARKER, "var publicAssistantFormsMinimized = false;", 1), site, index, assistant, transparency),
        ("gate domaines réactivé", widget.replace(DOMAINS_READY_MARKER, "var publicAssistantDomainsRestricted = true;", 1), site, index, assistant, transparency),
        ("double garde remplacée", widget.replace(VENDOR_BLOCK_MARKER, "if (!publicAssistantFormsMinimized) return;", 1), site, index, assistant, transparency),
        ("hôte officiel retiré", widget.replace("host === 'www.benoitcantin.com' || host === 'benoitcantin.com'", "host === 'example.com'", 1), site, index, assistant, transparency),
        ("exclusion compte retirée", widget.replace("path === '/compte' ||", "false ||", 1), site, index, assistant, transparency),
        ("noindex retiré", widget.replace("if (!isOfficialHost || isPrivateSurface || isNoindexSurface) return;", "if (!isOfficialHost || isPrivateSurface) return;", 1), site, index, assistant, transparency),
        ("clic retiré", widget.replace("launcher.addEventListener('click'", "launcher.addEventListener('mouseover'", 1), site, index, assistant, transparency),
        ("URL BubblaV changée", widget.replace(BUBBLAV_WIDGET_URL, "https://example.com/widget.js", 1), site, index, assistant, transparency),
        ("site-id changé", widget.replace(BUBBLAV_SITE_ID, "00000000-0000-0000-0000-000000000000", 1), site, index, assistant, transparency),
        ("loader site retiré", widget, site.replace(LOADER_URL, "/assets/js/other.js", 1), index, assistant, transparency),
        (
            "bandeau accueil retiré",
            widget,
            site,
            index.replace(
                '<aside class="ai-transparency-banner" data-ai-transparency',
                '<aside class="ai-transparency-banner" data-ai-hidden',
                1,
            ),
            assistant,
            transparency,
        ),
        ("neutralité retirée", widget, site, index, assistant.replace("Il ne doit pas dire aux visiteurs comment voter", "Il peut recommander un vote", 1), transparency),
        (
            "responsabilité retirée",
            widget,
            site,
            index,
            assistant,
            transparency.replace(
                "Validation finale et responsabilité du contenu : Benoit Cantin.",
                "Validation automatisée.",
            ),
        ),
    ]
    missed: list[str] = []
    for label, ww, ss, ii, aa, tt in fixtures:
        if not validate_all(ww, ss, ii, aa, tt):
            missed.append(label)
    if missed:
        raise SystemExit("ERREUR auto-test assistant IA: mutations non détectées: " + ", ".join(missed))
    print(f"OK auto-tests assistant IA public: {len(fixtures)}/{len(fixtures)} affaiblissements détectés.")


def main() -> int:
    try:
        values = load()
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ECHEC assistant IA public: {exc}", file=sys.stderr)
        return 1

    if "--self-test" in sys.argv[1:]:
        self_test()
        return 0

    errors = validate_all(*values)
    if errors:
        print(f"ECHEC assistant IA public: {len(errors)} problème(s).", file=sys.stderr)
        for error in errors:
            print("- " + error, file=sys.stderr)
        return 1

    print(
        "OK assistant IA public: formulaires #443 minimisés, domaine fournisseur #444 encore fail-closed, chargement futur après clic, domaine officiel, exclusions privées/noindex, "
        "site-id unique, neutralité civique et responsabilité humaine verrouillés."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
