"""P57A : validation du reclassement comptable et protection contre faux 2027."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/verifier_reclassement_credits_comptes_publics_nova_p57a.py"
FILES=[
ROOT/"projets/projet-nova/etudes/P57A_RECONCILIATION_CREDITS_2025_2026_COMPTES_PUBLICS_VOL1.json",
ROOT/"projets/projet-nova/etudes/P56P_BASE_BUDGET_PREELECTORALE_2026_2031_VGQ_ET_ECARTS.json",
ROOT/"projets/projet-nova/etudes/P56W_CREDITS_REMBOURSABLES_2023_PAR_CATEGORIE_ET_TRANCHES_PROTECTION.json",
ROOT/"projets/projet-nova/etudes/P56Y_RENDEMENT_BRUT_NECESSAIRE_DEUX_PRELEVEMENTS_2027_2031.json",
ROOT/"projets/projet-nova/etudes/P56Z_CONCORDANCE_CREDITS_2023_ET_RENDEMENT_2027_2031_SANS_DOUBLE_COMPTE.json",
ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
]
spec=importlib.util.spec_from_file_location("nova_p57a",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class P57A(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=[json.loads(p.read_text(encoding="utf-8")) for p in FILES]
        cls.out=m.verifier(*cls.data)
    def copy(self,n=0):
        return copy.deepcopy(self.data[n])
    def rejected(self,d,n=0):
        args=list(self.data);args[n]=d
        with self.assertRaises(ValueError):
            m.verifier(*args)
    def c(self,d,key):
        return d["revenus_et_reclassement_2025_2026_mcad"][key]
    def cat(self,d,kind,code):
        return next(x for x in d["transferts_2025_2026_par_programme_mcad"][kind] if x["id"]==code)
    def test_01_jalon(self):self.assertEqual(self.out["jalon"],"P57A")
    def test_02_annee_observee(self):self.assertEqual(self.out["exercice_preuve"],"2025-2026")
    def test_03_total_reclassement(self):self.assertEqual(self.out["total_reclassement_transferts_mcad"],"11578")
    def test_04_particuliers(self):self.assertEqual(self.out["particuliers_transferts_mcad"],"8291")
    def test_05_societes(self):self.assertEqual(self.out["societes_transferts_mcad"],"3287")
    def test_06_solidarite(self):self.assertEqual(self.out["degrevement_solidarite_taxes_consommation_mcad"],"1996")
    def test_07_revenus_net(self):self.assertEqual(self.out["reclassement_revenus_avant_mcad"],"62537")
    def test_08_revenus_consolides(self):self.assertEqual(self.out["reclassement_revenus_apres_mcad"],"74115")
    def test_09_sans_economie(self):self.assertTrue(self.out["une_reclassification_n_est_pas_une_economie"])
    def test_10_2023_not_2027(self):self.assertTrue(self.out["credits_de_2023_non_projetes_en_2027"])
    def test_11_z01_partielle(self):self.assertTrue(self.out["condition_Z01_preuve_partielle_historique"])
    def test_12_z01_non_fermee(self):self.assertFalse(self.out["condition_Z01_validee_pour_2027"])
    def test_13_budget_non_certifie(self):self.assertFalse(self.out["budget_Nova_2027_certifie"])
    def test_14_score(self):self.assertEqual(self.out["score_estime_pourcent"],53)
    def test_15_points(self):self.assertEqual(self.out["points_restants"],47)
    def test_16_no_go(self):self.assertEqual(self.out["decision"],"NO_GO_AUTOMATIQUE")
    def test_17_url_change(self):
        d=self.copy();d["sources"]["comptes_publics_volume_1"]["url"]="https://fake.org";self.rejected(d)
    def test_18_pdf_pages_changed(self):
        d=self.copy();d["sources"]["comptes_publics_volume_1"]["pages_pdf_index_zero"]=[0];self.rejected(d)
    def test_19_pdf_hash_fabrication(self):
        d=self.copy();d["sources"]["comptes_publics_volume_1"]["empreinte_fichier_original_sha256"]="invented";self.rejected(d)
    def test_20_disable_regle(self):
        d=self.copy();d["regle_comptable_verifiee"]["ce_reclassement_ne_cree_pas_d_argent_public_nouveau"]=False;self.rejected(d)
    def test_21_invent_reclassification(self):
        d=self.copy();self.c(d,"personnes")["credits_transferts_reclasses"]="0";self.rejected(d)
    def test_22_invent_societes(self):
        d=self.copy();self.c(d,"societes")["credits_transferts_reclasses"]="3288";self.rejected(d)
    def test_23_fss_wrong(self):
        d=self.copy();self.c(d,"cotisations_services_sante")["credits_transferts_reclasses"]="1";self.rejected(d)
    def test_24_revenues_wrong(self):
        d=self.copy();self.c(d,"total_revenus_impot_biens")["revenus_consolides"]="74116";self.rejected(d)
    def test_25_solidarity_false_transfer(self):
        d=self.copy();self.c(d,"credit_solidarite")["inclure_dans_somme_transferts_impot_biens_11578"]=True;self.rejected(d)
    def test_26_solidarity_wrong_amount(self):
        d=self.copy();self.c(d,"credit_solidarite")["montant_degrevement_taxes_ventes"]="2000";self.rejected(d)
    def test_27_family_credit_wrong(self):
        d=self.copy();self.cat(d,"particuliers","FAMILLE")["montant"]="100";self.rejected(d)
    def test_28_corporation_credit_wrong(self):
        d=self.copy();self.cat(d,"societes","RECHERCHE")["montant"]="0";self.rejected(d)
    def test_29_portfolio_wrong(self):
        d=self.copy();d["transferts_2025_2026_par_programme_mcad"]["ventilation_consolidee_par_portefeuille"]["FAMILLE"]="4000";self.rejected(d)
    def test_30_priors_wrong(self):
        d=self.copy();d["comparatif_2024_2025_mcad"]["credit_solidarite_reduction_taxes_ventes"]="0";self.rejected(d)
    def test_31_historical_2023_not_2026(self):
        d=self.copy();d["distinction_statistique_2023"]["statistique_fiscale_2023_non_directement_comparable_au_8291_2026"]=False;self.rejected(d)
    def test_32_fake_2027_admission(self):
        d=self.copy();d["risque_pour_scenarios_fiscaux_nova"]["classification_comptable_degrèvement_2027_verifiee"]=True;self.rejected(d)
    def test_33_fake_2027_cost(self):
        d=self.copy();d["risque_pour_scenarios_fiscaux_nova"]["cout_incremental_compensations_2027_mcad"]="0";self.rejected(d)
    def test_34_false_z01_close(self):
        d=self.copy();d["preuve_partiellement_obtenue"]["condition_Z01_fermee"]=True;self.rejected(d)
    def test_35_wrong_dependency_p56p(self):
        d=self.copy(1);d["annees_historique_et_previsions"][0]["revenus"]["impot_particuliers"]="40000";self.rejected(d,1)
    def test_36_wrong_dependency_p56w(self):
        d=self.copy(2);d["controle_arrondis"]["ligne_totale_officielle_mcad"]="9000";self.rejected(d,2)
    def test_37_wrong_dependency_p56y(self):
        d=self.copy(3);d["annees"][0]["rendement_nouveaux_piliers_pour_solde_zero_sans_resorption_mcad"]="0";self.rejected(d,3)
    def test_38_fake_open_gate(self):
        d=self.copy();d["etapes_suivantes"][0]["statut"]="CLOS";self.rejected(d)
    def test_39_inflation_score(self):
        d=self.copy(6);d["score_estimatif"]=100;self.rejected(d,6)
    def test_40_cli_report_no_overwrite(self):
        args=[sys.executable,str(SCRIPT)]
        for flag,path in zip(("preuve","p56p","p56w","p56y","p56z","p56o","p55n"),FILES):
            args.extend(["--"+flag,str(path)])
        r=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)["total_reclassement_transferts_mcad"],"11578")
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"report.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(path)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(path)],capture_output=True).returncode,2)
    def test_41_cli_refus(self):
        args=[sys.executable,str(SCRIPT)]
        for flag,path in zip(("preuve","p56p","p56w","p56y","p56z","p56o","p55n"),FILES):
            args.extend(["--"+flag,str(path)])
        self.assertEqual(subprocess.run(args+["--exiger-preuve-2027-validee"],capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
