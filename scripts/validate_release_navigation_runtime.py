#!/usr/bin/env python3
"""Garde de continuité JS pour la publication candidate isolée.

Conserve les corrections de navigation de main et le cloisonnement assistant/IA.
Ne remplace pas les tests navigateur ou une vérification HTTP de production.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SITE_MARKERS = (
    "function setNavOpen(open)",
    "toggle.setAttribute('aria-expanded', open ? 'true' : 'false')",
    "toggle.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu')",
    "setNavOpen(false);",
    "event.key !== 'Escape'",
    "toggle.focus();",
    "nav.contains(event.target)",
    "window.matchMedia('(min-width: 821px)')",
    "toggle.setAttribute('aria-controls', nav.id)",
    "function appendAiTransparencyAssets()",
    "function normalizePortalNavigation()",
    "if (isOfficialHost && !isPrivateSurface && !isNoindexSurface) return;",
    "path.indexOf('/compte/') === 0",
    "path.indexOf('/admin/') === 0",
    "path.indexOf('/app/') === 0",
    "path.indexOf('/histoire-de-vie/') === 0",
    "ai-transparency.js?v=1.5.0",
)

NOVA_MARKERS = (
    "boussole-electorale.html",
    "if(isOfficialHost&&!isNoindexSurface)return;",
    "data-sinjira-assistant-script",
)

SW_MARKERS = (
    "const releaseMarker=u.pathname==='/.well-known/release.json';",
    "if(releaseMarker){e.respondWith(fetch(new Request(r,{cache:'no-store'})));return}",
    "if(privatePath){e.respondWith(fetch(new Request(r,{cache:'no-store'}))",
    "function cacheableResponse(resp)",
    "/projets/projet-nova/boussole-electorale.html",
)

PRIVATE_PATHS = (
    "'/compte/'", "'/admin/'", "'/Admin/'", "'/app/'",
    "'/histoire-de-vie/'",
)


def check_markers(source: str, required: tuple[str, ...], surface: str) -> list[str]:
    return [f"{surface}: marqueur de continuité absent: {marker}" for marker in required if marker not in source]


def validate() -> list[str]:
    paths = {
        "navigation": ROOT / "assets/js/site.js",
        "nova": ROOT / "projets/projet-nova/script.js",
        "worker": ROOT / "sw.js",
    }
    contents: dict[str, str] = {}
    failures: list[str] = []
    for kind, path in paths.items():
        if not path.is_file():
            failures.append(f"{kind}: source absente: {path}")
            continue
        contents[kind] = path.read_text(encoding="utf-8")

    if "navigation" in contents:
        failures.extend(check_markers(contents["navigation"], SITE_MARKERS, "navigation"))
        navigation = contents["navigation"]
        if "setNavOpen(toggle.getAttribute('aria-expanded') !== 'true')" not in navigation:
            failures.append("Le bouton mobile n'emploie plus la synchronisation accessible.")
        if "if (isOfficialHost && !isPrivateSurface && !isNoindexSurface) return;" not in navigation:
            failures.append("Limite de chargement automatique de l'assistant officiel désactivée.")

    if "nova" in contents:
        failures.extend(check_markers(contents["nova"], NOVA_MARKERS, "Projet Nova"))
    if "worker" in contents:
        worker = contents["worker"]
        failures.extend(check_markers(worker, SW_MARKERS, "Service worker"))
        for route in PRIVATE_PATHS:
            if route not in worker:
                failures.append(f"Service worker: détection de l'espace privé manquante: {route}")

    # Le même garde doit être exécuté sur la branche de release APRÈS squash.
    workflow = ROOT / ".github/workflows/release-security-allowlist.yml"
    if not workflow.is_file():
        failures.append("Workflow de contrôle de release absent.")
    else:
        source = workflow.read_text(encoding="utf-8")
        if "  push:\n    branches:\n      - a1/web-release-transparency" not in source:
            failures.append("Les contrôles complets ne sont pas obligatoires sur chaque push candidat.")
        for command in (
            "node --check assets/js/site.js",
            "node --check projets/projet-nova/script.js",
            "node --check sw.js",
        ):
            if command not in source:
                failures.append(f"Syntaxe JavaScript non vérifiée: {command}")
    return failures


def self_test() -> list[str]:
    issues: list[str] = []
    example = "\n".join(SITE_MARKERS)
    if check_markers(example, SITE_MARKERS, "auto-test"):
        issues.append("Auto-test positif du contrat JS invalide.")
    invalid = example.replace("event.key !== 'Escape'", "", 1)
    if not check_markers(invalid, SITE_MARKERS, "auto-test"):
        issues.append("Le test négatif ne détecte pas la perte de gestion Échap.")
    if not check_markers("", NOVA_MARKERS, "auto-test"):
        issues.append("Le test négatif ne détecte pas la disparition de la Boussole.")
    if not check_markers("", SW_MARKERS, "auto-test"):
        issues.append("Le test négatif ne détecte pas la fuite du précache.")
    return issues


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    errors = self_test() if args.self_test else validate()
    for issue in errors:
        print("ECHEC:", issue)
    if errors:
        raise SystemExit(1)
    print("OK : menu accessible, JS syntactique (CI), protection assistant et précache public.")
