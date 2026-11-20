#!/usr/bin/env python3
"""Registre SINJIRA : aucun POST HTML natif ne doit transmettre les donnees privees.

Le formulaire est soumis exclusivement par le module JS vers Supabase Edge,
apres verification serveur du compte, du niveau MFA et du consentement.
Cette suite est volontairement hors reseau et n'accede a aucune donnee reelle.
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

NETLIFY_PATHS = ("/projets/sinjira/registre", "/projets/sinjira/registre/*")
VERCEL_PATHS = ("/projets/sinjira/registre", "/projets/sinjira/registre/(.*)")
FORM_ACTION = "/projets/sinjira/registre/"


class RegistryMarkup(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta_policies: list[str] = []
        self.forms: list[dict[str, str | None]] = []
        self.submit_buttons: list[dict[str, str | None]] = []
        self.scripts: list[dict[str, str | None]] = []
        self.inline_handlers: list[str] = []
        self.seen_form = False
        self.in_head = False
        self.meta_after_form = False
        self.meta_outside_head = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "head":
            self.in_head = True
        for k, value in attrs:
            if (k or "").lower().startswith("on"):
                self.inline_handlers.append(k)
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "content-security-policy":
            self.meta_policies.append(a.get("content") or "")
            self.meta_after_form |= self.seen_form
            self.meta_outside_head |= not self.in_head
        elif tag == "form" and "data-character-form" in a:
            self.forms.append(a)
            self.seen_form = True
        elif tag == "button" and a.get("type") == "submit":
            self.submit_buttons.append(a)
        elif tag == "script":
            self.scripts.append(a)

    def handle_endtag(self, tag: str) -> None:
        if tag == "head":
            self.in_head = False


def policy_directives(policy: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for declaration in policy.split(";"):
        tokens = declaration.split()
        if not tokens:
            continue
        if tokens[0] in result:
            raise ValueError("Directive CSP dupliquee : " + tokens[0])
        result[tokens[0]] = tokens[1:]
    return result


def policy_errors(policy: str) -> list[str]:
    try:
        directives = policy_directives(policy)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    if directives.get("form-action") != ["'none'"]:
        errors.append("form-action 'none' requis")
    scripts = directives.get("script-src", [])
    if "'self'" not in scripts or any(
        token in scripts for token in ("'unsafe-inline'", "'unsafe-eval'", "*", "data:")
    ):
        errors.append("script-src sans JavaScript inline requis")
    if directives.get("script-src-attr") != ["'none'"]:
        errors.append("gestionnaires inline interdits")
    if directives.get("object-src") != ["'none'"]:
        errors.append("objets embarques interdits")
    if directives.get("base-uri") != ["'self'"]:
        errors.append("base-uri strict requis")
    if directives.get("frame-ancestors") != ["'self'"]:
        errors.append("protection anti-framing requise")
    return errors


def markup_errors(html: str) -> list[str]:
    parsed = RegistryMarkup()
    parsed.feed(html)
    errors = []
    if (parsed.meta_policies != ["form-action 'none'"] or
            parsed.meta_after_form or parsed.meta_outside_head):
        errors.append("CSP locale form-action 'none' dans le head requise")
    if len(parsed.forms) != 1:
        errors.append("formulaire unique requis")
    else:
        form = parsed.forms[0]
        if form.get("autocomplete") != "off":
            errors.append("autocomplete off pour donnees privees requis")
        if form.get("action") != FORM_ACTION or form.get("method") != "post":
            errors.append("formulaire historique conserve, jamais GET")
    if len(parsed.submit_buttons) != 1 or "disabled" not in parsed.submit_buttons[0]:
        errors.append("soumission desactivee avant verification Auth obligatoire")
    if not any("sinjira-character-registry.js?" in (script.get("src") or "")
               for script in parsed.scripts):
        errors.append("module de soumission securisee requis")
    if parsed.inline_handlers:
        errors.append("attributs d'evenements inline interdits")
    return errors


def scoped_headers(items: list[dict], name: str, path: str) -> dict[str, str]:
    hits = [x for x in items if x.get(name) == path]
    if len(hits) != 1:
        raise AssertionError("Un seul bloc de protection attendu: " + path)
    if name == "for":
        return hits[0]["values"]
    return {item["key"]: item["value"] for item in hits[0]["headers"]}


class RegistryNativeSubmissionSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (ROOT / "projets/sinjira/registre/index.html").read_text("utf-8")
        cls.netlify = tomllib.loads((ROOT / "netlify.toml").read_text("utf-8"))
        cls.vercel = json.loads((ROOT / "vercel.json").read_text("utf-8"))

    def test_html_enforces_no_native_post_even_on_pages(self) -> None:
        self.assertEqual(markup_errors(self.html), [])

    def test_netlify_vercel_headers_match_and_deny_native_posts(self) -> None:
        active_policies = set()
        for netlify_path, vercel_path in zip(NETLIFY_PATHS, VERCEL_PATHS):
            with self.subTest(netlify=netlify_path, vercel=vercel_path):
                netlify = scoped_headers(self.netlify["headers"], "for", netlify_path)
                vercel = scoped_headers(self.vercel["headers"], "source", vercel_path)
                self.assertEqual(netlify["Content-Security-Policy"], vercel["Content-Security-Policy"])
                self.assertEqual(policy_errors(netlify["Content-Security-Policy"]), [])
                active_policies.add(netlify["Content-Security-Policy"])
                for value in (netlify, vercel):
                    self.assertIn("no-store", value["Cache-Control"])
                    self.assertEqual(value["Referrer-Policy"], "no-referrer")
                    self.assertIn("noindex", value["X-Robots-Tag"])
        self.assertEqual(len(active_policies), 1, "Pas de divergence CSP slash / sans slash")

    def test_standalone_netlify_artifact_emits_scoped_csp(self) -> None:
        generated = render_standalone_headers(deploy_context="production")
        for path in NETLIFY_PATHS:
            with self.subTest(path=path):
                parts = generated.split("\n" + path + "\n", 1)
                self.assertEqual(len(parts), 2)
                block = parts[1].split("\n\n", 1)[0]
                self.assertIn("form-action 'none'", block)
                self.assertIn("Content-Security-Policy:", block)
                self.assertIn("Cache-Control: private, no-store", block)

    def test_adversarial_regressions_are_caught(self) -> None:
        netlify = scoped_headers(self.netlify["headers"], "for", NETLIFY_PATHS[1])
        good_policy = netlify["Content-Security-Policy"]
        self.assertEqual(policy_errors(good_policy), [])
        for mutation in (
            good_policy.replace("form-action 'none'", "form-action 'self'"),
            good_policy.replace("form-action 'none'; ", ""),
            good_policy.replace("script-src 'self'", "script-src 'self' 'unsafe-inline'"),
            good_policy.replace("script-src-attr 'none'", "script-src-attr 'unsafe-inline'"),
            good_policy.replace("object-src 'none'", "object-src 'self'"),
        ):
            with self.subTest(mutated=mutation[:80]):
                self.assertNotEqual(mutation, good_policy)
                self.assertTrue(policy_errors(mutation))
        csp_meta = '<meta http-equiv="Content-Security-Policy" content="form-action \'none\'">'
        for mutation in (
            self.html.replace(csp_meta, ""),
            self.html.replace(csp_meta, "").replace("</head>", "</head>" + csp_meta, 1),
            self.html.replace('autocomplete="off" ', ""),
            self.html.replace('type="submit" disabled>', 'type="submit">'),
        ):
            with self.subTest(html_mutation=len(mutation)):
                self.assertNotEqual(mutation, self.html)
                self.assertTrue(markup_errors(mutation))


if __name__ == "__main__":
    unittest.main()
