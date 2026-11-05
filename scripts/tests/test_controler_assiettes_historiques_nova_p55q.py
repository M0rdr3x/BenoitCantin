"""P55Q : source officielle historique, deux millésimes, aucune base fiscale fusionnée."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import controler_assiettes_historiques_nova_p55q as m


class TestP55Q(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=m.load()

    def test_01_schema(self):
        self.assertEqual(self.doc["schema_version"],"P55Q-1")

    def test_02_person_year(self):
        self.assertEqual(self.doc["sources"]["personnes"]["annee_imposition"],2023)

    def test_03_corp_year(self):
        self.assertEqual(self.doc["sources"]["societes"]["annee_imposition"],2021)

    def test_04_sources_distinct(self):
        self.assertNotEqual(self.doc["sources"]["personnes"]["annee_imposition"],
                            self.doc["sources"]["societes"]["annee_imposition"])

    def test_05_person_taxable_income(self):
        self.assertEqual(self.doc["personnes_2023"]["revenu_imposable_mcad"],372261)

    def test_06_person_total_income(self):
        self.assertEqual(self.doc["personnes_2023"]["revenu_total_mcad"],427915)

    def test_07_person_net_income(self):
        self.assertEqual(self.doc["personnes_2023"]["revenu_net_mcad"],387023)

    def test_08_person_filers(self):
        self.assertEqual(self.doc["personnes_2023"]["contribuables_declares"],7220140)

    def test_09_person_tax_payable(self):
        self.assertEqual(self.doc["personnes_2023"]["impot_a_payer_mcad"],40790)

    def test_10_person_refundable_credits(self):
        self.assertEqual(self.doc["personnes_2023"]["credits_remboursables_mcad"],9305)

    def test_11_person_net_after_refundable(self):
        self.assertEqual(self.doc["personnes_2023"]["impot_moins_credits_remboursables_mcad"],31485)

    def test_12_person_rounding_one_million(self):
        p=self.doc["personnes_2023"]
        self.assertEqual(p["revenu_net_mcad"]-p["deductions_revenu_imposable_mcad"],
                         p["revenu_imposable_mcad"]+1)

    def test_13_corp_quebec_taxable(self):
        self.assertEqual(self.doc["societes_2021"]["revenu_imposable_au_quebec_mcad"],95784)

    def test_14_corp_world_not_quebec(self):
        c=self.doc["societes_2021"]
        self.assertGreater(c["revenu_imposable_mondial_mcad"],
                           c["revenu_imposable_au_quebec_mcad"])

    def test_15_corp_filers(self):
        self.assertEqual(self.doc["societes_2021"]["declarations_revenues"],564599)

    def test_16_corp_untaxed(self):
        self.assertEqual(self.doc["societes_2021"]["societe_non_imposees_nombre"],322020)

    def test_17_corp_tax(self):
        self.assertEqual(self.doc["societes_2021"]["impot_revenu_quebec_mcad"],10000)

    def test_18_corp_fss_not_tax(self):
        self.assertEqual(self.doc["societes_2021"]["cotisations_fonds_services_sante_mcad"],5327)

    def test_19_corp_rounding_one_million(self):
        c=self.doc["societes_2021"]
        self.assertEqual(c["total_impots_cotisations_mcad"]-c["credits_impot_mcad"]+1,
                         c["impot_cotisations_nets_credits_impot_mcad"])

    def test_20_no_composite_tax_base(self):
        self.assertIsNone(self.doc["comparaison_sans_addition"]["assiette_combinee_harmonisee_mcad"])

    def test_21_no_proposed_tax_rate(self):
        self.assertIsNone(self.doc["comparaison_sans_addition"]["taux_pour_financer_les_deux_prelevements_pct"])

    def test_22_thirty_guards(self):
        self.assertEqual(len(self.doc["protections"]),30)
        self.assertTrue(all(self.doc["protections"].values()))

    def test_23_ten_open_evidence_tasks(self):
        self.assertEqual(len(self.doc["pistes_de_travail"]),10)
        self.assertTrue(all(x["statut"]=="OUVERT" for x in self.doc["pistes_de_travail"]))

    def test_24_p55n_score_unchanged(self):
        self.assertEqual(m.public_report(self.doc)["score_estime_inchange_pct"],53)

    def test_25_p52b_unknown_unchanged(self):
        self.assertEqual(m.public_report(self.doc)["inconnues_financieres_decennales"],600)

    def test_26_no_go(self):
        self.assertEqual(m.public_report(self.doc)["decision"],m.NO_GO)

    def test_27_change_one_dollar_rejected(self):
        data=copy.deepcopy(self.doc)
        data["personnes_2023"]["revenu_imposable_mcad"]+=1
        with self.assertRaises(ValueError):
            m.validate(data)

    def test_28_change_year_rejected(self):
        data=copy.deepcopy(self.doc)
        data["sources"]["societes"]["annee_imposition"]=2023
        with self.assertRaises(ValueError):
            m.validate(data)

    def test_29_make_tax_rate_rejected(self):
        data=copy.deepcopy(self.doc)
        data["comparaison_sans_addition"]["taux_pour_financer_les_deux_prelevements_pct"]=15
        with self.assertRaises(ValueError):
            m.validate(data)

    def test_30_close_task_rejected(self):
        data=copy.deepcopy(self.doc)
        data["pistes_de_travail"][0]["statut"]="TERMINE"
        with self.assertRaises(ValueError):
            m.validate(data)

    def test_31_disable_safeguard_rejected(self):
        data=copy.deepcopy(self.doc)
        data["protections"]["NE_JAMAIS_ADDITIONNER_ASSIETTES_ANNEES_DIFFERENTES"]=False
        with self.assertRaises(ValueError):
            m.validate(data)

    def test_32_default_cli(self):
        self.assertEqual(m.main([]),0)

    def test_33_no_rate_cli(self):
        self.assertEqual(m.main(["--exiger-taux-demontre"]),3)

    def test_34_public_exports(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"report.json"
            b=Path(d)/"table.json"
            self.assertEqual(m.main(["--bilan-public",str(a),"--table-public",str(b)]),0)
            self.assertEqual(json.loads(a.read_text())["particuliers_revenu_imposable_historique_mcad"],372261)
            self.assertEqual(json.loads(b.read_text())["societes_2021"]["revenu_imposable_au_quebec_mcad"],95784)

    def test_35_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"report.json"
            a.write_text("conserver")
            self.assertEqual(m.main(["--bilan-public",str(a)]),2)
            self.assertEqual(a.read_text(),"conserver")

    def test_36_reject_equal_destinations(self):
        with tempfile.TemporaryDirectory() as d:
            a=str(Path(d)/"report.json")
            self.assertEqual(m.main(["--bilan-public",a,"--table-public",a]),2)


if __name__=="__main__":
    unittest.main()
