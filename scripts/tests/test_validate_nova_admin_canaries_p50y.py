"""P50Y - Tests de recevabilite de trois essais sans certifier la protection."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SRC=Path(__file__).resolve().parents[1]/"validate_nova_admin_canaries_p50y.py"
spec=importlib.util.spec_from_file_location("nova_p50y",SRC)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def basic():
    return {"schema_version":"P50Y-1","main_sha_avant_essai":m.MAIN_SHA,
            "protection_serveur_confirmee_par_admin":False,
            "bypass_et_permissions_examines":False,
            "relecteur_independant_disponible":False,
            "decision":"NO_GO",
            "cas":[{"id":s,"pr_number":None,"head_sha":None,"pr_url":None,
                    "blocage_constate":False,"verification_humaine":False,
                    "preuve_url":None} for s in m.CASES]}

def filled():
    f=basic()
    f["protection_serveur_confirmee_par_admin"]=True
    f["bypass_et_permissions_examines"]=True
    f["relecteur_independant_disponible"]=True
    for i,row in enumerate(f["cas"]):
        number=800+i
        row.update({"pr_number":number,"head_sha":str(i+1)*40,
                    "pr_url":f"https://github.com/{m.REPO}/pull/{number}",
                    "blocage_constate":True,"verification_humaine":True,
                    "preuve_url":f"https://github.com/{m.REPO}/pull/{number}"})
    return f

def observations(f):
    return {str(row["pr_number"]):{
        "head_sha":row["head_sha"],"open":True,"draft":False,
        "merged":False,"mergeable":True,"mergeable_state":"blocked",
        "base_ref":"main","base_repo":m.REPO,
        "head_repo":m.REPO,
        "head_ref":"test/p50y-"+row["id"]+"-non-fusion",
        "title":"[P50Y-CANARI:"+row["id"]+"] Essai non fusionne",
        "changed_paths":["projets/projet-nova/controles/canaris/"+row["id"]+".txt"],
        "changed_statuses":["added"],
        "changed_previous_paths":[None],
        "review_stats":{
            "submitted_substantive":0 if row["id"]=="sans_revue" else 1,
            "fresh_independent_approvals":1 if row["id"]=="check_non_satisfait" else 0,
            "prior_independent_approval_observed":row["id"]=="approbation_perimee"},
        "check_stats":{
            "checks_success":2 if row["id"]=="check_non_satisfait" else 3,
            "checks_non_satisfaits":1 if row["id"]=="check_non_satisfait" else 0}}
        for row in f["cas"]}

class P50Y(unittest.TestCase):
    def test_three_distinct_cases(self):
        self.assertEqual(len(m.CASES),3)
        self.assertEqual(len(set(m.CASES)),3)
    def test_blank_fixture_is_not_executed(self):
        x=m.analyze(basic())
        self.assertEqual(x["statut_dossier"],"RECETTE_REQUISE")
        self.assertIn("RECETTE_ADMIN_NON_CLOTUREE",x["obstacles"])
    def test_each_blank_case_is_pending(self):
        x=m.analyze(basic())
        self.assertTrue(all(v=="A_EXECUTER" for v in x["cases"].values()))
    def test_false_go_always_rejected(self):
        f=basic();f["decision"]="GO"
        self.assertIn("DOCUMENT_NE_DOIT_PAS_DECLARER_GO",m.analyze(f)["obstacles"])
    def test_unknown_schema_rejected(self):
        f=basic();f["schema_version"]="P50Y-2"
        self.assertIn("SCHEMA_INATTENDU",m.analyze(f)["obstacles"])
    def test_main_reference_drift_rejected(self):
        f=basic();f["main_sha_avant_essai"]="f"*40
        self.assertIn("SHA_MAIN_REFERENCE_A_ACTUALISER",m.analyze(f)["obstacles"])
    def test_duplicate_case_detected(self):
        f=basic();f["cas"][1]["id"]=f["cas"][0]["id"]
        self.assertIn("TROIS_CAS_UNIQUES_REQUIS",m.analyze(f)["obstacles"])
    def test_non_string_id_rejected_not_crash(self):
        f=basic();f["cas"][0]["id"]=None
        self.assertIn("TROIS_CAS_UNIQUES_REQUIS",m.analyze(f)["obstacles"])
    def test_no_canary_references_not_legal_evidence(self):
        r=m.analyze(basic())
        self.assertFalse(r["protection_main_installee_par_ce_programme"])
        self.assertFalse(r["fusion_autorisee"])
        self.assertFalse(r["publication_autorisee"])
    def test_filled_declarations_still_not_a_go(self):
        x=m.analyze(filled())
        self.assertEqual(x["statut_dossier"],"DECLARATIONS_COMPLETEES_A_VALIDER_EXTERNEMENT")
        self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")
        self.assertFalse(x["preuve_serveur_certifiee_automatiquement"])
    def test_urls_cannot_point_to_other_repo(self):
        f=filled();f["cas"][0]["preuve_url"]="https://github.com/unrelated/example/pull/2"
        self.assertIn("PREUVE_URL_NON_CONFORME:sans_revue",m.analyze(f)["obstacles"])
    def test_pr_url_matches_number(self):
        f=filled();f["cas"][0]["pr_url"]=f"https://github.com/{m.REPO}/pull/99"
        self.assertIn("URL_PR_NON_CONFORME:sans_revue",m.analyze(f)["obstacles"])
    def test_sha_must_be_forty_hex(self):
        f=filled();f["cas"][0]["head_sha"]="bad"
        self.assertIn("IDENTIFIANT_CANARI_ABSENT:sans_revue",m.analyze(f)["obstacles"])
    def test_pr_boolean_is_not_number(self):
        f=filled();f["cas"][0]["pr_number"]=True
        self.assertIn("IDENTIFIANT_CANARI_ABSENT:sans_revue",m.analyze(f)["obstacles"])
    def test_three_pr_numbers_must_be_distinct(self):
        f=filled();f["cas"][0]["pr_number"]=f["cas"][1]["pr_number"]
        self.assertIn("TROIS_PR_TEMOINS_DISTINCTES_REQUISES",m.analyze(f)["obstacles"])
    def test_missing_human_verification_blocks_completion(self):
        f=filled();f["cas"][2]["verification_humaine"]=False
        self.assertIn("PREUVE_HUMAINE_INCOMPLETE:check_non_satisfait",m.analyze(f)["obstacles"])
    def test_draft_cannot_prove_required_review_gate(self):
        f=filled();o=observations(f);o["800"]["draft"]=True
        self.assertIn("CANARI_PAS_OUVERT_PRET_OU_SHA_DIVERGENT:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_merged_canary_invalid(self):
        f=filled();o=observations(f);o["800"]["merged"]=True
        self.assertIn("CANARI_PAS_OUVERT_PRET_OU_SHA_DIVERGENT:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_clean_versus_blocked_distinguished(self):
        f=filled();o=observations(f);o["800"]["mergeable_state"]="clean"
        self.assertIn("GITHUB_N_ATTESTE_PAS_LE_BLOCAGE:sans_revue",m.analyze(f,o)["obstacles"])
    def test_blocked_state_is_still_not_a_go(self):
        f=filled();x=m.analyze(f,observations(f))
        self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")
        self.assertFalse(x["preuve_serveur_certifiee_automatiquement"])
    def test_missing_live_state_blocks(self):
        f=filled();o=observations(f);del o["800"]
        self.assertIn("ETAT_GITHUB_NON_LISIBLE:sans_revue",m.analyze(f,o)["obstacles"])
    def test_existing_real_pr_cannot_be_canary(self):
        f=filled();o=observations(f)
        o["800"]["title"]="P50Y — Vraie PR du projet"
        self.assertIn("CANARI_IDENTITE_OU_CIBLE_INVALIDE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_wrong_base_branch_rejected(self):
        f=filled();o=observations(f);o["800"]["base_ref"]="other-branch"
        self.assertIn("CANARI_IDENTITE_OU_CIBLE_INVALIDE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_wrong_target_repository_rejected(self):
        f=filled();o=observations(f);o["800"]["base_repo"]="another/repo"
        self.assertIn("CANARI_IDENTITE_OU_CIBLE_INVALIDE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_fork_not_implicitly_trusted(self):
        f=filled();o=observations(f);o["800"]["head_repo"]="another/repo"
        self.assertIn("CANARI_IDENTITE_OU_CIBLE_INVALIDE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_wrong_test_branch_rejected(self):
        f=filled();o=observations(f);o["800"]["head_ref"]="review/real-project"
        self.assertIn("CANARI_IDENTITE_OU_CIBLE_INVALIDE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_wrong_scenario_marker_rejected(self):
        f=filled();o=observations(f)
        o["800"]["title"]="[P50Y-CANARI:check_non_satisfait] Other"
        self.assertIn("CANARI_IDENTITE_OU_CIBLE_INVALIDE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_real_site_file_change_rejected(self):
        f=filled();o=observations(f)
        o["800"]["changed_paths"]=["projets/projet-nova/participer.html"]
        self.assertIn("CANARI_FICHIERS_HORS_REPERTOIRE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_empty_change_list_rejected(self):
        f=filled();o=observations(f);o["800"]["changed_paths"]=[]
        self.assertIn("CANARI_FICHIERS_HORS_REPERTOIRE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_excessive_change_list_rejected(self):
        f=filled();o=observations(f)
        o["800"]["changed_paths"]=["projets/projet-nova/controles/canaris/"+str(i)+".txt" for i in range(4)]
        self.assertIn("CANARI_FICHIERS_HORS_REPERTOIRE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_allowed_new_text_file_is_accepted_documentarily(self):
        f=filled();o=observations(f)
        r=m.analyze(f,o)
        self.assertEqual(r["statut_dossier"],"DECLARATIONS_COMPLETEES_A_VALIDER_EXTERNEMENT")
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
    def test_rename_from_real_website_is_not_safe(self):
        f=filled();o=observations(f)
        o["800"]["changed_statuses"]=["renamed"]
        o["800"]["changed_previous_paths"]=["projets/projet-nova/participer.html"]
        self.assertIn("CANARI_FICHIERS_HORS_REPERTOIRE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_replaced_file_in_canary_directory_is_not_safe(self):
        f=filled();o=observations(f)
        o["800"]["changed_statuses"]=["modified"]
        self.assertIn("CANARI_FICHIERS_HORS_REPERTOIRE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_deleted_file_in_canary_directory_is_not_safe(self):
        f=filled();o=observations(f)
        o["800"]["changed_statuses"]=["removed"]
        self.assertIn("CANARI_FICHIERS_HORS_REPERTOIRE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_unexpected_previous_filename_even_on_added_is_blocked(self):
        f=filled();o=observations(f)
        o["800"]["changed_previous_paths"]=["projets/projet-nova/participer.html"]
        self.assertIn("CANARI_FICHIERS_HORS_REPERTOIRE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_active_code_in_canary_path_is_rejected(self):
        f=filled();o=observations(f)
        o["800"]["changed_paths"]=["projets/projet-nova/controles/canaris/launch.py"]
        self.assertIn("CANARI_FICHIERS_HORS_REPERTOIRE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_nested_path_not_allowed(self):
        f=filled();o=observations(f)
        o["800"]["changed_paths"]=["projets/projet-nova/controles/canaris/inner/demo.txt"]
        self.assertIn("CANARI_FICHIERS_HORS_REPERTOIRE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_hidden_filename_not_allowed(self):
        f=filled();o=observations(f)
        o["800"]["changed_paths"]=["projets/projet-nova/controles/canaris/.secret.txt"]
        self.assertIn("CANARI_FICHIERS_HORS_REPERTOIRE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_missing_file_status_is_not_assumed_added(self):
        f=filled();o=observations(f)
        del o["800"]["changed_statuses"]
        self.assertIn("CANARI_FICHIERS_HORS_REPERTOIRE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_file_status_counts_must_match_paths(self):
        f=filled();o=observations(f)
        o["800"]["changed_statuses"]=[]
        self.assertIn("CANARI_FICHIERS_HORS_REPERTOIRE:sans_revue",
                      m.analyze(f,o)["obstacles"])
    def test_evidence_for_another_pr_not_accepted(self):
        f=filled()
        f["cas"][0]["preuve_url"]=f"https://github.com/{m.REPO}/pull/999"
        self.assertIn("PREUVE_NON_RATTACHEE_AU_CANARI:sans_revue",
                      m.analyze(f)["obstacles"])
    def test_unrelated_actions_run_not_accepted(self):
        f=filled()
        f["cas"][0]["preuve_url"]=f"https://github.com/{m.REPO}/actions/runs/99"
        self.assertIn("PREUVE_NON_RATTACHEE_AU_CANARI:sans_revue",
                      m.analyze(f)["obstacles"])
    def test_canary_cannot_use_another_real_pr_as_evidence(self):
        f=filled()
        f["cas"][0]["preuve_url"]=f"https://github.com/{m.REPO}/pull/640"
        self.assertEqual(m.analyze(f)["statut_dossier"],"RECETTE_REQUISE")
    def test_file_status_metadata_from_github_is_preserved(self):
        pr={
            "title":"[P50Y-CANARI:sans_revue] Test","user":{"id":90},
            "changed_files":1,"state":"open","draft":False,"merged":False,
            "mergeable":True,"mergeable_state":"blocked",
            "head":{"sha":"a"*40,"ref":"test/p50y-sans_revue-new",
                    "repo":{"full_name":m.REPO}},
            "base":{"ref":"main","repo":{"full_name":m.REPO}},
        }
        files=[{"filename":"projets/projet-nova/controles/canaris/a.txt",
                "status":"renamed","previous_filename":"projets/projet-nova/participer.html"}]
        check_runs={"total_count":3,"check_runs":[
            {"name":name,"head_sha":"a"*40,"app":{"id":m.ACTIONS_APP_ID},
             "status":"completed","conclusion":"success"} for name in m.REQUIRED_CHECKS]}
        with patch.object(m,"github",side_effect=[pr,files,[],check_runs]):
            r=m.actual_canary(801,"")
        self.assertEqual(r["changed_statuses"],["renamed"])
        self.assertEqual(r["changed_previous_paths"],["projets/projet-nova/participer.html"])
    def test_actual_canary_checks_file_count_and_scope(self):
        number=801
        github_pr={
            "title":"[P50Y-CANARI:sans_revue] Test",
            "user":{"id":90,"type":"User"},
            "changed_files":1,"state":"open","draft":False,"merged":False,
            "mergeable":True,"mergeable_state":"blocked",
            "head":{"sha":"a"*40,"ref":"test/p50y-sans_revue-1",
                    "repo":{"full_name":m.REPO}},
            "base":{"ref":"main","repo":{"full_name":m.REPO}},
        }
        files=[{"filename":"projets/projet-nova/controles/canaris/notice.txt",
                "status":"added"}]
        with patch.object(m,"github",side_effect=[
            github_pr, files, [],
            {"total_count":3,"check_runs":[
                {"name":name,"head_sha":"a"*40,"app":{"id":m.ACTIONS_APP_ID},
                 "status":"completed","conclusion":"success"}
                for name in m.REQUIRED_CHECKS]},
        ]) as mocked:
            result=m.actual_canary(number,"")
        self.assertEqual(mocked.call_count,4)
        self.assertEqual(result["base_ref"],"main")
        self.assertEqual(result["changed_paths"],[files[0]["filename"]])
    def test_actual_canary_refuses_partial_file_inventory(self):
        github_pr={"changed_files":2,"head":{},"base":{}}
        with patch.object(m,"github",side_effect=[github_pr,[{"filename":"one"}]]):
            with self.assertRaises(ValueError):
                m.actual_canary(801,"")
    def test_absence_revue_but_ci_failed_is_not_valid_test(self):
        f=filled();o=observations(f)
        o["800"]["check_stats"]={"checks_success":2,"checks_non_satisfaits":1}
        self.assertIn("OBSERVATIONS_NE_SOUTIENNENT_PAS_LE_SCENARIO:sans_revue",m.analyze(f,o)["obstacles"])
    def test_stale_approval_must_exist(self):
        f=filled();o=observations(f)
        o["801"]["review_stats"]["prior_independent_approval_observed"]=False
        self.assertIn("OBSERVATIONS_NE_SOUTIENNENT_PAS_LE_SCENARIO:approbation_perimee",m.analyze(f,o)["obstacles"])
    def test_stale_approval_with_fresh_approval_rejected(self):
        f=filled();o=observations(f)
        o["801"]["review_stats"]["fresh_independent_approvals"]=1
        self.assertIn("OBSERVATIONS_NE_SOUTIENNENT_PAS_LE_SCENARIO:approbation_perimee",m.analyze(f,o)["obstacles"])
    def test_check_failure_requires_independent_approval(self):
        f=filled();o=observations(f)
        o["802"]["review_stats"]["fresh_independent_approvals"]=0
        self.assertIn("OBSERVATIONS_NE_SOUTIENNENT_PAS_LE_SCENARIO:check_non_satisfait",m.analyze(f,o)["obstacles"])
    def test_check_failure_with_three_green_rejected(self):
        f=filled();o=observations(f)
        o["802"]["check_stats"]={"checks_success":3,"checks_non_satisfaits":0}
        self.assertIn("OBSERVATIONS_NE_SOUTIENNENT_PAS_LE_SCENARIO:check_non_satisfait",m.analyze(f,o)["obstacles"])
    def test_missing_review_summary_rejected(self):
        f=filled();o=observations(f)
        del o["800"]["review_stats"]
        self.assertIn("REVUES_OU_CHECKS_NON_ATTESTES:sans_revue",m.analyze(f,o)["obstacles"])
    def test_review_evidence_fresh_valid(self):
        rows=[{"state":"APPROVED","commit_id":"a"*40,
               "user":{"id":42,"type":"User"},"submitted_at":"2026-10-17T00:00:00Z"}]
        result=m.review_evidence(rows,"a"*40,author_id=99)
        self.assertEqual(result["fresh_independent_approvals"],1)
        self.assertFalse(result["prior_independent_approval_observed"])
    def test_review_evidence_stale_approval(self):
        rows=[{"state":"APPROVED","commit_id":"a"*40,
               "user":{"id":42,"type":"User"},"submitted_at":"2026-10-17T00:00:00Z"}]
        result=m.review_evidence(rows,"b"*40,author_id=99)
        self.assertEqual(result["fresh_independent_approvals"],0)
        self.assertTrue(result["prior_independent_approval_observed"])
    def test_dismissed_review_alone_not_historical_approval(self):
        rows=[{"state":"DISMISSED","commit_id":"a"*40,
               "user":{"id":42,"type":"User"},"submitted_at":"2026-10-17T00:00:00Z"}]
        result=m.review_evidence(rows,"b"*40,author_id=99)
        self.assertFalse(result["prior_independent_approval_observed"])
        self.assertEqual(result["fresh_independent_approvals"],0)
    def test_dismissed_review_does_not_prove_perimee_case(self):
        f=filled();o=observations(f)
        o["801"]["review_stats"]["prior_independent_approval_observed"]=False
        self.assertIn("OBSERVATIONS_NE_SOUTIENNENT_PAS_LE_SCENARIO:approbation_perimee",
                      m.analyze(f,o)["obstacles"])
    def test_latest_review_requested_changes_replaces_approval(self):
        rows=[
            {"state":"APPROVED","commit_id":"a"*40,"user":{"id":42,"type":"User"},
             "submitted_at":"2026-10-17T00:00:00Z"},
            {"state":"CHANGES_REQUESTED","commit_id":"a"*40,"user":{"id":42,"type":"User"},
             "submitted_at":"2026-10-17T00:30:00Z"},
        ]
        self.assertEqual(m.review_evidence(rows,"a"*40,author_id=99)
                         ["fresh_independent_approvals"],0)
    def test_review_evidence_author_excluded(self):
        rows=[{"state":"APPROVED","commit_id":"a"*40,
               "user":{"id":99,"type":"User"},"submitted_at":"2026-10-17T00:00:00Z"}]
        self.assertEqual(m.review_evidence(rows,"a"*40,99)["fresh_independent_approvals"],0)
    def test_review_pagination_rejected(self):
        with self.assertRaises(ValueError):
            m.review_evidence([{}]*100,"a"*40,99)
    def test_checks_successes_and_failure(self):
        checks={"total_count":3,"check_runs":[
            {"name":name,"head_sha":"a"*40,"app":{"id":m.ACTIONS_APP_ID},
             "status":"completed","conclusion":"failure" if i==1 else "success"}
            for i,name in enumerate(m.REQUIRED_CHECKS)]}
        evidence=m.checks_evidence(checks,"a"*40)
        self.assertEqual(evidence,{"checks_success":2,"checks_non_satisfaits":1})
    def test_duplicate_required_check_rejected(self):
        row={"name":m.REQUIRED_CHECKS[0],"head_sha":"a"*40,
             "app":{"id":m.ACTIONS_APP_ID},"status":"completed","conclusion":"success"}
        checks={"total_count":2,"check_runs":[row,row.copy()]}
        with self.assertRaises(ValueError):
            m.checks_evidence(checks,"a"*40)
    def test_check_from_wrong_app_rejected(self):
        checks={"total_count":1,"check_runs":[
            {"name":m.REQUIRED_CHECKS[0],"head_sha":"a"*40,
             "app":{"id":999},"status":"completed","conclusion":"success"}]}
        with self.assertRaises(ValueError):
            m.checks_evidence(checks,"a"*40)
    def test_missing_checks_not_considered_all_green(self):
        x=m.checks_evidence({"total_count":0,"check_runs":[]},"a"*40)
        self.assertEqual(x,{"checks_success":0,"checks_non_satisfaits":3})
    def test_checks_pagination_rejected(self):
        with self.assertRaises(ValueError):
            m.checks_evidence({"total_count":100,"check_runs":[]},"a"*40)
    def test_identified_blocked_canary_still_no_go(self):
        f=filled()
        x=m.analyze(f,observations(f))
        self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")
        self.assertEqual(x["statut_dossier"],"DECLARATIONS_COMPLETEES_A_VALIDER_EXTERNEMENT")
    def test_missing_file_cli_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            inp=Path(temp)/"missing.json";out=Path(temp)/"out.json"
            self.assertEqual(m.main(["--dossier",str(inp),"--rapport",str(out)]),2)
            self.assertEqual(json.loads(out.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_blank_file_cli_succeeds_as_report_only(self):
        with tempfile.TemporaryDirectory() as temp:
            inp=Path(temp)/"input.json";out=Path(temp)/"out.json"
            inp.write_text(json.dumps(basic()),encoding="utf-8")
            self.assertEqual(m.main(["--dossier",str(inp),"--rapport",str(out)]),0)
            self.assertEqual(json.loads(out.read_text())["statut_dossier"],"RECETTE_REQUISE")
    def test_external_github_endpoint_rejected(self):
        with self.assertRaises(ValueError):
            m.github("/repos/another/repo/pulls/999","")
    def test_no_reviewer_name_in_summary(self):
        f=filled()
        r=json.dumps(m.analyze(f))
        self.assertNotIn("@",r)
        self.assertNotIn("reviewer_login",r)

if __name__=="__main__":
    unittest.main()
