#!/usr/bin/env python3
"""P54D: 24 contrôles de transcription de cinq observations réelles CI."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verifier_observations_numeriques_nova_p54d as m

class ObservationsP54D(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.origin=json.loads(m.SOURCE.read_text("utf-8"))
        cls.valid=m.validate(cls.origin)
    def mutate(self,*parts,value):
        d=copy.deepcopy(self.origin)
        pos=d
        for key in parts[:-1]:pos=pos[key]
        pos[parts[-1]]=value
        with self.assertRaises((ValueError,KeyError,TypeError)):
            m.validate(d)
    def test_01_schema(self):self.assertEqual(self.valid["schema_version"],"P54D-OBSERVATIONS-CI-1")
    def test_02_run(self):self.assertEqual(self.valid["run_id"],40120462237)
    def test_03_job(self):self.assertEqual(self.valid["job_id"],120950677964)
    def test_04_artifact(self):self.assertEqual(self.valid["artifact_id"],12570359704)
    def test_05_archive_digest(self):self.assertEqual(len(self.valid["artifact_sha256"]),64)
    def test_06_exercice(self):self.assertEqual(self.valid["exercice"],2024)
    def test_07_pages(self):self.assertEqual(self.valid["pages"],{"ville":102,"mamh":162})
    def test_08_5_lines(self):self.assertEqual(len(self.valid["observations"]),5)
    def test_09_one_date(self):self.assertEqual(self.valid["classifications"]["ANNEE_DATE_PROBABLE"],1)
    def test_10_four_unknown(self):self.assertEqual(self.valid["classifications"]["INDETERMINE"],4)
    def test_11_city_one(self):self.assertEqual(self.valid["occurrences"]["ville"],1)
    def test_12_mamh_four(self):self.assertEqual(self.valid["occurrences"]["mamh"],4)
    def test_13_same_editions(self):self.assertTrue(self.valid["source_version_originale_compatible"])
    def test_14_no_original_tokens(self):
        s=json.dumps(self.valid,ensure_ascii=False)
        self.assertNotIn("token_brut",s)
        self.assertNotIn("contexte_local",s)
    def test_15_no_signed_expert(self):self.assertEqual(self.valid["etat"]["avis_independants_signes"],0)
    def test_16_no_money(self):self.assertIsNone(self.valid["etat"]["economies_certifiees_cad"])
    def test_17_no_go(self):self.assertEqual(m.result(self.valid)["decision"],m.NO_GO)
    def test_18_tamper_artifact(self):self.mutate("artifact_sha256",value="0"*64)
    def test_19_tamper_category(self):self.mutate("observations",2,"categorie_indicative",value="MONTANT_CONFIRME")
    def test_20_tamper_count(self):self.mutate("occurrences","mamh",value=3)
    def test_21_tamper_money(self):self.mutate("etat","economies_certifiees_cad",value=125)
    def test_22_tamper_guard(self):self.mutate("limites","protection_emploi_services",value=False)
    def test_23_cli_summary(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"bilan.json"
            self.assertEqual(m.main(["--bilan",str(target)]),0)
            self.assertEqual(json.loads(target.read_text("utf-8"))["occurrences_indeterminees"],4)
    def test_24_cli_strict(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"bilan.json"
            self.assertEqual(m.main(["--bilan",str(target),"--exiger-preuve-comptable"]),3)
if __name__=="__main__":
    unittest.main()
