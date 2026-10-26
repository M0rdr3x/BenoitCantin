#!/usr/bin/env python3
"""Tests stricts du triage P53J, aucun test ne certifie un flux."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auditer_appariements_municipaux_nova_p53j as m

class VerificationsP53J(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = m.lire_snapshot()
        cls.i = m.lire_json(m.P53I)
        cls.h = m.lire_json(m.P53H)
        cls.bilan, cls.journal = m.verifier_et_construire(cls.rows, cls.i, cls.h)

    def test_01_volume_1344(self):
        self.assertEqual(self.bilan["organismes_parcourus"], 1344)

    def test_02_priorites_25(self):
        self.assertEqual(self.bilan["priorites_p53h_controlees"], 25)
        self.assertEqual(sum(bool(x["rang_priorite_p53h"]) for x in self.journal), 25)

    def test_03_new_organisme(self):
        self.assertEqual([x["code_organisme_declarant"] for x in self.journal
                          if x["ajout_revision_p53i"] == "oui"], ["39135"])

    def test_04_source_signature(self):
        self.assertEqual(hashlib.sha256(m.CSV_SOURCE.read_bytes()).hexdigest(), m.ATTENDU_SHA)

    def test_05_retains_missing_not_zero(self):
        self.assertGreater(self.bilan["champs_absents_par_code"]["CRIIX00408"], 0)
        self.assertTrue(any(x["quotes_parts_recues_cad"] == "" for x in self.journal))

    def test_06_preserves_signs(self):
        self.assertTrue(any(int(x["transferts_recus_cad"]) < 0
                            for x in self.journal if x["transferts_recus_cad"]))

    def test_07_no_fake_transaction(self):
        self.assertTrue(all(not x["identifiant_ecriture_payeur"] and
                            not x["identifiant_ecriture_beneficiaire"]
                            for x in self.journal))

    def test_08_no_fake_payer(self):
        self.assertTrue(all(not x["code_payeur_documente"] and
                            not x["code_beneficiaire_transaction_documente"]
                            for x in self.journal))

    def test_09_no_elimination(self):
        self.assertTrue(all(x["montant_eliminable_certifie_cad"] == ""
                            for x in self.journal))
        self.assertIsNone(self.bilan["eliminations_comptables_certifiees_cad"])

    def test_10_no_savings_or_nova_rate(self):
        self.assertIsNone(self.bilan["economies_reelles_demontrees_cad"])
        self.assertIsNone(self.bilan["revenu_taxe_Nova_adopte_cad"])

    def test_11_no_go(self):
        self.assertEqual(self.bilan["decision"], "NO_GO_AUTOMATIQUE")

    def test_12_no_expertise_signed(self):
        self.assertFalse(self.bilan["avis_independant_signe"])

    def test_13_mutation_missing_organism(self):
        with self.assertRaises(ValueError):
            m.verifier_et_construire(self.rows[:-1], self.i, self.h)

    def test_14_mutation_duplicated_organism(self):
        rows = copy.deepcopy(self.rows)
        rows[-1]["cod_geo"] = rows[0]["cod_geo"]
        with self.assertRaises(ValueError):
            m.verifier_et_construire(rows, self.i, self.h)

    def test_15_mutation_p53i_evidence(self):
        i = copy.deepcopy(self.i)
        i["etat"]["appariements_transactionnels_confirmes"] = 1
        with self.assertRaises(ValueError):
            m.verifier_et_construire(self.rows, i, self.h)

    def test_16_mutation_p53h_priority(self):
        h = copy.deepcopy(self.h)
        h["priorites_relecture"][0]["flux_candidats_signes_cad"] = "0"
        with self.assertRaises(ValueError):
            m.verifier_et_construire(self.rows, self.i, h)

    def test_17_mutation_p53i_sha(self):
        i = copy.deepcopy(self.i)
        i["archives_derivées"]["nouvelle_selection_sha256"] = "false"
        with self.assertRaises(ValueError):
            m.verifier_et_construire(self.rows, i, self.h)

    def test_18_refuses_tampered_source(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "snapshot.csv"
            p.write_bytes(m.CSV_SOURCE.read_bytes() + b"x")
            with self.assertRaises(ValueError):
                m.lire_snapshot(p)

    def test_19_cli_writes_aggregates_and_journal(self):
        with tempfile.TemporaryDirectory() as t:
            result, journal = Path(t) / "result.json", Path(t) / "journal.csv"
            self.assertEqual(m.main(["--rapport", str(result),
                                     "--export-csv", str(journal)]), 0)
            self.assertEqual(json.loads(result.read_text(encoding="utf-8"))["organismes_parcourus"], 1344)
            with journal.open(encoding="utf-8", newline="") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 1344)

    def test_20_cli_refuses_certification(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(m.main(["--exiger-appariements",
                                     "--rapport", str(Path(t) / "refus.json")]), 3)

    def test_21_no_output_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "existant.json"
            p.write_text("important", encoding="utf-8")
            self.assertEqual(m.main(["--rapport", str(p)]), 2)
            self.assertEqual(p.read_text(encoding="utf-8"), "important")

    def test_22_no_budget_2026_conflation(self):
        self.assertEqual(self.bilan["exercice"], 2024)
        self.assertEqual(self.bilan["base_source"],
                         "P53I_DERIVEE_2024_NON_ORIGINAL_INTEGRAL")

if __name__ == "__main__":
    unittest.main()
