#!/usr/bin/env python3
"""Pré-bascule : observer les statuts HEAD, jamais le corps des sources techniques.

Preuve de risque, PAS attestation de publication : un HEAD 404 ne prouve
pas qu'un GET est refusé, qu'un secret a été effacé, ni que le bon SHA est
déployé. Exécution read-only sur un domaine/26 chemins fixés dans le code.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import os
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from validate_publication_live_boundary import BASE_URL, TECHNICAL_ROUTES

TIMEOUT_SECONDS = 8
DENIED = {404, 410}
EXPOSURE = {200, 206}
UNCERTAIN = {405, 501}


class RefuseRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def observe_status(route: str) -> int | None:
    if route not in TECHNICAL_ROUTES or not route.startswith("/"):
        raise ValueError("Seuls les chemins techniques prédéfinis sont interrogés")
    request = Request(
        BASE_URL + route,
        method="HEAD",
        headers={
            "User-Agent": "SINJIRA-Pages-PreCutover-HEAD/1.0",
            "Cache-Control": "no-cache, no-store",
            "Pragma": "no-cache",
            "Accept-Encoding": "identity",
        },
    )
    try:
        with build_opener(RefuseRedirect()).open(
            request, timeout=TIMEOUT_SECONDS
        ) as response:
            if response.geturl() != BASE_URL + route:
                return 302  # Redirection interdite, y compris sur le même host.
            return int(response.status)
    except HTTPError as error:
        try:
            return int(error.code)
        finally:
            error.close()
    except (URLError, OSError, TimeoutError):
        return None


def classify(statuses: Mapping[str, int | None]) -> tuple[str, tuple[str, ...]]:
    if set(statuses) != set(TECHNICAL_ROUTES):
        return "INCONNU", ("Inventaire des routes techniques incomplet",)
    exposed = sorted(route for route, code in statuses.items() if code in EXPOSURE)
    if exposed:
        return "EXPOSÉ", tuple(
            f"{route}: HTTP {statuses[route]} (HEAD public)" for route in exposed
        )
    other = sorted(
        route for route, code in statuses.items()
        if code is not None and code not in DENIED | UNCERTAIN
    )
    if other:
        return "NON_CONFORME", tuple(
            f"{route}: HTTP {statuses[route]} (404/410 strict attendu)" for route in other
        )
    unknown = sorted(
        route for route, code in statuses.items() if code in UNCERTAIN or code is None
    )
    if unknown:
        return "INCONNU", tuple(
            f"{route}: "
            + ("réponse réseau indisponible" if statuses[route] is None
               else f"HEAD non conclusif HTTP {statuses[route]}")
            for route in unknown
        )
    return "REFUS_HEAD_OBSERVÉ", (
        f"{len(TECHNICAL_ROUTES)} réponses HEAD 404/410 observées; contrôle GET et reçu SHA/run encore requis",
    )


def run_checks(probe: Callable[[str], int | None]) -> dict[str, int | None]:
    return {route: probe(route) for route in TECHNICAL_ROUTES}


def report(statuses: Mapping[str, int | None]) -> str:
    outcome, issues = classify(statuses)
    lines = [
        "## GitHub Pages — état HTTP des chemins techniques avant bascule",
        "",
        f"**Verdict HEAD : {outcome}**",
        "",
        f"Domaine fixé : {BASE_URL} ({len(TECHNICAL_ROUTES)} chemins, requêtes HEAD uniquement)",
        "",
        "| Chemin technique | Code HEAD |",
        "| --- | --- |",
    ]
    for route in TECHNICAL_ROUTES:
        code = statuses.get(route)
        lines.append(f"| `{route}` | {code if code is not None else 'Inconnu'} |")
    lines.extend(["", "### Écarts observés"])
    lines.extend(f"- {issue}" for issue in issues)
    lines.extend([
        "",
        "**Limite :** aucune réponse, donnée privée ni contenu de fichier technique",
        "n'est téléchargé. HEAD peut différer de GET; cette preuve ne",
        "certifie ni la confidentialité passée, ni le SHA du site publié.",
        "Après une bascule autorisée, le validateur HTTPS GET, le reçu SHA/run,",
        "les refus 404/410 et l'intégrité CDN restent obligatoires.",
        "",
    ])
    return "\n".join(lines)


def self_test() -> None:
    healthy = {route: 404 for route in TECHNICAL_ROUTES}
    assert len(healthy) == 26
    assert classify(healthy)[0] == "REFUS_HEAD_OBSERVÉ"
    for route in TECHNICAL_ROUTES:
        allowed = dict(healthy)
        allowed[route] = 410
        assert classify(allowed)[0] == "REFUS_HEAD_OBSERVÉ"
        for code, expected in (
            (200, "EXPOSÉ"), (206, "EXPOSÉ"),
            (301, "NON_CONFORME"), (302, "NON_CONFORME"),
            (403, "NON_CONFORME"), (500, "NON_CONFORME"),
            (405, "INCONNU"), (501, "INCONNU"), (None, "INCONNU")
        ):
            changed = dict(healthy)
            changed[route] = code
            assert classify(changed)[0] == expected, (route, code)
    assert classify({})[0] == "INCONNU"
    assert classify({**healthy, TECHNICAL_ROUTES[0]: 200,
                     TECHNICAL_ROUTES[1]: None})[0] == "EXPOSÉ"
    assert run_checks(lambda _: 410) == dict.fromkeys(TECHNICAL_ROUTES, 410)
    assert "HEAD peut différer de GET" in report(healthy)
    assert "contenu de fichier technique" in report(healthy)
    print(f"OK: {len(TECHNICAL_ROUTES)} HEAD techniques, exposition, redirections, erreurs et refus exacts")


def main() -> int:
    parser = argparse.ArgumentParser()
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument("--self-test", action="store_true")
    command.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    observed = run_checks(observe_status)
    text = report(observed)
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as writer:
            writer.write(text)
    state, differences = classify(observed)
    if state != "REFUS_HEAD_OBSERVÉ":
        print("::warning title=Confinement HTTP non prouvé::"
              + (f"{state}: " + "; ".join(differences))[:420])
    # Le succès du JOB signifie "observation terminée", pas "prêt à publier".
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
