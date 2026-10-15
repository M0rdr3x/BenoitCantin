"""P50M — tests de structure du dossier, jamais de validation de pouvoir réel."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "scripts/validate_nova_decision_p50m.py"
DOC = ROOT / "projets/projet-nova/controles/P50M_ETAT_PUBLIC_DECISION.json"
spec = importlib.util.spec_from_file_location("nova_p50m", MOD)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
FIXTURE = json.loads(DOC.read_text(encoding="utf-8"))

class TestP50M(unittest.TestCase):
    def sample(self):
        return copy.deepcopy(FIXTURE)
    def verify(self, data):
        return v.validate(data)
    def check_invalid(self, data, marker):
        result=self.verify(data)
        self.assertEqual(result["structure"],"INVALIDE")
        self.assertIn(marker, result["anomalies"])
        self.assertEqual(result["decision"],"NO_GO_AUTOMATIQUE")
    def test_template_valid(self):
        self.assertEqual(self.verify(self.sample())["structure"],"MODELE_VALIDE_NON_PROBANT")
    def test_never_go(self):
        self.assertEqual(self.verify(self.sample())["decision"],"NO_GO_AUTOMATIQUE")
    def test_ten_prs(self):
        self.assertEqual(len(self.sample()["pull_requests"]),10)
    def test_pr_review_snapshot(self):
        d=self.sample()
        self.assertEqual({p["number"]:p["formal_reviews_observed"] for p in d["pull_requests"]
                          if p["number"] in [636,638,650,651]},dict.fromkeys([636,638,650,651],0))
    def test_five_human_checks_all_unknown(self):
        d=self.sample();self.assertEqual(len(d["human_checks"]),5)
        self.assertTrue(all(x["status"]=="NON_ATTESTE" for x in d["human_checks"]))
    def test_nine_legal_evidence_empty(self):
        self.assertEqual(len(self.sample()["legal_evidence"]),9)
    def test_twelve_mail_proofs_empty(self):
        self.assertEqual(len(self.sample()["mail_evidence"]),12)
    def test_fourteen_publication_gates(self):
        d=self.sample();self.assertEqual(len(d["publication_gates"]),14)
        self.assertEqual([r["id"] for r in d["publication_gates"] if r["phase"]=="POST"],["B12","B14"])
    def test_go_forgery_rejected(self):
        d=self.sample();d["runtime_status"]="GO"
        self.check_invalid(d,"AUTORISATION_NON_RECEVABLE")
    def test_cannot_authorize_public_actions(self):
        d=self.sample();d["public_actions_authorized"]=["merge"]
        self.check_invalid(d,"AUTORISATION_NON_RECEVABLE")
    def test_pr640_guard_mandatory(self):
        d=self.sample();d["guards"].remove("PR_640_NE_JAMAIS_FUSIONNER")
        self.check_invalid(d,"GARDE_FOU_MANQUANT")
    def test_pr640_never_mergeable(self):
        d=self.sample();next(p for p in d["pull_requests"] if p["number"]==640)["eligible_for_automatic_merge"]=True
        self.check_invalid(d,"PR_PROMUE_SANS_PREUVE_640")
    def test_no_pr_already_merged(self):
        d=self.sample();d["pull_requests"][0]["merged"]=True
        self.check_invalid(d,"PR_PROMUE_SANS_PREUVE_636")
    def test_no_pr_ready_for_review(self):
        d=self.sample();d["pull_requests"][1]["draft"]=False
        self.check_invalid(d,"PR_PROMUE_SANS_PREUVE_638")
    def test_no_review_forgery(self):
        d=self.sample();next(p for p in d["pull_requests"] if p["number"]==651)["formal_reviews_observed"]=1
        self.check_invalid(d,"REVUE_FICTIVE_651")
    def test_no_claim_about_unsampled_reviews(self):
        d=self.sample();next(p for p in d["pull_requests"] if p["number"]==647)["formal_reviews_observed"]=0
        self.check_invalid(d,"REVUE_NON_RELEVE_647")
    def test_absent_pr_detected(self):
        d=self.sample();d["pull_requests"].pop()
        self.check_invalid(d,"PR_MANQUANTES")
    def test_duplicate_pr_detected(self):
        d=self.sample();d["pull_requests"][1]["number"]=636
        self.check_invalid(d,"PR_INCONNUE_OU_DUPLIQUEE")
    def test_bad_sha_detected(self):
        d=self.sample();d["main_sha"]="unknown"
        self.check_invalid(d,"SHA_MAIN_INVALIDE")
    def test_claim_mailbox_audited_detected(self):
        d=self.sample();d["mailbox_technical_audit_performed"]=True
        self.check_invalid(d,"FAUSSE_ATTESTATION_REELLE")
    def test_claim_legal_review_detected(self):
        d=self.sample();d["formal_legal_advice_authenticated"]=True
        self.check_invalid(d,"FAUSSE_ATTESTATION_REELLE")
    def test_false_human_check_attestation(self):
        d=self.sample();d["human_checks"][0]["status"]="VALIDE"
        self.check_invalid(d,"FAUSSE_ATTESTATION_C01")
    def test_false_mail_evidence_attestation(self):
        d=self.sample();d["mail_evidence"][6]["status"]="VERIFIE"
        self.check_invalid(d,"FAUSSE_ATTESTATION_M07")
    def test_wrong_phase_detected(self):
        d=self.sample();d["publication_gates"][11]["phase"]="PRE"
        self.check_invalid(d,"PHASE_INVALIDE_B12")
    def test_extra_private_key_rejected(self):
        d=self.sample();d["courriel_personnel"]="private@example.test"
        self.check_invalid(d,"CHAMPS_PUBLICS_SUPPLEMENTAIRES_OU_MANQUANTS")
    def test_source_says_not_live(self):
        d=self.sample();d["source"]="GITHUB_API_LIVE"
        self.check_invalid(d,"SOURCE_NON_FIABLE_OU_MODIFIEE")
    def test_missing_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            x=Path(td)/"missing.json"
            output=Path(td)/"result.json"
            self.assertEqual(v.main(["--registre",str(x),"--rapport",str(output)]),2)
            self.assertEqual(json.loads(output.read_text())["decision"],"NO_GO_AUTOMATIQUE")

if __name__=="__main__":
    unittest.main()
