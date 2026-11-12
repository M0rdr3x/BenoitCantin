#!/usr/bin/env python3
"""P54I : tests synthétiques de réception technique, réserves et non-attestation."""
import copy
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import recevoir_mandats_et_avis_nova_p54i as m

def row(mandat="MANDAT-COMPTABLE-2024",docs=None,
        nature="AVIS_PROFESSIONNEL_NON_AUTHENTIFIE",
        reserve="AUCUNE_DECLAREE_NON_VERIFIEE"):
    return {
        "mandat":mandat,"code_reception":"REC-DEMO0001",
        "documents":list(docs or []),
        "nature_declaree":nature,"reserve_declaree":reserve,
        "portee_dossiers":["P54E-V-001"],
        "controles_declaratifs":[],
        "contact_effectif_verifie":False,
        "contrat_signe_authentifie":False,
        "signature_avis_authentifiee":False,
        "independance_verifiee":False,
        "montant_financier_certifie":False,
    }

def fixture(directory,kind="AVIS_PROFESSIONNEL_NON_ATTESTE"):
    root=Path(directory)
    folder=root/"preuves";folder.mkdir(exist_ok=True)
    file=folder/"test.bin";data=b"AVIS FICTIF TEST HORS DEPOT"
    file.write_bytes(data);os.chmod(file,0o600)
    manifest=root/"manifest.json"
    obj=m.local_template(m.configuration())
    obj["pieces"]=[{
        "id":"PIECE-001","type":kind,"relative_path":"preuves/test.bin",
        "sha256":sha256(data).hexdigest()}]
    manifest.write_text(json.dumps(obj),encoding="utf-8")
    os.chmod(manifest,0o600)
    return manifest,obj,file

