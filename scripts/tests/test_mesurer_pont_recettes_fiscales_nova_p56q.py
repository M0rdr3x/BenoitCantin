"""P56Q : contrôle des recettes à remplacer, hors faux budget Nova et faux audit XLSX."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"scripts/mesurer_pont_recettes_fiscales_nova_p56q.py"
FILES=[
ROOT/"projets/projet-nova/etudes/P56Q_PONT_CONTREFACTUEL_RECETTES_2027_2031_SIMULATEUR_AMENDE.json",
ROOT/"projets/projet-nova/etudes/P56P_BASE_BUDGET_PREELECTORALE_2026_2031_VGQ_ET_ECARTS.json",
ROOT/"projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json",
ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json",
ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json"
]
spec=importlib.util.spec_from_file_location("nova_p56q",SRC)
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class TestP56Q(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contents=[json.loads(f.read_text(encoding="utf-8")) for f in FILES]
        cls.result=p.audit(*cls.contents)
    def clone(self,index=0):
        return copy.deepcopy(self.contents[index])
    def reject(self,changed,index=0):
        args=list(self.contents);args[index]=changed
        with self.assertRaises(ValueError):
            p.audit(*args)
    def year(self,data,fy):
        return next(x for x in data["annees_reconciliees"] if x["exercice"]==fy)
    def one(self,data,number):
        return next(x for x in data["preuves_suivantes"] if x["id"]==number)
    def test_01_jalon(self):self.assertEqual(self.result["jalon"],"P56Q")
    def test_02_score(self):self.assertEqual(self.result["score_estime_p55n"],53)
    def test_03_no_go(self):self.assertEqual(self.result["decision"],"NO_GO_AUTOMATIQUE")
    def test_04_six_years_historical_and_fiscal(self):self.assertEqual(self.result["nombre_exercices_chiffres_source"],6)
    def test_05_four_projection_years(self):self.assertEqual(self.result["nombre_exercices_2027_2036_source_disponibles"],4)
    def test_06_six_projection_years_missing(self):self.assertEqual(self.result["nombre_exercices_2027_2036_non_couverts"],6)
    def test_07_2025_original_risk(self):self.assertEqual(self.result["montants_par_exercice"]["2025-2026"]["risque_trois_catégories_mcad"],"40186")
    def test_08_2026_risk(self):self.assertEqual(self.result["montants_par_exercice"]["2026-2027"]["risque_trois_catégories_mcad"],"41521")
    def test_09_2027_risk(self):self.assertEqual(self.result["fiscal_2027_2028"]["risque_trois_catégories_mcad"],"42875")
    def test_10_2028_risk(self):self.assertEqual(self.result["montants_par_exercice"]["2028-2029"]["risque_trois_catégories_mcad"],"44169")
    def test_11_2029_risk(self):self.assertEqual(self.result["montants_par_exercice"]["2029-2030"]["risque_trois_catégories_mcad"],"45313")
    def test_12_2030_risk(self):self.assertEqual(self.result["montants_par_exercice"]["2030-2031"]["risque_trois_catégories_mcad"],"46528")
    def test_13_2027_remaining_revenues(self):self.assertEqual(self.result["fiscal_2027_2028"]["revenus_restants_mcad"],"131350")
    def test_14_2027_deficit_with_base_measures(self):self.assertEqual(self.result["fiscal_2027_2028"]["solde_statique_si_retrait_sans_remplacement_avec_ecart_mcad"],"-48570")
    def test_15_2027_deficit_without_base_measures(self):self.assertEqual(self.result["fiscal_2027_2028"]["solde_statique_si_retrait_sans_remplacement_sans_ecart_mcad"],"-48570")
    def test_16_2028_conditional_gap(self):self.assertEqual(self.result["montants_par_exercice"]["2028-2029"]["solde_statique_si_retrait_sans_remplacement_avec_ecart_mcad"],"-45669")
    def test_17_2028_unmitigated_gap(self):self.assertEqual(self.result["montants_par_exercice"]["2028-2029"]["solde_statique_si_retrait_sans_remplacement_sans_ecart_mcad"],"-47519")
    def test_18_2029_conditional_gap(self):self.assertEqual(self.result["montants_par_exercice"]["2029-2030"]["solde_statique_si_retrait_sans_remplacement_avec_ecart_mcad"],"-45313")
    def test_19_2029_unmitigated_gap(self):self.assertEqual(self.result["montants_par_exercice"]["2029-2030"]["solde_statique_si_retrait_sans_remplacement_sans_ecart_mcad"],"-47313")
    def test_20_2030_conditional_gap(self):self.assertEqual(self.result["montants_par_exercice"]["2030-2031"]["solde_statique_si_retrait_sans_remplacement_avec_ecart_mcad"],"-46278")
    def test_21_2030_unmitigated_gap(self):self.assertEqual(self.result["montants_par_exercice"]["2030-2031"]["solde_statique_si_retrait_sans_remplacement_sans_ecart_mcad"],"-48278")
    def test_22_2027_no_cut_rate(self):self.assertIsNone(self.result["taux_nova_issus_de_ces_calculs"])
    def test_23_no_nova_budget(self):self.assertFalse(self.result["budget_nova_2027_2036_valide"])
    def test_24_no_sovereign_budget(self):self.assertFalse(self.result["budget_souverain_valide"])
    def test_25_no_tax_repeal_adopted(self):self.assertFalse(self.result["suppressions_fiscales_adoptees"])
    def test_26_p52b_unfilled(self):self.assertEqual(self.result["p52b_montants_manquants"],600)
    def test_27_p52d_unfilled(self):self.assertEqual(self.result["p52d_incidences_manquantes"],720)
    def test_28_xlsx_not_authenticated(self):self.assertFalse(self.result["simulateur_officiel_amende_feuille_verifiee"])
    def test_29_bulletin_not_implemented(self):self.assertFalse(self.result["mesures_bulletin_2026_7_chiffrees_et_en_vigueur"])
    def test_30_exact_2027_revenue_replacement(self):self.assertEqual(self.result["fiscal_2027_2028"]["besoin_remplacement_revenus_mcad"],"42875")
    def test_31_exact_2027_legal_balance_requirement(self):self.assertEqual(self.result["fiscal_2027_2028"]["ressources_pour_equilibre_loi_avec_ecart_mcad"],"48570")
    def test_32_bad_fss_exposure(self):
        d=self.clone();self.year(d,"2027-2028")["revenus_fss_mcad"]="9877";self.reject(d)
    def test_33_change_consumption_tax(self):
        d=self.clone();self.year(d,"2028-2029")["revenus_taxes_consommation_mcad"]="0";self.reject(d)
    def test_34_change_school_tax(self):
        d=self.clone();self.year(d,"2029-2030")["revenus_impot_foncier_scolaire_mcad"]="0";self.reject(d)
    def test_35_income_tax_is_not_new_taxable_base(self):
        d=self.clone();self.year(d,"2027-2028")["revenus_existants_impots_personnes_et_societes_mcad"]="100000";self.reject(d)
    def test_36_fake_nova_rate(self):
        d=self.clone();self.year(d,"2027-2028")["nouveaux_taux_fiscaux_nova"]="50";self.reject(d)
    def test_37_no_anti_paradis_fictitious_yield(self):
        d=self.clone();self.year(d,"2027-2028")["recettes_nouveau_prelevement_anti_paradis_mcad"]="4000";self.reject(d)
    def test_38_no_expense_cut_claim(self):
        d=self.clone();self.year(d,"2027-2028")["hypothese_statique_depenses_services_inchangees"]=False;self.reject(d)
    def test_39_cannot_assume_unfunded_2028_fix(self):
        d=self.clone();self.year(d,"2028-2029")["solde_budgetaire_theorique_sans_recettes_remplacement_sans_ecart_a_resorber_mcad"]="-45669";self.reject(d)
    def test_40_no_auto_federal_transfer_sovereignty(self):
        d=self.clone();d["perimetres"]["QUEBEC_SOUVERAIN"]["transferts_federaux_montants_automatiquement_conserves"]=True;self.reject(d)
    def test_41_no_sovereign_budget(self):
        d=self.clone();d["perimetres"]["QUEBEC_SOUVERAIN"]["budget_souverain_decennal_etabli"]=True;self.reject(d)
    def test_42_no_unilateral_federal_tax_abolition(self):
        d=self.clone();d["perimetres"]["QUEBEC_DANS_CANADA"]["recettes_federales_non_supprimables_unilateralement"]=False;self.reject(d)
    def test_43_excel_not_read_cannot_claim_verification(self):
        d=self.clone();d["sources"]["SIMULATEUR_AMENDE_OFFICIEL"]["feuille_amendement_lue"]=True;self.reject(d)
    def test_44_excel_hash_not_invented(self):
        d=self.clone();d["sources"]["SIMULATEUR_AMENDE_OFFICIEL"]["empreinte_sha256"]="abc";self.reject(d)
    def test_45_bulletin_not_already_law(self):
        d=self.clone();d["sources"]["BULLETIN_FISCAL_2026_7"]["mesures_adoptees_et_en_vigueur"]=True;self.reject(d)
    def test_46_bulletin_no_assumed_revenue_effect(self):
        d=self.clone();d["sources"]["BULLETIN_FISCAL_2026_7"]["courant_budget_2027_2031_revise_mcad"]="100";self.reject(d)
    def test_47_no_fabricated_expert(self):
        d=self.clone();d["integration"]["avis_independants_signes"]=1;self.reject(d)
    def test_48_no_fake_maturity(self):
        d=self.clone();d["integration"]["p55n_score_estimatif_pourcent"]=67;self.reject(d)
    def test_49_no_fake_future_budget(self):
        d=self.clone(2);d["regimes"]["QUEBEC_DANS_CANADA"]["trajectoires"]["central"][0]["recettes"]["impot_revenu_net"]="1000";self.reject(d,2)
    def test_50_no_fake_source_number(self):
        d=self.clone(1);d["annees_historique_et_previsions"][2]["revenus"]["taxes_consommation"]="0";self.reject(d,1)
    def test_51_no_fake_closed_proof(self):
        d=self.clone();self.one(d,"Q01")["statut"]="FERME";self.reject(d)
    def test_52_no_published_claim_altering_control(self):
        d=self.clone();d["regles_usage"]["aucune_suppression_reelle_de_recettes_ou_de_services"]=False;self.reject(d)
    def test_53_cli_json_no_overwrite(self):
        args=[sys.executable,str(SRC),"--pont",str(FILES[0]),"--p56p",str(FILES[1]),
              "--p52b",str(FILES[2]),"--barometre",str(FILES[3]),"--p56o",str(FILES[4])]
        ret=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(ret.returncode,0,ret.stderr)
        self.assertEqual(json.loads(ret.stdout)["fiscal_2027_2028"]["risque_trois_catégories_mcad"],"42875")
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/"report.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(out)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(out)],capture_output=True).returncode,2)
    def test_54_cli_refuses_certified_budget(self):
        args=[sys.executable,str(SRC),"--pont",str(FILES[0]),"--p56p",str(FILES[1]),
              "--p52b",str(FILES[2]),"--barometre",str(FILES[3]),"--p56o",str(FILES[4]),
              "--exiger-budget-nova-certifie"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
