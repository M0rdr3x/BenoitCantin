#!/usr/bin/env python3
"""P54B : vérifier les comptes de jetons observés, sans authentifier l'audit."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verifier_observations_numeriques_nova_p54b as m

class TestMesuresP54B(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(m.SOURCE.read_text("utf-8"))
        cls.valid=m.check(cls.data)
    def corrupt(self,*keys,value):
        obj=copy.deepcopy(self.data);node=obj
        for k in keys[:-1]:node=node[k]
        node[keys[-1]]=value
        with self.assertRaises((ValueError,KeyError,TypeError)):
            m.check(obj)
    def test_01_valid(self):self.assertEqual(self.valid["schema_version"],"P54B-OBSERVE-1")
    def test_02_12_pairs(self):self.assertEqual(len(self.valid["lignes"]),12)
    def test_03_11_high(self):self.assertEqual(self.valid["resume"]["paires_dice_au_moins_0_97"],11)
    def test_04_weak_pair(self):self.assertEqual(self.valid["resume"]["paire_moins_similaire"],"102:162")
    def test_05_source_run(self):self.assertEqual(self.valid["workflow_run_id"],40118178035)
    def test_06_artifact(self):self.assertEqual(self.valid["artifact_id"],12569352928)
    def test_07_source_year(self):self.assertEqual(self.valid["exercice_financier"],2024)
    def test_08_two_sources(self):self.assertEqual(len(self.valid["documents_heureux"]),2)
    def test_09_all_no_money(self):self.assertIsNone(self.valid["resume"]["economies_certifiees_cad"])
    def test_10_all_no_go(self):self.assertEqual(self.valid["resume"]["decision"],m.NO_GO)
    def test_11_96_controls(self):self.assertEqual(self.valid["resume"]["controles_qualificatifs_restants"],96)
    def test_12_restrict_issuers(self):self.assertTrue(self.valid["limites"]["source_edition_perimetre_audit_non_certifies"])
    def test_13_no_raw_numbers_in_report(self):
        text=json.dumps(m.report(self.data))
        self.assertNotIn("occurrences_communes",text)
        self.assertNotIn("score_dice",text)
    def test_14_bad_sha(self):self.corrupt("documents_heureux",0,"sha256_copie",value="f"*64)
    def test_15_bad_artifact_hash(self):self.corrupt("artifact_archive_sha256",value="bad")
    def test_16_bad_run(self):self.corrupt("workflow_run_id",value=0)
    def test_17_bad_score(self):self.corrupt("lignes",0,"score_dice",value=0.1)
    def test_18_bad_common(self):self.corrupt("lignes",0,"occurrences_communes",value=999999)
    def test_19_bad_unpaired(self):self.corrupt("lignes",0,"non_appariees_ville",value=999)
    def test_20_bad_pair(self):self.corrupt("lignes",0,"index_pdf_mamh",value=0)
    def test_21_bad_certified(self):self.corrupt("resume","preuves_comptables_certifiees",value=1)
    def test_22_bad_money(self):self.corrupt("resume","economies_certifiees_cad",value=5)
    def test_23_bad_guard(self):self.corrupt("limites","protection_emplois_services",value=False)
    def test_24_cli_initial(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"out.json"
            self.assertEqual(m.main(["--bilan",str(p)]),0)
            self.assertEqual(json.loads(p.read_text("utf-8"))["paires_recouvrement_au_moins_97_pourcent"],11)
    def test_25_cli_strict(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"out.json"
            self.assertEqual(m.main(["--bilan",str(p),"--exiger-certification"]),3)
    def test_26_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"out.json";p.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(p)]),2)
            self.assertEqual(p.read_text("utf-8"),"keep")

if __name__=="__main__":
    unittest.main()
