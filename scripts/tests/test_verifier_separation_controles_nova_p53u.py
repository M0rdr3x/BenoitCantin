#!/usr/bin/env python3
"""P53U — contrôle des prérequis d'indépendance (aucune certification)."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verifier_separation_controles_nova_p53u as m

def sample(code="66023",step=None):
    s=step or m.GATES[0]
    return {
      "schema_version":"P53U-REVUE-1",
      "code_organisme":code,
      "controle":s,
      "statut_declaratif":"NON_EXAMINE",
      "role_pilote":m.ROLES[s],
      "role_relecture":m.REVIEWER,
      "presence_piece_primaire":"ABSENTE",
      "independance_declares":"INCONNUE",
      "droit_acces":"A_VERIFIER",
      "garanties_emplois_services":"A_VERIFIER",
      "traitement_consolidation":"A_VERIFIER",
      "avis_formel":"NON_OBTENU",
    }

def possible(code="66023",step=None):
    x=sample(code,step)
    x["statut_declaratif"]="REVUE_PREPAREE_NON_SIGNEE"
    x["presence_piece_primaire"]="CANDIDATE_NON_AUTHENTIFIEE"
    x["independance_declares"]="DECLAREE_NON_VERIFIEE"
    x["droit_acces"]="ACCES_POTENTIEL_NON_VERIFIE"
    x["garanties_emplois_services"]="PROTECTIONS_DECLAREES_NON_VERIFIEES"
    x["traitement_consolidation"]="RAPPROCHEMENT_DECLARE_NON_VERIFIE"
    x["avis_formel"]="SIGNE_DECLARE_NON_AUTHENTIFIE"
    return x

class P53U(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.parents=m.setup()
        cls.records=m.matrix(cls.cfg,cls.parents)
    def status(self,x):return m.review(x)["statut"]

    def test_01_six_organismes(self):self.assertEqual(len(self.parents),6)
    def test_02_eight_steps(self):self.assertEqual(len(m.GATES),8)
    def test_03_fortyeight_records(self):self.assertEqual(len(self.records),48)
    def test_04_unique_gates(self):self.assertEqual(len({(x["code_organisme"],x["controle"]) for x in self.records}),48)
    def test_05_eight_each(self):self.assertTrue(all(sum(x["code_organisme"]==c for x in self.records)==8 for c in m.CODES))
    def test_06_ordering(self):self.assertTrue(all(sorted(x["ordre_prealable"] for x in self.records if x["code_organisme"]==c)==list(range(1,9)) for c in m.CODES))
    def test_07_nominal_role_separation(self):self.assertTrue(all(x["role_pilote_prevu"]!=x["role_relecture_prevu"] for x in self.records))
    def test_08_role_not_person_independence(self):self.assertTrue(all(not x["personnes_reelles_distinctes_verifiees"] for x in self.records))
    def test_09_conflicts_not_proven(self):self.assertTrue(all(not x["absence_conflit_interets_verifiee"] for x in self.records))
    def test_10_no_signed_advice(self):self.assertTrue(all(not x["avis_independant_original_signe"] for x in self.records))
    def test_11_no_economy(self):self.assertTrue(all(x["economie_certifiee_cad"] is None for x in self.records))
    def test_12_no_go(self):self.assertTrue(all(x["decision"]==m.NO_GO for x in self.records))
    def test_13_checklist_nonempty(self):self.assertTrue(all(len(x["critere_exigences"])>=3 for x in self.records))
    def test_14_expected_total_checks(self):self.assertEqual(sum(len(x["critere_exigences"]) for x in self.records),m.setup()[0]["etat_initial"]["points_a_examiner"])
    def test_15_critical_double_que_rtc(self):self.assertTrue(all(x["controle_quebec_rtc_anti_double_elimination"] for x in self.records if x["code_organisme"] in ("23027","T0088")))
    def test_16_no_false_montreal_double(self):self.assertFalse(next(x for x in self.records if x["code_organisme"]=="66023")["controle_quebec_rtc_anti_double_elimination"])
    def test_17_initial_absent(self):self.assertEqual(self.status(sample()),"PIECE_PRIMAIRE_MANQUANTE")
    def test_18_missing_independence(self):
        x=sample();x["presence_piece_primaire"]="CANDIDATE_NON_AUTHENTIFIEE";x["statut_declaratif"]="REVUE_PREPAREE_NON_SIGNEE"
        self.assertEqual(self.status(x),"INDEPENDANCE_PERSONNELLE_NON_ETABLIE")
    def test_19_missing_advice(self):
        x=possible();x["avis_formel"]="NON_OBTENU"
        self.assertEqual(self.status(x),"AVIS_ORIGINAL_MANQUANT")
    def test_20_prep_no_cert(self):self.assertEqual(self.status(possible()),"EXAMEN_DECLARE_SANS_CERTIFICATION")
    def test_21_first_incomplete(self):
        x=sample();x["presence_piece_primaire"]="CANDIDATE_NON_AUTHENTIFIEE"
        self.assertEqual(self.status(x),"EXAMEN_EN_ATTENTE")
    def test_22_declared_block(self):
        x=possible();x["statut_declaratif"]="BLOCAGE_DECLARE"
        self.assertEqual(self.status(x),"ARRET_CONTROLE_DECLARE")
    def test_23_conflict_blocks(self):
        x=possible();x["independance_declares"]="CONFLIT_DECLARE"
        self.assertEqual(self.status(x),"ARRET_CONTROLE_DECLARE")
    def test_24_access_blocks(self):
        x=possible();x["droit_acces"]="ACCES_INTERDIT"
        self.assertEqual(self.status(x),"ARRET_CONTROLE_DECLARE")
    def test_25_jobs_blocks(self):
        x=possible();x["garanties_emplois_services"]="RISQUE_DECLARE"
        self.assertEqual(self.status(x),"ARRET_CONTROLE_DECLARE")
    def test_26_duplicate_cost_risk_blocks(self):
        x=possible();x["traitement_consolidation"]="RISQUE_DOUBLE_COMPTE"
        self.assertEqual(self.status(x),"ARRET_CONTROLE_DECLARE")
    def test_27_quebec_guard(self):
        x=possible("23027",m.GATES[3]);x["traitement_consolidation"]="A_VERIFIER"
        self.assertEqual(self.status(x),"ALERTE_QUEBEC_RTC_CONSOLIDATION_INCOMPLETE")
    def test_28_rtc_guard(self):
        x=possible("T0088",m.GATES[5]);x["traitement_consolidation"]="A_VERIFIER"
        self.assertEqual(self.status(x),"ALERTE_QUEBEC_RTC_CONSOLIDATION_INCOMPLETE")
    def test_29_quebec_remains_noncertified(self):
        x=possible("23027",m.GATES[3])
        self.assertEqual(self.status(x),"EXAMEN_DECLARE_SANS_CERTIFICATION")
    def test_30_unknown_org_rejected(self):
        x=sample("99999")
        with self.assertRaises(ValueError):self.status(x)
    def test_31_unknown_step_rejected(self):
        x=sample();x["controle"]="UNKNOWN"
        with self.assertRaises(ValueError):self.status(x)
    def test_32_role_mismatch_rejected(self):
        x=sample();x["role_pilote"]=m.REVIEWER
        with self.assertRaises(ValueError):self.status(x)
    def test_33_role_same_rejected(self):
        x=sample();x["role_relecture"]=m.ROLES[m.GATES[0]]
        with self.assertRaises(ValueError):self.status(x)
    def test_34_real_person_identifiers_rejected(self):
        x=sample();x["nom_auditeur"]="Anonyme"
        with self.assertRaises(ValueError):self.status(x)
    def test_35_fake_autocertification_rejected(self):
        x=sample();x["statut_declaratif"]="CERTIFIE"
        with self.assertRaises(ValueError):self.status(x)
    def test_36_fake_evidence_authentication_rejected(self):
        x=sample();x["presence_piece_primaire"]="AUTHENTIFIEE"
        with self.assertRaises(ValueError):self.status(x)
    def test_37_fake_independence_rejected(self):
        x=sample();x["independance_declares"]="VERIFIEE"
        with self.assertRaises(ValueError):self.status(x)
    def test_38_fake_signed_by_notary_rejected(self):
        x=sample();x["avis_formel"]="SIGNATURE_AUTHENTIFIEE"
        with self.assertRaises(ValueError):self.status(x)
    def test_39_no_journal(self):self.assertEqual(m.inspect([])["controles_declares"],0)
    def test_40_one_declarative(self):self.assertEqual(m.inspect([sample()])["controles_declares"],1)
    def test_41_next_gate_requires_predecessor(self):
        with self.assertRaises(ValueError):m.inspect([possible(step=m.GATES[1])])
    def test_42_previous_block_stops(self):
        with self.assertRaises(ValueError):m.inspect([sample(),possible(step=m.GATES[1])])
    def test_43_previous_positive_declaration_only(self):
        x=m.inspect([possible(),possible(step=m.GATES[1])])
        self.assertEqual(x["controles_declares"],2)
    def test_44_duplicate_gate(self):
        with self.assertRaises(ValueError):m.inspect([sample(),sample()])
    def test_45_different_codes_independent(self):
        self.assertEqual(m.inspect([sample(),sample("T1025")])["organismes_avec_controles_declares"],2)
    def test_46_sequential_all_eight_not_certified(self):
        t=[possible(step=g) for g in m.GATES]
        self.assertEqual(m.inspect(t)["controles_declares"],8)
        s=m.report(self.cfg,self.records,m.inspect(t))
        self.assertIsNone(s["economie_operationnelle_certifiee_cad"])
        self.assertEqual(s["avis_comptables_independants_signes"],0)
    def test_47_reporting_no_go(self):
        self.assertEqual(m.report(self.cfg,self.records,m.inspect([]))["decision"],"NO_GO_AUTOMATIQUE")
    def test_48_reporting_no_private_info(self):
        e=m.report(self.cfg,self.records,m.inspect([possible()]))
        s=json.dumps(e)
        self.assertNotIn("66023",s)
        self.assertNotIn("T1025",s)
        self.assertNotIn("SIGNE_DECLARE_NON_AUTHENTIFIE",s)
    def test_49_reporting_counts(self):
        s=m.report(self.cfg,self.records,m.inspect([]))
        self.assertEqual(s["points_controle_independance"],48)
        self.assertEqual(s["positions_documentaires_p53q"],102)
    def test_50_cli_generates(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"r.json",Path(td)/"m.json"
            self.assertEqual(m.main(["--rapport",str(a),"--matrice",str(b)]),0)
            self.assertEqual(len(json.loads(b.read_text("utf-8"))["positions"]),48)
            self.assertEqual(json.loads(a.read_text("utf-8"))["decision"],m.NO_GO)
    def test_51_cli_strict_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"r.json"
            self.assertEqual(m.main(["--rapport",str(p),"--exiger-certification-independante"]),3)
    def test_52_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            b.write_text("unchanged","utf-8")
            self.assertEqual(m.main(["--rapport",str(a),"--matrice",str(b)]),2)
            self.assertFalse(a.exists());self.assertEqual(b.read_text("utf-8"),"unchanged")
    def test_53_same_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"same.json"
            self.assertEqual(m.main(["--rapport",str(p),"--matrice",str(p)]),2)
    def test_54_cli_sample_declaration(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"d.json";f.write_text(json.dumps(possible()),"utf-8")
            p=Path(td)/"r.json"
            self.assertEqual(m.main(["--declaration",str(f),"--rapport",str(p)]),0)
            self.assertEqual(json.loads(p.read_text("utf-8"))["declarations_formellement_examinees"],1)
    def test_55_cli_invalid_order(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"d.json";f.write_text(json.dumps(possible(step=m.GATES[4])),"utf-8")
            self.assertEqual(m.main(["--declaration",str(f)]),2)
    def test_56_all_regimes_reform_not_transferred(self):
        self.assertEqual(self.cfg["verrous"]["deux_regimes_séparés"],True)
        self.assertTrue(all(x["economie_certifiee_cad"] is None for x in self.records))

if __name__=="__main__":
    unittest.main()
