#!/usr/bin/env python3
"""P54T: bilans publics historiques figés, sans acquisition réseau ni PDF."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verifier_archive_publique_figee_nova_p54t as m


def independent_copy(root):
    folder=Path(root)
    sources={}
    for name in m.NAMES:
        target=folder/name
        shutil.copyfile(m.FROZEN/name,target)
        sources[name]=target
    return sources


class TestP54T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()
        cls.data=m.verify_frozen(cls.cfg)
        cls.report=m.report(cls.cfg,cls.data)

    def test_01_schema(self):self.assertEqual(self.cfg["schema_version"],"P54T-1")
    def test_02_parent(self):self.assertEqual(self.cfg["source_jalon"],"P54R")
    def test_03_run(self):self.assertEqual(self.cfg["reference_run_p54p"],40151185184)
    def test_04_artifact(self):self.assertEqual(self.cfg["reference_artifact_p54p"],12583661231)
    def test_05_zip_sha(self):self.assertEqual(len(self.cfg["source_zip_sha256_historique"]),64)
    def test_06_two_members(self):self.assertEqual(set(self.cfg["copies_figees"]),set(m.NAMES))
    def test_07_fixed_795(self):self.assertEqual(self.cfg["copies_figees"][m.NAMES[0]]["taille_octets"],795)
    def test_08_fixed_2631(self):self.assertEqual(self.cfg["copies_figees"][m.NAMES[1]]["taille_octets"],2631)
    def test_09_exact_digest_first(self):
        raw=(m.FROZEN/m.NAMES[0]).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),self.cfg["copies_figees"][m.NAMES[0]]["sha256"])
    def test_10_exact_digest_second(self):
        raw=(m.FROZEN/m.NAMES[1]).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),self.cfg["copies_figees"][m.NAMES[1]]["sha256"])
    def test_11_real_frozen_files_verified(self):self.assertEqual(self.data["bilans_figes_verifies"],2)
    def test_12_bytes_verified(self):self.assertEqual(self.data["tailles_octets_verifiees"],3426)
    def test_13_five_historical_offsets(self):self.assertEqual(self.data["positions_historiques_hachees"],5)
    def test_14_positions_order(self):
        self.assertEqual([row["offset_texte_extrait"] for row in self.data["positions_de_reference"]],[2359,18,2420,2430,2436])
    def test_15_pdf_pages(self):
        self.assertEqual([row["pdf_index_zero"] for row in self.data["positions_de_reference"]],[102,162,162,162,162])
    def test_16_final_dossier_ids(self):
        self.assertEqual([row["dossier"] for row in self.data["positions_de_reference"]],["P54E-V-001","P54E-M-001",None,"P54E-M-002","P54E-M-003"])
    def test_17_not_pdf_reacquisition(self):self.assertEqual(self.report["pdf_originaux_relus_ce_run"],0)
    def test_18_not_zip_reverification(self):self.assertFalse(self.report["zip_archive_originale_relue_ce_run"])
    def test_19_no_professional_authentication(self):self.assertEqual(self.report["pdf_emetteurs_authentifies"],0)
    def test_20_no_counterexpertise(self):self.assertEqual(self.report["contre_expertises_independantes"],0)
    def test_21_no_money(self):self.assertIsNone(self.report["economies_certifiees_cad"])
    def test_22_no_go(self):self.assertEqual(self.report["decision"],m.NO_GO)
    def test_23_no_main(self):self.assertFalse(self.report["main_fusion_autorisee"])
    def test_24_p54b_open(self):self.assertEqual(self.report["controles_p54b_non_attestes"],96)
    def test_25_p54c_open(self):self.assertEqual(self.report["controles_p54c_non_attestes"],8)
    def test_26_date_remains(self):self.assertTrue(self.report["date_probable_non_certifiee"])
    def test_27_four_cases_open(self):self.assertEqual(self.report["dossiers_p54e_ouverts"],4)
    def test_28_baseline_not_verified(self):
        result=m.report(self.cfg)
        self.assertEqual(result["bilans_publics_fixes_reverifies_ce_run"],0)
        self.assertIsNone(result["positions_nfkc_texte_source"])
    def test_29_no_secret_fields(self):
        serialized=json.dumps(self.report)
        for forbidden in ("token_brut","contexte_local","nom_professionnel","signature_originale","chemin_pdf_local"):
            self.assertNotIn(forbidden,serialized)
    def test_30_copy_is_also_valid(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.verify_frozen(self.cfg,independent_copy(d)),self.data)
    def test_31_edited_final_fails(self):
        with tempfile.TemporaryDirectory() as d:
            copied=independent_copy(d);f=copied[m.NAMES[1]]
            f.write_bytes(f.read_bytes().replace(b'2436',b'2435'))
            with self.assertRaises(ValueError):m.verify_frozen(self.cfg,copied)
    def test_32_appended_bytes_fail(self):
        with tempfile.TemporaryDirectory() as d:
            copied=independent_copy(d)
            with copied[m.NAMES[1]].open("ab") as handle:handle.write(b" ")
            with self.assertRaises(ValueError):m.verify_frozen(self.cfg,copied)
    def test_33_same_size_tamper_fail(self):
        with tempfile.TemporaryDirectory() as d:
            copied=independent_copy(d);f=copied[m.NAMES[0]]
            b=bytearray(f.read_bytes());b[8]^=1;f.write_bytes(b)
            self.assertEqual(f.stat().st_size,795)
            with self.assertRaises(ValueError):m.verify_frozen(self.cfg,copied)
    def test_34_missing_final_fail(self):
        with tempfile.TemporaryDirectory() as d:
            copied=independent_copy(d)
            copied[m.NAMES[1]].unlink()
            with self.assertRaises(ValueError):m.verify_frozen(self.cfg,copied)
    def test_35_symlink_member_fail(self):
        with tempfile.TemporaryDirectory() as d:
            copied=independent_copy(d)
            old=copied[m.NAMES[0]]
            actual=Path(d)/"real.json";old.rename(actual)
            old.symlink_to(actual)
            with self.assertRaises(ValueError):m.verify_frozen(self.cfg,copied)
    def test_36_wrong_file_mapping_fail(self):
        with tempfile.TemporaryDirectory() as d:
            copied=independent_copy(d)
            copied[m.NAMES[0]],copied[m.NAMES[1]]=copied[m.NAMES[1]],copied[m.NAMES[0]]
            with self.assertRaises(ValueError):m.verify_frozen(self.cfg,copied)
    def test_37_only_one_member_fails(self):
        with tempfile.TemporaryDirectory() as d:
            copied=independent_copy(d);copied.pop(m.NAMES[0])
            with self.assertRaises(ValueError):m.verify_frozen(self.cfg,copied)
    def test_38_unexpected_member_fails(self):
        with tempfile.TemporaryDirectory() as d:
            copied=independent_copy(d);copied["readme.txt"]=Path(d)/"foo"
            with self.assertRaises(ValueError):m.verify_frozen(self.cfg,copied)
    def test_39_sha_anomaly_with_modified_manifest(self):
        local=copy.deepcopy(self.cfg)
        local["copies_figees"][m.NAMES[1]]["sha256"]="0"*64
        with self.assertRaises(ValueError):m.verify_frozen(local)
    def test_40_report_does_not_imply_original_zip_verified(self):
        self.assertFalse(m.report(self.cfg,self.data)["zip_archive_originale_relue_ce_run"])
    def test_41_report_does_not_reuse_verified_without_input(self):
        self.assertEqual(m.report(self.cfg)["positions_des_bilans_figes_reverifiees_ce_run"],0)
    def test_42_cli_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"baseline.json"
            self.assertEqual(m.main(["--bilan",str(target)]),0)
            result=json.loads(target.read_text("utf-8"))
            self.assertEqual(result["bilans_publics_fixes_reverifies_ce_run"],0)
    def test_43_cli_frozen_verified(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"verified.json"
            self.assertEqual(m.main(["--verifier-fichiers-figes","--bilan",str(target)]),0)
            result=json.loads(target.read_text("utf-8"))
            self.assertEqual(result["bilans_publics_fixes_reverifies_ce_run"],2)
            self.assertEqual(result["positions_des_bilans_figes_reverifiees_ce_run"],5)
    def test_44_cli_auto_certification_denied(self):
        self.assertEqual(m.main(["--exiger-certification"]),3)
    def test_45_cli_auto_certification_denied_even_if_verified(self):
        self.assertEqual(m.main(["--verifier-fichiers-figes","--exiger-certification"]),3)
    def test_46_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"present.json";target.write_text("KEEP","utf-8")
            self.assertEqual(m.main(["--bilan",str(target)]),2)
            self.assertEqual(target.read_text("utf-8"),"KEEP")
    def test_47_cli_no_symlink_output(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"actual.json";target.write_text("KEEP","utf-8")
            alias=Path(d)/"alias.json";alias.symlink_to(target)
            self.assertEqual(m.main(["--bilan",str(alias)]),2)
    def test_48_official_roles_unchanged(self):
        self.assertEqual(self.report["pdf_emetteurs_authentifies"],0)
    def test_49_provenance_member_size_total(self):
        self.assertEqual(self.report["octets_bilans_reverifies_ce_run"],3426)
    def test_50_immutable_paths_in_git(self):
        self.assertTrue(all((m.FROZEN/n).is_file() for n in m.NAMES))

def protection(name):
    def test(self):self.assertTrue(self.cfg["protections"][name])
    return test

for n,name in enumerate(sorted(m.GUARDS),51):
    setattr(TestP54T,"test_%02d_guard"%n,protection(name))

if __name__=="__main__":
    unittest.main()
