"""P52K: trente controles adversariaux sur provenance et reçus SHA256 locaux."""
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"controler_provenance_budget_nova_p52k.py"
spec=importlib.util.spec_from_file_location("p52k",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
FAKE=b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\ntrailer <<>>\n%%EOF\n"

def inputs():
    return {k:m.json_read(p) for k,p in m.FILES.items()}

class ProvenanceP52K(unittest.TestCase):
    def test_01_two_sources(self):
        self.assertEqual(m.verifier_registre(inputs())["sources_pdf_officielles_referencees"],2)
    def test_02_zero_hashes_are_unambiguous(self):
        self.assertEqual(m.verifier_registre(inputs())["empreintes_d_originaux_enregistrees_dans_le_registre"],0)
    def test_03_no_independent_attestation(self):
        self.assertFalse(m.verifier_registre(inputs())["attestation_budget_independante"])
    def test_04_twenty_missing_proofs(self):
        self.assertEqual(m.verifier_registre(inputs())["preuves_P52A_independantes_manquantes"],20)
    def test_05_f09_and_f20_not_validated(self):
        self.assertEqual(m.verifier_registre(inputs())["avis_F09_et_F20_manquants"],2)
    def test_06_default_decision_is_no_go(self):
        self.assertEqual(m.verifier_registre(inputs())["decision"],"NO_GO_AUTOMATIQUE")
    def test_07_new_source_url_rejected(self):
        d=inputs();d["registre"]["fichiers_source"][0]["url"]="https://fake.org/doc.pdf"
        with self.assertRaises(ValueError):m.verifier_registre(d)
    def test_08_page_tampering_rejected(self):
        d=inputs();d["registre"]["fichiers_source"][1]["page_pdf_index_zero"]=3
        with self.assertRaises(ValueError):m.verifier_registre(d)
    def test_09_fictitious_sha_rejected(self):
        d=inputs();d["registre"]["fichiers_source"][0]["empreinte_sha256_pdf_original"]="0"*64
        with self.assertRaises(ValueError):m.verifier_registre(d)
    def test_10_fictitious_archive_rejected(self):
        d=inputs();d["registre"]["fichiers_source"][0]["archive_integrite_verifiee"]=True
        with self.assertRaises(ValueError):m.verifier_registre(d)
    def test_11_fictitious_reviewer_rejected(self):
        d=inputs();d["registre"]["preuves_juridiques"][0]["expert_independant_mandate"]=True
        with self.assertRaises(ValueError):m.verifier_registre(d)
    def test_12_fictitious_privacy_review_rejected(self):
        d=inputs();d["registre"]["preuves_juridiques"][1]["analyse_vie_privee_externe"]=True
        with self.assertRaises(ValueError):m.verifier_registre(d)
    def test_13_fictitious_go_rejected(self):
        d=inputs();d["registre"]["fusion_autorisee"]=True
        with self.assertRaises(ValueError):m.verifier_registre(d)
    def test_14_fictitious_archive_certificate_rejected(self):
        d=inputs();d["registre"]["fichiers_source"][0]["certificat_horodatage_independant"]="FAUX"
        with self.assertRaises(ValueError):m.verifier_registre(d)
    def test_15_p52j_source_corruption_rejected(self):
        d=inputs();d["relecture"]["source_primaires"][0]["id"]="FAUX"
        with self.assertRaises(ValueError):m.verifier_registre(d)
    def test_16_f09_p52a_not_validated(self):
        d=inputs();d["preuves"]["required_evidence"][8]["statut"]="VALIDE"
        with self.assertRaises(ValueError):m.verifier_registre(d)
    def test_17_p52i_not_certified(self):
        d=inputs();d["pistes"]["donnees_extraites_certifiees"]=True
        with self.assertRaises(ValueError):m.verifier_registre(d)
    def test_18_whitelisted_aggregate_without_source_paths(self):
        d=inputs()
        d["registre"]["objet"]="SECRET_PRIVÉ_1234"
        result=json.dumps(m.verifier_registre(d),ensure_ascii=False)
        self.assertNotIn("SECRET_PRIVÉ_1234",result)
        self.assertNotIn("https://",result)
    def test_19_cli_audit_runs_zero_but_no_go(self):
        with tempfile.TemporaryDirectory() as p:
            dst=Path(p)/"rapport.json"
            self.assertEqual(m.main(["audit","--rapport",str(dst)]),0)
            self.assertEqual(json.loads(dst.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_20_cli_strict_returns_three(self):
        with tempfile.TemporaryDirectory() as p:
            self.assertEqual(m.main(["audit","--exiger-attestation",
                                       "--rapport",str(Path(p)/"rapport.json")]),3)
    def test_21_cli_missing_input_fails(self):
        with tempfile.TemporaryDirectory() as p:
            self.assertEqual(m.main(["audit","--registre",str(Path(p)/"none")]),2)
    def test_22_pdf_hash_matches_bytes(self):
        with tempfile.TemporaryDirectory() as p:
            path=Path(p)/"sample.pdf";path.write_bytes(FAKE)
            sz,sha=m.empreinte_pdf(path)
            self.assertEqual(sz,len(FAKE))
            self.assertEqual(sha,hashlib.sha256(FAKE).hexdigest())
    def test_23_generated_receipt_stays_uncertified(self):
        with tempfile.TemporaryDirectory() as p:
            path=Path(p)/"sample.pdf";path.write_bytes(FAKE)
            r=m.recu_local(inputs()["registre"],"DISC2026_T3",path,
                           datetime(2026,10,19,tzinfo=timezone.utc))
            self.assertFalse(r["preuve_origine_officielle_etablie"])
            self.assertFalse(r["fusion_autorisee"])
            self.assertNotIn(str(path),json.dumps(r))
    def test_24_local_receipt_verifies_without_go(self):
        with tempfile.TemporaryDirectory() as p:
            path=Path(p)/"sample.pdf";path.write_bytes(FAKE)
            reg=inputs()["registre"]
            r=m.recu_local(reg,"DISC2026_T3",path)
            out=m.verifier_recu(r,reg,"DISC2026_T3",path)
            self.assertEqual(out["integrite_octets_locale"],"CONCORDANTE")
            self.assertFalse(out["authenticite_officielle_certifiee"])
    def test_25_pdf_mutated_after_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as p:
            path=Path(p)/"sample.pdf";path.write_bytes(FAKE)
            reg=inputs()["registre"]
            r=m.recu_local(reg,"DISC2026_T3",path)
            path.write_bytes(FAKE+b"extra")
            with self.assertRaises(ValueError):m.verifier_recu(r,reg,"DISC2026_T3",path)
    def test_26_forged_hash_rejected(self):
        with tempfile.TemporaryDirectory() as p:
            path=Path(p)/"sample.pdf";path.write_bytes(FAKE)
            reg=inputs()["registre"]
            r=m.recu_local(reg,"DISC2026_T3",path)
            r["sha256_octets"]="0"*64
            with self.assertRaises(ValueError):m.verifier_recu(r,reg,"DISC2026_T3",path)
    def test_27_wrong_source_id_rejected(self):
        with tempfile.TemporaryDirectory() as p:
            path=Path(p)/"sample.pdf";path.write_bytes(FAKE)
            with self.assertRaises(ValueError):
                m.recu_local(inputs()["registre"],"INVALID",path)
    def test_28_not_a_pdf_rejected(self):
        with tempfile.TemporaryDirectory() as p:
            path=Path(p)/"sample.pdf";path.write_bytes(b"NOT PDF DOCUMENT CONTENT")
            with self.assertRaises(ValueError):m.empreinte_pdf(path)
    def test_29_symlink_pdf_rejected(self):
        with tempfile.TemporaryDirectory() as p:
            base=Path(p)/"original.pdf";base.write_bytes(FAKE)
            link=Path(p)/"linked.pdf";link.symlink_to(base)
            with self.assertRaises(ValueError):m.empreinte_pdf(link)
    def test_30_receipts_are_never_overwritten(self):
        with tempfile.TemporaryDirectory() as p:
            path=Path(p)/"recu.json"
            m.ecrire_json_non_ecrasant(path,{"a":1})
            with self.assertRaises(FileExistsError):
                m.ecrire_json_non_ecrasant(path,{"a":2})
            self.assertEqual(json.loads(path.read_text()),{"a":1})
if __name__=="__main__":
    unittest.main()
