#!/usr/bin/env python3
"""Pré-bascule Pages: observer uniquement les STATUTS GET des sources techniques.

Aucun corps de fichier n'est lu, enregistré ou imprimé. Ce diagnostic
complète HEAD; il ne prouve ni l'absence passée de fuite ni le bon SHA.
Le site visé et les 18 chemins sont des constantes, sans entrée libre.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from report_pages_live_exposure import (
    BASE_URL, TECHNICAL_ROUTES, RefuseRedirect, TIMEOUT_SECONDS,
)

REFUSALS = {404, 410}
EXPOSED = {200, 206}
UNDECIDED = {405, 501}


def observe_get_status(route: str, opener=None) -> int | None:
    if route not in TECHNICAL_ROUTES or not route.startswith("/"):
        raise ValueError("Route GET extérieure à l'inventaire technique fixe")
    url = BASE_URL + route
    request = Request(
        url, method="GET",
        headers={
            "User-Agent": "SINJIRA-Pages-PreCutover-GET-StatusOnly/1.0",
            "Cache-Control": "no-cache, no-store",
            "Pragma": "no-cache",
            "Accept-Encoding": "identity",
        },
    )
    try:
        with (opener or build_opener(RefuseRedirect())).open(
            request, timeout=TIMEOUT_SECONDS
        ) as response:
            # NE PAS appeler .read(), .json(), .text(), ou accéder au corps.
            if response.geturl() != url:
                return 302
            return int(response.status)
    except HTTPError as error:
        try:
            # HTTPError contient aussi des réponses 3xx (redirections refusées).
            return int(error.code)
        finally:
            error.close()
    except (URLError, OSError, TimeoutError):
        return None


def classify(statuses: Mapping[str, int | None]) -> tuple[str, tuple[str, ...]]:
    if set(statuses) != set(TECHNICAL_ROUTES):
        return "INCONNU", ("Inventaire GET des 18 routes incomplet",)
    exposed = sorted(route for route, code in statuses.items() if code in EXPOSED)
    if exposed:
        return "EXPOSÉ_GET", tuple(
            f"{route}: GET HTTP {statuses[route]} (route technique publiquement accessible)"
            for route in exposed
        )
    other = sorted(
        route for route, code in statuses.items()
        if code is not None and code not in REFUSALS | UNDECIDED
    )
    if other:
        return "NON_CONFORME_GET", tuple(
            f"{route}: GET HTTP {statuses[route]} (404/410 requis)"
            for route in other
        )
    unknown = sorted(
        route for route, code in statuses.items()
        if code in UNDECIDED or code is None
    )
    if unknown:
        return "INCONNU", tuple(
            f"{route}: "
            + ("erreur réseau" if statuses[route] is None
               else f"GET HTTP {statuses[route]} inconclusif")
            for route in unknown
        )
    return "REFUS_GET_OBSERVÉ", (
        "18 statuts GET 404/410; vérifier aussi Source GitHub Actions, reçu SHA/run et CDN",
    )


def run_checks(probe: Callable[[str], int | None]) -> dict[str, int | None]:
    return {route: probe(route) for route in TECHNICAL_ROUTES}


def markdown(statuses: Mapping[str, int | None]) -> str:
    status, observations = classify(statuses)
    text = [
        "## GitHub Pages — codes GET des fichiers techniques avant bascule",
        "",
        f"**Verdict GET (codes uniquement) : {status}**",
        "",
        f"Domaine fixe : {BASE_URL}; 18 chemins techniques; pas de lecture du corps.",
        "",
        "| Route technique | Statut GET |",
        "| --- | --- |",
    ]
    for route in TECHNICAL_ROUTES:
        code = statuses.get(route)
        text.append(f"| `{route}` | {code if code is not None else 'Inconnu'} |")
    text.extend(["", "### Anomalies / preuve partielle"])
    text.extend(f"- {line}" for line in observations)
    text.extend([
        "",
        "**Limite :** le script ferme la réponse sans lire le corps et ne",
        "révèle aucun contenu technique, jeton ou donnée privée.",
        "Un GET 200/206 confirme l'accessibilité HTTP du chemin,",
        "mais ne démontre pas la présence de secrets ni la nature du corps.",
        "Même 18 GET 404/410 ne prouvent pas la source de publication",
        "ou le SHA : seul un PUBLISH approuvé, reçu SHA/run et contrôle CDN",
        "avec tests complets peut permettre de conclure au confinement.",
        "",
    ])
    return "\n".join(text)


def self_test() -> None:
    good = dict.fromkeys(TECHNICAL_ROUTES, 404)
    assert len(good) == 18
    assert classify(good)[0] == "REFUS_GET_OBSERVÉ"
    for route in TECHNICAL_ROUTES:
        for code, expected in (
            (410, "REFUS_GET_OBSERVÉ"), (200, "EXPOSÉ_GET"),
            (206, "EXPOSÉ_GET"), (301, "NON_CONFORME_GET"),
            (302, "NON_CONFORME_GET"), (403, "NON_CONFORME_GET"),
            (500, "NON_CONFORME_GET"), (405, "INCONNU"),
            (501, "INCONNU"), (None, "INCONNU"),
        ):
            changed = {**good, route: code}
            assert classify(changed)[0] == expected, (route, code)
    assert classify({})[0] == "INCONNU"
    assert classify({**good, TECHNICAL_ROUTES[0]: 200,
                     TECHNICAL_ROUTES[1]: None})[0] == "EXPOSÉ_GET"
    assert run_checks(lambda _: 410) == dict.fromkeys(TECHNICAL_ROUTES, 410)
    assert "sans lire le corps" in markdown(good)
    assert "ne démontre pas la présence de secrets" in markdown(
        {**good, TECHNICAL_ROUTES[0]: 200}
    )
    # La fausse réponse contient un .read() qui DOIT rester inutilisé.
    class FakeResponse:
        status = 200
        def __init__(self, url: str): self.url = url
        def __enter__(self): return self
        def __exit__(self, *_args): return None
        def geturl(self): return self.url
        def read(self, *_args): raise AssertionError("Corps technique lu!")
    class FakeOpener:
        def __init__(self): self.requests = []
        def open(self, request, timeout):
            self.requests.append((request, timeout))
            return FakeResponse(request.full_url)
    opener = FakeOpener()
    assert observe_get_status(TECHNICAL_ROUTES[0], opener) == 200
    request, timeout = opener.requests[0]
    assert request.get_method() == "GET"
    assert request.full_url == BASE_URL + TECHNICAL_ROUTES[0]
    assert timeout == TIMEOUT_SECONDS
    for forbidden in ("/", "/public/index.html", "//evil.example/secret"):
        try:
            observe_get_status(forbidden, opener)
        except ValueError:
            pass
        else:
            raise AssertionError("GET de route hors inventaire autorisé")
    assert len(opener.requests) == 1
    print("OK : 18 statuts GET, aucun corps lu, erreurs, redirections et refus")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    statuses = run_checks(observe_get_status)
    text = markdown(statuses)
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as file:
            file.write(text)
    verdict, details = classify(statuses)
    if verdict != "REFUS_GET_OBSERVÉ":
        print("::warning title=Confinement GET non prouvé::"
              + (f"{verdict}: " + "; ".join(details))[:440])
    # Succès = rapport exécuté, jamais autorisation de PUBLISH.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
