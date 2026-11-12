"""P56V: tests de concordance financiére 2027-2029 et garde-fous VGQ."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
PY=ROOT/"scripts/verifier_pont_financement_services_nova_p56v.py"
FILES=[
ROOT/"projets/projet-nova/etudes/P56V_PONT_FINANCEMENT_SERVICES_OPTIONS_FISCALES_VGQ_2027_2029.json",
ROOT/"projets/projet-nova/etudes/P56P_BASE_BUDGET_PREELECTORALE_2026_2031_VGQ_ET_ECARTS.json",
ROOT/"projets/projet-nova/etudes/P56S_TROIS_OPTIONS_FISCALES_2027_2031_ET_CONDITIONS_PROTECTION.json",
ROOT/"projets/projet-nova/etudes/P56T_BASE_OFFICIELLE_DEPENSES_PORTEFEUILLES_2025_2029_PROTECTION_SERVICES.json",
ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
]
spec=importlib.util.spec_from_file_location("p56v",PY)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestP56V(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=[json.loads(p.read_text(encoding="utf-8")) for p in FILES]
        cls.report=mod.audit(*cls.data)
    def clone(self,i=0):return copy.deepcopy(self.data[i])
    def reject(self,d,i=0):
        data=list(self.data);data[i]=d
        with self.assertRaises(ValueError):mod.audit(*data)
    def row(self,d,year):
        return next(x for x in d["comptes_par_annee"] if x["exercice"]==year)
    def option(self,d,year,key):
        return next(x for x in self.row(d,year)["options"] if x["id"]==key)

    def test_01_stage(self):self.assertEqual(self.report["jalon"],"P56V")
    def test_02_score(self):self.assertEqual(self.report["score_estime_pourcent"],53)
    def test_03_rest(self):self.assertEqual(self.report["points_restants_estimes"],47)
    def test_04_years(self):self.assertEqual(self.report["annees_couvertes"],["2027-2028","2028-2029"])
    def test_05_first_portfolios(self):self.assertEqual(self.report["financement"]["2027-2028"]["depenses_portefeuilles_mcad"],"165049")
    def test_06_first_core(self):self.assertEqual(self.report["financement"]["2027-2028"]["quatre_portefeuilles_services_mcad"],"120433")
    def test_07_first_total_spend(self):self.assertEqual(self.report["financement"]["2027-2028"]["depenses_totales_hors_provision_mcad"],"175919")
    def test_08_second_portfolios(self):self.assertEqual(self.report["financement"]["2028-2029"]["depenses_portefeuilles_mcad"],"166666")
    def test_09_second_core(self):self.assertEqual(self.report["financement"]["2028-2029"]["quatre_portefeuilles_services_mcad"],"123776")
    def test_10_second_total_spend(self):self.assertEqual(self.report["financement"]["2028-2029"]["depenses_totales_hors_provision_mcad"],"178068")
    def test_11_vgq_2027(self):self.assertEqual(self.report["financement"]["2027-2028"]["efforts_budgetaires_vgq_minimum_estime_mcad"],"2000")
    def test_12_vgq_2028(self):self.assertEqual(self.report["financement"]["2028-2029"]["efforts_budgetaires_vgq_minimum_estime_mcad"],"3000")
    def test_13_2028_unfunded(self):self.assertEqual(self.report["financement"]["2028-2029"]["ecart_a_resorber_mcad"],"1850")
    def test_14_baseline_2027_balance(self):self.assertEqual(self.report["financement"]["2027-2028"]["options"]["S1_CONTINUITE"]["solde_sans_financement_ni_resorption_mcad"],"-5695")
    def test_15_intermediate_2027_balance(self):self.assertEqual(self.report["financement"]["2027-2028"]["options"]["S2_TRANSITION_CONDITIONNELLE"]["solde_sans_financement_ni_resorption_mcad"],"-16413.75")
    def test_16_final_2027_balance(self):self.assertEqual(self.report["financement"]["2027-2028"]["options"]["S3_CIBLE_DEUX_PRELEVEMENTS"]["solde_sans_financement_ni_resorption_mcad"],"-48570")
    def test_17_final_2028_balance(self):self.assertEqual(self.report["financement"]["2028-2029"]["options"]["S3_CIBLE_DEUX_PRELEVEMENTS"]["solde_sans_financement_ni_resorption_mcad"],"-47519")
    def test_18_no_double_spend(self):self.assertTrue(self.report["efforts_vgq_non_additionnes_aux_depenses"])
    def test_19_no_services_certified(self):self.assertTrue(self.report["aucune_garantie_de_services_automatiquement_etablie"])
    def test_20_no_sovereign_budget(self):self.assertFalse(self.report["budget_souverain_certifie"])
    def test_21_not_done(self):self.assertFalse(self.report["budget_nova_certifie"])
    def test_22_no_go(self):self.assertEqual(self.report["decision"],"NO_GO_AUTOMATIQUE")
    def test_23_source_vgq_changed(self):
        d=self.clone();d["provenance"]["vgq"]["url"]="https://invented.example";self.reject(d)
    def test_24_minimum_2027_changed(self):
        d=self.clone();d["provenance"]["vgq"]["efforts_minimum_2027_2028_mcad"]="1000";self.reject(d)
    def test_25_vgq_did_not_assess_quality(self):
        d=self.clone();d["provenance"]["vgq"]["examen_qualite_ou_adequation_services"]=True;self.reject(d)
    def test_26_double_vgq_effort(self):
        d=self.clone();d["perimetre"]["effort_vgq_ne_pas_ajouter_une_seconde_fois_au_total_depenses"]=False;self.reject(d)
    def test_27_fake_sovereign(self):
        d=self.clone();d["perimetre"]["montants_souverainete_restant_inconnus"]=False;self.reject(d)
    def test_28_wrong_2027_portfolios(self):
        d=self.clone();self.row(d,"2027-2028")["depenses_portefeuilles_publics_mcad"]="165050";self.reject(d)
    def test_29_wrong_2027_debt(self):
        d=self.clone();self.row(d,"2027-2028")["service_dette_deja_compte_dans_total_mcad"]="21000";self.reject(d)
    def test_30_wrong_health_2028(self):
        d=self.clone();self.row(d,"2028-2029")["sous_total_sante_education_superieur_famille_inclus_portefeuilles_mcad"]="140000";self.reject(d)
    def test_31_false_2028_gap(self):
        d=self.clone();self.row(d,"2028-2029")["ecart_a_resorber_non_prouve_mcad"]="0";self.reject(d)
    def test_32_false_2028_sustained_balance(self):
        d=self.clone();self.row(d,"2028-2029")["solde_legal_sans_ecart_a_resorber_mcad"]="-1500";self.reject(d)
    def test_33_fake_services_quality(self):
        d=self.clone();self.row(d,"2027-2028")["qualite_et_quantite_services_suffisantes_demonstrees"]=True;self.reject(d)
    def test_34_fake_saving(self):
        d=self.clone();self.row(d,"2027-2028")["economie_nova_certifiee_mcad"]="2000";self.reject(d)
    def test_35_wrong_25percent_loss(self):
        d=self.clone();self.option(d,"2027-2028","S2_TRANSITION_CONDITIONNELLE")["retrait_recettes_fictif_mcad"]="10000.00";self.reject(d)
    def test_36_wrong_2028_no_resorption(self):
        d=self.clone();self.option(d,"2028-2029","S3_CIBLE_DEUX_PRELEVEMENTS")["solde_loi_sans_remplacement_ni_resorption_mcad"]="-45669.00";self.reject(d)
    def test_37_claim_anti_haven_yield(self):
        d=self.clone();self.option(d,"2027-2028","S3_CIBLE_DEUX_PRELEVEMENTS")["montant_reel_prelevement_anti_paradis_nova_mcad"]="5000.00";self.reject(d)
    def test_38_fake_new_nova_income_tax(self):
        d=self.clone();self.option(d,"2028-2029","S2_TRANSITION_CONDITIONNELLE")["montant_reel_prelevement_revenu_nova_mcad"]="20000.00";self.reject(d)
    def test_39_fake_gap_certification(self):
        d=self.clone();self.option(d,"2027-2028","S3_CIBLE_DEUX_PRELEVEMENTS")["option_autorisee"]=True;self.reject(d)
    def test_40_fake_professional_opinion(self):
        d=self.clone();d["indicateurs"]["avis_externes_nova_signes"]=1;self.reject(d)
    def test_41_false_100(self):
        d=self.clone();d["indicateurs"]["score_p55n_estime"]=100;self.reject(d)
    def test_42_fake_complete_gate(self):
        d=self.clone();d["conditions_d_acception"][0]["statut"]="DEMONTRE";self.reject(d)
    def test_43_source_2027_changed(self):
        d=self.clone(1);d["annees_historique_et_previsions"][2]["service_dette_deja_inclus_mcad"]="10871";self.reject(d,1)
    def test_44_source_2028_changed(self):
        d=self.clone(3);d["annees"][3]["noyau_sante_education_superieur_famille_mcad"]="123775";self.reject(d,3)
    def test_45_source_option_changed(self):
        d=self.clone(2);d["options"][2]["resultats_par_exercice"][0]["recettes_retirees_uniquement_dans_le_test_mcad"]="40000.00";self.reject(d,2)
    def test_46_cli_json_report_no_overwrite(self):
        args=[sys.executable,str(PY),"--pont",str(FILES[0]),"--p56p",str(FILES[1]),
              "--p56s",str(FILES[2]),"--p56t",str(FILES[3]),"--p56o",str(FILES[4]),
              "--barometre",str(FILES[5])]
        res=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(res.returncode,0,res.stderr)
        self.assertEqual(json.loads(res.stdout)["score_estime_pourcent"],53)
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"result.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(out)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(out)],capture_output=True).returncode,2)
    def test_47_cli_rejects_certification(self):
        args=[sys.executable,str(PY),"--pont",str(FILES[0]),"--p56p",str(FILES[1]),
              "--p56s",str(FILES[2]),"--p56t",str(FILES[3]),"--p56o",str(FILES[4]),
              "--barometre",str(FILES[5]),"--certifier-financement-nova"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
