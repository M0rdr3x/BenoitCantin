#!/usr/bin/env python3
"""Régressions de publication privée dans la configuration Netlify NOVA.

Aucun appel réseau ni donnée utilisateur : tests de mutations TOML synthétiques.
"""
from __future__ import annotations

import unittest

import build_netlify_public as builder


class NovaNestedNetlifySecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid = builder.NOVA_NESTED_NETLIFY_CONFIG.read_text(encoding="utf-8")

    def test_nested_config_always_uses_isolated_public_builder(self):
        self.assertEqual(builder.validate_nova_nested_netlify_config(), [])
        self.assertEqual(builder.validate_nova_nested_netlify_config(self.valid), [])

    def test_emitted_http_policies_keep_privacy_and_technical_deny_rules(self):
        headers = builder.render_standalone_headers(deploy_context="production")
        redirects = builder.render_standalone_redirects()
        for policy in (
            "X-Content-Type-Options: nosniff",
            "Strict-Transport-Security: max-age=31536000",
            "Content-Security-Policy:",
            "https://challenges.cloudflare.com",
            "frame-ancestors 'self'",
            "/compte/*",
            "/admin/*",
            "Cache-Control: private, no-store",
        ):
            with self.subTest(header=policy):
                self.assertIn(policy, headers)
        for rule in (
            "/supabase/* /404.html 404!",
            "/scripts/* /404.html 404!",
            "/docs/* /404.html 404!",
            "/.github/* /404.html 404!",
            "/tests/* /404.html 404!",
            "/mobile-native/* /404.html 404!",
            "/roman /projets/sinjira/index.html 301",
            "/registre /projets/sinjira/registre/index.html 301",
        ):
            with self.subTest(redirect=rule):
                self.assertIn(rule, redirects)

    def test_mutants_fail_closed(self):
        bad_variants = {
            "publish current folder": self.valid.replace('publish = "_site"', 'publish = "."'),
            "publish repository root": self.valid.replace('publish = "_site"', 'publish = "../../"'),
            "publish source data": self.valid.replace('publish = "_site"', 'publish = "projets/projet-nova"'),
            "no artifact builder": self.valid.replace(
                "python3 scripts/build_netlify_public.py --standalone-netlify", "echo build"),
            "no standalone redirects": self.valid.replace(" --standalone-netlify", ""),
            "nested base override": self.valid + '\n[build.environment]\nBASE = "."\n',
            "custom headers override": self.valid + '\n[[headers]]\nfor = "/*"\n',
            "custom redirects override": self.valid + '\n[[redirects]]\nfrom = "/secret"\n',
            "unreviewed plugin": self.valid + '\n[[plugins]]\npackage = "unreviewed"\n',
            "malformed toml": self.valid + '\n[build\n',
            "missing publish": self.valid.replace('  publish = "_site"\n', ""),
            "missing build": "# empty file\n",
        }
        for label, changed in bad_variants.items():
            with self.subTest(mutant=label):
                self.assertNotEqual(changed, self.valid)
                self.assertTrue(
                    builder.validate_nova_nested_netlify_config(changed),
                    f"La configuration Netlify dangereuse devrait être refusée : {label}",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
