"""P56S : preuve arithmétique des trois options, sans chiffrer un programme adopté."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/comparer_options_fiscales_et_financement_nova_p56s.py"
PATHS=[
ROOT/"projets/projet-nova/etudes/P56S_TROIS_OPTIONS_FISCALES_2027_2031_ET_CONDITIONS_PROTECTION.json",
ROOT/"projets/projet-nova/etudes/P56R_INVENTAIRE_EXHAUSTIF_CATEGORIES_RECETTES_ET_PONT_FISCAL_2026_2031.json",
ROOT/"projets/projet-nova/etudes/P56Q_PONT_CONTREFACTUEL_RECETTES_2027_2031_SIMULATEUR_AMENDE.json",
ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
]
spec=importlib.util.spec_from_file_location("p56s",SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def option(d,key):
    return next(x for x in d["options"] if x["id"]==key)
def row(d,key,year="2027-2028"):
    return next(x for x in option(d,key)["resultats_par_exercice"] if x["exercice"]==year)

class TestP56S(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=[json.loads(f.read_text(encoding="utf-8")) for f in PATHS]
        cls.result=module.valider(*cls.data)
    def altered(self,i=0):
        return copy.deepcopy(self.data[i])
    def reject(self,d,i=0):
        args=list(self.data);args[i]=d
        with self.assertRaises(ValueError):
            module.valider(*args)
    def test_01_jalon(self):self.assertEqual(self.result["jalon"],"P56S")
    def test_02_53_percent(self):self.assertEqual(self.result["score_estime_pourcent"],53)
    def test_03_47_points(self):self.assertEqual(self.result["points_estimes_restants"],47)
    def test_04_three_options(self):self.assertEqual(self.result["nombre_options"],3)
    def test_05_four_years(self):self.assertEqual(len(self.result["exercices_comparables"]),4)
    def test_06_2027_baseline_lost_zero(self):
        self.assertEqual(self.result["2027_2028"]["S1_CONTINUITE"]["perte_fictive_recettes_mcad"],"0.00")
    def test_07_2027_baseline_deficit(self):
        self.assertEqual(self.result["2027_2028"]["S1_CONTINUITE"]["solde_sans_financement_mcad"],"-5695.00")
    def test_08_2027_partial_25_loss(self):
        self.assertEqual(self.result["2027_2028"]["S2_TRANSITION_CONDITIONNELLE"]["perte_fictive_recettes_mcad"],"10718.75")
    def test_09_2027_partial_25_deficit(self):
        self.assertEqual(self.result["2027_2028"]["S2_TRANSITION_CONDITIONNELLE"]["solde_sans_financement_mcad"],"-16413.75")
    def test_10_2027_partial_25_zero_balance(self):
        self.assertEqual(self.result["2027_2028"]["S2_TRANSITION_CONDITIONNELLE"]["besoin_total_equilibre_sans_resorption_mcad"],"16413.75")
    def test_11_2027_full_loss(self):
        self.assertEqual(self.result["2027_2028"]["S3_CIBLE_DEUX_PRELEVEMENTS"]["perte_fictive_recettes_mcad"],"42875.00")
    def test_12_2027_full_deficit(self):
        self.assertEqual(self.result["2027_2028"]["S3_CIBLE_DEUX_PRELEVEMENTS"]["solde_sans_financement_mcad"],"-48570.00")
    def test_13_2027_full_maintain_same_balance(self):
        self.assertEqual(self.result["2027_2028"]["S3_CIBLE_DEUX_PRELEVEMENTS"]["besoin_remplacement_meme_solde_mcad"],"42875.00")
    def test_14_2028_unfunded_gap(self):
        self.assertEqual(self.result["options"]["S3_CIBLE_DEUX_PRELEVEMENTS"]["2028-2029"]["solde_sans_financement_ni_resorption_mcad"],"-47519.00")
    def test_15_2029_no_mitigation(self):
        self.assertEqual(self.result["options"]["S3_CIBLE_DEUX_PRELEVEMENTS"]["2029-2030"]["solde_sans_financement_ni_resorption_mcad"],"-47313.00")
    def test_16_2030_no_mitigation(self):
        self.assertEqual(self.result["options"]["S3_CIBLE_DEUX_PRELEVEMENTS"]["2030-2031"]["solde_sans_financement_ni_resorption_mcad"],"-48278.00")
    def test_17_not_adopted(self):self.assertTrue(self.result["aucune_transition_adoptee"])
    def test_18_not_certified(self):self.assertFalse(self.result["budget_nova_certifie"])
    def test_19_no_sovereign_budget(self):self.assertFalse(self.result["budget_souverain_certifie"])
    def test_20_no_adopted_tax_rate(self):self.assertTrue(self.result["aucun_taux_nova_publie"])
    def test_21_zero_closure(self):self.assertEqual(self.result["conditions_au_100_pourcent_demontrees"],0)
    def test_22_no_go(self):self.assertEqual(self.result["decision"],"NO_GO_AUTOMATIQUE")
    def test_23_false_100(self):
        x=self.altered();x["barometre"]["score_estime_sur_100"]=100;self.reject(x)
    def test_24_fake_tax_approved(self):
        x=self.altered();x["indicateurs_refus"]["options_adoptees"]=1;self.reject(x)
    def test_25_wrong_source(self):
        x=self.altered();x["sources"]["p56r"]="https://untrusted.example";self.reject(x)
    def test_26_one_quarter_is_not_policy(self):
        x=self.altered();x["hypotheses_communes"]["un_quart_pour_S2_est_sensibilite_pas_echeancier"]=False;self.reject(x)
    def test_27_hide_services(self):
        x=self.altered();x["hypotheses_communes"]["budgets_services_inchanges_pour_mesure_risque"]=False;self.reject(x)
    def test_28_hide_credits(self):
        x=self.altered();x["hypotheses_communes"]["credits_et_prestations_des_menages_a_preserver"]=False;self.reject(x)
    def test_29_remove_year(self):
        x=self.altered();option(x,"S2_TRANSITION_CONDITIONNELLE")["resultats_par_exercice"].pop();self.reject(x)
    def test_30_2027_fake_quarter(self):
        x=self.altered();option(x,"S2_TRANSITION_CONDITIONNELLE")["numerateur"]=2;self.reject(x)
    def test_31_fake_phase_financing(self):
        x=self.altered();row(x,"S2_TRANSITION_CONDITIONNELLE")["recettes_nouvelles_impot_revenu_nova_reellement_demontrees_mcad"]="10718.75";self.reject(x)
    def test_32_fake_haven_cash(self):
        x=self.altered();row(x,"S3_CIBLE_DEUX_PRELEVEMENTS")["recettes_nouvelles_anti_paradis_reellement_demontrees_mcad"]="42875.00";self.reject(x)
    def test_33_fake_family_compensation(self):
        x=self.altered();row(x,"S2_TRANSITION_CONDITIONNELLE")["compensations_pertes_prestations_mcad"]="0.00";self.reject(x)
    def test_34_fake_transition_costs(self):
        x=self.altered();row(x,"S3_CIBLE_DEUX_PRELEVEMENTS")["cout_transition_mcad"]="0.00";self.reject(x)
    def test_35_wrong_fraction(self):
        x=self.altered();option(x,"S2_TRANSITION_CONDITIONNELLE")["denominateur"]=3;self.reject(x)
    def test_36_wrong_loss(self):
        x=self.altered();row(x,"S2_TRANSITION_CONDITIONNELLE")["recettes_retirees_uniquement_dans_le_test_mcad"]="10718.76";self.reject(x)
    def test_37_wrong_baseline(self):
        x=self.altered();row(x,"S1_CONTINUITE")["solde_loi_reference_avec_mesures_a_resorber_mcad"]="-5000.00";self.reject(x)
    def test_38_hide_unfunded_gap(self):
        x=self.altered();row(x,"S3_CIBLE_DEUX_PRELEVEMENTS","2028-2029")["solde_loi_sans_nouveau_financement_et_sans_resorption_mcad"]="-45669.00";self.reject(x)
    def test_39_false_unbalanced_replacement(self):
        x=self.altered();row(x,"S3_CIBLE_DEUX_PRELEVEMENTS")["ressources_additionnelles_pour_solde_loi_zero_sans_resorption_mcad"]="42875.00";self.reject(x)
    def test_40_duplicate_option(self):
        x=self.altered();x["options"][0]["id"]="S3_CIBLE_DEUX_PRELEVEMENTS";self.reject(x)
    def test_41_sovereign_is_undefined(self):
        x=self.altered();x["souverainete"]["toutes_lignes_quantitatives"]={"revenus":100};self.reject(x)
    def test_42_no_unjustified_2027_2036(self):
        x=self.altered();x["perimetre"]["annees_modeles_non_justifiees"].pop();self.reject(x)
    def test_43_false_independent_advice(self):
        x=self.altered();x["barometre"]["avis_independants_signes"]=5;self.reject(x)
    def test_44_no_fake_proof(self):
        x=self.altered();x["priorite_et_preuves_a_obtenir"][0]["statut"]="PROUVEE";self.reject(x)
    def test_45_no_fabricated_p56q_benchmark(self):
        x=self.altered(2);x["annees_reconciliees"][2]["solde_budgetaire_initial_au_sens_de_la_loi_mcad"]="-4000";self.reject(x,2)
    def test_46_no_fabricated_p56r_revenue(self):
        x=self.altered(1);x["rapprochement_annees"][2]["trois_categories_a_remplacer_si_supprimees_mcad"]="100";self.reject(x,1)
    def test_47_no_barometer_inflation(self):
        x=self.altered(4);x["score_estimatif"]=55;self.reject(x,4)
    def test_48_cli_report(self):
        args=[sys.executable,str(SCRIPT),"--options",str(PATHS[0]),"--p56r",str(PATHS[1]),
              "--p56q",str(PATHS[2]),"--cloture",str(PATHS[3]),"--barometre",str(PATHS[4])]
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)["2027_2028"]["S2_TRANSITION_CONDITIONNELLE"]["perte_fictive_recettes_mcad"],"10718.75")
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/"report.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(dest)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(dest)],capture_output=True).returncode,2)
    def test_49_cli_no_automatic_adoption(self):
        args=[sys.executable,str(SCRIPT),"--options",str(PATHS[0]),"--p56r",str(PATHS[1]),
              "--p56q",str(PATHS[2]),"--cloture",str(PATHS[3]),"--barometre",str(PATHS[4]),
              "--exiger-option-adoptee"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
