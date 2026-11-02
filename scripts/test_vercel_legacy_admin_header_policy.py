#!/usr/bin/env python3
"""Vérifie que seul le matcher d'en-têtes Vercel privés /Admin/ est exempté."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_site.py"
spec = importlib.util.spec_from_file_location("sinjira_validate_site", VALIDATOR)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

def base() -> dict:
    return {
        "headers": [{
            "source": "/Admin/(.*)",
            "headers": [
                {"key": "Cache-Control", "value": "no-store"},
                {"key": "Referrer-Policy", "value": "no-referrer"},
                {"key": "Pragma", "value": "no-cache"},
            ],
        }],
        "redirects": [],
    }

class LegacyAdminHeaderSecurityTests(unittest.TestCase):
    def test_actual_vercel_configuration_is_valid(self) -> None:
        text = (ROOT / "vercel.json").read_text("utf-8")
        self.assertFalse(validator.contains_unsafe_legacy_admin_link("vercel.json", text))

    def test_only_private_legacy_header_matcher_is_exempted(self) -> None:
        self.assertFalse(validator.contains_unsafe_legacy_admin_link("vercel.json", json.dumps(base())))
        self.assertTrue(validator.contains_unsafe_legacy_admin_link(
            "index.html", '<a href="/Admin/index.html">legacy</a>'
        ))
        self.assertFalse(validator.contains_unsafe_legacy_admin_link("index.html", '<a href="/admin/">admin</a>'))

    def test_legacy_redirect_and_rewrite_still_denied(self) -> None:
        for key in ("redirects", "rewrites"):
            doc = base()
            doc[key].append({"source": "/public", "destination": "/Admin/index.html"})
            with self.subTest(key=key):
                self.assertTrue(validator.contains_unsafe_legacy_admin_link(
                    "vercel.json", json.dumps(doc)
                ))

    def test_missing_private_headers_fails_closed(self) -> None:
        for item in ("Cache-Control", "Referrer-Policy", "Pragma"):
            doc = base()
            doc["headers"][0]["headers"] = [
                v for v in doc["headers"][0]["headers"] if v["key"] != item
            ]
            with self.subTest(missing=item):
                self.assertTrue(validator.contains_unsafe_legacy_admin_link(
                    "vercel.json", json.dumps(doc)
                ))

    def test_malformed_document_and_unprotected_rule_denied(self) -> None:
        self.assertTrue(validator.contains_unsafe_legacy_admin_link("vercel.json", "{invalid-json"))
        doc = base()
        doc["headers"][0]["headers"][0]["value"] = "public, max-age=3600"
        self.assertTrue(validator.contains_unsafe_legacy_admin_link("vercel.json", json.dumps(doc)))
        doc = base()
        doc["headers"][0]["source"] = "/Admin/hidden"
        self.assertTrue(validator.contains_unsafe_legacy_admin_link("vercel.json", json.dumps(doc)))

if __name__ == "__main__":
    unittest.main(verbosity=2)
