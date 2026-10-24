#!/usr/bin/env python3
"""P54C: 22 contrôles du résultat réellement observé, aucun avis signé."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verifier_observations_audit_nova_p54c as m

class ResultatP54C(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=json.loads(m.SOURCE.read_text("utf-8"))
        cls.valid=m.validate(cls.original)
    def changed(self,*keys,value):
        obj=copy.deepcopy(self.original)
        pos=obj
        for key in keys[:-1]:pos=pos[key]
        pos[keys[-1]]=value
        with self.assertRaises((ValueError,KeyError,TypeError)):
            m.validate(obj)
    def test_01_run(self):self.assertEqual(self.valid["source_run"],40119313052)
    def test_02_artifact(self):self.assertEqual(self.valid["artefact_id"],12570109480)
    def test_03_job(self):self.assertEqual(self.valid["source_job_id"],120947176733)
    def test_04_sha_archive(self):self.assertEqual(len(self.valid["artefact_archive_sha256"]),64)
    def test_05_pair(self):self.assertEqual(self.valid["pages"],{"ville":102,"mamh":162})
    def test_06_year(self):self.assertEqual(self.valid["date_reference"],"2026-10-24")
    def test_07_p53z_stable(self):self.assertTrue(self.valid["source_pdf_p53z_hash_stables"])
    def test_08_seven_markers(self):self.assertEqual(len(self.valid["marqueurs_documentaires"]),7)
    def test_09_two_truths_per_marker(self):self.assertTrue(all(all(v.values()) for v in self.valid["marqueurs_documentaires"].values()))
    def test_10_unknown_economy(self):self.assertIsNone(self.valid["etat"]["economies_certifiees_cad"])
    def test_11_no_signed_audit(self):self.assertEqual(self.valid["etat"]["expertises_independantes_signees_pour_nova"],0)
    def test_12_lexical_metrics(self):self.assertEqual(self.valid["comparaison_lexicale"]["score_dice"],0.7826)
    def test_13_five_unpaired(self):self.assertEqual(self.valid["etat"]["differences_numeric_lexical_non_classees"],5)
    def test_14_no_go(self):self.assertEqual(m.result(self.valid)["decision"],m.NO_GO)
    def test_15_changed_source_run(self):self.changed("source_run",value=7)
    def test_16_changed_audit_claim(self):self.changed("marqueurs_documentaires","rapport_auditeurs","mamh",value=False)
    def test_17_fake_financial_amount(self):self.changed("etat","economies_certifiees_cad",value=100)
    def test_18_fake_issuer_provenance(self):self.changed("source_pdf_p53z_hash_stables",value=False)
    def test_19_bad_numeric_counts(self):self.changed("comparaison_lexicale","communs",value=10)
    def test_20_bad_guard(self):self.changed("reserves","pas_d_anomalie_financiere_demontree",value=False)
    def test_21_cli_summary(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"bilan.json"
            self.assertEqual(m.main(["--bilan",str(p)]),0)
            self.assertEqual(json.loads(p.read_text("utf-8"))["marqueurs_communs"],7)
    def test_22_cli_strict(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"bilan.json"
            self.assertEqual(m.main(["--bilan",str(p),"--exiger-avis-independant"]),3)
    def test_23_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"bilan.json";p.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(p)]),2)
            self.assertEqual(p.read_text("utf-8"),"keep")

if __name__=="__main__":
    unittest.main()
