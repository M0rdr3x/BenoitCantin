"""P50N — scénarios artificiels; aucune fusion, écriture publique ni donnée privée."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts/verify_nova_cross_pr_p50n.py"
spec = importlib.util.spec_from_file_location("nova_p50n", MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TestP50N(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.trees = {ref:self.root/ref for ref in m.REFS}
        base = {
            "participer.html":"Soutien: formulaire intégré de soutien et de préadhésion",
            "avis-legal.html":"Les formulaires servent uniquement à communiquer avec le Projet Nova",
            "code-conduite.html":"Gouvernance du Parti Nova",
        }
        corrected = {
            "participer.html":(
                '<html><body>contact volontaire, formulaires externes suspendus '
                '<a href="recrutement.html">Participer</a>'
                '<a href="confidentialite.html">Confidentialité</a></body></html>'),
            "avis-legal.html":"<html><body>Le site n’exploite actuellement pas de formulaire externe.</body></html>",
            "code-conduite.html":"<html><head><title>Gouvernance du Projet Nova</title></head><body>Projet non adopté</body></html>",
        }
        for ref, tree in self.trees.items():
            site = tree/m.ROOT_REL
            site.mkdir(parents=True)
            for name in m.PAGES:
                value = base[name]
                if ref in ("pr636", "pr640") and name in ("participer.html", "avis-legal.html"):
                    value=corrected[name]
                if ref in ("pr638", "pr640") and name=="code-conduite.html":
                    value=corrected[name]
                (site/name).write_text(value,encoding="utf-8")
            (site/"official/reference").mkdir(parents=True)
            (site/"data").mkdir(parents=True)
            statuts="Statuts non adoptés du Projet Nova\n"
            (site/"official/reference/statuts.md").write_text(statuts,encoding="utf-8")
            digest=hashlib.sha256(statuts.encode("utf-8")).hexdigest()
            cfg={"documents":{"statuts":{"parts":[{"path":"official/reference/statuts.md","sha256":digest}]}}}
            (site/"data/sources.json").write_text(json.dumps(cfg),encoding="utf-8")
        self.manifest = {
            "schema_version":"P50N-1.0",
            "refs":{ref:"a"*40 for ref in m.REFS},
            "garde_fous":{
                "fusionner_pr640":False,"etat_publication":"NO_GO",
                "revues_humaines_obtenues":False,"habilitations_prouvees":False,
                "mise_en_ligne_verifiee":False,
            },
            "fichiers":{
                name:{ref:m.git_blob_sha((tree/m.ROOT_REL/name).read_bytes())
                      for ref,tree in self.trees.items()} for name in m.PAGES
            }
        }
    def tearDown(self):
        self.tmp.cleanup()
    def check(self, manifest=None):
        return m.evaluate(copy.deepcopy(self.manifest if manifest is None else manifest),self.trees)
    def assert_fails(self, code):
        r=self.check()
        self.assertIn(code,r["ecarts"])
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")

    def test_base_snapshot_compatible_but_never_go(self):
        r=self.check()
        self.assertEqual(r["resultat_technique"],"COHERENCE_SNAPSHOT_VERIFIEE")
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
        self.assertFalse(r["revue_humaine_effectuee"])
        self.assertFalse(r["controle_http_production_effectue"])

    def test_sha_git_blob_matches_reference_format(self):
        payload=b"hello\n"
        self.assertEqual(m.git_blob_sha(payload),"ce013625030ba8dba906f756967f9e9ca394464a")

    def test_missing_page_blocked(self):
        (self.trees["pr636"]/m.ROOT_REL/"participer.html").unlink()
        self.assert_fails("PAGE_NON_LISIBLE_pr636_participer.html")

    def test_modified_page_detected_by_exact_blob(self):
        page=self.trees["pr636"]/m.ROOT_REL/"participer.html"
        page.write_text(page.read_text()+"X",encoding="utf-8")
        self.assert_fails("BLOB_INATTENDU_pr636_participer.html")

    def test_unexpected_overlap_on_participation(self):
        page=self.trees["pr638"]/m.ROOT_REL/"participer.html"
        page.write_text("PR638 changed the page",encoding="utf-8")
        self.assert_fails("CHEVAUCHEMENT_PR638_participer.html")

    def test_unexpected_overlap_on_governance(self):
        page=self.trees["pr636"]/m.ROOT_REL/"code-conduite.html"
        page.write_text("PR636 changed the page",encoding="utf-8")
        self.assert_fails("CHEVAUCHEMENT_PR636_code-conduite.html")

    def test_integration_not_equal_pr636(self):
        page=self.trees["pr640"]/m.ROOT_REL/"avis-legal.html"
        page.write_text(page.read_text()+"X",encoding="utf-8")
        self.assert_fails("INTEGRATION_DIVERGENTE_PR636_avis-legal.html")

    def test_integration_not_equal_pr638(self):
        page=self.trees["pr640"]/m.ROOT_REL/"code-conduite.html"
        page.write_text(page.read_text()+"X",encoding="utf-8")
        self.assert_fails("INTEGRATION_DIVERGENTE_PR638_code-conduite.html")

    def test_obsolete_legacy_claim_detected(self):
        page=self.trees["pr636"]/m.ROOT_REL/"participer.html"
        page.write_text(page.read_text()+" formulaire intégré de soutien et de préadhésion",encoding="utf-8")
        self.assert_fails("ANCIENNE_FORMULATION_participer.html")

    def test_active_form_detected(self):
        page=self.trees["pr636"]/m.ROOT_REL/"participer.html"
        page.write_text(page.read_text()+"<form action='/upload'></form>",encoding="utf-8")
        self.assert_fails("COLLECTE_OU_PAIEMENT_DANS_PAGE_participer.html")

    def test_embedded_external_form_detected(self):
        page=self.trees["pr636"]/m.ROOT_REL/"participer.html"
        page.write_text(page.read_text()+'<iframe src="https://formspree.io/f/example"></iframe>',encoding="utf-8")
        self.assert_fails("COLLECTE_OU_PAIEMENT_DANS_PAGE_participer.html")

    def test_payment_script_detected(self):
        page=self.trees["pr638"]/m.ROOT_REL/"code-conduite.html"
        page.write_text(page.read_text()+"<script>const u='https://checkout.stripe.com/q'</script>",encoding="utf-8")
        self.assert_fails("COLLECTE_OU_PAIEMENT_DANS_PAGE_code-conduite.html")

    def test_required_links_missing(self):
        page=self.trees["pr636"]/m.ROOT_REL/"participer.html"
        page.write_text("contact volontaire, formulaires externes suspendus",encoding="utf-8")
        self.assert_fails("LIENS_PARTICIPATION_MANQUANTS")

    def test_statuts_manifest_digest_corrupted(self):
        page=self.trees["pr638"]/m.ROOT_REL/"official/reference/statuts.md"
        page.write_text(page.read_text()+"signed?",encoding="utf-8")
        self.assert_fails("MANIFESTE_STATUTS_SHA256_pr638")

    def test_statuts_manifest_path_wrong(self):
        path=self.trees["pr640"]/m.ROOT_REL/"data/sources.json"
        obj=json.loads(path.read_text())
        obj["documents"]["statuts"]["parts"][0]["path"]="incorrect.md"
        path.write_text(json.dumps(obj))
        self.assert_fails("MANIFESTE_STATUTS_CHEMIN_pr640")

    def test_never_fuse_640_guard(self):
        self.manifest["garde_fous"]["fusionner_pr640"]=True
        self.assert_fails("VERROUS_INSTITUTIONNELS_MODIFIES")

    def test_no_go_even_on_invalid_schema(self):
        r=m.evaluate({"schema_version":"wrong"},self.trees)
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")

if __name__ == "__main__":
    unittest.main()
