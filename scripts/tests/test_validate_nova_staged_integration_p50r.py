"""P50R — tests purement locaux du verificateur de staging (aucun git distant)."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SRC=Path(__file__).resolve().parents[1]/"validate_nova_staged_integration_p50r.py"
spec=importlib.util.spec_from_file_location("p50r",SRC)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class P50RTests(unittest.TestCase):
    def test_expected_files_are_fourteen(self):
        self.assertEqual(len(mod.EXPECT),14)

    def test_no_unlisted_file_allowed(self):
        errors=mod.examine_paths(set(mod.EXPECT)|{"projets/projet-nova/formulaire-soutien.html"})
        self.assertIn("DELTA_CHEMINS_NON_CONFORME",errors)

    def test_missing_file_fails_closed(self):
        errors=mod.examine_paths(set(mod.EXPECT)-{"scripts/validate_nova_identity.py"})
        self.assertIn("DELTA_CHEMINS_NON_CONFORME",errors)

    def test_exact_manifest_succeeds(self):
        self.assertEqual(mod.examine_paths(set(mod.EXPECT)),[])

    def test_blob_git_known_value(self):
        self.assertEqual(mod.blob_sha(b"hello\n"),"ce013625030ba8dba906f756967f9e9ca394464a")

    def test_statuts_digest_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"projets/projet-nova"
            (root/"data").mkdir(parents=True)
            (root/"official/reference").mkdir(parents=True)
            payload=b"projet de statuts NON ADOPTE\n"
            (root/"official/reference/statuts.md").write_bytes(payload)
            m={"documents":{"statuts":{"parts":[{
                "path":"official/reference/statuts.md",
                "sha256":hashlib.sha256(payload).hexdigest(),
            }]}}}
            (root/"data/sources.json").write_text(json.dumps(m),encoding="utf-8")
            self.assertEqual(mod.check_statuts(Path(tmp)),[])

    def test_modified_statuts_digest_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"projets/projet-nova"
            (root/"data").mkdir(parents=True)
            (root/"official/reference").mkdir(parents=True)
            (root/"official/reference/statuts.md").write_text("original",encoding="utf-8")
            m={"documents":{"statuts":{"parts":[{
                "path":"official/reference/statuts.md",
                "sha256":hashlib.sha256(b"original").hexdigest(),
            }]}}}
            (root/"data/sources.json").write_text(json.dumps(m),encoding="utf-8")
            (root/"official/reference/statuts.md").write_text("modified",encoding="utf-8")
            self.assertEqual(mod.check_statuts(Path(tmp)),["EMPREINTE_STATUTS_INVALIDE"])

    def test_missing_git_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=mod.inspect(Path(tmp))
            self.assertEqual(r["statut_technique"],"ECHEC_OU_PREUVE_INCOMPLETE")
            self.assertIn("ARBRE_GIT_ABSENT",r["problemes"])

    def test_unexpected_baseline_sha_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=mod.inspect(Path(tmp),base="not-a-sha")
            self.assertIn("SHA_BASE_INVALIDE",r["problemes"])

    def test_a_green_technical_review_is_still_no_go(self):
        result=mod.make_report([], "a"*40,list(mod.EXPECT))
        self.assertEqual(result["statut_technique"],"COHERENCE_SIMULEE")
        self.assertEqual(result["decision"],"NO_GO_AUTOMATIQUE")
        self.assertFalse(result["autorisation_publication"])
        self.assertFalse(result["revue_humaine_obtenue"])

if __name__=="__main__":
    unittest.main()
