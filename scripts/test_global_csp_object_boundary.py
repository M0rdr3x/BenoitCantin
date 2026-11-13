#!/usr/bin/env python3
"""Garde de sécurité CSP globale, sans accès réseau ni déploiement.

Les pages privées disposent déjà d'une politique stricte. Ce test verrouille
également les pages publiques pour interdire les éléments <object>/<embed>.
"""
from __future__ import annotations

import json
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


def directives(policy: str) -> dict[str, list[str]]:
    """Parser strict: une directive CSP ne peut pas être déclarée deux fois."""
    parsed: dict[str, list[str]] = {}
    for chunk in policy.split(";"):
        tokens = chunk.split()
        if not tokens:
            continue
        key, values = tokens[0].lower(), tokens[1:]
        if key in parsed:
            raise ValueError(f"directive CSP dupliquée: {key}")
        parsed[key] = values
    return parsed


def check_object_boundary(policy: str) -> bool:
    try:
        parsed = directives(policy)
    except ValueError:
        return False
    return parsed.get("object-src") == ["'none'"]


def production_csp() -> str:
    config = tomllib.loads((ROOT / "netlify.toml").read_text("utf-8"))
    matches = [rule["values"].get("Content-Security-Policy", "")
               for rule in config["headers"] if rule.get("for") == "/*"]
    if len(matches) != 1:
        raise ValueError("Règle CSP globale Netlify absente ou ambiguë")
    return matches[0]


def preview_csp() -> str:
    config = json.loads((ROOT / "vercel.json").read_text("utf-8"))
    matches = [header.get("value", "")
               for rule in config["headers"] if rule.get("source") == "/(.*)"
               for header in rule.get("headers", [])
               if header.get("key") == "Content-Security-Policy"]
    if len(matches) != 1:
        raise ValueError("Règle CSP globale Vercel absente ou ambiguë")
    return matches[0]


class GlobalCspObjectBoundary(unittest.TestCase):
    def test_real_global_hosts_are_strict_and_equivalent(self):
        production = production_csp()
        preview = preview_csp()
        self.assertEqual(production, preview)
        self.assertTrue(check_object_boundary(production))
        self.assertIn("frame-ancestors", directives(production))
        self.assertIn("base-uri", directives(production))

    def test_object_sources_cannot_reappear(self):
        base = production_csp()
        self.assertTrue(check_object_boundary(base))
        for bad in (
            base.replace("object-src 'none'", "object-src 'self'"),
            base.replace("object-src 'none'", "object-src *"),
            base.replace("object-src 'none'", "object-src https:"),
            base.replace("object-src 'none'", "object-src 'none' 'self'"),
            base.replace("object-src 'none'", ""),
            base + "; object-src 'none'",
            base + "; OBJECT-SRC 'self'",
        ):
            with self.subTest(policy=bad[-100:]):
                self.assertFalse(check_object_boundary(bad))

    def test_private_polices_remain_separate_and_stricter(self):
        netlify = tomllib.loads((ROOT / "netlify.toml").read_text("utf-8"))
        for entry in netlify["headers"]:
            if entry.get("for") in (
                "/compte/*", "/admin/*", "/Admin/*", "/app/*",
                "/administration.html", "/histoire-de-vie/*",
            ):
                self.assertTrue(check_object_boundary(
                    entry.get("values", {}).get("Content-Security-Policy", "")
                ), entry.get("for"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
