#!/usr/bin/env python3
"""No-network regressions for SINJIRA's literature Playwright API boundary."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tests/e2e/isolated_supabase_api.py"
TEST_FILE = ROOT / "tests/e2e/test_literature_site.py"
spec = importlib.util.spec_from_file_location("isolated_supabase_api", MODULE)
assert spec is not None and spec.loader is not None
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class DummyRequest:
    def __init__(self, method, url):
        self.method, self.url = method, url


class DummyRoute:
    def __init__(self, method, url):
        self.request = DummyRequest(method, url)
        self.fulfilled = None

    def fulfill(self, **options):
        self.fulfilled = options

    def continue_(self):
        raise AssertionError("CI must not contact production")

    def fetch(self):
        raise AssertionError("CI must not fetch production")


class DummyWebSocket:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

    def connect_to_server(self):
        raise AssertionError("Production WebSocket egress forbidden")


class DummyContext:
    def __init__(self):
        self.pattern = None
        self.handler = None
        self.websockets = {}

    def route(self, pattern, handler):
        self.pattern, self.handler = pattern, handler

    def route_web_socket(self, pattern, handler):
        self.websockets[pattern] = handler


class ProductionEgressIsolationTests(unittest.TestCase):
    def test_public_novel_metadata_is_synthetic_and_cors_safe(self):
        code, content = api.isolated_api_response(
            "GET", api.PRODUCTION_SUPABASE_ORIGIN + api.NOVEL_TABLE
            + "?select=id,comments_enabled&slug=eq.synthetic")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(content), {
            "id": "ci-synthetic-novel", "comments_enabled": True
        })
        self.assertNotIn("apikey", content)

    def test_comment_rpc_is_empty_and_mutation_is_denied(self):
        url = api.PRODUCTION_SUPABASE_ORIGIN + api.NOVEL_COMMENTS_RPC
        self.assertEqual(api.isolated_api_response("POST", url), (200, "[]"))
        self.assertEqual(api.isolated_api_response("OPTIONS", url), (204, ""))
        for method, path in (
            ("PATCH", api.NOVEL_TABLE),
            ("DELETE", api.NOVEL_TABLE),
            ("POST", api.NOVEL_TABLE),
            ("GET", api.NOVEL_COMMENTS_RPC),
            ("POST", "/rest/v1/rpc/revoke_account"),
            ("GET", "/auth/v1/admin/users"),
            ("GET", "/storage/v1/object/sign/private/master.pdf"),
            ("GET", "/functions/v1/admin-console"),
        ):
            with self.subTest(method=method, path=path):
                code, payload = api.isolated_api_response(
                    method, api.PRODUCTION_SUPABASE_ORIGIN + path
                )
                self.assertEqual(code, 403)
                self.assertEqual(json.loads(payload)["code"], "CI_NETWORK_DENIED")

    def test_other_supabase_and_http_origins_are_rejected(self):
        for url in (
            "http://gpvivleexywljowcqkru.supabase.co/rest/v1/sinjira_novels",
            "https://fake.supabase.co/rest/v1/sinjira_novels",
            "https://gpvivleexywljowcqkru.supabase.co.evil.invalid/rest/v1/sinjira_novels",
        ):
            with self.subTest(url=url):
                self.assertEqual(api.isolated_api_response("GET", url)[0], 403)

    def test_playwright_route_never_leaks_to_network(self):
        context = DummyContext()
        api.install_isolated_supabase_api(context)
        self.assertEqual(
            context.pattern, api.PRODUCTION_SUPABASE_ORIGIN + "/**")
        self.assertEqual(len(context.websockets), 2)
        for protocol in ("wss://", "ws://"):
            pattern = api.PRODUCTION_SUPABASE_ORIGIN.replace(
                "https://", protocol, 1
            ) + "/**"
            socket = DummyWebSocket()
            context.websockets[pattern](socket)
            self.assertTrue(socket.closed)
        for method, path, expected in (
            ("GET", api.NOVEL_TABLE, 200),
            ("POST", api.NOVEL_COMMENTS_RPC, 200),
            ("POST", "/rest/v1/rpc/dangerous-write", 403),
        ):
            with self.subTest(path=path):
                dummy = DummyRoute(method, api.PRODUCTION_SUPABASE_ORIGIN + path)
                context.handler(dummy)
                self.assertEqual(dummy.fulfilled["status"], expected)
                self.assertEqual(
                    dummy.fulfilled["headers"]["access-control-allow-origin"], "*")
                self.assertEqual(
                    dummy.fulfilled["headers"]["cache-control"], "no-store")

    def test_all_literature_browser_contexts_apply_sandbox(self):
        text = TEST_FILE.read_text(encoding="utf-8", errors="strict")
        self.assertEqual(text.count("browser.new_context("), 5)
        self.assertEqual(text.count("install_isolated_supabase_api("), 5)
        self.assertEqual(text.count("service_workers="), 5)
        self.assertIn("from isolated_supabase_api import install_isolated_supabase_api", text)
        for context in ("private_context", "ctx", "no_js", "context", "mobile"):
            with self.subTest(context=context):
                self.assertIn(
                    "install_isolated_supabase_api(" + context + ")", text
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
