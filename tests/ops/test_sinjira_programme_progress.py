"""Tests adversariaux du tableau d'avancement global SINJIRA."""
import copy
import json
import unittest
from scripts.sinjira_programme_progress import REGISTER, summarize, validate_report


class ProgrammeProgressContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(REGISTER.read_text(encoding="utf-8"))

    def variant(self, change):
        item = copy.deepcopy(self.data)
        change(item)
        return item

    def assert_invalid(self, change, code=None):
        data = self.variant(change)
        errors = validate_report(data)
        self.assertTrue(errors, "Une altération non vérifiée doit être refusée.")
        if code:
            self.assertTrue(any(code in e for e in errors), errors)
        with self.assertRaises(ValueError):
            summarize(data)

    def test_weighted_maturity_is_66_point_5_and_rounded_67(self):
        status = summarize(self.data)
        self.assertEqual(status["maturity_estimate"], 66.5)
        self.assertEqual(status["maturity_rounded"], 67)
        self.assertEqual(status["remaining_estimate"], 33.5)
        self.assertEqual(status["uncertainty_percentage_points"], 10)

    def test_launch_is_not_complete_and_no_date_is_promised(self):
        status = summarize(self.data)
        self.assertIsNone(status["date_of_completion"])
        self.assertFalse(status["launch_ready"])
        self.assertEqual(status["launch_decision"], "NO_GO")
        self.assertEqual(status["open_gate_count"], 13)

    def test_scope_excludes_nova(self):
        self.assert_invalid(lambda d: d.__setitem__("scope", "NOVA"), "WRONG_SCOPE")

    def test_missing_domain_refused(self):
        self.assert_invalid(lambda d: d["domains"].pop(), "DOMAIN_INVENTORY_DRIFT")

    def test_adding_domain_changes_weight_is_refused(self):
        self.assert_invalid(lambda d: d["domains"].append(copy.deepcopy(d["domains"][0])), "DOMAIN_INVENTORY_DRIFT")

    def test_weights_cannot_be_adjusted_to_inflate_maturity(self):
        self.assert_invalid(lambda d: d["domains"][0].__setitem__("weight", 100), "WEIGHT_CHANGED")

    def test_out_of_range_score_refused(self):
        self.assert_invalid(lambda d: d["domains"][1].__setitem__("maturity", 101), "BAD_MATURITY")

    def test_non_numeric_score_refused(self):
        self.assert_invalid(lambda d: d["domains"][2].__setitem__("maturity", "100"), "BAD_MATURITY")

    def test_missing_gate_refused(self):
        self.assert_invalid(lambda d: d["gates"].pop(), "GATE_INVENTORY_DRIFT")

    def test_duplicate_gate_refused(self):
        self.assert_invalid(lambda d: d["gates"].append(copy.deepcopy(d["gates"][0])), "GATE_INVENTORY_DRIFT")

    def test_gate_cannot_be_verified_without_real_proof_fields(self):
        self.assert_invalid(lambda d: d["gates"][0].__setitem__("status", "VERIFIED"), "UNPROVEN_GATE")

    def test_fake_evidence_on_open_gate_refused(self):
        self.assert_invalid(lambda d: d["gates"][1].__setitem__("evidence_url", "https://example.com/fake"),
                            "UNVERIFIED_GATE_HAS_PROOF")

    def test_fake_finish_date_rejected(self):
        self.assert_invalid(lambda d: d["forecast"].__setitem__("estimated_completion_date", "2027-02-15"),
                            "UNSUPPORTED_FINISH_DATE")

    def test_malformed_finish_date_rejected_even_with_source(self):
        def change(d):
            d["forecast"].update({
                "estimated_completion_date": "2027-02-31",
                "evidence_url": "https://github.com/M0rdr3x/BenoitCantin/issues/826",
                "evidence_as_of": "2026-11-08",
            })
        self.assert_invalid(change, "UNSUPPORTED_FINISH_DATE")

    def test_no_100_percent_launch_with_open_gates(self):
        def change(d):
            for row in d["domains"]:
                row["maturity"] = 100
            d["launch"]["complete"] = True
        self.assert_invalid(change, "RELEASE_WITH_OPEN_GATES")

    def test_false_approval_without_provenance_rejected(self):
        self.assert_invalid(lambda d: d["launch"].__setitem__("approved", True), "UNPROVEN_RELEASE_APPROVAL")

    def test_no_declaration_of_complete_without_approval(self):
        self.assert_invalid(lambda d: d["launch"].__setitem__("complete", True), "RELEASE_WITHOUT_APPROVAL")

    def test_100_percent_domains_still_not_a_release(self):
        data = self.variant(lambda d: [
            x.__setitem__("maturity", 100) for x in d["domains"]
        ])
        status = summarize(data)
        self.assertEqual(status["maturity_rounded"], 100)
        self.assertFalse(status["launch_ready"])
        self.assertEqual(status["launch_decision"], "NO_GO")

    def test_forged_commit_sha_rejected(self):
        self.assert_invalid(lambda d: d["recent_verified_deliveries"][0].__setitem__("merge_commit", "fake"),
                            "INVALID_DELIVERY_PROOF")

    def test_launch_cannot_skip_required_maturity_domains(self):
        self.assert_invalid(lambda d: d["domains"][0].__setitem__("id", "novа"),
                            "DOMAIN_INVENTORY_DRIFT")

    def test_baseline_document_cannot_be_swapped(self):
        self.assert_invalid(lambda d: d.__setitem__("baseline_source", "docs/NOVA.md"), "WRONG_BASELINE")

    def test_estimate_requires_documented_uncertainty(self):
        self.assert_invalid(lambda d: d.__setitem__("estimate_uncertainty_percentage_points", 0),
                            "UNCERTAINTY_NOT_DOCUMENTED")


if __name__ == "__main__":
    unittest.main()
