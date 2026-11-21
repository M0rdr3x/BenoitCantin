#!/usr/bin/env python3
"""Sonde passive des en-têtes HTTP publics et privés.

Aucune authentification, aucun corps de réponse lu et aucun changement serveur.
Les mutations sont testées sans réseau; --live est réservé au monitoring.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import re
import urllib.error
import urllib.request

BASE = "https://www.benoitcantin.com"
ROUTES = ("/", "/compte/", "/admin/")
PRIVATE_ROUTES = frozenset(("/compte/", "/admin/"))
TIMEOUT_SECONDS = 8
CRITICAL = frozenset((
    "strict-transport-security", "x-content-type-options",
    "content-security-policy", "x-frame-options", "referrer-policy",
    "cache-control", "x-robots-tag",
))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def normalize(pairs) -> tuple[dict[str, str], list[str]]:
    """Refuser les en-têtes de sécurité dupliqués, sans imprimer leurs valeurs."""
    values: dict[str, str] = {}
    errors: list[str] = []
    for key, value in pairs:
        name = key.strip().lower()
        if name in values and name in CRITICAL:
            errors.append("En-tête de sécurité dupliqué : " + name)
        values[name] = value.strip()
    return values, errors


def csp_directives(value: str) -> tuple[dict[str, tuple[str, ...]], list[str]]:
    result: dict[str, tuple[str, ...]] = {}
    errors: list[str] = []
    for part in value.split(";"):
        tokens = part.split()
        if not tokens:
            continue
        name = tokens[0].lower()
        if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
            errors.append("Directive CSP malformée")
            continue
        if name in result:
            errors.append("Directive CSP répétée : " + name)
        result[name] = tuple(tokens[1:])
    return result, errors


def validate(path: str, status: int | None,
             headers: Mapping[str, str]) -> list[str]:
    if path not in ROUTES:
        raise ValueError("Chemin hors liste autorisée")
    if status != 200:
        return [f"{path} : HTTP {status}, en-têtes non vérifiables"]
    failures = []
    hsts = headers.get("strict-transport-security", "")
    match = re.search(r"(?:^|;)\s*max-age\s*=\s*(\d+)(?:\s*;|$)", hsts, re.I)
    if not match or int(match.group(1)) < 31536000:
        failures.append("HSTS insuffisant")
    if headers.get("x-content-type-options", "").lower() != "nosniff":
        failures.append("MIME nosniff absent")
    if headers.get("x-frame-options", "").upper() not in ("DENY", "SAMEORIGIN"):
        failures.append("X-Frame-Options insuffisant")
    referrer = headers.get("referrer-policy", "").lower()
    if referrer not in ("no-referrer", "strict-origin",
                        "strict-origin-when-cross-origin", "same-origin"):
        failures.append("Referrer-Policy insuffisante")
    policy, csp_errors = csp_directives(headers.get("content-security-policy", ""))
    failures.extend(csp_errors)
    # Les directives mixtes comme "'self' https://tiers" élargissent les
    # privilèges. Un préfixe sûr ne rend pas une politique permissive sûre.
    if policy.get("default-src") != ("'self'",):
        failures.append("CSP default-src self exclusif requis")
    if policy.get("frame-ancestors") not in (("'self'",), ("'none'",)):
        failures.append("CSP frame-ancestors exclusif requis")
    if policy.get("base-uri") not in (("'self'",), ("'none'",)):
        failures.append("CSP base-uri exclusif requis")
    if "'unsafe-eval'" in policy.get("script-src", ()):
        failures.append("CSP unsafe-eval interdit")
    if any(t in ("*", "http:") for t in policy.get("default-src", ())):
        failures.append("CSP default-src trop permissif")
    if path in PRIVATE_ROUTES:
        cache = {t.strip().lower() for t in
                 headers.get("cache-control", "").split(",")}
        if "no-store" not in cache:
            failures.append("Cache-Control no-store privé absent")
        if referrer != "no-referrer":
            failures.append("Referrer-Policy no-referrer privé absent")
        robots = {t.strip().lower() for t in
                  headers.get("x-robots-tag", "").split(",")}
        if "noindex" not in robots:
            failures.append("X-Robots-Tag noindex absent")
        if policy.get("script-src-attr") != ("'none'",):
            failures.append("CSP script-src-attr none absent")
        if policy.get("object-src") != ("'none'",):
            failures.append("CSP object-src none absent")
        if "'unsafe-inline'" in policy.get("script-src", ()):
            failures.append("CSP privée unsafe-inline interdit")
    return [path + " : " + message for message in failures]


def probe(path: str) -> tuple[int, dict[str, str], list[str]]:
    assert path in ROUTES
    req = urllib.request.Request(
        BASE + path, method="GET",
        headers={"Accept": "text/html",
                 "Cache-Control": "no-cache",
                 "User-Agent": "Sinjira-Security-Headers-ReadOnly/1.0"},
    )
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(req, timeout=TIMEOUT_SECONDS) as response:
            headers, errors = normalize(response.headers.items())
            return response.status, headers, errors
    except urllib.error.HTTPError as error:
        try:
            headers, errors = normalize(error.headers.items())
            return error.code, headers, errors
        finally:
            error.close()


def self_test() -> None:
    public = {
        "strict-transport-security": "max-age=31536000",
        "x-content-type-options": "nosniff",
        "x-frame-options": "SAMEORIGIN",
        "referrer-policy": "strict-origin-when-cross-origin",
        "content-security-policy":
            "default-src 'self'; frame-ancestors 'self'; base-uri 'self';"
            " script-src 'self'; object-src 'self'",
    }
    private = {
        **public, "referrer-policy": "no-referrer",
        "cache-control": "private, no-store, max-age=0",
        "x-robots-tag": "noindex, nofollow, noarchive",
        "content-security-policy":
            "default-src 'self'; frame-ancestors 'self'; base-uri 'self';"
            " script-src 'self'; script-src-attr 'none'; object-src 'none'",
    }
    assert not validate("/", 200, public)
    assert not validate("/compte/", 200, private)
    assert not validate("/admin/", 200, private)
    trials = (
        ("/", public, "strict-transport-security", "max-age=20", "HSTS"),
        ("/", public, "x-content-type-options", "", "nosniff"),
        ("/", public, "x-frame-options", "", "X-Frame"),
        ("/", public, "content-security-policy", "", "default-src"),
        ("/", public, "content-security-policy", "default-src *", "default-src"),
        ("/", public, "content-security-policy",
         "default-src 'self' https://untrusted.invalid; frame-ancestors 'self'; base-uri 'self'",
         "default-src"),
        ("/", public, "content-security-policy",
         "default-src 'self'; frame-ancestors 'self' https://untrusted.invalid; base-uri 'self'",
         "frame-ancestors"),
        ("/", public, "content-security-policy",
         "default-src 'self'; frame-ancestors 'self'; base-uri 'self' https://untrusted.invalid",
         "base-uri"),
        ("/", public, "content-security-policy",
         public["content-security-policy"] + "; script-src 'self' 'unsafe-eval'", "unsafe-eval"),
        ("/compte/", private, "cache-control", "public, max-age=30", "no-store"),
        ("/compte/", private, "referrer-policy", "same-origin", "no-referrer"),
        ("/admin/", private, "x-robots-tag", "index", "noindex"),
        ("/admin/", private, "content-security-policy",
         private["content-security-policy"].replace("script-src-attr 'none'",
                                                    "script-src-attr 'unsafe-inline'"), "script-src-attr"),
        ("/compte/", private, "content-security-policy",
         private["content-security-policy"].replace("object-src 'none'",
                                                    "object-src 'self'"), "object-src"),
    )
    for path, original, name, unsafe, expected in trials:
        mutated = {**original, name: unsafe}
        assert any(expected in e for e in validate(path, 200, mutated)), (path, expected)
    for status in (None, 301, 302, 503):
        assert validate("/", status, public)
    normalized, errors = normalize([
        ("Content-Security-Policy", "default-src 'self'"),
        ("content-security-policy", "default-src *"),
    ])
    assert errors and normalized["content-security-policy"] == "default-src *"
    _policy, errors = csp_directives("default-src 'self'; default-src *")
    assert errors
    assert NoRedirect().redirect_request(None, None, 302, "", {},
                                         "https://untrusted.invalid") is None
    print("PASS : 3 routes, 14 mutations et refus des réponses ambiguës.")


def live() -> int:
    failures: list[str] = []
    for path in ROUTES:
        try:
            status, headers, errors = probe(path)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            failures.append(f"{path} : vérification indéterminée ({type(exc).__name__})")
            continue
        print(f"HTTP {status} {path}")
        failures.extend(path + " : " + e for e in errors)
        failures.extend(validate(path, status, headers))
    for failure in failures:
        print("FAIL : " + failure)
    if failures:
        return 1
    print("PASS : HSTS, CSP, no-store, noindex et en-têtes navigateur vérifiés.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
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
