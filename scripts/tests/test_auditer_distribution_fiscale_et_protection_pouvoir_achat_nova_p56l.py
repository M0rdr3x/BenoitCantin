"""P56L : protéger les crédits et mesurer la répartition 2023 sans gains Nova inventés."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
CODE=ROOT/"scripts/auditer_distribution_fiscale_et_protection_pouvoir_achat_nova_p56l.py"
DATA=ROOT/"projets/projet-nova/etudes/P56L_BASE_DISTRIBUTIVE_PARTICULIERS_2023_CREDITS_ET_QUINTILES.json"
PREVIOUS=ROOT/"projets/projet-nova/etudes/P56K_ASSIETTES_PARTICULIERS_SOCIETES_CREDITS_SOURCES_OFFICIELLES.json"
MODEL=ROOT/"projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json"
EVIDENCE=ROOT/"projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json"
BAROMETER=ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"

spec=importlib.util.spec_from_file_location("p56l",CODE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestP56L(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files=[DATA,PREVIOUS,MODEL,EVIDENCE,BAROMETER]
        cls.contents=[json.loads(x.read_text(encoding="utf-8")) for x in cls.files]
        cls.result=mod.audit(*cls.contents)
    def altered(self,i=0):
        return copy.deepcopy(self.contents[i])
    def reject(self,data,i=0):
        tmp=list(self.contents)
        tmp[i]=data
        with self.assertRaises(ValueError):
            mod.audit(*tmp)
    def bracket(self,d,id):
        return next(x for x in d["tranches_a14"] if x["id"]==id)
    def q(self,d,id):
        return next(x for x in d["quintiles_a3"] if x["id"]==id)
    def gate(self,d,id):
        return next(x for x in d["portes_protection"] if x["id"]==id)
    def test_01_schema(self):self.assertEqual(self.result["schema_version"],"P56L-1")
    def test_02_source_year(self):self.assertEqual(self.contents[0]["annee_observee"],2023)
    def test_03_six_brackets(self):self.assertEqual(self.result["tranches_revenu_total"],6)
    def test_04_five_quintiles(self):self.assertEqual(self.result["quintiles_de_declarants"],5)
    def test_05_income_total(self):self.assertEqual(self.result["total_revenu_declare_mcad"],"427915")
    def test_06_tax_payable(self):self.assertEqual(self.result["total_impot_a_payer_mcad"],"40790")
    def test_07_refundable_total(self):self.assertEqual(self.result["total_credits_remboursables_mcad"],"9305")
    def test_08_tax_minus_credits_total(self):self.assertEqual(self.result["net_impot_moins_credits_mcad"],"31485")
    def test_09_low_income_aggregate(self):self.assertEqual(self.result["revenus_total_moins_30000_mcad"],"41654")
    def test_10_low_income_tax_payable(self):self.assertEqual(self.result["impot_a_payer_moins_30000_mcad"],"285")
    def test_11_low_income_refundable(self):self.assertEqual(self.result["credits_remboursables_moins_30000_mcad"],"4201")
    def test_12_low_income_net(self):self.assertEqual(self.result["solde_impot_moins_credits_moins_30000_mcad"],"-3916")
    def test_13_low_income_credit_share(self):self.assertEqual(self.result["part_credits_remboursables_moins_30000_pourcent"],"45.1")
    def test_14_q5_income(self):self.assertEqual(self.result["q5_part_revenu_pourcent"],"50.10")
    def test_15_q5_tax(self):self.assertEqual(self.result["q5_part_impot_pourcent"],"69.41")
    def test_16_no_nova_cash_from_credits(self):self.assertIsNone(self.result["credits_ou_prestations_recuperables_nova_mcad"])
    def test_17_no_household_income(self):self.assertFalse(self.result["revenu_disponible_menages_demonstre"])
    def test_18_no_nova_incidence(self):self.assertFalse(self.result["simulation_incidence_reforme_nova_validee"])
    def test_19_ten_protection_gates(self):self.assertEqual(self.result["nombre_portes_protection_ouvertes"],10)
    def test_20_no_aligned_corporations(self):self.assertFalse(self.result["annees_fiscales_personnes_societes_harmonisees"])
    def test_21_no_tax_rate(self):self.assertIsNone(self.result["taux_propose_pour_2027_2036"])
    def test_22_no_p52d_data(self):self.assertEqual(self.result["cellules_incidence_p52d_certifiees"],0)
    def test_23_no_p52b_data(self):self.assertEqual(self.result["cellules_budget_p52b_certifiees"],0)
    def test_24_budget_still_missing(self):self.assertEqual(self.result["montants_budget_p52b_inconnus"],600)
    def test_25_incidence_still_missing(self):self.assertEqual(self.result["incidences_p52d_inconnues"],720)
    def test_26_score_not_inflated(self):self.assertEqual(self.result["p55n_score_estime"],53)
    def test_27_no_go(self):self.assertEqual(self.result["decision"],"NO_GO_AUTOMATIQUE")
    def test_28_false_gross_tax(self):
        d=self.altered();self.bracket(d,"R00_09999")["impot_sur_revenu_imposable_mcad"]="334";self.reject(d)
    def test_29_false_low_credits(self):
        d=self.altered();self.bracket(d,"R20_29999")["credits_remboursables_mcad"]="2305";self.reject(d)
    def test_30_false_100k_net(self):
        d=self.altered();self.bracket(d,"R100_PLUS")["impot_net_apres_credits_remboursables_mcad"]="22641";self.reject(d)
    def test_31_false_total_tax(self):
        d=self.altered();d["totaux_publies_a14"]["impot_a_payer_mcad"]="40791";self.reject(d)
    def test_32_no_rounding_erasure(self):
        d=self.altered();d["reconciliation_arrondis"]["ecart_somme_lignes_moins_total_credits_remboursables_mcad"]="0";self.reject(d)
    def test_33_no_low_income_credit_removal(self):
        d=self.altered();d["agregat_sensible_moins_30000"]["somme_fiscale_a_supprimer_dans_nova"]=True;self.reject(d)
    def test_34_no_fake_income_per_household(self):
        d=self.altered();d["agregat_sensible_moins_30000"]["aide_reelle_par_menage"]="1000";self.reject(d)
    def test_35_no_quintile_scenario(self):
        d=self.altered();self.q(d,"Q5")["simulation_nova_nette"]="positive";self.reject(d)
    def test_36_no_quintile_switch(self):
        d=self.altered();self.q(d,"Q1")["part_impot_a_payer_pourcent"]="1.46";self.reject(d)
    def test_37_no_quintile_household(self):
        d=self.altered();d["comparabilite_et_controles"]["statistique_unite_n_est_pas"]="MENAGES";self.reject(d)
    def test_38_no_policy_proof(self):
        d=self.altered();self.gate(d,"L01")["statut"]="OBTENU";self.reject(d)
    def test_39_no_independent_proof(self):
        d=self.altered();self.gate(d,"L10")["avis_independant_id"]="signe";self.reject(d)
    def test_40_no_sovereign_funds(self):
        d=self.altered();d["regimes"]["QUEBEC_SOUVERAIN"]["prestations_transferees_net_mcad"]="3000";self.reject(d)
    def test_41_no_gst_control(self):
        d=self.altered();d["regimes"]["QUEBEC_DANS_CANADA"]["taxes_federales_sous_controle_quebec"]=True;self.reject(d)
    def test_42_no_new_tax_rate(self):
        d=self.altered();d["taux_nova_adopte"]=True;self.reject(d)
    def test_43_no_2027_2036_data(self):
        d=self.altered();d["p52d_incidences_inconnues"]=700;self.reject(d)
    def test_44_no_false_source(self):
        d=self.altered();d["sources"]["A14"]["url"]="https://example.org/invalid";self.reject(d)
    def test_45_integration_p56k_baseline(self):
        d=self.altered(1);d["particuliers_2023"]["credits_remboursables_mcad"]="9304";self.reject(d,1)
    def test_46_integration_barometer(self):
        d=self.altered(4);d["score_estimatif"]=54;self.reject(d,4)
    def test_47_cannot_replace_taxable_base(self):
        d=self.altered();self.bracket(d,"R30_49999")["revenu_imposable_de_la_tranche_mcad"]="10000";self.reject(d)
    def test_48_no_fake_scenario_gain(self):
        d=self.altered();d["scenarios_a_etudier"][1]["solde_menage"]="100";self.reject(d)
    def test_49_cli_success_and_no_overwrite(self):
        args=[sys.executable,str(CODE),"--distribution",str(DATA),
              "--p56k",str(PREVIOUS),"--gabarit",str(MODEL),
              "--preuves",str(EVIDENCE),"--barometre",str(BAROMETER)]
        r=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)["solde_impot_moins_credits_moins_30000_mcad"],"-3916")
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"report.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(target)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(target)],capture_output=True).returncode,2)
    def test_50_cli_refuses_nova_certification(self):
        args=[sys.executable,str(CODE),"--distribution",str(DATA),
              "--p56k",str(PREVIOUS),"--gabarit",str(MODEL),
              "--preuves",str(EVIDENCE),"--barometre",str(BAROMETER),
              "--exiger-incidence-certifiee"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
