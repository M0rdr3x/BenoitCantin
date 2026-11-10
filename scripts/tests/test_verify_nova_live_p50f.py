#!/usr/bin/env python3
"""Onze essais hors ligne, sans échange avec le site public."""
import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1] / "verify_nova_live_p50f.py"
spec = importlib.util.spec_from_file_location("verify_nova_live_p50f", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class VerificationPublication(unittest.TestCase):
    def valid(self, name):
        return '<!DOCTYPE html><html lang="fr"><head><title>Projet Nova</title></head><body><p>' + '</p><p>'.join(m.PAGES[name]["required"]) + '</p></body></html>'

    def test_valid_pages(self):
        for name in m.PAGES:
            with self.subTest(name=name):
                self.assertEqual(m.evaluate(name, self.valid(name), 200, m.BASE_URL + name)["resultat"], "CONFORME_TECHNIQUE")

    def test_old_text_rejected(self):
        for name, rules in m.PAGES.items():
            for text in rules["forbidden"]:
                with self.subTest(name=name):
                    self.assertEqual(m.evaluate(name, self.valid(name) + text, 200, m.BASE_URL + name)["resultat"], "ECART")

    def test_offsite_host_rejected(self):
        self.assertEqual(m.evaluate("participer.html", self.valid("participer.html"), 200, "https://other.example/projets/projet-nova/participer.html")["resultat"], "ECART")

    def test_query_rejected(self):
        self.assertEqual(m.evaluate("participer.html", self.valid("participer.html"), 200, m.BASE_URL + "participer.html?foo=bar")["resultat"], "ECART")

    def test_non_html_rejected(self):
        self.assertEqual(m.evaluate("participer.html", self.valid("participer.html"), 200, m.BASE_URL + "participer.html", "text/plain")["resultat"], "ECART")

    def test_http_error(self):
        self.assertEqual(m.evaluate("participer.html", self.valid("participer.html"), 404, m.BASE_URL + "participer.html")["resultat"], "ECART")

    def test_active_form(self):
        self.assertEqual(m.evaluate("participer.html", self.valid("participer.html") + "<form>", 200, m.BASE_URL + "participer.html")["resultat"], "ECART")

    def test_entity_normalization(self):
        self.assertEqual(m.normalize("A&nbsp;&amp;B"), "A &B")

    def test_non_html_body(self):
        self.assertEqual(m.evaluate("participer.html", " ".join(m.PAGES["participer.html"]["required"]), 200, m.BASE_URL + "participer.html")["resultat"], "ECART")

    def test_unexpected_page(self):
        with self.assertRaises(ValueError):
            m.evaluate("other.html", "<html></html>", 200, m.BASE_URL + "other.html")

    def test_http_origin_denied(self):
        self.assertFalse(m.exact_public_url("http://www.benoitcantin.com/projets/projet-nova/participer.html", "participer.html"))
        self.assertTrue(m.exact_public_url(m.BASE_URL + "participer.html", "participer.html"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
