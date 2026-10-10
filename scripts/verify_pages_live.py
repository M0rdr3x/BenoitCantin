#!/usr/bin/env python3
"""Contrôle HTTP externe en lecture seule après une publication Pages explicitement approuvée."""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE = "https://www.benoitcantin.com"
PUBLIC_ROUTES = (
    "/", "/404.html", "/compte/", "/projets/sinjira/",
    "/projets/projet-nova/", "/robots.txt", "/sitemap.xml",
    "/assets/js/site.js",
)
PRIVATE_ROUTES = (
    "/supabase/config.toml",
    "/tests/e2e/test_public_site.py",
    "/mobile-native/App.tsx",
    "/scripts/validate_site.py",
    "/scripts/audit_pages_jekyll.py",
    "/.github/workflows/validate-site.yml",
    "/docs/README.md",
    "/_config.yml",
)
ERROR_CODES = {404, 410}
USER_AGENT = "SINJIRA-Pages-Publication-Audit/1.0"


@dataclass(frozen=True)
class Reply:
    status: int
    location: str = ""
    content_type: str = ""


class StopRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def fetch(url: str) -> Reply:
    opener = build_opener(StopRedirects)
    req = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Accept": "*/*",
    })
    try:
        response = opener.open(req, timeout=12)
    except HTTPError as exc:
        return Reply(exc.code, exc.headers.get("Location", ""),
                     exc.headers.get("Content-Type", ""))
    with response:
        return Reply(response.status, response.headers.get("Location", ""),
                     response.headers.get("Content-Type", ""))


def verify(base: str, getter: Callable[[str], Reply]) -> list[str]:
    target = urlparse(base)
    if (base != BASE or target.scheme != "https" or target.netloc != "www.benoitcantin.com"
            or target.path or target.query or target.fragment):
        return ["Base de contrôle interdite : le domaine officiel HTTPS est requis."]
    errors: list[str] = []
    for path in PUBLIC_ROUTES:
        current = base + path
        result = None
        for hop in range(4):
            try:
                result = getter(current)
            except (URLError, OSError, TimeoutError, ValueError) as exc:
                errors.append(f"Parcours public {path}: erreur réseau ({type(exc).__name__})")
                result = None
                break
            if result.status not in {301, 302, 307, 308}:
                break
            if not result.location or hop == 3:
                errors.append(f"Parcours public {path}: trop de redirections")
                break
            new = urljoin(current, result.location)
            u = urlparse(new)
            if u.scheme != "https" or u.netloc != "www.benoitcantin.com":
                errors.append(f"Parcours public {path}: redirection hors domaine officiel")
                break
            current = new
        if result is None:
            continue
        if result.status != 200:
            errors.append(f"Parcours public {path}: HTTP {result.status} (200 attendu)")
        if path.endswith(".html") or path.endswith("/") and path not in {"/assets/js/"}:
            if result.status == 200 and "text/html" not in result.content_type.lower():
                errors.append(f"Parcours public {path}: type MIME HTML inattendu")
    for path in PRIVATE_ROUTES:
        try:
            result = getter(base + path)
        except (URLError, OSError, TimeoutError, ValueError) as exc:
            errors.append(f"Source technique {path}: erreur réseau ({type(exc).__name__})")
            continue
        if result.status not in ERROR_CODES:
            errors.append(f"Source technique {path}: HTTP {result.status} (404/410 strict requis)")
    return errors


def self_test() -> None:
    def fixture(url: str) -> Reply:
        path = urlparse(url).path
        if path in PRIVATE_ROUTES:
            return Reply(404, content_type="text/html")
        return Reply(200, content_type="text/html" if path.endswith("/") or path.endswith(".html") else "text/plain")
    assert not verify(BASE, fixture), verify(BASE, fixture)
    def leak(url: str) -> Reply:
        if url.endswith(PRIVATE_ROUTES[0]):
            return Reply(200, content_type="text/plain")
        return fixture(url)
    assert any("supabase/config.toml" in e for e in verify(BASE, leak)), "Fuite technique non détectée"
    def redirect_leak(url: str) -> Reply:
        if url.endswith(PRIVATE_ROUTES[1]):
            return Reply(302, location="/compte/")
        return fixture(url)
    assert any("test_public_site.py" in e for e in verify(BASE, redirect_leak)), "Redirect trompeur"
    def external(url: str) -> Reply:
        if url == BASE + "/":
            return Reply(302, location="https://other.example/")
        return fixture(url)
    assert any("hors domaine" in e for e in verify(BASE, external)), "Redirection externe"
    def missing(url: str) -> Reply:
        if url == BASE + "/projets/sinjira/":
            return Reply(404, content_type="text/html")
        return fixture(url)
    assert any("projets/sinjira/" in e for e in verify(BASE, missing)), "Parcours public disparu"
    assert verify("http://www.benoitcantin.com", fixture), "HTTP en clair"
    assert verify("https://example.com", fixture), "Hôte tiers"
    print("OK autotests HTTP : fuites, redirections, pertes de routes et origin imposée")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check", action="store_true",
                        help="Envoie exclusivement des requêtes GET HTTPS en lecture seule au site officiel")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.check:
        parser.error("Préciser --self-test ou --check (aucun réseau par défaut)")
    errors = verify(BASE, fetch)
    if errors:
        print(f"ECHEC preuve live : {len(errors)} problème(s) détecté(s)", file=sys.stderr)
        for error in errors:
            print("- " + error, file=sys.stderr)
        return 1
    print(f"OK HTTP : {len(PUBLIC_ROUTES)} routes publiques et "
          f"{len(PRIVATE_ROUTES)} chemins techniques protégés")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
