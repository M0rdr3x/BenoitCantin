#!/usr/bin/env python3
"""P53V : tests de refus, de contradiction et d'absence de clôture."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reconcilier_ecarts_nova_p53v as m

def example(code="66023",category=None,role="COLLECTE_DOCUMENTAIRE",state="NON_INSTRUIT"):
    c=category or m.CATEGORIES[0]
    return {
        "schema_version":"P53V-DECLARATION-1",
        "code_organisme":code,
        "categorie":c,
        "role_source":role,
        "statut_declaratif":state,
        "niveau_piece":"ABSENTE",
        "code_correctif":m.FIX[c] if state in m.CORR else "AUCUN",
        "perimetre_comptable":"NON_ETABLI",
        "droit_acces":"A_VERIFIER",
        "emplois_services":"A_VERIFIER",
        "independance_personnelle":"A_VERIFIER",
    }

def both(category=None):
    return [
        example(category=category),
        example(category=category,role="REVUE_QUALITE_INDEPENDANTE"),
    ]

class CheckP53V(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.organismes=m.sources()
        cls.rows=m.build(cls.cfg,cls.organismes)
    def examine(self,d):return m.evaluate(d)
    def summary(self,entries):
        return m.report(self.cfg,self.rows,m.reconcile(entries))

    def test_01_six_organismes(self):self.assertEqual(len(self.organismes),6)
    def test_02_eight_categories(self):self.assertEqual(len(m.CATEGORIES),8)
    def test_03_48_positions(self):self.assertEqual(len(self.rows),48)
    def test_04_48_unique(self):self.assertEqual(len({(r["code_organisme"],r["categorie_a_examiner"]) for r in self.rows}),48)
    def test_05_eight_per_organisme(self):
        self.assertTrue(all(sum(r["code_organisme"]==c for r in self.rows)==8 for c in m.CODES))
    def test_06_every_item_p53u(self):
        self.assertTrue(all(r["controle_p53u_associe"] in m.p53u.GATES for r in self.rows))
    def test_07_corrective_mapping(self):
        self.assertTrue(all(r["correctif_potentiel"]==m.FIX[r["categorie_a_examiner"]] for r in self.rows))
    def test_08_all_uninvestigated(self):
        self.assertTrue(all(r["statut"]=="NON_INSTRUIT" for r in self.rows))
    def test_09_no_finding_invented(self):
        self.assertTrue(all(not r["ecart_reel_etabli"] for r in self.rows))
    def test_10_no_authorized_closure(self):
        self.assertTrue(all(not r["cloture_par_personne_habilitee"] for r in self.rows))
    def test_11_no_certified_repair(self):
        self.assertTrue(all(not r["correctif_effectivement_realise_verifie"] for r in self.rows))
    def test_12_no_savings(self):
        self.assertTrue(all(r["economie_certifiee_cad"] is None for r in self.rows))
    def test_13_no_external_signatures(self):
        self.assertTrue(all(r["avis_independants_signes"]==0 for r in self.rows))
    def test_14_no_go_all(self):
        self.assertTrue(all(r["decision"]==m.NO_GO for r in self.rows))
    def test_15_exactly_two_special_notices(self):
        self.assertEqual(sum(r["signalement_documentaire_preexistant"]=="PRECAUTION_METHODOLOGIQUE_CONSOLIDATION_P53P" for r in self.rows),2)
    def test_16_only_quebec_rtc_special(self):
        self.assertEqual({r["code_organisme"] for r in self.rows if r["signalement_documentaire_preexistant"]=="PRECAUTION_METHODOLOGIQUE_CONSOLIDATION_P53P"},{"23027","T0088"})
    def test_17_social_priority(self):
        self.assertEqual(m.priority("66023","EMPLOIS_ET_SERVICES_NON_DEMONTRES"),"PROTECTION_DROITS_ET_SERVICES_A_VERIFIER")
    def test_18_access_priority(self):
        self.assertEqual(m.priority("66023","DROIT_ACCES_ET_CONFIDENTIALITE_INCERTAINS"),"PROTECTION_DROITS_ET_SERVICES_A_VERIFIER")
    def test_19_rtc_consolidation_priority(self):
        self.assertEqual(m.priority("T0088","ELIMINATIONS_ANTERIEURES_A_RECONCILIER"),"PRIORITE_RAPPROCHEMENT_CONSOLIDATION_QUEBEC_RTC")
    def test_20_other_consolidation_not_fact(self):
        self.assertEqual(m.priority("66023","ELIMINATIONS_ANTERIEURES_A_RECONCILIER"),"RECHERCHE_PROBATOIRE_SANS_CONCLUSION")
    def test_21_evaluate_structural(self):
        self.assertFalse(self.examine(example())["preuve_authentifiee"])
    def test_22_unknown_code_rejected(self):
        with self.assertRaises(ValueError):self.examine(example(code="FICTIF"))
    def test_23_unknown_category_rejected(self):
        x=example();x["categorie"]="CORRUPTION"
        with self.assertRaises(ValueError):self.examine(x)
    def test_24_unknown_role_rejected(self):
        x=example();x["role_source"]="DIRECTEUR_CERTIFICATEUR"
        with self.assertRaises(ValueError):self.examine(x)
    def test_25_closed_status_disallowed(self):
        x=example();x["statut_declaratif"]="CORRECTIF_CLOS_ET_VERIFIE"
        with self.assertRaises(ValueError):self.examine(x)
    def test_26_signed_evidence_disallowed(self):
        x=example();x["niveau_piece"]="DOCUMENT_AUTHENTIFIE"
        with self.assertRaises(ValueError):self.examine(x)
    def test_27_extra_personal_data_rejected(self):
        x=example();x["email_responsable"]="private@example.invalid"
        with self.assertRaises(ValueError):self.examine(x)
    def test_28_no_fake_action_if_undone(self):
        x=example();x["code_correctif"]=m.FIX[m.CATEGORIES[0]]
        with self.assertRaises(ValueError):self.examine(x)
    def test_29_missing_action_if_proposed(self):
        x=example(state="CORRECTIF_PROPOSE_NON_VERIFIE");x["code_correctif"]="AUCUN"
        with self.assertRaises(ValueError):self.examine(x)
    def test_30_action_must_match_category(self):
        x=example(state="CORRECTIF_EXAMINE_NON_CERTIFIE");x["code_correctif"]=m.FIX[m.CATEGORIES[1]]
        with self.assertRaises(ValueError):self.examine(x)
    def test_31_proposed_not_certified(self):
        self.assertFalse(self.examine(example(state="CORRECTIF_PROPOSE_NON_VERIFIE"))["correction_validee"])
    def test_32_examined_still_not_certified(self):
        self.assertFalse(self.examine(example(state="CORRECTIF_EXAMINE_NON_CERTIFIE"))["correction_validee"])
    def test_33_block_by_status(self):
        self.assertTrue(self.examine(example(state="BLOCAGE_DECLARE"))["bloquant_declare"])
    def test_34_block_by_no_legal_access(self):
        x=example();x["droit_acces"]="ACCES_INTERDIT"
        self.assertTrue(self.examine(x)["bloquant_declare"])
    def test_35_block_by_labor(self):
        x=example();x["emplois_services"]="RISQUE_DECLARE"
        self.assertTrue(self.examine(x)["bloquant_declare"])
    def test_36_block_by_conflict(self):
        x=example();x["independance_personnelle"]="CONFLIT_DECLARE"
        self.assertTrue(self.examine(x)["bloquant_declare"])
    def test_37_block_by_scope(self):
        x=example();x["perimetre_comptable"]="INCOHERENCE_DECLAREE"
        self.assertTrue(self.examine(x)["bloquant_declare"])
    def test_38_no_auto_go(self):
        self.assertEqual(self.summary([])["decision"],m.NO_GO)
    def test_39_empty_reconcile(self):
        self.assertEqual(m.reconcile([])["positions_avec_declarations"],0)
    def test_40_single_opinion(self):
        self.assertEqual(m.reconcile([example()])["statuts_agreges"]["AVIS_UNIQUE_DECLARE_SANS_PREUVE"],1)
    def test_41_concordant_unexamined(self):
        self.assertEqual(m.reconcile(both())["statuts_agreges"]["NON_INSTRUIT"],1)
    def test_42_concordant_proposed(self):
        o=both();o[0]["statut_declaratif"]="CORRECTIF_PROPOSE_NON_VERIFIE";o[0]["code_correctif"]=m.FIX[m.CATEGORIES[0]]
        o[1]["statut_declaratif"]="CORRECTIF_PROPOSE_NON_VERIFIE";o[1]["code_correctif"]=m.FIX[m.CATEGORIES[0]]
        self.assertEqual(m.reconcile(o)["statuts_agreges"]["AVIS_CONCORDANTS_DECLARATIFS_NON_CERTIFIES"],1)
    def test_43_contradictory_states_retained(self):
        o=[example(),example(role="REVUE_QUALITE_INDEPENDANTE",state="ECART_POTENTIEL_DECLARE")]
        self.assertEqual(m.reconcile(o)["positions_avec_contradictions"],1)
    def test_44_contradiction_with_block_retained(self):
        o=[example(),example(role="REVUE_QUALITE_INDEPENDANTE",state="BLOCAGE_DECLARE")]
        s=m.reconcile(o)
        self.assertEqual(s["statuts_agreges"]["CONTRADICTION_AVEC_BLOCAGE_NON_RESOLUE"],1)
        self.assertEqual(s["positions_avec_blocages"],1)
    def test_45_concordant_block_not_closed(self):
        a=example(state="BLOCAGE_DECLARE")
        b=example(role="REVUE_QUALITE_INDEPENDANTE",state="BLOCAGE_DECLARE")
        self.assertEqual(m.reconcile([a,b])["statuts_agreges"]["BLOCAGE_DECLARE_NON_RESOLU"],1)
    def test_46_duplicate_role_rejected(self):
        with self.assertRaises(ValueError):m.reconcile([example(),example()])
    def test_47_multi_org_is_independent(self):
        s=m.reconcile([example(),example(code="T1025")])
        self.assertEqual(s["positions_avec_declarations"],2)
    def test_48_multi_category_same_org(self):
        s=m.reconcile([example(),example(category=m.CATEGORIES[1])])
        self.assertEqual(s["positions_avec_declarations"],2)
    def test_49_no_certified_savings_if_concordant(self):
        x=self.summary(both())
        self.assertIsNone(x["economies_certifiees_cad"])
        self.assertEqual(x["correctifs_independamment_valides"],0)
    def test_50_no_real_finding_if_conflicting(self):
        x=self.summary([example(),example(role="REVUE_QUALITE_INDEPENDANTE",state="ECART_POTENTIEL_DECLARE")])
        self.assertEqual(x["ecarts_financiers_reels_authentifies"],0)
    def test_51_report_48_and_162(self):
        s=self.summary([])
        self.assertEqual(s["positions_d_examen"],48)
        self.assertEqual(s["exigences_p53u_en_suspens"],162)
    def test_52_report_no_private_data(self):
        s=json.dumps(self.summary([example()]))
        self.assertNotIn("66023",s)
        self.assertNotIn("private@example.invalid",s)
    def test_53_cli_generates_plan(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"b.json",Path(td)/"p.json"
            self.assertEqual(m.main(["--bilan",str(a),"--registre",str(b)]),0)
            self.assertEqual(len(json.loads(b.read_text("utf-8"))["lignes"]),48)
            self.assertEqual(json.loads(a.read_text("utf-8"))["positions_d_examen"],48)
    def test_54_cli_no_false_closure(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/"b.json"
            self.assertEqual(m.main(["--bilan",str(a),"--exiger-correctifs-clos"]),3)
    def test_55_cli_prevents_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"b.json",Path(td)/"p.json"
            b.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(a),"--registre",str(b)]),2)
            self.assertFalse(a.exists());self.assertEqual(b.read_text("utf-8"),"keep")
    def test_56_cli_same_path_denied(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"file.json"
            self.assertEqual(m.main(["--bilan",str(p),"--registre",str(p)]),2)
    def test_57_cli_process_sample_declaration(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"d.json";f.write_text(json.dumps(example()),"utf-8")
            b=Path(td)/"b.json"
            self.assertEqual(m.main(["--declaration",str(f),"--bilan",str(b)]),0)
            self.assertEqual(json.loads(b.read_text("utf-8"))["positions_avec_declarations"],1)
    def test_58_cli_rejects_duplicate_declaration(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"d.json";f.write_text(json.dumps(example()),"utf-8")
            self.assertEqual(m.main(["--declaration",str(f),"--declaration",str(f)]),2)
    def test_59_cli_cross_checks_two_roles(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            a.write_text(json.dumps(example()),"utf-8")
            b.write_text(json.dumps(example(role="REVUE_QUALITE_INDEPENDANTE",state="ECART_POTENTIEL_DECLARE")),"utf-8")
            r=Path(td)/"r.json"
            self.assertEqual(m.main(["--declaration",str(a),"--declaration",str(b),"--bilan",str(r)]),0)
            self.assertEqual(json.loads(r.read_text("utf-8"))["positions_avec_contradictions_declarees"],1)
    def test_60_regimes_stay_separate(self):
        self.assertTrue(self.cfg["verrous"]["regimes_constitutionnels_non_additifs"])
    def test_61_empty_evidence_is_not_zero_money(self):
        self.assertTrue(all(x["economie_certifiee_cad"] is None for x in self.rows))
    def test_62_independent_names_not_in_git(self):
        self.assertTrue(all("responsable_nominatif" not in x for x in self.rows))
    def test_63_statuses_no_closed(self):
        self.assertTrue(all("CERTIFIE" not in s and "CLOS" not in s for s in m.STATES))
    def test_64_historical_reference_year(self):
        self.assertTrue(all(x["exercice"]==2024 for x in self.rows))

if __name__=="__main__":
    unittest.main()
