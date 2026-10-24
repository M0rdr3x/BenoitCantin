#!/usr/bin/env python3
"""P53X: comparer des PDFs synthétiques sans réseau, faux audit ou révélation."""
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from pypdf import PdfWriter
from pypdf.generic import NameObject,DictionaryObject,DecodedStreamObject
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import comparer_versions_pdf_nova_p53x as m

def pdf_bytes(*texts):
    w=PdfWriter()
    font=w._add_object(DictionaryObject({
        NameObject("/Type"):NameObject("/Font"),
        NameObject("/Subtype"):NameObject("/Type1"),
        NameObject("/BaseFont"):NameObject("/Helvetica"),
    }))
    for text in texts:
        page=w.add_blank_page(width=612,height=792)
        page[NameObject("/Resources")]=DictionaryObject({
            NameObject("/Font"):DictionaryObject({NameObject("/F1"):font})})
        if text is not None:
            stream=DecodedStreamObject()
            txt="".join(c for c in text if ord(c)<128 and c not in "()\\")
            stream.set_data(("BT /F1 12 Tf 72 720 Td ("+txt+") Tj ET").encode("ascii"))
            page[NameObject("/Contents")]=w._add_object(stream)
    buf=BytesIO();w.write(buf)
    return buf.getvalue()

A="VILLE QUEBEC RAPPORT FINANCIER 2024"
B="RTC ET SOMHAC CONSOLIDATION RECIPROQUE"
C="MAMH DOCUMENT ADDITIONNEL ANNEXE 2024"

