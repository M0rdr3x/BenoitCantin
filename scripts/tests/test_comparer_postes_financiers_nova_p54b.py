#!/usr/bin/env python3
"""P54B : tests offline, sans données financières véritables."""
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from pypdf import PdfWriter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import comparer_postes_financiers_nova_p54b as m

def pdf_synthetic():
    writer=PdfWriter()
    writer.add_blank_page(width=612,height=792)
    stream=BytesIO()
    writer.write(stream)
    return stream.getvalue()

def fake_capture(source):
    content=b"FAUX_VILLE" if source=="ville" else b"FAUX_MAMH"
    return content,{
      "source_id":source,
      "sha256_fichier_copie_publique":sha256(content).hexdigest(),
      "taille_octets":len(content),
    }

def test_hashes():
    return {src:("fixture",len(fake_capture(src)[0]),
                 sha256(fake_capture(src)[0]).hexdigest(),1,0)
            for src in ("ville","mamh")}

def sample_tokens(rows):
    return (
      {x["index_pdf_ville"]:Counter({"2024":1,"1000":2,"850":1}) for x in rows},
      {x["index_pdf_mamh"]:Counter({"2024":1,"1000":1,"900":1}) for x in rows},
    )

class TestsP54B(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.source=m.config()
        cls.rows=m.matrix(cls.source)

    def test_01_source_year(self):self.assertEqual(self.cfg["exercice_source"],2024)
    def test_02_12_pairs(self):self.assertEqual(len(self.rows),12)
    def test_03_8_gates(self):self.assertEqual(len(m.GATES),8)
    def test_04_96_positions(self):self.assertEqual(sum(len(x["controles"]) for x in self.rows),96)
    def test_05_p54a_provenance(self):self.assertEqual(self.cfg["sources_p54a"]["run_id"],40116065853)
    def test_06_sha_anchor(self):
        self.assertEqual(self.cfg["sources_p54a"]["copies_sha256"]["ville"],m.p54a.COPIES["ville"][2])
    def test_07_gates_uninvestigated(self):
        self.assertTrue(all(y["statut"]=="NON_INSTRUIT" for x in self.rows for y in x["controles"]))
    def test_08_no_independent_check(self):
        self.assertTrue(all(not y["validation_independante"] for x in self.rows for y in x["controles"]))
    def test_09_no_amounts(self):
        self.assertTrue(all(x["jetons"] is None for x in self.rows))
    def test_10_no_economy(self):
        self.assertTrue(all(x["economie_certifiee_cad"] is None for x in self.rows))
    def test_11_no_go(self):self.assertTrue(all(x["decision"]==m.NO_GO for x in self.rows))
    def test_12_unique_pair(self):
        self.assertEqual(len({(x["index_pdf_ville"],x["index_pdf_mamh"]) for x in self.rows}),12)
    def test_13_audit_gate(self):self.assertIn("STATUT_AUDITE_VS_NON_AUDITE",m.GATES)
    def test_14_service_gate(self):self.assertIn("TRAVAIL_SERVICES_TIERS_ET_COUTS_COMPLETS",m.GATES)
    def test_15_thousands(self):self.assertEqual(m.tokens("Total 1 234 cad")["1234"],1)
    def test_16_narrow_thousands(self):self.assertEqual(m.tokens("Total 1\u202f234 567")["1234567"],1)
    def test_17_year(self):self.assertEqual(m.tokens("Exercice 2024")["2024"],1)
    def test_18_negative(self):self.assertEqual(m.tokens("Valeur -100")["-100"],1)
    def test_19_parentheses(self):self.assertEqual(m.tokens("(320)")["320"],1)
    def test_20_nonnumeric(self):self.assertEqual(m.tokens("Aucune somme"),Counter())
    def test_21_repeat(self):self.assertEqual(m.tokens("2024 2024")["2024"],2)
    def test_22_equal_token_overlap(self):
        self.assertEqual(m.scores(Counter({"10":2}),Counter({"10":2}))["recouvrement_dice"],1)
    def test_23_zero_overlap(self):
        self.assertEqual(m.scores(Counter({"10":1}),Counter({"20":1}))["recouvrement_dice"],0)
    def test_24_unknown_empty(self):self.assertIsNone(m.scores(Counter(),Counter())["recouvrement_dice"])
    def test_25_minimum_multiset(self):
        self.assertEqual(m.scores(Counter({"10":3}),Counter({"10":1}))["occurrences_lexicales_communes"],1)
    def test_26_not_a_monetary_value(self):
        self.assertEqual(m.scores(Counter(),Counter())["statut"],"RECOUVREMENT_LEXICAL_NON_MONETAIRE")
    def test_27_no_raw_digits_in_report(self):
        r=m.scores(Counter({"987654":1}),Counter({"987654":1}))
        self.assertNotIn("987654",json.dumps(r))
    def test_28_blank_pdf_page(self):
        self.assertEqual(m.page_tokens(pdf_synthetic(),{0})[0],Counter())
    def test_29_invalid_pdf_index(self):
        with self.assertRaises(ValueError):m.page_tokens(pdf_synthetic(),{1})
    def test_30_baseline_not_attempted(self):
        s=m.summary({"comparaison_possible":False,"sources":{},"lignes":self.rows,"statut":"NON_TENTE"})
        self.assertFalse(s["comparaison_lexicale_des_nombres_executee"])
    def test_31_baseline_12_96(self):
        s=m.summary({"comparaison_possible":False,"sources":{},"lignes":self.rows,"statut":"NON_TENTE"})
        self.assertEqual((s["paires_p54a_cibles"],s["controles_comptables_requis"]),(12,96))
    def test_32_baseline_unknown_numeric(self):
        s=m.summary({"comparaison_possible":False,"sources":{},"lignes":self.rows,"statut":"NON_TENTE"})
        self.assertIsNone(s["pages"]["14:173"])
    def test_33_baseline_no_certification(self):
        s=m.summary({"comparaison_possible":False,"sources":{},"lignes":self.rows,"statut":"NON_TENTE"})
        self.assertEqual(s["concordances_comptables_certifiees"],0)
        self.assertIsNone(s["economies_certifiees_cad"])
    def test_34_reject_false_reported_hash(self):
        def forged(src):
            raw,meta=fake_capture(src)
            meta["sha256_fichier_copie_publique"]=m.p54a.COPIES[src][2]
            meta["taille_octets"]=m.p54a.COPIES[src][1]
            return raw,meta
        self.assertFalse(m.actualize(m.matrix(self.source),forged)["comparaison_possible"])
    def test_35_changed_source_denied(self):
        self.assertFalse(m.actualize(m.matrix(self.source),fake_capture)["comparaison_possible"])
    def test_36_missing_file_denied(self):
        def source(src):
            if src=="mamh":raise ValueError("unavailable")
            return fake_capture(src)
        result=m.actualize(m.matrix(self.source),source)
        self.assertFalse(result["comparaison_possible"])
        self.assertFalse(result["sources"]["mamh"]["capture_reussie"])
    def test_37_synthetic_pair_measurement(self):
        with patch.object(m.p54a,"COPIES",test_hashes()):
            with patch.object(m,"page_tokens",side_effect=sample_tokens(self.rows)):
                result=m.actualize(m.matrix(self.source),fake_capture)
        self.assertTrue(result["comparaison_possible"])
        self.assertEqual(result["lignes"][0]["jetons"]["occurrences_lexicales_communes"],2)
    def test_38_synthetic_pair_cannot_certify_money(self):
        with patch.object(m.p54a,"COPIES",test_hashes()):
            with patch.object(m,"page_tokens",side_effect=sample_tokens(self.rows)):
                r=m.actualize(m.matrix(self.source),fake_capture)
        self.assertEqual(m.summary(r)["concordances_comptables_certifiees"],0)
        self.assertIsNone(m.summary(r)["economies_certifiees_cad"])
    def test_39_synthetic_keeps_all_gates_pending(self):
        with patch.object(m.p54a,"COPIES",test_hashes()):
            with patch.object(m,"page_tokens",side_effect=sample_tokens(self.rows)):
                r=m.actualize(m.matrix(self.source),fake_capture)
        self.assertTrue(all(z["statut"]=="NON_INSTRUIT" for x in r["lignes"] for z in x["controles"]))
    def test_40_cli_writes_neutral(self):
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/"b.json",Path(folder)/"m.json"
            self.assertEqual(m.main(["--bilan",str(a),"--matrice",str(b)]),0)
            self.assertEqual(len(json.loads(b.read_text("utf-8"))["lignes"]),12)
    def test_41_cli_denies_fake_certification(self):
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/"b.json"
            self.assertEqual(m.main(["--bilan",str(a),"--exiger-concordance-comptable"]),3)
    def test_42_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"b.json";p.write_text("original","utf-8")
            self.assertEqual(m.main(["--bilan",str(p)]),2)
            self.assertEqual(p.read_text("utf-8"),"original")
    def test_43_cli_no_same_output(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"b.json"
            self.assertEqual(m.main(["--bilan",str(p),"--matrice",str(p)]),2)
    def test_44_observation_not_transaction(self):
        self.assertEqual(self.cfg["etat_initial"]["montants_comparables_certifies"],0)
    def test_45_no_merge(self):self.assertTrue(self.cfg["limitations"]["aucune_fusion_main"])
    def test_46_no_2026_fiscal_comparison(self):
        self.assertTrue(self.cfg["limitations"]["scenario_quebec_canada_separe_independance"])
    def test_47_skips_numeric_if_no_hash(self):
        r=m.actualize(m.matrix(self.source),fake_capture)
        self.assertTrue(all(x["jetons"] is None for x in r["lignes"]))
    def test_48_dice_is_bounded(self):
        r=m.scores(Counter({"100":4}),Counter({"100":2}))
        self.assertLessEqual(r["recouvrement_dice"],1)

def make_guard_test(flag):
    def case(self):
        self.assertTrue(self.cfg["limitations"][flag])
    return case

for i,flag in enumerate(sorted(m.FLAGS)[:8],49):
    setattr(TestsP54B,"test_%02d_protection"%i,make_guard_test(flag))

if __name__=="__main__":
    unittest.main()
