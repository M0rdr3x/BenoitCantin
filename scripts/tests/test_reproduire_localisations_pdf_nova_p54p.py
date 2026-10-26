#!/usr/bin/env python3
"""Tests P54P sans récupération réseau ni contenu PDF non autorisé."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reproduire_localisations_pdf_nova_p54p as m

def synthetic_texts():
    common=";".join(str(100+i) for i in range(9))
    return {
      "ville":"z "*130+common+" z "*100+";789;",
      "mamh":";321;"+" z "*160+common+" z "*180+";2024;432;543;",
    }

def expected_demo(texts=None):
    texts=texts or synthetic_texts()
    raw={k:("%PDF-SIMULATION-"+k).encode() for k in m.NAMES}
    references={
       k:{"pdf_index_zero":m.p54d.PAGES[k],
          "taille_octets":len(raw[k]),
          "sha256":hashlib.sha256(raw[k]).hexdigest()}
       for k in m.NAMES}
    def fetch(k):
        blob=raw[k]
        return blob,{
          "source_id":k,"taille_octets":len(blob),
          "sha256_fichier_copie_publique":hashlib.sha256(blob).hexdigest(),
        }
    def extract(blob,index):
        for k in m.NAMES:
            if blob==raw[k]:
                if index!=references[k]["pdf_index_zero"]:
                    raise ValueError("wrong index")
                return texts[k]
        raise ValueError("unknown bytes")
    return raw,references,fetch,extract

class TestsP54P(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=m.configuration()
        cls.texts=synthetic_texts()

    def synthetic_localize(self,text=None):
        with patch.object(m.context,"analyze_text",
           return_value={"sections_se_rapportent_probablement_au_meme_audit":True}):
            return m.localize(text or self.texts)

    def synthetic_verify(self,fetch=None,extract=None,refs=None):
        _,original,fetcher,extractor=expected_demo()
        with patch.object(m.context,"analyze_text",
           return_value={"sections_se_rapportent_probablement_au_meme_audit":True}):
            return m.verify_captures(fetch or fetcher,extract or extractor,
                                     refs or original)

    def test_01_schema(self):self.assertEqual(self.config["schema_version"],"P54P-1")
    def test_02_2024(self):self.assertEqual(self.config["exercice"],2024)
    def test_03_sources(self):self.assertEqual(set(self.config["sources"]),set(m.NAMES))
    def test_04_sha64(self):self.assertTrue(all(len(x["sha256"])==64 for x in self.config["sources"].values()))
    def test_05_ville_page(self):self.assertEqual(self.config["sources"]["ville"]["pdf_index_zero"],102)
    def test_06_mamh_page(self):self.assertEqual(self.config["sources"]["mamh"]["pdf_index_zero"],162)
    def test_07_observations_count(self):self.assertEqual(len(m.EXPECTED_ROWS),5)
    def test_08_indeterminate_four(self):self.assertEqual(sum(x["classe"]=="INDETERMINE" for x in m.EXPECTED_ROWS),4)
    def test_09_date_one(self):self.assertEqual(sum(x["classe"]=="ANNEE_DATE_PROBABLE" for x in m.EXPECTED_ROWS),1)
    def test_10_fifth_not_p54e(self):self.assertIsNone(m.EXPECTED_ROWS[2]["dossier"])
    def test_11_initial_baseline_not_attempted(self):self.assertEqual(m.baseline()["statut"],"NON_TENTE")
    def test_12_zero_baseline_locations(self):self.assertIsNone(m.baseline()["positions"])
    def test_13_zero_baseline_savings(self):self.assertIsNone(m.report(self.config)["economies_certifiees_cad"])
    def test_14_no_go(self):self.assertEqual(m.report(self.config)["decision"],m.NO_GO)
    def test_15_no_main(self):self.assertFalse(m.report(self.config)["fusion_main_autorisee"])
    def test_16_no_close(self):self.assertEqual(m.report(self.config)["dossiers_p54e_ouverts"],4)
    def test_17_p54b_open(self):self.assertEqual(m.report(self.config)["controles_p54b_non_attestes"],96)
    def test_18_p54c_open(self):self.assertEqual(m.report(self.config)["controles_p54c_non_attestes"],8)
    def test_19_localization_synthetic_five(self):
        found=self.synthetic_localize()
        self.assertEqual(len(found),5)
        self.assertEqual([r["index_observation_p54d"] for r in found],list(range(5)))
    def test_20_localization_synthetic_expected_zones(self):
        r=self.synthetic_localize()
        self.assertEqual([x["zone_confirmee_par_parseur"] for x in r],
                         ["FIN","DEBUT","FIN","FIN","FIN"])
    def test_21_localization_synthetic_date(self):
        r=self.synthetic_localize()
        self.assertEqual(r[2]["classification_indicative"],"ANNEE_DATE_PROBABLE")
        self.assertIsNone(r[2]["dossier"])
    def test_22_localization_synthetic_offsets(self):
        r=self.synthetic_localize()
        self.assertTrue(all(0<=x["offset_texte_extrait"]<x["longueur_texte_normalise_nfkc"] for x in r))
    def test_23_no_raw_token_or_context(self):
        r=self.synthetic_localize()
        self.assertTrue(all(set(item)=={
          "index_observation_p54d","source","dossier","pdf_index_zero",
          "offset_texte_extrait","longueur_texte_normalise_nfkc",
          "zone_confirmee_par_parseur","classification_indicative",
          "aucune_conclusion_financiere"} for item in r))
    def test_24_wrong_token_count_rejected(self):
        texts=copy.deepcopy(self.texts);texts["ville"]=texts["ville"].replace(";789;",";")
        with self.assertRaises(ValueError):self.synthetic_localize(texts)
    def test_25_wrong_date_classification_rejected(self):
        texts=copy.deepcopy(self.texts);texts["mamh"]=texts["mamh"].replace(";2024;",";666;")
        with self.assertRaises(ValueError):self.synthetic_localize(texts)
    def test_26_wrong_audit_scope_rejected(self):
        with patch.object(m.context,"analyze_text",
           return_value={"sections_se_rapportent_probablement_au_meme_audit":False}):
            with self.assertRaises(ValueError):m.localize(self.texts)
    def test_27_unauthorized_text_fields_rejected(self):
        with self.assertRaises(ValueError):self.synthetic_localize({"ville":self.texts["ville"],"mamh":self.texts["mamh"],"extra":"text"})
    def test_28_blank_source_rejected(self):
        with self.assertRaises(ValueError):self.synthetic_localize({"ville":"","mamh":self.texts["mamh"]})
    def test_29_successful_synthetic_pair_still_not_certified(self):
        r=self.synthetic_verify()
        self.assertEqual(r["statut"],"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION")
        self.assertEqual(len(r["positions"]),5)
        out=m.report(self.config,r)
        self.assertIsNone(out["economies_certifiees_cad"])
        self.assertFalse(out["pdf_sources_deja_attestes_par_emetteur"])
    def test_30_wrong_octets_rejected(self):
        raw,refs,fetch,extract=expected_demo()
        def wrong(k):
            blob,meta=fetch(k)
            if k=="ville":blob+=b"ALT"
            return blob,meta
        r=self.synthetic_verify(fetch=wrong)
        self.assertEqual(r["statut"],"NON_REPRODUIT")
        self.assertIsNone(r["positions"])
        self.assertEqual(r["sources"]["ville"],"EDITION_DIFFERENTE")
    def test_31_wrong_metadata_rejected(self):
        raw,refs,fetch,extract=expected_demo()
        def wrong(k):
            blob,meta=fetch(k)
            if k=="mamh":meta["source_id"]="ville"
            return blob,meta
        r=self.synthetic_verify(fetch=wrong)
        self.assertEqual(r["statut"],"NON_REPRODUIT")
        self.assertEqual(r["sources"]["mamh"],"EDITION_DIFFERENTE")
    def test_32_unavailable_mamh_not_falsely_verified(self):
        raw,refs,fetch,extract=expected_demo()
        def offline(k):
            if k=="mamh":raise OSError("indisponible")
            return fetch(k)
        r=self.synthetic_verify(fetch=offline)
        self.assertEqual(r["statut"],"NON_REPRODUIT")
        self.assertEqual(r["sources"]["mamh"],"SOURCE_NON_ACQUISE")
    def test_33_wrong_extractor_index_rejected(self):
        raw,refs,fetch,extract=expected_demo()
        def invalid(blob,idx):
            raise ValueError("synthetic bad page")
        r=self.synthetic_verify(extract=invalid)
        self.assertEqual(r["statut"],"NON_REPRODUIT")
        self.assertIsNone(r["positions"])
    def test_34_wrong_version_even_identical_context(self):
        _,refs,fetch,extract=expected_demo()
        refs["ville"]["sha256"]="0"*64
        r=self.synthetic_verify(refs=refs)
        self.assertIsNone(r["positions"])
        self.assertEqual(r["sources"]["ville"],"EDITION_DIFFERENTE")
    def test_35_bad_audit_context_no_positions(self):
        _,refs,fetch,extract=expected_demo()
        with patch.object(m.context,"analyze_text",
           return_value={"sections_se_rapportent_probablement_au_meme_audit":False}):
            r=m.verify_captures(fetch,extract,refs)
        self.assertEqual(r["statut"],"NON_REPRODUIT")
    def test_36_no_private_jetons_in_public_json(self):
        r=self.synthetic_verify()
        out=json.dumps(m.report(self.config,r))
        self.assertNotIn("token_brut",out)
        self.assertNotIn("contexte_local",out)
        self.assertNotIn("789",out)
        self.assertNotIn("543",out)
    def test_37_all_locations_only_if_all_reproduced(self):
        r=self.synthetic_verify()
        self.assertEqual(m.report(self.config,r)["occurrences_localisees_automatiquement"],5)
        r["cinq_positions_reproduites"]=False
        r["statut"]="NON_REPRODUIT"
        r["positions"]=None
        r["sources"]["ville"]="CONTEXTE_OU_EXTRACTION_INCOHERENTE"
        self.assertEqual(m.report(self.config,r)["occurrences_localisees_automatiquement"],0)
        self.assertIsNone(m.report(self.config,r)["positions_caracteres_sur_texte_extrait"])
    def test_38_cli_baseline_neutral(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/"summary.json"
            self.assertEqual(m.main(["--bilan",str(f)]),0)
            out=json.loads(f.read_text(encoding="utf-8"))
            self.assertEqual(out["statut_capture"],"NON_TENTE")
            self.assertEqual(out["occurrences_localisees_automatiquement"],0)
    def test_39_cli_auto_certification_denied(self):
        self.assertEqual(m.main(["--exiger-certification"]),3)
    def test_40_cli_fail_closed_if_no_network(self):
        with patch.object(m.acquire,"capture",side_effect=OSError("offline")):
            self.assertEqual(m.main(["--acquerir"]),4)
    def test_41_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"already.json";f.write_text("PRESERVED","utf-8")
            self.assertEqual(m.main(["--bilan",str(f)]),2)
            self.assertEqual(f.read_text("utf-8"),"PRESERVED")
    def test_42_cli_symlink_refused(self):
        with tempfile.TemporaryDirectory() as d:
            real=Path(d)/"real.json";real.write_text("SAVED","utf-8")
            alias=Path(d)/"alias.json";alias.symlink_to(real)
            self.assertEqual(m.main(["--bilan",str(alias)]),2)
            self.assertEqual(real.read_text("utf-8"),"SAVED")
    def test_43_source_hash_not_identity(self):
        self.assertFalse(m.report(self.config)["pdf_sources_deja_attestes_par_emetteur"])
    def test_44_false_client_saving_denied(self):
        self.assertIsNone(m.report(self.config)["economies_certifiees_cad"])

    def test_44a_public_report_extra_raw_token_refused(self):
        r=self.synthetic_verify()
        r["positions"][0]["token_brut"]="SENSITIVE"
        with self.assertRaises(ValueError):m.report(self.config,r)
    def test_44b_public_report_extra_context_refused(self):
        r=self.synthetic_verify()
        r["positions"][0]["contexte_local"]="SENSITIVE"
        with self.assertRaises(ValueError):m.report(self.config,r)
    def test_44c_public_report_wrong_page_refused(self):
        r=self.synthetic_verify()
        r["positions"][0]["pdf_index_zero"]=777
        with self.assertRaises(ValueError):m.report(self.config,r)
    def test_44d_public_report_duplicate_offset_refused(self):
        r=self.synthetic_verify()
        r["positions"][4]["offset_texte_extrait"]=r["positions"][3]["offset_texte_extrait"]
        with self.assertRaises(ValueError):m.report(self.config,r)
    def test_44e_public_report_incomplete_positions_refused(self):
        r=self.synthetic_verify()
        r["positions"].pop()
        with self.assertRaises(ValueError):m.report(self.config,r)
    def test_44f_public_report_falsely_verified_refused(self):
        r=self.synthetic_verify()
        r["copies_verifiees_par_hachage"]=1
        with self.assertRaises(ValueError):m.report(self.config,r)
    def test_44g_public_report_forged_success_without_positions_refused(self):
        r=m.baseline()
        r["statut"]="REPRODUCTION_TECHNIQUE_SANS_ATTESTATION"
        r["cinq_positions_reproduites"]=True
        with self.assertRaises(ValueError):m.report(self.config,r)
    def test_44h_public_report_bare_secret_field_refused(self):
        r=m.baseline()
        r["nom_professionnel"]="SENSITIVE"
        with self.assertRaises(ValueError):m.report(self.config,r)

def guard(key):
    def run(self):self.assertTrue(self.config["protections"][key])
    return run
for n,key in enumerate(sorted(m.GUARDS),45):
    setattr(TestsP54P,"test_%02d_guard"%n,guard(key))

if __name__=="__main__":
    unittest.main()
