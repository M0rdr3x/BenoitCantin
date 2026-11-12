"""P57B: tests de continuite du credit solidarite, calendrier et concordance comptable."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"scripts/verifier_continuite_solidarite_nova_p57b.py"
FILES=[
 ROOT/"projets/projet-nova/etudes/P57B_SOLIDARITE_VERSEMENTS_2026_2027_ET_VERROU_PROTECTION_TVQ.json",
 ROOT/"projets/projet-nova/etudes/P57A_RECONCILIATION_CREDITS_2025_2026_COMPTES_PUBLICS_VOL1.json",
 ROOT/"projets/projet-nova/etudes/P56Z_CONCORDANCE_CREDITS_2023_ET_RENDEMENT_2027_2031_SANS_DOUBLE_COMPTE.json",
 ROOT/"projets/projet-nova/etudes/P56Y_RENDEMENT_BRUT_NECESSAIRE_DEUX_PRELEVEMENTS_2027_2031.json",
 ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
 ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
]
sp=importlib.util.spec_from_file_location("p57b",SRC)
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)

class TestP57B(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=[json.loads(x.read_text(encoding="utf-8")) for x in FILES]
        cls.out=m.auditer(*cls.docs)
    def clone(self,n=0):
        return copy.deepcopy(self.docs[n])
    def refuse(self,d,n=0):
        docs=list(self.docs);docs[n]=d
        with self.assertRaises(ValueError):
            m.auditer(*docs)
    def cadence(self,d,id):
        return next(c for c in d["cadences"] if c["id"]==id)
    def composante(self,d,id):
        return next(c for c in d["composantes"] if c["id"]==id)
    def test_01_jalon(self):self.assertEqual(self.out["jalon"],"P57B")
    def test_02_score(self):self.assertEqual(self.out["score_estime_pourcent"],53)
    def test_03_points(self):self.assertEqual(self.out["points_restants"],47)
    def test_04_no_go(self):self.assertEqual(self.out["decision"],"NO_GO_AUTOMATIQUE")
    def test_05_fy_actual(self):self.assertEqual(self.out["degrevement_solidarite_constate_exercice_2025_2026_mcad"],"1996")
    def test_06_2026_projection(self):self.assertEqual(self.out["cout_solidarite_projete_annee_2026_mcad"],"2029.1")
    def test_07_not_same_year(self):self.assertFalse(self.out["comparabilite_d_annees"])
    def test_08_2025_date_reference(self):self.assertEqual(self.out["date_situation_admissibilite"],"2025-12-31")
    def test_09_cash_year(self):self.assertTrue(self.out["versement_reference_juillet_2026_juin_2027"])
    def test_10_tax_year(self):self.assertEqual(self.out["annee_declaration_reference"],2025)
    def test_11_three_components(self):self.assertEqual(self.out["trois_composantes"],["LOGEMENT","TVQ","VILLAGES_NORDIQUES"])
    def test_12_annual_count(self):self.assertEqual(self.out["calendrier_versement"]["ANNUELLE"]["nb_versements_par_regime"],1)
    def test_13_quarterly_count(self):self.assertEqual(self.out["calendrier_versement"]["TRIMESTRIELLE"]["nb_versements_par_regime"],4)
    def test_14_monthly_count(self):self.assertEqual(self.out["calendrier_versement"]["MENSUELLE"]["nb_versements_par_regime"],12)
    def test_15_monthly_splits(self):self.assertEqual(self.out["calendrier_versement"]["MENSUELLE"]["avril_juin_2027"],3)
    def test_16_quarterly_splits(self):self.assertEqual(self.out["calendrier_versement"]["TRIMESTRIELLE"]["avril_juin_2027"],1)
    def test_17_annual_splits(self):self.assertEqual(self.out["calendrier_versement"]["ANNUELLE"]["avril_juin_2027"],0)
    def test_18_no_budget_proven(self):self.assertFalse(self.out["budget_droits_2027_2028_confirme"])
    def test_19_no_household_gain_proven(self):self.assertFalse(self.out["benefice_nova_net_menages_certifie"])
    def test_20_dont_abolish(self):self.assertFalse(self.out["soutien_solidarite_aboli_par_option_nova"])
    def test_21_not_done(self):self.assertFalse(self.out["modele_reforme_fiscale_acheve"])
    def test_22_zero_closed(self):self.assertEqual(self.out["portes_p57b_closes"],0)
    def test_23_change_official_link(self):
        d=self.clone();d["sources"]["versements_officiels"]="https://example.invalid";self.refuse(d)
    def test_24_false_actual_value(self):
        d=self.clone();d["classification_des_sources"]["comptes_publics_2025_2026"]["credit_solidarite_degrevement_tvq_mcad"]="2029";self.refuse(d)
    def test_25_false_projected_value(self):
        d=self.clone();d["classification_des_sources"]["depense_fiscale_2025_pour_2026"]["credit_solidarite_total_mcad"]="1996";self.refuse(d)
    def test_26_no_2026_beneficiaries(self):
        d=self.clone();d["classification_des_sources"]["depense_fiscale_2025_pour_2026"]["nombre_beneficiaires_2026_constate"]="2836085";self.refuse(d)
    def test_27_no_2027_tax_year(self):
        d=self.clone();d["droits_et_calcul_actuels"]["declaration_fiscale_annee_reference"]=2027;self.refuse(d)
    def test_28_threshold_not_a_nova_tax_rate(self):
        d=self.clone();d["droits_et_calcul_actuels"]["seuil_revenu_familial_max_sans_conjoint_2026_2027_cad"]="100000";self.refuse(d)
    def test_29_no_credit_tvq_deletion(self):
        d=self.clone();self.composante(d,"TVQ")["a_remplacer_ou_maintenir_si_retrait_tvq"]=False;self.refuse(d)
    def test_30_no_nordic_omission(self):
        d=self.clone();d["composantes"]=[x for x in d["composantes"] if x["id"]!="VILLAGES_NORDIQUES"];self.refuse(d)
    def test_31_no_fictitious_credit_yield(self):
        d=self.clone();self.composante(d,"LOGEMENT")["cout_2027_concorde_mcad"]="500";self.refuse(d)
    def test_32_not_assume_monthly_only(self):
        d=self.clone();self.cadence(d,"TRIMESTRIELLE")["versements_mois"]=["2026-07","2026-10","2027-01"];self.refuse(d)
    def test_33_no_fictitious_fiscal_date(self):
        d=self.clone();self.cadence(d,"MENSUELLE")["nb_dans_debut_exercice_2027_2028"]=4;self.refuse(d)
    def test_34_no_full_expense_from_cash_date(self):
        d=self.clone();d["frontiere_calendrier"]["calendrier_cash_non_identique_imputation_en_droits_constates"]=False;self.refuse(d)
    def test_35_no_2027_fiscal_model(self):
        d=self.clone();d["frontiere_calendrier"]["montant_total_2027_2028_inconnu_mcad"]="2000";self.refuse(d)
    def test_36_no_unproved_family_savings(self):
        d=self.clone();d["regle_protection_citoyens_candidate"]["maintien_pouvoir_achat_n_est_pas_encore_demontre"]=False;self.refuse(d)
    def test_37_no_double_count(self):
        d=self.clone();d["rapprochement_financier"]["ne_pas_ajouter_1996_credits_comptables_2025_2026_aux_besoins_2027"]=False;self.refuse(d)
    def test_38_no_stated_nova_gain(self):
        d=self.clone();d["rapprochement_financier"]["calcul_increment_2027_2028_mcad"]="0";self.refuse(d)
    def test_39_no_made_up_adoption(self):
        d=self.clone();d["regle_protection_citoyens_candidate"]["statut"]="LOI_ADOPTEE";self.refuse(d)
    def test_40_no_fake_closed_gate(self):
        d=self.clone();d["portes"][0]["statut"]="TERMINE";self.refuse(d)
    def test_41_no_fake_score(self):
        d=self.clone(5);d["score_estimatif"]=100;self.refuse(d,5)
    def test_42_no_fake_p57a_actual(self):
        d=self.clone(1);d["revenus_et_reclassement_2025_2026_mcad"]["credit_solidarite"]["montant_degrevement_taxes_ventes"]="0";self.refuse(d,1)
    def test_43_no_fake_p56y_yield(self):
        d=self.clone(3);d["annees"][0]["rendement_nouveaux_piliers_pour_solde_zero_sans_resorption_mcad"]="120000";self.refuse(d,3)
    def test_44_cli_no_overwrite(self):
        args=[sys.executable,str(SRC)]
        for name,path in zip(("registre","p57a","p56z","p56y","p56o","barometre"),FILES):
            args.extend(["--"+name,str(path)])
        r=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)["calendrier_versement"]["MENSUELLE"]["avril_juin_2027"],3)
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"report.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(target)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(target)],capture_output=True).returncode,2)
    def test_45_cli_refuses_certification(self):
        args=[sys.executable,str(SRC)]
        for name,path in zip(("registre","p57a","p56z","p56y","p56o","barometre"),FILES):
            args.extend(["--"+name,str(path)])
        self.assertEqual(subprocess.run(args+["--exiger-protection-2027-certifiee"],capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
