#!/usr/bin/env python3
"""P54G : tests synthétiques des transitions et de la confidentialité."""
import copy
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import controler_decisions_procedurales_nova_p54g as m

def fake_upstream(state="EN_ATTENTE",roles=0):
    dossiers=[]
    for cid in m.config()["dossiers"]:
        dossiers.append({
          "dossier_id":cid,"etat_procedural":state,
          "roles_declares_recus":roles,
          "avis_independant_signe":False,"dossier_certifie":False})
    return {"dossiers":dossiers,
            "fiches_roles_recues":roles*4,
            "statuts":{state:4},
            "preuves_locales_verifiees_par_sha":0,
            "points_declares_examines":0,
            "desaccords_documentaires":4 if state=="DESACCORD" else 0}

def decision(cid="P54E-V-001",action="AJOURNER",reason="PREUVE_NON_CORROBOREE",needed=None):
    return {
      "dossier_id":cid,"action_suivi":action,"motif":reason,
      "pieces_a_demander":list(needed or []),
      "identite_verifiee":False,
      "avis_independant_signe_verifie":False,
      "cloture_financiere_autorisee":False,
      "transmission_externe_effectuee":False}

def doc(rows):
    d=m.decision_template(m.config())
    d["suivis"]=rows
    return d

def private_json(path,data):
    path.write_text(json.dumps(data),encoding="utf-8")
    os.chmod(path,0o600)

