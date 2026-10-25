#!/usr/bin/env python3
"""P54Q: reproductions hors-ligne sur données entièrement synthétiques."""
import copy
import hashlib
import json
from pathlib import Path
import os
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import reproduire_pdf_locaux_nova_p54q as m
from test_reproduire_localisations_pdf_nova_p54p import synthetic_texts

def setup(folder):
    paths={};blobs={};refs={}
    for name in m.NAMES:
        data=("%PDF-1.4\nSYNTHETIQUE-SANS-AVIS-%s\n"%name).encode()
        file=Path(folder)/(name+".pdf")
        file.write_bytes(data)
        paths[name]=file
        blobs[name]=data
        refs[name]={
          "pdf_index_zero":m.p54p.p54d.PAGES[name],
          "taille_octets":len(data),
          "sha256":hashlib.sha256(data).hexdigest(),
        }
    texts=synthetic_texts()
    def extract(blob,page):
        name=next(k for k,v in blobs.items() if v==blob)
        assert page==refs[name]["pdf_index_zero"]
        return texts[name]
    return paths,blobs,refs,extract

class TestP54Q(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()
    def fake(self,paths,refs,extract):
        with patch.object(m.p54p.context,"analyze_text",
          return_value={"sections_se_rapportent_probablement_au_meme_audit":True}):
            return m.reproduce(paths,refs,extract)
    def test_01_schema(self):self.assertEqual(self.cfg["schema_version"],"P54Q-1")
    def test_02_year(self):self.assertEqual(self.cfg["exercice"],2024)
    def test_03_parent(self):self.assertEqual(self.cfg["source_jalon"],"P54P")
    def test_04_anchoring_run(self):self.assertEqual(self.cfg["source_p54d_run"],40120462237)
    def test_05_exact_two(self):self.assertEqual(set(self.cfg["copies"]),{"ville","mamh"})
    def test_06_city_page(self):self.assertEqual(self.cfg["copies"]["ville"]["pdf_index_zero"],102)
    def test_07_ministry_page(self):self.assertEqual(self.cfg["copies"]["mamh"]["pdf_index_zero"],162)
    def test_08_city_sha_length(self):self.assertEqual(len(self.cfg["copies"]["ville"]["sha256"]),64)
    def test_09_mamh_sha_length(self):self.assertEqual(len(self.cfg["copies"]["mamh"]["sha256"]),64)
    def test_10_no_go(self):self.assertEqual(m.report(self.cfg)["decision"],m.NO_GO)
    def test_11_zero_locations_initial(self):self.assertEqual(m.report(self.cfg)["occurrences_localisees"],0)
    def test_12_zero_certification_initial(self):self.assertIsNone(m.report(self.cfg)["economies_certifiees_cad"])
    def test_13_no_external_signature(self):self.assertFalse(m.report(self.cfg)["signature_emetteur_authentifiee"])
    def test_14_no_merge(self):self.assertFalse(m.report(self.cfg)["fusion_main_autorisee"])
    def test_15_four_open(self):self.assertEqual(m.report(self.cfg)["dossiers_p54e_ouverts"],4)
    def test_16_date_not_signed(self):self.assertFalse(m.report(self.cfg)["date_probable_certifiee"])
    def test_17_96_remain(self):self.assertEqual(m.report(self.cfg)["controles_p54b_non_attestes"],96)
    def test_18_8_remain(self):self.assertEqual(m.report(self.cfg)["controles_p54c_non_attestes"],8)
    def test_19_no_net_mode(self):self.assertEqual(m.report(self.cfg)["mode"],"COPIES_LOCALES_HORS_GIT_SANS_RESEAU")
    def test_20_two_paths_readable(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,_,_=setup(d)
            self.assertEqual(m.checked_local_paths(paths),paths)
    def test_21_verified_synthetic_pair(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            report=self.fake(paths,refs,extract)
            self.assertEqual(report["statut"],"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION")
            self.assertEqual(report["copies_verifiees_par_hachage"],2)
            self.assertEqual(len(report["positions"]),5)
    def test_22_five_offsets_not_money(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            observed=self.fake(paths,refs,extract)
            report=m.report(self.cfg,observed)
            self.assertEqual(report["occurrences_localisees"],5)
            self.assertIsNone(report["economies_certifiees_cad"])
            self.assertEqual(report["avis_professionnels_certifies"],0)
    def test_23_no_tokens_context_paths(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            payload=json.dumps(m.report(self.cfg,self.fake(paths,refs,extract)))
            for value in ("contexte_local","token_brut",str(paths["ville"]),
                          str(paths["mamh"]),"SYNTHETIQUE-SANS-AVIS"):
                self.assertNotIn(value,payload)
    def test_24_exact_offsets_only_normalized(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            result=m.report(self.cfg,self.fake(paths,refs,extract))
            self.assertTrue(all("longueur_texte_normalise_nfkc" in row for row in result["positions_nfkc"]))
    def test_25_bad_size_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            paths["ville"].write_bytes(b"%PDF-X")
            result=self.fake(paths,refs,extract)
            self.assertEqual(result["sources"]["ville"],"EDITION_DIFFERENTE")
            self.assertIsNone(result["positions"])
    def test_26_changed_bytes_same_size_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            blob=paths["mamh"].read_bytes()
            paths["mamh"].write_bytes(blob[:-1]+b"Z")
            result=self.fake(paths,refs,extract)
            self.assertEqual(result["sources"]["mamh"],"EDITION_DIFFERENTE")
            self.assertIsNone(result["positions"])
    def test_27_no_partial_positions(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            refs["ville"]["sha256"]="0"*64
            result=self.fake(paths,refs,extract)
            self.assertFalse(result["cinq_positions_reproduites"])
            self.assertEqual(m.report(self.cfg,result)["occurrences_localisees"],0)
    def test_28_bad_extraction_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,_=setup(d)
            result=self.fake(paths,refs,lambda blob,page: (_ for _ in ()).throw(ValueError("bad")))
            self.assertEqual(result["statut"],"NON_REPRODUIT")
    def test_29_one_path_missing_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            paths["ville"].unlink()
            with self.assertRaises((ValueError,OSError)):
                self.fake(paths,refs,extract)
    def test_30_input_alias_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            paths["mamh"]=paths["ville"]
            with self.assertRaises(ValueError):self.fake(paths,refs,extract)
    def test_31_input_file_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            alias=Path(d)/"alias.pdf";alias.symlink_to(paths["ville"])
            paths["ville"]=alias
            with self.assertRaises(ValueError):self.fake(paths,refs,extract)
    def test_32_input_directory_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            alias=Path(d)/"alias";alias.symlink_to(Path(d),target_is_directory=True)
            paths["mamh"]=alias/"mamh.pdf"
            with self.assertRaises(ValueError):self.fake(paths,refs,extract)
    def test_33_folder_input_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            paths["mamh"]=Path(d)
            with self.assertRaises(ValueError):self.fake(paths,refs,extract)
    def test_34_wrong_keys_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            paths["unknown"]=paths["ville"]
            with self.assertRaises(ValueError):self.fake(paths,refs,extract)
    def test_35_wrong_reference_structure(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            del refs["ville"]["sha256"]
            with self.assertRaises(ValueError):self.fake(paths,refs,extract)
    def test_36_reject_file_inside_repo(self):
        with self.assertRaises(ValueError):
            m.checked_local_paths({"ville":m.CONFIG,"mamh":m.CONFIG})
    def test_37_no_network_function_called(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            with patch.object(m.p54p.acquire,"capture",
                              side_effect=AssertionError("NETWORK_FELT")):
                result=self.fake(paths,refs,extract)
            self.assertEqual(len(result["positions"]),5)
    def test_38_cli_neutral(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"public.json"
            self.assertEqual(m.main(["--bilan",str(target)]),0)
            self.assertEqual(json.loads(target.read_text("utf-8"))["occurrences_localisees"],0)
    def test_39_cli_one_missing_input(self):
        self.assertEqual(m.main(["--ville-pdf","/tmp/fake.pdf"]),2)
    def test_40_cli_reject_claimed_certification(self):
        self.assertEqual(m.main(["--exiger-certification"]),3)
    def test_41_cli_deny_existing_output(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"public.json";out.write_text("PRESERVE",encoding="utf-8")
            self.assertEqual(m.main(["--bilan",str(out)]),2)
            self.assertEqual(out.read_text("utf-8"),"PRESERVE")
    def test_42_cli_offline_reproduction_not_actual_pdf(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            with patch.object(m,"configuration",return_value={"copies":refs}):
                with patch.object(m.p54p.context,"page",side_effect=extract):
                    with patch.object(m.p54p.context,"analyze_text",
                          return_value={"sections_se_rapportent_probablement_au_meme_audit":True}):
                        status=m.main(["--ville-pdf",str(paths["ville"]),
                                       "--mamh-pdf",str(paths["mamh"])])
            self.assertEqual(status,0)
    def test_43_cli_bad_version_exit4(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            refs["ville"]["sha256"]="0"*64
            with patch.object(m,"configuration",return_value={"copies":refs}):
                with patch.object(m.p54p.context,"page",side_effect=extract):
                    status=m.main(["--ville-pdf",str(paths["ville"]),
                                   "--mamh-pdf",str(paths["mamh"])])
            self.assertEqual(status,4)
    def test_44_cli_output_collision(self):
        with tempfile.TemporaryDirectory() as d:
            paths,_,refs,extract=setup(d)
            with patch.object(m,"configuration",return_value={"copies":refs}):
                status=m.main(["--ville-pdf",str(paths["ville"]),
                               "--mamh-pdf",str(paths["mamh"]),
                               "--bilan",str(paths["ville"])])
            self.assertEqual(status,2)
    def test_45_privacy_no_files_published(self):
        self.assertEqual(m.report(self.cfg)["originaux_et_chemins_publies"],0)
    def test_46_no_expert_contact_claim(self):
        self.assertEqual(m.report(self.cfg)["avis_professionnels_certifies"],0)

def test_guard(name):
    def assertion(self):self.assertTrue(self.cfg["protections"][name])
    return assertion

for index,key in enumerate(sorted(m.GUARDS),47):
    setattr(TestP54Q,"test_%02d_guard"%index,test_guard(key))

if __name__=="__main__":
    unittest.main()
