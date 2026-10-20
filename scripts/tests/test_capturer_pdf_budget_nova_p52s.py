"""P52S : tests sans réseau pour capture HTTPS limitée et fausses preuves."""
from io import BytesIO
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/"scripts"/"capturer_pdf_budget_nova_p52s.py"
spec=importlib.util.spec_from_file_location("p52s",PATH)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
PDF=b"%PDF-1.7\n"+"hello".encode()*5+b"\n%%EOF\n"
class FakeResponse:
    def __init__(self,buf=PDF,kind="application/pdf",url=None,status=200,declared=None):
        self._bytes=BytesIO(buf)
        self.url=url or m.URLS[0]
        self.status=status
        self.headers={"Content-Type":kind,
                      "Content-Length":str(len(buf)) if declared is None else declared}
    def geturl(self):return self.url
    def read(self,size):return self._bytes.read(size)
    def __enter__(self):return self
    def __exit__(self,*a):self._bytes.close()
class FakeOpener:
    def __init__(self,response=None,raise_error=None):
        self.response=response or FakeResponse()
        self.raise_error=raise_error
    def open(self,req,timeout):
        if self.raise_error:raise self.raise_error
        return self.response

def docs():
    return {k:m.read(v) for k,v in m.FILES.items()}

class SourceReception(unittest.TestCase):
    def reject(self,change):
        d=docs();change(d)
        with self.assertRaises(ValueError):m.validate(d)
    def test_01_schema(self):self.assertEqual(len(m.validate(docs())),2)
    def test_02_default_no_network(self):self.assertEqual(m.run(docs())["tentatives_reseau_effectuees"],0)
    def test_03_default_no_go(self):self.assertEqual(m.run(docs())["decision"],"NO_GO_AUTOMATIQUE")
    def test_04_no_archive(self):self.assertEqual(m.run(docs())["archives_officielles_certifiees"],0)
    def test_05_source_ids(self):self.assertEqual(tuple(x["id"] for x in m.validate(docs())),m.IDS)
    def test_06_hash_null_default(self):
        self.assertTrue(all(x["sha256_octets_recus"] is None for x in m.run(docs())["reçus_techniques"]))
    def test_07_model_approval_rejected(self):
        self.reject(lambda d:d["p52s"]["etat"].update(adoption_autorisee=True))
    def test_08_fake_registry_pdf_hash_rejected(self):
        self.reject(lambda d:d["p52s"]["sources"][0].update(sha256_pdf_officiel_atteste="a"*64))
    def test_09_fake_k_hash_rejected(self):
        self.reject(lambda d:d["p52k"]["fichiers_source"][0].update(empreinte_sha256_pdf_original="b"*64))
    def test_10_fake_j_hash_rejected(self):
        self.reject(lambda d:d["p52j"]["source_primaires"][0].update(empreinte_sha256_pdf="c"*64))
    def test_11_fake_r_hash_rejected(self):
        self.reject(lambda d:d["p52r"]["origine_constats"][0].update(sha256_original="d"*64))
    def test_12_fake_F09_approval_rejected(self):
        self.reject(lambda d:d["p52a"]["required_evidence"][8].update(statut="VALIDE"))
    def test_13_unlisted_url_refused(self):
        with self.assertRaises(ValueError):m.fetch_one("https://other.example.com/test.pdf")
    def test_14_http_refused(self):
        with self.assertRaises(ValueError):m.fetch_one("http://www.finances.gouv.qc.ca/test.pdf")
    def test_15_fake_pdf_received_and_hash(self):
        import hashlib
        r=m.fetch_one(m.URLS[0],FakeOpener())
        self.assertEqual(r["sha256_octets_recus"],hashlib.sha256(PDF).hexdigest())
        self.assertEqual(r["taille_octets"],len(PDF))
        self.assertFalse(r["signature_ministerielle_verifiee"])
    def test_16_invalid_media_type_refused(self):
        with self.assertRaises(ValueError):
            m.fetch_one(m.URLS[0],FakeOpener(FakeResponse(kind="text/html")))
    def test_17_redirect_result_refused(self):
        with self.assertRaises(ValueError):
            m.fetch_one(m.URLS[0],FakeOpener(FakeResponse(url="https://example.com/pdf")))
    def test_18_http_status_refused(self):
        with self.assertRaises(ValueError):
            m.fetch_one(m.URLS[0],FakeOpener(FakeResponse(status=206)))
    def test_19_html_response_refused(self):
        with self.assertRaises(ValueError):
            m.fetch_one(m.URLS[0],FakeOpener(FakeResponse(buf=b"<html>oops</html>",kind="application/pdf")))
    def test_20_truncated_pdf_refused(self):
        with self.assertRaises(ValueError):
            m.fetch_one(m.URLS[0],FakeOpener(FakeResponse(buf=PDF.replace(b"%%EOF",b"end"))))
    def test_21_wrong_declared_length_refused(self):
        with self.assertRaises(ValueError):
            m.fetch_one(m.URLS[0],FakeOpener(FakeResponse(declared="999999999")))
    def test_22_declared_length_non_numeric(self):
        with self.assertRaises(ValueError):
            m.fetch_one(m.URLS[0],FakeOpener(FakeResponse(declared="abc")))
    def test_23_forged_original_statement_rejected(self):
        self.reject(lambda d:d["p52s"]["sources"][0].update(document_archivage_effectue=True))
    def test_24_mistaken_external_signature(self):
        self.reject(lambda d:d["p52s"]["sources"][0].update(signature_editeur_verifiee=True))
    def test_25_wrong_page_number(self):
        self.reject(lambda d:d["p52s"]["sources"][1].update(page_tableau_pdf_zero=276))
    def test_26_missing_manifest_safeguard(self):
        self.reject(lambda d:d["p52s"]["conditions"].update(aucun_pdf_original_conserve_en_artefact=False))
    def test_27_enlarged_download_limit_rejected(self):
        self.reject(lambda d:d["p52s"]["conditions"].update(taille_octets_maximum=999999999))
    def test_28_fake_external_attestation_p52j(self):
        self.reject(lambda d:d["p52j"]["validation_de_nature"].update(preuve_F09_independamment_attestee=True))
    def test_29_network_failure_no_hash(self):
        d=docs()
        out=m.run(d,"sonde",FakeOpener(raise_error=TimeoutError("fake test")))
        self.assertEqual(out["flux_pdf_recus_non_authentifies"],0)
        self.assertEqual(out["sources_non_recuperees"],2)
        self.assertTrue(all(x["sha256_octets_recus"] is None for x in out["reçus_techniques"]))
    def test_30_failure_no_error_message_leaked(self):
        out=m.run(docs(),"sonde",FakeOpener(raise_error=OSError("SENSITIVE USER SECRET")))
        self.assertNotIn("SENSITIVE",json.dumps(out))
    def test_31_successful_simulated_two_sources(self):
        class SourceAwareOpener:
            def open(self,req,timeout):
                return FakeResponse(url=req.full_url)
        out=m.run(docs(),"sonde",SourceAwareOpener())
        self.assertEqual(out["flux_pdf_recus_non_authentifies"],2)
        self.assertEqual(out["archives_officielles_certifiees"],0)
        self.assertFalse(out["adoption_autorisee"])
    def test_32_no_late_sources_p52a(self):
        self.assertEqual(m.run(docs())["preuves_F01_F20_validees"],0)
    def test_33_cli_bilan(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"result.json"
            self.assertEqual(m.main(["--rapport",str(path)]),0)
            self.assertEqual(json.loads(path.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_34_cli_strict_origins_code_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(m.main(["--exiger-originaux","--rapport",str(Path(tmp)/"r.json")]),3)
    def test_35_cli_strict_expertise_code_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(m.main(["--exiger-expertise","--rapport",str(Path(tmp)/"r.json")]),3)
    def test_36_cli_missing_manifest_code_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(m.main(["--p52s",str(Path(tmp)/"missing.json")]),2)
    def test_37_cli_report_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"r.json"
            self.assertEqual(m.main(["--rapport",str(path)]),0)
            self.assertEqual(m.main(["--rapport",str(path)]),2)
    def test_38_no_url_in_aggregate_bilan(self):
        out=json.dumps(m.run(docs()),ensure_ascii=False)
        self.assertNotIn("https://",out)
        self.assertNotIn('"preuve_id":',out)
    def test_39_attempt_timestamp_not_handwritten(self):
        out=m.run(docs(),"sonde",FakeOpener(raise_error=TimeoutError()))
        self.assertTrue(all(x["date_utc_tentative"] for x in out["reçus_techniques"]))
    def test_40_no_pdf_data_in_report(self):
        out=m.run(docs(),"sonde",FakeOpener(raise_error=OSError()))
        self.assertNotIn("%PDF",json.dumps(out))
if __name__=="__main__":
    unittest.main()
