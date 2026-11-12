"""P56P : vérifie l'ancrage officiel août/septembre 2026, sans prétendre un budget Nova."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"scripts/rapprocher_rapport_preelectoral_2026_nova_p56p.py"
FILES=[
ROOT/"projets/projet-nova/etudes/P56P_BASE_BUDGET_PREELECTORALE_2026_2031_VGQ_ET_ECARTS.json",
ROOT/"projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json",
ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json",
ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json"
]
spec=importlib.util.spec_from_file_location("p56p",SRC)
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

class TestP56P(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items=[json.loads(f.read_text(encoding="utf-8")) for f in FILES]
        cls.result=a.assess(*cls.items)
    def changed(self,i=0):
        return copy.deepcopy(self.items[i])
    def reject(self,mutated,i=0):
        args=list(self.items)
        args[i]=mutated
        with self.assertRaises(ValueError):
            a.assess(*args)
    def year(self,data,y):
        return next(x for x in data["annees_historique_et_previsions"] if x["exercice"]==y)
    def risk(self,data,id):
        return next(x for x in data["observations_pertinentes"]["sensibilites_risques_publics_rapport_tableau_13"] if x["id"]==id)
    def test_01_jalon(self):self.assertEqual(self.result["jalon"],"P56P")
    def test_02_source(self):self.assertEqual(self.result["source"],"RAPPORT_PREELECTORAL_2026_AOUT_TABLEAU_2")
    def test_03_six_fiscal_years(self):self.assertEqual(self.result["annees_source_count"],6)
    def test_04_first_audited(self):self.assertTrue(self.result["donnees_2025_2026_auditees"])
    def test_05_vgq_scope_3_years(self):
        self.assertEqual(self.result["annees_previsions_considerees_plausibles_vgq"],
                         ["2026-2027","2027-2028","2028-2029"])
    def test_06_later_years_outside_vgq(self):
        self.assertEqual(self.result["annees_2029_2031_hors_examens_vgq"],["2029-2030","2030-2031"])
    def test_07_2026_revenue(self):self.assertEqual(self.result["previsions_gouv_2026_2027_revenus_mcad"],"168389")
    def test_08_2026_expense(self):self.assertEqual(self.result["previsions_gouv_2026_2027_depenses_sans_provision_mcad"],"171597")
    def test_09_2027_revenue(self):self.assertEqual(self.result["previsions_gouv_2027_2028_revenus_mcad"],"174225")
    def test_10_2027_expense(self):self.assertEqual(self.result["previsions_gouv_2027_2028_depenses_sans_provision_mcad"],"175919")
    def test_11_delta_march_aug_revenues(self):self.assertEqual(self.result["ecart_Mars_Aout_revenus_2026_27_mcad"],"1897")
    def test_12_delta_march_aug_expenses(self):self.assertEqual(self.result["ecart_Mars_Aout_depenses_2026_27_mcad"],"840")
    def test_13_q1_september_confirmation(self):
        self.assertTrue(self.result["rapport_trimestriel_2026_27_confirme_cadre_aout"])
    def test_14_2025_statutory_deficit(self):self.assertEqual(self.result["solde_loi_par_annee_mcad"]["2025-2026"],"-7791")
    def test_15_2026_statutory_deficit(self):self.assertEqual(self.result["solde_loi_par_annee_mcad"]["2026-2027"],"-7690")
    def test_16_2027_statutory_deficit(self):self.assertEqual(self.result["solde_loi_par_annee_mcad"]["2027-2028"],"-5695")
    def test_17_2028_statutory_deficit(self):self.assertEqual(self.result["solde_loi_par_annee_mcad"]["2028-2029"],"-1500")
    def test_18_2029_conditional_balance(self):self.assertEqual(self.result["solde_loi_par_annee_mcad"]["2029-2030"],"0")
    def test_19_2030_conditional_surplus(self):self.assertEqual(self.result["solde_loi_par_annee_mcad"]["2030-2031"],"250")
    def test_20_2028_unfunded_gap(self):self.assertEqual(self.result["ecarts_a_resorber_par_annee_mcad"]["2028-2029"],"1850")
    def test_21_2029_unfunded_gap(self):self.assertEqual(self.result["ecarts_a_resorber_par_annee_mcad"]["2029-2030"],"2000")
    def test_22_2030_unfunded_gap(self):self.assertEqual(self.result["ecarts_a_resorber_par_annee_mcad"]["2030-2031"],"2000")
    def test_23_5850_cumulative_conditional(self):self.assertEqual(self.result["ecarts_conditionnels_2028_2031_mcad"],"5850")
    def test_24_missing_p52b_600(self):self.assertEqual(self.result["p52b_montants_encore_inconnus"],600)
    def test_25_missing_p52d_720(self):self.assertEqual(self.result["p52d_incidences_encore_inconnues"],720)
    def test_26_missing_p52a_20(self):self.assertEqual(self.result["p52a_preuves_encore_non_validees"],20)
    def test_27_score_53(self):self.assertEqual(self.result["score_estime_pourcent"],53)
    def test_28_no_nova_budget(self):self.assertFalse(self.result["budget_nova_adopte"])
    def test_29_no_sovereign_budget(self):self.assertTrue(self.result["aucun_bilan_souverain_p56p"])
    def test_30_no_go(self):self.assertEqual(self.result["decision"],"NO_GO_AUTOMATIQUE")
    def test_31_change_pdf_link(self):
        d=self.changed();d["sources"]["RAPPORT_PREELECTORAL"]["url"]="https://fake.example/pdf";self.reject(d)
    def test_32_change_quarterly_link(self):
        d=self.changed();d["sources"]["RAPPORT_TRIMESTRIEL"]["url"]="https://example.org/report";self.reject(d)
    def test_33_hide_vgq_scope(self):
        d=self.changed();d["sources"]["EXAMEN_VGQ"]["portee_annees"].append("2029-2030");self.reject(d)
    def test_34_claim_outlook_guarantee(self):
        d=self.changed();d["sources"]["EXAMEN_VGQ"]["ne_certifie_pas_realisation_previsions"]=False;self.reject(d)
    def test_35_false_2025_projection(self):
        d=self.changed();self.year(d,"2025-2026")["categorie"]="PREVISION_GOUVERNEMENT_AOUT_2026";self.reject(d)
    def test_36_false_2029_vgq_examination(self):
        d=self.changed();self.year(d,"2029-2030")["portee_certification_vgq"]="HYPOTHESES_ET_PREVISIONS_PLAUSIBLES_AU_10_JUILLET_2026_NON_GARANTIES";self.reject(d)
    def test_37_increase_people_tax(self):
        d=self.changed();self.year(d,"2027-2028")["revenus"]["impot_particuliers"]="52842";self.reject(d)
    def test_38_fake_corporation_tax(self):
        d=self.changed();self.year(d,"2028-2029")["revenus"]["impots_societes"]="16000";self.reject(d)
    def test_39_fake_federal_transfer(self):
        d=self.changed();self.year(d,"2027-2028")["transferts_federaux_mcad"]="35011";self.reject(d)
    def test_40_double_count_debt(self):
        d=self.changed();self.year(d,"2026-2027")["total_depenses_hors_provision_mcad"]="182113";self.reject(d)
    def test_41_remove_contingency(self):
        d=self.changed();self.year(d,"2026-2027")["provision_eventualites_mcad"]="0";self.reject(d)
    def test_42_remove_unfunded_2028_gap(self):
        d=self.changed();self.year(d,"2028-2029")["ecart_a_resorber_non_finance_par_mesures_identifiees_mcad"]="0";self.reject(d)
    def test_43_remove_2029_gap(self):
        d=self.changed();self.year(d,"2029-2030")["ecart_a_resorber_non_finance_par_mesures_identifiees_mcad"]="0";self.reject(d)
    def test_44_fake_statutory_surplus(self):
        d=self.changed();self.year(d,"2029-2030")["solde_budgetaire_selon_loi_mcad"]="2000";self.reject(d)
    def test_45_fake_accounting_after_gap(self):
        d=self.changed();d["observations_pertinentes"]["solde_comptable_2028_2029_apres_resorption_theorique_mcad"]="1125";self.reject(d)
    def test_46_old_2026_reference_must_match_p52b(self):
        d=self.changed();d["reconciliation_mars_vs_aout_2026_2027"]["ancienne_reference_mars_2026_2027"]["revenus_consolides_mcad"]="170000";self.reject(d)
    def test_47_false_difference(self):
        d=self.changed();d["reconciliation_mars_vs_aout_2026_2027"]["variations_aout_moins_mars"]["revenus_consolides_mcad"]="0";self.reject(d)
    def test_48_false_q1_nonaudited_income(self):
        d=self.changed();d["observation_trimestrielle_au_30_juin_2026"]["revenus_avril_juin_mcad"]="50000";self.reject(d)
    def test_49_q1_quarter_not_full_year(self):
        d=self.changed();d["observation_trimestrielle_au_30_juin_2026"]["n_est_pas_un_quart_de_la_prevision_annuelle"]=False;self.reject(d)
    def test_50_risk_interests_no_double_count(self):
        d=self.changed();self.risk(d,"RISQUE_INTERETS")["impact_service_dette_annuel_mcad"]="1280";self.reject(d)
    def test_51_no_risk_as_certified_nova_gain(self):
        d=self.changed();d["observations_pertinentes"]["economie_nova_non_identifiee_pour_les_ecarts_mcad"]="5850";self.reject(d)
    def test_52_no_amended_xlsx_certification(self):
        d=self.changed();d["sources"]["OUTIL_SIMULATION_AMENDE"]["contenu_tableur_verifie_par_P56P"]=True;self.reject(d)
    def test_53_no_main(self):
        d=self.changed();d["integration_nova"]["main_modifiee"]=True;self.reject(d)
    def test_54_no_new_p52b_rows(self):
        d=self.changed();d["integration_nova"]["nombre_cellules_P52B_modifiees"]=30;self.reject(d)
    def test_55_no_fabricated_proof(self):
        d=self.changed();d["livrables_manquants"][0]["statut"]="TERMINE";self.reject(d)
    def test_56_false_maturity(self):
        d=self.changed();d["integration_nova"]["score_estimatif_pourcent"]=70;self.reject(d)
    def test_57_mutate_actual_p52b(self):
        d=self.changed(1);d["reference_2026_2027"]["revenus_consolides"]="170.000";self.reject(d,1)
    def test_58_mutate_score_p55n(self):
        d=self.changed(2);d["score_estimatif"]=100;self.reject(d,2)
    def test_59_mutate_p56o_gates(self):
        d=self.changed(3);d["portes"][0]["statut"]="PROUVE";self.reject(d,3)
    def test_60_cli_valid_json_and_no_overwrite(self):
        args=[sys.executable,str(SRC),"--base",str(FILES[0]),
              "--p52b",str(FILES[1]),"--barometre",str(FILES[2]),
              "--p56o",str(FILES[3])]
        r=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)["ecarts_conditionnels_2028_2031_mcad"],"5850")
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"report.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(out)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(out)],capture_output=True).returncode,2)
    def test_61_cli_refuses_certified_budget(self):
        args=[sys.executable,str(SRC),"--base",str(FILES[0]),
              "--p52b",str(FILES[1]),"--barometre",str(FILES[2]),
              "--p56o",str(FILES[3]),"--exiger-budget-nova-certifie"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
