#!/usr/bin/env python3
"""Diagnostic Pages PR sans mutation, sans upload et sans validation fictive.

La réussite de ce workflow signifie seulement que le diagnostic a été exécuté.
Son verdict explicite PRÊT/BLOQUÉ/INCONNU n'autorise jamais PUBLISH.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Callable

from attest_pages_production import PAGES_URL, github_get_json

DOMAIN = "www.benoitcantin.com"
SETTINGS = "https://github.com/M0rdr3x/BenoitCantin/settings/pages"


def verdict(pages: object) -> tuple[str, tuple[str, ...]]:
    if not isinstance(pages, dict):
        return "INCONNU", ("Réponse GitHub Pages inexploitable",)
    source = pages.get("build_type")
    cname = pages.get("cname")
    https = pages.get("https_enforced")
    if source not in {"legacy", "workflow"}:
        return "INCONNU", ("Type de source Pages absent ou inconnu",)
    blockers: list[str] = []
    if source != "workflow":
        blockers.append("Source Pages = branche/legacy, pas GitHub Actions")
    if cname != DOMAIN:
        blockers.append("Domaine personnalisé différent de www.benoitcantin.com")
    if https is not True:
        blockers.append("HTTPS forcé non attesté")
    if blockers:
        return "BLOQUÉ", tuple(blockers)
    return "SOURCE_CONFORME", (
        "Source, CNAME et HTTPS conformes aux prérequis administratifs",
    )


def check(fetch: Callable[[], object]) -> tuple[str, tuple[str, ...]]:
    try:
        data = fetch()
    except Exception as exc:
        return "INCONNU", (
            f"Lecture API Pages impossible ({type(exc).__name__}); ne pas présumer de la source",
        )
    return verdict(data)


def markdown(status: str, details: tuple[str, ...]) -> str:
    text = [
        "## GitHub Pages — diagnostic administratif en lecture seule",
        "",
        f"**État du prérequis Source/CNAME/HTTPS : {status}**",
        "",
    ]
    text.extend(f"- {item}" for item in details)
    text.extend([
        "",
        f"**Vérification par le propriétaire :** {SETTINGS}",
        "",
        "Ce diagnostic n'émet aucune requête de modification, ne crée pas",
        "d'artefact Pages et ne déploie rien. Même SOURCE_CONFORME ne signifie",
        "ni absence de sources techniques en ligne, ni autorisation de",
        "fusion ou de PUBLISH. Les étapes DRY_RUN, approbation SHA,",
        "PUBLISH et preuves HTTP 404/410 + intégrité CDN restent obligatoires.",
        "",
    ])
    return "\n".join(text)


def self_test() -> None:
    ready = {"build_type": "workflow", "cname": DOMAIN,
             "https_enforced": True}
    assert verdict(ready)[0] == "SOURCE_CONFORME"
    for changed, reason in (
        ({"build_type": "legacy"}, "Source Pages"),
        ({"cname": "evil.example"}, "Domaine"),
        ({"https_enforced": False}, "HTTPS"),
    ):
        payload = {**ready, **changed}
        state, issues = verdict(payload)
        assert state == "BLOQUÉ" and any(reason in m for m in issues)
    for malformed in (None, [], {}, {"build_type": "future"}):
        assert verdict(malformed)[0] == "INCONNU"
    def denied() -> object:
        raise PermissionError("simulated token not authorized")
    assert check(denied)[0] == "INCONNU"
    assert check(lambda: ready)[0] == "SOURCE_CONFORME"
    assert "ne déploie rien" in markdown("BLOQUÉ", ("Simulation",))
    # Une erreur de configuration/API interdit la promotion, même si
    # le diagnostic d'une PR brouillon reste informatif.
    def release_allowed(value: str) -> bool:
        return value == "SOURCE_CONFORME"
    assert release_allowed(verdict(ready)[0])
    for payload in ({"build_type": "legacy", "cname": DOMAIN,
                     "https_enforced": True}, {},
                    {"build_type": "workflow", "cname": DOMAIN,
                     "https_enforced": False}):
        assert not release_allowed(verdict(payload)[0])
    assert not release_allowed(check(denied)[0])
    assert "SOURCE_CONFORME ne signifie" in markdown(
        "SOURCE_CONFORME", ("Simulation",)
    )
    print("OK diagnostic read-only : legacy, CNAME, HTTPS, permissions et états inconnus")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--report", action="store_true")
    mode.add_argument("--require-source", action="store_true",
                      help="Bloquer la promotion d'une PR si Pages n'est pas sur GitHub Actions")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    token = os.environ.get("GH_PAGES_READ_TOKEN", "")
    if not token:
        status, details = "INCONNU", ("Jeton GitHub Pages non accessible",)
    else:
        status, details = check(lambda: github_get_json(PAGES_URL, token))
    report = markdown(status, details)
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write(report)
    if args.require_source:
        if status != "SOURCE_CONFORME":
            print("::error title=Promotion GitHub Pages interdite::"
                  + (status + ": " + "; ".join(details))[:340])
            return 2
        print("Garde de promotion : Source GitHub Actions, CNAME et HTTPS confirmés.")
        print("Ce PASS n'atteste pas le GET privé, le reçu SHA/run ni les octets du CDN.")
        return 0
    if status != "SOURCE_CONFORME":
        # Le rapport courant reste informatif; seule la promotion exige une conformité.
        print("::warning title=GitHub Pages non prêt::"
              + ("; ".join(details))[:300])
    # Exit 0 en mode rapport prouve seulement que la vérification est terminée.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
