"""P50U — tests fictifs de la protection de main, sans API ni identité."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MOD=Path(__file__).resolve().parents[1]/"audit_nova_protection_main_p50u.py"
spec=importlib.util.spec_from_file_location("nova_p50u",MOD)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def unprotected():
    return {"name":"main","commit":{"sha":m.EXPECTED_MAIN},"protected":False,
            "protection":{"enabled":False,"required_status_checks":{
                "enforcement_level":"off","contexts":[],"checks":[]}}}

def protected():
    return {"name":"main","commit":{"sha":m.EXPECTED_MAIN},"protected":True,
            "protection":{"enabled":True,"required_status_checks":{
                "enforcement_level":"non_admins","contexts":[],
                "checks":[{"context":"nova-tests","app_id":15368}]}}}

class P50UGates(unittest.TestCase):
    def test_main_observed_unprotected_is_blocking(self):
        r=m.evaluate(unprotected(),[],"* @owner\n")
        self.assertEqual(r["etat_porte_technique"],"BLOQUANT")
        self.assertIn("MAIN_NON_PROTEGEE_OU_ETAT_INCONNU",r["obstacles"])
    def test_no_required_checks_is_blocking(self):
        r=m.evaluate(unprotected(),[],"* @owner\n")
        self.assertIn("AUCUN_CHECK_OBLIGATOIRE",r["obstacles"])
    def test_no_ruleset_is_explicitly_blocking(self):
        r=m.evaluate(unprotected(),[],"* @owner\n")
        self.assertIn("AUCUNE_PROTECTION_PREVENTIVE_OBSERVEE",r["obstacles"])
    def test_single_codeowner_insufficient_for_independent_review(self):
        r=m.evaluate(unprotected(),[],"# comment\n* @owner\n")
        self.assertEqual(r["codeowners_comptes"],1)
        self.assertIn("CODEOWNERS_NE_GARANTIT_PAS_REVUE_INDEPENDANTE",r["obstacles"])
    def test_no_owner_yields_blocker(self):
        self.assertEqual(m.owners_from_codeowners("docs/ @someone\n"),0)
    def test_two_codeowners_counted_but_no_human_claim(self):
        r=m.evaluate(protected(),[{"enforcement":"active"}],
                     "* @reviewerOne @reviewerTwo\n")
        self.assertEqual(r["etat_porte_technique"],"CONTROLES_TECHNIQUES_VISIBLES")
        self.assertFalse(r["autorisation_publication"])
        self.assertFalse(r["revue_humaine_qualifiee_attestee"])
        self.assertEqual(r["approbation_pre_fusion_exigee_par_serveur"],"NON_ATTESTEE")
        self.assertFalse(r["independance_revue_pre_fusion_attestee"])
    def test_bot_or_owner_identity_never_in_report(self):
        report=json.dumps(m.evaluate(unprotected(),[],"* @publicOwner\n"))
        self.assertNotIn("publicOwner",report)
    def test_head_drift_fails_closed(self):
        b=protected()
        b["commit"]["sha"]="b"*40
        r=m.evaluate(b,[{"enforcement":"active"}],"* @r1 @r2")
        self.assertIn("HEAD_MAIN_CHANGE_REEXAMEN",r["obstacles"])
    def test_unavailable_branch_fails_closed(self):
        r=m.evaluate(None,None,None)
        self.assertIn("BRANCHE_MAIN_NON_LISIBLE",r["obstacles"])
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
    def test_unavailable_rulesets_is_not_assumed_success(self):
        r=m.evaluate(protected(),None,"* @a @b")
        self.assertIn("RULESETS_NON_LISIBLES",r["obstacles"])
    def test_wrong_required_check_fields_are_blocked(self):
        b=protected()
        b["protection"]["required_status_checks"]={"enforcement_level":"off"}
        r=m.evaluate(b,[],"* @a @b")
        self.assertIn("LISTE_CHECKS_NON_LISIBLE",r["obstacles"])
    def test_missing_check_enforcement_blocked(self):
        b=protected()
        b["protection"]["required_status_checks"]["enforcement_level"]="off"
        r=m.evaluate(b,[],"* @a @b")
        self.assertIn("ENFORCEMENT_CHECKS_DESACTIVE_OU_INCONNU",r["obstacles"])
    def test_non_repo_endpoint_rejected(self):
        with self.assertRaises(ValueError):
            m.read_api("/repos/foreign/project/branches/main","")
    def test_cli_gate_fails_with_exit3(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=root/"snapshot.json"
            snap.write_text(json.dumps({"branch":unprotected(),"rulesets":[]}),encoding="utf-8")
            owners=root/"CODEOWNERS"
            owners.write_text("* @owner\n",encoding="utf-8")
            report=root/"report.json"
            code=m.main(["--snapshot",str(snap),"--codeowners",str(owners),
                         "--rapport",str(report),"--exiger-protection"])
            self.assertEqual(code,3)
            self.assertEqual(json.loads(report.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_cli_report_without_gate_returns0(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=root/"snapshot.json"
            snap.write_text(json.dumps({"branch":unprotected(),"rulesets":[]}))
            owners=root/"CODEOWNERS";owners.write_text("* @owner\n")
            code=m.main(["--snapshot",str(snap),"--codeowners",str(owners)])
            self.assertEqual(code,0)
    def test_no_magic_go_even_with_all_fields_green(self):
        r=m.evaluate(protected(),[{"enforcement":"active"}],"* @reviewer1 @reviewer2")
        self.assertFalse(r["autorisation_fusion"])
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")

if __name__=="__main__":
    unittest.main()
