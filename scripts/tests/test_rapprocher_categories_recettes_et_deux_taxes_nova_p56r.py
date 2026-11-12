"""P56R: 48 tests pour les 8 catégories de revenus et l'impossibilité d'inventer un taux Nova."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/rapprocher_categories_recettes_et_deux_taxes_nova_p56r.py"
FILES=[
ROOT/"projets/projet-nova/etudes/P56R_INVENTAIRE_EXHAUSTIF_CATEGORIES_RECETTES_ET_PONT_FISCAL_2026_2031.json",
ROOT/"projets/projet-nova/etudes/P56P_BASE_BUDGET_PREELECTORALE_2026_2031_VGQ_ET_ECARTS.json",
ROOT/"projets/projet-nova/etudes/P56Q_PONT_CONTREFACTUEL_RECETTES_2027_2031_SIMULATEUR_AMENDE.json",
ROOT/"projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json",
ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json",
ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json"
]
spec=importlib.util.spec_from_file_location("p56r",SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestP56R(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=[json.loads(p.read_text(encoding="utf-8")) for p in FILES]
        cls.result=module.controler(*cls.args)
    def clone(self,n=0):
        return copy.deepcopy(self.args[n])
    def reject(self,d,n=0):
        args=list(self.args);args[n]=d
        with self.assertRaises(ValueError):
            module.controler(*args)
    def cat(self,d,key):
        return next(x for x in d["categories_officielles"] if x["poste_p56p"]==key)
    def year(self,d,fy):
        return next(x for x in d["rapprochement_annees"] if x["exercice"]==fy)
    def gate(self,d,n):
        return next(x for x in d["conditions_pour_prochaine_phase"] if x["id"]==n)
    def test_01_schema(self):self.assertEqual(self.args[0]["schema_version"],"P56R-1")
    def test_02_count_categories(self):self.assertEqual(self.result["nombre_categories_revenues"],8)
    def test_03_count_years(self):self.assertEqual(self.result["nombre_exercices_reference"],6)
    def test_04_pivot_year(self):self.assertEqual(self.result["annee_pivot"],"2027-2028")
    def test_05_income_current(self):self.assertEqual(self.result["tableau_annee_pivot"]["impots_revenu_actuels_mcad"],"68093")
    def test_06_three_levies(self):self.assertEqual(self.result["tableau_annee_pivot"]["trois_categories_a_remplacer_mcad"],"42875")
    def test_07_other_income(self):self.assertEqual(self.result["tableau_annee_pivot"]["autres_revenus_provinciaux_mcad"],"29246")
    def test_08_federal_transfers(self):self.assertEqual(self.result["tableau_annee_pivot"]["transferts_federaux_mcad"],"34011")
    def test_09_public_total(self):self.assertEqual(self.result["tableau_annee_pivot"]["revenus_publics_totaux_mcad"],"174225")
    def test_10_current_yield_ratio(self):self.assertEqual(self.result["tableau_annee_pivot"]["ratio_recettes_a_remplacer_sur_impots_revenu_actuels_pourcent"],"62.97")
    def test_11_static_balancing_requirement(self):self.assertEqual(self.result["tableau_annee_pivot"]["besoin_statique_zero_solde_loi_mcad"],"48570")
    def test_12_no_tax_rate(self):self.assertFalse(self.result["taux_fiscal_nova_calculable"])
    def test_13_no_adoption(self):self.assertFalse(self.result["mesures_deux_prelevements_adoptees"])
    def test_14_no_sovereign_transfers(self):self.assertTrue(self.result["transferts_federaux_non_recettes_souveraines_acquises"])
    def test_15_unknown_other_income(self):self.assertTrue(self.result["revenus_non_classes_comme_impots_a_ventiler"])
    def test_16_gates(self):self.assertEqual(self.result["conditions_non_demontrees"],10)
    def test_17_score(self):self.assertEqual(self.result["score_estime_p55n"],53)
    def test_18_points_remaining(self):self.assertEqual(self.result["points_restants_estimes"],47)
    def test_19_missing_budget(self):self.assertEqual(self.result["p52b_montants_inconnus"],600)
    def test_20_missing_incidence(self):self.assertEqual(self.result["p52d_incidences_inconnues"],720)
    def test_21_not_done(self):self.assertFalse(self.result["programme_termine"])
    def test_22_no_go(self):self.assertEqual(self.result["decision"],"NO_GO_AUTOMATIQUE")
    def test_23_source_modified(self):
        d=self.clone();d["provenance"]["budget_officiel"]["url"]="https://example.org";self.reject(d)
    def test_24_fss_source_modified(self):
        d=self.clone();d["provenance"]["fss"]["url"]="https://example.org";self.reject(d)
    def test_25_school_source_modified(self):
        d=self.clone();d["provenance"]["taxe_scolaire"]["url"]="https://example.org";self.reject(d)
    def test_26_shorten_category_list(self):
        d=self.clone();d["categories_officielles"].pop();self.reject(d)
    def test_27_duplicate_category(self):
        d=self.clone();d["categories_officielles"][0]["poste_p56p"]="impots_societes";self.reject(d)
    def test_28_fake_income_tax(self):
        d=self.clone();self.cat(d,"impot_particuliers")["montants_annee_p56p_mcad"]["2027-2028"]="52842";self.reject(d)
    def test_29_fake_other_revenues(self):
        d=self.clone();self.cat(d,"revenus_divers")["montants_annee_p56p_mcad"]["2027-2028"]="0";self.reject(d)
    def test_30_wrong_class_for_FSS(self):
        d=self.clone();self.cat(d,"cotisations_services_sante")["nature"]="IMPOT_SUR_PROFIT";self.reject(d)
    def test_31_wrong_class_for_public_business(self):
        d=self.clone();self.cat(d,"entreprises_gouvernement")["traitement_provisoire"]="IMPOT_REVENU";self.reject(d)
    def test_32_false_proven_legal_opinion(self):
        d=self.clone();self.cat(d,"impot_foncier_scolaire")["avis_juridique_independant"]="signe";self.reject(d)
    def test_33_fake_household_revenue(self):
        d=self.clone();self.year(d,"2027-2028")["impots_sur_revenu_actuels_mcad"]="68094";self.reject(d)
    def test_34_fake_other_autonomous(self):
        d=self.clone();self.year(d,"2027-2028")["autres_revenus_autonomes_a_qualifier_mcad"]="29247";self.reject(d)
    def test_35_fake_transfer(self):
        d=self.clone();self.year(d,"2027-2028")["transferts_federaux_au_regime_actuel_mcad"]="0";self.reject(d)
    def test_36_invent_tax_rate(self):
        d=self.clone();self.year(d,"2027-2028")["taux_effectif_nova"]="62.97";self.reject(d)
    def test_37_invent_anti_haven_yield(self):
        d=self.clone();self.year(d,"2027-2028")["rendement_cible_anti_paradis_prevu_mcad"]="42875";self.reject(d)
    def test_38_tax_yield_percentage_is_not_a_tax_rate(self):
        d=self.clone();self.year(d,"2027-2028")["n_est_pas_une_hausse_de_taux_recommandee"]=False;self.reject(d)
    def test_39_wrong_ratio(self):
        d=self.clone();self.year(d,"2027-2028")["recettes_remplacement_en_pourcentage_des_impots_revenu_actuels"]="63.00";self.reject(d)
    def test_40_abolition_not_adopted(self):
        d=self.clone();d["deux_prelevements_et_limites"]["suppression_taxes_consommation_provinciales_NON_adoptee"]=False;self.reject(d)
    def test_41_public_services_not_saved(self):
        d=self.clone();d["deux_prelevements_et_limites"]["offre_services_publics_maintenue_dans_contre_factuel"]=False;self.reject(d)
    def test_42_sovereign_unauthorized_transfer(self):
        d=self.clone();d["deux_regimes"]["QUEBEC_SOUVERAIN"]["transferts_federaux_maintenus_par_defaut"]=True;self.reject(d)
    def test_43_sovereign_free_cash(self):
        d=self.clone();d["deux_regimes"]["QUEBEC_SOUVERAIN"]["assiettes_impots_federaux_devenu_souverains_mcad"]="90000";self.reject(d)
    def test_44_no_federal_tax_unilaterally_abrogated(self):
        d=self.clone();d["deux_regimes"]["QUEBEC_DANS_CANADA"]["tps_et_impots_federaux_non_abolissables_unilateralement"]=False;self.reject(d)
    def test_45_false_gate_closed(self):
        d=self.clone();self.gate(d,"R01")["statut"]="VALIDE";self.reject(d)
    def test_46_wrong_p56q_source(self):
        d=self.clone(2);d["annees_reconciliees"][2]["trois_categories_risque_suppression_mcad"]="40000";self.reject(d,2)
    def test_47_cli_json_and_no_overwrite(self):
        args=[sys.executable,str(SCRIPT),"--inventaire",str(FILES[0]),
              "--p56p",str(FILES[1]),"--p56q",str(FILES[2]),
              "--p52b",str(FILES[3]),"--barometre",str(FILES[4]),
              "--p56o",str(FILES[5])]
        result=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)["tableau_annee_pivot"]["trois_categories_a_remplacer_mcad"],"42875")
        with tempfile.TemporaryDirectory() as f:
            output=Path(f)/"r.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(output)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(output)],capture_output=True).returncode,2)
    def test_48_cli_refuse_certified_budget(self):
        args=[sys.executable,str(SCRIPT),"--inventaire",str(FILES[0]),
              "--p56p",str(FILES[1]),"--p56q",str(FILES[2]),
              "--p52b",str(FILES[3]),"--barometre",str(FILES[4]),
              "--p56o",str(FILES[5]),"--exiger-budget-nova-certifie"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
