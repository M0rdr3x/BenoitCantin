"""P56T : tests de concordance des dépenses sectorielles sans double comptage."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/verifier_soutenabilite_services_et_depenses_nova_p56t.py"
FILES=[
ROOT/"projets/projet-nova/etudes/P56T_BASE_OFFICIELLE_DEPENSES_PORTEFEUILLES_2025_2029_PROTECTION_SERVICES.json",
ROOT/"projets/projet-nova/etudes/P56P_BASE_BUDGET_PREELECTORALE_2026_2031_VGQ_ET_ECARTS.json",
ROOT/"projets/projet-nova/etudes/P56S_TROIS_OPTIONS_FISCALES_2027_2031_ET_CONDITIONS_PROTECTION.json",
ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
]
spec=importlib.util.spec_from_file_location("p56t",SCRIPT)
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class TestP56T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=[json.loads(f.read_text(encoding="utf-8")) for f in FILES]
        cls.report=p.auditer(*cls.data)
    def fresh(self,n=0):return copy.deepcopy(self.data[n])
    def reject(self,mutated,n=0):
        args=list(self.data);args[n]=mutated
        with self.assertRaises(ValueError):p.auditer(*args)
    def row(self,d,year):
        return next(x for x in d["annees"] if x["exercice"]==year)
    def cat(self,d,key):
        return next(x for x in d["categories"] if x["id"]==key)
    def test_01_jalon(self):self.assertEqual(self.report["jalon"],"P56T")
    def test_02_2027_year(self):self.assertEqual(self.report["annee_pivot"],"2027-2028")
    def test_03_2025_total(self):self.assertEqual(self.report["annees"]["2025-2026"]["total_portefeuilles_publics_mcad"],"155782")
    def test_04_2026_total(self):self.assertEqual(self.report["annees"]["2026-2027"]["total_portefeuilles_publics_mcad"],"161081")
    def test_05_2027_total(self):self.assertEqual(self.report["annees"]["2027-2028"]["total_portefeuilles_publics_mcad"],"165049")
    def test_06_2028_total(self):self.assertEqual(self.report["annees"]["2028-2029"]["total_portefeuilles_publics_mcad"],"166666")
    def test_07_2027_four_core(self):self.assertEqual(self.report["sante_education_superieur_famille_mcad"],"120433")
    def test_08_2027_seven_core(self):self.assertEqual(self.report["annees"]["2027-2028"]["sept_portefeuilles_services_mcad"],"140657")
    def test_09_2028_four_core(self):self.assertEqual(self.report["annees"]["2028-2029"]["quatre_portefeuilles_sante_education_superieur_famille_mcad"],"123776")
    def test_10_explicit_negative_reallocation(self):self.assertEqual(self.report["annees"]["2027-2028"]["reallocation_mcad"],"-600")
    def test_11_score_53(self):self.assertEqual(self.report["score_estime_pourcent"],53)
    def test_12_points_left(self):self.assertEqual(self.report["points_estimés_restants"],47)
    def test_13_not_certified(self):self.assertFalse(self.report["chiffres_source_certifies_comme_depenses_nova"])
    def test_14_no_tax_plan(self):self.assertFalse(self.report["politique_fiscale_nova_chiffree"])
    def test_15_no_services_funding_certification(self):self.assertFalse(self.report["services_publics_proteges_et_finances_par_nova_demontres"])
    def test_16_p52b_unknown(self):self.assertEqual(self.report["budgets_nova_p52b_manquants"],600)
    def test_17_p52d_unknown(self):self.assertEqual(self.report["incidences_p52d_manquantes"],720)
    def test_18_p52a_unknown(self):self.assertEqual(self.report["preuves_p52a_non_validees"],20)
    def test_19_gates(self):self.assertEqual(self.report["conditions_non_demontrees"],10)
    def test_20_no_go(self):self.assertEqual(self.report["decision"],"NO_GO_AUTOMATIQUE")
    def test_21_falsify_pdf_url(self):
        x=self.fresh();x["source"]["url"]="https://example.invalid";self.reject(x)
    def test_22_falsify_pdf_page(self):
        x=self.fresh();x["source"]["page_pdf_index_zero"]=27;self.reject(x)
    def test_23_falsify_2027_health(self):
        x=self.fresh();self.cat(x,"SANTE")["montants_par_exercice_mcad"]["2027-2028"]="72745";self.reject(x)
    def test_24_falsify_2026_education(self):
        x=self.fresh();self.row(x,"2026-2027")["depenses_portefeuilles_mcad"]["EDUCATION"]="20000";self.reject(x)
    def test_25_falsify_2028_other(self):
        x=self.fresh();self.row(x,"2028-2029")["depenses_portefeuilles_mcad"]["AUTRES"]="0";self.reject(x)
    def test_26_remove_reallocation(self):
        x=self.fresh();self.row(x,"2027-2028")["depenses_portefeuilles_mcad"]["REALLOCATION"]="0";self.reject(x)
    def test_27_doublecount_debt(self):
        x=self.fresh();self.row(x,"2027-2028")["total_portefeuilles_publie_mcad"]="175919";self.reject(x)
    def test_28_fake_sector_savings(self):
        x=self.fresh();self.row(x,"2027-2028")["economies_nova_reelles_certifiees_mcad"]="4000";self.reject(x)
    def test_29_fake_service_funding(self):
        x=self.fresh();self.row(x,"2027-2028")["cout_de_continuite_nova_propre_non_mesure_mcad"]="0";self.reject(x)
    def test_30_fake_public_workers(self):
        x=self.fresh();self.row(x,"2027-2028")["emploi_public_maintenu_economiquement_demontre"]=True;self.reject(x)
    def test_31_claim_sovereign_financed(self):
        x=self.fresh();x["perimetre"]["services_regime_souverain_estimes"]=True;self.reject(x)
    def test_32_invent_future_2029_2037(self):
        x=self.fresh();x["perimetre"]["annees_horizon_nova_non_couvertes"]=[];self.reject(x)
    def test_33_fake_independent_review(self):
        x=self.fresh();x["validation"]["avis_externes_nova_signes"]=1;self.reject(x)
    def test_34_fake_project_score(self):
        x=self.fresh();x["validation"]["score_estime"]=95;self.reject(x)
    def test_35_gates_cannot_close(self):
        x=self.fresh();x["points_critiques"][0]["validation"]="OBTENUE";self.reject(x)
    def test_36_modified_original_source(self):
        x=self.fresh(1);x["annees_historique_et_previsions"][2]["depenses_portefeuilles_mcad"]="165050";self.reject(x,1)
    def test_37_modified_comparison_source(self):
        x=self.fresh(2);x["options"][2]["resultats_par_exercice"][0]["recettes_retirees_uniquement_dans_le_test_mcad"]="40000.00";self.reject(x,2)
    def test_38_modified_barometer(self):
        x=self.fresh(4);x["score_estimatif"]=75;self.reject(x,4)
    def test_39_wrong_source_counts(self):
        x=self.fresh();self.row(x,"2027-2028")["noyau_sante_education_superieur_famille_mcad"]="125000";self.reject(x)
    def test_40_cli_json_and_no_overwrite(self):
        args=[sys.executable,str(SCRIPT),"--secteurs",str(FILES[0]),"--p56p",str(FILES[1]),
              "--p56s",str(FILES[2]),"--p56o",str(FILES[3]),"--barometre",str(FILES[4])]
        r=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)["sante_education_superieur_famille_mcad"],"120433")
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"result.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(output)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(output)],capture_output=True).returncode,2)
    def test_41_cli_refuse_finished_services(self):
        args=[sys.executable,str(SCRIPT),"--secteurs",str(FILES[0]),"--p56p",str(FILES[1]),
              "--p56s",str(FILES[2]),"--p56o",str(FILES[3]),"--barometre",str(FILES[4]),
              "--declarer-services-finances"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":unittest.main()
