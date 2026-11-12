import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verifier_preparation_revue_nova_p54y as m

class TestP54Y(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()
        cls.out=m.report(cls.cfg)
    def test_schema(self):self.assertEqual(self.cfg["schema_version"],"P54Y-1")
    def test_stages(self):self.assertEqual(len(self.cfg["chaine_reference"]),8)
    def test_no_go(self):self.assertEqual(self.out["decision"],"NO_GO_AUTOMATIQUE")
    def test_no_money(self):self.assertIsNone(self.out["economies_certifiees_cad"])
    def test_no_certification(self):self.assertFalse(self.out["pret_a_certifier"])
    def test_no_merge(self):self.assertFalse(self.out["pret_a_fusionner"])
    def test_no_fake_ci(self):self.assertFalse(self.out["workflow_git_hub_actions_estime_reussi"])
    def test_human_unverified(self):self.assertFalse(self.out["revue_humaine_effectivement_realisee"])
    def test_five(self):self.assertEqual(self.out["occurrences_a_qualifier"],5)
    def test_four(self):self.assertEqual(self.out["dossiers_p54e_ouverts"],4)
    def test_ten(self):self.assertEqual(self.out["blocages_p54o_non_leves"],10)
    def test_forty(self):self.assertEqual(self.out["taches_p54n_non_attestees"],40)
    def test_p54b(self):self.assertEqual(self.out["controles_p54b_non_attestes"],96)
    def test_p54c(self):self.assertEqual(self.out["controles_p54c_non_attestes"],8)
    def test_all_safeguards(self):self.assertTrue(all(self.cfg["protections"].values()))
    def test_all_stages(self):self.assertEqual([r["jalon"] for r in self.out["jalons_documentaires"]],list(m.STAGES))
    def test_structure_complete(self):self.assertEqual(self.out["jalons_structurellement_presents"],8)
    def test_no_attestation_in_rows(self):self.assertTrue(all(not r["attestation_professionnelle_obtenue"] for r in self.out["jalons_documentaires"]))
    def test_missing_structure_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            r=m.report(self.cfg,Path(d))
            self.assertEqual(r["jalons_structurellement_presents"],0)
            self.assertFalse(r["pret_a_certifier"])
    def test_cli_report(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"bilan.json"
            self.assertEqual(m.main(["--bilan",str(path)]),0)
            self.assertEqual(json.loads(path.read_text("utf-8"))["decision"],m.NO_GO)
    def test_cli_go_fails(self):self.assertEqual(m.main(["--exiger-go"]),3)
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"bilan.json";path.write_text("PREVENT")
            self.assertEqual(m.main(["--bilan",str(path)]),2)
            self.assertEqual(path.read_text(),"PREVENT")

if __name__=="__main__":
    unittest.main()
