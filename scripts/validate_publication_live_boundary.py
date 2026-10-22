#!/usr/bin/env python3
"""Surveillance HTTP indépendante de la frontière de publication SINJIRA.

La validation du dépôt ne prouve pas que l'hébergeur publie la bonne racine.
Ce contrôle en lecture seule exige une réponse 404 pour les routes techniques
et une signature de l'hébergement Netlify cible, sans télécharger leur corps.
"""
from __future__ import annotations

import argparse
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE_URL = "https://www.benoitcantin.com"
TECHNICAL_ROUTES = (
    "/supabase/config.toml",
    "/tests/e2e/test_public_site.py",
    "/mobile-native/App.tsx",
    "/scripts/build_netlify_public.py",
    "/docs/README.md",
    "/.github/workflows/validate-site.yml",
)
TIMEOUT_SECONDS = 12


class RefuseRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Une redirection vers / ou vers une page HTML ne vaut pas un 404.
        return None


def validate_observations(statuses: Mapping[str, int], *, netlify: bool) -> list[str]:
    errors: list[str] = []
    if statuses.get("/") != 200:
        errors.append("La page d'accueil officielle ne répond pas en HTTP 200.")
    if not netlify:
        errors.append(
            "La réponse de l'accueil ne prouve pas l'hébergement Netlify "
            "(x-nf-request-id / Server: Netlify absents)."
        )
    for route in TECHNICAL_ROUTES:
        observed = statuses.get(route)
        if observed != 404:
            actual = str(observed) if observed is not None else "indisponible"
            errors.append(f"Chemin technique non confiné: {route} -> HTTP {actual} (404 attendu).")
    return errors


def self_test() -> None:
    good: dict[str, int] = {"/": 200}
    good.update({route: 404 for route in TECHNICAL_ROUTES})
    if validate_observations(good, netlify=True):
        raise AssertionError("Le cas nominal isolé a été refusé.")
    for route in TECHNICAL_ROUTES:
        for status in (200, 301, 302, 403, 500):
            bad = dict(good)
            bad[route] = status
            if not any(route in error for error in validate_observations(bad, netlify=True)):
                raise AssertionError(f"Fuite ou redirection non détectée: {route}, HTTP {status}")
        bad = dict(good)
        del bad[route]
        if not any(route in error for error in validate_observations(bad, netlify=True)):
            raise AssertionError(f"Absence de preuve non détectée: {route}")
    if not validate_observations(good, netlify=False):
        raise AssertionError("Hébergement non qualifié accepté.")
    bad_home = dict(good)
    bad_home["/"] = 503
    if not validate_observations(bad_home, netlify=True):
        raise AssertionError("Accueil non disponible accepté.")
    print("OK: fixtures de confinement HTTP, redirections et hébergement fail-closed.")


def read_status(opener, route: str) -> tuple[int, bool]:
    # Origine fixe, sans URL, hostname ni identifiants fournis par l'utilisateur.
    request = Request(
        BASE_URL + route,
        headers={
            "User-Agent": "SINJIRA-publication-boundary/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Accept": "*/*",
        },
        method="GET",
    )
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            status = int(response.status)
            headers = response.headers
            return status, bool(headers.get("x-nf-request-id")) or (
                "netlify" in headers.get("Server", "").lower()
            )
    except HTTPError as error:
        try:
            return int(error.code), bool(error.headers.get("x-nf-request-id")) or (
                "netlify" in error.headers.get("Server", "").lower()
            )
        finally:
            error.close()


def live() -> int:
    opener = build_opener(RefuseRedirect())
    observations: dict[str, int] = {}
    origin_is_netlify = False
    for route in ("/", *TECHNICAL_ROUTES):
        try:
            status, netlify = read_status(opener, route)
        except (URLError, OSError, TimeoutError) as error:
            # Ne jamais transformer une erreur réseau en 404 réputé conforme.
            print(f"ECHEC réseau sur {route}: {type(error).__name__}")
            return 1
        observations[route] = status
        if route == "/":
            origin_is_netlify = netlify
        print(f"{route}: HTTP {status}")
    errors = validate_observations(observations, netlify=origin_is_netlify)
    if errors:
        print(f"ECHEC: {len(errors)} écart(s) de publication; aucune donnée de réponse affichée.")
        for error in errors:
            print("- " + error)
        return 1
    print("PASS: six routes techniques en HTTP 404 et origine Netlify confirmée.")
    print("Ce contrôle ne remplace pas le smoke complet de sécurité et des en-têtes #450.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Contrôler la frontière HTTP du site public.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true", help="Fixtures locales sans réseau.")
    group.add_argument("--live", action="store_true", help="GET sur l'origine officielle uniquement.")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    return live()


if __name__ == "__main__":
    raise SystemExit(main())
