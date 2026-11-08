#!/usr/bin/env python3
"""Bloquer les attributs événementiels JavaScript inline sur toutes les pages du site."""
from __future__ import annotations

import json
import tomllib
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIRS = ("compte", "admin", "Admin", "app", "histoire-de-vie", "projets")


class InlineEventAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.violations: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name.startswith("on"):
                self.violations.append(f"{tag}: attribut {name} interdit")
            if name in ("href", "src", "action", "formaction", "xlink:href"):
                if (value or "").strip().lower().startswith("javascript:"):
                    self.violations.append(f"{tag}: URL javascript interdite")
        if tag == "script":
            src = dict(attrs).get("src", "")
            if isinstance(src, str) and src.lower().startswith("data:"):
                self.violations.append("script data: interdit")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def html_files() -> list[Path]:
    pages = sorted(ROOT.glob("*.html"))
    for folder in PUBLIC_DIRS:
        root = ROOT / folder
        if root.is_dir():
            pages.extend(sorted(root.rglob("*.html")))
    return pages


def policy_directives(policy: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for item in policy.split(";"):
        tokens = item.strip().split()
        if not tokens:
            continue
        if tokens[0] in result:
            raise AssertionError(f"Directive CSP dupliquée : {tokens[0]}")
        result[tokens[0]] = tokens[1:]
    return result


class SiteWideInlineAttributeSecurity(unittest.TestCase):
    def test_csp_globale_identique_et_sans_attribut_inline(self) -> None:
        netlify = tomllib.loads((ROOT / "netlify.toml").read_text("utf-8"))
        vercel = json.loads((ROOT / "vercel.json").read_text("utf-8"))
        n = [x for x in netlify["headers"] if x["for"] == "/*"]
        v = [x for x in vercel["headers"] if x["source"] == "/(.*)"]
        self.assertEqual(len(n), 1)
        self.assertEqual(len(v), 1)
        n_policy = n[0]["values"]["Content-Security-Policy"]
        v_policy = next(x["value"] for x in v[0]["headers"] if x["key"] == "Content-Security-Policy")
        self.assertEqual(n_policy, v_policy)
        policy = policy_directives(n_policy)
        self.assertEqual(policy.get("script-src-attr"), ["'none'"])
        self.assertEqual(policy.get("object-src"), ["'self'"])
        self.assertIn("'self'", policy.get("script-src", []))

    def test_chaque_page_html_du_site_est_sans_evenement_inline(self) -> None:
        pages = html_files()
        self.assertGreaterEqual(len(pages), 170)
        for page in pages:
            with self.subTest(path=page.relative_to(ROOT).as_posix()):
                parser = InlineEventAudit()
                parser.feed(page.read_text("utf-8"))
                parser.close()
                self.assertEqual(parser.violations, [])

    def test_actions_publiques_externes_et_strictement_limitees(self) -> None:
        src = (ROOT / "assets/js/sinjira-static-actions.js").read_text("utf-8")
        self.assertIn("document.addEventListener('click'", src)
        self.assertIn("action === 'reload'", src)
        self.assertIn("action === 'print'", src)
        self.assertIn("button.disabled", src)
        for page, attribute in (
            ("offline.html", 'data-static-action="reload"'),
            ("projets/sinjira/jeux/fracture-du-reseau-mere/regles.html",
             'data-static-action="print"'),
        ):
            html = (ROOT / page).read_text("utf-8")
            self.assertIn(attribute, html)
            self.assertIn('src="/assets/js/sinjira-static-actions.js', html)
            self.assertNotIn("onclick=", html.lower())

    def test_mutants_de_securite_rejetes(self) -> None:
        for example in (
            '<button onclick="window.print()">Imprimer</button>',
            "<img onerror='alert(1)' src=x>",
            '<a href="javascript:alert(1)">Lien</a>',
            '<script src="data:text/javascript,alert(1)"></script>',
        ):
            with self.subTest(example=example):
                parser = InlineEventAudit()
                parser.feed(example)
                self.assertTrue(parser.violations)
        safe_policy = "default-src 'self'; script-src-attr 'none'; object-src 'self'"
        self.assertEqual(policy_directives(safe_policy)["script-src-attr"], ["'none'"])
        for unsafe in ("'unsafe-inline'", "'self'", "*"):
            with self.subTest(policy=unsafe):
                bad = safe_policy.replace("'none'", unsafe, 1)
                self.assertNotEqual(policy_directives(bad)["script-src-attr"], ["'none'"])


if __name__ == "__main__":
    unittest.main()
