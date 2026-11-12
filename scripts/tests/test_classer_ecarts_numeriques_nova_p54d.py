#!/usr/bin/env python3
"""P54D — tests 100 % synthétiques, sans téléchargement ni pièces privées."""
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import classer_ecarts_numeriques_nova_p54d as m

HEADER=("Rapport des auditeurs independants sur la ventilation des "
        "depenses mixtes, competences locales et d'agglomeration. ")
COMMON=["2024","1435","100","200","300","400","500","600","700"]
VILLE=HEADER+"; ".join(COMMON)+"; Page 103"
MAMH=HEADER+"; ".join(COMMON)+"; Page 163; reference reglement 42; tel 75; Date 2025"
def fake_capture(src):
    data=b"SYNTHESE_VILLE" if src=="ville" else b"SYNTHESE_MAMH"
    return data,{"source_id":src,"taille_octets":len(data),
        "sha256_fichier_copie_publique":sha256(data).hexdigest()}
def fake_refs():
    return {k:("date",len(fake_capture(k)[0]),
             sha256(fake_capture(k)[0]).hexdigest(),1,0)
            for k in ("ville","mamh")}
def extract(_raw,idx):
    return VILLE if idx==102 else MAMH

class TestP54D(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.config()
        cls.extras=m.unmatched(VILLE,MAMH)
    def test_01_schema(self):self.assertEqual(self.cfg["schema_version"],"P54D-1")
    def test_02_p54c_run(self):self.assertEqual(self.cfg["source_p54c_run"],40119313052)
    def test_03_scope_year(self):self.assertEqual(self.cfg["exercice"],2024)
    def test_04_pages(self):self.assertEqual(self.cfg["pair_pdf_index_zero"],m.PAGES)
    def test_05_ref_city(self):self.assertEqual(m.REFERENCE["ville"],10)
    def test_06_ref_mamh(self):self.assertEqual(m.REFERENCE["mamh"],13)
    def test_07_ref_common(self):self.assertEqual(m.REFERENCE["communes"],9)
    def test_08_ref_five(self):self.assertEqual(m.REFERENCE["total_non_appariees"],5)
    def test_09_eight_gates(self):self.assertEqual(len(m.GATES),8)
    def test_10_six_categories(self):self.assertEqual(len(m.CATEGORIES),6)
    def test_11_all_guards(self):self.assertTrue(all(self.cfg["guards"].values()))
    def test_12_initial_go_denied(self):self.assertEqual(self.cfg["baseline"]["decision"],m.NO_GO)
    def test_13_unknown_financial(self):self.assertIsNone(self.cfg["baseline"]["economie_certifiee_cad"])
    def test_14_instances_city(self):self.assertEqual(len(m.instances(VILLE)),10)
    def test_15_instances_mamh(self):self.assertEqual(len(m.instances(MAMH)),13)
    def test_16_unmatched_city(self):self.assertEqual(len(self.extras["ville"]),1)
    def test_17_unmatched_mamh(self):self.assertEqual(len(self.extras["mamh"]),4)
    def test_18_5_total(self):
        self.assertEqual(sum(map(len,self.extras.values())),5)
    def test_19_2024_common(self):
        self.assertNotIn("2024",[x["token"] for s in self.extras.values() for x in s])
    def test_20_2025_date(self):
        self.assertEqual(m.classify({"token":"2025","context":"Date 2025","zone":"FIN"}),"ANNEE_DATE_PROBABLE")
    def test_21_ravq_regulation(self):
        self.assertEqual(m.classify({"token":"1435","context":"reglement R.A.V.Q. 1435","zone":"MILIEU"}),"REFERENCE_REGLEMENTAIRE_PROBABLE")
    def test_22_page(self):
        self.assertEqual(m.classify({"token":"103","context":"Page 103","zone":"FIN"}),"PAGINATION_FOLIO_PROBABLE")
    def test_23_contact(self):
        self.assertEqual(m.classify({"token":"75","context":"tel 75","zone":"FIN"}),"COORDONNEE_IDENTIFIANT_PROBABLE")
    def test_24_currency(self):
        self.assertEqual(m.classify({"token":"500","context":"Valeur $ 500","zone":"MILIEU"}),"VALEUR_CHIFFREE_A_QUALIFIER")
    def test_25_unknown(self):
        self.assertEqual(m.classify({"token":"123","context":"mesure 123 autre","zone":"MILIEU"}),"INDETERMINE")
    def test_26_accent(self):
        self.assertEqual(m.normalize_context("FÉVRIER"),"fevrier")
    def test_27_classify_total(self):
        rows,raw=m.classify_extras(self.extras)
        self.assertEqual(len(rows),5)
        self.assertEqual(len(raw),5)
    def test_28_private_token_only_private(self):
        rows,private=m.classify_extras(self.extras)
        self.assertTrue(all("token_brut" not in row and "contexte_local" not in row for row in rows))
        self.assertTrue(all("token_brut" in row for row in private))
    def test_29_city_mamh_counts(self):
        rows,_=m.classify_extras(self.extras)
        self.assertEqual(Counter(x["source"] for x in rows),Counter({"ville":1,"mamh":4}))
    def test_30_neutral_report(self):
        r=m.summary({},None)
        self.assertFalse(r["cinq_occurrences_verifiees"])
        self.assertIsNone(r["categories_observees"])
    def test_31_success_report(self):
        rows,_=m.classify_extras(self.extras)
        r=m.summary({},rows)
        self.assertTrue(r["cinq_occurrences_verifiees"])
        self.assertEqual(sum(r["categories_observees"].values()),5)
    def test_32_no_money_in_public(self):
        rows,_=m.classify_extras(self.extras)
        data=json.dumps(m.summary({},rows),ensure_ascii=False)
        self.assertNotIn("token_brut",data)
        self.assertNotIn("contexte_local",data)
        self.assertNotIn("Page 163",data)
    def test_33_refuse_partial(self):
        with self.assertRaises(ValueError):m.summary({},[{"categorie_indicative":"INDETERMINE","qualification":"NON_CERTIFIEE"}])
    def test_34_refuse_wrong_counts(self):
        with self.assertRaises(ValueError):m.unmatched(VILLE,MAMH+" 999")
    def test_35_no_edit_certified(self):
        self.assertFalse(m.summary({},None)["expertise_comptable_independante_signee"])
    def test_36_no_false_audit(self):
        self.assertEqual(m.summary({},None)["ecarts_de_montants_comptables_authentifies"],0)
    def test_37_mock_bad_hash(self):
        obs,rows,private=m.fetch_pair(fake_capture,extract)
        self.assertIsNone(rows)
        self.assertFalse(obs["ville"]["version_p53z_identique"])
    def test_38_good_capture_with_mock(self):
        with patch.object(m.p54b.p54a,"COPIES",fake_refs()):
            obs,rows,private=m.fetch_pair(fake_capture,extract)
        self.assertIsNotNone(rows)
        self.assertEqual(len(rows),5)
        self.assertTrue(obs["mamh"]["version_p53z_identique"])
    def test_39_one_missing_source(self):
        def fetch(src):
            if src=="mamh":raise ValueError("unavailable")
            return fake_capture(src)
        obs,rows,private=m.fetch_pair(fetch,extract)
        self.assertIsNone(rows)
        self.assertFalse(obs["mamh"]["capture"])
    def test_40_wrong_document_context(self):
        with patch.object(m.p54b.p54a,"COPIES",fake_refs()):
            obs,rows,private=m.fetch_pair(fake_capture,
              lambda _blob,index: VILLE if index==102 else "unrelated document")
        self.assertIsNone(rows)
    def test_41_output_new_file(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"public.json"
            m.write_json(target,m.summary({},None))
            self.assertTrue(target.is_file())
    def test_42_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"data.json"
            target.write_text("preserve","utf-8")
            with self.assertRaises(ValueError):m.write_json(target,{})
            self.assertEqual(target.read_text("utf-8"),"preserve")
    def test_43_private_mode(self):
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/"private.json"
            m.write_json(output,{"private":True},private=True)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode),0o600)
    def test_44_private_disallowed_git(self):
        with self.assertRaises(ValueError):m.write_json(m.ROOT/"mysecret.json",{},private=True)
    def test_45_cli_neutral(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"report.json"
            self.assertEqual(m.main(["--bilan",str(p)]),0)
            self.assertFalse(json.loads(p.read_text("utf-8"))["cinq_occurrences_verifiees"])
    def test_46_cli_no_private_without_download(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(m.main(["--diagnostic-prive",str(Path(td)/"secrets.json")]),2)
    def test_47_cli_explicit_no_cert(self):
        self.assertEqual(m.main(["--exiger-preuve-comptable"]),3)
    def test_48_report_no_go(self):
        self.assertEqual(m.summary({},None)["decision"],m.NO_GO)
    def test_49_no_jobs_cuts(self):
        self.assertFalse(m.summary({},None)["emploi_et_services_reduits_autorises"])
    def test_50_neutral_no_sources(self):
        self.assertEqual(m.summary({},None)["sources"],{})
    def test_51_public_noncertified(self):
        rows,_=m.classify_extras(self.extras)
        self.assertTrue(all(row["qualification"]=="NON_CERTIFIEE" for row in rows))
    def test_52_no_certification_anyway(self):
        self.assertIsNone(m.summary({},None)["economie_certifiee_cad"])

if __name__=="__main__":
    unittest.main()
