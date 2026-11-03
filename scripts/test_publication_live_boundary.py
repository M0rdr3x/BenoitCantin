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
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

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
    "/_config.yml",
    "/netlify.toml",
    "/vercel.json",
    "/supabase/production-migration-ledger.txt",
    "/supabase/functions/_shared/auth.ts",
    "/supabase/functions/send-game-report/index.ts",
    "/supabase/migrations/20260824013042_sinjira_v24_5_14_admin_privacy_safety_aal2_hardening.sql",
    "/scripts/validate_publication_live_boundary.py",
    "/scripts/test_publication_live_boundary.py",
    "/docs/SUPABASE_PRODUCTION_RUNBOOK.md",
    "/mobile-native/package.json",
    "/mobile-native/NativeProfileHub.tsx",
    "/.github/workflows/supabase-production-preflight.yml",
    "/projets/sinjira/codex/livre-i-delivery-contract.json",
    "/projets/projet-nova/README.md",
    "/projets/projet-nova/official/versions/V317/V317_CYBERSECURITE_RESILIENCE_CONTINUITE_STATE.json",
    "/projets/projet-nova/official/versions/V317/V317_REGISTRE_CHANGEMENTS_SECURITE_CONFIGURATIONS_MODELE.csv",
    "/projets/projet-nova/official/versions/V316/V316_FINAL_INDEPENDENT_VERIFICATION.json",
    "/ADMINISTRATION_FORMULAIRES.md",
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

    def test_independent_hosting_and_confidentiality_verdicts(self):
        statuses = {"/": 200}
        statuses.update({route: 404 for route in REQUIRED_ROUTES})
        self.assertEqual(boundary.validate_public_boundary(statuses), [])
        self.assertEqual(boundary.validate_target_hosting(statuses, netlify=True), [])
        self.assertTrue(boundary.validate_target_hosting(statuses, netlify=False))
        self.assertTrue(boundary.validate_observations(statuses, netlify=False))
        # Aucun défaut d'hébergement ne peut masquer une fuite technique.
        statuses[REQUIRED_ROUTES[-1]] = 200
        self.assertTrue(boundary.validate_public_boundary(statuses))
        self.assertTrue(boundary.validate_observations(statuses, netlify=True))
        statuses["/"] = 503
        self.assertTrue(boundary.validate_public_boundary(statuses))
        self.assertTrue(boundary.validate_target_hosting(statuses, netlify=True))

    def test_live_modes_are_bounded_and_do_not_hide_exposures(self):
        statuses = {"/": 200}
        statuses.update({route: 404 for route in REQUIRED_ROUTES})
        observed = []
        def fake_read(opener, route):
            observed.append(route)
            return (statuses[route], False)
        with patch.object(boundary, "build_opener", return_value=object()), \\
             patch.object(boundary, "read_status", side_effect=fake_read), \\
             redirect_stdout(StringIO()):
            self.assertEqual(boundary.live(mode="boundary"), 0)
            self.assertEqual(observed, ["/", *REQUIRED_ROUTES])
            observed.clear()
            self.assertEqual(boundary.live(mode="hosting"), 1)
            self.assertEqual(observed, ["/"])
            observed.clear()
            self.assertEqual(boundary.live(mode="strict"), 1)
            self.assertEqual(observed, ["/", *REQUIRED_ROUTES])
            observed.clear()
            statuses[REQUIRED_ROUTES[0]] = 200
            self.assertEqual(boundary.live(mode="boundary"), 1)
            self.assertEqual(observed, ["/", *REQUIRED_ROUTES])

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
