#!/usr/bin/env python3
"""Régressions de la frontière privée PWA sans réseau ni identifiants."""
from __future__ import annotations

import unittest

from scripts import validate_pwa


class PrivateCacheBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = (validate_pwa.ROOT / "sw.js").read_text(encoding="utf-8")

    def test_real_worker_has_private_network_only_boundary(self):
        self.assertEqual(validate_pwa.validate_private_cache_boundary(self.source), [])

    def test_missing_private_route_is_rejected(self):
        for route in (
            "/app", "/compte", "/Admin", "/admin", "/histoire-de-vie", "/supabase",
        ):
            with self.subTest(route=route):
                token = f"path.startsWith('{route}/')"
                self.assertIn(token, self.source)
                bad = self.source.replace(token, "false", 1)
                self.assertTrue(validate_pwa.validate_private_cache_boundary(bad))

    def test_missing_admin_route_is_rejected(self):
        for route in ("/administration", "/administration.html"):
            with self.subTest(route=route):
                token = f"path==='{route}'"
                self.assertIn(token, self.source)
                bad = self.source.replace(token, "false", 1)
                self.assertTrue(validate_pwa.validate_private_cache_boundary(bad))

    def test_private_dispatch_must_remain_direct_network_only(self):
        cases = {
            "branch removed": ("if(privatePath(path)){", "if(false){"),
            "not no-store": (
                "fetch(new Request(request,{cache:'no-store'}))",
                "fetch(new Request(request,{cache:'default'}))",
            ),
            "cache fallback": (
                "event.respondWith(fetch(new Request(request,{cache:'no-store'})));",
                "event.respondWith(fetch(new Request(request,{cache:'no-store'})).catch(()=>caches.match('/offline.html')));",
            ),
            "return removed": ("    return;\n  }\n  if(request.headers", "    ;\n  }\n  if(request.headers"),
        }
        for label, (old, new) in cases.items():
            with self.subTest(label=label):
                self.assertIn(old, self.source)
                bad = self.source.replace(old, new, 1)
                self.assertTrue(validate_pwa.validate_private_cache_boundary(bad))


if __name__ == "__main__":
    unittest.main()
