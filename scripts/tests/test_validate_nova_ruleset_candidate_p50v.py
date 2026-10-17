"""P50V — tests du candidat de ruleset, sans GitHub admin ni réseau."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MOD=Path(__file__).resolve().parents[1]/"validate_nova_ruleset_candidate_p50v.py"
sp=importlib.util.spec_from_file_location("nova_p50v",MOD)
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)

def valid_ruleset():
    return {
      "name":"SINJIRA et Projet Nova - protection main (candidat P50V)",
      "target":"branch","enforcement":"disabled","bypass_actors":[],
      "conditions":{"ref_name":{"include":["refs/heads/main"],"exclude":[]}},
      "rules":[
        {"type":"deletion"},
        {"type":"non_fast_forward"},
        {"type":"pull_request","parameters":{
            "allowed_merge_methods":["merge","squash"],
            "dismiss_stale_reviews_on_push":True,
            "require_code_owner_review":False,
            "require_last_push_approval":True,
            "required_approving_review_count":1,
            "required_review_thread_resolution":True}},
        {"type":"required_status_checks","parameters":{
            "strict_required_status_checks_policy":True,
            "required_status_checks":[{"context":x} for x in m.SOURCES]}}
      ]
    }

def mock_sources():
    result={}
    for name,(path,sha,needle) in m.SOURCES.items():
        header="on:\n  pull_request:\n"
        workflow=header+"permissions:\n  contents: read\njobs:\n  test:\n    "+needle+"\n"
        result[path]=workflow.encode()
    return result

class P50VCandidate(unittest.TestCase):
    def setUp(self):
        self.original=m.SOURCES.copy()
        self.sources=mock_sources()
        for label,(path,sha,needle) in self.original.items():
            m.SOURCES[label]=(path,m.git_blob_sha(self.sources[path]),needle)
        self.spec=valid_ruleset()
    def tearDown(self):
        m.SOURCES.clear()
        m.SOURCES.update(self.original)
    def has(self,issue):
        return issue in m.validate(self.spec,self.sources)["anomalies"]
    def test_valid_disabled_model(self):
        r=m.validate(self.spec,self.sources)
        self.assertEqual(r["validation_du_candidat"],"CANDIDAT_CONFORME_EN_LECTURE_SEULE")
        self.assertFalse(r["ruleset_installe"])
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
    def test_attempt_to_activate_in_repo_blocked(self):
        self.spec["enforcement"]="active"
        self.assertTrue(self.has("ENFORCEMENT_DOIT_RESTER_DISABLED_DANS_DEPOT"))
    def test_bypass_actors_forbidden(self):
        self.spec["bypass_actors"]=[{"actor_id":1,"actor_type":"RepositoryRole"}]
        self.assertTrue(self.has("BYPASS_NON_AUTORISE_DANS_CANDIDAT"))
    def test_main_scope_only(self):
        self.spec["conditions"]["ref_name"]["include"].append("refs/heads/develop")
        self.assertTrue(self.has("CIBLE_MAIN_NON_EXCLUSIVE"))
    def test_required_review_not_zero(self):
        self.spec["rules"][2]["parameters"]["required_approving_review_count"]=0
        self.assertTrue(self.has("PARAMETRE_REVUE_INCORRECT:required_approving_review_count"))
    def test_no_last_push_review_blocked(self):
        self.spec["rules"][2]["parameters"]["require_last_push_approval"]=False
        self.assertTrue(self.has("PARAMETRE_REVUE_INCORRECT:require_last_push_approval"))
    def test_stale_approvals_must_be_dismissed(self):
        self.spec["rules"][2]["parameters"]["dismiss_stale_reviews_on_push"]=False
        self.assertTrue(self.has("PARAMETRE_REVUE_INCORRECT:dismiss_stale_reviews_on_push"))
    def test_code_owner_review_cannot_be_assumed(self):
        self.spec["rules"][2]["parameters"]["require_code_owner_review"]=True
        self.assertTrue(self.has("PARAMETRE_REVUE_INCORRECT:require_code_owner_review"))
    def test_no_force_pushes(self):
        self.spec["rules"]=[r for r in self.spec["rules"] if r["type"]!="non_fast_forward"]
        self.assertIn("REGLES_SECURITE_MANQUANTES_OU_INATTENDUES",
                      m.validate(self.spec,self.sources)["anomalies"])
    def test_no_deletion_required(self):
        self.spec["rules"][0]={"type":"branch_name_pattern"}
        self.assertIn("REGLES_SECURITE_MANQUANTES_OU_INATTENDUES",
                      m.validate(self.spec,self.sources)["anomalies"])
    def test_three_exact_checks_required(self):
        self.spec["rules"][3]["parameters"]["required_status_checks"].pop()
        self.assertTrue(self.has("TROIS_CHECKS_UNIVERSELS_EXACTS_MANQUANTS"))
    def test_strict_ci_required(self):
        self.spec["rules"][3]["parameters"]["strict_required_status_checks_policy"]=False
        self.assertTrue(self.has("CHECKS_STRICT_NON_ACTIFS"))
    def test_duplicate_rules_are_disallowed(self):
        self.spec["rules"][1]={"type":"deletion"}
        self.assertTrue(self.has("REGLES_SECURITE_MANQUANTES_OU_INATTENDUES"))
    def test_path_filters_forbidden(self):
        path=next(iter(self.sources))
        self.sources[path]=self.sources[path].replace(b"  pull_request:\n",
                                                     b"  pull_request:\n    paths:\n      - foo/**\n")
        problems=m.validate(self.spec,self.sources)["anomalies"]
        self.assertIn("FILTRE_CHEMIN_INTERDIT:no-committed-secrets",problems)
    def test_source_drift_blocked(self):
        path=next(iter(self.sources))
        self.sources[path]+=b"\n# changed"
        self.assertIn("WORKFLOW_SOURCE_SHA_MODIFIE:no-committed-secrets",
                      m.validate(self.spec,self.sources)["anomalies"])
    def test_missing_job_name_blocked(self):
        label="Contrat sécurité validation site"
        path=m.SOURCES[label][0]
        self.sources[path]=self.sources[path].replace(b"name: Contrat securite",
                                                     b"name: Renamed")
        # Exact accents are intentional in the actual fixture.
        self.sources[path]=self.sources[path].replace(
            "name: Contrat sécurité validation site".encode(),
            b"name: Renamed")
        self.assertIn("NOM_JOB_EXACT_ABSENT:"+label,
                      m.validate(self.spec,self.sources)["anomalies"])
    def test_missing_source_blocked(self):
        del self.sources[next(iter(self.sources))]
        self.assertIn("WORKFLOW_SOURCE_INDISPONIBLE:no-committed-secrets",
                      m.validate(self.spec,self.sources)["anomalies"])
    def test_bad_source_is_no_go(self):
        r=m.validate(None,{})
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
        self.assertEqual(r["validation_du_candidat"],"CANDIDAT_BLOQUE")
    def test_file_blob_sha(self):
        self.assertEqual(m.git_blob_sha(b"hello\n"),"ce013625030ba8dba906f756967f9e9ca394464a")
    def test_no_legal_powers_conveyed(self):
        r=m.validate(self.spec,self.sources)
        self.assertFalse(r["publication_autorisee"])
        self.assertFalse(r["fusion_autorisee"])
        self.assertFalse(r["revue_independante_juridiquement_attestee"])

if __name__=="__main__":
    unittest.main()
