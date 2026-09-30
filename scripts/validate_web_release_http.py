#!/usr/bin/env python3
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re
import threading
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

USER_AGENT = "SINJIRA-Web-Release-Smoke/1.0"
TIMEOUT_SECONDS = 12
OFFICIAL_PRODUCTION_HOSTS = {"www.benoitcantin.com", "benoitcantin.com"}

PRIVATE_RUNTIME_PATHS = (
    "/compte/",
    "/admin/",
    "/app/",
)

PUBLIC_PATHS = (
    "/",
    "/.well-known/security.txt",
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
REQUIRED_ROBOTS_DISALLOWS = (
    "/app/",
    "/compte/",
    "/histoire-de-vie/",
    "/Admin/",
    "/admin/",
    "/supabase/",
    "/.github/",
    "/mobile-native/",
    "/tests/",
    "/docs/",
    "/scripts/",
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


class SameHostRedirectHandler(HTTPRedirectHandler):
    def __init__(self, allowed_host: str, allow_http: bool = False) -> None:
        super().__init__()
        self.allowed_host = allowed_host.lower()
        self.allow_http = allow_http

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlparse(newurl)
        host = (parsed.hostname or "").lower()
        if host != self.allowed_host:
            raise HTTPError(newurl, code, "Redirection vers un autre hôte refusée", headers, fp)
        if parsed.scheme != "https" and not self.allow_http:
            raise HTTPError(newurl, code, "Redirection non HTTPS refusée", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def validate_target_url(base_url: str, context: str) -> list[str]:
    errors: list[str] = []
    if len(base_url) > 2048:
        errors.append("URL de release invalide: longueur supérieure à 2048 caractères.")
    if any(ord(char) < 32 or ord(char) == 127 for char in base_url):
        errors.append("URL de release invalide: caractères de contrôle interdits.")
    if errors:
        return errors

    parsed = urlparse(base_url)
    host = (parsed.hostname or "").lower()
    local = host in {"127.0.0.1", "localhost"}

    if parsed.username or parsed.password:
        errors.append("URL de release invalide: credentials interdits.")
    if not host:
        errors.append("URL de release invalide: hôte absent.")
    if parsed.scheme != "https" and not local:
        errors.append("URL de release invalide: HTTPS requis.")
    if parsed.port not in {None, 443} and not local:
        errors.append("URL de release invalide: port non standard interdit.")

    if parsed.path not in {"", "/"}:
        errors.append("URL de release invalide: fournir uniquement l’origine, sans sous-chemin.")
    if parsed.query:
        errors.append("URL de release invalide: query string interdite.")
    if parsed.fragment:
        errors.append("URL de release invalide: fragment interdit.")

    if context == "preview" and not local and not host.endswith(".netlify.app"):
        errors.append("Deploy preview invalide: hôte *.netlify.app requis.")
    if context == "production" and not local and host not in OFFICIAL_PRODUCTION_HOSTS:
        errors.append("Production invalide: domaine officiel benoîtcantin.com requis.")

    return errors


def request(base_url: str, path: str) -> tuple[int, object, str]:
    parsed_base = urlparse(base_url)
    host = (parsed_base.hostname or "").lower()
    local = host in {"127.0.0.1", "localhost"}
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
    opener = build_opener(SameHostRedirectHandler(host, allow_http=local))
    try:
        with opener.open(req, timeout=TIMEOUT_SECONDS) as response:
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

    if "https://www.bubblav.com" in directives.get("script-src", []):
        errors.append("CSP réseau: BubblaV doit rester bloqué dans script-src.")
    if "https://www.bubblav.com" in directives.get("connect-src", []):
        errors.append("CSP réseau: BubblaV doit rester bloqué dans connect-src.")
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


def validate_private_headers(headers: object, path: str) -> list[str]:
    errors: list[str] = []
    get = getattr(headers, "get")

    cache_control = str(get("Cache-Control") or "").lower()
    if "no-store" not in cache_control:
        errors.append(f"{path}: Cache-Control no-store absent.")

    robots = str(get("X-Robots-Tag") or "").lower()
    for token in ("noindex", "nofollow", "noarchive"):
        if token not in robots:
            errors.append(f"{path}: X-Robots-Tag sans {token}.")

    return errors


def validate_release(base_url: str, context: str) -> list[str]:
    errors = validate_target_url(base_url, context)
    if errors:
        return errors

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

    for private_path in PRIVATE_RUNTIME_PATHS:
        response = responses.get(private_path)
        if response:
            errors.extend(validate_private_headers(response[1], private_path))

    assistant = responses.get("/assistant.html")
    if assistant and "Assistant Nova" not in assistant[2]:
        errors.append("/assistant.html: contenu attendu absent.")

    transparency = responses.get("/transparence-ia.html")
    if transparency and "Transparence IA" not in transparency[2]:
        errors.append("/transparence-ia.html: contenu attendu absent.")

    robots = responses.get("/robots.txt")
    if robots:
        robots_body = robots[2]
        for route in REQUIRED_ROBOTS_DISALLOWS:
            if f"Disallow: {route}" not in robots_body:
                errors.append(f"/robots.txt: exclusion requise absente: {route}")

    security = responses.get("/.well-known/security.txt")
    if security:
        security_body = security[2]
        required_security_lines = (
            "Contact: https://www.benoitcantin.com/contact.html",
            "Canonical: https://www.benoitcantin.com/.well-known/security.txt",
            "Preferred-Languages: fr, en",
            "Expires:",
        )
        for expected_line in required_security_lines:
            if expected_line not in security_body:
                errors.append(
                    f"/.well-known/security.txt: champ canonique absent: {expected_line}"
                )

    return errors


class FixtureHandler(BaseHTTPRequestHandler):
    server_version = "SINJIRASmokeFixture/1.0"

    def do_GET(self) -> None:
        technical = self.path in TECHNICAL_404_PATHS
        private_runtime = self.path in PRIVATE_RUNTIME_PATHS
        self.send_response(404 if technical else 200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'self'; object-src 'self'; base-uri 'self'",
        )
        if private_runtime:
            self.send_header("Cache-Control", "no-store")
        if getattr(self.server, "preview", False) or private_runtime:
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
        elif self.path == "/.well-known/security.txt":
            body = (
                "Contact: https://www.benoitcantin.com/contact.html\n"
                "Expires: 2027-09-27T23:59:59Z\n"
                "Preferred-Languages: fr, en\n"
                "Canonical: https://www.benoitcantin.com/.well-known/security.txt\n"
            )
        elif self.path == "/robots.txt":
            body = "User-agent: *\n" + "".join(
                f"Disallow: {route}\n" for route in REQUIRED_ROBOTS_DISALLOWS
            )
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

    private_broken = validate_private_headers(
        {"X-Robots-Tag": "noindex"},
        "/compte/",
    )
    if not private_broken:
        raise SystemExit("ERREUR auto-test smoke HTTP: en-têtes privés affaiblis non détectés.")

    provider_enabled = validate_headers(
        {
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' https://www.bubblav.com; "
                "connect-src 'self' https://www.bubblav.com; "
                "frame-ancestors 'self'; object-src 'self'; base-uri 'self'"
            ),
            "X-Content-Type-Options": "nosniff",
            "X-Robots-Tag": "noindex, nofollow, noarchive",
        },
        "preview",
    )
    if not any("BubblaV doit rester bloqué" in error for error in provider_enabled):
        raise SystemExit("ERREUR auto-test smoke HTTP: CSP BubblaV réactivée non détectée.")

    invalid_targets = (
        ("http://example.netlify.app", "preview"),
        ("https://example.com", "preview"),
        ("https://user:pass@example.netlify.app", "preview"),
        ("https://www.netlify.app:8443", "preview"),
        ("https://example.netlify.app/sub/path", "preview"),
        ("https://example.netlify.app/?draft=1", "preview"),
        ("https://example.netlify.app/#section", "preview"),
        ("https://example.netlify.app\n#summary-injection", "preview"),
        ("https://example.netlify.app\t", "preview"),
        ("https://" + ("a" * 2040) + ".netlify.app", "preview"),
        ("https://example.netlify.app", "production"),
    )
    missed = [
        url
        for url, context in invalid_targets
        if not validate_target_url(url, context)
    ]
    if missed:
        raise SystemExit("ERREUR auto-test smoke HTTP: cibles dangereuses acceptées: " + ", ".join(missed))

    print(
        "OK auto-tests smoke HTTP: preview, production, cibles autorisées, "
        "CSP, noindex, no-store privé, robots privés et 404 techniques vérifiés."
    )


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
