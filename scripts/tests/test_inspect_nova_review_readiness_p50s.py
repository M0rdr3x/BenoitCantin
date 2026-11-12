"""P50S: simulations locales des portes de revue; aucune permission GitHub requise."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE=Path(__file__).resolve().parents[1]/"inspect_nova_review_readiness_p50s.py"
sp=importlib.util.spec_from_file_location("nova_p50s",MODULE)
mod=importlib.util.module_from_spec(sp)
sp.loader.exec_module(mod)

def fixture():
    prs={}
    for n,(base,sha) in mod.PRS.items():
        prs[str(n)]={"state":"open","draft":True,"merged":False,
                     "head":sha,"base":base,"author":"auteur",
                     "reviews":[],"requests":0}
    prs["640"]={"state":"open","draft":True,"merged":False,
                "head":mod.EXCLUDED,"base":"main","reviews":[],"requests":0}
    runs={key:{"sha":sha,"name":name,"success":True}
          for key,(sha,name) in mod.RUNS.items()}
    return {"main":mod.MAIN,"prs":prs,"runs":runs}

class PorteP50S(unittest.TestCase):
    def test_five_review_targets(self):
        self.assertEqual(len(mod.PRS),5)
    def test_evidence_ci_stays_distinct(self):
        r=mod.analyze(fixture())
        self.assertEqual(r["ci"]["P50Q"],"REUSSITE_CI_VERIFIEE_AU_SHA")
        self.assertEqual(r["ci"]["P50R"],"REUSSITE_CI_VERIFIEE_AU_SHA")
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
    def test_missing_five_reviews(self):
        r=mod.analyze(fixture())
        self.assertEqual(r["nombre_pr_sans_approbation_github"],5)
        self.assertIn("PR636_REVUE_FORMELLE_ABSENTE",r["obstacles"])
        self.assertIn("PR638_AUCUNE_DEMANDE_REVISEUR",r["obstacles"])
    def test_review_requested_not_approved(self):
        x=fixture()
        x["prs"]["636"]["requests"]=1
        r=mod.analyze(x)
        self.assertIn("PR636_REVUE_FORMELLE_ABSENTE",r["obstacles"])
        self.assertNotIn("PR636_AUCUNE_DEMANDE_REVISEUR",r["obstacles"])
    def test_fresh_approval_counted_as_github_only(self):
        x=fixture()
        x["prs"]["636"]["reviews"]=[{"user":"code_reviewer","type":"User","state":"APPROVED",
                                     "commit":mod.PRS[636][1],"date":"2026-10-16T10:00:00Z"}]
        r=mod.analyze(x)
        self.assertEqual(r["revues"]["636"]["approbations_git_head"],1)
        self.assertFalse(r["revues"]["636"]["habilitation_humaine_attestee"])
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
    def test_stale_review_does_not_count(self):
        x=fixture()
        x["prs"]["636"]["reviews"]=[{"user":"reviewer","type":"User","state":"APPROVED",
                                     "commit":"a"*40,"date":"2026-10-16T10:00:00Z"}]
        self.assertEqual(mod.approvals(x["prs"]["636"]),0)
    def test_bot_and_self_reviews_not_counted(self):
        x=fixture()
        x["prs"]["636"]["reviews"]=[
            {"user":"auteur","type":"User","state":"APPROVED","commit":mod.PRS[636][1]},
            {"user":"bot","type":"Bot","state":"APPROVED","commit":mod.PRS[636][1]},
        ]
        self.assertEqual(mod.approvals(x["prs"]["636"]),0)
    def test_newer_changes_requested_overrides_approved(self):
        x=fixture()
        x["prs"]["636"]["reviews"]=[
            {"user":"relecteur","type":"User","state":"APPROVED",
             "commit":mod.PRS[636][1],"date":"2026-10-15T12:00:00Z"},
            {"user":"relecteur","type":"User","state":"CHANGES_REQUESTED",
             "commit":mod.PRS[636][1],"date":"2026-10-16T12:00:00Z"},
        ]
        self.assertEqual(mod.approvals(x["prs"]["636"]),0)
    def test_main_drift_is_blocker(self):
        x=fixture();x["main"]="b"*40
        self.assertIn("MAIN_MODIFIE_REPRISE_OBLIGATOIRE",mod.analyze(x)["obstacles"])
    def test_head_drift_is_blocker(self):
        x=fixture();x["prs"]["657"]["head"]="b"*40
        self.assertIn("PR657_SHA_OU_BASE_CHANGE",mod.analyze(x)["obstacles"])
    def test_base_drift_is_blocker(self):
        x=fixture();x["prs"]["655"]["base"]="main"
        self.assertIn("PR655_SHA_OU_BASE_CHANGE",mod.analyze(x)["obstacles"])
    def test_pr640_merged_is_blocker(self):
        x=fixture();x["prs"]["640"]["merged"]=True
        self.assertIn("PR640_VERROU_A_REVERIFIER",mod.analyze(x)["obstacles"])
    def test_missing_pr_fails_closed(self):
        x=fixture();del x["prs"]["638"]
        self.assertIn("PR638_INACCESSIBLE",mod.analyze(x)["obstacles"])
    def test_missing_workflow_evidence(self):
        x=fixture();x["runs"]["P50R"]["success"]=False
        self.assertIn("PREUVE_CI_INSUFFISANTE_P50R",mod.analyze(x)["obstacles"])
    def test_absent_snapshot_no_go(self):
        r=mod.analyze(None)
        self.assertEqual(r["structure"],"INCONNUE")
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
    def test_missing_snapshot_file_is_nonzero(self):
        with tempfile.TemporaryDirectory() as d:
            report=Path(d)/"r.json"
            result=mod.main(["--snapshot",str(Path(d)/"missing.json"),
                             "--rapport",str(report)])
            self.assertEqual(result,2)
            self.assertIn("NO_GO_AUTOMATIQUE",report.read_text("utf-8"))
    def test_api_rejects_other_repository(self):
        with self.assertRaises(ValueError):
            mod.get("/repos/autre/autre/pulls/1","mock-token")

if __name__=="__main__":
    unittest.main()
