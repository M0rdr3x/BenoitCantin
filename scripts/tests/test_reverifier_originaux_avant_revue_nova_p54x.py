#!/usr/bin/env python3
"""P54X — toutes les pièces de tests sont fictives et hors Git."""
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import reverifier_originaux_avant_revue_nova_p54x as m
from test_qualifier_occurrences_privees_nova_p54w import (
    source as fake_sheet,review as fake_review,examined as fake_examined)

def fixture(root,rows=None):
    root=Path(root)
    paths={}
    for name in ("ville","mamh"):
        path=root/(name+".pdf")
        path.write_bytes(("%PDF-SYNTHETIC-"+name).encode())
        paths[name]=path
    sheet=fake_sheet()
    sheet_path=root/"p54v.json"
    sheet_path.write_text(json.dumps(sheet),encoding="utf-8")
    os.chmod(sheet_path,0o600)
    original=sheet_path.read_bytes()
    doc=m.p54w.private_template(original)
    doc["declarations"]=list(rows or [])
    review_path=root/"p54w.json"
    review_path.write_text(json.dumps(doc),encoding="utf-8")
    os.chmod(review_path,0o600)
    verified={
      "bilans_figes_verifies":2,
      "positions_historiques_hachees":5,
      "positions_de_reference":m.p54w.p54v.p54t.p54r.known_rows(),
    }
    return paths,sheet_path,review_path,sheet,verified

def run_private(root,rows=None):
    paths,s,r,doc,verified=fixture(root,rows)
    with patch.object(m.p54w.p54v,"verify_local",return_value=(doc,verified)):
        return m.inspect_pair(paths,s,r)

