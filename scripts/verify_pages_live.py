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
from pages_release_proof import MARKER, render

BASE = "https://www.benoitcantin.com"
PUBLIC_ROUTES = (
    "/", "/404.html", "/compte/", "/projets/sinjira/",
    "/projets/projet-nova/", "/robots.txt", "/sitemap.xml",
    "/assets/js/site.js",
    "/projets/projet-nova/data/boussole-partis-2026.json",
    "/projets/projet-nova/data/boussole-preuves-2026.json",
    "/projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf",
    "/assets/media/nova-logo.webp",
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
    "/assets/icons/README.md",
    "/projets/projet-nova/netlify.toml",
    "/projets/projet-nova/UPLOAD_GITHUB.md",
    "/projets/projet-nova/SECURITY.md",
    "/projets/sinjira/codex/livre-i-delivery-contract.json",
)
ERROR_CODES = {404, 410}
# Un HTTP 200 HTML sur un JS, un sitemap ou un robots.txt masque une publication cassée.
MIME_HINTS = {
    "/robots.txt": ("text/plain",),
    "/sitemap.xml": ("application/xml", "text/xml"),
    "/assets/js/site.js": ("application/javascript", "text/javascript",
                           "application/x-javascript", "application/ecmascript",
                           "text/ecmascript"),
    "/projets/projet-nova/data/boussole-partis-2026.json": ("application/json",),
    "/projets/projet-nova/data/boussole-preuves-2026.json": ("application/json",),
    "/projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf": ("application/pdf",),
    "/assets/media/nova-logo.webp": ("image/webp",),
}
USER_AGENT = "SINJIRA-Pages-Publication-Audit/1.0"


@dataclass(frozen=True)
class Reply:
    status: int
    location: str = ""
    content_type: str = ""
    body: bytes = b""


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
        body = response.read(2049) if urlparse(url).path == "/" + MARKER else b""
        return Reply(response.status, response.headers.get("Location", ""),
                     response.headers.get("Content-Type", ""), body)


def verify(base: str, getter: Callable[[str], Reply],
           release: tuple[str, str] | None = None) -> list[str]:
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
        if result.status == 200:
            content_type = result.content_type.split(";", 1)[0].strip().lower()
            if path.endswith((".html", "/")) and content_type != "text/html":
                errors.append(f"Parcours public {path}: type MIME HTML inattendu")
            if path in MIME_HINTS and content_type not in MIME_HINTS[path]:
                errors.append(f"Parcours public {path}: type MIME non conforme ({content_type or 'absent'})")
    if release is not None:
        marker_url = base + "/" + MARKER
        try:
            expected_receipt = render(*release)
            receipt = getter(marker_url)
        except (URLError, OSError, TimeoutError, ValueError) as exc:
            errors.append(f"Reçu de publication non vérifiable ({type(exc).__name__})")
        else:
            if receipt.status != 200:
                errors.append(f"Reçu de publication absent: HTTP {receipt.status}")
            if receipt.location:
                errors.append("Reçu de publication : redirection interdite")
            mime = receipt.content_type.split(";", 1)[0].strip().lower()
            if mime != "application/json":
                errors.append("Reçu de publication : MIME JSON incorrect")
            if receipt.body != expected_receipt:
                errors.append("Reçu de publication différent du SHA/run approuvés")
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
        mime = "text/html" if path.endswith(("/", ".html")) else {
            "/assets/js/site.js": "text/javascript",
            "/sitemap.xml": "application/xml",
            "/projets/projet-nova/data/boussole-partis-2026.json": "application/json",
            "/projets/projet-nova/data/boussole-preuves-2026.json": "application/json",
            "/projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf": "application/pdf",
            "/assets/media/nova-logo.webp": "image/webp",
        }.get(path, "text/plain")
        return Reply(200, content_type=mime)
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
    for asset in MIME_HINTS:
        def wrong_mime(url: str) -> Reply:
            if url == BASE + asset:
                return Reply(200, content_type="text/html")
            return fixture(url)
        assert any(asset in e and "MIME" in e for e in verify(BASE, wrong_mime)), (
            f'Réponse HTML déguisée en ressource non détectée: {asset}'
        )
    def missing_mime(url: str) -> Reply:
        if url == BASE + "/assets/js/site.js":
            return Reply(200, content_type="")
        return fixture(url)
    assert any("site.js" in e and "MIME" in e for e in verify(BASE, missing_mime)), (
        "Header Content-Type manquant non détecté"
    )
    sha, run = "a" * 40, "1234567"
    def receipt_ok(url: str) -> Reply:
        if url == BASE + "/" + MARKER:
            return Reply(200, content_type="application/json", body=render(sha, run))
        return fixture(url)
    assert not verify(BASE, receipt_ok, (sha, run)), (
        verify(BASE, receipt_ok, (sha, run))
    )
    assert any("Reçu de publication" in e for e in verify(BASE, receipt_ok, ("b" * 40, run))), (
        "Mauvaise version publiée non détectée"
    )
    assert any("Reçu de publication" in e for e in verify(BASE, fixture, (sha, run))), (
        "Absence de reçu non détectée"
    )
    def receipt_redirect(url: str) -> Reply:
        if url == BASE + "/" + MARKER:
            return Reply(302, location="https://other.example/", content_type="text/html")
        return fixture(url)
    assert any("Reçu de publication" in e for e in verify(BASE, receipt_redirect, (sha, run))), (
        "Redirection d'identité non détectée"
    )
    assert verify("http://www.benoitcantin.com", fixture), "HTTP en clair"
    assert verify("https://example.com", fixture), "Hôte tiers"
    print("OK autotests HTTP : fuites, MIME, redirections et identité SHA/run prouvées")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check", action="store_true",
                        help="Envoie exclusivement des requêtes GET HTTPS en lecture seule au site officiel")
    parser.add_argument("--release-sha")
    parser.add_argument("--release-run-id")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.check:
        parser.error("Préciser --self-test ou --check (aucun réseau par défaut)")
    if bool(args.release_sha) != bool(args.release_run_id):
        parser.error("--release-sha et --release-run-id requis ensemble")
    identity = (args.release_sha, args.release_run_id) if args.release_sha else None
    errors = verify(BASE, fetch, identity)
    if errors:
        print(f"ECHEC preuve live : {len(errors)} problème(s) détecté(s)", file=sys.stderr)
        for error in errors:
            print("- " + error, file=sys.stderr)
        return 1
    print(f"OK HTTP : {len(PUBLIC_ROUTES)} routes publiques, "
          f"{len(PRIVATE_ROUTES)} chemins techniques protégés"
          + (", et reçu SHA/run identique au déploiement" if identity else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
