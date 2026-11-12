#!/usr/bin/env python3
"""Validation du premier pilote public 2024; sans PDF confidentiel."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import constituer_dossier_pilote_nova_p53w as m

def view(fid="F02_RTC_SOMHAC",status="LECTURE_DECLAREE_NON_AUTHENTIFIEE"):
    return {
      "schema_version":"P53W-DECLARATION-1",
      "fait_id":fid,"source_id":m.PAGES[fid][0],
      "index_pdf":m.PAGES[fid][1],"appreciation":status,
      "avis_expert_verifie":False,
    }

class Pilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.load()
        cls.by={x["id"]:x for x in cls.cfg["constats"]}
    def test_01_ville(self):self.assertEqual(self.cfg["code_ville"],"23027")
    def test_02_rtc(self):self.assertEqual(self.cfg["code_rtc"],"T0088")
    def test_03_2024(self):self.assertEqual(self.cfg["exercice"],2024)
    def test_04_sources_three(self):self.assertEqual(len(self.cfg["sources"]),3)
    def test_05_first_url(self):self.assertEqual(self.cfg["sources"]["ville"]["url"],m.SOURCES["ville"])
    def test_06_mamh_url(self):self.assertEqual(self.cfg["sources"]["mamh"]["url"],m.SOURCES["mamh"])
    def test_07_sha_missing(self):self.assertIsNone(self.cfg["sources"]["ville"]["sha256_fichier"])
    def test_08_not_identical(self):self.assertFalse(self.cfg["sources"]["mamh"]["versions_confrontees"])
    def test_09_not_octet_verified(self):self.assertFalse(self.cfg["sources"]["ville"]["octets_locaux_verifies"])
    def test_10_230_pages(self):self.assertEqual(self.cfg["sources"]["ville"]["pages_pdf_observees"],230)
    def test_11_eight_facts(self):self.assertEqual(len(self.by),8)
    def test_12_no_duplicates(self):self.assertEqual(set(self.by),set(m.PAGES))
    def test_13_page35(self):self.assertEqual(self.by["F02_RTC_SOMHAC"]["page_imprimee"],35)
    def test_14_index34(self):self.assertEqual(self.by["F04_RECIPROQUES_ELIMINEES"]["index_pdf"],34)
    def test_15_page197(self):self.assertEqual(self.by["F06_ELIMINATIONS_BUDGET"]["page_imprimee"],197)
    def test_16_index196(self):self.assertEqual(self.by["F07_RESOLUTION_CITEE"]["index_pdf"],196)
    def test_17_index0(self):self.assertEqual(self.by["F01_EXERCICE_2024"]["index_pdf"],0)
    def test_18_html_no_pdf(self):self.assertIsNone(self.by["F08_CATALOGUE"]["index_pdf"])
    def test_19_three_pdf_pages(self):self.assertEqual({x["index_pdf"] for x in self.by.values() if x["source"]=="ville"},{0,34,196})
    def test_20_rtc_and_somhac(self):
        self.assertTrue(all(k in self.by["F02_RTC_SOMHAC"]["observation"] for k in ("RTC","SOMHAC")))
    def test_21_line_by_line(self):self.assertIn("ligne par ligne",self.by["F03_CONSOLIDATION_LIGNE"]["observation"])
    def test_22_elimination_existing(self):self.assertIn("éliminés",self.by["F04_RECIPROQUES_ELIMINEES"]["observation"])
    def test_23_non_audited_p197(self):self.assertIn("Non audité",self.by["F05_NOTE_NON_AUDITEE"]["observation"])
    def test_24_budget_197(self):self.assertEqual(self.by["F06_ELIMINATIONS_BUDGET"]["classe"],"BUDGET_NON_AUDITE")
    def test_25_resolution_not_verified(self):self.assertIn("n'a pas été vérifié",self.by["F07_RESOLUTION_CITEE"]["observation"])
    def test_26_questions_six(self):self.assertEqual(len(self.cfg["questions"]),6)
    def test_27_questions_all_blocked(self):self.assertTrue(all(q["statut"]=="NON_RESOLUE_BLOQUANTE" for q in self.cfg["questions"]))
    def test_28_initial_no_money(self):self.assertIsNone(self.cfg["etat_initial"]["economies_certifiees_cad"])
    def test_29_no_go_initial(self):self.assertEqual(self.cfg["etat_initial"]["decision"],m.NO_GO)
    def test_30_declare_valid(self):self.assertEqual(m.declaration(view()),("F02_RTC_SOMHAC","LECTURE_DECLAREE_NON_AUTHENTIFIEE"))
    def test_31_bad_id(self):
        a=view();a["fait_id"]="FAUX"
        with self.assertRaises(ValueError):m.declaration(a)
    def test_32_bad_pdf_page(self):
        a=view();a["index_pdf"]=196
        with self.assertRaises(ValueError):m.declaration(a)
    def test_33_bad_source(self):
        a=view();a["source_id"]="mamh"
        with self.assertRaises(ValueError):m.declaration(a)
    def test_34_signed_fake(self):
        a=view();a["avis_expert_verifie"]=True
        with self.assertRaises(ValueError):m.declaration(a)
    def test_35_certified_fake(self):
        a=view();a["appreciation"]="CERTIFIE"
        with self.assertRaises(ValueError):m.declaration(a)
    def test_36_pii_extra(self):
        a=view();a["courriel"]="nom@example.invalid"
        with self.assertRaises(ValueError):m.declaration(a)
    def test_37_duplicate_refused(self):
        with self.assertRaises(ValueError):m.reconcile([view(),view()])
    def test_38_two_distinct(self):self.assertEqual(m.reconcile([view(),view("F03_CONSOLIDATION_LIGNE")])["declarations"],2)
    def test_39_contradiction_not_certified(self):
        a=view(status="CONTRADICTION_DECLAREE_NON_AUTHENTIFIEE")
        self.assertEqual(m.reconcile([a])["statuts"]["CONTRADICTION_DECLAREE_NON_AUTHENTIFIEE"],1)
    def test_40_summary_no_savings(self):self.assertIsNone(m.report(self.cfg,m.reconcile([]))["economies_certifiees_cad"])
    def test_41_summary_no_sources_auth(self):self.assertEqual(m.report(self.cfg,m.reconcile([]))["pdf_source_octets_authentifies"],0)
    def test_42_summary_pages(self):self.assertEqual(m.report(self.cfg,m.reconcile([]))["pages_pdf_examinees"],3)
    def test_43_summary_no_go(self):self.assertEqual(m.report(self.cfg,m.reconcile([]))["decision"],m.NO_GO)
    def test_44_summary_no_merge(self):self.assertFalse(m.report(self.cfg,m.reconcile([]))["fusion_autorisee"])
    def test_45_summary_not_leaking_url(self):self.assertNotIn(m.SOURCES["ville"],json.dumps(m.report(self.cfg,m.reconcile([]))))
    def test_46_cli_write(self):
        with tempfile.TemporaryDirectory() as d:
            p,q=Path(d)/"a.json",Path(d)/"b.json"
            self.assertEqual(m.main(["--bilan",str(p),"--dossier",str(q)]),0)
            self.assertEqual(len(json.loads(q.read_text("utf-8"))["constats"]),8)
    def test_47_cli_refuse_cert(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.main(["--exiger-gain-certifie","--bilan",str(Path(d)/"a.json")]),3)
    def test_48_cli_overwrite_denied(self):
        with tempfile.TemporaryDirectory() as d:
            p,q=Path(d)/"a.json",Path(d)/"b.json";q.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(p),"--dossier",str(q)]),2)
            self.assertFalse(p.exists())
    def test_49_cli_same_denied(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.json"
            self.assertEqual(m.main(["--bilan",str(p),"--dossier",str(p)]),2)
    def test_50_no_fiscal_adoption(self):self.assertTrue(self.cfg["verrous"]["aucun_taux_fiscal_adopte"])
    def test_51_no_job_cut(self):self.assertTrue(self.cfg["verrous"]["aucune_baisse_emplois_services"])
    def test_52_not_new_savings(self):self.assertTrue(self.cfg["verrous"]["elimination_reciproque_pas_second_gain"])
    def test_53_non_audit_not_extended(self):self.assertTrue(self.cfg["verrous"]["statut_non_audite_197_non_generalise"])
    def test_54_no_transaction_primary(self):self.assertEqual(m.report(self.cfg,m.reconcile([]))["pieces_transactionnelles_origines_authentifiees"],0)
    def test_55_zero_version_comparisons(self):self.assertEqual(m.report(self.cfg,m.reconcile([]))["comparaisons_entre_versions_certifiees"],0)
    def test_56_all_pages_locked(self):self.assertEqual(len(m.PAGES),8)
if __name__=="__main__":
    unittest.main()
