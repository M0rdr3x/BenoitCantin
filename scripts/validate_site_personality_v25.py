#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "assets/js/site-personality-v25.js"
STYLE = ROOT / "assets/css/site-personality-v25.css"
DOC = ROOT / "docs/SITE_PERSONALITY_V25.md"
ARCH = ROOT / "ARCHITECTURE_DES_UNIVERS.md"
LOADER = '<script defer src="/assets/js/site-personality-v25.js?v=25.0.0"></script>'
PAGES = (
    ROOT / "index.html",
    ROOT / "projets/sinjira/index.html",
    ROOT / "projets/projet-nova/index.html",
    ROOT / "projets/futurax/index.html",
    ROOT / "projets/lumina/index.html",
    ROOT / "projets/chroniques-des-mondes-fractures/index.html",
)


def errors(module: str, style: str, doc: str, arch: str, pages: dict[Path, str]) -> list[str]:
    out: list[str] = []

    required_module = (
        "var VERSION = '25.0.0';",
        "portal: {",
        "sinjira: {",
        "nova: {",
        "futurax: {",
        "lumina: {",
        "chroniques: {",
        "L’humain avant tout. Protéger sans surveiller.",
        "Avoir la capacité d’agir, sans perdre l’humain.",
        "Construire une capacité durable, pas une dépendance de plus.",
        "La technologie reste au service de la personne.",
        "Un pouvoir utile doit rester compréhensible, traçable et corrigeable.",
        "Des choix qui comptent, sans fermer inutilement toutes les portes.",
        "window.location.pathname",
        "footer.parentNode.insertBefore(section, footer);",
        "section.setAttribute('aria-labelledby', headingId);",
        "node.textContent = text;",
        "doc.addEventListener('DOMContentLoaded', render, { once: true });",
        "data-disable-site-personality",
    )
    for marker in required_module:
        if marker not in module:
            out.append(f"module: marqueur obligatoire absent: {marker}")

    forbidden_module = (
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "EventSource",
        "sendBeacon",
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "document.cookie",
        "navigator.geolocation",
        "location.search",
        "location.hash",
        "/rest/v1/",
        "/functions/v1/",
        "supabase",
        "Authorization",
        "access_token",
        "refresh_token",
        ".innerHTML",
        "eval(",
        "new Function",
        "http://",
        "https://",
    )
    for marker in forbidden_module:
        if marker in module:
            out.append(f"module: capacité interdite détectée: {marker}")

    if module.count("window.location.pathname") != 1:
        out.append("module: pathname doit être l'unique source de contexte de navigation")
    if module.count("data-site-personality', environment") != 1:
        out.append("module: une seule déclaration d'environnement de personnalité est attendue")

    required_style = (
        ".bc-personality-signature",
        '[data-site-personality="sinjira"]',
        '[data-site-personality="nova"]',
        '[data-site-personality="futurax"]',
        '[data-site-personality="lumina"]',
        '[data-site-personality="chroniques"]',
        "@media (max-width: 900px)",
        "@media (max-width: 680px)",
        "@media (prefers-reduced-motion: reduce)",
    )
    for marker in required_style:
        if marker not in style:
            out.append(f"style: marqueur obligatoire absent: {marker}")
    for marker in ("position: fixed", "position: sticky", "animation: infinite", "z-index: 9999"):
        if marker in style:
            out.append(f"style: comportement intrusif interdit: {marker}")

    required_doc = (
        "L’humain avant tout",
        "Protéger sans surveiller",
        "Capacité d’agir",
        "Autonomie",
        "Long terme",
        "Réversibilité",
        "Liberté de choix",
        "Transparence et responsabilité",
        "sans lecture de compte, profil, identité, stockage local, géolocalisation, query-string ou fragment",
        "sans télémétrie, analytics, cookie, beacon ou appel d’API",
    )
    for marker in required_doc:
        if marker not in doc:
            out.append(f"documentation: principe ou frontière absent: {marker}")

    for name in ("SINJIRA™", "Projet Nova", "Futurax", "Lumina", "Chroniques des Mondes Fracturés"):
        if name not in arch:
            out.append(f"architecture: environnement principal absent: {name}")
    if "cinq espaces principaux" not in arch:
        out.append("architecture: le nombre canonique de cinq environnements doit rester explicite")

    if set(pages) != set(PAGES):
        out.append("pages: ensemble des six portes publiques inattendu")
    for path in PAGES:
        text = pages.get(path, "")
        if text.count(LOADER) != 1:
            out.append(f"page: chargeur personnalité attendu exactement une fois: {path.relative_to(ROOT)}")
        if "<main" not in text or "<footer" not in text:
            out.append(f"page: main/footer requis pour la signature: {path.relative_to(ROOT)}")

    return out


