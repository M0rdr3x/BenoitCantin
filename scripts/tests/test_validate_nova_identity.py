#!/usr/bin/env python3
"""Essais entièrement fictifs — aucune donnée ni identité personnelle."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nova_identity", HERE / "validate_nova_identity.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestIdentiteUnique(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "projet-nova"
        self.root.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_identite_actuelle_valide(self):
        (self.root / "index.html").write_text("Projet Nova — démarche citoyenne", encoding="utf-8")
        self.assertEqual(module.scan_site(self.root), [])

    def test_futur_parti_explicitement_projete(self):
        (self.root / "statuts.md").write_text("Parti Nova : dénomination future conditionnelle; non autorisé.", encoding="utf-8")
        self.assertEqual(module.scan_site(self.root), [])

    def test_acronyme_rejete(self):
        (self.root / "index.html").write_text("Ancien mouvement : SCQ", encoding="utf-8")
        self.assertEqual(len(module.scan_site(self.root)), 1)

    def test_acronyme_en_minuscule_rejete(self):
        (self.root / "meta.json").write_text('{"label":"scq"}', encoding="utf-8")
        self.assertEqual(len(module.scan_site(self.root)), 1)

    def test_denomination_longue_rejetee(self):
        (self.root / "intro.md").write_text("Souveraineté et Citoyenneté du Québec", encoding="utf-8")
        self.assertEqual(len(module.scan_site(self.root)), 1)

    def test_nom_de_fichier_rejete(self):
        (self.root / "SCQ_regles.md").write_text("Projet Nova", encoding="utf-8")
        self.assertEqual(len(module.scan_site(self.root)), 1)

    def test_historique_preserve(self):
        (self.root / "archives").mkdir()
        (self.root / "archives" / "ancien.md").write_text("SCQ — source historique", encoding="utf-8")
        self.assertEqual(module.scan_site(self.root), [])

    def test_fichiers_binaires_ignores(self):
        (self.root / "image.png").write_bytes(b"SCQ\x00\xff")
        self.assertEqual(module.scan_site(self.root), [])

    def test_absence_repertoire_refusee(self):
        self.assertTrue(module.scan_site(self.root / "inexistant"))

    def test_denomination_espacements_rejetee(self):
        (self.root / "a.txt").write_text("Souverainete  et  Citoyennete du Quebec", encoding="utf-8")
        self.assertEqual(len(module.scan_site(self.root)), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
