"""P50W — tests fictifs du précontrôle GitHub en lecture seule."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SRC=Path(__file__).resolve().parents[1]/"preflight_nova_ruleset_p50w.py"
spec=importlib.util.spec_from_file_location("p50w",SRC)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def candidate():
    return {
        "target":"branch","enforcement":"disabled","bypass_actors":[],
        "conditions":{"ref_name":{"include":["refs/heads/main"],"exclude":[]}},
        "rules":[
            {"type":"deletion"},{"type":"non_fast_forward"},
            {"type":"pull_request","parameters":{
                "required_approving_review_count":1,
                "dismiss_stale_reviews_on_push":True,
                "require_last_push_approval":True}},
            {"type":"required_status_checks","parameters":{
                "strict_required_status_checks_policy":True,
                "required_status_checks":[{"context":x,"integration_id":m.APP_ID} for x in m.CHECKS]}}
        ]
    }

def snapshot():
    checks={}
    pulls={}
    for n,sha in {**m.SAMPLES,**m.PRIORITY}.items():
        pulls[str(n)]={"head":sha,"state":"open","draft":True,"merged":False}
    for n in m.PRIORITY:
        pulls[str(n)].update({"submitted_review_count":0,"review_requests":0})
    for n,sha in m.SAMPLES.items():
        checks[str(n)]=[{"name":name,"head_sha":sha,"app_id":m.APP_ID,
                         "status":"completed","conclusion":"success"} for name in m.CHECKS]
    return {"main_branch":{"commit":{"sha":m.EXPECTED_MAIN},"protected":False},
            "rulesets":[],"prs":pulls,"check_runs":checks}

class PreflightP50W(unittest.TestCase):
    def test_candidate_requires_disabled(self):
        c=candidate();c["enforcement"]="active"
        self.assertIn("CANDIDAT_DEVRAIT_RESTER_DESACTIVE",m.ruleset_checks(c))
    def test_target_branch_exact(self):
        c=candidate();c["conditions"]["ref_name"]["include"].append("refs/heads/extra")
        self.assertIn("CIBLE_MAIN_NOM_NON_UNIQUE",m.ruleset_checks(c))
    def test_no_bypass_in_candidate(self):
        c=candidate();c["bypass_actors"]=[{"actor_id":123}]
        self.assertIn("BYPASS_CANDIDAT_PRESENT",m.ruleset_checks(c))
    def test_three_check_names_exact(self):
        c=candidate();c["rules"][3]["parameters"]["required_status_checks"][0]["context"]="invented"
        self.assertIn("CONTEXTES_CANDIDATS_NON_CONFORMES",m.ruleset_checks(c))
    def test_check_app_must_be_official(self):
        c=candidate();c["rules"][3]["parameters"]["required_status_checks"][0]["integration_id"]=10
        self.assertIn("CONTEXTES_CANDIDATS_NON_CONFORMES",m.ruleset_checks(c))
    def test_review_last_push_required(self):
        c=candidate();c["rules"][2]["parameters"]["require_last_push_approval"]=False
        self.assertIn("REVUES_EXIGEES_NON_CONFORMES",m.ruleset_checks(c))
    def test_valid_candidate(self):
        self.assertEqual(m.ruleset_checks(candidate()),[])
    def test_nine_sample_checks_pass(self):
        p=m.analyze(snapshot(),candidate())
        self.assertEqual(p["checks_reussis_sur_sha"],9)
        self.assertEqual(p["checks_attendus"],9)
        self.assertEqual(p["compatibilite_technique_echantillon"],"CONFIRMEE")
        self.assertFalse(p["autorisation_fusion"])
    def test_unprotected_main_remains_blocker(self):
        p=m.analyze(snapshot(),candidate())
        self.assertIn("MAIN_NON_PROTEGEE",p["obstacles"])
        self.assertIn("AUCUN_RULESET_ACTIF",p["obstacles"])
    def test_missing_human_review_remains_blocker(self):
        p=m.analyze(snapshot(),candidate())
        self.assertIn("PR657_AUCUNE_REVUE_DEMANDEE",p["obstacles"])
        self.assertIn("PR638_REVUE_FORMELLE_ABSENTE",p["obstacles"])
    def test_wrong_check_app_is_rejected(self):
        p=snapshot();p["check_runs"]["636"][0]["app_id"]=99
        x=m.analyze(p,candidate())
        self.assertEqual(x["checks_reussis_sur_sha"],8)
        self.assertEqual(x["compatibilite_technique_echantillon"],"INCONCLUSIVE")
    def test_skipped_check_is_rejected(self):
        p=snapshot();p["check_runs"]["638"][0]["conclusion"]="skipped"
        self.assertEqual(m.analyze(p,candidate())["checks_reussis_sur_sha"],8)
    def test_wrong_commit_is_rejected(self):
        p=snapshot();p["prs"]["664"]["head"]="f"*40
        x=m.analyze(p,candidate())
        self.assertIn("PR664_SHA_OU_ETAT_CHANGE",x["obstacles"])
        self.assertEqual(x["compatibilite_technique_echantillon"],"INCONCLUSIVE")
    def test_wrong_check_sha_is_rejected(self):
        p=snapshot();p["check_runs"]["664"][0]["head_sha"]="f"*40
        self.assertEqual(m.analyze(p,candidate())["checks_reussis_sur_sha"],8)
    def test_duplicate_check_is_ambiguous(self):
        p=snapshot();p["check_runs"]["664"].append(copy.deepcopy(p["check_runs"]["664"][0]))
        x=m.analyze(p,candidate())
        self.assertIn("PR664_CHECK_MANQUANT_OU_AMBIGU:no-committed-secrets",x["obstacles"])
    def test_review_requests_do_not_grant_go(self):
        p=snapshot()
        p["prs"]["657"]["review_requests"]=1
        p["prs"]["638"]["review_requests"]=1
        x=m.analyze(p,candidate())
        self.assertEqual(x["requetes_revues_prioritaires"],2)
        self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")
    def test_missing_snapshot_is_blocking(self):
        x=m.analyze(None,candidate())
        self.assertIn("RELEVE_INCONNU",x["obstacles"])
        self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")
    def test_no_private_data_leaked(self):
        x=m.analyze(snapshot(),candidate())
        self.assertNotIn("@",json.dumps(x))
        self.assertFalse(x["ruleset_installe_par_ce_controle"])
    def test_api_outside_repo_rejected(self):
        with self.assertRaises(ValueError):
            m.api("/repos/other/project/check-runs","token")
    def test_cli_unknown_snapshot_returns2(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            cfg=p/"candidate.json";cfg.write_text(json.dumps(candidate()),encoding="utf-8")
            out=p/"output.json"
            code=m.main(["--snapshot",str(p/"absent.json"),"--candidate",str(cfg),
                         "--report",str(out)])
            self.assertEqual(code,2)
            self.assertEqual(json.loads(out.read_text())["decision"],"NO_GO_AUTOMATIQUE")

if __name__=="__main__":
    unittest.main()
