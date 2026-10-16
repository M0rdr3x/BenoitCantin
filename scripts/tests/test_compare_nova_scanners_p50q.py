"""P50Q — tests fictifs du comparateur, sans accès au dépôt distant."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "compare_nova_scanners_p50q.py"
sp = importlib.util.spec_from_file_location("nova_p50q", MODULE)
audit=importlib.util.module_from_spec(sp)
sp.loader.exec_module(audit)

class ComparateurP50Q(unittest.TestCase):
    def test_fourteen_cases_and_distinct_names(self):
        self.assertEqual(len(audit.CASES),14)
        self.assertEqual(len({x[0] for x in audit.CASES}),14)
    def test_eleven_pos_and_three_neg(self):
        self.assertEqual(sum(x[-1] is True for x in audit.CASES),11)
        self.assertEqual(sum(x[-1] is False for x in audit.CASES),3)
    def test_fictitious_always_accepting_scanners_never_go(self):
        r=audit.compare(lambda p: [],lambda p: [])
        self.assertEqual(r["ecarts_avant"],11)
        self.assertEqual(r["ecarts_apres"],11)
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
    def test_fictitious_baseline_rejection_fails_closed(self):
        r=audit.compare(lambda p: ["bad"],lambda p: [])
        self.assertEqual(r["statut"],"INVALIDE")
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
    def test_fake_missing_module_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"report.json"
            rc=audit.main(["--original",str(Path(d)/"missing.py"),
                           "--candidate",str(Path(d)/"missing2.py"),
                           "--report",str(out)])
            self.assertEqual(rc,2)
            self.assertIn("NO_GO_AUTOMATIQUE",out.read_text())

if __name__=="__main__":
    unittest.main()
