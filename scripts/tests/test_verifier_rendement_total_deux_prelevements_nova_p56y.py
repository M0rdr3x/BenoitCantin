"""P56Y: revenu total des deux nouveaux piliers vs seules recettes additionnelles."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/verifier_rendement_total_deux_prelevements_nova_p56y.py"
FILES=[
ROOT/"projets/projet-nova/etudes/P56Y_RENDEMENT_BRUT_NECESSAIRE_DEUX_PRELEVEMENTS_2027_2031.json",
ROOT/"projets/projet-nova/etudes/P56R_INVENTAIRE_EXHAUSTIF_CATEGORIES_RECETTES_ET_PONT_FISCAL_2026_2031.json",
ROOT/"projets/projet-nova/etudes/P56Q_PONT_CONTREFACTUEL_RECETTES_2027_2031_SIMULATEUR_AMENDE.json",
ROOT/"projets/projet-nova/etudes/P56X_ASSIETTES_HISTORIQUES_ET_VERROU_TAUX_NOVA_2027_2028.json",
ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"]
spec=importlib.util.spec_from_file_location("p56y",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class TestP56Y(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=[json.loads(f.read_text(encoding="utf-8")) for f in FILES]
        cls.summary=mod.audit(*cls.d)
    def fresh(self,i=0):return copy.deepcopy(self.d[i])
    def deny(self,data,i=0):
        args=list(self.d);args[i]=data
        with self.assertRaises(ValueError):mod.audit(*args)
    def year(self,d,fy):
        return next(x for x in d["annees"] if x["exercice"]==fy)
    def test_01_jalon(self):self.assertEqual(self.summary["jalon"],"P56Y")
    def test_02_score(self):self.assertEqual(self.summary["score_estime_pourcent"],53)
    def test_03_gross_target_2027(self):self.assertEqual(self.summary["objectif_2027_2028_mcad"],"116663")
    def test_04_incremental_2027(self):self.assertEqual(self.summary["objectif_seulement_additionnel_2027_2028_mcad"],"48570")
    def test_05_revenue_excluding_two_pillars_2027(self):self.assertEqual(self.summary["annees"]["2027-2028"]["autres_recettes_conservees_mcad"],"63257")
    def test_06_keep_same_income_2027(self):self.assertEqual(self.summary["annees"]["2027-2028"]["rendement_nouveaux_piliers_memes_recettes_mcad"],"110968")
    def test_07_prudent_2028(self):self.assertEqual(self.summary["annees"]["2028-2029"]["rendement_nouveaux_piliers_pour_solde_zero_prudent_mcad"],"117620")
    def test_08_prudent_2029(self):self.assertEqual(self.summary["annees"]["2029-2030"]["rendement_nouveaux_piliers_pour_solde_zero_prudent_mcad"],"120015")
    def test_09_prudent_2030(self):self.assertEqual(self.summary["annees"]["2030-2031"]["rendement_nouveaux_piliers_pour_solde_zero_prudent_mcad"],"124159")
    def test_10_tax_rate_not_adopted(self):self.assertFalse(self.summary["taux_fiscal_nova_choisi"])
    def test_11_nova_revenues_not_observed(self):self.assertFalse(self.summary["recettes_fiscales_nova_nouvelles_validees"])
    def test_12_no_sovereign_budget(self):self.assertFalse(self.summary["budget_decennal_nova_certifie"])
    def test_13_no_go(self):self.assertEqual(self.summary["decision"],"NO_GO_AUTOMATIQUE")
    def test_14_wrong_income_2027(self):
        d=self.fresh();self.year(d,"2027-2028")["impots_personnes_societes_actuels_que_nova_remplacerait_mcad"]="0";self.deny(d)
    def test_15_wrong_vat_2027(self):
        d=self.fresh();self.year(d,"2027-2028")["trois_autres_prelevements_que_nova_pourrait_remplacer_mcad"]="0";self.deny(d)
    def test_16_hide_current_income_2027(self):
        d=self.fresh();self.year(d,"2027-2028")["recettes_total_a_substituer_si_deux_nouveaux_piliers_mcad"]="42875";self.deny(d)
    def test_17_wrong_residual(self):
        d=self.fresh();self.year(d,"2027-2028")["recettes_restant_hors_impots_et_trois_prelevements_mcad"]="100";self.deny(d)
    def test_18_2028_missing_unfunded_gap(self):
        d=self.fresh();self.year(d,"2028-2029")["rendement_nouveaux_piliers_pour_solde_zero_sans_resorption_mcad"]="115770";self.deny(d)
    def test_19_invent_2027_base(self):
        d=self.fresh();self.year(d,"2027-2028")["nouvelle_assiette_imposable_personnes_mcad"]="500000";self.deny(d)
    def test_20_invent_anti_paradis_cash(self):
        d=self.fresh();self.year(d,"2027-2028")["rendement_net_prelevement_anti_paradis_nova_mcad"]="100";self.deny(d)
    def test_21_invent_family_compensation(self):
        d=self.fresh();self.year(d,"2027-2028")["compensations_sociales_nova_mcad"]="0";self.deny(d)
    def test_22_claim_abrogation(self):
        d=self.fresh();self.year(d,"2027-2028")["taux_nova_2027_2036_adopte"]=True;self.deny(d)
    def test_23_double_count_income(self):
        d=self.fresh();d["precautions"]["ne_pas_additionner_un_impot_nouveau_au_maintien_d_impots_remplaces"]=False;self.deny(d)
    def test_24_double_count_42G(self):
        d=self.fresh();d["precautions"]["ne_pas_ajouter_les_42_875_deux_fois"]=False;self.deny(d)
    def test_25_invent_sovereign(self):
        d=self.fresh();d["regimes"]["QUEBEC_SOUVERAIN"]["nouveaux_couts_competences_federales_mcad"]="0";self.deny(d)
    def test_26_transfer_federal_error(self):
        d=self.fresh();d["regimes"]["QUEBEC_SOUVERAIN"]["transferts_federaux_de_reference_conserves_automatiquement"]=True;self.deny(d)
    def test_27_close_evidence(self):
        d=self.fresh();d["blocages"][0]["statut"]="VALIDE";self.deny(d)
    def test_28_fabricate_score(self):
        d=self.fresh();d["avancement"]["score_p55n"]=99;self.deny(d)
    def test_29_corrupt_P56X(self):
        d=self.fresh(3);d["repere_2027_2028"]["impots_revenu_existants_mcad"]="0";self.deny(d,3)
    def test_30_corrupt_P56Q(self):
        d=self.fresh(2);self_year=next(x for x in d["annees_reconciliees"] if x["exercice"]=="2027-2028");self_year["trois_categories_risque_suppression_mcad"]="0";self.deny(d,2)
    def test_31_corrupt_P56R(self):
        d=self.fresh(1);self_year=next(x for x in d["rapprochement_annees"] if x["exercice"]=="2028-2029");self_year["impots_sur_revenu_actuels_mcad"]="1";self.deny(d,1)
    def test_32_bad_source(self):
        d=self.fresh();d["sources"]["P56X"]="P56X_FORGED";self.deny(d)
    def test_33_cli_and_no_overwrite(self):
        args=[sys.executable,str(SCRIPT),"--pont",str(FILES[0]),
              "--p56r",str(FILES[1]),"--p56q",str(FILES[2]),"--p56x",str(FILES[3]),
              "--p56o",str(FILES[4]),"--barometre",str(FILES[5])]
        r=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)["objectif_2027_2028_mcad"],"116663")
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/"report.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(file)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(file)],capture_output=True).returncode,2)
    def test_34_cli_refuse_rates(self):
        args=[sys.executable,str(SCRIPT),"--pont",str(FILES[0]),
              "--p56r",str(FILES[1]),"--p56q",str(FILES[2]),"--p56x",str(FILES[3]),
              "--p56o",str(FILES[4]),"--barometre",str(FILES[5]),
              "--exiger-taux-adoptes"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
