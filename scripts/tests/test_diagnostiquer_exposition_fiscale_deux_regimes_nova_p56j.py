"""P56J : tests du chiffrage historique des recettes à remplacer, sans taux Nova fictif."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"scripts/diagnostiquer_exposition_fiscale_deux_regimes_nova_p56j.py"
D=ROOT/"projets/projet-nova/etudes/P56J_DIAGNOSTIC_RECETTES_A_REMPLACER_DEUX_REGIMES_2025_2026.json"
C=ROOT/"projets/projet-nova/etudes/P56C_TABLE_PASSAGE_COMPTES_PUBLICS_VERS_P52B_2025_2026.json"
B=ROOT/"projets/projet-nova/etudes/P56B_SNAPSHOTS_FINANCES_2025_2026_SOURCES_OFFICIELLES.json"
M=ROOT/"projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json"
E=ROOT/"projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json"
N=ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"

spec=importlib.util.spec_from_file_location("p56j",SRC)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestsP56J(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=[json.loads(x.read_text(encoding="utf-8")) for x in (D,C,B,M,E,N)]
        cls.report=mod.audit(*cls.inputs)
    def altered(self,idx=0):
        return copy.deepcopy(self.inputs[idx])
    def reject(self,idx,edited):
        args=list(self.inputs)
        args[idx]=edited
        with self.assertRaises(ValueError):
            mod.audit(*args)
    def group(self,d,key):
        return next(x for x in d["groupes_de_repartition"] if x["id"]==key)
    def test_01_schema(self):self.assertEqual(self.report["schema_version"],"P56J-1")
    def test_02_historical_year(self):self.assertEqual(self.report["exercice_source"],"2025-2026")
    def test_03_income_tax_person_corporate(self):
        self.assertEqual(self.report["groupes_historique_mcad"]["IMPOTS_REVENU_EXISTANTS"],"63568")
    def test_04_removed_three_categories(self):
        self.assertEqual(self.report["groupes_historique_mcad"]["PRELEVEMENTS_EXISTANTS_A_REMPLACER_SI_ABOLIS"],"40186")
    def test_05_mixed_uncertain(self):
        self.assertEqual(self.report["groupes_historique_mcad"]["RECETTES_MIXTES_A_CLARIFIER"],"26871")
    def test_06_federal(self):
        self.assertEqual(self.report["groupes_historique_mcad"]["TRANSFERTS_FEDERAUX_DANS_CANADA"],"29803")
    def test_07_revenues(self):self.assertEqual(self.report["revenus_consolides_constates_mcad"],"160428")
    def test_08_spending(self):self.assertEqual(self.report["depenses_consolidees_constatees_mcad"],"165930")
    def test_09_accounting_deficit(self):
        self.assertEqual(self.report["deficit_comptable_constate_mcad"],"5502")
    def test_10_counterfactual_revenues(self):
        self.assertEqual(self.report["revenus_restants_si_trois_groupes_supprimes_mcad"],"120242")
    def test_11_counterfactual_deficit(self):
        self.assertEqual(self.report["deficit_comptable_mecanique_sans_substitution_mcad"],"45688")
    def test_12_original_replacement_sum(self):
        self.assertEqual(self.report["recettes_a_remplacer_pour_revenir_au_niveau_historique_mcad"],"40186")
    def test_13_balance_gap_mechanical(self):
        self.assertEqual(self.report["recettes_additionnelles_mecaniques_pour_equilibre_comptable_mcad"],"45688")
    def test_14_no_claim_funding(self):
        self.assertEqual(self.report["deficit_comptable_initial_non_elimine_si_substitution_integrale_mcad"],"5502")
    def test_15_arithmetic_identity(self):
        v=self.report
        self.assertEqual(int(v["revenus_consolides_constates_mcad"])-int(v["groupes_historique_mcad"]["PRELEVEMENTS_EXISTANTS_A_REMPLACER_SI_ABOLIS"]),int(v["revenus_restants_si_trois_groupes_supprimes_mcad"]))
    def test_16_no_income_tax_rate(self):self.assertTrue(self.report["ces_sommes_ne_sont_pas_un_taux_fiscal"])
    def test_17_no_adoption(self):self.assertTrue(self.report["ces_sommes_ne_sont_pas_un_budget_adopte"])
    def test_18_no_sovereignty_budget(self):self.assertTrue(self.report["ces_sommes_ne_sont_pas_un_budget_souverain"])
    def test_19_no_anti_evasion_gain(self):
        self.assertEqual(self.report["anti_evasion_recouvrement_non_certifie_mcad"],"0")
    def test_20_no_tax_expenditure_redistribution(self):
        self.assertTrue(self.report["depenses_fiscales_estimees_non_ajoutees_comme_recettes"])
    def test_21_no_2027_2036_inputs(self):self.assertEqual(self.report["cellules_p52b_renseignees_2027_2036"],0)
    def test_22_seventeen_evidence_gates(self):self.assertEqual(self.report["preuves_obligatoires_a_obtenir"],17)
    def test_23_zero_sovereign_scenarios(self):self.assertEqual(self.report["scenarios_souverains_financiers_chiffres"],0)
    def test_24_no_household_analysis(self):self.assertFalse(self.report["incidence_sur_menages_et_entreprises_chiffree"])
    def test_25_no_services_financing(self):self.assertFalse(self.report["garantie_services_municipaux_sante_education_validee"])
    def test_26_no_independent_advice(self):self.assertFalse(self.report["avis_independants_verifies"])
    def test_27_maturity(self):self.assertEqual(self.report["p55n_score_estimatif_pourcent"],53)
    def test_28_missing_points(self):self.assertEqual(self.report["p55n_points_restants_estimes"],47)
    def test_29_no_go(self):self.assertEqual(self.report["decision"],"NO_GO_AUTOMATIQUE")
    def test_30_misclass_fss_to_income(self):
        d=self.altered();self.group(d,"IMPOTS_REVENU_EXISTANTS")["postes_p56c"].append("cotisations_services_sante")
        self.reject(0,d)
    def test_31_misclass_federal_as_income(self):
        d=self.altered();self.group(d,"TRANSFERTS_FEDERAUX_DANS_CANADA")["postes_p56c"]=[]
        self.reject(0,d)
    def test_32_double_count_consumption(self):
        d=self.altered();self.group(d,"RECETTES_MIXTES_A_CLARIFIER")["postes_p56c"].append("taxes_consommation")
        self.reject(0,d)
    def test_33_fake_abolition(self):
        d=self.altered();d["contre_factuel"]["supprime_effectivement_les_prelevements"]=True
        self.reject(0,d)
    def test_34_keep_costs_in_static_model(self):
        d=self.altered();d["contre_factuel"]["aucun_montant_depenses_supprime"]=False
        self.reject(0,d)
    def test_35_no_assumed_anti_evasion(self):
        d=self.altered();d["contre_factuel"]["revenus_anti_evasion_supposes_nets_mcad"]="5000"
        self.reject(0,d)
    def test_36_no_federal_gst_abolition(self):
        d=self.altered();d["regimes"]["QUEBEC_DANS_CANADA"]["federal_TPS_et_impot_demeurent"]=False
        self.reject(0,d)
    def test_37_no_sovereignty_transfer(self):
        d=self.altered();d["regimes"]["QUEBEC_SOUVERAIN"]["transferts_federaux_continues_mcad"]="29803"
        self.reject(0,d)
    def test_38_no_sovereign_spending_estimate(self):
        d=self.altered();d["regimes"]["QUEBEC_SOUVERAIN"]["defense_frontieres_dette_pensions_couts_mcad"]="0"
        self.reject(0,d)
    def test_39_no_tax_base_invented(self):
        d=self.altered();d["contre_factuel"]["base_de_calcul_taux_imposition_candidat"]="100000"
        self.reject(0,d)
    def test_40_no_false_evidence(self):
        d=self.altered();d["preuves_a_obtenir"][0]["statut"]="OBTENU"
        self.reject(0,d)
    def test_41_no_false_expert_review(self):
        d=self.altered();d["avis_independant_nova"]=True
        self.reject(0,d)
    def test_42_no_false_maturity(self):
        d=self.altered();d["p55n_score_estimatif"]=75
        self.reject(0,d)
    def test_43_no_fake_source_revenue(self):
        x=self.altered(1)
        next(i for i in x["poste_sources"] if i["id"]=="taxes_consommation")["montant_audite_mcad"]="29640"
        self.reject(1,x)
    def test_44_no_fake_projections(self):
        d=self.altered();d["projections_p52b_alterees"]=True
        self.reject(0,d)
    def test_45_no_false_barometer(self):
        d=self.altered(5);d["score_estimatif"]=99
        self.reject(5,d)
    def test_46_no_auto_tax_cut(self):
        d=self.altered();d["conditions_prudence"]["autorisation_automatique"]=True
        self.reject(0,d)
    def test_47_no_false_budget_year(self):
        d=self.altered();d["contre_factuel"]["annee_cible_p52b"]=2027
        self.reject(0,d)
    def test_48_cli_json_and_no_overwrite(self):
        args=[sys.executable,str(SRC),"--diagnostic",str(D),
              "--p56c",str(C),"--p56b",str(B),"--gabarit",str(M),
              "--preuves",str(E),"--barometre",str(N)]
        result=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)["deficit_comptable_mecanique_sans_substitution_mcad"],"45688")
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"result.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(target)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(target)],capture_output=True).returncode,2)
    def test_49_cli_refuses_rate_certification(self):
        result=subprocess.run([sys.executable,str(SRC),"--diagnostic",str(D),
              "--p56c",str(C),"--p56b",str(B),"--gabarit",str(M),
              "--preuves",str(E),"--barometre",str(N),"--exiger-taux-certifie"],capture_output=True)
        self.assertEqual(result.returncode,3)

if __name__=="__main__":
    unittest.main()
