"""P50O : tests sur données fictives de l'instrument de diagnostic."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
SOURCE = HERE / "diagnostic_nova_pr636_p50o.py"
spec = importlib.util.spec_from_file_location("p50o", SOURCE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class ReviewDiagnosticTests(unittest.TestCase):
    def fake_candidate(self, root):
        page = lambda p: (root/p).read_text(encoding="utf-8")
        if "formspree.io" in page("participer.html"):
            return ["formspree detected"]
        if "<form" in page("contact.html"):
            return ["active form detected"]
        if "visionneuse.html?doc=formulaire-soutien" in page("participer.html"):
            return ["legacy pdf detected"]
        return []

    def robust_candidate(self, root):
        # La variante fictive rejette toutes les anomalies simulées.
        pages = {x:(root/x).read_text(encoding="utf-8") for x in tool.FILES}
        if (pages == tool.BASE):
            return []
        return ["modification detected"]

    def test_expected_fixture_count(self):
        self.assertEqual(len(tool.FILES), 5)
        self.assertEqual(len(tool.PROBES), 11)

    def test_all_probe_identifiers_unique(self):
        ids = [x["id"] for x in tool.PROBES]
        self.assertEqual(len(ids),len(set(ids)))

    def test_no_personal_data_in_probe_payload(self):
        text = json.dumps(tool.PROBES)
        self.assertNotIn("nass",text.lower())
        self.assertNotIn("password",text.lower())

    def test_baseline_contains_mailto_link(self):
        self.assertIn('href="mailto:',tool.BASE["contact.html"])

    def test_faux_validator_yields_eight_blind_spots(self):
        out = tool.diagnose(self.fake_candidate)
        self.assertEqual(out["audit"],"DIAGNOSTIC_TERMINE")
        self.assertEqual(out["angles_morts_reproduits"],8)
        self.assertEqual(out["decision"],"NO_GO_AUTOMATIQUE")

    def test_faux_validator_catches_three_positive_controls(self):
        out = tool.diagnose(self.fake_candidate)
        found={x["id"]:x["rejet_observe"] for x in out["cas"]}
        self.assertEqual({k:found[k] for k in ("C01","C02","C03")},
                         {"C01":True,"C02":True,"C03":True})

    def test_robust_validator_should_have_zero_gaps(self):
        out = tool.diagnose(self.robust_candidate)
        self.assertEqual(out["angles_morts_reproduits"],0)
        self.assertEqual(out["decision"],"NO_GO_AUTOMATIQUE")

    def test_never_claim_human_approval(self):
        out = tool.diagnose(self.fake_candidate)
        self.assertFalse(out["approbation_humaine"])
        self.assertFalse(out["autorisation_juridique"])

    def test_baseline_noncompliance_fails_closed(self):
        def rejects_all(root):
            return ["invalid"]
        out = tool.diagnose(rejects_all)
        self.assertEqual(out["audit"],"BASE_NON_CONFORME")
        self.assertEqual(out["decision"],"NO_GO_AUTOMATIQUE")

    def test_missing_candidate_is_error(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                tool.load_candidate(Path(td)/"absent.py")

    def test_end_to_end_with_safe_dummy_candidate_module(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td)/"fake.py"
            src.write_text("def validate(root):\n    return []\n",encoding="utf-8")
            func = tool.load_candidate(src)
            out = tool.diagnose(func)
            self.assertEqual(out["angles_morts_reproduits"],11)
            self.assertEqual(out["decision"],"NO_GO_AUTOMATIQUE")

    def test_cli_missing_candidate_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            report=Path(td)/"out.json"
            self.assertEqual(tool.main(["--candidate",str(Path(td)/"missing.py"),
                                        "--report",str(report)]),2)
            self.assertEqual(json.loads(report.read_text())["decision"],"NO_GO_AUTOMATIQUE")

if __name__=="__main__":
    unittest.main()
