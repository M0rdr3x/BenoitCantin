#!/usr/bin/env python3
"""Garde CSP des routes privées : bloque JavaScript inline et dérives hébergeurs.

Aucun réseau, secret ou donnée utilisateur : validation de fichiers suivis par Git.
"""
from __future__ import annotations

import json
import sys
import tomllib
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_netlify_public import render_standalone_headers  # noqa: E402
from private_route_csp import harden_private_html, private_csp_output_errors  # noqa: E402

SCOPES = {
    "compte": ("/compte/*", "/compte/(.*)"),
    "admin": ("/admin/*", "/admin/(.*)"),
    "Admin": ("/Admin/*", "/Admin/(.*)"),
    "app": ("/app/*", "/app/(.*)"),
}
DISALLOWED_SCRIPT_TOKENS = {"'unsafe-inline'", "'unsafe-eval'", "data:", "blob:", "*"}
ATTR_URLS = {"href", "src", "action", "formaction", "xlink:href"}


class ScriptSurfaceAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "script" and not attributes.get("src"):
            self.errors.append("script intégré sans src")
        for key, value in attrs:
            key = (key or "").lower()
            if key.startswith("on"):
                self.errors.append(f"gestionnaire HTML inline: {key}")
            if key in ATTR_URLS and (value or "").lstrip().lower().startswith("javascript:"):
                self.errors.append(f"URL javascript: dans {key}")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def csp_errors(policy: str) -> list[str]:
    directives: dict[str, list[str]] = {}
    for part in policy.split(";"):
        tokens = part.strip().split()
        if not tokens:
            continue
        if tokens[0] in directives:
            return [f"directive CSP dupliquée: {tokens[0]}"]
        directives[tokens[0]] = tokens[1:]

    errors: list[str] = []
    scripts = directives.get("script-src", [])
    if not scripts or "'self'" not in scripts:
        errors.append("script-src doit cibler explicitement les scripts approuvés")
    for token in DISALLOWED_SCRIPT_TOKENS:
        if token in scripts:
            errors.append(f"source script interdite: {token}")
    if directives.get("script-src-attr") != ["'none'"]:
        errors.append("script-src-attr 'none' obligatoire")
    if directives.get("object-src") != ["'none'"]:
        errors.append("object-src 'none' obligatoire")
    if directives.get("base-uri") != ["'self'"]:
        errors.append("base-uri 'self' obligatoire")
    if directives.get("frame-ancestors") != ["'self'"]:
        errors.append("frame-ancestors 'self' obligatoire")
    if "upgrade-insecure-requests" not in directives:
        errors.append("upgrade-insecure-requests obligatoire")
    if any(v for v in directives.get("upgrade-insecure-requests", [])):
        errors.append("upgrade-insecure-requests ne prend aucun argument")
    return errors


class PrivateRoutesCspSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.netlify = tomllib.loads((ROOT / "netlify.toml").read_text("utf-8"))
        cls.vercel = json.loads((ROOT / "vercel.json").read_text("utf-8"))

    def test_csp_appliquee_aux_deux_hebergeurs(self) -> None:
        netlify_headers = {
            item["for"]: item.get("values", {})
            for item in self.netlify.get("headers", [])
        }
        vercel_headers = {
            item["source"]: {
                h["key"]: h["value"] for h in item.get("headers", [])
            }
            for item in self.vercel.get("headers", [])
        }
        for directory, (netlify_path, vercel_path) in SCOPES.items():
            with self.subTest(directory=directory):
                n = netlify_headers[netlify_path]["Content-Security-Policy"]
                v = vercel_headers[vercel_path]["Content-Security-Policy"]
                self.assertEqual(n, v, "CSP Netlify/Vercel doivent être identiques")
                self.assertEqual(csp_errors(n), [])
                self.assertIn("no-store", netlify_headers[netlify_path]["Cache-Control"])
                self.assertIn("no-store", vercel_headers[vercel_path]["Cache-Control"])

    def test_entetes_produits_conservent_les_csp_privees(self) -> None:
        headers = render_standalone_headers(deploy_context="production")
        for netlify_path, _ in SCOPES.values():
            with self.subTest(route=netlify_path):
                block = headers.split("\n" + netlify_path + "\n", 1)
                self.assertEqual(len(block), 2)
                scoped = block[1].split("\n\n", 1)[0]
                self.assertIn("script-src-attr 'none'", scoped)
                self.assertIn("object-src 'none'", scoped)
                self.assertNotIn("script-src 'self' 'unsafe-inline'", scoped)

    def test_toutes_pages_privees_sans_javascript_inline(self) -> None:
        for directory in SCOPES:
            paths = sorted((ROOT / directory).rglob("*.html"))
            self.assertTrue(paths, f"Aucune page HTML trouvée dans {directory}")
            for path in paths:
                with self.subTest(path=path.relative_to(ROOT).as_posix()):
                    parser = ScriptSurfaceAudit()
                    parser.feed(path.read_text("utf-8"))
                    parser.close()
                    self.assertEqual(parser.errors, [])

    def test_fallback_pages_statiques_ont_une_csp_meta_precoce(self) -> None:
        for directory in SCOPES:
            for page in sorted((ROOT / directory).rglob("*.html")):
                with self.subTest(page=page.relative_to(ROOT).as_posix()):
                    rel = page.relative_to(ROOT)
                    source = page.read_text("utf-8")
                    generated = harden_private_html(rel, source, self.netlify)
                    self.assertEqual(
                        private_csp_output_errors(rel, generated, self.netlify), []
                    )
                    self.assertIn('http-equiv="Content-Security-Policy"', generated)

    def test_fallback_refuse_toute_injection_html_inline(self) -> None:
        fixture = "<!doctype html><html><head></head><body><p>Sûr</p></body></html>"
        rel = Path("compte/test-synthetique.html")
        generated = harden_private_html(rel, fixture, self.netlify)
        self.assertEqual(private_csp_output_errors(rel, generated, self.netlify), [])
        hostile = [
            "<script>alert(1)</script>",
            '<img src="x" onerror="alert(1)">',
            '<a href="javascript:alert(1)">liens</a>',
        ]
        for snippet in hostile:
            with self.subTest(snippet=snippet):
                with self.assertRaises(ValueError):
                    harden_private_html(rel, fixture.replace("<p>Sûr</p>", snippet), self.netlify)
        self.assertTrue(private_csp_output_errors(
            rel, generated.replace('http-equiv="Content-Security-Policy"', 'http-equiv="X-Test"'),
            self.netlify,
        ))

    def test_module_admin_compte_est_externe_et_publie(self) -> None:
        html = (ROOT / "compte/index.html").read_text("utf-8")
        asset = ROOT / "assets/js/sinjira-account-admin-overview.js"
        self.assertTrue(asset.is_file())
        self.assertIn(
            '<script type="module" src="../assets/js/sinjira-account-admin-overview.js',
            html,
        )
        module = asset.read_text("utf-8")
        self.assertIn("from './sinjira-supabase.js'", module)
        self.assertIn("s.functions.invoke('admin-console'", module)
        self.assertIn("s.functions.invoke('admin-reports'", module)

    def test_aliases_admin_redirigent_via_un_script_externe(self) -> None:
        paths = [
            ROOT / "Admin/sinjira-analytics.html",
            ROOT / "Admin/sinjira/index.html",
            ROOT / "Admin/sinjira/licences.html",
            ROOT / "admin/index.html",
            ROOT / "admin/sinjira-analytics.html",
        ]
        redirect = ROOT / "assets/js/sinjira-admin-alias-redirect.js"
        source = redirect.read_text("utf-8")
        self.assertIn("document.currentScript", source)
        self.assertIn("target.search = window.location.search", source)
        self.assertIn("target.hash = window.location.hash", source)
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                html = path.read_text("utf-8")
                self.assertIn('src="/assets/js/sinjira-admin-alias-redirect.js"', html)
                self.assertIn("data-admin-redirect-target=\"/admin/", html)
                self.assertNotIn("<script>location.replace", html)

    def test_mutants_dangereux_sont_detectes(self) -> None:
        safe = ("default-src 'self'; script-src 'self'; script-src-attr 'none'; "
                "object-src 'none'; base-uri 'self'; frame-ancestors 'self'; "
                "upgrade-insecure-requests")
        self.assertEqual(csp_errors(safe), [])
        mutants = {
            "javascript inline réintroduit": safe.replace(
                "script-src 'self'", "script-src 'self' 'unsafe-inline'"),
            "URL data de scripts": safe.replace("script-src 'self'", "script-src 'self' data:"),
            "événements inline": safe.replace("script-src-attr 'none'", "script-src-attr 'unsafe-inline'"),
            "objets actifs": safe.replace("object-src 'none'", "object-src 'self'"),
            "base HTML hostile": safe.replace("base-uri 'self'", "base-uri *"),
        }
        for name, text in mutants.items():
            with self.subTest(name=name):
                self.assertTrue(csp_errors(text))
        html_mutants = [
            "<img src=x onerror=alert(1)>",
            "<a href='javascript:alert(1)'>Test</a>",
            "<script>alert(1)</script>",
            "<form onsubmit='return true'></form>",
        ]
        for text in html_mutants:
            with self.subTest(html=text):
                parser = ScriptSurfaceAudit()
                parser.feed(text)
                self.assertTrue(parser.errors)


if __name__ == "__main__":
    unittest.main()