class TestP54G(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.config()

    def test_01_schema(self):self.assertEqual(self.cfg["schema_version"],"P54G-1")
    def test_02_year(self):self.assertEqual(self.cfg["exercice"],2024)
    def test_03_p54f_source(self):self.assertEqual(self.cfg["jalon_precedent"],"P54F")
    def test_04_four_cases(self):self.assertEqual(len(self.cfg["dossiers"]),4)
    def test_05_case_id(self):self.assertIn("P54E-V-001",self.cfg["dossiers"])
    def test_06_no_go(self):self.assertEqual(self.cfg["etat_initial"]["decision"],m.NO_GO)
    def test_07_no_saved_money(self):self.assertIsNone(self.cfg["etat_initial"]["economies_certifiees_cad"])
    def test_08_no_signed(self):self.assertEqual(self.cfg["etat_initial"]["avis_independants_signes"],0)
    def test_09_no_default_reviewer(self):self.assertEqual(m.report(self.cfg)["declarations_P54F_recues"],0)
    def test_10_initial_open(self):
        self.assertEqual(m.report(self.cfg)["statuts_source_P54F"],{"EN_ATTENTE":4})
    def test_11_initial_all_manual(self):self.assertEqual(m.report(self.cfg)["dossiers_a_resoudre_manuellement"],4)
    def test_12_no_certified_cases(self):self.assertEqual(m.report(self.cfg)["dossiers_certifies"],0)
    def test_13_no_bank_amounts(self):self.assertEqual(m.report(self.cfg)["montants_financiers_certifies"],0)
    def test_14_no_job_cuts(self):self.assertFalse(m.report(self.cfg)["emplois_services_reduits_autorises"])
    def test_15_no_merge(self):self.assertFalse(m.report(self.cfg)["fusion_main_autorisee"])
    def test_16_guards_present(self):self.assertTrue(all(self.cfg["guardrails"].values()))
    def test_17_five_actions(self):self.assertEqual(len(m.ACTIONS),5)
    def test_18_seven_motives(self):self.assertEqual(len(m.REASONS),7)
    def test_19_seven_proof_requests(self):self.assertEqual(len(m.NEEDED),7)
    def test_20_all_states_have_actions(self):
        self.assertEqual(set(m.ALLOWED),set(m.p54f.ETATS))
    def test_21_no_go_action(self):
        self.assertTrue(all("APPROUVER" not in x for v in m.ALLOWED.values() for x in v))
    def test_22_no_source_record_edit(self):
        self.assertEqual(m.decision_template(self.cfg)["suivis"],[])
    def test_23_empty_allowed(self):
        s=m.validate_decisions(doc([]),self.cfg,fake_upstream())
        self.assertEqual(s["suivis_declares"],0)
    def test_24_pending_adjourn(self):
        s=m.validate_decisions(doc([decision()]),self.cfg,fake_upstream())
        self.assertEqual(s["suivis_declares"],1)
    def test_25_pending_requests_docs(self):
        d=decision(action="DEMANDER_PIECES",needed=["PDF_PUBLIC_ORIGINAL"])
        s=m.validate_decisions(doc([d]),self.cfg,fake_upstream())
        self.assertEqual(s["actions_par_categorie"]["DEMANDER_PIECES"],1)
    def test_26_no_empty_request_docs(self):
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([decision(action="DEMANDER_PIECES")]),self.cfg,fake_upstream())
    def test_27_pending_no_expert(self):
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([decision(action="SAISIR_EXPERT_INDEPENDANT")]),self.cfg,fake_upstream())
    def test_28_unilateral_needs_second(self):
        s=m.validate_decisions(doc([decision(action="DEMANDER_CONTRE_REVUE")]),self.cfg,fake_upstream("EXAMEN_UNIQUE",1))
        self.assertEqual(s["suivis_declares"],1)
    def test_29_unilateral_no_signed_expert(self):
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([decision(action="SAISIR_EXPERT_INDEPENDANT")]),self.cfg,fake_upstream("EXAMEN_UNIQUE",1))
    def test_30_disagreement_expert_allowed_as_referral(self):
        s=m.validate_decisions(doc([decision(action="SAISIR_EXPERT_INDEPENDANT",reason="DESACCORD_OUVERT")]),self.cfg,fake_upstream("DESACCORD",2))
        self.assertEqual(s["dossiers_en_desaccord_ou_suspendus"],4)
    def test_31_disagreement_no_direct_closure(self):
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([decision(action="MAINTENIR_SUSPENSION")]),self.cfg,fake_upstream("DESACCORD",2))
    def test_32_suspended_stays_suspended(self):
        s=m.validate_decisions(doc([decision(action="MAINTENIR_SUSPENSION")]),self.cfg,fake_upstream("SUSPENDU",1))
        self.assertEqual(s["lignes"][0]["etat_procedural_source"],"SUSPENDU")
        self.assertFalse(s["lignes"][0]["dossier_clos"])
    def test_33_suspension_no_request_docs(self):
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([decision(action="DEMANDER_PIECES",needed=["PAGE_ET_FOLIO"])]),self.cfg,fake_upstream("SUSPENDU",1))
    def test_34_incomplete_agreement_more_proofs(self):
        s=m.validate_decisions(doc([decision(action="DEMANDER_PIECES",needed=["PERIMETRE_ET_PERIODE"])]),self.cfg,fake_upstream("CONCORDANCE_DECLARATIVE_INCOMPLETE",2))
        self.assertEqual(s["suivis_declares"],1)
    def test_35_documented_can_refer_expert_not_certify(self):
        s=m.validate_decisions(doc([decision(action="SAISIR_EXPERT_INDEPENDANT")]),self.cfg,fake_upstream("CONCORDANCE_DECLARATIVE_DOCUMENTEE_NON_ATTESTEE",2))
        r=m.report(self.cfg,fake_upstream("CONCORDANCE_DECLARATIVE_DOCUMENTEE_NON_ATTESTEE",2),s)
        self.assertEqual(r["avis_independants_signes_authentifies"],0)
        self.assertIsNone(r["economies_certifiees_cad"])
    def test_36_duplicate_id(self):
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([decision(),decision()]),self.cfg,fake_upstream())
    def test_37_unknown_id(self):
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([decision(cid="UNKNOWN")]),self.cfg,fake_upstream())
    def test_38_unknown_reason(self):
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([decision(reason="GROS_GAIN")]),self.cfg,fake_upstream())
    def test_39_unknown_pieces(self):
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([decision(needed=["SECRET_NAME"])]),self.cfg,fake_upstream())
    def test_40_extra_free_text(self):
        d=decision();d["commentaires"]="texte sensible"
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([d]),self.cfg,fake_upstream())
    def test_41_fake_signed(self):
        d=decision();d["avis_independant_signe_verifie"]=True
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([d]),self.cfg,fake_upstream())
    def test_42_fake_closure(self):
        d=decision();d["cloture_financiere_autorisee"]=True
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([d]),self.cfg,fake_upstream())
    def test_43_fake_external_transfer(self):
        d=decision();d["transmission_externe_effectuee"]=True
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([d]),self.cfg,fake_upstream())
    def test_44_fake_identity(self):
        d=decision();d["identite_verifiee"]=True
        with self.assertRaises(ValueError):
            m.validate_decisions(doc([d]),self.cfg,fake_upstream())
    def test_45_wrong_anchor_sha(self):
        d=doc([]);d["sources_sha256"]["mamh"]="0"*64
        with self.assertRaises(ValueError):
            m.validate_decisions(d,self.cfg,fake_upstream())
    def test_46_wrong_run(self):
        d=doc([]);d["p54d_run"]=42
        with self.assertRaises(ValueError):
            m.validate_decisions(d,self.cfg,fake_upstream())
    def test_47_report_no_personal_evidence(self):
        s=m.validate_decisions(doc([decision()]),self.cfg,fake_upstream())
        r=json.dumps(m.report(self.cfg,fake_upstream(),s))
        self.assertNotIn("sources_sha256",r)
        self.assertNotIn("identite_verifiee",r)
    def test_48_cli_neutral(self):
        with tempfile.TemporaryDirectory() as temp:
            f=Path(temp)/"bilan.json"
            self.assertEqual(m.main(["--bilan",str(f)]),0)
            self.assertEqual(json.loads(f.read_text("utf-8"))["dossiers_a_resoudre_manuellement"],4)
    def test_49_cli_go_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            f=Path(temp)/"bilan.json"
            self.assertEqual(m.main(["--bilan",str(f),"--exiger-go"]),3)
    def test_50_cli_private_decisions_require_reviews(self):
        self.assertEqual(m.main(["--decisions-locales","/unknown/path"]),2)
    def test_51_cli_existing_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            f=Path(temp)/"bilan.json";f.write_text("original","utf-8")
            self.assertEqual(m.main(["--bilan",str(f)]),2)
            self.assertEqual(f.read_text("utf-8"),"original")
    def test_52_cli_private_template(self):
        with tempfile.TemporaryDirectory() as temp:
            f=Path(temp)/"decision.json"
            self.assertEqual(m.main(["--modele-prive",str(f)]),0)
            self.assertEqual(stat.S_IMODE(f.stat().st_mode),0o600)
    def test_53_cli_private_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            f=folder/"reviews.json";d=folder/"decisions.json";out=folder/"public.json"
            review=m.p54f.private_template(m.p54f.configuration())
            private_json(f,review)
            private_json(d,doc([decision()]))
            self.assertEqual(m.main(["--revues-locales",str(f),
                                      "--decisions-locales",str(d),"--bilan",str(out)]),0)
            record=json.loads(out.read_text("utf-8"))
            self.assertEqual(record["actions_suivi_declarees"],1)
            self.assertEqual(record["dossiers_certifies"],0)
    def test_54_cli_private_permissions(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);f=folder/"reviews.json"
            f.write_text(json.dumps(m.p54f.private_template(m.p54f.configuration())),"utf-8")
            os.chmod(f,0o644)
            self.assertEqual(m.main(["--revues-locales",str(f)]),2)

if __name__=="__main__":
    unittest.main()
