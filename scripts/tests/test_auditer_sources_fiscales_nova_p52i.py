"""P52I — garde-fous des sources : aucun GO invente."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "auditer_sources_fiscales_nova_p52i.py"
spec = importlib.util.spec_from_file_location("nova_p52i", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def inputs():
    return m.read_json(m.DEFAULT_CATALOG), m.read_json(m.DEFAULT_PROOFS)

class SourcesNova(unittest.TestCase):
    def test_01_twenty_source_requirements(self):
        c, p = inputs()
        self.assertEqual(m.analyser(c,p)["preuves_P52A_requises"], 20)
    def test_02_eight_sources_not_eight_certifications(self):
        c, p = inputs()
        self.assertEqual(m.analyser(c,p)["sources_officielles_candidatures"], 8)
        self.assertEqual(m.analyser(c,p)["sources_avec_extraction_certifiee"], 0)
    def test_03_no_go(self):
        c, p = inputs()
        r = m.analyser(c,p)
        self.assertEqual(r["decision"], "NO_GO_AUTOMATIQUE")
        self.assertFalse(r["publication_autorisee"])
    def test_04_budget_levels_separate(self):
        c, p = inputs()
        self.assertEqual(m.analyser(c,p)["perimetres_budgetaires_concilies"],0)
    def test_05_license_not_obtained(self):
        c, p = inputs()
        self.assertFalse(m.analyser(c,p)["licence_microsimulation_obtenue"])
    def test_06_unsupported_web_host_rejected(self):
        c, p = inputs()
        c["sources"][0]["url"] = "https://example.org/mensonge"
        with self.assertRaises(ValueError): m.analyser(c,p)
    def test_07_http_source_rejected(self):
        c, p = inputs()
        c["sources"][0]["url"] = "http://www.finances.gouv.qc.ca/faux"
        with self.assertRaises(ValueError): m.analyser(c,p)
    def test_08_unknown_evidence_link_rejected(self):
        c, p = inputs()
        c["plan_preuves"][0]["source_ids_candidats"]=["S99"]
        with self.assertRaises(ValueError): m.analyser(c,p)
    def test_09_changed_evidence_theme_rejected(self):
        c, p = inputs()
        c["plan_preuves"][0]["theme"]="changement malveillant"
        with self.assertRaises(ValueError): m.analyser(c,p)
    def test_10_fake_attestation_rejected(self):
        c, p = inputs()
        c["plan_preuves"][0]["statut"]="VALIDE"
        with self.assertRaises(ValueError): m.analyser(c,p)
    def test_11_certification_by_page_rejected(self):
        c, p = inputs()
        c["sources"][0]["preuve_validee"]=True
        with self.assertRaises(ValueError): m.analyser(c,p)
    def test_12_fake_representative_dataset_rejected(self):
        c, p = inputs()
        c["representativite"]["echantillon_quebec_calibre"]=True
        with self.assertRaises(ValueError): m.analyser(c,p)
    def test_13_fake_municipal_consolidation_rejected(self):
        c, p = inputs()
        c["perimetres_budgetaires"][2]["conciliation"]="FAITE"
        with self.assertRaises(ValueError): m.analyser(c,p)
    def test_14_outputs_exclude_source_urls_and_microdata(self):
        c, p = inputs()
        c["sources"][0]["usage"]="SECRET_NE_PAS_RESTITUER_P52I"
        x=json.dumps(m.analyser(c,p), ensure_ascii=False)
        self.assertNotIn("SECRET_NE_PAS_RESTITUER_P52I",x)
        self.assertNotIn("https://",x)
        self.assertNotIn("plan_preuves",x)
    def test_15_cli_observation_is_not_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"result.json"
            self.assertEqual(m.main(["--rapport",str(file)]),0)
            self.assertEqual(json.loads(file.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_16_cli_strict_requires_missing_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(m.main(["--exiger-preuves","--rapport",str(Path(tmp)/"x.json")]),3)
    def test_17_cli_bad_source_is_failure_with_no_go(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"result.json"
            self.assertEqual(m.main(["--catalogue",str(Path(tmp)/"missing"),
                                     "--rapport",str(file)]),2)
            self.assertEqual(json.loads(file.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_18_duplicate_source_ids_rejected(self):
        c, p=inputs()
        c["sources"][1]["id"]="S01"
        with self.assertRaises(ValueError): m.analyser(c,p)

if __name__=="__main__":
    unittest.main()
