"""P50X : tests unitaires hors réseau des protections serveur effectives."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

FILE=Path(__file__).resolve().parents[1]/"audit_nova_effective_rules_p50x.py"
spec=importlib.util.spec_from_file_location("nova_p50x",FILE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def candidate():
    return {"name":"SINJIRA et Projet Nova - protection main (candidat P50V)",
            "enforcement":"disabled"}

def sample(active=False,bypass=None,bypass_visible=True):
    types=["deletion","non_fast_forward","pull_request","required_status_checks"]
    detail={
        "id":77,"name":candidate()["name"],"target":"branch","enforcement":"active",
        "conditions":{"ref_name":{"include":["refs/heads/main"],"exclude":[]}},
        "rules":[
            {"type":"deletion"},{"type":"non_fast_forward"},
            {"type":"pull_request","parameters":{
                "required_approving_review_count":1,
                "require_last_push_approval":True,
                "dismiss_stale_reviews_on_push":True,
                "required_review_thread_resolution":True,
            }},
            {"type":"required_status_checks","parameters":{
                "strict_required_status_checks_policy":True,
                "required_status_checks":[
                    {"context":a,"integration_id":b} for a,b in sorted(m.REQUIRED_CHECKS)]
            }},
        ],
    }
    if bypass_visible:
        detail["bypass_actors"]=[] if bypass is None else bypass
    return {
        "branch":{"commit":{"sha":m.MAIN_SHA},"protected":active},
        "rulesets":[{"id":77,"enforcement":"active"}] if active else [],
        "details":[detail] if active else [],
        "effective":[{"type":t} for t in types] if active else [],
        "effective_access":"CONSULTABLE",
    }

class EffectiveRulesTests(unittest.TestCase):
    def test_no_ruleset_blocks(self):
        r=m.evaluate(sample(),candidate())
        self.assertIn("AUCUN_RULESET_ACTIF",r["obstacles"])
        self.assertIn("MAIN_NON_PROTEGEE_OU_INCONNUE",r["obstacles"])
    def test_empty_effective_rules_block(self):
        r=m.evaluate(sample(),candidate())
        self.assertIn("REGLES_EFFECTIVES_MAIN_INCOMPLETES",r["obstacles"])
    def test_matching_active_config_is_not_a_go(self):
        r=m.evaluate(sample(active=True),candidate())
        self.assertTrue(r["ruleset_candidat_actif_et_parametres_compatibles"])
        self.assertEqual(r["exceptions_bypass"],"AUCUN_BYPASS_DECLARÉ_DANS_LA_REPONSE")
        self.assertFalse(r["activation_effective_certifiee"])
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
    def test_hidden_bypass_fails_closed(self):
        r=m.evaluate(sample(active=True,bypass_visible=False),candidate())
        self.assertIn("EXCEPTIONS_DE_CONTOURNEMENT_NON_AUDITABLES",r["obstacles"])
        self.assertEqual(r["exceptions_bypass"],"NON_DIVULGUE_PAR_API")
    def test_present_bypass_blocks(self):
        s=sample(active=True,bypass=[{"actor_id":99,"actor_type":"User"}])
        self.assertIn("EXCEPTIONS_DE_CONTOURNEMENT_A_REVOIR",m.evaluate(s,candidate())["obstacles"])
    def test_missing_approval_rule_detected(self):
        s=sample(active=True)
        s["details"][0]["rules"][2]["parameters"]["required_approving_review_count"]=0
        self.assertIn("REVUES_OBLIGATOIRES_NON_CONFIRMEES",m.evaluate(s,candidate())["obstacles"])
    def test_stale_approval_policy_required(self):
        s=sample(active=True)
        s["details"][0]["rules"][2]["parameters"]["dismiss_stale_reviews_on_push"]=False
        self.assertIn("REVUES_OBLIGATOIRES_NON_CONFIRMEES",m.evaluate(s,candidate())["obstacles"])
    def test_wrong_check_app_detected(self):
        s=sample(active=True)
        s["details"][0]["rules"][3]["parameters"]["required_status_checks"][0]["integration_id"]=7
        self.assertIn("CHECKS_REQUIS_OU_APPLICATION_INCORRECTS",m.evaluate(s,candidate())["obstacles"])
    def test_missing_effective_source_detected(self):
        s=sample(active=True)
        s["effective"]=None;s["effective_access"]="NON_ACCESSIBLE_A_CETTE_INTEGRATION"
        self.assertIn("REGLES_EFFECTIVES_MAIN_NON_ATTESTEES",m.evaluate(s,candidate())["obstacles"])
    def test_effective_rules_missing_review_detected(self):
        s=sample(active=True)
        s["effective"]=[x for x in s["effective"] if x["type"]!="pull_request"]
        self.assertIn("REGLES_EFFECTIVES_MAIN_INCOMPLETES",m.evaluate(s,candidate())["obstacles"])
    def test_changed_main_sha_detected(self):
        s=sample(active=True);s["branch"]["commit"]["sha"]="f"*40
        self.assertIn("MAIN_A_CHANGE_RELANCER_VALIDATIONS",m.evaluate(s,candidate())["obstacles"])
    def test_not_active_ruleset_even_if_protected_detected(self):
        s=sample(active=False);s["branch"]["protected"]=True
        self.assertIn("AUCUN_RULESET_ACTIF",m.evaluate(s,candidate())["obstacles"])
    def test_candidate_cannot_claim_active_in_repo(self):
        c=candidate();c["enforcement"]="active"
        self.assertIn("CANDIDAT_DOIT_RESTER_DESACTIVE",m.evaluate(sample(),c)["obstacles"])
    def test_scope_drift_detected(self):
        s=sample(active=True)
        s["details"][0]["conditions"]["ref_name"]["include"].append("refs/heads/experiment")
        self.assertIn("CONDITIONS_MAIN_DIFFERENTES",m.evaluate(s,candidate())["obstacles"])
    def test_unknown_snapshot_no_go(self):
        r=m.evaluate(None,candidate())
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
        self.assertFalse(r["publication_autorisee"])
    def test_unknown_candidate_no_go(self):
        self.assertIn("CANDIDAT_P50V_NON_LISIBLE",m.evaluate(sample(),None)["obstacles"])
    def test_cli_blocking_exit_3(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cfg=root/"p50v.json";state=root/"github.json";out=root/"result.json"
            cfg.write_text(json.dumps(candidate()),encoding="utf-8")
            state.write_text(json.dumps(sample()),encoding="utf-8")
            rc=m.main(["--candidate",str(cfg),"--snapshot",str(state),
                       "--result",str(out),"--exiger-protection"])
            self.assertEqual(rc,3)
            self.assertEqual(json.loads(out.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_cli_reporting_exit_0(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cfg=root/"p50v.json";state=root/"github.json"
            cfg.write_text(json.dumps(candidate()),encoding="utf-8")
            state.write_text(json.dumps(sample()),encoding="utf-8")
            self.assertEqual(m.main(["--candidate",str(cfg),"--snapshot",str(state)]),0)
    def test_reject_external_repository(self):
        with self.assertRaises(ValueError):
            m.get("/repos/unrelated/website/rulesets","")
    def test_no_sensitive_identifiers_in_result(self):
        r=m.evaluate(sample(active=True,bypass=[{"actor_id":123456}]),candidate())
        self.assertNotIn("123456",json.dumps(r))
        self.assertNotIn("@",json.dumps(r))

if __name__=="__main__":
    unittest.main()
