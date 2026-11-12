"""P56M : tests d'exercices fictifs, contrôle des prestations et refus d'un faux GO."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
CODE=ROOT/"scripts/simuler_revenu_disponible_menages_nova_p56m.py"
REG=ROOT/"projets/projet-nova/etudes/P56M_CADRE_MICROSIMULATION_REVENUS_MENAGES_2027_2036.json"
P56L=ROOT/"projets/projet-nova/etudes/P56L_BASE_DISTRIBUTIVE_PARTICULIERS_2023_CREDITS_ET_QUINTILES.json"
P55N=ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
spec=importlib.util.spec_from_file_location("p56m",CODE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def scenario():
    out={}
    for group,fields in (
        ("revenus",m.INCOME),("prestations",m.BENEFITS),
        ("prelevements",m.LEVIES),("essentiels",m.ESSENTIAL)):
        out[group]={k:"0" for k in fields}
    out["revenus"]["salaire_brut"]="50000"
    out["prestations"]["credits_remboursables_quebec"]="1600"
    out["prestations"]["credits_remboursables_federal"]="900"
    out["prelevements"].update({
      "impot_quebec_net":"4000","impot_federal_net":"5500","cotisation_rrq":"2500",
      "cotisation_ae":"600","cotisation_rqap":"350","prime_ramq":"100"
    })
    out["essentiels"].update({"logement_cash":"18000","alimentation_ttc":"6000",
        "transport_ttc":"2800","energie_ttc":"2400","autres_depenses_essentielles_ttc":"2000"})
    return out

def case():
    baseline=scenario()
    after=copy.deepcopy(baseline)
    after["prelevements"]["impot_quebec_net"]="3400"
    after["prestations"]["credits_remboursables_quebec"]="300"
    return {
      "type":"EXERCICE_FICTIF_SANS_POUVOIR",
      "usage_reel_interdit":True,"historique_personnel_reel":False,
      "archetype_id":"M02","regime_id":"QUEBEC_DANS_CANADA","annee":2027,
      "hypothese_pouvoir_d_achat":"MÊME_MENAGE_MÊME_ANNEE_MÊME_UNITE_DE_PRIX",
      "composition":{"adultes":1,"enfants":0,"aines":0},
      "region":"QUEBEC_FICTIF_NON_REPRESENTATIF",
      "reference":baseline,"candidat":after
    }

class TestP56M(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cadre=json.loads(REG.read_text(encoding="utf-8"))
        cls.l=json.loads(P56L.read_text(encoding="utf-8"))
        cls.b=json.loads(P55N.read_text(encoding="utf-8"))
        cls.report=m.controler(cls.cadre,cls.l,cls.b)
    def changed(self):return copy.deepcopy(self.cadre)
    def reject(self,d):
        with self.assertRaises(ValueError):
            m.controler(d,self.l,self.b)
    def reject_case(self,c):
        with self.assertRaises(ValueError):
            m.exercice_fictif(self.cadre,c)
    def test_01_schema(self):self.assertEqual(self.cadre["schema_version"],"P56M-1")
    def test_02_years(self):self.assertEqual(self.report["annees"],10)
    def test_03_eight_profiles(self):self.assertEqual(self.report["archetypes"],8)
    def test_04_two_regimes(self):self.assertEqual(self.report["regimes"],2)
    def test_05_160_slots(self):self.assertEqual(self.report["unites_archetype_regime_annee_a_renseigner"],160)
    def test_06_zero_real_values(self):self.assertEqual(self.report["montants_reels_certifies"],0)
    def test_07_ten_gates(self):self.assertEqual(self.report["conditions_non_demontrees"],10)
    def test_08_no_business_effects(self):self.assertFalse(self.report["effets_PME_chiffres"])
    def test_09_no_household_effects(self):self.assertFalse(self.report["revenus_disponibles_nova_calcules"])
    def test_10_no_purchasing_certification(self):self.assertFalse(self.report["protection_pouvoir_achat_certifiee"])
    def test_11_p52b_unknown(self):self.assertEqual(self.report["p52b_inconnus"],600)
    def test_12_p52d_unknown(self):self.assertEqual(self.report["p52d_inconnus"],720)
    def test_13_score(self):self.assertEqual(self.report["p55n_score_estime"],53)
    def test_14_no_go(self):self.assertEqual(self.report["decision"],"NO_GO_AUTOMATIQUE")
    def test_15_baseline_disposable(self):
        self.assertEqual(m._scenario(scenario())["revenu_disponible"],"39450")
    def test_16_baseline_after_essentials(self):
        self.assertEqual(m._scenario(scenario())["reste_apres_essentiels"],"8250")
    def test_17_candidate_disposable(self):
        self.assertEqual(m.exercice_fictif(self.cadre,case())["candidat"]["revenu_disponible"],"38750")
    def test_18_candidate_fails_protection(self):
        self.assertEqual(m.exercice_fictif(self.cadre,case())["variation_cash_apres_essentiels_cad"],"-700")
    def test_19_loss_requires_compensation(self):
        self.assertEqual(m.exercice_fictif(self.cadre,case())["compensation_minimale_arithmetique_fictive_cad"],"700")
    def test_20_candidate_is_not_certified(self):
        self.assertFalse(m.exercice_fictif(self.cadre,case())["gain_reel_de_menage_certifie"])
    def test_21_public_services_unfunded(self):
        self.assertFalse(m.exercice_fictif(self.cadre,case())["financement_des_services_demontre"])
    def test_22_fiction_never_go(self):
        self.assertEqual(m.exercice_fictif(self.cadre,case())["decision"],"NO_GO_AUTOMATIQUE")
    def test_23_complete_gain_does_not_certify(self):
        c=case();c["candidat"]["prestations"]["credits_remboursables_quebec"]="1600"
        x=m.exercice_fictif(self.cadre,c)
        self.assertEqual(x["variation_cash_apres_essentiels_cad"],"600")
        self.assertEqual(x["compensation_minimale_arithmetique_fictive_cad"],"0")
        self.assertFalse(x["gain_reel_de_menage_certifie"])
    def test_24_cost_increase_independently_reported(self):
        c=case();c["candidat"]["essentiels"]["logement_cash"]="18500"
        x=m.exercice_fictif(self.cadre,c)
        self.assertEqual(x["variation_revenu_disponible_cad"],"-700")
        self.assertEqual(x["variation_cash_apres_essentiels_cad"],"-1200")
    def test_25_missing_is_not_zero(self):
        c=case();c["candidat"]["prestations"]["prestations_federal"]=None
        x=m.exercice_fictif(self.cadre,c)
        self.assertIsNone(x["variation_revenu_disponible_cad"])
        self.assertIn("prestations_federal",x["candidat"]["champs_manquants"])
    def test_26_all_null_fields_return_incomplete(self):
        c=case()
        for grp in c["reference"]:
            for key in c["reference"][grp]:
                c["reference"][grp][key]=None
        x=m.exercice_fictif(self.cadre,c)
        self.assertIsNone(x["variation_cash_apres_essentiels_cad"])
        self.assertEqual(len(x["reference"]["champs_manquants"]),25)
    def test_27_hypothesis_flag_required(self):
        c=case();c["usage_reel_interdit"]=False;self.reject_case(c)
    def test_28_real_data_flag_forbidden(self):
        c=case();c["historique_personnel_reel"]=True;self.reject_case(c)
    def test_29_only_declared_profiles(self):
        c=case();c["archetype_id"]="M09";self.reject_case(c)
    def test_30_wrong_composition_rejected(self):
        c=case();c["composition"]["enfants"]=1;self.reject_case(c)
    def test_31_wrong_year_rejected(self):
        c=case();c["annee"]=2026;self.reject_case(c)
    def test_32_end_boundary_included(self):
        c=case();c["annee"]=2036;self.assertEqual(m.exercice_fictif(self.cadre,c)["annee"],2036)
    def test_33_2037_rejected(self):
        c=case();c["annee"]=2037;self.reject_case(c)
    def test_34_no_federal_tax_power(self):
        c=case();c["candidat"]["prelevements"]["impot_federal_net"]="0";self.reject_case(c)
    def test_35_no_ei_power(self):
        c=case();c["candidat"]["prelevements"]["cotisation_ae"]="0";self.reject_case(c)
    def test_36_market_income_static(self):
        c=case();c["candidat"]["revenus"]["salaire_brut"]="56000";self.reject_case(c)
    def test_37_no_double_sales_tax(self):
        c=case();c["reference"]["essentiels"]["TVQ"]="100";self.reject_case(c)
    def test_38_no_malformed_negative_amount(self):
        c=case();c["reference"]["prestations"]["prestations_quebec"]="-100";self.reject_case(c)
    def test_39_no_float_amount(self):
        c=case();c["reference"]["revenus"]["salaire_brut"]=50000.1;self.reject_case(c)
    def test_40_no_nan(self):
        c=case();c["reference"]["revenus"]["salaire_brut"]="NaN";self.reject_case(c)
    def test_41_no_extra_precision(self):
        c=case();c["reference"]["revenus"]["salaire_brut"]="50000.999";self.reject_case(c)
    def test_42_disable_service_claim(self):
        c=self.changed();c["regimes"][0]["services_publics_sous_financement_p52b"]=True;self.reject(c)
    def test_43_cannot_inflate_maturity(self):
        c=self.changed();c["issues_conserves"]["p55n_score_estimatif"]=90;self.reject(c)
    def test_44_no_false_real_coverage(self):
        c=self.changed();c["modele_cas"]["couverture_observee"]=160;self.reject(c)
    def test_45_no_missing_profile(self):
        c=self.changed();c["archetypes"].pop();self.reject(c)
    def test_46_no_false_published_assurance(self):
        c=self.changed();c["conditions_publication"][0]["ok"]=True;self.reject(c)
    def test_47_no_fake_credits_funding(self):
        c=self.changed();c["issues_conserves"]["economie_nova_certifiee_mcad"]="15000";self.reject(c)
    def test_48_source_replacement_not_allowed(self):
        c=self.changed();c["sources_methodologiques"][0]["url"]="https://example.org";self.reject(c)
    def test_49_baseline_mismatch_p56l(self):
        base=copy.deepcopy(self.l);base["p52d_incidences_inconnues"]=0
        with self.assertRaises(ValueError):
            m.controler(self.cadre,base,self.b)
    def test_50_p55n_still_53(self):
        b=copy.deepcopy(self.b);b["score_estimatif"]=100
        with self.assertRaises(ValueError):
            m.controler(self.cadre,self.l,b)
    def test_51_cli_validation(self):
        cmd=[sys.executable,str(CODE),"--cadre",str(REG),
             "--p56l",str(P56L),"--barometre",str(P55N)]
        r=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)["p55n_score_estime"],53)
    def test_52_cli_fiction_requires_opt_in(self):
        with tempfile.TemporaryDirectory() as temp:
            f=Path(temp)/"f.json";f.write_text(json.dumps(case()),encoding="utf-8")
            cmd=[sys.executable,str(CODE),"--cadre",str(REG),
                 "--p56l",str(P56L),"--barometre",str(P55N),"--exercice",str(f)]
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
            run=subprocess.run(cmd+["--autoriser-exercice-fictif"],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout)["exercice_fictif"]["variation_cash_apres_essentiels_cad"],"-700")
    def test_53_cli_refuses_certification(self):
        cmd=[sys.executable,str(CODE),"--cadre",str(REG),
             "--p56l",str(P56L),"--barometre",str(P55N),
             "--exiger-microsimulation-certifiee"]
        self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,3)
    def test_54_report_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            f=Path(temp)/"r.json"
            cmd=[sys.executable,str(CODE),"--cadre",str(REG),
                 "--p56l",str(P56L),"--barometre",str(P55N),"--rapport",str(f)]
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
    def test_55_sovereignty_mode_is_fiction_only(self):
        c=case();c["regime_id"]="QUEBEC_SOUVERAIN"
        x=m.exercice_fictif(self.cadre,c)
        self.assertFalse(x["financement_des_services_demontre"])
        self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")

if __name__=="__main__":
    unittest.main()
