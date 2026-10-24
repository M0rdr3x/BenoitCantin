#!/usr/bin/env python3
"""P54F : cas synthétiques de revue contradictoire et intégrité privée."""
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import gerer_contre_revues_nova_p54f as m

def reviewer(role="EXAMINATEUR",identity="REV001",
             hypothesis="INDETERMINE",status="EN_EXAMEN",
             contradiction="NON_EVALUE",checks=None,proofs=None,
             case="P54E-V-001"):
    return {
      "dossier_id":case,"role":role,"code_relecteur":identity,
      "hypothese":hypothesis,"statut":status,"contradiction":contradiction,
      "controles_declares":list(checks or []),
      "pieces_referencees":list(proofs or []),
      "avis_independant_signe_valide":False,
      "certification_financiere_autorisee":False,
    }

def create_evidence(folder):
    sub=Path(folder)/"preuves"
    sub.mkdir()
    f=sub/"note_test.bin"
    b=b"SYNTHESE SANS AUCUN CHIFFRE DE GAIN"
    f.write_bytes(b)
    os.chmod(f,0o600)
    return {"id":"PIECE-001","type":"NOTE_ANALYSE_PRIVEE",
            "relative_path":"preuves/note_test.bin",
            "sha256":hashlib.sha256(b).hexdigest()}

def package(folder,proof=True):
    p=m.private_template(m.configuration())
    if proof:
        p["pieces"]=[create_evidence(folder)]
    file=Path(folder)/"fiche_privee.json"
    file.write_text(json.dumps(p),encoding="utf-8")
    os.chmod(file,0o600)
    return file,p

