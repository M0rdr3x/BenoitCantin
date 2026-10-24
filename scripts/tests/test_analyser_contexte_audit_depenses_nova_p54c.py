#!/usr/bin/env python3
"""P54C: tests hors réseau d'un rapport d'audit à portée limitée."""
from hashlib import sha256
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import analyser_contexte_audit_depenses_nova_p54c as m

VILLE=("RAPPORT DES AUDITEURS INDÉPENDANTS. Opinion. Nous avons effectué "
       "l'audit du tableau de la ventilation des dépenses mixtes entre les "
       "compétences de nature locale et les compétences d'agglomération, "
       "pour l'exercice terminé le 31 décembre 2024, conformément au "
       "R.A.V.Q. 1435. Page 103")
MAMH=("Rapport des auditeurs indépendants. Opinion. "
      "Ventilation des dépenses mixtes, compétences de nature locale "
      "et compétences d’agglomération au 31 décembre 2024, R.A.V.Q. 1435. "
      "Page 163, annexe 1")
def fixture_fetch(src):
    blob=b"SYNTHETIQUE_VILLE" if src=="ville" else b"SYNTHETIQUE_MAMH"
    return blob,{
      "source_id":src,"taille_octets":len(blob),
      "sha256_fichier_copie_publique":sha256(blob).hexdigest()
    }
def fixture_refs():
    return {key:("not_date",len(fixture_fetch(key)[0]),
                 sha256(fixture_fetch(key)[0]).hexdigest(),2,0)
            for key in ("ville","mamh")}

