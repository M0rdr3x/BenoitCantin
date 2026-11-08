"""P56K: tests des vraies assiettes 2021/2023 et des dépenses fiscales 2025."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/auditer_assiettes_revenues_societes_nova_p56k.py"
DATA=ROOT/"projets/projet-nova/etudes/P56K_ASSIETTES_PARTICULIERS_SOCIETES_CREDITS_SOURCES_OFFICIELLES.json"
MODEL=ROOT/"projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json"
EVIDENCE=ROOT/"projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json"
BAROMETER=ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
spec=importlib.util.spec_from_file_location("p56k",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestsP56K(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=[json.loads(f.read_text(encoding="utf-8")) for f in
                    (DATA,MODEL,EVIDENCE,BAROMETER)]
        cls.report=mod.auditer(*cls.inputs)
    def changed(self,index=0):
        return copy.deepcopy(self.inputs[index])
    def reject(self,x,index=0):
        args=list(self.inputs)
        args[index]=x
        with self.assertRaises(ValueError):
            mod.auditer(*args)
    def test_01_schema(self):self.assertEqual(self.report["schema_version"],"P56K-1")
    def test_02_personal_year(self):self.assertEqual(self.report["particuliers_annee"],2023)
    def test_03_personal_income_total(self):self.assertEqual(self.report["particuliers_revenu_total_mcad"],"427915")
    def test_04_personal_taxable(self):self.assertEqual(self.report["particuliers_revenu_imposable_mcad"],"372261")
    def test_05_personal_after_refundable(self):self.assertEqual(self.report["particuliers_impot_apres_credits_remboursables_mcad"],"31485")
    def test_06_personal_2023_rounding(self):self.assertEqual(self.report["particuliers_ecart_arrondi_imposable_mcad"],"1")
    def test_07_brackets_total(self):self.assertEqual(self.report["particuliers_six_tranches_revenus_totaux_mcad"],"427915")
    def test_08_corporate_year(self):self.assertEqual(self.report["societes_annee"],2021)
    def test_09_corporate_taxable(self):self.assertEqual(self.report["societes_revenu_imposable_quebec_mcad"],"95784")
    def test_10_corporate_fss_base(self):self.assertEqual(self.report["societes_fss_masse_salariale_assujettie_mcad"],"155850")
    def test_11_corporate_credits(self):self.assertEqual(self.report["societes_credits_mcad"],"2468")
    def test_12_corporate_rounding(self):self.assertEqual(self.report["societes_ecart_arrondi_net_mcad"],"-1")
    def test_13_corporate_no_tax(self):self.assertEqual(self.report["societes_non_imposees_nombre"],"322020")
    def test_14_fiscal_year(self):self.assertEqual(self.report["depenses_fiscales_annee"],2025)
    def test_15_tax_expenditures(self):self.assertEqual(self.report["depenses_fiscales_publiees_mcad"],"52864.9")
    def test_16_tax_expenditures_not_cash(self):self.assertIsNone(self.report["recettes_certaines_du_retrait_credits_mcad"])
    def test_17_fiscal_control(self):self.assertEqual(self.report["controle_fiscal_2025_2026_resultats_publies_mcad"],"4797")
    def test_18_fiscal_control_not_nova_revenue(self):self.assertIsNone(self.report["recettes_nouvelles_nova_anti_paradis_mcad"])
    def test_19_different_years(self):self.assertFalse(self.report["annees_harmonisees"])
    def test_20_no_future_tax_base(self):self.assertIsNone(self.report["assiette_nova_2027_2036_mcad"])
    def test_21_no_rate(self):self.assertFalse(self.report["taux_nova_calculable"])
    def test_22_no_incidence(self):self.assertFalse(self.report["incidence_distributive_calculee"])
    def test_23_no_budget(self):self.assertFalse(self.report["budget_nova_valide"])
    def test_24_missing_budget(self):self.assertEqual(self.report["montants_budget_p52b_inconnus"],600)
    def test_25_missing_incidence(self):self.assertEqual(self.report["incidences_p52d_inconnues"],720)
    def test_26_missing_proofs(self):self.assertEqual(self.report["preuves_p52a_non_validees"],20)
    def test_27_score(self):self.assertEqual(self.report["score_estime_p55n"],53)
    def test_28_no_go(self):self.assertEqual(self.report["decision"],"NO_GO_AUTOMATIQUE")
    def test_29_personal_taxable_falsification(self):
        d=self.changed();d["particuliers_2023"]["revenu_imposable_mcad"]="372262";self.reject(d)
    def test_30_personal_credits_falsification(self):
        d=self.changed();d["particuliers_2023"]["credits_remboursables_mcad"]="0";self.reject(d)
    def test_31_personal_wrong_denominator(self):
        d=self.changed();d["particuliers_2023"]["taux_moyen_denominateur"]="REVENU_IMPOSABLE";self.reject(d)
    def test_32_brackets_not_taxable_income(self):
        d=self.changed();d["particuliers_2023"]["distribution_type"]="REVENU_IMPOSABLE";self.reject(d)
    def test_33_personal_bracket_modified(self):
        d=self.changed();d["particuliers_2023"]["distribution_revenu_total_2023_mcad"][0]["montant"]="2533";self.reject(d)
    def test_34_personal_counts_modified(self):
        d=self.changed();d["particuliers_2023"]["declarations_non_imposables_milliers"]="2300";self.reject(d)
    def test_35_corporate_fss_base_not_profit(self):
        d=self.changed();d["societes_2021"]["masse_salariale_assujettie_fss_mcad"]="95784";self.reject(d)
    def test_36_corporate_2021_net_must_round(self):
        d=self.changed();d["societes_2021"]["impots_et_cotisations_nets_apres_credits_publies_mcad"]="12859";self.reject(d)
    def test_37_corporate_count_modified(self):
        d=self.changed();d["societes_2021"]["nb_societes_non_imposees_revenu"]="322021";self.reject(d)
    def test_38_fiscal_expenditure_invented_cash(self):
        d=self.changed();d["depenses_fiscales_2025"]["recettes_automatiquement_recuperables_mcad"]="52864.9";self.reject(d)
    def test_39_fiscal_expenditure_total_falsified(self):
        d=self.changed();d["depenses_fiscales_2025"]["total_publie_mcad"]="53000";self.reject(d)
    def test_40_no_nova_anti_evasion_from_controls(self):
        d=self.changed();d["controle_fiscal_2025_2026"]["nouveau_rendement_recouvrable_nova_mcad"]="4797";self.reject(d)
    def test_41_no_p52b_fiscal_control_addition(self):
        d=self.changed();d["controle_fiscal_2025_2026"]["ajout_au_revenu_p52b_autorise"]=True;self.reject(d)
    def test_42_no_federal_cut(self):
        d=self.changed();d["deux_regimes"]["QUEBEC_DANS_CANADA"]["impots_federaux_non_supprimables_unilateralement"]=False;self.reject(d)
    def test_43_no_sovereign_fiscal_yield(self):
        d=self.changed();d["deux_regimes"]["QUEBEC_SOUVERAIN"]["assiettes_federales_net_recouvrables_mcad"]="90000";self.reject(d)
    def test_44_no_decade_importation(self):
        d=self.changed();d["transposition_p52b"]=True;self.reject(d)
    def test_45_no_false_adopted_rate(self):
        d=self.changed();d["taux_fiscaux_nova_adoptes"]=True;self.reject(d)
    def test_46_no_false_validation(self):
        d=self.changed();d["validation_independante_nova"]=True;self.reject(d)
    def test_47_p55n_not_faked(self):
        d=self.changed(3);d["score_estimatif"]=100;self.reject(d,3)
    def test_48_p52b_without_invented_funds(self):
        d=self.changed(1)
        d["regimes"]["QUEBEC_DANS_CANADA"]["trajectoires"]["central"][0]["recettes"]["impot_revenu_net"]="999"
        self.reject(d,1)
    def test_49_source_url_provenance(self):
        d=self.changed();d["sources"]["SOCIETES_2021"]["url"]="https://example.com/faux";self.reject(d)
    def test_50_no_sources_year_merge(self):
        d=self.changed();d["comparabilite"]["annees_alignées"]=True;self.reject(d)
    def test_51_no_fake_proof(self):
        d=self.changed();d["preuves_suivantes"][0]["statut"]="OBTENUE";self.reject(d)
    def test_52_cli_output_and_refuse_overwrite(self):
        args=[sys.executable,str(SCRIPT),"--assiettes",str(DATA),
              "--gabarit",str(MODEL),"--preuves",str(EVIDENCE),
              "--barometre",str(BAROMETER)]
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)["societes_revenu_imposable_quebec_mcad"],"95784")
        with tempfile.TemporaryDirectory() as tmp:
            report=Path(tmp)/"rapport.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(report)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(report)],capture_output=True).returncode,2)
    def test_53_cli_refuse_taux_certifie(self):
        args=[sys.executable,str(SCRIPT),"--assiettes",str(DATA),
              "--gabarit",str(MODEL),"--preuves",str(EVIDENCE),
              "--barometre",str(BAROMETER),"--exiger-taux-certifie"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
