"""P56O : non-réévaluation sans preuve et conditions objectives avant 100 %."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/evaluer_cloture_programme_nova_p56o.py"
PATHS=[
 ROOT/"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
 ROOT/"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json",
 ROOT/"projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json",
 ROOT/"projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json",
 ROOT/"projets/projet-nova/etudes/P56M_CADRE_MICROSIMULATION_REVENUS_MENAGES_2027_2036.json",
 ROOT/"projets/projet-nova/etudes/P56N_CAS_TYPES_2026_REFERENCES_OFFICIELLES_PRESTATIONS_ET_LIMITES.json"
]
spec=importlib.util.spec_from_file_location("p56o",SCRIPT)
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

class TestP56O(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=[json.loads(p.read_text(encoding="utf-8")) for p in PATHS]
        cls.report=a.analyser(*cls.data)
    def alter(self,index=0):
        return copy.deepcopy(self.data[index])
    def refuse(self,changed,index=0):
        args=list(self.data);args[index]=changed
        with self.assertRaises(ValueError):
            a.analyser(*args)
    def gate(self,d,id):
        return next(x for x in d["portes"] if x["id"]==id)
    def task(self,d,id):
        return next(x for x in d["priorites"] if x["id"]==id)
    def axis(self,d,id):
        return next(x for x in d["axes"] if x["id"]==id)

    def test_01_stage(self):
        self.assertEqual(self.report["jalon"],"P56O")
    def test_02_current_score(self):
        self.assertEqual(self.report["score_estime_pourcent"],53)
    def test_03_remaining_points(self):
        self.assertEqual(self.report["points_restants_estimes"],47)
    def test_04_score_interval(self):
        self.assertEqual(self.report["fourchette_prudente_pourcent"],[45,60])
    def test_05_axes_count(self):
        self.assertEqual(self.report["axes_total"],8)
    def test_06_two_axes_full(self):
        self.assertEqual(self.report["axes_au_maximum"],1)
    def test_07_fiscal_remaining_15(self):
        self.assertEqual(self.report["points_restants_par_axe"]["FISCALITE"],15)
    def test_08_sector_remaining_6(self):
        self.assertEqual(self.report["points_restants_par_axe"]["SECTEURS"],6)
    def test_09_transition_remaining_6(self):
        self.assertEqual(self.report["points_restants_par_axe"]["TRANSITION"],6)
    def test_10_independent_remaining_10(self):
        self.assertEqual(self.report["points_restants_par_axe"]["EXPERTISE"],10)
    def test_11_adoption_remaining_5(self):
        self.assertEqual(self.report["points_restants_par_axe"]["ADOPTION"],5)
    def test_12_ten_doors(self):
        self.assertEqual(self.report["portes_total"],10)
    def test_13_zero_closed_doors(self):
        self.assertEqual(self.report["portes_fermees_documentairement"],0)
    def test_14_12_priorities(self):
        self.assertEqual(self.report["priorites_total"],12)
    def test_15_zero_closed_priorities(self):
        self.assertEqual(self.report["priorites_closes_documentairement"],0)
    def test_16_60_budget_cuts(self):
        self.assertEqual(self.report["trajectoires_regime_scenario_annee"],60)
    def test_17_600_missing_budget_values(self):
        self.assertEqual(self.report["valeurs_budgetaires_p52b_inconnues"],600)
    def test_18_20_unproven_tax_governance(self):
        self.assertEqual(self.report["preuves_fiscales_p52a_non_validees"],20)
    def test_19_720_unknown_incidence_declared(self):
        self.assertEqual(self.report["incidences_p52d_inconnues_declares"],720)
    def test_20_zero_real_household_cases(self):
        self.assertEqual(self.report["cas_menages_reels_p56m"],0)
    def test_21_zero_expert_opinion(self):
        self.assertEqual(self.report["avis_independants_signes"],0)
    def test_22_no_automatic_readiness(self):
        self.assertFalse(self.report["candidat_a_attestation_humaine_finale"])
    def test_23_not_complete(self):
        self.assertFalse(self.report["programme_termine_et_atteste"])
    def test_24_no_date_invented(self):
        self.assertIsNone(self.report["date_de_fin_validee"])
    def test_25_no_go(self):
        self.assertEqual(self.report["decision"],"NO_GO_AUTOMATIQUE")
    def test_26_no_score_from_commits(self):
        self.assertFalse(self.report["nombre_commits_influence_score"])
    def test_27_edit_score_claim(self):
        d=self.alter();d["metadonnees_qualification"]["estimation_centrale_pourcent"]=72;self.refuse(d)
    def test_28_edit_remaining_claim(self):
        d=self.alter();d["metadonnees_qualification"]["nb_points_estimes_restant"]=0;self.refuse(d)
    def test_29_axis_fiscal_falsified(self):
        d=self.alter();self.axis(d,"FISCALITE")["points_estimes"]=20;self.refuse(d)
    def test_30_false_range(self):
        d=self.alter();d["metadonnees_qualification"]["intervalle_prudent_pourcent"]=[53,100];self.refuse(d)
    def test_31_duplicate_gate(self):
        d=self.alter();d["portes"][0]["id"]="LEGAL";self.refuse(d)
    def test_32_fake_door_proven(self):
        d=self.alter();self.gate(d,"FIN_BUDGET")["statut"]="PROUVE";self.refuse(d)
    def test_33_fake_door_has_nonexistent_document(self):
        d=self.alter();self.gate(d,"FIN_INC")["piece_justificative_id"]="document-invente";self.refuse(d)
    def test_34_disable_external_gate(self):
        d=self.alter();self.gate(d,"EXPERTS")["approbation_humaine_formelle"]=True;self.refuse(d)
    def test_35_dummy_evidence(self):
        d=self.alter();self.gate(d,"FIN_MUNICIPAL")["critere_objectif"]="OK";self.refuse(d)
    def test_36_remove_legal_proof(self):
        d=self.alter();d["portes"]=[g for g in d["portes"] if g["id"]!="LEGAL"];self.refuse(d)
    def test_37_task_fake_close(self):
        d=self.alter();self.task(d,"N01")["statut"]="CLOS";self.refuse(d)
    def test_38_task_fake_external_review(self):
        d=self.alter();self.task(d,"N09")["controle_qualite_independant"]=True;self.refuse(d)
    def test_39_priority_missing(self):
        d=self.alter();d["priorites"].pop();self.refuse(d)
    def test_40_priority_missing_wave(self):
        d=self.alter();d["vagues"][-1]["priorites"]=[];self.refuse(d)
    def test_41_false_100_announcement(self):
        d=self.alter();d["definition_terminee"]["etat_actuel_termine"]=True;self.refuse(d)
    def test_42_fake_finished_date(self):
        d=self.alter();d["definition_terminee"]["date_termine"]="2026-11-08";self.refuse(d)
    def test_43_wrong_completion_definition(self):
        d=self.alter();d["definition_terminee"]["p52b_budget_decennal_sans_null_et_scenarios_reconcilies"]=False;self.refuse(d)
    def test_44_fake_signed_reviews(self):
        d=self.alter();d["inventaire_manquants"]["avis_independants_signes"]=3;self.refuse(d)
    def test_45_invent_new_2027_budget(self):
        d=self.alter(2)
        d["regimes"]["QUEBEC_DANS_CANADA"]["trajectoires"]["central"][0]["recettes"]["impot_revenu_net"]="1"
        self.refuse(d,2)
    def test_46_missing_budget_year(self):
        d=self.alter(2);d["regimes"]["QUEBEC_SOUVERAIN"]["trajectoires"]["stress"].pop()
        self.refuse(d,2)
    def test_47_fake_fiscal_proof(self):
        d=self.alter(3);d["required_evidence"][0]["statut"]="VALIDE";self.refuse(d,3)
    def test_48_unrecognized_household_coverage(self):
        d=self.alter(4);d["modele_cas"]["montants_reels_popules"]=160;self.refuse(d,4)
    def test_49_distributive_coverage_fake(self):
        d=self.alter(5);d["integration"]["p52d_incidences_inconnues"]=0;self.refuse(d,5)
    def test_50_original_barometer_not_altered(self):
        d=self.alter(1);d["score_estimatif"]=100;self.refuse(d,1)
    def test_51_incorrect_separation_program_power(self):
        d=self.alter();del d["separation_statuts"]["APPLIQUE_PAR_LE_GOUVERNEMENT"];self.refuse(d)
    def test_52_no_main_auto_merge(self):
        d=self.alter();d["prohibitions"]["ne_pas_fusionner_main_automatiquement"]=False;self.refuse(d)
    def test_53_cli_json(self):
        args=[sys.executable,str(SCRIPT),"--cloture",str(PATHS[0]),
             "--barometre",str(PATHS[1]),"--p52b",str(PATHS[2]),
             "--p52a",str(PATHS[3]),"--p56m",str(PATHS[4]),"--p56n",str(PATHS[5])]
        res=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(res.returncode,0,res.stderr)
        self.assertEqual(json.loads(res.stdout)["points_restants_estimes"],47)
    def test_54_cli_cannot_claim_done(self):
        args=[sys.executable,str(SCRIPT),"--cloture",str(PATHS[0]),
             "--barometre",str(PATHS[1]),"--p52b",str(PATHS[2]),
             "--p52a",str(PATHS[3]),"--p56m",str(PATHS[4]),
             "--p56n",str(PATHS[5]),"--declarer-programme-termine"]
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,3)
    def test_55_cli_report_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"report.json"
            args=[sys.executable,str(SCRIPT),"--cloture",str(PATHS[0]),
                 "--barometre",str(PATHS[1]),"--p52b",str(PATHS[2]),
                 "--p52a",str(PATHS[3]),"--p56m",str(PATHS[4]),
                 "--p56n",str(PATHS[5]),"--rapport",str(path)]
            self.assertEqual(subprocess.run(args,capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args,capture_output=True).returncode,2)

if __name__=="__main__":
    unittest.main()
