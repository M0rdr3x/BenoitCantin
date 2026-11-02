#!/usr/bin/env python3
"""Protect the production leak monitor's HTTP-only, fail-closed contract.

All fixtures are synthetic. No request is sent to a real website.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from urllib.error import HTTPError
from email.message import Message

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/validate_publication_live_boundary.py"
spec = importlib.util.spec_from_file_location("publication_boundary", SOURCE)
assert spec and spec.loader
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)

REQUIRED_ROUTES = (
    "/supabase/config.toml",
    "/tests/e2e/test_public_site.py",
    "/mobile-native/App.tsx",
    "/scripts/build_netlify_public.py",
    "/docs/README.md",
    "/.github/workflows/validate-site.yml",
    "/projets/projet-nova/official/versions/V322/V322_CURRENT_STATE.json",
    "/projets/projet-nova/official/versions/V316/README.md",
    "/projets/projet-nova/data/modele_comptabilite.csv",
    "/projets/projet-nova/CNAME_APRES_NAMECHEAP.txt",
    "/assets/icons/README.md",
)


class FakeResponse:
    status = 404

    def __init__(self, headers=None):
        self.headers = headers or {}
        self.read_called = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, *_):
        self.read_called = True
        raise AssertionError("The monitor must never download technical file contents")


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append((request, timeout))
        return self.response


class PublicationMonitorSecurityTests(unittest.TestCase):
    def test_exact_fenced_routes(self):
        self.assertEqual(boundary.BASE_URL, "https://www.benoitcantin.com")
        self.assertEqual(boundary.TECHNICAL_ROUTES, REQUIRED_ROUTES)
        self.assertEqual(len(REQUIRED_ROUTES), len(set(REQUIRED_ROUTES)))
        self.assertTrue(all(x.startswith("/") and not x.startswith("//") for x in REQUIRED_ROUTES))

    def test_status_404_required_for_every_route(self):
        expected = {"/": 200}
        expected.update({route: 404 for route in REQUIRED_ROUTES})
        self.assertEqual(boundary.validate_observations(expected, netlify=True), [])
        for route in REQUIRED_ROUTES:
            for code in (200, 301, 302, 403, 500, None):
                with self.subTest(route=route, code=code):
                    statuses = dict(expected)
                    if code is None:
                        statuses.pop(route)
                    else:
                        statuses[route] = code
                    problems = boundary.validate_observations(statuses, netlify=True)
                    self.assertTrue(any(route in p for p in problems))

    def test_ambiguous_hosting_and_broken_home_are_denied(self):
        expected = {"/": 200}
        expected.update({route: 404 for route in REQUIRED_ROUTES})
        self.assertTrue(boundary.validate_observations(expected, netlify=False))
        expected["/"] = 503
        self.assertTrue(boundary.validate_observations(expected, netlify=True))

    def test_http_requests_never_read_body(self):
        for route in REQUIRED_ROUTES:
            with self.subTest(route=route):
                response = FakeResponse()
                opener = FakeOpener(response)
                result = boundary.read_status(opener, route)
                self.assertEqual(result, (404, False))
                self.assertFalse(response.read_called)
                self.assertEqual(len(opener.requests), 1)
                request, timeout = opener.requests[0]
                self.assertEqual(request.full_url, boundary.BASE_URL + route)
                self.assertEqual(request.get_method(), "GET")
                self.assertEqual(timeout, boundary.TIMEOUT_SECONDS)

    def test_redirect_is_never_followed(self):
        handler = boundary.RefuseRedirect()
        self.assertIsNone(handler.redirect_request(None, None, 302, "redirect", {}, "https://evil.invalid/"))
        self.assertIsNone(handler.redirect_request(None, None, 301, "redirect", {}, "/"))

    def test_http_errors_retain_actual_status(self):
        headers = Message()
        headers["Server"] = "GitHub.com"
        error = HTTPError(boundary.BASE_URL + REQUIRED_ROUTES[0], 200, "response", headers, None)
        opener = FakeOpener(error)
        with self.assertRaises(HTTPError):
            # HTTPError 200 isn't a realistic HTTPError instance; use a
            # controlled network error below to exercise the real exception.
            raise error
        headers = Message()
        headers["x-nf-request-id"] = "synthetic"
        error = HTTPError(boundary.BASE_URL + REQUIRED_ROUTES[0], 403, "forbidden", headers, None)
        opener = FakeOpener(error)
        # An opener normally raises HTTPError, instead of returning it.
        def raise_http_error(*_args, **_kwargs):
            raise error
        opener.open = raise_http_error
        self.assertEqual(boundary.read_status(opener, REQUIRED_ROUTES[0]), (403, True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
