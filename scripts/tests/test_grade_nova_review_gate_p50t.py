"""P50T: tests fictifs sur les portes de revue, sans permissions GitHub."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE=Path(__file__).resolve().parents[1]/"grade_nova_review_gate_p50t.py"
spec=importlib.util.spec_from_file_location("p50t", SOURCE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {
        "structure":"RELEVE_EFFECTUE",
        "decision":"NO_GO_AUTOMATIQUE",
        "autorisation_publication":False,
        "signature_juridique_attestee":False,
        "revues":{str(n):{"approbations_git_head":0,
                          "habilitation_humaine_attestee":False}
                  for n in m.ALL},
        "ci":dict(m.REQUIRED_TECH),
        "obstacles":["PR640_NE_PAS_FUSIONNER"],
    }

class Gates(unittest.TestCase):
    def test_priorities_are_distinct(self):
        self.assertEqual(m.PRIORITY,(657,638))
        self.assertEqual(len(m.ALL),5)
    def test_priorities_both_blocked(self):
        r=m.inspect(fixture())
        self.assertIn("PR657_APPROBATION_ABSENTE",r["obstacles_revues"])
        self.assertIn("PR638_APPROBATION_ABSENTE",r["obstacles_revues"])
    def test_other_three_not_yet_blockers(self):
        r=m.inspect(fixture())
        self.assertNotIn("PR636_APPROBATION_ABSENTE",r["obstacles_revues"])
    def test_full_stage_all_five_blocked(self):
        r=m.inspect(fixture(),"complete")
        self.assertEqual(sum(x.endswith("APPROBATION_ABSENTE") for x in r["obstacles_revues"]),5)
    def test_all_approved_still_no_go(self):
        x=fixture()
        for n in m.ALL:x["revues"][str(n)]["approbations_git_head"]=1
        r=m.inspect(x,"complete")
        self.assertEqual(r["etat_porte_revues"],"REVUES_GITHUB_OBSERVEES_SEULEMENT")
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
        self.assertFalse(r["autorisation_fusion"])
    def test_one_review_insufficient(self):
        x=fixture(); x["revues"]["657"]["approbations_git_head"]=1
        self.assertIn("PR638_APPROBATION_ABSENTE",m.inspect(x)["obstacles_revues"])
    def test_string_approval_refused(self):
        x=fixture();x["revues"]["638"]["approbations_git_head"]="1"
        self.assertIn("PR638_PREUVE_DE_REVUE_INVALIDE",m.inspect(x)["obstacles_revues"])
    def test_bool_approval_refused(self):
        x=fixture();x["revues"]["657"]["approbations_git_head"]=True
        self.assertIn("PR657_PREUVE_DE_REVUE_INVALIDE",m.inspect(x)["obstacles_revues"])
    def test_claim_of_habilitation_refused(self):
        x=fixture();x["revues"]["657"]["habilitation_humaine_attestee"]=True
        self.assertIn("PR657_PREUVE_DE_REVUE_INVALIDE",m.inspect(x)["obstacles_revues"])
    def test_failed_ci_blocks(self):
        x=fixture();x["ci"]["P50R"]="A_REVERIFIER"
        self.assertIn("PREUVE_TECHNIQUE_P50R_INSUFFISANTE",m.inspect(x)["obstacles_revues"])
    def test_missing_report_blocks(self):
        r=m.inspect(None)
        self.assertIn("RAPPORT_P50S_ABSENT_OU_INVALIDE",r["obstacles_revues"])
    def test_false_go_blocks(self):
        x=fixture();x["decision"]="GO"
        self.assertIn("NO_GO_P50S_ABSENT",m.inspect(x)["obstacles_revues"])
    def test_false_legal_signoff_blocks(self):
        x=fixture();x["signature_juridique_attestee"]=True
        self.assertIn("PRETENTION_SIGNATURE_JURIDIQUE",m.inspect(x)["obstacles_revues"])
    def test_pr640_changed_blocks(self):
        x=fixture();x["obstacles"].append("PR640_VERROU_A_REVERIFIER")
        self.assertIn("DERIVE_P50S:PR640_VERROU_A_REVERIFIER",m.inspect(x)["obstacles_revues"])
    def test_unknown_phase_refused(self):
        with self.assertRaises(ValueError):m.inspect(fixture(),"publier")
    def test_cli_exit_three_without_reviews(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"input.json";o=Path(d)/"out.json"
            f.write_text(json.dumps(fixture()),encoding="utf-8")
            rc=m.main(["--rapport-p50s",str(f),"--resultat",str(o),"--exiger-revues"])
            self.assertEqual(rc,3)
            self.assertEqual(json.loads(o.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_cli_report_valid_without_gate(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"input.json";o=Path(d)/"out.json"
            f.write_text(json.dumps(fixture()),encoding="utf-8")
            self.assertEqual(m.main(["--rapport-p50s",str(f),"--resultat",str(o)]),0)
    def test_cli_missing_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.main(["--rapport-p50s",str(Path(d)/"missing")]),2)
    def test_no_go_even_if_all_approved(self):
        x=fixture()
        for n in m.ALL:x["revues"][str(n)]["approbations_git_head"]=2
        self.assertFalse(m.inspect(x,"complete")["autorisation_publication"])
    def test_report_no_personal_data(self):
        self.assertNotIn("@",json.dumps(m.inspect(fixture())))

if __name__=="__main__":
    unittest.main()
