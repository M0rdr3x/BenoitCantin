#!/usr/bin/env python3
"""Surveillance publique de confinement HTTP, compatible Netlify et Pages Actions.

Ne jamais accepter un en-tête GitHub Pages comme preuve suffisante : ce
fournisseur exige AUSSI le reçu de publication au SHA exact de main.
Seule l'identité du reçu est lue (4 Kio max) ; aucun corps de route
technique, secret, réponse personnalisée ou jeton n'est téléchargé.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pages_release_proof import MARKER, SHA_PATTERN, render
from verify_pages_live import PRIVATE_ROUTES, PUBLIC_ROUTES, MIME_HINTS

BASE_URL = "https://www.benoitcantin.com"
# Source de vérité commune aux sondes pré/post-PUBLISH : tout chemin
# technique interdit est désormais contrôlé dans les deux modes.
TECHNICAL_ROUTES = PRIVATE_ROUTES
TIMEOUT_SECONDS = 12
MAX_RECEIPT_BYTES = 4096
PRIVATE_DENIAL = {404, 410}


@dataclass(frozen=True)
class StatusObservation:
    status: int
    content_type: str = ""
    location: str = ""
    netlify: bool = False
    github_pages: bool = False


def validate_public_routes(observed: Mapping[str, StatusObservation]) -> list[str]:
    """Même 21 routes et mêmes MIME que le post-PUBLISH, sans lire de corps."""
    errors: list[str] = []
    if set(observed) != set(PUBLIC_ROUTES):
        errors.append("Inventaire quotidien incomplet des 21 routes publiques.")
    for route in PUBLIC_ROUTES:
        result = observed.get(route)
        if result is None:
            errors.append(f"Route publique non contrôlée: {route}")
            continue
        if result.location or result.status in {301, 302, 303, 307, 308}:
            errors.append(f"Route publique redirigée: {route} (HTTP {result.status})")
            continue
        if result.status != 200:
            errors.append(f"Route publique indisponible: {route} (HTTP {result.status})")
            continue
        expected = ("text/html",) if route == "/" or route.endswith(("/", ".html")) else MIME_HINTS.get(route, ())
        mime = result.content_type.split(";", 1)[0].strip().lower()
        if not expected or mime not in expected:
            errors.append(f"Type MIME de la route publique non conforme: {route} ({mime or 'absent'})")
    return errors


class RefuseRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Un redirect vers / (ou une page HTML) n'est pas un refus technique.
        return None


def validate_observations(
    statuses: Mapping[str, int], *, netlify: bool,
    github_pages: bool = False, pages_receipt_valid: bool = False
) -> list[str]:
    errors: list[str] = []
    if statuses.get("/") != 200:
        errors.append("La page d'accueil officielle ne répond pas en HTTP 200.")
    if netlify == github_pages:
        errors.append("Origine de publication non qualifiée ou ambiguë.")
    elif github_pages and not pages_receipt_valid:
        errors.append("Reçu GitHub Pages absent, périmé ou différent du SHA de main.")
    for route in TECHNICAL_ROUTES:
        observed = statuses.get(route)
        if observed not in PRIVATE_DENIAL:
            actual = str(observed) if observed is not None else "indisponible"
            errors.append(
                f"Chemin technique non confiné: {route} -> HTTP {actual} "
                "(404/410 strict attendu)."
            )
    return errors


def validate_receipt_payload(
    body: bytes, content_type: str, expected_sha: str
) -> bool:
    if not SHA_PATTERN.fullmatch(expected_sha):
        return False
    if content_type.split(";", 1)[0].strip().lower() != "application/json":
        return False
    if len(body) > MAX_RECEIPT_BYTES:
        return False
    try:
        obj = json.loads(body)
        if not isinstance(obj, dict):
            return False
        run_id = obj.get("run_id")
        if not isinstance(run_id, str):
            return False
        return body == render(expected_sha, run_id)
    except (ValueError, UnicodeError, TypeError):
        return False


def self_test() -> None:
    assert len(TECHNICAL_ROUTES) == len(set(TECHNICAL_ROUTES)) == 14, (
        "Les diagnostics et la publication doivent tester exactement 14 routes"
    )
    assert TECHNICAL_ROUTES is PRIVATE_ROUTES, (
        "La liste des chemins ne doit plus diverger des tests post-PUBLISH"
    )
    good: dict[str, int] = {"/": 200}
    good.update({route: 404 for route in TECHNICAL_ROUTES})
    sha, run = "a" * 40, "38433761170"
    proof = render(sha, run)
    assert validate_receipt_payload(proof, "application/json; charset=utf-8", sha)
    for body, content_type, expected in (
        (proof, "text/html", sha),
        (proof, "application/json", "b" * 40),
        (b"{}", "application/json", sha),
        (proof[:-1], "application/json", sha),
        (b"x" * (MAX_RECEIPT_BYTES + 1), "application/json", sha),
        (proof, "application/json", "invalid"),
    ):
        assert not validate_receipt_payload(body, content_type, expected), (
            "Fausse identité Pages acceptée"
        )
    assert not validate_observations(good, netlify=True)
    assert not validate_observations(
        good, netlify=False, github_pages=True, pages_receipt_valid=True
    )
    for kw in (
        {"netlify": False, "github_pages": False},
        {"netlify": True, "github_pages": True, "pages_receipt_valid": True},
        {"netlify": False, "github_pages": True, "pages_receipt_valid": False},
    ):
        assert validate_observations(good, **kw), (
            "Origine non attestée ou ambiguë acceptée"
        )
    for route in TECHNICAL_ROUTES:
        permitted = dict(good)
        permitted[route] = 410
        assert not validate_observations(permitted, netlify=True)
        for status in (200, 301, 302, 403, 500):
            bad = dict(good)
            bad[route] = status
            assert any(route in error for error in validate_observations(
                bad, netlify=True
            )), f"Fuite ou redirection non détectée: {route}, HTTP {status}"
        bad = dict(good)
        del bad[route]
        assert any(route in error for error in validate_observations(
            bad, netlify=True
        )), f"Absence de preuve non détectée: {route}"
    assert validate_observations({**good, "/": 503}, netlify=True)
    print(
        f"OK: {len(TECHNICAL_ROUTES)} routes techniques, origine "
        "Netlify ou reçu Pages/main, tests négatifs sans trafic privé."
    )


def provider(headers) -> tuple[bool, bool]:
    server = headers.get("Server", "").lower()
    netlify = bool(headers.get("x-nf-request-id")) or "netlify" in server
    pages = "github.com" in server or "github pages" in server
    return netlify, pages


def read_status(opener, route: str) -> StatusObservation:
    if route not in PUBLIC_ROUTES and route not in TECHNICAL_ROUTES:
        raise ValueError("Route hors de l'inventaire de surveillance approuvé")
    url = BASE_URL + route
    request = Request(
        url,
        headers={
            "User-Agent": "SINJIRA-publication-boundary/2.1",
            "Cache-Control": "no-cache, no-store",
            "Pragma": "no-cache",
            "Accept-Encoding": "identity",
            "Accept": "*/*",
        },
        method="GET",
    )
    def observation(code: int, headers, actual_url: str) -> StatusObservation:
        netlify, pages = provider(headers)
        # Les en-têtes sont suffisants : ne jamais lire le corps technique.
        location = headers.get("Location", "") or (
            actual_url if actual_url != url else ""
        )
        return StatusObservation(
            int(code), headers.get("Content-Type", ""), location, netlify, pages
        )
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            return observation(response.status, response.headers, response.geturl())
    except HTTPError as error:
        try:
            return observation(error.code, error.headers, error.geturl())
        finally:
            error.close()


def read_pages_receipt(opener, expected_sha: str) -> bool:
    if not SHA_PATTERN.fullmatch(expected_sha):
        return False
    url = BASE_URL + "/" + MARKER
    request = Request(
        url,
        headers={
            "User-Agent": "SINJIRA-publication-boundary/2.0",
            "Cache-Control": "no-cache, no-store",
            "Pragma": "no-cache",
            "Accept-Encoding": "identity",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.geturl() != url:
                return False
            if response.headers.get("Content-Encoding", "").strip().lower() not in (
                "", "identity"
            ):
                return False
            payload = response.read(MAX_RECEIPT_BYTES + 1)
            return validate_receipt_payload(
                payload, response.headers.get("Content-Type", ""), expected_sha
            )
    except (HTTPError, URLError, OSError, TimeoutError, ValueError):
        return False


def live() -> int:
    opener = build_opener(RefuseRedirect())
    observations: dict[str, int] = {}
    public: dict[str, StatusObservation] = {}
    is_netlify = is_pages = False
    # 21 routes publiques + 14 chemins interdits : une seule visite par URL.
    # Les corps publics/techniques restent tous fermés sans lecture.
    for route in (*PUBLIC_ROUTES, *TECHNICAL_ROUTES):
        try:
            result = read_status(opener, route)
        except (URLError, OSError, TimeoutError, ValueError) as error:
            print(f"ECHEC réseau sur {route}: {type(error).__name__}")
            return 1
        if route in PUBLIC_ROUTES:
            public[route] = result
        if route in TECHNICAL_ROUTES or route == "/":
            observations[route] = result.status
        if route == "/":
            is_netlify, is_pages = result.netlify, result.github_pages
        print(f"{route}: HTTP {result.status}")
    receipt_valid = (
        is_pages and not is_netlify and
        os.environ.get("GITHUB_REF") == "refs/heads/main" and
        read_pages_receipt(opener, os.environ.get("GITHUB_SHA", ""))
    )
    errors = validate_observations(
        observations, netlify=is_netlify, github_pages=is_pages,
        pages_receipt_valid=receipt_valid
    )
    errors.extend(validate_public_routes(public))
    if errors:
        print(
            f"ECHEC: {len(errors)} écart(s) de publication; "
            "aucun contenu de réponse affiché."
        )
        for error in errors:
            print("- " + error)
        return 1
    origin = "Netlify" if is_netlify else "Pages Actions (reçu/main prouvé)"
    print(
        f"PASS: {len(PUBLIC_ROUTES)} routes publiques en HTTP 200 / MIME conforme; "
        f"{len(TECHNICAL_ROUTES)} routes techniques en HTTP 404/410 et origine {origin}."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Contrôler le confinement HTTP du site public."
    )
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    return live()


if __name__ == "__main__":
    raise SystemExit(main())
