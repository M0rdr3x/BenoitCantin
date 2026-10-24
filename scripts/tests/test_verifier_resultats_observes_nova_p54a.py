#!/usr/bin/env python3
"""P54A — vérifier la transcription de résultats CI observés."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verifier_resultats_observes_nova_p54a as m

class TestObservationsP54A(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(m.PATH.read_text("utf-8"))
        cls.valid=m.validate(cls.report)
    def tamper(self,*keys,value):
        r=copy.deepcopy(self.report)
        field=r
        for name in keys[:-1]:field=field[name]
        field[keys[-1]]=value
        with self.assertRaises((ValueError,TypeError,KeyError)):
            m.validate(r)
    def test_01_schema(self):self.assertEqual(self.valid["schema_version"],"P54A-OBSERVATIONS-CI-1")
    def test_02_p53z_run(self):self.assertEqual(self.valid["capture_source_p53z_run_id"],40113700739)
    def test_03_p54a_run(self):self.assertEqual(self.valid["rapport_validation_run_id"],40116065853)
    def test_04_artefact(self):self.assertEqual(self.valid["rapport_validation_artifact_id"],12568158622)
    def test_05_two_copies(self):self.assertEqual(len(self.valid["copies"]),2)
    def test_06_ville_sha_stable(self):self.assertTrue(self.valid["copies"]["ville"]["sha_identique_capture_p53z"])
    def test_07_mamh_sha_stable(self):self.assertTrue(self.valid["copies"]["mamh"]["sha_identique_capture_p53z"])
    def test_08_twelve(self):self.assertEqual(len(self.valid["candidates"]),12)
    def test_09_unique_ville(self):self.assertEqual(len({p["page_index_pdf_ville"] for p in self.valid["candidates"]}),12)
    def test_10_unique_mamh(self):self.assertEqual(len({p["page_index_pdf_mamh"] for p in self.valid["candidates"]}),12)
    def test_11_heuristic_not_final(self):self.assertTrue(all(x["conclusion"]=="CANDIDAT_DOCUMENTAIRE_NON_CERTIFIE" for x in self.valid["candidates"]))
    def test_12_no_audit(self):self.assertEqual(self.valid["resultats"]["rapprochements_comptables_authentifies"],0)
    def test_13_no_money(self):self.assertIsNone(self.valid["resultats"]["economies_certifiees_cad"])
    def test_14_no_go(self):self.assertEqual(m.summary(self.report)["decision"],m.NO_GO)
    def test_15_cap_not_total(self):self.assertTrue(self.valid["limites"]["maximum_12_pas_nombre_total_correspondances"])
    def test_16_bad_sha(self):self.tamper("copies","ville","sha256",value="0"*64)
    def test_17_bad_capture_date(self):self.tamper("copies","mamh","capture_utc",value="2026-10-25")
    def test_18_bad_artifact(self):self.tamper("rapport_validation_artifact_id",value=999)
    def test_19_bad_artifact_digest(self):self.tamper("rapport_validation_artifact_sha256",value="bad")
    def test_20_bad_p53z_run(self):self.tamper("capture_source_p53z_run_id",value=0)
    def test_21_bad_status_money(self):self.tamper("resultats","economies_certifiees_cad",value=123)
    def test_22_bad_claim_comptable(self):self.tamper("resultats","rapprochements_comptables_authentifies",value=1)
    def test_23_bad_page_pair(self):self.tamper("candidates",0,"page_index_pdf_mamh",value=3)
    def test_24_bad_score(self):self.tamper("candidates",2,"score_jaccard",value=0.1)
    def test_25_bad_count(self):self.tamper("candidates_affichees",value=13)
    def test_26_guard_cleared(self):self.tamper("limites","emplois_et_services_garantis",value=False)
    def test_27_cli_neutral(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"bil.json"
            self.assertEqual(m.main(["--bilan",str(f)]),0)
            self.assertEqual(json.loads(f.read_text("utf-8"))["candidats_affiches"],12)
    def test_28_cli_strict(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"bil.json"
            self.assertEqual(m.main(["--bilan",str(f),"--exiger-comparabilite-comptable"]),3)
    def test_29_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"bil.json";f.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(f)]),2)
            self.assertEqual(f.read_text("utf-8"),"keep")
    def test_30_recap_no_financial_error(self):
        s=m.summary(self.report)
        self.assertEqual(s["nombre_total_de_pages_equivalentes_certifiees"],0)
        self.assertEqual(s["expertises_independantes_certifiees"],0)

if __name__=="__main__":
    unittest.main()
