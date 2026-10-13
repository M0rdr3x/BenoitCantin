#!/usr/bin/env python3
"""Tests hors réseau du contrôle P50F."""
import importlib.util
from pathlib import Path
import unittest
import urllib.error

PATH = Path(__file__).resolve().parents[1] / "verify_nova_public_p50f.py"
spec = importlib.util.spec_from_file_location("nova_public_p50f", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def good(name):
    return "<html><title>" + " ".join(module.EXPECT[name]["required"]) + "</title><p>Projet Nova</p></html>"


def fetch_good(name):
    return good(name), 200, module.BASE + name, "text/html; charset=utf-8"


class TestPublication(unittest.TestCase):
    def test_quatre_pages_conformes(self):
        output = module.run(fetch_good)
        self.assertEqual(output["pages_conformes"], 4)
        self.assertEqual(output["statut"], "PUBLIÉ_ET_CONFORME")

    def test_ancienne_formulation(self):
        name = "participer.html"
        result = module.evaluate(name, good(name) + module.EXPECT[name]["forbidden"][0], 200, module.BASE + name)
        self.assertEqual(result["etat"], "NON_CONFORME")

    def test_absence_marqueur(self):
        result = module.evaluate("participer.html", "Projet Nova", 200, module.BASE + "participer.html")
        self.assertEqual(result["etat"], "NON_CONFORME")

    def test_ancienne_gouvernance(self):
        name = "code-conduite.html"
        result = module.evaluate(name, good(name) + module.EXPECT[name]["forbidden"][1], 200, module.BASE + name)
        self.assertEqual(result["etat"], "NON_CONFORME")

    def test_formulaire_reintroduit(self):
        name = "participer.html"
        result = module.evaluate(name, good(name) + "<form action='/'>", 200, module.BASE + name)
        self.assertEqual(result["etat"], "NON_CONFORME")

    def test_point_de_collecte_externe(self):
        name = "avis-legal.html"
        result = module.evaluate(name, good(name) + "https://formsubmit.co/test", 200, module.BASE + name)
        self.assertEqual(result["etat"], "NON_CONFORME")

    def test_mauvaise_origine(self):
        name = "recrutement.html"
        result = module.evaluate(name, good(name), 200, "https://example.org/recrutement.html")
        self.assertEqual(result["etat"], "NON_CONFORME")

    def test_page_non_html(self):
        name = "recrutement.html"
        result = module.evaluate(name, good(name), 200, module.BASE + name, "application/pdf")
        self.assertEqual(result["etat"], "NON_CONFORME")

    def test_http_404(self):
        name = "recrutement.html"
        result = module.evaluate(name, good(name), 404, module.BASE + name)
        self.assertEqual(result["etat"], "NON_CONFORME")

    def test_reseau_hors_service(self):
        def offline(name):
            raise urllib.error.URLError("hors réseau")
        result = module.run(offline)
        self.assertEqual(result["statut"], "NON_CONFORME_OU_NON_PUBLIE")
        self.assertEqual(sum(p["etat"] == "ERREUR_RESEAU" for p in result["pages"]), 4)

    def test_page_hors_perimetre(self):
        with self.assertRaises(ValueError):
            module.evaluate("prive.html", "", 200, module.BASE + "prive.html")


if __name__ == "__main__":
    unittest.main(verbosity=2)
