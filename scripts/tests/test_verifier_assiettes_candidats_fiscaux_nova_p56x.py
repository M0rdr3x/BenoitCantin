"""P56X : fiscalite historique 2021/2023 n'est pas un taux Nova 2027."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/verifier_assiettes_candidats_fiscaux_nova_p56x.py"
FILE_NAMES=(
"P56X_ASSIETTES_HISTORIQUES_ET_VERROU_TAUX_NOVA_2027_2028.json",
"P56K_ASSIETTES_PARTICULIERS_SOCIETES_CREDITS_SOURCES_OFFICIELLES.json",
"P56R_INVENTAIRE_EXHAUSTIF_CATEGORIES_RECETTES_ET_PONT_FISCAL_2026_2031.json",
"P56V_PONT_FINANCEMENT_SERVICES_OPTIONS_FISCALES_VGQ_2027_2029.json",
"P56W_CREDITS_REMBOURSABLES_2023_PAR_CATEGORIE_ET_TRANCHES_PROTECTION.json",
"P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
"P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
)
FILES=[ROOT/"projets/projet-nova/etudes"/name for name in FILE_NAMES]
spec=importlib.util.spec_from_file_location("p56x",SCRIPT)
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class TestP56X(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=[json.loads(f.read_text(encoding="utf-8")) for f in FILES]
        cls.report=p.audit(*cls.data)
    def clone(self,n=0):
        return copy.deepcopy(self.data[n])
    def reject(self,d,n=0):
        a=list(self.data);a[n]=d
        with self.assertRaises(ValueError):
            p.audit(*a)
    def test_01_jalon(self):self.assertEqual(self.report["jalon"],"P56X")
    def test_02_score(self):self.assertEqual(self.report["score_estime_pourcent"],53)
    def test_03_gap(self):self.assertEqual(self.report["points_restants_estimes"],47)
    def test_04_2023_base(self):self.assertEqual(self.report["personnes_2023_assiette_imposable_mcad"],"372261")
    def test_05_2021_base(self):self.assertEqual(self.report["societes_2021_assiette_imposable_mcad"],"95784")
    def test_06_pit_total_income_ratio(self):self.assertEqual(self.report["personnes_2023_taux_observe_revenu_total_pourcent"],"9.53")
    def test_07_pit_taxable_ratio(self):self.assertEqual(self.report["personnes_2023_taux_observe_revenu_imposable_pourcent"],"10.96")
    def test_08_corporate_ratio(self):self.assertEqual(self.report["societes_2021_ratio_observe_pourcent"],"10.44")
    def test_09_revenue_baseline_2027(self):self.assertEqual(self.report["recettes_reference_2027_revenu_mcad"],"68093")
    def test_10_revenue_at_risk_2027(self):self.assertEqual(self.report["recettes_a_remplacer_scenario_integral_mcad"],"42875")
    def test_11_balance_2027(self):self.assertEqual(self.report["financement_statique_equilibre_2027_mcad"],"48570")
    def test_12_no_tax_rate(self):self.assertFalse(self.report["taux_2027_nova_certifie"])
    def test_13_no_2027_base(self):self.assertFalse(self.report["assiettes_2027_nova_connues"])
    def test_14_mixed_years(self):self.assertFalse(self.report["comparabilite_assiettes_historique"])
    def test_15_no_sovereign_budget(self):self.assertFalse(self.report["deux_regimes_budgetises"])
    def test_16_no_go(self):self.assertEqual(self.report["decision"],"NO_GO_AUTOMATIQUE")
    def test_17_mutate_pit_taxable(self):
        d=self.clone();d["donnees_historiques"]["personnes_2023"]["revenu_imposable_mcad"]="372262";self.reject(d)
    def test_18_mutate_pit_total(self):
        d=self.clone();d["donnees_historiques"]["personnes_2023"]["revenu_total_mcad"]="0";self.reject(d)
    def test_19_mutate_pit_tax(self):
        d=self.clone();d["donnees_historiques"]["personnes_2023"]["impot_a_payer_mcad"]="100";self.reject(d)
    def test_20_mutate_pit_credit(self):
        d=self.clone();d["donnees_historiques"]["personnes_2023"]["credits_remboursables_mcad"]="1";self.reject(d)
    def test_21_gross_vs_taxable_rate(self):
        d=self.clone();d["donnees_historiques"]["personnes_2023"]["ratio_observe_impot_a_payer_sur_revenu_total_pourcent"]="10.96";self.reject(d)
    def test_22_do_not_claim_2023_rate_nova(self):
        d=self.clone();d["donnees_historiques"]["personnes_2023"]["ratio_historique_n_est_pas_taux_nova"]=False;self.reject(d)
    def test_23_mutate_corp_taxable(self):
        d=self.clone();d["donnees_historiques"]["societes_2021"]["revenu_imposable_quebec_mcad"]="95785";self.reject(d)
    def test_24_mutate_corp_tax(self):
        d=self.clone();d["donnees_historiques"]["societes_2021"]["impot_revenu_societes_mcad"]="9999";self.reject(d)
    def test_25_do_not_rate_corporate(self):
        d=self.clone();d["donnees_historiques"]["societes_2021"]["ratio_historique_n_est_pas_taux_nova"]=False;self.reject(d)
    def test_26_no_sum_different_years(self):
        d=self.clone();d["donnees_historiques"]["assiettes_personnes_et_societes_agregees_mcad"]="468045";self.reject(d)
    def test_27_no_fabricated_2027_taxable(self):
        d=self.clone();d["etude_taux_candidat_bloquee"]["QUEBEC_DANS_CANADA"]["assiette_personnes_imposable_2027_2028_mcad"]="500000";self.reject(d)
    def test_28_no_fabricated_2027_corporate(self):
        d=self.clone();d["etude_taux_candidat_bloquee"]["QUEBEC_DANS_CANADA"]["assiette_societes_imposable_2027_2028_mcad"]="150000";self.reject(d)
    def test_29_no_fabricated_anti_haven(self):
        d=self.clone();d["etude_taux_candidat_bloquee"]["QUEBEC_DANS_CANADA"]["rendement_antiparadis_net_additionnel_2027_2028_mcad"]="5000";self.reject(d)
    def test_30_no_2027_tax_rate(self):
        d=self.clone();d["etude_taux_candidat_bloquee"]["QUEBEC_DANS_CANADA"]["taux_personnes_candidat_pourcent"]="20.0";self.reject(d)
    def test_31_no_sovereign_federal_free(self):
        d=self.clone();d["etude_taux_candidat_bloquee"]["QUEBEC_SOUVERAIN"]["revenus_competences_federales_nets_mcad"]="20000";self.reject(d)
    def test_32_no_sovereign_duty_free(self):
        d=self.clone();d["etude_taux_candidat_bloquee"]["QUEBEC_SOUVERAIN"]["depenses_nouvelles_competences_mcad"]="0";self.reject(d)
    def test_33_no_mixed_revenue_as_rate(self):
        d=self.clone();d["repere_2027_2028"]["ratio_62_97_ne_constitue_pas_un_taux_de_taxation"]=False;self.reject(d)
    def test_34_mutate_budget(self):
        d=self.clone();d["repere_2027_2028"]["besoin_financement_arithmetique_pour_solde_legal_zero_si_retrait_integral_mcad"]="42875";self.reject(d)
    def test_35_no_divide_by_2023(self):
        d=self.clone();d["regles"]["pas_de_taux_nova_par_division_2027_sur_assiette_particuliers_2023"]=False;self.reject(d)
    def test_36_no_false_poor_households_gains(self):
        d=self.clone();d["etude_taux_candidat_bloquee"]["QUEBEC_DANS_CANADA"]["deciles_cout_menages_2027_2028"]={"premier":100};self.reject(d)
    def test_37_no_self_certification(self):
        d=self.clone();d["completude"]["avis_independants_signes"]=3;self.reject(d)
    def test_38_do_not_close_proofs(self):
        d=self.clone();d["preuves_prioritaires"][0]["statut"]="VALIDE";self.reject(d)
    def test_39_wrong_p56k(self):
        d=self.clone(1);d["particuliers_2023"]["revenu_imposable_mcad"]="400000";self.reject(d,1)
    def test_40_wrong_p56r(self):
        d=self.clone(2);next(y for y in d["rapprochement_annees"] if y["exercice"]=="2027-2028")["impots_sur_revenu_actuels_mcad"]="1";self.reject(d,2)
    def test_41_wrong_p56v(self):
        d=self.clone(3);d["comptes_par_annee"][0]["revenus_consolides_publics_mcad"]="999";self.reject(d,3)
    def test_42_wrong_p56w(self):
        d=self.clone(4);d["controle_arrondis"]["ligne_totale_officielle_mcad"]="9306";self.reject(d,4)
    def test_43_wrong_p55n(self):
        d=self.clone(6);d["score_estimatif"]=100;self.reject(d,6)
    def test_44_wrong_base_date(self):
        d=self.clone();d["sources"]["officiel_a17"]["date_donnee"]=2027;self.reject(d)
    def test_45_cli_and_no_overwrite(self):
        args=[sys.executable,str(SCRIPT),"--assiettes",str(FILES[0]),"--p56k",str(FILES[1]),
              "--p56r",str(FILES[2]),"--p56v",str(FILES[3]),"--p56w",str(FILES[4]),
              "--p56o",str(FILES[5]),"--barometre",str(FILES[6])]
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)["personnes_2023_assiette_imposable_mcad"],"372261")
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/"out.json"
            self.assertEqual(subprocess.run(args+["--rapport",str(target)],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+["--rapport",str(target)],capture_output=True).returncode,2)
    def test_46_cli_refuses_rate(self):
        args=[sys.executable,str(SCRIPT),"--assiettes",str(FILES[0]),"--p56k",str(FILES[1]),
              "--p56r",str(FILES[2]),"--p56v",str(FILES[3]),"--p56w",str(FILES[4]),
              "--p56o",str(FILES[5]),"--barometre",str(FILES[6]),"--publier-taux-nova"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)

if __name__=="__main__":
    unittest.main()
