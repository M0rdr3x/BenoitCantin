"""P56W: A15 credits 2023, ecarts d'arrondis et refus de gains fictifs Nova."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"scripts/verifier_credits_remboursables_protection_nova_p56w.py"
FILES=[
ROOT/"projets/projet-nova/etudes/P56W_CREDITS_REMBOURSABLES_2023_PAR_CATEGORIE_ET_TRANCHES_PROTECTION.json",
ROOT/"projets/projet-nova/etudes/P56L_BASE_DISTRIBUTIVE_PARTICULIERS_2023_CREDITS_ET_QUINTILES.json",
ROOT/"projets/projet-nova/etudes/P56V_PONT_FINANCEMENT_SERVICES_OPTIONS_FISCALES_VGQ_2027_2029.json",
ROOT/"projets/projet-nova/etudes/P56N_CAS_TYPES_2026_REFERENCES_OFFICIELLES_PRESTATIONS_ET_LIMITES.json",
ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
]
spec=importlib.util.spec_from_file_location("p56w",SRC)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestP56W(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=[json.loads(f.read_text(encoding="utf-8")) for f in FILES]
        cls.out=m.audit(*cls.d)
    def copy(self,index=0):return copy.deepcopy(self.d[index])
    def reject(self,x,index=0):
        data=list(self.d);data[index]=x
        with self.assertRaises(ValueError):m.audit(*data)
    def cat(self,x,key):
        return next(y for y in x["credits_par_categorie"] if y["id"]==key)
    def test_01_version(self):self.assertEqual(self.out["jalon"],"P56W")
    def test_02_year(self):self.assertEqual(self.out["millesime"],2023)
    def test_03_grand_total(self):self.assertEqual(self.out["credits_remboursables_officiels_mcad"],"9305")
    def test_04_low_group(self):self.assertEqual(self.out["credits_sous_30000_mcad"],"4201")
    def test_05_low_share(self):self.assertEqual(self.out["part_sous_30000_pourcent"],"45.1")
    def test_06_categories(self):self.assertEqual(self.out["nombre_categories"],13)
    def test_07_six_bins(self):self.assertEqual(self.out["nombre_tranches"],6)
    def test_08_total_credits_rows(self):self.assertEqual(self.out["somme_categories_arrondies_mcad"],"9306")
    def test_09_rounded_diff(self):self.assertEqual(self.out["ecart_arrondis_categories_mcad"],"1")
    def test_10_first_bin_rounding(self):self.assertEqual(self.out["ecarts_par_tranche_mcad"]["MOINS_10000"],"-1")
    def test_11_third_bin_rounding(self):self.assertEqual(self.out["ecarts_par_tranche_mcad"]["20000_29999"],"2")
    def test_12_sixth_bin_rounding(self):self.assertEqual(self.out["ecarts_par_tranche_mcad"]["100000_PLUS"],"-1")
    def test_13_no_future_certification(self):self.assertFalse(self.out["credits_2027_2036_nova_certifies"])
    def test_14_no_dpi_claim(self):self.assertFalse(self.out["gains_revenu_disponible_nova_certifies"])
    def test_15_no_budget_certified(self):self.assertFalse(self.out["budget_nova_certifie"])
    def test_16_score_not_inflated(self):self.assertEqual(self.out["score_estime_pourcent"],53)
    def test_17_remaining_47(self):self.assertEqual(self.out["points_restants_estimes"],47)
    def test_18_no_go(self):self.assertEqual(self.out["decision"],"NO_GO_AUTOMATIQUE")
    def test_19_wrong_2023_total(self):
        x=self.copy();x["controle_arrondis"]["ligne_totale_officielle_mcad"]="9306";self.reject(x)
    def test_20_wrong_2023_bins_total(self):
        x=self.copy();x["controle_arrondis"]["somme_credits_total_officielle_par_tranche_mcad"]="9305";self.reject(x)
    def test_21_delete_rounding_difference(self):
        x=self.copy();x["controle_arrondis"]["ecart_somme_tranches_publiees_moins_total_officiel_mcad"]="0";self.reject(x)
    def test_22_false_2023_to_2027(self):
        x=self.copy();x["règles_integrite"]["credits_2023_non_automatiquement_reconduits_a_2027"]=False;self.reject(x)
    def test_23_double_spending(self):
        x=self.copy();x["règles_integrite"]["credits_2023_non_additionnes_aux_depenses_portefeuilles_p56v"]=False;self.reject(x)
    def test_24_wrong_family_2023(self):
        x=self.copy();self.cat(x,"FAMILLE")["total_publie_mcad"]="3600";self.reject(x)
    def test_25_wrong_solidarity(self):
        x=self.copy();self.cat(x,"SOLIDARITE")["montants_par_tranche_mcad"]["20000_29999"]="700";self.reject(x)
    def test_26_wrong_seniors(self):
        x=self.copy();self.cat(x,"SOUTIEN_AINES")["montants_par_tranche_mcad"]["20000_29999"]="700";self.reject(x)
    def test_27_invent_low_income_people(self):
        x=self.copy();x["tranches"][0]["nombre_declarants_par_tranche"]=50000;self.reject(x)
    def test_28_invent_forecast_credit(self):
        x=self.copy();self.cat(x,"GARDE")["effet_nova_2027_2036_mcad"]="1100";self.reject(x)
    def test_29_claim_sovereign_rate(self):
        x=self.copy();x["controle_completion"]["nouveaux_taux_nova_adoptes"]=1;self.reject(x)
    def test_30_false_score(self):
        x=self.copy();x["controle_completion"]["score_estime_p55n"]=100;self.reject(x)
    def test_31_wrong_A15(self):
        x=self.copy();x["provenance"]["fiscal_a15"]["url"]="https://bogus.example";self.reject(x)
    def test_32_invent_household_transfer(self):
        x=self.copy();self.cat(x,"MAINTIEN_DOMICILE")["remplacement_par_transfert_direct_legalement_valide"]=True;self.reject(x)
    def test_33_close_missing_proof(self):
        x=self.copy();x["preuves_pour_etape_suivante"][0]["statut"]="OBTENUE";self.reject(x)
    def test_34_change_p56l_data(self):
        x=self.copy(1);x["tranches_a14"][0]["credits_remboursables_mcad"]="700";self.reject(x,1)
    def test_35_change_p56v_status(self):
        x=self.copy(2);x["decision"]="GO";self.reject(x,2)
    def test_36_change_p56n_oneoff(self):
        x=self.copy(3);x["versement_ponctuel_provincial_2026"]["prorogation_2027_2036_constatee"]=True;self.reject(x,3)
    def test_37_cli_and_no_overwrite(self):
        args=[sys.executable,str(SRC),"--credits",str(FILES[0]),"--p56l",str(FILES[1]),
              "--p56v",str(FILES[2]),"--p56n",str(FILES[3]),
              "--p56o",str(FILES[4]),"--barometre",str(FILES[5])]
        res=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(res.returncode,0,res.stderr)
        self.assertEqual(json.loads(res.stdout)["credits_sous_30000_mcad"],"4201")
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"r.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(p)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(p)],capture_output=True).returncode,2)
    def test_38_cli_no_automatic_tax_gain(self):
        args=[sys.executable,str(SRC),"--credits",str(FILES[0]),"--p56l",str(FILES[1]),
              "--p56v",str(FILES[2]),"--p56n",str(FILES[3]),
              "--p56o",str(FILES[4]),"--barometre",str(FILES[5]),
              "--certifier-gains-fiscaux-nova"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
