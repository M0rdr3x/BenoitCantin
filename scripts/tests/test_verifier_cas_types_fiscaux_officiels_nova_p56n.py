"""P56N: 40 contrôles de cas types officiels 2026 et absence d'effet Nova inventé."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
CODE=ROOT/"scripts/verifier_cas_types_fiscaux_officiels_nova_p56n.py"
DOC=ROOT/"projets/projet-nova/etudes/P56N_CAS_TYPES_2026_REFERENCES_OFFICIELLES_PRESTATIONS_ET_LIMITES.json"
M=ROOT/"projets/projet-nova/etudes/P56M_CADRE_MICROSIMULATION_REVENUS_MENAGES_2027_2036.json"
L=ROOT/"projets/projet-nova/etudes/P56L_BASE_DISTRIBUTIVE_PARTICULIERS_2023_CREDITS_ET_QUINTILES.json"
B=ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
spec=importlib.util.spec_from_file_location("p56n",CODE)
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class TestP56N(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=[json.loads(f.read_text(encoding="utf-8")) for f in (DOC,M,L,B)]
        cls.report=p.verifier(*cls.inputs)
    def d(self):return copy.deepcopy(self.inputs[0])
    def reject(self,d,index=0):
        args=list(self.inputs)
        args[index]=d
        with self.assertRaises(ValueError):
            p.verifier(*args)
    def component(self,d,id):
        return next(x for x in d["cas_type_officiel_2026"]["contributions_a_variation_publiees_cad"] if x["id"]==id)
    def aid(self,d,id):
        return next(x for x in d["versement_ponctuel_provincial_2026"]["cas"] if x["id"]==id)
    def test_01_schema(self):self.assertEqual(self.inputs[0]["schema_version"],"P56N-1")
    def test_02_50000_income(self):self.assertEqual(self.report["cas_type_50000_cad"],"50000")
    def test_03_official_delta(self):self.assertEqual(self.report["variation_officielle_2025_2026_cad"],"847")
    def test_04_sum_components(self):self.assertEqual(self.report["somme_variations_composantes_cad"],"846")
    def test_05_one_dollar_rounding(self):self.assertEqual(self.report["ecart_non_resolu_cad"],"1")
    def test_06_four_one_off_categories(self):self.assertEqual(self.report["categories_aides_ponctuelles_2026"],4)
    def test_07_family_max(self):self.assertEqual(self.report["allocation_famille_max_par_enfant_2026_cad"],"3068")
    def test_08_no_nova_cases(self):self.assertEqual(self.report["cas_types_microsimules_et_certifies"],0)
    def test_09_one_off_not_2027(self):self.assertFalse(self.report["paiements_2026_projetes_automatiquement_2027"])
    def test_10_no_new_p52d(self):self.assertEqual(self.report["incidences_P52D_nouvelles_certifiees"],0)
    def test_11_p52b_missing(self):self.assertEqual(self.report["p52b_montants_inconnus"],600)
    def test_12_p52d_missing(self):self.assertEqual(self.report["p52d_incidences_inconnues"],720)
    def test_13_score(self):self.assertEqual(self.report["score_estime_p55n"],53)
    def test_14_no_go(self):self.assertEqual(self.report["decision"],"NO_GO_AUTOMATIQUE")
    def test_15_bad_income(self):
        x=self.d();x["cas_type_officiel_2026"]["revenu_brut_annuel_cad"]="60000";self.reject(x)
    def test_16_bad_delta(self):
        x=self.d();x["cas_type_officiel_2026"]["variation_revenu_disponible_publiee_cad"]="846";self.reject(x)
    def test_17_bad_total(self):
        x=self.d();x["cas_type_officiel_2026"]["somme_composantes_cad"]="847";self.reject(x)
    def test_18_hide_rounding(self):
        x=self.d();x["cas_type_officiel_2026"]["ecart_total_publie_moins_somme_cad"]="0";self.reject(x)
    def test_19_one_off_component_as_recurring(self):
        x=self.d();self.component(x,"EPICERIE_ENERGIE")["recurrence_2027_validee"]=True;self.reject(x)
    def test_20_change_federal_component(self):
        x=self.d();self.component(x,"ALLOC_FED_EPICERIE")["montant"]="359";self.reject(x)
    def test_21_duplicate_component(self):
        x=self.d();x["cas_type_officiel_2026"]["contributions_a_variation_publiees_cad"][0]["id"]="INDEXATION_QC";self.reject(x)
    def test_22_invent_absolute_income_2026(self):
        x=self.d();x["cas_type_officiel_2026"]["revenu_disponible_2026_cad"]="40000";self.reject(x)
    def test_23_invent_nova_gain(self):
        x=self.d();x["cas_type_officiel_2026"]["variation_causale_nova_cad"]="5000";self.reject(x)
    def test_24_2026_aid_not_year_2027(self):
        x=self.d();x["versement_ponctuel_provincial_2026"]["prorogation_2027_2036_constatee"]=True;self.reject(x)
    def test_25_conditional_eligibility(self):
        x=self.d();x["versement_ponctuel_provincial_2026"]["admissibilite"]="TOUS";self.reject(x)
    def test_26_monoparental_amount(self):
        x=self.d();self.aid(x,"MONOPARENTAL")["montant_potentiel_cad"]="200";self.reject(x)
    def test_27_couple_family_amount(self):
        x=self.d();self.aid(x,"COUPLE_AVEC_ENFANTS")["montant_potentiel_cad"]="150";self.reject(x)
    def test_28_family_max_income(self):
        x=self.d();x["allocation_famille_2026"]["par_enfant_max_cad"]="3069";self.reject(x)
    def test_29_family_min_income(self):
        x=self.d();x["allocation_famille_2026"]["par_enfant_min_cad"]="1200";self.reject(x)
    def test_30_family_single_parent_sum(self):
        x=self.d();x["allocation_famille_2026"]["famille_monoparentale_un_enfant_max_theorique_cad"]="4155";self.reject(x)
    def test_31_family_rights_not_guaranteed(self):
        x=self.d();x["allocation_famille_2026"]["montant_une_famille_reelle_cad"]="4145";self.reject(x)
    def test_32_reduced_rrq_changed(self):
        x=self.d();x["cotisations_parametres_2026"]["rrq_employe_base_taux_2026_pourcent"]="5.4";self.reject(x)
    def test_33_payroll_calc_not_invented(self):
        x=self.d();x["cotisations_parametres_2026"]["calcul_integral_de_cotisation_individuelle_cad"]="2000";self.reject(x)
    def test_34_simulrevenu_autonomous_limit(self):
        x=self.d();x["limitations"]["simulrevenu_non_adapte_travail_autonome"]=False;self.reject(x)
    def test_35_no_sovereign_budget(self):
        x=self.d();x["tiers_modelisation"]["EVALUATION_SOUVERAINETE"]["services_publics_budgetes"]=True;self.reject(x)
    def test_36_no_false_proof(self):
        x=self.d();x["preuves_manquantes"][0]["statut"]="OBTENUE";self.reject(x)
    def test_37_no_p55n_increase(self):
        x=self.d();x["integration"]["p55n_estimation_pourcent"]=54;self.reject(x)
    def test_38_source_not_faked(self):
        x=self.d();x["sources"]["REVENU_DISPONIBLE"]["url"]="https://example.org";self.reject(x)
    def test_39_cli_valid_and_no_overwrite(self):
        args=[sys.executable,str(CODE),"--references",str(DOC),
              "--p56m",str(M),"--p56l",str(L),"--barometre",str(B)]
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)["ecart_non_resolu_cad"],"1")
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/"audit.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(out)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(out)],capture_output=True).returncode,2)
    def test_40_cli_refuses_tax_rate(self):
        args=[sys.executable,str(CODE),"--references",str(DOC),
              "--p56m",str(M),"--p56l",str(L),"--barometre",str(B),
              "--exiger-taux-certifie"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
