"""P55P : comptes budgétaires publics et risque statique, non prévisionnel."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import calculer_exposition_prelevements_nova_p55p as m


class TestP55P(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.load()
        cls.source=m.p55o.read_json(m.P52C)

    def test_01_version(self):
        self.assertEqual(self.cfg["schema_version"],"P55P-1")

    def test_02_exercice(self):
        self.assertEqual(self.cfg["exercice_base"],"2026-2027")

    def test_03_sources(self):
        self.assertEqual(self.cfg["source_ref"],m.SOURCE)
        self.assertEqual(m.SOURCE["page_pdf_index_zero_discours"],29)

    def test_04_groups(self):
        self.assertEqual(len(m.GROUPS),3)
        self.assertEqual(self.cfg["classification_exposition"],
                         m.expected_groups())

    def test_05_revenue_existing(self):
        r=self.cfg["recettes"]
        self.assertEqual(r["impot_particuliers"],50800)
        self.assertEqual(r["impot_societes"],14527)
        self.assertEqual(r["recettes_impot_revenus_actuels"],65327)

    def test_06_exposure(self):
        r=self.cfg["recettes"]
        self.assertEqual(r["cotisations_sante"]+r["foncier_scolaire"]
                         +r["consommation_total"],40731)

    def test_07_other_revenue(self):
        r=self.cfg["recettes"]
        self.assertEqual(r["entreprises_gouvernement"]
                         +r["droits_permis_redevances"]
                         +r["revenus_divers"]+r["transferts_federaux"],60434)

    def test_08_total_revenues(self):
        self.assertEqual(65327+40731+60434,166492)

    def test_09_budget_cost(self):
        d=self.cfg["depenses_et_solde"]
        self.assertEqual(d["depenses_portefeuilles"]
                         +d["service_dette"],170757)

    def test_10_accounting_deficit(self):
        self.assertEqual(166492-170757-2000,-6265)

    def test_11_statutory_deficit(self):
        self.assertEqual(-6265-2347,-8612)

    def test_12_static_retained_revenue(self):
        self.assertEqual(166492-40731,125761)

    def test_13_static_accounting_deficit(self):
        self.assertEqual(125761-170757-2000,-46996)

    def test_14_static_statutory_deficit(self):
        self.assertEqual(-46996-2347,-49343)

    def test_15_static_only_never_forecast(self):
        self.assertFalse(self.cfg["exposition_sensibilite_statique"]["prevision_validee"])
        self.assertFalse(m.public_report(self.cfg)["scenario_est_prevision"])

    def test_16_no_fiscal_rate(self):
        self.assertIsNone(self.cfg["exposition_sensibilite_statique"][
            "taux_sur_revenus_necessaire_pct"])

    def test_17_no_tax_base(self):
        self.assertIsNone(self.cfg["exposition_sensibilite_statique"][
            "assiette_revenus_a_taxer_mcad"])

    def test_18_no_anti_haven_benefit(self):
        self.assertIsNone(self.cfg["exposition_sensibilite_statique"][
            "rendement_prelevement_anti_paradis_fiscaux_mcad"])

    def test_19_unresolved_questions(self):
        self.assertEqual(len(self.cfg["questions_a_resoudre"]),6)
        self.assertTrue(all(q["statut"]=="OUVERT"
                            for q in self.cfg["questions_a_resoudre"]))

    def test_20_guards(self):
        self.assertEqual(len(self.cfg["garde_fous"]),22)
        self.assertEqual(set(self.cfg["garde_fous"]),m.GUARDS)

    def test_21_status(self):
        report=m.public_report(self.cfg)
        self.assertEqual(report["decision"],m.NO_GO)
        self.assertEqual(report["score_maturite_estimatif_inchange_pct"],53)
        self.assertEqual(report["montants_financiers_nova_2027_2036_inconnus"],600)

    def test_22_no_savings(self):
        self.assertIsNone(m.public_report(self.cfg)["economies_certifiees_mcad"])
        self.assertFalse(m.public_report(self.cfg)[
            "benefice_net_pouvoir_achat_demontre"])

    def test_23_source_concordance(self):
        self.assertTrue(m.compare_source(self.source))
        self.assertTrue(m.verify(self.cfg))

    def test_24_tampered_income_rejected(self):
        cfg=copy.deepcopy(self.cfg)
        cfg["recettes"]["impot_particuliers"]+=1
        with self.assertRaises(ValueError):
            m.verify(cfg)

    def test_25_tampered_deficit_rejected(self):
        cfg=copy.deepcopy(self.cfg)
        cfg["depenses_et_solde"]["deficit_comptable"]+=1
        with self.assertRaises(ValueError):
            m.verify(cfg)

    def test_26_unsafe_scenario_rejected(self):
        cfg=copy.deepcopy(self.cfg)
        cfg["exposition_sensibilite_statique"][
            "taux_sur_revenus_necessaire_pct"]="15.0"
        with self.assertRaises(ValueError):
            m.verify(cfg)

    def test_27_changed_source_rejected(self):
        source=copy.deepcopy(self.source)
        next(x for x in source["lignes_revenus"]
             if x["id"]=="cotisations_sante")["valeur_mcad"]="9000"
        with self.assertRaises(ValueError):
            m.compare_source(source)

    def test_28_cli_default(self):
        self.assertEqual(m.main([]),0)
        self.assertEqual(m.main(["--exiger-faisabilite"]),3)

    def test_29_cli_public_outputs(self):
        with tempfile.TemporaryDirectory() as root:
            a=Path(root)/"report.json"
            b=Path(root)/"table.json"
            self.assertEqual(m.main(["--bilan-public",str(a),
                                     "--table-public",str(b)]),0)
            self.assertEqual(json.loads(a.read_text())[
                "recettes_actuelles_hors_impot_revenus_exposees_mcad"],40731)
            self.assertEqual(json.loads(b.read_text())[
                "contrefactuel_statique"]["solde_loi_si_aucUNE_ADAPTATION"],-49343)

    def test_30_cli_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"report.json"
            p.write_text("conserver")
            self.assertEqual(m.main(["--bilan-public",str(p)]),2)
            self.assertEqual(p.read_text(),"conserver")

    def test_31_cli_rejects_duplicate(self):
        with tempfile.TemporaryDirectory() as root:
            p=str(Path(root)/"report.json")
            self.assertEqual(m.main(["--bilan-public",p,"--table-public",p]),2)

    def test_32_output_no_claim_of_adoption(self):
        self.assertFalse(m.public_report(self.cfg)[
            "suppression_de_taxes_proposee_comme_actee"])
        self.assertTrue(m.public_table(self.cfg)["mesure_non_certifiante"])


if __name__=="__main__":
    unittest.main()