class TestP53X(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cfg=m.sources()
    def one(self):return pdf_bytes(A,B)
    def two(self):return pdf_bytes(A,B,C)
    def test_01_setup(self):self.assertEqual(self.cfg["schema_version"],"P53X-1")
    def test_02_year(self):self.assertEqual(self.cfg["exercice_reference"],2024)
    def test_03_two_sources(self):self.assertEqual(len(self.cfg["sources_p53w"]),2)
    def test_04_urls(self):self.assertEqual(self.cfg["sources_p53w"]["mamh"],m.URL_MAMH)
    def test_05_anchors(self):self.assertEqual(self.cfg["controle_pages_ville"],[0,34,196])
    def test_06_limits(self):self.assertEqual(self.cfg["plafonds"]["taille_pdf_octets"],m.SIZE_MAX)
    def test_07_standard_ops(self):self.assertEqual(len(m.OPS),4)
    def test_08_neutral_not_compared(self):self.assertFalse(m.summary(None)["comparaison_pdf_effectuee_localement"])
    def test_09_neutral_hash_unknown(self):self.assertIsNone(m.summary(None)["octets_strictement_identiques"])
    def test_10_neutral_page_unknown(self):self.assertIsNone(m.summary(None)["nombre_pages_mamh_mesure"])
    def test_11_neutral_anchor_unknown(self):self.assertIsNone(m.summary(None)["ancrages_p53w_textuellement_retrouves"]["34"])
    def test_12_neutral_no_go(self):self.assertEqual(m.summary(None)["decision"],m.NO_GO)
    def test_13_normalization_spaces(self):self.assertEqual(m.normalized(" A \n B  "),"a b")
    def test_14_normalization_unicode(self):self.assertEqual(m.normalized("ＣＡＦＥ"),"cafe")
    def test_15_normalization_none(self):self.assertEqual(m.normalized(None),"")
    def test_16_pdf_pages(self):self.assertEqual(m.pdf_pages(self.one())["nombre_pages"],2)
    def test_17_pdf_extracts(self):self.assertEqual(m.pdf_pages(self.one())["pages_avec_texte"],2)
    def test_18_pdf_blank_unknown(self):self.assertEqual(m.pdf_pages(pdf_bytes(None))["pages_sans_texte_exploitable"],1)
    def test_19_same_binary(self):self.assertTrue(m.compare(self.one(),self.one())["octets_strictement_identiques"])
    def test_20_diff_binary(self):self.assertFalse(m.compare(self.one(),self.two())["octets_strictement_identiques"])
    def test_21_same_pagecount(self):self.assertTrue(m.compare(self.one(),self.one())["meme_nombre_pages"])
    def test_22_diff_pagecount(self):self.assertFalse(m.compare(self.one(),self.two())["meme_nombre_pages"])
    def test_23_embedded_document_matching(self):self.assertEqual(m.compare(self.one(),self.two())["pages_textuellement_appariees"],2)
    def test_24_page_index_shift(self):
        result=m.compare(self.one(),pdf_bytes(C,A,B))
        self.assertEqual(result["correspondances_indices"],[[0,1],[1,2]])
    def test_25_partial_text(self):
        result=m.compare(self.one(),pdf_bytes(A,C))
        self.assertEqual(result["textes_ville_non_apparies"],1)
    def test_26_blank_not_match(self):
        result=m.compare(pdf_bytes(None,A),pdf_bytes(None,A))
        self.assertEqual(result["pages_textuellement_appariees"],1)
    def test_27_blank_is_unknown(self):self.assertEqual(m.compare(pdf_bytes(None,A),self.one())["pages_ville_sans_texte_exploitable"],1)
    def test_28_invalid_pdf(self):
        with self.assertRaises(Exception):m.pdf_pages(b"not pdf")
    def test_29_reject_nonbytes(self):
        with self.assertRaises(ValueError):m.compare("pdf",b"x")
    def test_30_no_provenance(self):self.assertFalse(m.compare(self.one(),self.one())["provenance_institutionnelle_authentifiee"])
    def test_31_no_comptability(self):self.assertFalse(m.compare(self.one(),self.one())["audit_comptable_effectue"])
    def test_32_no_saving(self):self.assertIsNone(m.compare(self.one(),self.one())["economie_certifiee_cad"])
    def test_33_no_false_anchor(self):self.assertIsNone(m.compare(self.one(),self.one())["ancrages_p53w_textuellement_retrouves"]["34"])
    def test_34_hash_calculated(self):self.assertEqual(m.compare(self.one(),self.one())["sha256_ville"],hashlib.sha256(self.one()).hexdigest())
    def test_35_no_hash_public(self):
        comparison=m.compare(self.one(),self.two())
        self.assertNotIn(comparison["sha256_ville"],json.dumps(m.summary(comparison)))
    def test_36_no_file_paths_public(self):self.assertNotIn("rapport_ville.pdf",json.dumps(m.summary(m.compare(self.one(),self.two()))))
    def test_37_public_counts(self):self.assertEqual(m.summary(m.compare(self.one(),self.two()))["nombre_pages_mamh_mesure"],3)
    def test_38_no_false_financial_diff(self):self.assertEqual(m.summary(m.compare(self.one(),self.two()))["differends_comptables_demontres"],0)
    def test_39_no_certified_comparison(self):self.assertEqual(m.summary(m.compare(self.one(),self.two()))["comparaisons_certifiees_par_expert"],0)
    def test_40_reject_traversal(self):
        with self.assertRaises(ValueError):m.relative_pdf("../secret.pdf")
    def test_41_reject_absolute(self):
        with self.assertRaises(ValueError):m.relative_pdf("/tmp/secret.pdf")
    def test_42_reject_other_format(self):
        with self.assertRaises(ValueError):m.relative_pdf("image.png")
    def test_43_reject_hidden(self):
        with self.assertRaises(ValueError):m.relative_pdf(".private.pdf")
    def test_44_allow_nested(self):self.assertEqual(str(m.relative_pdf("dossier/ville.pdf")),"dossier/ville.pdf")
    def test_45_reject_file_in_repo(self):
        with self.assertRaises(ValueError):m.evidence_root(m.ROOT)
    def test_46_missing_pdf(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(OSError):m.read_local_pdf(d,"absent.pdf")
    def test_47_reject_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"good.pdf").write_bytes(self.one())
            (p/"link.pdf").symlink_to(p/"good.pdf")
            with self.assertRaises(ValueError):m.read_local_pdf(d,"link.pdf")
    def test_48_read_valid(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/"good.pdf").write_bytes(self.one())
            self.assertEqual(m.read_local_pdf(d,"good.pdf"),self.one())
    def test_49_cli_neutral(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"bilan.json"
            self.assertEqual(m.main(["--bilan",str(f)]),0)
            self.assertIsNone(json.loads(f.read_text("utf-8"))["octets_strictement_identiques"])
    def test_50_cli_reject_missing_pair(self):self.assertEqual(m.main(["--racine","/tmp","--ville","x.pdf"]),2)
    def test_51_cli_requires_access(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/"ville.pdf").write_bytes(self.one())
            (Path(d)/"mamh.pdf").write_bytes(self.two())
            self.assertEqual(m.main(["--racine",d,"--ville","ville.pdf","--mamh","mamh.pdf"]),2)
    def test_52_cli_real_synthetic_pair(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"ville.pdf").write_bytes(self.one())
            (p/"mamh.pdf").write_bytes(self.two())
            f=p/"bilan.json"
            self.assertEqual(m.main(["--racine",d,"--ville","ville.pdf",
                                     "--mamh","mamh.pdf","--confirmer-acces-legal",
                                     "--bilan",str(f)]),0)
            result=json.loads(f.read_text("utf-8"))
            self.assertTrue(result["comparaison_pdf_effectuee_localement"])
            self.assertEqual(result["pages_textuellement_appariees"],2)
    def test_53_private_hash_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"ville.pdf").write_bytes(self.one())
            (p/"mamh.pdf").write_bytes(self.one())
            f=p/"details.json"
            self.assertEqual(m.main(["--racine",d,"--ville","ville.pdf",
                                     "--mamh","mamh.pdf","--confirmer-acces-legal",
                                     "--detail-prive",str(f)]),0)
            self.assertEqual(json.loads(f.read_text("utf-8"))["comparaison"]["sha256_ville"],hashlib.sha256(self.one()).hexdigest())
    def test_54_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"bilan.json";f.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(f)]),2)
            self.assertEqual(f.read_text("utf-8"),"keep")
    def test_55_different_targets(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"bilan.json"
            self.assertEqual(m.main(["--bilan",str(f),"--detail-prive",str(f)]),2)
    def test_56_strict_denies(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"bilan.json"
            self.assertEqual(m.main(["--bilan",str(f),"--exiger-certification"]),3)

if __name__=="__main__":
    unittest.main()