class ReceptionP54I(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cfg=m.configuration()

    def test_01_source_year(self):self.assertEqual(self.cfg["exercice_source"],2024)
    def test_02_schema(self):self.assertEqual(self.cfg["schema_version"],"P54I-1")
    def test_03_parent(self):self.assertEqual(self.cfg["source_jalon"],"P54H")
    def test_04_two_mandates(self):self.assertEqual(len(self.cfg["mandats"]),2)
    def test_05_case_count(self):self.assertEqual(len(self.cfg["dossiers_source"]),4)
    def test_06_gate_count(self):self.assertEqual(len(m.GATES),10)
    def test_07_twenty_gates(self):self.assertEqual(len(m.GATES)*len(m.MANDATS),20)
    def test_08_safe_defaults(self):self.assertEqual(m.report(self.cfg)["statuts_locaux"],{"FICHIER_LOCAL_NON_RECU":2})
    def test_09_zero_originals(self):self.assertEqual(m.report(self.cfg)["avis_independants_signes_authentifies"],0)
    def test_10_zero_economy(self):self.assertIsNone(m.report(self.cfg)["economies_certifiees_cad"])
    def test_11_no_go(self):self.assertEqual(m.report(self.cfg)["decision"],m.NO_GO)
    def test_12_no_merge(self):self.assertFalse(m.report(self.cfg)["fusion_main_autorisee"])
    def test_13_96_unresolved(self):self.assertEqual(m.report(self.cfg)["controles_p54b_en_attente"],96)
    def test_14_8_unresolved(self):self.assertEqual(m.report(self.cfg)["controles_p54c_en_attente"],8)
    def test_15_initial_template(self):self.assertEqual(m.local_template(self.cfg)["pieces"],[])
    def test_16_empty_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"manifest.json";v=m.local_template(self.cfg)
            f.write_text(json.dumps(v),"utf-8");os.chmod(f,0o600)
            r=m.validate_private(v,f,self.cfg)
            self.assertEqual(r["pieces_locales_integrite_verifiee"],0)
            self.assertEqual(r["etats"],{"FICHIER_LOCAL_NON_RECU":2})
    def test_17_real_sha_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["receptions"]=[row(docs=["PIECE-001"])]
            a=m.validate_private(v,f,self.cfg)
            self.assertEqual(a["pieces_locales_integrite_verifiee"],1)
            self.assertEqual(a["etats"]["FICHIER_LOCAL_INTEGRE_NON_AUTHENTIFIE"],1)
    def test_18_not_authenticated_even_with_hash(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["receptions"]=[row(docs=["PIECE-001"])]
            result=m.report(self.cfg,m.validate_private(v,f,self.cfg))
            self.assertEqual(result["avis_independants_signes_authentifies"],0)
            self.assertEqual(result["mandats_reellement_authentifies"],0)
    def test_19_reserved_file(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["receptions"]=[row(docs=["PIECE-001"],reserve="SIGNATURE_A_VERIFIER")]
            r=m.validate_private(v,f,self.cfg)
            self.assertEqual(r["etats"]["RESERVE_OUVERTE"],1)
    def test_20_explicit_suspension_no_file(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["pieces"]=[]
            v["receptions"]=[row(reserve="SUSPENSION_EXPLICITE")]
            r=m.validate_private(v,f,self.cfg)
            self.assertEqual(r["etats"]["SUSPENDU"],1)
    def test_21_explicit_suspension_with_file(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["receptions"]=[row(docs=["PIECE-001"],reserve="SUSPENSION_EXPLICITE")]
            self.assertEqual(m.validate_private(v,f,self.cfg)["etats"]["SUSPENDU"],1)
    def test_22_no_file_state(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["pieces"]=[];v["receptions"]=[row()]
            self.assertEqual(m.validate_private(v,f,self.cfg)["etats"]["FICHIER_LOCAL_NON_RECU"],2)
    def test_23_document_count(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["receptions"]=[row(docs=["PIECE-001"])]
            s=m.validate_private(v,f,self.cfg)
            self.assertEqual(s["mandats"][0]["nb_pieces_locales_verifiees_par_hachage"],1)
    def test_24_bad_digest_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["pieces"][0]["sha256"]="0"*64
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_25_tampered_file_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);b.write_bytes(b"changed bytes")
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_26_other_permissions_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);os.chmod(b,0o644)
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_27_symlink_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);link=Path(d)/"preuves"/"link.bin"
            link.symlink_to("test.bin");v["pieces"][0]["relative_path"]="preuves/link.bin"
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_28_traversal_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["pieces"][0]["relative_path"]="preuves/../manifest.json"
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_29_wrong_kind_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d,kind="NOTE_ANALYSE_PRIVEE");v["receptions"]=[row(docs=["PIECE-001"])]
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_30_mandate_document_consistent(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d,kind="PIECE_JUSTIFICATIVE_PRIVEE")
            v["receptions"]=[row(docs=["PIECE-001"],nature="DOCUMENT_MANDAT_DECLARATIF")]
            self.assertEqual(m.validate_private(v,f,self.cfg)["declarations_de_reception"],1)
    def test_31_fake_signature_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);r=row(docs=["PIECE-001"]);r["signature_avis_authentifiee"]=True;v["receptions"]=[r]
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_32_fake_contract_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);r=row();r["contrat_signe_authentifie"]=True;v["receptions"]=[r]
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_33_fake_independence_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);r=row();r["independance_verifiee"]=True;v["receptions"]=[r]
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_34_fake_money_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);r=row();r["montant_financier_certifie"]=True;v["receptions"]=[r]
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_35_fake_contact_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);r=row();r["contact_effectif_verifie"]=True;v["receptions"]=[r]
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_36_private_text_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);r=row();r["nom_expert"]="Test";v["receptions"]=[r]
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_37_duplicated_mandate_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["receptions"]=[row(),row()]
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_38_same_evidence_twice_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["receptions"]=[
                row(docs=["PIECE-001"]),
                row(mandat="MANDAT-JURIDIQUE-2024",docs=["PIECE-001"])]
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_39_duplicate_checks_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);r=row();r["controles_declaratifs"]=[m.GATES[0]]*2;v["receptions"]=[r]
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_40_bad_scope_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);r=row();r["portee_dossiers"]=["P54E-Z-999"];v["receptions"]=[r]
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_41_unknown_mandate_denied(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["receptions"]=[row(mandat="MANDAT-FAUX")]
            with self.assertRaises(ValueError):m.validate_private(v,f,self.cfg)
    def test_42_no_private_hash_in_summary(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["receptions"]=[row(docs=["PIECE-001"])]
            s=json.dumps(m.report(self.cfg,m.validate_private(v,f,self.cfg)))
            self.assertNotIn(v["pieces"][0]["sha256"],s)
            self.assertNotIn("test.bin",s)
            self.assertNotIn("REC-DEMO0001",s)
    def test_43_cli_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"bilan.json"
            self.assertEqual(m.main(["--bilan",str(path)]),0)
            self.assertEqual(json.loads(path.read_text("utf-8"))["statuts_locaux"],{"FICHIER_LOCAL_NON_RECU":2})
    def test_44_cli_private_template(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"private.json"
            self.assertEqual(m.main(["--modele-prive",str(p)]),0)
            self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600)
    def test_45_cli_strict_refuses(self):
        self.assertEqual(m.main(["--exiger-authenticite-certifiee"]),3)
    def test_46_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"report.json";p.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(p)]),2)
            self.assertEqual(p.read_text("utf-8"),"keep")
    def test_47_cli_real_synthetic_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["receptions"]=[row(docs=["PIECE-001"])]
            f.write_text(json.dumps(v),"utf-8")
            out=Path(d)/"public.json"
            self.assertEqual(m.main(["--fiche-locale",str(f),"--bilan",str(out)]),0)
            self.assertEqual(json.loads(out.read_text("utf-8"))["pieces_locales_integrite_seulement"],1)
    def test_48_cli_reject_public_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);os.chmod(f,0o644)
            self.assertEqual(m.main(["--fiche-locale",str(f)]),2)
    def test_49_no_green_even_with_expert_file(self):
        with tempfile.TemporaryDirectory() as d:
            f,v,b=fixture(d);v["receptions"]=[row(docs=["PIECE-001"])]
            outcome=m.report(self.cfg,m.validate_private(v,f,self.cfg))
            self.assertFalse(outcome["fusion_main_autorisee"])
            self.assertEqual(outcome["dossiers_clos"],0)
    def test_50_explicit_no_external_contact(self):
        self.assertTrue(self.cfg["protections"]["aucun_contact_ou_mandat_reel_pretendu"])

def guard_test(name):
    def one(self):
        self.assertTrue(self.cfg["protections"][name])
    return one
for i,name in enumerate(sorted(m.GUARDS),51):
    setattr(ReceptionP54I,"test_%02d_protection"%i,guard_test(name))

if __name__=="__main__":
    unittest.main()
