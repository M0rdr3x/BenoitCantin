#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "validate_nova_publication_p50b.py"
spec = importlib.util.spec_from_file_location("nova_publication", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ValidationPublication(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pages = {
            "participer.html": 'contact volontaire, formulaires externes suspendus <a href="recrutement.html"></a><a href="confidentialite.html"></a>',
            "avis-legal.html": "Le site n’exploite actuellement pas de formulaire externe",
            "recrutement.html": "Aucun paiement; contact volontaire direct",
            "confidentialite.html": "Les formulaires publics externes sont suspendus.",
            "contact.html": '<a href="mailto:officiellenovaparti@gmail.com">Contact</a>',
        }
        for name, value in self.pages.items():
            (self.root / name).write_text(value, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def modify(self, name, value):
        (self.root / name).write_text(value, encoding="utf-8")

    def test_corpus_minimal_ok(self):
        self.assertEqual(module.validate(self.root), [])

    def test_formulaire_reintroduit(self):
        self.modify("contact.html", self.pages["contact.html"] + "<form action='/'>")
        self.assertTrue(module.validate(self.root))

    def test_fournisseur_externe_detecte(self):
        self.modify("participer.html", self.pages["participer.html"] + "https://formspree.io/f/test")
        self.assertTrue(module.validate(self.root))

    def test_declaration_perimee_detectee(self):
        self.modify("participer.html", self.pages["participer.html"] + " qui contient le formulaire intégré de soutien et de préadhésion")
        self.assertTrue(module.validate(self.root))

    def test_metadonnee_perimee_detectee(self):
        self.modify("participer.html", self.pages["participer.html"] + "Soutenir Projet Nova et accéder au formulaire de recrutement.")
        self.assertTrue(module.validate(self.root))

    def test_ancien_lien_pdf_detecte(self):
        self.modify("participer.html", self.pages["participer.html"] + "visionneuse.html?doc=formulaire-soutien")
        self.assertTrue(module.validate(self.root))

    def test_avis_legal_incomplet(self):
        self.modify("avis-legal.html", "Texte sans suspension")
        self.assertTrue(module.validate(self.root))

    def test_canal_contact_absent(self):
        self.modify("contact.html", "contact absent")
        self.assertTrue(module.validate(self.root))

    def test_page_absente(self):
        (self.root / "recrutement.html").unlink()
        self.assertTrue(module.validate(self.root))

    def test_suspension_page_participer_absente(self):
        self.modify("participer.html", self.pages["participer.html"].replace("suspendus", "ouverts"))
        self.assertTrue(module.validate(self.root))


if __name__ == "__main__":
    unittest.main(verbosity=2)
