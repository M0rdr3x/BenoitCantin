#!/usr/bin/env python3
"""Tests P54E: preuves de sécurité, double revue déclarée, refus de certification."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import preparer_revue_humaine_nova_p54e as m

def form():
    return {
      "schema_version":"P54E-DECLARATIONS-1",
      "source_run_p54d":40120462237,
      "sha256_copies":{
        x:m.p54d.p54d.p54b.p54a.COPIES[x][2] for x in ("ville","mamh")},
      "declarations":[],
    }

def row(cid="P54E-V-001",hyp="INDETERMINE",status="EN_EXAMEN"):
    return {
      "dossier_id":cid,
      "hypothese":hyp,
      "statut":status,
      "controles_declares":[],
      "pieces_hors_git_declarees":0,
      "contradiction":"NON_EVALUE",
      "role_examen":"EXAMINATEUR_DECLARE",
      "role_relecture":"RELECTEUR_DISTINCT_DECLARE",
      "avis_independant_signe_valide":False,
      "decision_certifiante_autorisee":False,
    }

class TestP54E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.config()
        cls.dossiers=m.baseline(cls.cfg)

    def test_01_schema(self):self.assertEqual(self.cfg["schema_version"],"P54E-1")
    def test_02_year(self):self.assertEqual(self.cfg["exercice"],2024)
    def test_03_source_run(self):self.assertEqual(self.cfg["source_run_p54d"],40120462237)
    def test_04_four_cases(self):self.assertEqual(len(self.dossiers["dossiers"]),4)
    def test_05_10_gates(self):self.assertEqual(len(m.GATES),10)
    def test_06_40_gates(self):
        self.assertEqual(sum(len(d["points"]) for d in self.dossiers["dossiers"]),40)
    def test_07_four_ids_unique(self):
        self.assertEqual(len({c["id"] for c in self.dossiers["dossiers"]}),4)
    def test_08_one_ville(self):
        self.assertEqual(sum(c["source"]=="ville" for c in self.dossiers["dossiers"]),1)
    def test_09_three_mamh(self):
        self.assertEqual(sum(c["source"]=="mamh" for c in self.dossiers["dossiers"]),3)
    def test_10_page102(self):
        self.assertEqual(self.dossiers["dossiers"][0]["page_pdf_index_zero"],102)
    def test_11_page162(self):
        self.assertTrue(all(x["page_pdf_index_zero"]==162
                 for x in self.dossiers["dossiers"][1:]))
    def test_12_positions_not_exact_folios(self):
        self.assertEqual([x["zone_approximative"] for x in self.dossiers["dossiers"]],
                         ["FIN","DEBUT","FIN","FIN"])
    def test_13_no_risky_conclusions(self):
        self.assertTrue(all(d["economie_certifiee_cad"] is None
                            for d in self.dossiers["dossiers"]))
    def test_14_no_preapproved_checks(self):
        self.assertTrue(all(not p["preuve_verifiee"]
                            for d in self.dossiers["dossiers"] for p in d["points"]))
    def test_15_no_preapproved_second_review(self):
        self.assertTrue(all(not p["contre_revision_validee"]
                            for d in self.dossiers["dossiers"] for p in d["points"]))
    def test_16_guards(self):self.assertTrue(all(self.cfg["guards"].values()))
    def test_17_96_p54b_remain(self):self.assertEqual(m.summary(self.cfg)["controles_p54b_restant"],96)
    def test_18_8_p54c_remain(self):self.assertEqual(m.summary(self.cfg)["controles_p54c_restant"],8)
    def test_19_one_date_provisional(self):
        self.assertEqual(m.summary(self.cfg)["date_probable_p54d_non_cloturee"],1)
    def test_20_no_money(self):self.assertIsNone(m.summary(self.cfg)["economies_certifiees_cad"])
    def test_21_no_jobs_cut(self):self.assertFalse(m.summary(self.cfg)["emplois_services_reduits_autorises"])
    def test_22_no_merge(self):self.assertFalse(m.summary(self.cfg)["fusion_main_autorisee"])
    def test_23_empty_valid(self):
        self.assertEqual(m.review_stats(form(),self.cfg)["fiches_declarations"],0)
    def test_24_one_valid(self):
        f=form();f["declarations"].append(row())
        self.assertEqual(m.review_stats(f,self.cfg)["fiches_declarations"],1)
    def test_25_all_four_valid(self):
        f=form()
        f["declarations"]=[row(cid) for cid,*other in m.CASES]
        self.assertEqual(m.review_stats(f,self.cfg)["fiches_declarations"],4)
    def test_26_pending_not_certified(self):
        f=form();f["declarations"]=[row()]
        s=m.summary(self.cfg,m.review_stats(f,self.cfg))
        self.assertEqual(s["dossiers_certifies"],0)
        self.assertEqual(s["controles_effectivement_attestes"],0)
    def test_27_recorded_not_certified(self):
        f=form();d=row(status="DOCUMENTE_NON_ATTESTE")
        d["controles_declares"]=list(m.GATES)
        d["pieces_hors_git_declarees"]=3
        f["declarations"]=[d]
        result=m.summary(self.cfg,m.review_stats(f,self.cfg))
        self.assertEqual(result["declarations_locales"]["checks_declares_examines_non_attestes"],10)
        self.assertEqual(result["dossiers_certifies"],0)
        self.assertIsNone(result["economies_certifiees_cad"])
    def test_28_documented_without_pieces(self):
        f=form();f["declarations"]=[row(status="DOCUMENTE_NON_ATTESTE")]
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_29_duplicate_id(self):
        f=form();f["declarations"]=[row(),row()]
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_30_wrong_id(self):
        f=form();f["declarations"]=[row("P54E-UNKNOWN")]
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_31_no_raw_values_or_context(self):
        f=form();r=row();r["texte_source"]="Nom privé"
        f["declarations"]=[r]
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_32_no_signed_claim(self):
        f=form();r=row();r["avis_independant_signe_valide"]=True
        f["declarations"]=[r]
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_33_no_auto_go(self):
        f=form();r=row();r["decision_certifiante_autorisee"]=True
        f["declarations"]=[r]
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_34_roles_not_verified(self):
        f=form();r=row();r["role_relecture"]="CERTIFIE"
        f["declarations"]=[r]
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_35_unknown_hypothesis(self):
        f=form();r=row(hyp="ECONOMIE_VALIDEE")
        f["declarations"]=[r]
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_36_bad_status(self):
        f=form();r=row(status="RESOLU")
        f["declarations"]=[r]
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_37_unknown_check(self):
        f=form();r=row();r["controles_declares"]=["ECONOMIE"]
        f["declarations"]=[r]
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_38_duplicate_check(self):
        f=form();r=row();r["controles_declares"]=[m.GATES[0],m.GATES[0]]
        f["declarations"]=[r]
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_39_negative_pieces(self):
        f=form();r=row();r["pieces_hors_git_declarees"]=-1
        f["declarations"]=[r]
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_40_non2024_hash(self):
        f=form();f["sha256_copies"]["ville"]="0"*64
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_41_bad_run(self):
        f=form();f["source_run_p54d"]=0
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_42_private_only_outside_repo(self):
        with self.assertRaises(ValueError):m.local_file(m.CFG)
    def test_43_too_many_records(self):
        f=form();f["declarations"]=[row()]*5
        with self.assertRaises(ValueError):m.review_stats(f,self.cfg)
    def test_44_local_file(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.json"
            p.write_text(json.dumps(form()),"utf-8")
            self.assertEqual(m.local_file(str(p)),p)
    def test_45_cli_no_net(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"r.json",Path(td)/"d.json"
            self.assertEqual(m.main(["--rapport",str(a),"--dossiers",str(b)]),0)
            report=json.loads(a.read_text("utf-8"))
            self.assertEqual(report["points_de_revue"],40)
            self.assertEqual(len(json.loads(b.read_text("utf-8"))["dossiers"]),4)
    def test_46_cli_signed_refusal(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(m.main(["--rapport",str(Path(td)/"r.json"),
                                     "--exiger-avis-signe"]),3)
    def test_47_cli_overwrite_denied(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/"r.json";a.write_text("keep","utf-8")
            self.assertEqual(m.main(["--rapport",str(a)]),2)
            self.assertEqual(a.read_text("utf-8"),"keep")
    def test_48_duplicate_output_paths(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/"r.json"
            self.assertEqual(m.main(["--rapport",str(a),"--dossiers",str(a)]),2)
    def test_49_cli_local_declaration(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"private.json"
            data=form();data["declarations"]=[row()]
            f.write_text(json.dumps(data),"utf-8")
            r=Path(td)/"report.json"
            self.assertEqual(m.main(["--revue-locale",str(f),"--rapport",str(r)]),0)
            self.assertEqual(json.loads(r.read_text("utf-8"))["declarations_locales"]["fiches_declarations"],1)
    def test_50_no_sensitive_raw_output(self):
        f=form();r=row();r["hypothese"]="DATE_PROBABLE"
        f["declarations"]=[r]
        s=json.dumps(m.summary(self.cfg,m.review_stats(f,self.cfg)))
        self.assertNotIn("hypothese",s)
        self.assertNotIn("dossier_id",s)

if __name__=="__main__":
    unittest.main()