class TestP54F(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()
    def test_01_config(self):self.assertEqual(self.cfg["schema_version"],"P54F-1")
    def test_02_source_year(self):self.assertEqual(self.cfg["exercice"],2024)
    def test_03_p54d_run(self):self.assertEqual(self.cfg["source_run_p54d"],40120462237)
    def test_04_four_dossiers(self):self.assertEqual(len(self.cfg["dossiers"]),4)
    def test_05_two_roles(self):self.assertEqual(len(m.ROLES),2)
    def test_06_eighty_controls(self):self.assertEqual(len(m.p54e.GATES)*len(m.ROLES)*4,80)
    def test_07_no_initial_economy(self):self.assertIsNone(self.cfg["etat_initial"]["economies_certifiees_cad"])
    def test_08_essential_protections(self):self.assertTrue(all(self.cfg["protections"].values()))
    def test_09_neutral_four_waiting(self):
        r=m.summary(self.cfg)
        self.assertEqual(r["statuts_de_revues"],{"EN_ATTENTE":4})
        self.assertEqual(r["positions_controle_qualitatif_2_roles"],80)
    def test_10_neutral_no_go(self):self.assertEqual(m.summary(self.cfg)["decision"],m.NO_GO)
    def test_11_neutral_no_certification(self):
        r=m.summary(self.cfg)
        self.assertEqual(r["dossiers_clos_et_certifies"],0)
        self.assertEqual(r["identites_independantes_authentifiees"],0)
    def test_12_empty_valid(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t,proof=False)
            s=m.validate_local(p,f,self.cfg)
            self.assertEqual(s["fiches_roles_recues"],0)
            self.assertEqual(s["preuves_locales_verifiees_par_sha"],0)
    def test_13_one_examination(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t,proof=False)
            p["revues"]=[reviewer()]
            s=m.validate_local(p,f,self.cfg)
            self.assertEqual(s["statuts"]["EXAMEN_UNIQUE"],1)
    def test_14_second_role_only(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t,proof=False)
            p["revues"]=[reviewer("CONTRE_REVISEUR","REV002")]
            self.assertEqual(m.validate_local(p,f,self.cfg)["statuts"]["EXAMEN_UNIQUE"],1)
    def test_15_matching_no_proof_incomplete(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t,proof=False)
            p["revues"]=[reviewer(),reviewer("CONTRE_REVISEUR","REV002")]
            self.assertEqual(m.validate_local(p,f,self.cfg)["statuts"]["CONCORDANCE_DECLARATIVE_INCOMPLETE"],1)
    def test_16_two_roles_documented_still_no_go(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t)
            p["revues"]=[
                reviewer(status="DOCUMENTE_NON_ATTESTE",checks=m.p54e.GATES,proofs=["PIECE-001"]),
                reviewer("CONTRE_REVISEUR","REV002",status="DOCUMENTE_NON_ATTESTE",
                         checks=m.p54e.GATES,proofs=["PIECE-001"])]
            s=m.validate_local(p,f,self.cfg)
            self.assertEqual(s["statuts"]["CONCORDANCE_DECLARATIVE_DOCUMENTEE_NON_ATTESTEE"],1)
            report=m.summary(self.cfg,s)
            self.assertEqual(report["dossiers_clos_et_certifies"],0)
            self.assertIsNone(report["economies_certifiees_cad"])
    def test_17_disagreement_hypotheses(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t,proof=False)
            p["revues"]=[reviewer(),reviewer("CONTRE_REVISEUR","REV002",hypothesis="DATE_PROBABLE")]
            self.assertEqual(m.validate_local(p,f,self.cfg)["desaccords_documentaires"],1)
    def test_18_disagreement_status(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t,proof=False)
            p["revues"]=[reviewer(),reviewer("CONTRE_REVISEUR","REV002",status="CONTRADICTOIRE")]
            self.assertEqual(m.validate_local(p,f,self.cfg)["statuts"]["DESACCORD"],1)
    def test_19_open_contradiction_stays_open(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t,proof=False)
            p["revues"]=[reviewer(contradiction="QUESTION_OUVERTE"),
                         reviewer("CONTRE_REVISEUR","REV002",contradiction="QUESTION_OUVERTE")]
            self.assertEqual(m.validate_local(p,f,self.cfg)["statuts"]["DESACCORD"],1)
    def test_20_suspend_takes_precedence(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t,proof=False)
            p["revues"]=[reviewer(status="SUSPENDU"),
                         reviewer("CONTRE_REVISEUR","REV002")]
            self.assertEqual(m.validate_local(p,f,self.cfg)["statuts"]["SUSPENDU"],1)
    def test_21_same_role_twice_denied(self):
        x=[reviewer(),reviewer(identity="REV002")]
        with self.assertRaises(ValueError):m.classify_reviews(x,set(),self.cfg)
    def test_22_same_reviewer_in_two_roles_denied(self):
        x=[reviewer(),reviewer("CONTRE_REVISEUR","REV001")]
        with self.assertRaises(ValueError):m.classify_reviews(x,set(),self.cfg)
    def test_23_bad_reviewer_code(self):
        with self.assertRaises(ValueError):m.classify_reviews([reviewer(identity="Real Name")],set(),self.cfg)
    def test_24_bad_case(self):
        with self.assertRaises(ValueError):m.classify_reviews([reviewer(case="P54E-UNKNOWN")],set(),self.cfg)
    def test_25_no_fake_professional_signature(self):
        x=reviewer();x["avis_independant_signe_valide"]=True
        with self.assertRaises(ValueError):m.classify_reviews([x],set(),self.cfg)
    def test_26_no_auto_certification(self):
        x=reviewer();x["certification_financiere_autorisee"]=True
        with self.assertRaises(ValueError):m.classify_reviews([x],set(),self.cfg)
    def test_27_raw_text_disallowed(self):
        x=reviewer();x["piece_texte"]="contenu prive"
        with self.assertRaises(ValueError):m.classify_reviews([x],set(),self.cfg)
    def test_28_wrong_control_denied(self):
        x=reviewer(checks=["UNE_ECONOMIE"])
        with self.assertRaises(ValueError):m.classify_reviews([x],set(),self.cfg)
    def test_29_duplicate_checks_denied(self):
        x=reviewer(checks=[m.p54e.GATES[0],m.p54e.GATES[0]])
        with self.assertRaises(ValueError):m.classify_reviews([x],set(),self.cfg)
    def test_30_documented_without_proofs_denied(self):
        x=reviewer(status="DOCUMENTE_NON_ATTESTE",checks=m.p54e.GATES)
        with self.assertRaises(ValueError):m.classify_reviews([x],set(),self.cfg)
    def test_31_proof_integrity_real_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t)
            self.assertEqual(m.verify_proofs(f,p["pieces"]),{"PIECE-001"})
    def test_32_proof_digest_tampering_denied(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t)
            p["pieces"][0]["sha256"]="0"*64
            with self.assertRaises(ValueError):m.verify_proofs(f,p["pieces"])
    def test_33_private_permissions_required(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t)
            os.chmod(Path(t)/"preuves/note_test.bin",0o644)
            with self.assertRaises(ValueError):m.verify_proofs(f,p["pieces"])
    def test_34_path_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t)
            p["pieces"][0]["relative_path"]="preuves/../fiche_privee.json"
            with self.assertRaises(ValueError):m.verify_proofs(f,p["pieces"])
    def test_35_symlink_blocked(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t)
            (Path(t)/"preuves/link.bin").symlink_to("note_test.bin")
            p["pieces"][0]["relative_path"]="preuves/link.bin"
            with self.assertRaises(ValueError):m.verify_proofs(f,p["pieces"])
    def test_36_review_root_not_inside_git(self):
        with self.assertRaises(ValueError):m.private_file(m.CONFIG,65536)
    def test_37_template_created_private(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"modele.json"
            m.write_new(p,m.private_template(self.cfg),private=True)
            self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600)
            self.assertEqual(json.loads(p.read_text("utf-8"))["pieces"],[])
    def test_38_private_template_refused_inside_git(self):
        with self.assertRaises(ValueError):
            m.write_new(m.ROOT/"p54f_interdit_prive.json",{},private=True)
    def test_39_aggregate_does_not_leak_reviewer(self):
        r=m.summary(self.cfg,m.classify_reviews([reviewer(identity="REV009")],set(),self.cfg))
        self.assertNotIn("REV009",json.dumps(r))
    def test_40_aggregate_no_evidence_names(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t)
            r=m.summary(self.cfg,m.validate_local(p,f,self.cfg))
            self.assertNotIn("note_test.bin",json.dumps(r))
            self.assertNotIn("sha256",json.dumps(r))
    def test_41_wrong_original_hash_denied(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t,proof=False)
            p["sources_sha256"]["ville"]="0"*64
            with self.assertRaises(ValueError):m.validate_local(p,f,self.cfg)
    def test_42_duplicate_evidence_id_denied(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t)
            p["pieces"].append(copy.deepcopy(p["pieces"][0]))
            with self.assertRaises(ValueError):m.validate_local(p,f,self.cfg)
    def test_43_cli_neutral(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/"result.json"
            self.assertEqual(m.main(["--bilan",str(target)]),0)
            self.assertEqual(json.loads(target.read_text("utf-8"))["dossiers_attendus"],4)
    def test_44_cli_refuses_signed_certification(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(m.main(["--bilan",str(Path(t)/"r.json"),
                                     "--exiger-certification"]),3)
    def test_45_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/"bilan.json";f.write_text("preserve","utf-8")
            self.assertEqual(m.main(["--bilan",str(f)]),2)
            self.assertEqual(f.read_text("utf-8"),"preserve")
    def test_46_cli_local_private(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t)
            p["revues"]=[reviewer()]
            f.write_text(json.dumps(p),"utf-8")
            output=Path(t)/"bilan.json"
            self.assertEqual(m.main(["--revues-locales",str(f),"--bilan",str(output)]),0)
            self.assertEqual(json.loads(output.read_text("utf-8"))["declarations_recues"],1)
    def test_47_cli_private_read_denied_if_world_readable(self):
        with tempfile.TemporaryDirectory() as t:
            f,p=package(t,proof=False)
            os.chmod(f,0o644)
            self.assertEqual(m.main(["--revues-locales",str(f)]),2)
    def test_48_cli_two_same_outputs(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/"same.json"
            self.assertEqual(m.main(["--bilan",str(f),"--modele-prive",str(f)]),2)

def make_guard_test(flag):
    def testcase(self):
        self.assertTrue(self.cfg["protections"][flag])
    return testcase

for i,flag in enumerate(sorted(m.FLAGS),49):
    setattr(TestP54F,"test_%02d_garde_fou"%i,make_guard_test(flag))

if __name__=="__main__":
    unittest.main()
