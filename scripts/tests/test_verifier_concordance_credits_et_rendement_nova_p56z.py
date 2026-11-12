"""P56Z : 47 contrôles contre le double comptage des crédits et faux gains fiscaux."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/verifier_concordance_credits_et_rendement_nova_p56z.py"
PATHS=[
ROOT/"projets/projet-nova/etudes/P56Z_CONCORDANCE_CREDITS_2023_ET_RENDEMENT_2027_2031_SANS_DOUBLE_COMPTE.json",
ROOT/"projets/projet-nova/etudes/P56W_CREDITS_REMBOURSABLES_2023_PAR_CATEGORIE_ET_TRANCHES_PROTECTION.json",
ROOT/"projets/projet-nova/etudes/P56Y_RENDEMENT_BRUT_NECESSAIRE_DEUX_PRELEVEMENTS_2027_2031.json",
ROOT/"projets/projet-nova/etudes/P56X_ASSIETTES_HISTORIQUES_ET_VERROU_TAUX_NOVA_2027_2028.json",
ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
]
spec=importlib.util.spec_from_file_location("p56z",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestP56Z(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=[json.loads(p.read_text(encoding="utf-8")) for p in PATHS]
        cls.report=m.audit(*cls.data)
    def clone(self,index=0):
        return copy.deepcopy(self.data[index])
    def fail_with(self,changed,index=0):
        args=list(self.data);args[index]=changed
        with self.assertRaises(ValueError):
            m.audit(*args)
    def credit(self,d,id):
        return next(x for x in d["credits_remboursables_2023"]["categories_extraites_pertinentes"] if x["id"]==id)
    def year(self,d,fy):
        return next(x for x in d["rapprochement_decennal_amorce"] if x["exercice"]==fy)
    def test_01_jalon(self):self.assertEqual(self.report["jalon"],"P56Z")
    def test_02_version(self):self.assertEqual(self.data[0]["schema_version"],"P56Z-1")
    def test_03_gross_income_tax_2023(self):self.assertEqual(self.report["impot_2023_avant_credits_non_remboursables_mcad"],"62148")
    def test_04_nonrefundable_2023(self):self.assertEqual(self.report["credits_non_remboursables_2023_mcad"],"21358")
    def test_05_payable_2023(self):self.assertEqual(self.report["impot_2023_apres_non_remboursables_mcad"],"40790")
    def test_06_refundable_2023(self):self.assertEqual(self.report["credits_remboursables_2023_mcad"],"9305")
    def test_07_arithmetic_net_2023(self):self.assertEqual(self.report["indicateur_arithmetique_apres_credits_mcad"],"31485")
    def test_08_low_income_2023(self):self.assertEqual(self.report["credit_tranches_moins_30000_cad_mcad"],"4201")
    def test_09_category_rounding(self):self.assertEqual(self.report["credits_arrondis_somme_categories_mcad"],"9306")
    def test_10_bracket_rounding(self):self.assertEqual(self.report["credits_arrondis_somme_tranches_mcad"],"9304")
    def test_11_2027_target(self):self.assertEqual(self.report["besoin_rendement_2027_2028_sans_resorption_mcad"],"116663")
    def test_12_no_2023_credits_added(self):self.assertFalse(self.report["credits_2023_supposes_cout_additionnel_en_2027"])
    def test_13_households_unproven(self):self.assertFalse(self.report["couverture_menages_protection_2027_demontree"])
    def test_14_no_accounting_certification(self):self.assertFalse(self.report["reclassement_credits_2027_certifie"])
    def test_15_tgt_2028(self):self.assertEqual(self.report["cibles_de_rendement_2027_2031"]["2028-2029"],"117620")
    def test_16_tgt_2029(self):self.assertEqual(self.report["cibles_de_rendement_2027_2031"]["2029-2030"],"120015")
    def test_17_tgt_2030(self):self.assertEqual(self.report["cibles_de_rendement_2027_2031"]["2030-2031"],"124159")
    def test_18_no_reform_forecast(self):self.assertFalse(self.report["previsions_nova_validees"])
    def test_19_ten_doors(self):self.assertEqual(self.report["portes_non_demontrees"],10)
    def test_20_score(self):self.assertEqual(self.report["score_estime_p55n"],53)
    def test_21_points_remaining(self):self.assertEqual(self.report["points_restants"],47)
    def test_22_no_go(self):self.assertEqual(self.report["decision"],"NO_GO_AUTOMATIQUE")
    def test_23_change_official_page(self):
        d=self.clone();d["sources"]["A14"]["url"]="https://example.org";self.fail_with(d)
    def test_24_change_source_year(self):
        d=self.clone();d["sources"]["A15"]["annee"]=2027;self.fail_with(d)
    def test_25_change_source_P56Y(self):
        d=self.clone();d["sources"]["P56Y"]="inexistant";self.fail_with(d)
    def test_26_fake_revenue(self):
        d=self.clone();d["exercice_observation"]["revenu_total_declarants_mcad"]="500000";self.fail_with(d)
    def test_27_fake_non_ref_credit(self):
        d=self.clone();d["exercice_observation"]["credits_non_remboursables_mcad"]="21000";self.fail_with(d)
    def test_28_fake_payable(self):
        d=self.clone();d["exercice_observation"]["impot_a_payer_apres_non_remboursables_mcad"]="31485";self.fail_with(d)
    def test_29_fake_2023_refundable(self):
        d=self.clone();d["exercice_observation"]["credits_remboursables_mcad"]="0";self.fail_with(d)
    def test_30_fake_net_is_consolidated(self):
        d=self.clone();d["exercice_observation"]["ce_solde_est_un_indicateur_statistique_non_recette_comptable_consolidee"]=False;self.fail_with(d)
    def test_31_hide_rounding(self):
        d=self.clone();d["credits_remboursables_2023"]["somme_categories_arrondies_mcad"]="9305";self.fail_with(d)
    def test_32_fake_family_credit(self):
        d=self.clone();self.credit(d,"FAMILLE")["total_mcad"]="0";self.fail_with(d)
    def test_33_fake_solidarity(self):
        d=self.clone();self.credit(d,"SOLIDARITE")["total_mcad"]="0";self.fail_with(d)
    def test_34_repeat_2023_as_2027(self):
        d=self.clone();self.credit(d,"SOUTIEN_AINES")["remboursement_reel_nova_2027_mcad"]="1703";self.fail_with(d)
    def test_35_hide_low_income_credit(self):
        d=self.clone();d["credits_remboursables_2023"]["moins_30000_cad"]["somme_mcad"]="0";self.fail_with(d)
    def test_36_revise_2027_using_2023_credit(self):
        d=self.clone();self.year(d,"2027-2028")["rendement_conditionnel_pour_solde_zero_sans_resorption_mcad"]="125968";self.fail_with(d)
    def test_37_protect_zero_not_known(self):
        d=self.clone();self.year(d,"2027-2028")["cout_compensations_incremental_net_mcad"]="0";self.fail_with(d)
    def test_38_fictitious_fiscal_yield(self):
        d=self.clone();self.year(d,"2027-2028")["rendement_net_nova_certifie_mcad"]="116663";self.fail_with(d)
    def test_39_false_neutrality(self):
        d=self.clone();d["conventions_reclassement"]["regime_actuel_comptabilisation_exacte_2027_connue"]=True;self.fail_with(d)
    def test_40_bad_double_count_rule(self):
        d=self.clone();d["conventions_reclassement"]["si_credit_actuel_est_deja_charge_de_transfert"]="AJOUTER_DEUX_FOIS";self.fail_with(d)
    def test_41_false_credit_abolition_gain(self):
        d=self.clone();d["garde_fous"]["ne_pas_abolir_prestation_pour_afficher_un_gain"]=False;self.fail_with(d)
    def test_42_sovereign_federal_transfers_assumed(self):
        d=self.clone();d["juridictions"]["QUEBEC_SOUVERAIN"]["transferts_federaux_continues_presumes"]=True;self.fail_with(d)
    def test_43_nonexistent_professional_validation(self):
        d=self.clone();d["portes"][0]["avis_independant_signe"]=True;self.fail_with(d)
    def test_44_changed_p56w_historical_data(self):
        d=self.clone(1);d["controle_arrondis"]["ligne_totale_officielle_mcad"]="9304";self.fail_with(d,1)
    def test_45_changed_p56y_target(self):
        d=self.clone(2);d["annees"][0]["rendement_nouveaux_piliers_pour_solde_zero_sans_resorption_mcad"]="9305";self.fail_with(d,2)
    def test_46_changed_p56x_2023(self):
        d=self.clone(3);d["donnees_historiques"]["personnes_2023"]["revenu_total_mcad"]="300000";self.fail_with(d,3)
    def test_47_cli_success_and_nonoverwrite(self):
        args=[sys.executable,str(SCRIPT),"--concordance",str(PATHS[0]),
              "--p56w",str(PATHS[1]),"--p56y",str(PATHS[2]),
              "--p56x",str(PATHS[3]),"--p56o",str(PATHS[4]),
              "--barometre",str(PATHS[5])]
        result=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)["credits_remboursables_2023_mcad"],"9305")
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"r.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(dest)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(dest)],capture_output=True).returncode,2)
    def test_48_cli_refuse_false_certification(self):
        args=[sys.executable,str(SCRIPT),"--concordance",str(PATHS[0]),
              "--p56w",str(PATHS[1]),"--p56y",str(PATHS[2]),
              "--p56x",str(PATHS[3]),"--p56o",str(PATHS[4]),
              "--barometre",str(PATHS[5]),"--exiger-protection-certifiee"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