class TestsP54X(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.configuration()

    def test_01_schema(self):self.assertEqual(self.cfg["schema_version"],"P54X-1")
    def test_02_source_exercice(self):self.assertEqual(self.cfg["source_exercice"],2024)
    def test_03_four_chained_jalons(self):
        self.assertEqual(self.cfg["source_jalons"],["P54Q","P54T","P54V","P54W"])
    def test_04_reference_run(self):self.assertEqual(self.cfg["source_run_p54p"],40151185184)
    def test_05_five_refs(self):self.assertEqual(len(self.cfg["references"]),5)
    def test_06_two_roles(self):self.assertEqual(len(self.cfg["roles"]),2)
    def test_07_requires_four_inputs(self):
        self.assertTrue(self.cfg["revue_privée_exige_quatre_fichiers"])
    def test_08_initial_pdf_zero(self):
        self.assertEqual(self.cfg["etat_initial"]["originaux_pdf_locaux_revus"],0)
    def test_09_neutral_five(self):
        r=m.public_report(self.cfg)
        self.assertEqual(len(r["occurrences"]),5)
        self.assertEqual(r["statuts_de_qualification"],{"NON_EXAMINE":5})
    def test_10_no_savings(self):
        self.assertIsNone(m.public_report(self.cfg)["economies_certifiees_cad"])
    def test_11_no_go(self):
        self.assertEqual(m.public_report(self.cfg)["decision"],m.NO_GO)
    def test_12_no_authenticated(self):
        self.assertEqual(m.public_report(self.cfg)["signatures_professionnelles_authentifiees"],0)
    def test_13_no_transmission(self):
        self.assertFalse(m.public_report(self.cfg)["pret_a_transmettre"])
    def test_14_no_merge(self):
        self.assertFalse(m.public_report(self.cfg)["fusion_main_autorisee"])
    def test_15_open_comparability(self):
        report=m.public_report(self.cfg)
        self.assertEqual((report["controles_p54b_non_attestes"],
                          report["controles_p54c_non_attestes"]),(96,8))
    def test_16_pending_human_review(self):
        self.assertEqual(m.public_report(self.cfg)["qualifications_humaines_certifiees"],0)
    def test_17_private_pair_test_fixture_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=run_private(tmp)
            self.assertEqual(state["statuts"],{"NON_EXAMINE":5})
    def test_18_pair_checked_count_only_when_both_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=run_private(tmp)
            public=m.public_report(self.cfg,state)
            self.assertEqual(public["copies_pdf_sha256_reverifiees"],2)
            self.assertTrue(public["revue_des_sources_originales_ce_run"])
            self.assertEqual(public["cinq_contextes_p54v_reconstruits"],5)
    def test_19_technical_success_no_professional_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=m.public_report(self.cfg,run_private(tmp))
            self.assertFalse(r["cloture_automatique_autorisee"])
            self.assertEqual(r["qualifications_humaines_certifiees"],0)
            self.assertIsNone(r["economies_certifiees_cad"])
    def test_20_declared_examination_not_certified(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=run_private(tmp,[fake_examined()])
            r=m.public_report(self.cfg,state)
            self.assertEqual(r["declarations_p54w_non_authentifiees"],1)
            self.assertEqual(r["statuts_de_qualification"],
                             {"NON_EXAMINE":4,"REVUE_PARTIELLE_NON_ATTESTEE":1})
            self.assertEqual(r["signatures_professionnelles_authentifiees"],0)
    def test_21_two_pseudonym_roles_not_independence(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=[fake_examined(),fake_examined(role="CONTRE_LECTEUR_DECLARE",
                  code="REV-TEST0002")]
            state=run_private(tmp,data)
            p=m.public_report(self.cfg,state)
            self.assertEqual(p["statuts_de_qualification"],
                             {"DEUX_REVUES_DECLARATIVES_NON_ATTESTEES":1,"NON_EXAMINE":4})
            self.assertEqual(p["qualifications_humaines_certifiees"],0)
    def test_22_suspension_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows=[fake_review(progress="SUSPENDU",reserve="SUSPENSION_DEMANDEE")]
            p=m.public_report(self.cfg,run_private(tmp,rows))
            self.assertEqual(p["statuts_de_qualification"]["SUSPENSION_MAINTENUE"],1)
    def test_23_conflict_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows=[fake_examined(reserve="CONTRADICTION_OUVERTE")]
            p=m.public_report(self.cfg,run_private(tmp,rows))
            self.assertEqual(p["statuts_de_qualification"]["CONTRADICTION_DECLAREE_NON_RESOLUE"],1)
    def test_24_private_text_not_in_public(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=run_private(tmp,[fake_examined()])
            visible=json.dumps(m.public_report(self.cfg,state))
            for forbidden in ("jeton_brut_STRICTEMENT_PRIVE",
                             "extrait_contextuel_STRICTEMENT_PRIVE",
                             "REV-TEST0001","hash256_fiche_p54v"):
                self.assertNotIn(forbidden,visible)
    def test_25_p54v_byte_change_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp)
            changed=copy.deepcopy(sheet)
            changed["occurrences"][0]["jeton_brut_STRICTEMENT_PRIVE"]="FAUX"
            s.write_text(json.dumps(changed),encoding="utf-8")
            with patch.object(m.p54w.p54v,"verify_local",return_value=(sheet,verified)):
                with self.assertRaises(ValueError):m.inspect_pair(paths,s,r)
    def test_26_p54v_changed_context_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp)
            changed=copy.deepcopy(sheet)
            changed["occurrences"][0]["extrait_contextuel_STRICTEMENT_PRIVE"]="FAUX"
            s.write_text(json.dumps(changed),encoding="utf-8")
            with patch.object(m.p54w.p54v,"verify_local",return_value=(sheet,verified)):
                with self.assertRaises(ValueError):m.inspect_pair(paths,s,r)
    def test_27_p54w_broken_digest_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp,[fake_examined()])
            d=json.loads(r.read_text("utf-8"))
            d["sha256_fiche_p54v"]="0"*64
            r.write_text(json.dumps(d),encoding="utf-8")
            with patch.object(m.p54w.p54v,"verify_local",return_value=(sheet,verified)):
                with self.assertRaises(ValueError):m.inspect_pair(paths,s,r)
    def test_28_review_forged_certificate_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            wrong=fake_examined()
            wrong["signature_professionnelle_authentifiee"]=True
            paths,s,r,sheet,verified=fixture(tmp,[wrong])
            with patch.object(m.p54w.p54v,"verify_local",return_value=(sheet,verified)):
                with self.assertRaises(ValueError):m.inspect_pair(paths,s,r)
    def test_29_absent_pdf_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp)
            paths["mamh"].unlink()
            with self.assertRaises((ValueError,OSError)):m.inspect_pair(paths,s,r)
    def test_30_duplicate_pdf_paths_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp)
            paths["mamh"]=paths["ville"]
            with self.assertRaises(ValueError):m.inspect_pair(paths,s,r)
    def test_31_pdf_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp)
            link=Path(tmp)/"pdf_link.pdf"
            link.symlink_to(paths["ville"])
            paths["ville"]=link
            with self.assertRaises(ValueError):m.inspect_pair(paths,s,r)
    def test_32_p54v_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp)
            link=Path(tmp)/"link.json";link.symlink_to(s)
            with self.assertRaises(ValueError):m.inspect_pair(paths,link,r)
    def test_33_p54v_permissions_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp)
            os.chmod(s,0o644)
            with self.assertRaises(ValueError):m.inspect_pair(paths,s,r)
    def test_34_review_permissions_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp)
            os.chmod(r,0o644)
            with self.assertRaises(ValueError):m.inspect_pair(paths,s,r)
    def test_35_distinct_source_file_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp)
            with self.assertRaises(ValueError):m.inspect_pair(paths,s,s)
    def test_36_frozen_archive_verification_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp)
            bad=copy.deepcopy(verified)
            bad["bilans_figes_verifies"]=0
            with patch.object(m.p54w.p54v,"verify_local",return_value=(sheet,bad)):
                with self.assertRaises(ValueError):m.inspect_pair(paths,s,r)
    def test_37_exact_five_positions_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp)
            bad=copy.deepcopy(verified)
            bad["positions_historiques_hachees"]=4
            with patch.object(m.p54w.p54v,"verify_local",return_value=(sheet,bad)):
                with self.assertRaises(ValueError):m.inspect_pair(paths,s,r)
    def test_38_cli_neutral(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"public.json"
            self.assertEqual(m.main(["--bilan-public",str(output)]),0)
            self.assertEqual(json.loads(output.read_text("utf-8"))[
                             "copies_pdf_sha256_reverifiees"],0)
    def test_39_cli_partial_inputs_rejected(self):
        self.assertEqual(m.main(["--pdf-ville","/tmp/nonexistent.pdf"]),2)
    def test_40_cli_go_always_refused(self):
        self.assertEqual(m.main(["--exiger-cloture"]),3)
    def test_41_cli_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/"public.json";f.write_text("KEEP",encoding="utf-8")
            self.assertEqual(m.main(["--bilan-public",str(f)]),2)
            self.assertEqual(f.read_text("utf-8"),"KEEP")
    def test_42_cli_pdf_group_complete_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp,[fake_examined()])
            dest=Path(tmp)/"public.json"
            with patch.object(m.p54w.p54v,"verify_local",return_value=(sheet,verified)):
                code=m.main(["--pdf-ville",str(paths["ville"]),
                             "--pdf-mamh",str(paths["mamh"]),
                             "--fiche-privee-p54v",str(s),
                             "--revues-privees-p54w",str(r),
                             "--bilan-public",str(dest)])
            self.assertEqual(code,0)
            self.assertEqual(json.loads(dest.read_text("utf-8"))[
                             "declarations_p54w_non_authentifiees"],1)
    def test_43_cli_bad_doc_raises_no_private_text_on_stderr(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths,s,r,sheet,verified=fixture(tmp)
            s.write_text("secret_jeton_invalid_json",encoding="utf-8")
            from contextlib import redirect_stderr
            from io import StringIO
            buf=StringIO()
            with patch.object(m.p54w.p54v,"verify_local",return_value=(sheet,verified)),redirect_stderr(buf):
                code=m.main(["--pdf-ville",str(paths["ville"]),
                             "--pdf-mamh",str(paths["mamh"]),
                             "--fiche-privee-p54v",str(s),
                             "--revues-privees-p54w",str(r)])
            self.assertEqual(code,2)
            self.assertNotIn("secret_jeton",buf.getvalue())
    def test_44_no_network_in_module(self):
        import inspect
        src=inspect.getsource(m)
        for name in ("urllib.request","requests.get","http.client","subprocess.run"):
            self.assertNotIn(name,src)

def guard_case(name):
    def guard(self):self.assertTrue(self.cfg["protections"][name])
    return guard
for number,name in enumerate(sorted(m.PROTECTIONS),45):
    setattr(TestsP54X,"test_%02d_guard"%number,guard_case(name))

if __name__=="__main__":
    unittest.main()
