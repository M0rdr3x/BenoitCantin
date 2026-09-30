#!/usr/bin/env python3
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re
import threading
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

USER_AGENT = "SINJIRA-Web-Release-Smoke/1.0"
TIMEOUT_SECONDS = 12

PUBLIC_PATHS = (
    "/",
    "/assistant.html",
    "/transparence-ia.html",
    "/projets/projet-nova/",
    "/compte/",
    "/admin/",
    "/app/",
    "/robots.txt",
    "/sitemap.xml",
)

TECHNICAL_404_PATHS = (
    "/supabase/config.toml",
    "/scripts/build_netlify_public.py",
    "/docs/README.md",
    "/.github/workflows/validate-site.yml",
    "/tests/e2e/test_public_site.py",
    "/mobile-native/App.tsx",
)

EXPECTED_NAV_HREFS = (
    "/",
    "/projets/sinjira/",
    "/projets/projet-nova/",
    "/a-propos.html",
    "/compte/",
)

FORBIDDEN_GLOBAL_NAV_HREFS = (
    "/projets/sinjira/registre/",
    "/contact.html",
)


def request(base_url: str, path: str) -> tuple[int, object, str]:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
    try:
        with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, response.headers, body
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, exc.headers, body


def parse_csp(value: str) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {}
    for raw in value.split(";"):
        tokens = raw.strip().split()
        if tokens:
            directives[tokens[0].lower()] = tokens[1:]
    return directives


