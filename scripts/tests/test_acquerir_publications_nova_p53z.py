#!/usr/bin/env python3
"""P53Z: accès simulés pour vérifier la sécurité du collecteur."""
from email.message import Message
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import URLError
from pypdf import PdfWriter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import acquerir_publications_nova_p53z as m

def make_pdf():
    writer=PdfWriter()
    writer.add_blank_page(width=612,height=792)
    writer.add_blank_page(width=612,height=792)
    stream=BytesIO()
    writer.write(stream)
    return stream.getvalue()

PDF=make_pdf()

class Response:
    def __init__(self,content,url,mime="application/pdf",length=None):
        self.buffer=BytesIO(content)
        self.url=url
        self.headers=Message()
        self.headers["Content-Type"]=mime
        if length is not None:self.headers["Content-Length"]=str(length)
    def __enter__(self):return self
    def __exit__(self,*unused):self.buffer.close()
    def read(self,n=-1):return self.buffer.read(n)
    def geturl(self):return self.url
    def info(self):return self.headers

def opener_for(flags):
    def opener(url,source):
        flag=flags.get(source,"OK")
        if flag=="TIMEOUT":raise TimeoutError("synthetic")
        if flag=="NETWORK":raise URLError("synthetic")
        if flag=="REJECT":raise ValueError("synthetic")
        if flag=="HTML":return Response(b"<html>fake</html>",url,"text/html")
        if flag=="BODY":return Response(b"not pdf",url)
        if flag=="REDIRECT":return Response(PDF,"https://bad.example/test.pdf")
        if flag=="TOO_BIG":return Response(PDF,url,length=m.MAX+1)
        if flag=="BAD_LENGTH":return Response(PDF,url,length="not-a-number")
        if flag=="TRUNCATED":return Response(PDF[:-10],url)
        return Response(PDF,url,length=len(PDF))
    return opener