class TestsP54C(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c=m.cfg()
    def test_01_source_year(self):self.assertEqual(self.c["exercice"],2024)
    def test_02_page102(self):self.assertEqual(self.c["pair_prioritaire"]["page_index_pdf_ville"],102)
    def test_03_page162(self):self.assertEqual(self.c["pair_prioritaire"]["page_index_pdf_mamh"],162)
    def test_04_7826(self):self.assertEqual(self.c["pair_prioritaire"]["score_dice_p54b"],0.7826)
    def test_05_10_tokens(self):self.assertEqual(self.c["pair_prioritaire"]["jetons_numeriques_ville"],10)
    def test_06_13_tokens(self):self.assertEqual(self.c["pair_prioritaire"]["jetons_numeriques_mamh"],13)
    def test_07_9_overlap(self):self.assertEqual(self.c["pair_prioritaire"]["jetons_numeriques_communs"],9)
    def test_08_eight_gates(self):self.assertEqual(len(m.GATES),8)
    def test_09_all_guards_true(self):self.assertTrue(all(self.c["verrous"].values()))
    def test_10_no_signed_nova_audit(self):self.assertEqual(self.c["etat_initial"]["examen_professionnel_independant_signe"],0)
    def test_11_unknown_economy(self):self.assertIsNone(self.c["etat_initial"]["economies_certifiees_cad"])
    def test_12_limit_audit_document(self):self.assertIn("VENTILATION",self.c["contexte_documente_ville"]["document"])
    def test_13_source_p54b(self):self.assertEqual(self.c["source_p54b_run"],40118178035)
    def test_14_normalize_french(self):self.assertEqual(m.normalize("DÉPENSES   mixtes"),"depenses mixtes")
    def test_15_normalize_unicode_apostrophe(self):
        self.assertTrue(m.indicators(VILLE)["competences_agglomeration"])
    def test_16_all_document_markers_ville(self):
        self.assertTrue(all(m.indicators(VILLE).values()))
    def test_17_all_document_markers_mamh(self):
        self.assertTrue(all(m.indicators(MAMH).values()))
    def test_18_empty_text_unknown(self):
        self.assertEqual(sum(m.indicators("").values()),0)
    def test_19_unrelated_text(self):
        self.assertFalse(m.indicators("Analyse de la charge par catégorie")["rapport_auditeurs"])
    def test_20_same_scope(self):
        self.assertTrue(m.analyze_text(VILLE,MAMH)["sections_se_rapportent_probablement_au_meme_audit"])
    def test_21_different_scope(self):
        self.assertFalse(m.analyze_text(VILLE,"Tableau de calcul sans audit")["sections_se_rapportent_probablement_au_meme_audit"])
    def test_22_lexical_not_financial(self):
        self.assertEqual(m.analyze_text(VILLE,MAMH)["comparaison_lexicale"]["statut"],"RECOUVREMENT_LEXICAL_NON_MONETAIRE")
    def test_23_no_numbers_exported(self):
        self.assertNotIn("jetons_bruts",json.dumps(m.analyze_text(VILLE,MAMH)))
    def test_24_no_financial_anomaly(self):
        self.assertEqual(m.analyze_text(VILLE,MAMH)["ecarts_financiers_verifies"],0)
    def test_25_nova_certification_false(self):
        self.assertFalse(m.analyze_text(VILLE,MAMH)["comparabilite_comptable_certifiee"])
    def test_26_zero_based(self):self.assertEqual(m.PAGES,{"ville":102,"mamh":162})
    def test_27_initial_unattempted(self):
        self.assertFalse(m.report({},None)["contexte_examine"])
    def test_28_initial_no_go(self):
        self.assertEqual(m.report({},None)["decision"],m.NO_GO)
    def test_29_no_jobs_reduced(self):
        self.assertFalse(m.report({},None)["reductions_emplois_services_autorisees"])
    def test_30_no_money(self):
        self.assertIsNone(m.report({},None)["economie_certifiee_cad"])
    def test_31_mock_fetch_forged_sha(self):
        def fake(src):
            data,meta=fixture_fetch(src)
            meta["sha256_fichier_copie_publique"]=m.p54b.p54a.COPIES[src][2]
            meta["taille_octets"]=m.p54b.p54a.COPIES[src][1]
            return data,meta
        sources,pair=m.capture_pair(fake)
        self.assertIsNone(pair)
        self.assertFalse(sources["ville"]["copie_reference_P53Z_identique"])
    def test_32_mock_good_bytes(self):
        with patch.object(m.p54b.p54a,"COPIES",fixture_refs()):
            sources,pair=m.capture_pair(fixture_fetch,
                     lambda data,page: VILLE if page==102 else MAMH)
        self.assertIsNotNone(pair)
        self.assertTrue(sources["ville"]["copie_reference_P53Z_identique"])
        self.assertTrue(sources["mamh"]["copie_reference_P53Z_identique"])
    def test_33_mock_pair_context(self):
        with patch.object(m.p54b.p54a,"COPIES",fixture_refs()):
            sources,pair=m.capture_pair(fixture_fetch,
                     lambda data,index: VILLE if index==102 else MAMH)
        self.assertTrue(pair["sections_se_rapportent_probablement_au_meme_audit"])
    def test_34_mismatched_bytes(self):
        sources,pair=m.capture_pair(fixture_fetch)
        self.assertIsNone(pair)
    def test_35_unavailable_second(self):
        def f(src):
            if src=="mamh":raise ValueError("indisponible")
            return fixture_fetch(src)
        sources,pair=m.capture_pair(f)
        self.assertIsNone(pair)
        self.assertFalse(sources["mamh"]["capture"])
    def test_36_extraction_failure(self):
        with patch.object(m.p54b.p54a,"COPIES",fixture_refs()):
            sources,pair=m.capture_pair(fixture_fetch,
                     lambda data,index: (_ for _ in ()).throw(ValueError("no PDF")))
        self.assertIsNone(pair)
    def test_37_summary_good_mock(self):
        with patch.object(m.p54b.p54a,"COPIES",fixture_refs()):
            sources,pair=m.capture_pair(fixture_fetch,
                     lambda data,index: VILLE if index==102 else MAMH)
        d=m.report(sources,pair)
        self.assertTrue(d["contexte_examine"])
        self.assertFalse(d["concordance_comptable_certifiee"])
    def test_38_cli_neutral(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"s.json"
            self.assertEqual(m.main(["--bilan",str(f)]),0)
            self.assertFalse(json.loads(f.read_text("utf-8"))["contexte_examine"])
    def test_39_cli_strict(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"s.json"
            self.assertEqual(m.main(["--bilan",str(f),"--exiger-audit-certifie"]),3)
    def test_40_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"s.json";f.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(f)]),2)
            self.assertEqual(f.read_text("utf-8"),"keep")

if __name__=="__main__":
    unittest.main()