def validate_home(body: str) -> list[str]:
    errors: list[str] = []
    nav = re.search(
        r'<nav[^>]+id=["\']navigation-principale["\'][^>]*>(.*?)</nav>',
        body,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not nav:
        return ["Navigation principale introuvable sur l’accueil."]

    nav_html = nav.group(1)
    for href in EXPECTED_NAV_HREFS:
        if f'href="{href}"' not in nav_html and f"href='{href}'" not in nav_html:
            errors.append(f"Lien navigation attendu absent: {href}")
    for href in FORBIDDEN_GLOBAL_NAV_HREFS:
        if f'href="{href}"' in nav_html or f"href='{href}'" in nav_html:
            errors.append(f"Lien interdit encore présent dans la navigation globale: {href}")

    if "data-ai-transparency" not in body:
        errors.append("Bandeau Transparence IA absent de l’accueil.")
    if "/transparence-ia.html" not in body:
        errors.append("Lien Transparence IA absent de l’accueil.")
    return errors


def validate_headers(headers: object, context: str) -> list[str]:
    errors: list[str] = []
    get = getattr(headers, "get")
    csp = str(get("Content-Security-Policy") or "")
    directives = parse_csp(csp)

    if "https://www.bubblav.com" not in directives.get("script-src", []):
        errors.append("CSP réseau: BubblaV absent de script-src.")
    if "https://www.bubblav.com" not in directives.get("connect-src", []):
        errors.append("CSP réseau: BubblaV absent de connect-src.")
    if "'self'" not in directives.get("frame-ancestors", []):
        errors.append("CSP réseau: frame-ancestors 'self' absent.")
    if "'self'" not in directives.get("object-src", []):
        errors.append("CSP réseau: object-src 'self' absent.")
    if "'self'" not in directives.get("base-uri", []):
        errors.append("CSP réseau: base-uri 'self' absent.")

    if str(get("X-Content-Type-Options") or "").lower() != "nosniff":
        errors.append("En-tête réseau X-Content-Type-Options=nosniff absent.")

    robots = str(get("X-Robots-Tag") or "").lower()
    if context == "preview":
        for token in ("noindex", "nofollow", "noarchive"):
            if token not in robots:
                errors.append(f"Deploy preview: X-Robots-Tag sans {token}.")
    elif "noindex" in robots:
        errors.append("Production: X-Robots-Tag noindex inattendu sur l’accueil.")

    return errors


def validate_release(base_url: str, context: str) -> list[str]:
    errors: list[str] = []
    parsed = urlparse(base_url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" and host not in {"127.0.0.1", "localhost"}:
        return ["URL de release invalide: HTTPS requis hors auto-test local."]

    responses: dict[str, tuple[int, object, str]] = {}
    for path in PUBLIC_PATHS:
        try:
            responses[path] = request(base_url, path)
        except (URLError, OSError, TimeoutError) as exc:
            errors.append(f"{path}: requête impossible: {exc}")
            continue
        status, _, _ = responses[path]
        if status != 200:
            errors.append(f"{path}: HTTP {status}, 200 attendu.")

    for path in TECHNICAL_404_PATHS:
        try:
            status, _, _ = request(base_url, path)
        except (URLError, OSError, TimeoutError) as exc:
            errors.append(f"{path}: requête impossible: {exc}")
            continue
        if status != 404:
            errors.append(f"{path}: HTTP {status}, 404 attendu.")

    home = responses.get("/")
    if home:
        _, headers, body = home
        errors.extend(validate_headers(headers, context))
        errors.extend(validate_home(body))

    assistant = responses.get("/assistant.html")
    if assistant and "Assistant Nova" not in assistant[2]:
        errors.append("/assistant.html: contenu attendu absent.")

    transparency = responses.get("/transparence-ia.html")
    if transparency and "Transparence IA" not in transparency[2]:
        errors.append("/transparence-ia.html: contenu attendu absent.")

    return errors


class FixtureHandler(BaseHTTPRequestHandler):
    server_version = "SINJIRASmokeFixture/1.0"

    def do_GET(self) -> None:
        technical = self.path in TECHNICAL_404_PATHS
        self.send_response(404 if technical else 200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' https://www.bubblav.com; "
            "connect-src 'self' https://www.bubblav.com; "
            "frame-ancestors 'self'; object-src 'self'; base-uri 'self'",
        )
        if getattr(self.server, "preview", False):
            self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
        self.end_headers()

        if technical:
            self.wfile.write(b"not found")
            return

        if self.path == "/":
            body = """<!doctype html><html><body>
<nav class="main-nav" id="navigation-principale">
<a href="/">Accueil</a><a href="/projets/sinjira/">SINJIRA</a>
<a href="/projets/projet-nova/">Projet Nova</a><a href="/a-propos.html">A propos</a>
<a href="/compte/">Compte</a></nav>
<aside data-ai-transparency>Transparence IA <a href="/transparence-ia.html">Lire</a></aside>
</body></html>"""
        elif self.path == "/assistant.html":
            body = "<html><body>Assistant Nova</body></html>"
        elif self.path == "/transparence-ia.html":
            body = "<html><body>Transparence IA</body></html>"
        else:
            body = "<html><body>OK</body></html>"
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        return


def run_fixture(preview: bool) -> str:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    server.preview = preview
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        errors = validate_release(base, "preview" if preview else "production")
        if errors:
            raise SystemExit("ERREUR auto-test smoke HTTP: " + " | ".join(errors))
        return base
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def self_test() -> None:
    run_fixture(preview=True)
    run_fixture(preview=False)

    broken = validate_headers(
        {
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; connect-src 'self'",
            "X-Content-Type-Options": "nosniff",
        },
        "preview",
    )
    if not broken:
        raise SystemExit("ERREUR auto-test smoke HTTP: en-têtes affaiblis non détectés.")

    print("OK auto-tests smoke HTTP: preview, production, CSP, noindex et 404 techniques vérifiés.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke HTTP d'une preview ou production web SINJIRA.")
    parser.add_argument("url", nargs="?")
    parser.add_argument("--context", choices=("preview", "production"), default="preview")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if not args.url:
        parser.error("URL requise hors --self-test")

    errors = validate_release(args.url, args.context)
    if errors:
        print(f"ECHEC smoke HTTP: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        f"OK smoke HTTP {args.context}: navigation, pages IA, en-têtes, "
        "routes publiques et 404 techniques conformes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