class TestP53Z(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.config()
    def test_01_schema(self):self.assertEqual(self.cfg["schema_version"],"P53Z-1")
    def test_02_year(self):self.assertEqual(self.cfg["exercice"],2024)
    def test_03_two_sources(self):self.assertEqual(len(m.SOURCE),2)
    def test_04_ville_domain(self):self.assertIn("ville.quebec",m.SOURCE["ville"])
    def test_05_mamh_domain(self):self.assertIn("mamh.gouv",m.SOURCE["mamh"])
    def test_06_exact_pdf_limits(self):self.assertEqual(self.cfg["plafonds"]["octets_par_pdf"],m.MAX)
    def test_07_timeout(self):self.assertEqual(self.cfg["plafonds"]["secondes_par_source"],25)
    def test_08_originals_not_in_git(self):self.assertTrue(self.cfg["gardes"]["aucune_piece_originale_dans_git"])
    def test_09_no_jobs_reduced(self):self.assertTrue(self.cfg["gardes"]["emplois_et_services_maintenus"])
    def test_10_scope(self):self.assertEqual(self.cfg["organismes"],["23027","T0088"])
    def test_11_baseline_no_hash(self):self.assertIsNone(self.cfg["etat_initial"]["equivalences_pdf_constatees"])
    def test_12_baseline_no_cert(self):self.assertIsNone(self.cfg["etat_initial"]["economies_certifiees_cad"])
    def test_13_url_ville_ok(self):self.assertEqual(m.safe_url(m.SOURCE["ville"],"ville"),m.SOURCE["ville"])
    def test_14_url_mamh_ok(self):self.assertEqual(m.safe_url(m.SOURCE["mamh"],"mamh"),m.SOURCE["mamh"])
    def test_15_copy_downloaded(self):self.assertEqual(m.capture("ville",opener_for({}))[0],PDF)
    def test_16_sha_real(self):
        data,obs=m.capture("mamh",opener_for({}))
        self.assertEqual(obs["sha256_fichier_copie_publique"],hashlib.sha256(data).hexdigest())
    def test_17_validates_byte_count(self):self.assertEqual(m.capture("ville",opener_for({}))[1]["taille_octets"],len(PDF))
    def test_18_no_auth_claim(self):self.assertFalse(m.capture("ville",opener_for({}))[1]["identite_emetteur_certifiee"])
    def test_19_empty_aggregate(self):self.assertEqual(m.aggregate({})["copies_https_observees"],0)
    def test_20_no_hash_if_absent(self):self.assertIsNone(m.aggregate({})["observations"]["ville"]["sha256_fichier_copie_publique"])
    def test_21_offline_no_comparison(self):self.assertFalse(m.aggregate({})["comparaison_octets_officiels_effectuee"])
    def test_22_mocked_two_acquisitions(self):self.assertEqual(m.fetch_all(opener_for({}))["copies_https_observees"],2)
    def test_23_mocked_comparison(self):self.assertTrue(m.fetch_all(opener_for({}))["comparaison_octets_officiels_effectuee"])
    def test_24_mocked_identical(self):self.assertTrue(m.fetch_all(opener_for({}))["comparaison"]["octets_strictement_identiques"])
    def test_25_mocked_page_count(self):self.assertEqual(m.fetch_all(opener_for({}))["observations"]["ville"]["pages_extraites"],2)
    def test_26_mocked_no_cert(self):self.assertFalse(m.fetch_all(opener_for({}))["preuve_authenticite_emetteur"])
    def test_27_mocked_no_savings(self):self.assertIsNone(m.fetch_all(opener_for({}))["economies_certifiees_cad"])
    def test_28_one_fails(self):self.assertEqual(m.fetch_all(opener_for({"ville":"TIMEOUT"}))["copies_https_observees"],1)
    def test_29_one_fails_no_comparison(self):self.assertFalse(m.fetch_all(opener_for({"ville":"TIMEOUT"}))["comparaison_octets_officiels_effectuee"])
    def test_30_no_pdf_in_output(self):self.assertNotIn("%PDF-",json.dumps(m.fetch_all(opener_for({}))))
    def test_31_cli_neutral(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"rapport.json"
            self.assertEqual(m.main(["--bilan",str(p)]),0)
            self.assertEqual(json.loads(p.read_text("utf-8"))["copies_https_observees"],0)
    def test_32_cli_strict(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.main(["--exiger-authenticite","--bilan",str(Path(d)/"rapport.json")]),3)

def add_bad_url_test(i,url,source):
    def t(self):
        with self.assertRaises(ValueError):m.safe_url(url,source)
    setattr(TestP53Z,"test_%02d_url_refusee"%i,t)

BAD_URLS=[
 ("http://www.ville.quebec.qc.ca/test.pdf","ville"),
 ("https://evil.example/test.pdf","ville"),
 (m.SOURCE["mamh"],"ville"),
 ("https://user:pass@www.mamh.gouv.qc.ca/test.pdf","mamh"),
 (m.SOURCE["ville"]+"?secret=1","ville"),
 (m.SOURCE["ville"]+"#frag","ville"),
 ("https://www.mamh.gouv.qc.ca:8000/test.pdf","mamh"),
 ("ftp://www.ville.quebec.qc.ca/test.pdf","ville"),
 ("https://www.ville.quebec.qc.ca","INVALID"),
 ("https://www.mamh.gouv.qc.ca/test.pdf","ville"),
]
for number,(url,source) in enumerate(BAD_URLS,33):
    add_bad_url_test(number,url,source)

def add_bad_download_test(i,reason):
    def t(self):
        with self.assertRaises((ValueError,TimeoutError,URLError)):
            m.capture("ville",opener_for({"ville":reason}))
    setattr(TestP53Z,"test_%02d_capture_refusee"%i,t)

for number,reason in enumerate(("TIMEOUT","NETWORK","REJECT","HTML",
                                "BODY","REDIRECT","TOO_BIG","BAD_LENGTH","TRUNCATED"),43):
    add_bad_download_test(number,reason)

def last_test(self):
    result=m.fetch_all(opener_for({"mamh":"NETWORK"}))
    self.assertEqual(result["observations"]["mamh"]["erreur"],"RESEAU_OU_HTTP_INDISPONIBLE")
    self.assertEqual(result["decision"],m.NO_GO)

setattr(TestP53Z,"test_52_error_classification",last_test)

if __name__=="__main__":
    unittest.main()
