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
        "changed_paths":["projets/projet-nova/controles/canaris/"+row["id"]+".txt"]}
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
    def test_actual_canary_checks_file_count_and_scope(self):
        number=801
        github_pr={
            "title":"[P50Y-CANARI:sans_revue] Test",
            "changed_files":1,"state":"open","draft":False,"merged":False,
            "mergeable":True,"mergeable_state":"blocked",
            "head":{"sha":"a"*40,"ref":"test/p50y-sans_revue-1",
                    "repo":{"full_name":m.REPO}},
            "base":{"ref":"main","repo":{"full_name":m.REPO}},
        }
        files=[{"filename":"projets/projet-nova/controles/canaris/notice.txt"}]
        with patch.object(m,"github",side_effect=[github_pr,files]) as mocked:
            result=m.actual_canary(number,"")
        self.assertEqual(mocked.call_count,2)
        self.assertEqual(result["base_ref"],"main")
        self.assertEqual(result["changed_paths"],[files[0]["filename"]])
    def test_actual_canary_refuses_partial_file_inventory(self):
        github_pr={"changed_files":2,"head":{},"base":{}}
        with patch.object(m,"github",side_effect=[github_pr,[{"filename":"one"}]]):
            with self.assertRaises(ValueError):
                m.actual_canary(801,"")
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
