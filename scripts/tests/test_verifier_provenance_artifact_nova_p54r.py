#!/usr/bin/env python3
"""P54R: tests ZIP publics fictifs, aucun PDF ou signature professionnelle."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verifier_provenance_artifact_nova_p54r as m

def fixture(directory,variant="OK"):
    initial=m.p54p.report(m.p54p.configuration())
    attempt={
      "statut":"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION",
      "sources":{k:"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION"
                 for k in m.p54p.NAMES},
      "copies_verifiees_par_hachage":2,
      "cinq_positions_reproduites":True,
      "positions":m.known_rows(),
    }
    final=m.p54p.report(m.p54p.configuration(),attempt)
    if variant=="SANS_POSITIONS":final["positions_caracteres_sur_texte_extrait"]=None
    if variant=="JETON_BRUT":final["jeton_brut"]="secret"
    if variant=="ERREUR_FINANCIERE":final["economies_certifiees_cad"]=12000
    if variant=="AUTRE_OFFSET":final["positions_caracteres_sur_texte_extrait"][0]["offset_texte_extrait"]=999
    if variant=="NON_CERTIFIE_FALSE":final["positions_caracteres_sur_texte_extrait"][0]["aucune_conclusion_financiere"]=False
    if variant=="INITIAL_FALSIFIE":initial["statut_capture"]="REPRODUCTION_TECHNIQUE_SANS_ATTESTATION"
    name1="p54p_avant_acquisition.json";name2="p54p_reproduction_conditionnelle.json"
    files={
      name1:(json.dumps(initial,sort_keys=True).encode("utf-8")),
      name2:(json.dumps(final,sort_keys=True).encode("utf-8")),
    }
    if variant=="EXTRA_FILE":files["../../secret.txt"]=b"SECRET"
    if variant=="MISSING_FILE":del files[name1]
    if variant=="NOT_JSON":files[name2]=b"\xff"
    data=io.BytesIO()
    with zipfile.ZipFile(data,"w",zipfile.ZIP_DEFLATED) as z:
        for name,content in files.items():z.writestr(name,content)
    blob=data.getvalue()
    dest=Path(directory)/"source.zip";dest.write_bytes(blob)
    cfg=copy.deepcopy(m.configuration())
    cfg["artifact_sha256"]=hashlib.sha256(blob).hexdigest()
    cfg["archive_size_octets"]=len(blob)
    listing={k:(hashlib.sha256(v).hexdigest(),len(v)) for k,v in files.items()}
    cfg["pieces_archive"]={k:{"sha256":v[0],"taille_octets":v[1]} for k,v in listing.items()}
    return dest,cfg,listing

class TestP54R(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cfg=m.configuration()
    def test_01_config(self):self.assertEqual(self.cfg["schema_version"],"P54R-1")
    def test_02_run(self):self.assertEqual(self.cfg["source_run_id"],40151185184)
    def test_03_job(self):self.assertEqual(self.cfg["source_job_id"],121042887853)
    def test_04_artifact(self):self.assertEqual(self.cfg["artifact_id"],12583661231)
    def test_05_zip_digest(self):self.assertEqual(len(self.cfg["artifact_sha256"]),64)
    def test_06_zip_size(self):self.assertEqual(self.cfg["archive_size_octets"],1533)
    def test_07_member_digests(self):self.assertTrue(all(len(x["sha256"])==64 for x in self.cfg["pieces_archive"].values()))
    def test_08_members_exact(self):self.assertEqual(set(self.cfg["pieces_archive"]),set(m.PIECES))
    def test_09_sources(self):self.assertEqual(set(self.cfg["sha256_sources_p54d"]),{"ville","mamh"})
    def test_10_positions(self):self.assertEqual(len(m.known_rows()),5)
    def test_11_offsets(self):self.assertEqual([x["offset_texte_extrait"] for x in m.known_rows()],[2359,18,2420,2430,2436])
    def test_12_pages(self):self.assertEqual([x["pdf_index_zero"] for x in m.known_rows()],[102,162,162,162,162])
    def test_13_date(self):self.assertIsNone(m.known_rows()[2]["dossier"])
    def test_14_baseline_archive_unread(self):self.assertFalse(m.report(self.cfg)["archive_verifiee_par_octets_dans_cette_execution"])
    def test_15_baseline_not_reverified(self):self.assertEqual(m.report(self.cfg)["positions_reverifiees_dans_cette_execution"],0)
    def test_16_historical_five(self):self.assertEqual(len(m.report(self.cfg)["cinq_positions_de_reference"]),5)
    def test_17_no_go(self):self.assertEqual(m.report(self.cfg)["decision"],m.NO_GO)
    def test_18_no_money(self):self.assertIsNone(m.report(self.cfg)["economies_certifiees_cad"])
    def test_19_no_closure(self):self.assertEqual(m.report(self.cfg)["dossiers_p54e_ouverts"],4)
    def test_20_sources_not_read_in_runner(self):self.assertEqual(m.report(self.cfg)["sources_pdf_physiquement_relues_dans_cette_execution"],0)
    def test_21_valid_synthetic_archive(self):
        with tempfile.TemporaryDirectory() as d:
            file,cfg,listing=fixture(d)
            with patch.dict(m.PIECES,listing,clear=True):
                self.assertTrue(m.examine_archive(file,cfg))
                self.assertTrue(m.report(cfg,True)["archive_verifiee_par_octets_dans_cette_execution"])
    def test_22_wrong_digest(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d);c["artifact_sha256"]="0"*64
            with self.assertRaisesRegex(ValueError,"ARCHIVE_SHA256"):
                m.examine_archive(f,c)
    def test_23_wrong_size(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d);c["archive_size_octets"]+=1
            with self.assertRaises(ValueError):m.examine_archive(f,c)
    def test_24_extra_zip_member(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d,"EXTRA_FILE")
            with patch.dict(m.PIECES,l,clear=True):
                with self.assertRaises(ValueError):m.examine_archive(f,c)
    def test_25_missing_zip_member(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d,"MISSING_FILE")
            with patch.dict(m.PIECES,l,clear=True):
                with self.assertRaises(ValueError):m.examine_archive(f,c)
    def test_26_member_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d)
            altered=dict(l);key="p54p_reproduction_conditionnelle.json"
            altered[key]=("0"*64,l[key][1])
            with patch.dict(m.PIECES,altered,clear=True):
                with self.assertRaises(ValueError):m.examine_archive(f,c)
    def test_27_unsigned_artifact_not_attested(self):
        self.assertFalse(m.report(self.cfg)["qualification_professionnelle"])
    def test_28_bad_local_signature(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d,"ERREUR_FINANCIERE")
            with patch.dict(m.PIECES,l,clear=True):
                with self.assertRaises(ValueError):m.examine_archive(f,c)
    def test_29_no_raw_tokens(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d,"JETON_BRUT")
            with patch.dict(m.PIECES,l,clear=True):
                with self.assertRaises(ValueError):m.examine_archive(f,c)
    def test_30_wrong_report_offset(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d,"AUTRE_OFFSET")
            with patch.dict(m.PIECES,l,clear=True):
                with self.assertRaises(ValueError):m.examine_archive(f,c)
    def test_31_no_partial_rows(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d,"SANS_POSITIONS")
            with patch.dict(m.PIECES,l,clear=True):
                with self.assertRaises(ValueError):m.examine_archive(f,c)
    def test_32_no_financial_conclusion(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d,"NON_CERTIFIE_FALSE")
            with patch.dict(m.PIECES,l,clear=True):
                with self.assertRaises(ValueError):m.examine_archive(f,c)
    def test_33_initial_must_be_neutral(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d,"INITIAL_FALSIFIE")
            with patch.dict(m.PIECES,l,clear=True):
                with self.assertRaises(ValueError):m.examine_archive(f,c)
    def test_34_invalid_utf8_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d,"NOT_JSON")
            with patch.dict(m.PIECES,l,clear=True):
                with self.assertRaises(ValueError):m.examine_archive(f,c)
    def test_35_no_rewrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"keep.json";p.write_text("PRESERVE",encoding="utf-8")
            self.assertEqual(m.main(["--bilan",str(p)]),2)
            self.assertEqual(p.read_text(encoding="utf-8"),"PRESERVE")
    def test_36_cli_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"bilan.json"
            self.assertEqual(m.main(["--bilan",str(file)]),0)
            self.assertEqual(json.loads(file.read_text(encoding="utf-8"))["positions_reverifiees_dans_cette_execution"],0)
    def test_37_cli_refuse_certification(self):self.assertEqual(m.main(["--exiger-certification"]),3)
    def test_38_cli_bad_archive(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"bad.zip";f.write_bytes(b"NOT A ZIP")
            self.assertEqual(m.main(["--archive",str(f)]),2)
    def test_39_no_same_output_as_input(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"input.zip";f.write_bytes(b"test")
            self.assertEqual(m.main(["--archive",str(f),"--bilan",str(f)]),2)
    def test_40_baseline_no_private_path(self):
        out=json.dumps(m.report(self.cfg))
        self.assertNotIn("source.zip",out)
    def test_41_archive_path_symlink_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,c,l=fixture(d)
            link=Path(d)/"alias.zip";link.symlink_to(f)
            with self.assertRaises(ValueError):m.examine_archive(link,c)

def guard(name):
    def test(self):self.assertTrue(self.cfg["protections"][name])
    return test
for n,key in enumerate(sorted(m.GUARDS),42):
    setattr(TestP54R,"test_%02d_guard"%n,guard(key))

if __name__=="__main__":
    unittest.main()
