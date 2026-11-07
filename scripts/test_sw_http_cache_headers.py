#!/usr/bin/env python3
"""Test statique des en-têtes anti-cache du Service Worker; aucun réseau."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("public_builder_http", ROOT / "scripts/build_netlify_public.py")
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class ServiceWorkerCacheHeaders(unittest.TestCase):
    def test_exact_no_store_required(self):
        for invalid in (None, {}, {"Cache-Control": "max-age=0"},
                        {"Cache-Control": "no-cache"},
                        {"Cache-Control": "public, no-store"},
                        {"Cache-Control": "no-store, max-age=0"}):
            with self.subTest(value=invalid):
                self.assertTrue(builder.validate_sw_http_cache_header(invalid, "test"))
        self.assertEqual(
            builder.validate_sw_http_cache_header({"Cache-Control": "no-store"}, "test"),
            [],
        )

    def test_netlify_and_standalone_artifact_serve_sw_without_cache(self):
        config = tomllib.loads((ROOT / "netlify.toml").read_text(encoding="utf-8"))
        routes = [item for item in config.get("headers", []) if item.get("for") == "/sw.js"]
        self.assertEqual(len(routes), 1)
        self.assertEqual(builder.validate_sw_http_cache_header(routes[0]["values"], "Netlify"), [])
        self.assertEqual(builder.validate_netlify_config(), [])
        for context in ("production", "deploy-preview"):
            rendered = builder.render_standalone_headers(context)
            self.assertIn("/sw.js\n  Cache-Control: no-store\n", rendered)

    def test_vercel_preview_sw_must_not_be_cached(self):
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        routes = [item for item in config.get("headers", []) if item.get("source") == "/sw.js"]
        self.assertEqual(len(routes), 1)
        values = {str(item.get("key")): str(item.get("value")) for item in routes[0]["headers"]}
        self.assertEqual(builder.validate_sw_http_cache_header(values, "Vercel"), [])
        self.assertEqual(builder.validate_vercel_config(), [])


if __name__ == "__main__":
    unittest.main()
