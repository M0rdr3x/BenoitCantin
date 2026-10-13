#!/usr/bin/env python3
"""P50F — scenarios de verification sans requete reseau."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "verify_nova_live_p50f.py"
spec = importlib.util.spec_from_file_location("nova_live_p50f", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PublicationP50F(unittest.TestCase):
    def good(self, name):
        return "<html><title>Projet Nova</title><main>" + "<p>".join(module.EXPECTED[name]["required"]) + "</main></html>"

    def test_quatre_pages_correctes(self):
        for name in module.EXPECTED:
            with self.subTest(name=name):
                self.assertEqual(module.evaluate(name, self.good(name), 200, module.BASE + name)["resultat"], "CONFORME")

    def test_ancien_texte_refuse(self):
        for name, spec in module.EXPECTED.items():
            for phrase in spec["forbidden"]:
                with self.subTest(name=name, phrase=phrase):
                    body = self.good(name) + phrase
                    self.assertEqual(module.evaluate(name, body, 200, module.BASE + name)["resultat"], "NON_CONFORME")

    def test_absence_mention_refusee(self):
        self.assertEqual(module.evaluate("participer.html", "<p>Nova</p>", 200, module.BASE + "participer.html")["resultat"], "NON_CONFORME")

    def test_http_404_refuse(self):
        name = "recrutement.html"
        self.assertEqual(module.evaluate(name, self.good(name), 404, module.BASE + name)["resultat"], "NON_CONFORME")

    def test_redirection_domaine_tiers_refusee(self):
        name = "recrutement.html"
        self.assertEqual(module.evaluate(name, self.good(name), 200, "https://example.org/recrutement.html")["resultat"], "NON_CONFORME")

    def test_redirection_autre_chemin_refusee(self):
        name = "recrutement.html"
        self.assertEqual(module.evaluate(name, self.good(name), 200, module.BASE + "participer.html")["resultat"], "NON_CONFORME")

    def test_page_avec_formulaire_refusee(self):
        name = "participer.html"
        self.assertEqual(module.evaluate(name, self.good(name) + "<form action='/'>", 200, module.BASE + name)["resultat"], "NON_CONFORME")

    def test_fournisseur_externe_refuse(self):
        name = "participer.html"
        self.assertEqual(module.evaluate(name, self.good(name) + "https://formsubmit.co/test", 200, module.BASE + name)["resultat"], "NON_CONFORME")

    def test_entities_html_acceptees(self):
        self.assertEqual(module.normalized("A&nbsp;&amp;B"), "A &B")

    def test_page_non_autorisee_refusee(self):
        with self.assertRaises(ValueError):
            module.evaluate("autre.html", "test", 200, module.BASE + "autre.html")

    def test_succes_simule_sur_les_quatre_pages(self):
        def fake_read(url):
            name = url.rsplit("/", 1)[-1]
            return self.good(name), 200, url
        with patch.object(module, "read_public", side_effect=fake_read):
            result = module.run()
            self.assertEqual(result["statut"], "PUBLIÉ_ET_CONFORME")
            self.assertEqual(result["pages_conformes"], 4)

    def test_erreur_reseau_bloquante(self):
        with patch.object(module, "read_public", side_effect=TimeoutError("réseau simulé")):
            result = module.run()
            self.assertEqual(result["statut"], "NON_PRET_PUBLICATION")
            self.assertEqual(result["pages_conformes"], 0)
            self.assertTrue(all(x["resultat"] == "ERREUR_RESEAU" for x in result["pages"]))

if __name__ == "__main__":
    unittest.main(verbosity=2)
