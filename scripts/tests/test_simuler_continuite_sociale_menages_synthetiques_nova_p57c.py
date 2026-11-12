"""P57C : seuils, cadence, protection retenue dette, sans créer de droit fictif."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/simuler_continuite_sociale_menages_synthetiques_nova_p57c.py"
FILES=[
ROOT/"projets/projet-nova/etudes/P57C_PILOTE_MENAGES_SYNTHETIQUES_SOLIDARITE_2026_2027.json",
ROOT/"projets/projet-nova/etudes/P57B_SOLIDARITE_VERSEMENTS_2026_2027_ET_VERROU_PROTECTION_TVQ.json",
ROOT/"projets/projet-nova/etudes/P57A_RECONCILIATION_CREDITS_2025_2026_COMPTES_PUBLICS_VOL1.json",
ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
]
spec=importlib.util.spec_from_file_location("nova_p57c",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestP57C(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=[json.loads(f.read_text(encoding="utf-8")) for f in FILES]
        cls.r=m.auditer(*cls.args)
    def clone(self,n=0):
        return copy.deepcopy(self.args[n])
    def reject(self,d,n=0):
        args=list(self.args);args[n]=d
        with self.assertRaises(ValueError):
            m.auditer(*args)
    def case(self,d,id):
        return next(x for x in d["jeux_de_cas_fictifs"] if x["id"]==id)
    def item(self,id):
        return self.r["resultats_par_cas"][id]
    def test_01_jalon(self):self.assertEqual(self.r["jalon"],"P57C")
    def test_02_nb_cases(self):self.assertEqual(self.r["nombre_cas_synthetiques"],10)
    def test_03_no_real_household(self):self.assertEqual(self.r["fiches_de_menages_reels_incluses"],0)
    def test_04_no_real_right_calculation(self):self.assertEqual(self.r["droits_individuels_reels_calcules"],0)
    def test_05_threshold_for_debt_cap(self):self.assertEqual(self.r["plafond_retenue_dette_protegee_revenu_familial_cad"],"26190")
    def test_06_single_20k_income_below_max(self):
        self.assertEqual(self.item("C01")["status_plafond_revenu"],"SOUS_PLAFOND_SANS_PREUVE_D_ADMISSIBILITE")
    def test_07_single_threshold(self):self.assertEqual(self.item("C01")["plafond_general_applicable_cad"],"64545")
    def test_08_single_1200_monthly(self):self.assertEqual(self.item("C01")["cadence_theorique"],"MENSUELLE")
    def test_09_single_monthly_9_first(self):self.assertEqual(self.item("C01")["nb_versements_jusque_mars_2027"],9)
    def test_10_single_monthly_3_later(self):self.assertEqual(self.item("C01")["nb_versements_avril_juin_2027"],3)
    def test_11_single_debt_cap_600(self):self.assertEqual(self.item("C01")["borne_superieure_retenue_sur_credit_annuel_si_protection_cad"],"600.00")
    def test_12_single_parent_max(self):self.assertEqual(self.item("C02")["plafond_general_applicable_cad"],"67179")
    def test_13_single_parent_quarterly(self):self.assertEqual(self.item("C02")["cadence_theorique"],"TRIMESTRIELLE")
    def test_14_single_parent_quarterly_3_plus_1(self):
        self.assertEqual((self.item("C02")["nb_versements_jusque_mars_2027"],self.item("C02")["nb_versements_avril_juin_2027"]),(3,1))
    def test_15_couple_excluded_by_general_threshold(self):
        self.assertEqual(self.item("C03")["status_plafond_revenu"],"PLAFOND_GENERAL_ATTEINT_OU_DEPASSE")
    def test_16_couple_no_hypothetical_payout(self):self.assertEqual(self.item("C03")["nb_versements_jusque_mars_2027"],0)
    def test_17_single_debt_cap_inclusive(self):
        self.assertEqual(self.item("C04")["borne_superieure_retenue_sur_credit_annuel_si_protection_cad"],"120.00")
    def test_18_single_240_annual(self):self.assertEqual(self.item("C04")["cadence_theorique"],"ANNUELLE")
    def test_19_above_debt_threshold_unknown(self):
        self.assertIsNone(self.item("C05")["borne_superieure_retenue_sur_credit_annuel_si_protection_cad"])
    def test_20_debt_above_threshold_must_not_imply_full_offset(self):
        self.assertEqual(self.item("C05")["retenue_potentielle_statut"],"PLAFOND_DE_50_PCT_NON_ETABLI_PAR_CES_CRITERES")
    def test_21_800_monthly(self):self.assertEqual(self.item("C05")["cadence_theorique"],"MENSUELLE")
    def test_22_northern_no_general_threshold(self):self.assertIsNone(self.item("C06")["plafond_general_applicable_cad"])
    def test_23_northern_status(self):self.assertEqual(self.item("C06")["status_plafond_revenu"],"VILLAGE_NORDIQUE_HORS_TABLEAU_GENERAL")
    def test_24_assistance_odd_799_half(self):
        self.assertEqual(self.item("C07")["borne_superieure_retenue_sur_credit_annuel_si_protection_cad"],"399.50")
    def test_25_750_northern_quarterly(self):self.assertEqual(self.item("C06")["cadence_theorique"],"TRIMESTRIELLE")
    def test_26_income_below_threshold_not_automatic_credit(self):
        self.assertEqual(self.item("C08")["cadence_theorique"],"AUCUN_CREDIT_FICTIF_ATTRIBUE")
    def test_27_exact_couple_max(self):self.assertEqual(self.item("C09")["status_plafond_revenu"],"PLAFOND_GENERAL_ATTEINT_OU_DEPASSE")
    def test_28_exact_single_parent_max(self):self.assertEqual(self.item("C10")["status_plafond_revenu"],"PLAFOND_GENERAL_ATTEINT_OU_DEPASSE")
    def test_29_no_certified_budget(self):self.assertFalse(self.r["budget_protection_menages_2027_certifie"])
    def test_30_no_household_gain(self):self.assertTrue(self.r["aucun_nouveau_benefice_nova_certifie"])
    def test_31_score_unchanged(self):self.assertEqual(self.r["score_estime_pourcent"],53)
    def test_32_points_remaining(self):self.assertEqual(self.r["points_restants_estimes"],47)
    def test_33_no_go(self):self.assertEqual(self.r["decision"],"NO_GO_AUTOMATIQUE")
    def test_34_invalid_source(self):
        d=self.clone();d["provenance"]["retenue_dette_revenu_quebec"]="https://example.invalid";self.reject(d)
    def test_35_fake_debt_100_percent(self):
        d=self.clone();d["parametres_publies_2026_2027"]["part_maximum_retenue_si_protege"]="1.00";self.reject(d)
    def test_36_fake_debt_threshold(self):
        d=self.clone();d["parametres_publies_2026_2027"]["seuil_retenue_dette_maximum_moins_de_50_pct_2026_2027_cad"]="30000";self.reject(d)
    def test_37_fake_general_threshold(self):
        d=self.clone();d["parametres_publies_2026_2027"]["seuil_revenu_familial_personne_seule_ou_monoparentale_cad"]="50000";self.reject(d)
    def test_38_change_synthetic_case(self):
        d=self.clone();self.case(d,"C01")["credit_annuel_fictif_deja_determine_par_avis_cad"]="500";self.reject(d)
    def test_39_inject_real_beneficiary(self):
        d=self.clone();self.case(d,"C01")["source_beneficiaire_reel"]="NAME";self.reject(d)
    def test_40_fake_real_credit(self):
        d=self.clone();self.case(d,"C02")["credit_effectivement_recu_cad"]="799";self.reject(d)
    def test_41_zero_not_evidence_of_ineligibility(self):
        d=self.clone();d["integrite_qualificatifs"]["cas_de_0_credit_n_est_pas_preuve_inéligibilite"]=False;self.reject(d)
    def test_42_remove_north_protection(self):
        d=self.clone();d["integrite_qualificatifs"]["conformite_aux_droits_individuels_avant_simplification"]=False;self.reject(d)
    def test_43_missing_case(self):
        d=self.clone();d["jeux_de_cas_fictifs"].pop();self.reject(d)
    def test_44_fake_closed_gate(self):
        d=self.clone();d["pistes_au_dela_du_banc_essai"][0]["preuve_statut"]="CLOSED";self.reject(d)
    def test_45_fake_maturity(self):
        d=self.clone();d["avancement"]["score_estime"]=100;self.reject(d)
    def test_46_fake_p57b_month(self):
        d=self.clone(1);d["cadences"][2]["versements_mois"].pop();self.reject(d,1)
    def test_47_negative_hypothetical_credit_rejected(self):
        c=self.clone()["jeux_de_cas_fictifs"][0]
        c["credit_annuel_fictif_deja_determine_par_avis_cad"]="-1"
        with self.assertRaises(ValueError):m.simuler(c)
    def test_48_general_max_with_positive_award_rejected(self):
        c=self.clone()["jeux_de_cas_fictifs"][8]
        c["credit_annuel_fictif_deja_determine_par_avis_cad"]="400"
        with self.assertRaises(ValueError):m.simuler(c)
    def test_49_northern_exception_not_excluded_at_75k(self):
        c=self.clone()["jeux_de_cas_fictifs"][5]
        self.assertEqual(m.simuler(c)["status_plafond_revenu"],"VILLAGE_NORDIQUE_HORS_TABLEAU_GENERAL")
    def test_50_infer_eligibility_not_allowed(self):
        self.assertTrue(self.item("C07")["credit_annuel_ne_garantit_pas_droit"])
    def test_51_no_actual_debt_withholding(self):
        self.assertIsNone(self.item("C07")["retenue_reelle_imputee_cad"])
    def test_52_cli_and_no_overwrite(self):
        args=[sys.executable,str(SCRIPT)]
        for k,f in zip(("pilote","p57b","p57a","p56o","barometre"),FILES):
            args.extend(["--"+k,str(f)])
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)["resultats_par_cas"]["C07"]["borne_superieure_retenue_sur_credit_annuel_si_protection_cad"],"399.50")
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"pilot.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(out)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(out)],capture_output=True).returncode,2)
    def test_53_cli_refuses_fake_nova_budget(self):
        args=[sys.executable,str(SCRIPT)]
        for k,f in zip(("pilote","p57b","p57a","p56o","barometre"),FILES):
            args.extend(["--"+k,str(f)])
        self.assertEqual(subprocess.run(args+["--exiger-microsimulation-validee"],capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