def load() -> tuple[str, str, str, str, dict[Path, str]]:
    required = (MODULE, STYLE, DOC, ARCH, *PAGES)
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise ValueError("fichiers manquants: " + ", ".join(missing))
    return (
        MODULE.read_text("utf-8"),
        STYLE.read_text("utf-8"),
        DOC.read_text("utf-8"),
        ARCH.read_text("utf-8"),
        {path: path.read_text("utf-8") for path in PAGES},
    )


def validate() -> None:
    found = errors(*load())
    if found:
        raise ValueError("\n - ".join(["contrat personnalité invalide", *found]))


def self_test() -> None:
    module, style, doc, arch, pages = load()
    cases: list[tuple[str, str, str, str, dict[Path, str]]] = []

    def m_module(label: str, old: str, new: str = "") -> None:
        mutated = module.replace(old, new, 1)
        if mutated == module:
            raise AssertionError(f"mutation inactive: {label}")
        cases.append((label, mutated, style, doc, arch, dict(pages)))

    def m_style(label: str, old: str, new: str = "") -> None:
        mutated = style.replace(old, new, 1)
        if mutated == style:
            raise AssertionError(f"mutation inactive: {label}")
        cases.append((label, module, mutated, doc, arch, dict(pages)))

    def m_doc(label: str, old: str, new: str = "") -> None:
        mutated = doc.replace(old, new, 1)
        if mutated == doc:
            raise AssertionError(f"mutation inactive: {label}")
        cases.append((label, module, style, mutated, arch, dict(pages)))

    m_module("retirer humain", "L’humain avant tout. Protéger sans surveiller.")
    m_module("retirer capacité", "Avoir la capacité d’agir, sans perdre l’humain.")
    m_module("retirer Nova", "Un pouvoir utile doit rester compréhensible, traçable et corrigeable.")
    m_module("retirer Futurax", "Construire une capacité durable, pas une dépendance de plus.")
    m_module("retirer Lumina", "La technologie reste au service de la personne.")
    m_module("retirer Chroniques", "Des choix qui comptent, sans fermer inutilement toutes les portes.")
    m_module("profilage API", "var VERSION = '25.0.0';", "var VERSION = '25.0.0';\n  fetch('/profile');")
    m_module("stockage local", "var VERSION = '25.0.0';", "var VERSION = '25.0.0';\n  localStorage.setItem('profile','1');")
    m_module("session", "var VERSION = '25.0.0';", "var VERSION = '25.0.0';\n  sessionStorage.getItem('profile');")
    m_module("cookie", "var VERSION = '25.0.0';", "var VERSION = '25.0.0';\n  document.cookie;")
    m_module("géolocalisation", "var VERSION = '25.0.0';", "var VERSION = '25.0.0';\n  navigator.geolocation;")
    m_module("query string", "window.location.pathname", "window.location.search")
    m_module("fragment", "window.location.pathname", "window.location.hash")
    m_module("HTML injecté", "node.textContent = text;", "node.innerHTML = text;")
    m_module("URL externe", "var VERSION = '25.0.0';", "var VERSION = '25.0.0';\n  var x='https://example.com';")
    m_module("retirer aria", "section.setAttribute('aria-labelledby', headingId);")
    m_module("retirer footer", "footer.parentNode.insertBefore(section, footer);")
    m_module("retirer opt-out", "data-disable-site-personality")
    m_style("retirer responsive", "@media (max-width: 680px)")
    m_style("retirer reduced motion", "@media (prefers-reduced-motion: reduce)")
    m_style("overlay fixe", "position: relative", "position: fixed")
    m_doc("retirer vie privée", "sans lecture de compte, profil, identité, stockage local, géolocalisation, query-string ou fragment")
    m_doc("retirer télémétrie", "sans télémétrie, analytics, cookie, beacon ou appel d’API")
    m_doc("retirer autonomie", "Autonomie")

    for path in PAGES:
        mutated_pages = dict(pages)
        mutated_pages[path] = mutated_pages[path].replace(LOADER, "", 1)
        if mutated_pages[path] == pages[path]:
            raise AssertionError(f"mutation inactive: chargeur {path.relative_to(ROOT)}")
        cases.append((f"retirer chargeur {path.relative_to(ROOT)}", module, style, doc, arch, mutated_pages))

    for label, mm, ss, dd, aa, pp in cases:
        if not errors(mm, ss, dd, aa, pp):
            raise AssertionError(f"mutation non détectée: {label}")

    print(f"OK {len(cases)}/{len(cases)} mutations personnalité V25 détectées.")


def main() -> int:
    try:
        if "--self-test" in sys.argv:
            self_test()
        validate()
    except (AssertionError, ValueError) as exc:
        print(f"ECHEC personnalité site V25: {exc}", file=sys.stderr)
        return 1
    print("OK personnalité site V25: six portes, personnalité publique bornée, aucune capacité de profilage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
