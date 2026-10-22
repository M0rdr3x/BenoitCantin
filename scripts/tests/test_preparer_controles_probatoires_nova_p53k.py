#!/usr/bin/env python3
"""30 tests : robustesse de P53K, pas validation de pièces comptables."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import preparer_controles_probatoires_nova_p53k as m

def synthetique():
    return {
        "schema_version": "P53K-DOSSIER-1", "exercice": 2024, "devise": "CAD",
        "nature": "QUOTE_PART_MUNICIPALE", "montant_cad": "123.45",
        "payeur": {
            "code_organisme": "23027", "poste_comptable": "CRIIX00681",
            "montant_cad": "123.45", "date_ecriture": "2024-09-30",
            "identifiant_ecriture": "EXEMPLE-P001",
        },
        "beneficiaire": {
            "code_organisme": "66023", "poste_comptable": "CRIIX00408",
            "montant_cad": "123.45", "date_ecriture": "2024-09-30",
            "identifiant_ecriture": "EXEMPLE-B001",
        },
        "empreintes_pieces": {k: format(n, "064x") for n, k in enumerate(m.DOCUMENTS, 1)},
        "consolidation": {"meme_perimetre": "OUI", "deja_elimine": "NON"},
    }

class P53K(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.h, cls.regles = m.sources()
        cls.queue = m.file_dossiers(cls.rows, cls.h)
        cls.codes = {r["cod_geo"] for r in cls.rows}

    def evaluation(self, d):
        return m.evaluer_declaration(d, self.codes)[0]

    def test_01_population(self):
        self.assertEqual(len(self.rows), 1344)

    def test_02_priorites_plus_revision(self):
        self.assertEqual(len(self.queue), 26)

    def test_03_rangs(self):
        self.assertEqual([int(r["rang_p53h"]) for r in self.queue[:25]], list(range(1, 26)))

    def test_04_saint_valere_separe(self):
        self.assertEqual(self.queue[-1]["code_organisme"], "39135")
        self.assertEqual(self.queue[-1]["rang_p53h"], "")

    def test_05_enregistrement_sans_preuves(self):
        self.assertTrue(all(r["avis_independant_signe"] == "non" for r in self.queue))

    def test_06_pas_de_fausse_economie(self):
        self.assertTrue(all(r["economie_budgetaire_demontree_cad"] == "" for r in self.queue))

    def test_07_codes_unique(self):
        self.assertEqual(len({r["code_organisme"] for r in self.queue}), 26)

    def test_08_pas_de_sources_privees(self):
        self.assertNotIn("adresse_postale", json.dumps(self.queue, ensure_ascii=False))
        self.assertNotIn("facture_id", json.dumps(self.queue, ensure_ascii=False))

    def test_09_signe_ou_blanc_non_reinterprete(self):
        r = next(x for x in self.queue if x["code_organisme"] == "39135")
        self.assertEqual(r["quotes_parts_recues_cad"], "0")

    def test_10_dossier_valide_techniquement(self):
        self.assertEqual(self.evaluation(synthetique()), "CANDIDAT_ARITHMETIQUE_NON_CERTIFIE")

    def test_11_dossier_test_reste_non_certifie(self):
        b = m.bilan(self.queue, [self.evaluation(synthetique())], len(self.rows))
        self.assertEqual(b["appariements_certifies"], 0)
        self.assertIsNone(b["eliminations_certifiees_cad"])
        self.assertIsNone(b["economies_budgetaires_demontrees_cad"])

    def test_12_preuve_manquante(self):
        d = synthetique()
        d["empreintes_pieces"][m.DOCUMENTS[1]] = ""
        self.assertEqual(self.evaluation(d), "PIECES_NON_COMPLETES")

    def test_13_perimetre_inconnu(self):
        d = synthetique()
        d["consolidation"]["meme_perimetre"] = "INCONNU"
        self.assertEqual(self.evaluation(d), "PERIMETRE_OU_ELIMINATION_A_VERIFIER")

    def test_14_deja_elimine(self):
        d = synthetique()
        d["consolidation"]["deja_elimine"] = "OUI"
        self.assertEqual(self.evaluation(d), "ELIMINATION_DEJA_SIGNALEE_A_CONTROLER")

    def test_15_hors_perimetre(self):
        d = synthetique()
        d["consolidation"]["meme_perimetre"] = "NON"
        self.assertEqual(self.evaluation(d), "HORS_PERIMETRE_DE_CETTE_ELIMINATION")

    def test_16_montant_non_egal(self):
        d = synthetique()
        d["payeur"]["montant_cad"] = "123.44"
        with self.assertRaises(ValueError): self.evaluation(d)

    def test_17_montant_negatif(self):
        d = synthetique()
        d["montant_cad"] = "-123.45"
        with self.assertRaises(ValueError): self.evaluation(d)

    def test_18_montant_plus_de_deux_decimales(self):
        d = synthetique()
        d["montant_cad"] = "123.456"
        with self.assertRaises(ValueError): self.evaluation(d)

    def test_19_bad_year(self):
        d = synthetique()
        d["payeur"]["date_ecriture"] = "2026-09-30"
        with self.assertRaises(ValueError): self.evaluation(d)

    def test_20_bad_calendar_date(self):
        d = synthetique()
        d["payeur"]["date_ecriture"] = "2024-02-30"
        with self.assertRaises(ValueError): self.evaluation(d)

    def test_21_duplicate_actor_code(self):
        d = synthetique()
        d["payeur"]["code_organisme"] = d["beneficiaire"]["code_organisme"]
        with self.assertRaises(ValueError): self.evaluation(d)

    def test_22_unknown_actor_code(self):
        d = synthetique()
        d["beneficiaire"]["code_organisme"] = "INCONNU"
        with self.assertRaises(ValueError): self.evaluation(d)

    def test_23_wrong_account(self):
        d = synthetique()
        d["payeur"]["poste_comptable"] = "CRIIX00408"
        with self.assertRaises(ValueError): self.evaluation(d)

    def test_24_duplicate_entry_identifiers(self):
        d = synthetique()
        d["payeur"]["identifiant_ecriture"] = d["beneficiaire"]["identifiant_ecriture"]
        with self.assertRaises(ValueError): self.evaluation(d)

    def test_25_invalid_document_hash(self):
        d = synthetique()
        d["empreintes_pieces"][m.DOCUMENTS[1]] = "not-a-sha"
        with self.assertRaises(ValueError): self.evaluation(d)

    def test_26_identical_ledgers_hash(self):
        d = synthetique()
        d["empreintes_pieces"][m.DOCUMENTS[1]] = d["empreintes_pieces"][m.DOCUMENTS[0]]
        with self.assertRaises(ValueError): self.evaluation(d)

    def test_27_transfer_account_pairs(self):
        d = synthetique()
        d["nature"] = "TRANSFERT_MUNICIPAL"
        d["payeur"]["poste_comptable"] = "CRIIX00682"
        d["beneficiaire"]["poste_comptable"] = "CRIIX00409"
        self.assertEqual(self.evaluation(d), "CANDIDAT_ARITHMETIQUE_NON_CERTIFIE")

    def test_28_cli_result_and_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, c = Path(tmp)/"result.json", Path(tmp)/"queue.csv"
            self.assertEqual(m.main(["--rapport", str(p), "--export-registre", str(c)]), 0)
            r = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(r["dossiers_a_documenter"], 26)
            self.assertEqual(r["decision"], "NO_GO_AUTOMATIQUE")
            self.assertEqual(len(c.read_text(encoding="utf-8").splitlines()), 27)

    def test_29_cli_no_go_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"strict.json"
            self.assertEqual(m.main(["--exiger-certification", "--rapport", str(p)]), 3)
            self.assertEqual(json.loads(p.read_text(encoding="utf-8"))["F01_F20_validees"], 0)

    def test_30_cli_protected_output_and_untrusted_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/"existing.json"
            output.write_text("ne pas ecraser", encoding="utf-8")
            self.assertEqual(m.main(["--rapport", str(output)]), 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "ne pas ecraser")
            dossier = Path(tmp)/"test.json"
            dossier.write_text(json.dumps(synthetique()), encoding="utf-8")
            rapport = Path(tmp)/"synthese.json"
            self.assertEqual(m.main(["--dossier", str(dossier), "--rapport", str(rapport)]), 0)
            public = rapport.read_text(encoding="utf-8")
            self.assertIn("CANDIDAT_ARITHMETIQUE_NON_CERTIFIE", public)
            self.assertNotIn("EXEMPLE-P001", public)
            self.assertNotIn("123.45", public)

if __name__ == "__main__":
    unittest.main()
