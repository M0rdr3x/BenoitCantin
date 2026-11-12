#!/usr/bin/env python3
"""P54A : données de capture P53Z, comparaison approximative, limites explicites."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import analyser_ecarts_publications_nova_p54a as m

def words(label="a",n=60):
    return {str(label)+"_4gram_"+str(j) for j in range(n)}

def fixture(source):
    d,octets,hash_,pages,missing=m.COPIES[source]
    return (b"fake-fixture-not-a-financial-document",{
      "date_capture_utc":d,
      "sha256_fichier_copie_publique":hash_,
      "taille_octets":octets,
    })

def fake_capture(source):
    return fixture(source)

class TestP54A(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.original_snapshot()
    def test_01_schema(self):self.assertEqual(self.cfg["schema_version"],"P54A-SNAPSHOT-P53Z-1")
    def test_02_run_id(self):self.assertEqual(self.cfg["run_id"],40113700739)
    def test_03_artifact(self):self.assertEqual(self.cfg["artifact_id"],12567252796)
    def test_04_2024(self):self.assertEqual(self.cfg["exercice"],2024)
    def test_05_two_captures(self):self.assertEqual(len(self.cfg["sources"]),2)
    def test_06_ville_length(self):self.assertEqual(self.cfg["sources"]["ville"]["octets"],8984919)
    def test_07_mamh_length(self):self.assertEqual(self.cfg["sources"]["mamh"]["octets"],10818312)
    def test_08_ville_pages(self):self.assertEqual(self.cfg["sources"]["ville"]["pages"],230)
    def test_09_mamh_pages(self):self.assertEqual(self.cfg["sources"]["mamh"]["pages"],177)
    def test_10_snapshot_different_hashes(self):
        self.assertNotEqual(self.cfg["sources"]["ville"]["sha256"],self.cfg["sources"]["mamh"]["sha256"])
    def test_11_snapshot_exact_no_match(self):
        self.assertEqual(self.cfg["comparaison_p53z"]["pages_textes_normalises_identiques_appariees"],0)
    def test_12_ville_27_nonextractable(self):
        self.assertEqual(self.cfg["sources"]["ville"]["pages_sans_texte_extractible"],27)
    def test_13_mamh_3_nonextractable(self):
        self.assertEqual(self.cfg["sources"]["mamh"]["pages_sans_texte_extractible"],3)
    def test_14_guard_no_financial_assumption(self):
        self.assertTrue(self.cfg["verrous"]["difference_octets_pas_erreur_comptable"])
    def test_15_guard_job_services(self):
        self.assertTrue(self.cfg["verrous"]["maintien_emplois_services"])
    def test_16_guard_no_double_count(self):
        self.assertTrue(self.cfg["verrous"]["double_compte_quebec_rtc_interdit"])
    def test_17_snapshot_no_go(self):
        self.assertEqual(self.cfg["comparaison_p53z"]["decision"],m.NO_GO)
    def test_18_snapshot_no_money(self):
        self.assertIsNone(self.cfg["comparaison_p53z"]["economies_certifiees_cad"])
    def test_19_publication_sources(self):
        self.assertEqual(self.cfg["sources"]["ville"]["url"],m.p53z.SOURCE["ville"])
    def test_20_issues_seven(self):self.assertEqual(len(m.ISSUES),7)
    def test_21_report_neutral(self):
        r=m.report(self.cfg,{},[],False)
        self.assertEqual(r["etat_reanalyse"],"REANALYSE_INCOMPLETE_SOURCES_OU_PAGES_INDISPONIBLES")
    def test_22_report_real_prior_capture(self):
        r=m.report(self.cfg,{},[],False)
        self.assertEqual(r["capture_p53z_sources"],2)
    def test_23_neutral_no_fuzzy_score(self):
        self.assertIsNone(m.report(self.cfg,{},[],False)["pages_approximativement_appariees_heuristique"])
    def test_24_approval_never_auto(self):
        r=m.report(self.cfg,{},[],False)
        self.assertFalse(r["fusion_autorisee"])
    def test_25_empty_fuzzy(self):self.assertEqual(m.probable_pages([],[]),[])
    def test_26_exact_fuzzy(self):
        r=m.probable_pages([words()],[words()])
        self.assertEqual(len(r),1)
        self.assertEqual(r[0]["score_jaccard"],1)
    def test_27_reorder_fuzzy(self):
        r=m.probable_pages([words("A"),words("B")],[words("B"),words("A")])
        self.assertEqual([(x["page_pdf_ville"],x["page_pdf_mamh"]) for x in r],[(0,1),(1,0)])
    def test_28_blank_undetermined(self):
        self.assertEqual(m.probable_pages([set()],[words()]),[])
    def test_29_different_text_not_fraud(self):
        self.assertEqual(m.probable_pages([words("X")],[words("Y")]),[])
    def test_30_limited_shared_shingles(self):
        a=words("x",50)
        b=words("y",50) | set(list(a)[:10])
        self.assertEqual(m.probable_pages([a],[b]),[])
    def test_31_heuristic_not_certified(self):
        r=m.probable_pages([words()],[words()])
        self.assertEqual(r[0]["statut"],"CORRESPONDANCE_HEURISTIQUE_NON_CERTIFIEE")
    def test_32_limit_max_matches(self):
        a=[words(str(i)) for i in range(5)]
        self.assertEqual(len(m.probable_pages(a,a,max_results=2)),2)
    def test_33_malformed_threshold(self):
        with self.assertRaises(ValueError):m.probable_pages([],[],threshold=0.1)
    def test_34_no_double_match_to_one_page(self):
        r=m.probable_pages([words(),words()],[words()])
        self.assertEqual(len(r),1)
    def test_35_live_capture_with_mocked_extraction(self):
        with patch.object(m,"fingerprints",side_effect=[[words("v")],[words("v")]]):
            obs,pairs,ok=m.run_analysis(fake_capture)
        self.assertTrue(ok)
        self.assertEqual(len(pairs),1)
        self.assertEqual(len(obs),2)
    def test_36_mocked_reread_no_false_certification(self):
        with patch.object(m,"fingerprints",side_effect=[[words("a")],[words("a")]]):
            obs,pairs,ok=m.run_analysis(fake_capture)
        result=m.report(self.cfg,obs,pairs,ok)
        self.assertIsNone(result["economies_certifiees_cad"])
        self.assertEqual(result["anomalies_comptables_certifiees"],0)
    def test_37_one_missing_source(self):
        def fail(source):
            if source=="mamh":raise ValueError("unavailable")
            return fixture(source)
        obs,pairs,ok=m.run_analysis(fail)
        self.assertFalse(ok)
        self.assertEqual(len(pairs),0)
        self.assertFalse(obs["mamh"]["capture_effective"])
    def test_38_report_records_fresh_capture(self):
        with patch.object(m,"fingerprints",side_effect=[[words("a")],[words("a")]]):
            obs,pairs,ok=m.run_analysis(fake_capture)
        result=m.report(self.cfg,obs,pairs,ok)
        self.assertEqual(result["captures_actualisees"],2)
        self.assertTrue(result["observations"]["ville"]["concordance_empreinte_P53Z"])
    def test_39_report_records_changed_capture(self):
        def changed(source):
            data,meta=fixture(source)
            if source=="ville":meta["sha256_fichier_copie_publique"]="f"*64
            return data,meta
        with patch.object(m,"fingerprints",side_effect=[[words("a")],[words("a")]]):
            obs,pairs,ok=m.run_analysis(changed)
        self.assertFalse(obs["ville"]["concordance_empreinte_P53Z"])
    def test_40_no_network_without_flag(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"r.json"
            self.assertEqual(m.main(["--bilan",str(path)]),0)
            report=json.loads(path.read_text("utf-8"))
            self.assertEqual(report["captures_actualisees"],0)
            self.assertEqual(report["capture_p53z_sources"],2)
    def test_41_cli_strict_refusal(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"r.json"
            self.assertEqual(m.main(["--bilan",str(target),"--exiger-anomalie-certifiee"]),3)
    def test_42_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"r.json";p.write_text("kept","utf-8")
            self.assertEqual(m.main(["--bilan",str(p)]),2)
            self.assertEqual(p.read_text("utf-8"),"kept")
    def test_43_fake_financial_alert_disallowed(self):
        self.assertEqual(m.report(self.cfg,{},[],False)["anomalies_comptables_certifiees"],0)
    def test_44_snapshot_linked_run(self):
        self.assertEqual(m.report(self.cfg,{},[],False)["run_original_p53z"],m.RUN)
    def test_45_unsigned_original(self):
        self.assertEqual(self.cfg["comparaison_p53z"]["avis_professionnels_signes"],0)
    def test_46_empty_candidates_not_proven_equivalence(self):
        self.assertFalse(m.report(self.cfg,{},[],False)["fusion_autorisee"])
    def test_47_public_snapshot_no_original_files(self):
        self.assertTrue(self.cfg["verrous"]["original_pdf_non_archive_dans_git"])
    def test_48_legal_issuer_not_attested(self):
        self.assertEqual(m.report(self.cfg,{},[],False)["conclusions_sur_version_officielle_authentifiees"],0)

if __name__=="__main__":
    unittest.main()
