#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re
import threading
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

USER_AGENT = "SINJIRA-Web-Release-Smoke/1.0"
TIMEOUT_SECONDS = 12
OFFICIAL_PRODUCTION_HOSTS = {"www.benoitcantin.com", "benoitcantin.com"}
RELEASE_METADATA_PATH = "/.well-known/release.json"
SELF_TEST_RELEASE_SHA = "a" * 40

PRIVATE_RUNTIME_PATHS = (
    "/compte/",
    "/admin/",
    "/app/",
    "/Admin/sinjira/",
    "/histoire-de-vie/remise.html",
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
    "/Admin/sinjira/",
    "/histoire-de-vie/remise.html",
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

    if context in {"preview", "production-candidate"} and not local:
        if not host.endswith(".netlify.app"):
            errors.append("Deploy Netlify invalide: hôte *.netlify.app requis.")
        else:
            netlify_label = host.removesuffix(".netlify.app")
            if "--" not in netlify_label:
                errors.append("Deploy Netlify invalide: permalink atomique requis (deploy-id--site.netlify.app).")
            else:
                deploy_id, site_name = netlify_label.split("--", 1)
                if not re.fullmatch(r"[0-9a-f]{12,64}", deploy_id):
                    errors.append("Deploy Netlify invalide: préfixe deploy-id hexadécimal requis; alias preview/branche refusé.")
                if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", site_name or ""):
                    errors.append("Deploy Netlify invalide: nom de site inattendu.")
    if context == "production" and not local and host not in OFFICIAL_PRODUCTION_HOSTS:
        errors.append("Production invalide: domaine officiel benoîtcantin.com requis.")

    return errors


def validate_netlify_pair(preview_url: str, production_url: str) -> list[str]:
    errors: list[str] = []
    preview_errors = validate_target_url(preview_url, "preview")
    production_errors = validate_target_url(production_url, "production-candidate")
    errors.extend(f"preview: {error}" for error in preview_errors)
    errors.extend(f"production-candidate: {error}" for error in production_errors)
    if errors:
        return errors

    preview_host = (urlparse(preview_url).hostname or "").lower()
    production_host = (urlparse(production_url).hostname or "").lower()
    preview_deploy, preview_site = preview_host.removesuffix(".netlify.app").split("--", 1)
    production_deploy, production_site = production_host.removesuffix(".netlify.app").split("--", 1)

    if preview_site != production_site:
        errors.append(
            "Gate pré-DNS: preview et production-candidate doivent appartenir au même site Netlify."
        )
    if preview_deploy == production_deploy:
        errors.append(
            "Gate pré-DNS: preview et production-candidate doivent utiliser deux deploy-id distincts."
        )
    return errors


def request(base_url: str, path: str) -> tuple[int, object, str]:
    parsed_base = urlparse(base_url)
    host = (parsed_base.hostname or "").lower()
    local = host in {"127.0.0.1", "localhost"}
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,*/*",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
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

    if "'self'" not in directives.get("default-src", []):
        errors.append("CSP réseau: default-src 'self' absent.")
    if "'self'" not in directives.get("script-src", []):
        errors.append("CSP réseau: script-src 'self' absent.")
    if "https://cdn.jsdelivr.net" not in directives.get("script-src", []):
        errors.append("CSP réseau: CDN JavaScript attendu absent de script-src.")
    if "'self'" not in directives.get("connect-src", []):
        errors.append("CSP réseau: connect-src 'self' absent.")
    for endpoint in (
        "https://gpvivleexywljowcqkru.supabase.co",
        "wss://gpvivleexywljowcqkru.supabase.co",
    ):
        if endpoint not in directives.get("connect-src", []):
            errors.append(f"CSP réseau: endpoint Supabase attendu absent: {endpoint}.")
    if "https://formspree.io" not in directives.get("form-action", []):
        errors.append("CSP réseau: Formspree attendu absent de form-action.")
    if "'self'" not in directives.get("form-action", []):
        errors.append("CSP réseau: form-action 'self' absent.")
    if "'self'" not in directives.get("img-src", []):
        errors.append("CSP réseau: img-src 'self' absent.")
    if "data:" not in directives.get("img-src", []):
        errors.append("CSP réseau: data: absent de img-src.")
    if "'self'" not in directives.get("style-src", []):
        errors.append("CSP réseau: style-src 'self' absent.")
    if "'self'" not in directives.get("worker-src", []):
        errors.append("CSP réseau: worker-src 'self' absent.")
    if "blob:" not in directives.get("worker-src", []):
        errors.append("CSP réseau: blob: absent de worker-src.")
    if "'self'" not in directives.get("font-src", []):
        errors.append("CSP réseau: font-src 'self' absent.")

    if str(get("X-Content-Type-Options") or "").lower() != "nosniff":
        errors.append("En-tête réseau X-Content-Type-Options=nosniff absent.")
    if str(get("X-Permitted-Cross-Domain-Policies") or "").lower() != "none":
        errors.append("En-tête réseau X-Permitted-Cross-Domain-Policies=none absent.")
    if str(get("X-Frame-Options") or "").upper() != "SAMEORIGIN":
        errors.append("En-tête réseau X-Frame-Options=SAMEORIGIN absent.")
    if str(get("Referrer-Policy") or "").lower() != "strict-origin-when-cross-origin":
        errors.append("En-tête réseau Referrer-Policy strict-origin-when-cross-origin absent.")

    permissions = str(get("Permissions-Policy") or "").lower().replace(" ", "")
    for directive in ("camera=()", "microphone=()", "geolocation=()", "payment=()"):
        if directive not in permissions:
            errors.append(f"En-tête réseau Permissions-Policy sans {directive}.")

    hsts = str(get("Strict-Transport-Security") or "").lower()
    match = re.search(r"(?:^|;)\s*max-age=(\d+)", hsts)
    if not match or int(match.group(1)) < 31536000:
        errors.append("En-tête réseau HSTS max-age >= 31536000 absent.")

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


def validate_release_headers(headers: object) -> list[str]:
    errors: list[str] = []
    get = getattr(headers, "get")
    cache_control = str(get("Cache-Control") or "").lower()
    if "no-store" not in cache_control:
        errors.append(f"{RELEASE_METADATA_PATH}: Cache-Control no-store absent.")
    robots = str(get("X-Robots-Tag") or "").lower()
    for token in ("noindex", "nofollow", "noarchive"):
        if token not in robots:
            errors.append(f"{RELEASE_METADATA_PATH}: X-Robots-Tag sans {token}.")
    return errors


def validate_release_metadata(body: str, context: str, expected_sha: str) -> list[str]:
    errors: list[str] = []
    normalized_sha = expected_sha.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", normalized_sha):
        return ["SHA de release attendu invalide: 40 caractères hexadécimaux requis."]
    try:
        metadata = json.loads(body)
    except json.JSONDecodeError as exc:
        return [f"{RELEASE_METADATA_PATH}: JSON invalide: {exc}"]
    if not isinstance(metadata, dict):
        return [f"{RELEASE_METADATA_PATH}: objet JSON attendu."]
    if metadata.get("schema_version") != 1:
        errors.append(f"{RELEASE_METADATA_PATH}: schema_version=1 requis.")
    if str(metadata.get("source_sha") or "").lower() != normalized_sha:
        errors.append(f"{RELEASE_METADATA_PATH}: source_sha ne correspond pas au SHA attendu.")
    metadata_context = "preview" if context == "preview" else "production"
    if metadata.get("context") != metadata_context:
        errors.append(f"{RELEASE_METADATA_PATH}: contexte {metadata_context!r} attendu.")
    return errors


def validate_release(
    base_url: str,
    context: str,
    expected_sha: str | None = None,
    same_netlify_site_as: str | None = None,
) -> list[str]:
    errors = validate_target_url(base_url, context)
    if expected_sha and not re.fullmatch(r"[0-9a-fA-F]{40}", expected_sha.strip()):
        errors.append("SHA de release attendu invalide: 40 caractères hexadécimaux requis.")
    if same_netlify_site_as:
        if context != "production-candidate":
            errors.append("--same-netlify-site-as est réservé au contexte production-candidate.")
        else:
            errors.extend(validate_netlify_pair(same_netlify_site_as, base_url))
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

    if expected_sha:
        try:
            release_status, release_headers, release_body = request(base_url, RELEASE_METADATA_PATH)
        except (URLError, OSError, TimeoutError) as exc:
            errors.append(f"{RELEASE_METADATA_PATH}: requête impossible: {exc}")
        else:
            if release_status != 200:
                errors.append(f"{RELEASE_METADATA_PATH}: HTTP {release_status}, 200 attendu.")
            else:
                errors.extend(validate_release_headers(release_headers))
                errors.extend(validate_release_metadata(release_body, context, expected_sha))

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
        release_metadata = self.path == RELEASE_METADATA_PATH
        self.send_response(404 if technical else 200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Strict-Transport-Security", "max-age=31536000")
        self.send_header("X-Permitted-Cross-Domain-Policies", "none")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=()",
        )
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "worker-src 'self' blob:; "
            "font-src 'self'; "
            "connect-src 'self' https://gpvivleexywljowcqkru.supabase.co "
            "wss://gpvivleexywljowcqkru.supabase.co; "
            "form-action 'self' https://formspree.io; "
            "frame-ancestors 'self'; object-src 'self'; base-uri 'self'",
        )
        if private_runtime or release_metadata:
            self.send_header("Cache-Control", "no-store")
        if getattr(self.server, "preview", False) or private_runtime or release_metadata:
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
        elif self.path == RELEASE_METADATA_PATH:
            body = json.dumps(
                {
                    "schema_version": 1,
                    "source_sha": SELF_TEST_RELEASE_SHA,
                    "context": "preview" if getattr(self.server, "preview", False) else "production",
                }
            )
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


def run_fixture(context: str) -> str:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    server.preview = context == "preview"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        errors = validate_release(
            base,
            context,
            expected_sha=SELF_TEST_RELEASE_SHA,
        )
        if errors:
            raise SystemExit("ERREUR auto-test smoke HTTP: " + " | ".join(errors))
        return base
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def self_test() -> None:
    run_fixture("preview")
    run_fixture("production-candidate")
    run_fixture("production")

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

    release_headers_broken = validate_release_headers(
        {"X-Robots-Tag": "noindex, nofollow, noarchive"}
    )
    if not release_headers_broken:
        raise SystemExit("ERREUR auto-test smoke HTTP: release.json cacheable non détecté.")

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

    marker_broken = validate_release_metadata(
        json.dumps(
            {
                "schema_version": 1,
                "source_sha": "b" * 40,
                "context": "preview",
            }
        ),
        "preview",
        SELF_TEST_RELEASE_SHA,
    )
    if not marker_broken:
        raise SystemExit("ERREUR auto-test smoke HTTP: mauvais SHA release non détecté.")

    valid_atomic_preview = "https://1234abcd12acde000111cdef--example-site.netlify.app"
    if validate_target_url(valid_atomic_preview, "preview"):
        raise SystemExit("ERREUR auto-test smoke HTTP: permalink atomique Netlify preview valide refusé.")
    if validate_target_url(valid_atomic_preview, "production-candidate"):
        raise SystemExit("ERREUR auto-test smoke HTTP: permalink atomique production-candidate valide refusé.")

    candidate_marker_errors = validate_release_metadata(
        json.dumps(
            {
                "schema_version": 1,
                "source_sha": SELF_TEST_RELEASE_SHA,
                "context": "production",
            }
        ),
        "production-candidate",
        SELF_TEST_RELEASE_SHA,
    )
    if candidate_marker_errors:
        raise SystemExit("ERREUR auto-test smoke HTTP: marqueur production-candidate valide refusé.")

    candidate_preview_marker = validate_release_metadata(
        json.dumps(
            {
                "schema_version": 1,
                "source_sha": SELF_TEST_RELEASE_SHA,
                "context": "preview",
            }
        ),
        "production-candidate",
        SELF_TEST_RELEASE_SHA,
    )
    if not candidate_preview_marker:
        raise SystemExit("ERREUR auto-test smoke HTTP: marqueur preview accepté comme production-candidate.")

    same_site_preview = "https://1111aaaabbbb--example-site.netlify.app"
    same_site_production = "https://2222ccccdddd--example-site.netlify.app"
    if validate_netlify_pair(same_site_preview, same_site_production):
        raise SystemExit("ERREUR auto-test smoke HTTP: paire Netlify même site valide refusée.")

    cross_site_errors = validate_netlify_pair(
        same_site_preview,
        "https://2222ccccdddd--other-site.netlify.app",
    )
    if not any("même site Netlify" in error for error in cross_site_errors):
        raise SystemExit("ERREUR auto-test smoke HTTP: paire Netlify inter-sites acceptée.")

    same_deploy_errors = validate_netlify_pair(
        same_site_preview,
        same_site_preview,
    )
    if not any("deploy-id distincts" in error for error in same_deploy_errors):
        raise SystemExit("ERREUR auto-test smoke HTTP: même deploy Netlify accepté deux fois.")

    invalid_targets = (
        ("http://example.netlify.app", "preview"),
        ("https://example.com", "preview"),
        ("https://example.netlify.app", "preview"),
        ("https://deploy-preview-449--example.netlify.app", "preview"),
        ("https://staging--example.netlify.app", "preview"),
        ("https://user:pass@example.netlify.app", "preview"),
        ("https://www.netlify.app:8443", "preview"),
        ("https://example.netlify.app/sub/path", "preview"),
        ("https://example.netlify.app/?draft=1", "preview"),
        ("https://example.netlify.app/#section", "preview"),
        ("https://example.netlify.app\n#summary-injection", "preview"),
        ("https://example.netlify.app\t", "preview"),
        ("https://" + ("a" * 2040) + ".netlify.app", "preview"),
        ("https://example.netlify.app", "production"),
        ("https://example.netlify.app", "production-candidate"),
        ("https://www.benoitcantin.com", "production-candidate"),
    )
    missed = [
        url
        for url, context in invalid_targets
        if not validate_target_url(url, context)
    ]
    if missed:
        raise SystemExit("ERREUR auto-test smoke HTTP: cibles dangereuses acceptées: " + ", ".join(missed))

    print(
        "OK auto-tests smoke HTTP: paire Netlify même site, permalink atomique preview/production-candidate, production, cibles autorisées, "
        "CSP complète, HSTS, en-têtes défensifs, noindex, no-store privé/release, "
        "robots privés et 404 techniques vérifiés."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke HTTP d'une preview ou production web SINJIRA.")
    parser.add_argument("url", nargs="?")
    parser.add_argument("--context", choices=("preview", "production-candidate", "production"), default="preview")
    parser.add_argument("--expected-sha", help="SHA source exact attendu dans /.well-known/release.json")
    parser.add_argument(
        "--same-netlify-site-as",
        help="Permalink preview atomique qui doit appartenir au même site Netlify que le production-candidate",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if not args.url:
        parser.error("URL requise hors --self-test")

    errors = validate_release(
        args.url,
        args.context,
        expected_sha=args.expected_sha,
        same_netlify_site_as=args.same_netlify_site_as,
    )
    if errors:
        print(f"ECHEC smoke HTTP: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        f"OK smoke HTTP {args.context}: navigation, pages IA, en-têtes, "
        "routes publiques, identité de release et 404 techniques conformes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
