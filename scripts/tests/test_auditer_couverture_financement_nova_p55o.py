"""P55O : tests sur la couverture des hypothèses de financement non remplies."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import auditer_couverture_financement_nova_p55o as m


class TestP55O(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.analysis=m.load()
        cls.model=m.read_json(m.P52B)
        cls.evidence=m.read_json(m.P52A)
        cls.fiscal=m.read_json(m.P52C)
        cls.maturity=m.p55n.load()

    def test_01_schema(self):
        self.assertEqual(self.cfg["schema_version"],"P55O-1")

    def test_02_date(self):
        self.assertEqual(self.cfg["date_reference"],"2026-11-05")

    def test_03_sources(self):
        self.assertEqual(self.cfg["references"],["P52A","P52B","P52C","P55N"])

    def test_04_packages(self):
        self.assertEqual(len(self.cfg["plans_acquisition"]),10)

    def test_05_packages_match(self):
        self.assertEqual(
            [v["champ"] for v in self.cfg["plans_acquisition"]],list(m.CODES))

    def test_06_guards(self):
        self.assertEqual(len(m.GUARDS),14)
        self.assertTrue(all(self.cfg["protections"].values()))

    def test_07_blockers(self):
        self.assertEqual(len(m.BLOCKS),12)

    def test_08_regimes(self):
        self.assertEqual(self.cfg["perimetre"]["regimes"],list(m.p52b.REGIMES))

    def test_09_scenarios(self):
        self.assertEqual(
            self.cfg["perimetre"]["scenarios"],list(m.p52b.TRAJECTOIRES))

    def test_10_years(self):
        self.assertEqual(
            self.cfg["perimetre"]["exercices_debut"],list(m.p52b.EXERCICES))

    def test_11_six_scenarios(self):
        self.assertEqual(len(self.analysis["scenarios"]),6)

    def test_12_missing_revenue(self):
        self.assertEqual(sum(x["recettes_inconnues"]
                             for x in self.analysis["scenarios"]),240)

    def test_13_missing_spending(self):
        self.assertEqual(sum(x["depenses_inconnues"]
                             for x in self.analysis["scenarios"]),360)

    def test_14_missing_total(self):
        self.assertEqual(sum(self.analysis["frequence_par_champ"].values()),600)

    def test_15_each_field_missing(self):
        self.assertEqual(list(self.analysis["frequence_par_champ"].values()),
                         [60]*10)

    def test_16_each_year_missing(self):
        self.assertEqual(list(self.analysis["lacunes_par_exercice"].values()),
                         [60]*10)

    def test_17_anti_evasion_zero_not_revenue(self):
        self.assertEqual(self.analysis["anti_evasion_zeros_non_certifies"],60)

    def test_18_previsions_fiscal(self):
        self.assertEqual(m.TAX_SOURCE["impot_particuliers"],50800)
        self.assertEqual(m.TAX_SOURCE["impot_societes"],14527)
        self.assertEqual(50800+14527,65327)

    def test_19_no_fiscal_rate(self):
        self.assertFalse(
            m.public_report(self.cfg,self.analysis)["taux_de_deux_prelevements_determinables"])

    def test_20_no_financing(self):
        self.assertFalse(
            m.public_report(self.cfg,self.analysis)["financement_projet_demontre"])

    def test_21_no_purchasing_power_claim(self):
        self.assertFalse(
            m.public_report(self.cfg,self.analysis)["gains_pouvoir_achat_demontres"])

    def test_22_score_unchanged(self):
        self.assertEqual(
            m.public_report(self.cfg,self.analysis)["maturite_programme_estimative_pourcent"],53)
        self.assertFalse(
            m.public_report(self.cfg,self.analysis)["maturite_modifiee_par_ce_jalon"])

    def test_23_no_future_budget_calculable(self):
        self.assertEqual(
            m.public_report(self.cfg,self.analysis)["soldes_futurs_calculables"],0)

    def test_24_p52a_twenty_pending(self):
        self.assertEqual(
            m.public_report(self.cfg,self.analysis)["preuves_fiscales_p52a_ouvertes"],20)

    def test_25_no_go(self):
        self.assertEqual(m.public_report(self.cfg,self.analysis)["decision"],
                         m.NO_GO)

    def test_26_fake_number_rejected(self):
        model=copy.deepcopy(self.model)
        item=model["regimes"]["QUEBEC_DANS_CANADA"]["trajectoires"]["central"][0]
        item["recettes"]["impot_revenu_net"]="20"
        item["sources"]["impot_revenu_net"]="HYPOTHESE_SANS_PREUVE"
        with self.assertRaises(ValueError):
            m.inspect(self.cfg,model,self.evidence,self.fiscal,self.maturity)

    def test_27_missing_source_rejected(self):
        model=copy.deepcopy(self.model)
        item=model["regimes"]["QUEBEC_DANS_CANADA"]["trajectoires"]["central"][0]
        item["recettes"]["impot_revenu_net"]="20"
        with self.assertRaises(ValueError):
            m.inspect(self.cfg,model,self.evidence,self.fiscal,self.maturity)

    def test_28_fabricated_budget_rejected(self):
        source=copy.deepcopy(self.fiscal)
        item=next(x for x in source["lignes_revenus"]
                  if x["id"]=="impot_particuliers")
        item["valeur_mcad"]="99999"
        with self.assertRaises(ValueError):
            m.inspect(self.cfg,self.model,self.evidence,source,self.maturity)

    def test_29_safeguard_disabled_rejected(self):
        cfg=copy.deepcopy(self.cfg)
        cfg["protections"]["pas_de_taux_ni_economies_certifies"]=False
        with self.assertRaises(ValueError):
            m.validate_catalogue(cfg)

    def test_30_fake_p55n_score_rejected(self):
        score=copy.deepcopy(self.maturity)
        score["score_estimatif"]=99
        with self.assertRaises(ValueError):
            m.inspect(self.cfg,self.model,self.evidence,self.fiscal,score)

    def test_31_null_to_zero_without_proof_rejected(self):
        model=copy.deepcopy(self.model)
        item=model["regimes"]["QUEBEC_SOUVERAIN"]["trajectoires"]["stress"][0]
        item["depenses"]["couts_transition_nets"]="0"
        item["sources"]["couts_transition_nets"]="HYPOTHESE_SANS_PROVENANCE"
        with self.assertRaises(ValueError):
            m.inspect(self.cfg,model,self.evidence,self.fiscal,self.maturity)

    def test_32_cli_default(self):
        self.assertEqual(m.main([]),0)

    def test_33_cli_no_financing(self):
        self.assertEqual(m.main(["--exiger-financement-demontre"]),3)

    def test_34_cli_public_outputs(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"report.json"
            q=Path(root)/"table.json"
            self.assertEqual(m.main(["--bilan-public",str(p),
                                     "--table-public",str(q)]),0)
            self.assertEqual(json.loads(p.read_text())["total_montants_inconnus"],600)
            self.assertEqual(len(json.loads(q.read_text())["plans_acquisition"]),10)

    def test_35_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"report.json"
            p.write_text("conserver")
            self.assertEqual(m.main(["--bilan-public",str(p)]),2)
            self.assertEqual(p.read_text(),"conserver")

    def test_36_cli_no_duplicate(self):
        with tempfile.TemporaryDirectory() as root:
            p=str(Path(root)/"report.json")
            self.assertEqual(m.main(["--bilan-public",p,
                                     "--table-public",p]),2)


if __name__=="__main__":
    unittest.main()
