"""P52H — 20 contrôles contradictoires du bilan fiscal agrégé."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/auditer_preparation_fiscale_nova_p52h.py"
spec=importlib.util.spec_from_file_location("p52h_audit",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def inputs():
    return m.load_inputs()

class FiscalReadiness(unittest.TestCase):
    def test_01_four_source_documents_exist(self):
        self.assertEqual(set(inputs()),set(m.FILES))
    def test_02_counts_reconcile_across_models(self):
        x=m.analyser(inputs())
        self.assertEqual((x["lignes_projection"],x["cas_incidence"]),(60,42))
        self.assertEqual((x["cas_menages"],x["cas_entreprises"]),(30,12))
    def test_03_initial_model_unknown_not_zero(self):
        x=m.analyser(inputs())
        self.assertEqual(x["champs_financiers_encore_inconnus"],600)
        self.assertEqual(x["montants_individuels_encore_inconnus"],720)
        self.assertEqual(x["preuves_fiscales_P52A_encore_non_attestees"],20)
    def test_04_zero_observed_loss_not_proof_of_zero_loss(self):
        x=m.analyser(inputs())
        self.assertEqual(x["pertes_signalees_dans_cas_calculables"],0)
        self.assertEqual(x["cas_incidence_conditionnellement_calculables"],0)
        self.assertEqual(x["statut_conclusion_pertes"],
                         "AUCUN_CAS_EVALUABLE_PAS_ZERO_PERTE_DEMONTREE")
        self.assertFalse(x["absence_appauvrissement_population_demontree"])
    def test_05_budget_baseline_never_expands_to_future(self):
        x=m.analyser(inputs())
        self.assertTrue(x["recettes_budget_2026_2027_reference_verifiees_arithmetiquement"])
        self.assertTrue(x["budget_reference_non_extrapole_aux_annees_futures"])
        self.assertFalse(x["budget_source_originale_verifiee_independamment"])
    def test_06_no_go_flags_unconditionally_false(self):
        x=m.analyser(inputs())
        for key in ("absence_appauvrissement_population_demontree",
                    "causalite_fiscale_demontree","reforme_deux_prelevements_financee",
                    "souverainete_etablie",
                    "revenus_anti_evasion_supplementaires_certifies",
                    "tarif_fiscal_calcule_ou_adopte",
                    "publication_autorisee","fusion_autorisee"):
            self.assertIs(x[key],False,key)
        self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")
    def test_07_strict_blocks_present(self):
        blocks=m.analyser(inputs())["blocages"]
        self.assertIn("PREUVES_FISCALES_INDEPENDANTES_NON_REUNIES",blocks)
        self.assertIn("INCIDENCE_MENAGES_ENTREPRISES_INCOMPLETE",blocks)
        self.assertIn("REPRESENTATIVITE_POPULATION_NON_ETABLIE",blocks)
        self.assertIn("AUTORISATION_JURIDIQUE_DEMOCRATIQUE_ABSENTE",blocks)
    def test_08_aggregate_report_excludes_case_lists_and_balances(self):
        x=m.analyser(inputs())
        self.assertNotIn("cas",x)
        self.assertNotIn("resultats",x)
        self.assertNotIn("soldes_gcad",x)
        self.assertNotIn("sources",x)
        self.assertNotIn("variation_cad",json.dumps(x))
        self.assertTrue(x["rapport_sans_donnees_par_cas"])
    def test_09_tampered_official_budget_amount_rejected(self):
        src=inputs()
        src["budget"]["lignes_revenus"][0]["valeur_mcad"]="99999"
        with self.assertRaises(ValueError):
            m.analyser(src)
    def test_10_tampered_financial_schema_rejected(self):
        src=inputs()
        src["projection"]["schema_version"]="P52X"
        with self.assertRaises(ValueError):
            m.analyser(src)
    def test_11_changed_projection_year_rejected(self):
        src=inputs()
        src["projection"]["regimes"]["QUEBEC_DANS_CANADA"]["trajectoires"]["central"][0]["exercice_debut"]=2036
        with self.assertRaises(ValueError):
            m.analyser(src)
    def test_12_tampered_population_claim_rejected(self):
        src=inputs()
        p=m.p52d.evaluate(src["incidence"])
        p["aucune_projection_population"]=False
        with patch.object(m.p52d,"evaluate",return_value=p):
            with self.assertRaisesRegex(ValueError,"REPRESENTATIVITE_OU_CAUSALITE"):
                m.analyser(src)
    def test_13_disagreeing_incidence_totals_rejected(self):
        src=inputs()
        p=m.p52e.analyse(src["incidence"])
        p["montants_manquants"]=1
        with patch.object(m.p52e,"analyse",return_value=p):
            with self.assertRaisesRegex(ValueError,"INCIDENCE_ET_ALERTE"):
                m.analyser(src)
    def test_14_per_case_payload_is_not_copied_into_aggregate(self):
        src=inputs()
        p=m.p52e.analyse(src["incidence"])
        p["cas"]={"menages":[{"secret":"DO_NOT_EXPORT_12345"}]}
        with patch.object(m.p52e,"analyse",return_value=p):
            x=m.analyser(src)
            self.assertNotIn("DO_NOT_EXPORT_12345",json.dumps(x))
    def test_15_fake_source_registry_gives_no_validation(self):
        src=inputs()
        src["preuves"]["automatic_go"]=True
        with self.assertRaises(ValueError):
            m.analyser(src)
    def test_16_wrong_source_set_rejected(self):
        src=inputs()
        del src["incidence"]
        with self.assertRaisesRegex(ValueError,"QUATRE_SOURCES"):
            m.analyser(src)
    def test_17_invalid_claimed_go_from_downstream_rejected(self):
        src=inputs()
        p=m.p52e.analyse(src["incidence"])
        p["decision"]="GO"
        with patch.object(m.p52e,"analyse",return_value=p):
            with self.assertRaisesRegex(ValueError,"DECISION_INCOHERENTE"):
                m.analyser(src)
    def test_18_cli_observation_zero_means_report_only(self):
        with tempfile.TemporaryDirectory() as root:
            out=Path(root)/"report.json"
            self.assertEqual(m.main(["--rapport",str(out)]),0)
            x=json.loads(out.read_text("utf-8"))
            self.assertFalse(x["publication_autorisee"])
            self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")
    def test_19_cli_strict_returns_three_even_when_all_sources_readable(self):
        with tempfile.TemporaryDirectory() as root:
            out=Path(root)/"strict.json"
            self.assertEqual(m.main(["--rapport",str(out),
                                     "--exiger-preparation"]),3)
            x=json.loads(out.read_text("utf-8"))
            self.assertTrue(x["blocages"])
    def test_20_cli_missing_file_returns_two_and_no_go(self):
        with tempfile.TemporaryDirectory() as root:
            out=Path(root)/"error.json"
            self.assertEqual(m.main(["--preuves",str(Path(root)/"missing.json"),
                                     "--rapport",str(out)]),2)
            x=json.loads(out.read_text("utf-8"))
            self.assertEqual(x["statut"],"ERREUR_VALIDATION")
            self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")

if __name__=="__main__":
    unittest.main()
