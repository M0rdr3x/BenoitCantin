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
    "/netlify.toml",
    "/.gitignore",
)
# Pages et métadonnées explicitement publiques; les pages privées doivent
# être accessibles mais jamais conservées en cache ni indexées.
PRIVATE_ROUTES = (
    "/compte/connexion.html",
    "/admin/index.html",
)
SECURITY_CONTACT = "/.well-known/security.txt"
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
    headers: dict[str, dict[str, str]] = {
        "/": {
            "strict-transport-security": "max-age=31536000",
            "x-content-type-options": "nosniff",
            "content-security-policy": "default-src 'self'; object-src 'self'; frame-ancestors 'self'",
            "referrer-policy": "strict-origin-when-cross-origin",
            "permissions-policy": "camera=(), microphone=()",
        },
    }
    for route in PRIVATE_ROUTES:
        headers[route] = {"cache-control": "private, no-store, max-age=0",
                          "x-robots-tag": "noindex, nofollow, noarchive",
                          "referrer-policy": "no-referrer"}
    live_statuses = dict(good)
    live_statuses.update({route: 200 for route in PRIVATE_ROUTES})
    live_statuses[SECURITY_CONTACT] = 200
    if validate_response_controls(live_statuses, headers):
        raise AssertionError("En-têtes nominaux refusés.")
    mutations = [
        ({**live_statuses, SECURITY_CONTACT: 404}, headers),
        (live_statuses, {**headers, "/": {**headers["/"], "x-content-type-options": "invalid"}}),
        (live_statuses, {**headers, "/": {**headers["/"], "content-security-policy": "default-src *"}}),
        (live_statuses, {**headers, "/": {**headers["/"], "strict-transport-security": "max-age=60"}}),
        (live_statuses, {**headers, PRIVATE_ROUTES[0]: {**headers[PRIVATE_ROUTES[0]], "cache-control": "public"}}),
        (live_statuses, {**headers, PRIVATE_ROUTES[1]: {**headers[PRIVATE_ROUTES[1]], "x-robots-tag": "index"}}),
        ({**live_statuses, PRIVATE_ROUTES[0]: 302}, headers),
    ]
    for index, (mutated_statuses, mutated_headers) in enumerate(mutations, 1):
        if not validate_response_controls(mutated_statuses, mutated_headers):
            raise AssertionError(f"Protection en-têtes non testée: mutation {index}")
    print(f"OK: fixtures de confinement HTTP, en-têtes, confidentialité et {len(mutations)} mutations fail-closed.")


def validate_response_controls(
    statuses: Mapping[str, int],
    observed_headers: Mapping[str, Mapping[str, str]],
) -> list[str]:
    """Contrôles indépendants de l'hébergeur sur les pages publiques et privées.

    Seuls les statuts et les noms/valeurs d'en-têtes de sécurité sont lus.
    Aucun corps, cookie, jeton ou donnée personnelle n'est conservé.
    """
    errors: list[str] = []
    if statuses.get(SECURITY_CONTACT) != 200:
        errors.append("Le canal public de signalement security.txt n'est pas publié (HTTP 200 attendu).")
    home = observed_headers.get("/", {})
    required = {
        "x-content-type-options": "nosniff",
        "referrer-policy": "strict-origin-when-cross-origin",
        "permissions-policy": "camera=",
    }
    for name, fragment in required.items():
        if fragment not in home.get(name, "").lower():
            errors.append(f"Accueil: protection HTTP insuffisante: {name}")
    hsts = home.get("strict-transport-security", "")
    from re import search
    match = search(r"(?:^|;)\s*max-age\s*=\s*(\d+)\b", hsts, flags=2)
    if not match or int(match.group(1)) < 31_536_000:
        errors.append("Accueil: HSTS absent ou max-age < 31536000.")
    csp = home.get("content-security-policy", "").lower()
    for fragment in ("default-src 'self'", "object-src 'self'", "frame-ancestors 'self'"):
        if fragment not in csp:
            errors.append(f"Accueil: CSP absente ou incomplète ({fragment}).")
    for route in PRIVATE_ROUTES:
        if statuses.get(route) != 200:
            errors.append(f"Espace privé non disponible en HTTP 200: {route}")
        headers = observed_headers.get(route, {})
        if "no-store" not in headers.get("cache-control", "").lower():
            errors.append(f"Cache navigateur/intermédiaire non interdit: {route}")
        if "noindex" not in headers.get("x-robots-tag", "").lower():
            errors.append(f"Indexation de la page de compte non interdite: {route}")
        if headers.get("referrer-policy", "").lower() != "no-referrer":
            errors.append(f"Referrer-Policy de la page privée non restrictive: {route}")
    return errors


def read_status(opener, route: str) -> tuple[int, bool, dict[str, str]]:
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
            ), {key.lower(): value for key, value in headers.items()}
    except HTTPError as error:
        try:
            return int(error.code), bool(error.headers.get("x-nf-request-id")) or (
                "netlify" in error.headers.get("Server", "").lower()
            ), {key.lower(): value for key, value in error.headers.items()}
        finally:
            error.close()


def live() -> int:
    opener = build_opener(RefuseRedirect())
    observations: dict[str, int] = {}
    observed_headers: dict[str, dict[str, str]] = {}
    origin_is_netlify = False
    for route in ("/", *TECHNICAL_ROUTES, *PRIVATE_ROUTES, SECURITY_CONTACT):
        try:
            status, netlify, headers = read_status(opener, route)
        except (URLError, OSError, TimeoutError) as error:
            # Ne jamais transformer une erreur réseau en 404 réputé conforme.
            print(f"ECHEC réseau sur {route}: {type(error).__name__}")
            return 1
        observations[route] = status
        if route in ("/", *PRIVATE_ROUTES):
            observed_headers[route] = headers
        if route == "/":
            origin_is_netlify = netlify
        print(f"{route}: HTTP {status}")
    errors = validate_observations(observations, netlify=origin_is_netlify)
    errors.extend(validate_response_controls(observations, observed_headers))
    if errors:
        print(f"ECHEC: {len(errors)} écart(s) de publication; aucune donnée de réponse affichée.")
        for error in errors:
            print("- " + error)
        return 1
    print("PASS: chemins techniques HTTP 404, origine Netlify, en-têtes et confidentialité des espaces privés.")
    print("Ce contrôle ne remplace pas un test d'intrusion ou la preuve de protection de branche main.")
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
