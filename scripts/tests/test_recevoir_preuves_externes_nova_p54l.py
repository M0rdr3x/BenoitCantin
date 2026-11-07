#!/usr/bin/env python3
"""P54L : preuves synthétiques, aucune authentification d'expert réelle."""
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import recevoir_preuves_externes_nova_p54l as m
from test_verifier_habilitations_signatures_nova_p54k import (
    synthetic as prior_fixture, row as prior_row)

CITY="P54E-V-001"
MINISTRY="P54E-M-001"
CPA="MANDAT-COMPTABLE-2024"
LAW="MANDAT-JURIDIQUE-2024"

def setup(directory,reserve="AUCUNE_DECLAREE_NON_VERIFIEE"):
    fi,fj,k,mi,opinions,ri,rj=prior_fixture(directory,reserve=reserve)
    k["declarations"]=[prior_row()]
    fk=Path(directory)/"p54k.json"
    fk.write_text(json.dumps(k),encoding="utf-8")
    os.chmod(fk,0o600)
    raw,reviewed,upstream=m.load_chain(str(fi),str(fj),str(fk))
    f=Path(directory)/"p54l.json"
    doc=m.private_template(*raw)
    f.write_text(json.dumps(doc),encoding="utf-8")
    os.chmod(f,0o600)
    return (fi,fj,fk),raw,reviewed,upstream,f,doc

def observation(case=CITY,mandate=CPA,category="TABLEAU_PROFESSIONNEL",
                quality="PIECE_LOCALE_NON_AUTHENTIFIEE",proof="PIECE-002"):
    return {
        "dossier_id":case,"mandat":mandate,"categorie":category,
        "qualification_declaree":quality,"piece_referencee":proof,
        "authenticite_source_verifiee":False,
        "signature_officielle_authentifiee":False,
        "statut_ordre_certifie":False,
        "absence_conflit_certifiee":False,
        "decision_institutionnelle_autorisee":False,
    }

def proof(directory,doc,name="attestation_test.bin",ident="PIECE-002"):
    data=b"PIECE FICTIVE TEST SANS STATUT PROFESSIONNEL"
    path=Path(directory)/"preuves"/name
    path.write_bytes(data);os.chmod(path,0o600)
    doc["pieces"].append({
        "id":ident,"type":"PIECE_JUSTIFICATIVE_PRIVEE",
        "relative_path":"preuves/"+name,
        "sha256":hashlib.sha256(data).hexdigest()})
    return path

class TestP54L(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cfg=m.config()

    def test_01_schema(self):self.assertEqual(self.cfg["schema_version"],"P54L-1")
    def test_02_exercice(self):self.assertEqual(self.cfg["exercice"],2024)
    def test_03_parent(self):self.assertEqual(self.cfg["source_jalon"],"P54K")
    def test_04_sources(self):self.assertEqual(self.cfg["ancrage_p54d_run"],40120462237)
    def test_05_mandats(self):self.assertEqual(len(self.cfg["mandats"]),2)
    def test_06_dossiers(self):self.assertEqual(len(self.cfg["dossiers"]),4)
    def test_07_types(self):self.assertEqual(len(self.cfg["categories"]),4)
    def test_08_vocabulaire(self):self.assertEqual(len(m.QUALIFS),4)
    def test_09_baseline(self):
        self.assertEqual(m.report(self.cfg)["etats"],{"AUCUNE_PIECE_LOCALE":4})
    def test_10_baseline_no_go(self):self.assertEqual(m.report(self.cfg)["decision"],m.NO_GO)
    def test_11_no_signature(self):self.assertEqual(m.report(self.cfg)["signatures_professionnelles_authentifiees"],0)
    def test_12_no_conclusions(self):self.assertEqual(m.report(self.cfg)["avis_professionnels_certifies"],0)
    def test_13_no_savings(self):self.assertIsNone(m.report(self.cfg)["economies_certifiees_cad"])
    def test_14_no_jobs_cuts(self):self.assertFalse(m.report(self.cfg)["effectifs_services_reduits_autorises"])
    def test_15_no_main_merge(self):self.assertFalse(m.report(self.cfg)["fusion_main_autorisee"])
    def test_16_old_checks_open(self):
        self.assertEqual((m.report(self.cfg)["controles_p54b_restants"],
                          m.report(self.cfg)["controles_p54c_restants"]),(96,8))
    def test_17_template_zero_digest(self):
        self.assertEqual(m.private_template()["sha256_fiche_p54k"],"0"*64)
    def test_18_full_source_chain_real_synthetic_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            self.assertEqual(len(raw),3)
            self.assertEqual(len(rev),1)
            self.assertEqual(up[CITY],"REVUE_PARTIELLE_NON_AUTHENTIFIEE")
    def test_19_empty_private_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            r=m.validate_evidence(doc,f,*raw,rev)
            self.assertEqual(r["pieces_verifiees"],0)
            self.assertEqual(r["observations_recues"],0)
    def test_20_one_real_sha_document_is_untrusted(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            proof(d,doc)
            doc["observations"]=[observation()]
            checked=m.validate_evidence(doc,f,*raw,rev)
            result=m.report(self.cfg,checked,up)
            self.assertEqual(result["etats"]["PIECES_LOCALES_A_AUTHENTIFIER"],1)
            self.assertEqual(result["signatures_professionnelles_authentifiees"],0)
    def test_21_suspension_without_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            doc["observations"]=[observation(quality="SUSPENSION_EXPLICITE",proof=None)]
            checked=m.validate_evidence(doc,f,*raw,rev)
            self.assertEqual(m.report(self.cfg,checked,up)["etats"]["SUSPENSION_PRIORITAIRE"],1)
    def test_22_upstream_suspend_cannot_downgrade(self):
        self.assertEqual(m.case_matrix(None,{CITY:"SUSPENSION_PRIORITAIRE"})[1]["SUSPENSION_PRIORITAIRE"],1)
    def test_23_upstream_conflict_cannot_downgrade(self):
        self.assertEqual(m.case_matrix(None,{CITY:"CONTRADICTION_OUVERTE"})[1]["CONTRADICTION_OUVERTE"],1)
    def test_24_upstream_reserve_cannot_downgrade(self):
        self.assertEqual(m.case_matrix(None,{CITY:"RESERVE_OUVERTE"})[1]["RESERVE_OUVERTE"],1)
    def test_25_local_reserve(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            doc["observations"]=[observation(quality="RESERVE_EXPLICITE",proof=None)]
            self.assertEqual(m.report(self.cfg,m.validate_evidence(doc,f,*raw,rev),up)["etats"]["RESERVE_OUVERTE"],1)
    def test_26_unreferenced_piece_refused(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            proof(d,doc)
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_27_corrupt_sha_refused(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            proof(d,doc);doc["pieces"][0]["sha256"]="0"*64
            doc["observations"]=[observation()]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_28_changed_file_refused(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            file=proof(d,doc);file.write_bytes(b"MODIFICATION")
            doc["observations"]=[observation()]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_29_wrong_sha_p54i(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            doc["sha256_fiche_p54i"]="0"*64
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_30_wrong_sha_p54j(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            doc["sha256_fiche_p54j"]="0"*64
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_31_wrong_sha_p54k(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            doc["sha256_fiche_p54k"]="0"*64
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_32_wrong_scope(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            doc["observations"]=[observation(case=MINISTRY,quality="A_VERIFIER",proof=None)]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_33_wrong_mandate(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            doc["observations"]=[observation(mandate=LAW,quality="A_VERIFIER",proof=None)]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_34_unknown_category(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            doc["observations"]=[observation(category="GO_AUTOMATIQUE",quality="A_VERIFIER",proof=None)]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_35_duplicate_category_case_mandate(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            x=observation(quality="A_VERIFIER",proof=None)
            doc["observations"]=[x,copy.deepcopy(x)]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_36_unknown_proof_id(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            doc["observations"]=[observation()]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_37_no_proof_but_claim_it_exists(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            doc["observations"]=[observation(proof=None)]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_38_fake_licensed(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            x=observation(quality="A_VERIFIER",proof=None);x["statut_ordre_certifie"]=True
            doc["observations"]=[x]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_39_fake_signature(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            x=observation(quality="A_VERIFIER",proof=None);x["signature_officielle_authentifiee"]=True
            doc["observations"]=[x]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_40_fake_approval(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            x=observation(quality="A_VERIFIER",proof=None);x["decision_institutionnelle_autorisee"]=True
            doc["observations"]=[x]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_41_extra_free_text(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            x=observation(quality="A_VERIFIER",proof=None);x["nom_professionnel"]="PRIVE"
            doc["observations"]=[x]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_42_reused_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            proof(d,doc)
            doc["observations"]=[observation(),observation(category="AUTHENTICITE_SIGNATURE")]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_43_wrong_type(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            proof(d,doc);doc["pieces"][0]["type"]="AVIS_PROFESSIONNEL_NON_ATTESTE"
            doc["observations"]=[observation()]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_44_file_public_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            file=proof(d,doc);os.chmod(file,0o644)
            doc["observations"]=[observation()]
            with self.assertRaises(ValueError):m.validate_evidence(doc,f,*raw,rev)
    def test_45_no_identifiers_in_public(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            proof(d,doc);doc["observations"]=[observation()]
            summary=json.dumps(m.report(self.cfg,m.validate_evidence(doc,f,*raw,rev),up))
            for forbidden in (doc["pieces"][0]["sha256"],"attestation_test.bin",
                              "sha256_fiche_p54i","PIECE-002"):
                self.assertNotIn(forbidden,summary)
    def test_46_cli_initial_report(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"out.json"
            self.assertEqual(m.main(["--bilan",str(path)]),0)
            self.assertEqual(json.loads(path.read_text("utf-8"))["etats"],{"AUCUNE_PIECE_LOCALE":4})
    def test_47_cli_denies_authenticity(self):
        self.assertEqual(m.main(["--exiger-authenticite"]),3)
    def test_48_cli_requires_all_sources(self):
        self.assertEqual(m.main(["--p54i","/tmp/unknown.json"]),2)
    def test_49_cli_private_template_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/"private.json"
            self.assertEqual(m.main(["--modele-prive",str(dest)]),0)
            self.assertEqual(stat.S_IMODE(dest.stat().st_mode),0o600)
    def test_50_cli_reuses_real_chain(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            proof(d,doc)
            doc["observations"]=[observation()]
            f.write_text(json.dumps(doc),"utf-8")
            out=Path(d)/"public.json"
            args=["--p54i",str(paths[0]),"--p54j",str(paths[1]),
                  "--p54k",str(paths[2]),"--pieces-locales",str(f),
                  "--bilan",str(out)]
            self.assertEqual(m.main(args),0)
            self.assertEqual(json.loads(out.read_text("utf-8"))["pieces_locales_integrite_seulement"],1)
    def test_51_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"out.json";out.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(out)]),2)
            self.assertEqual(out.read_text("utf-8"),"keep")
    def test_52_cli_no_public_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            os.chmod(f,0o644)
            self.assertEqual(m.main(["--p54i",str(paths[0]),
                  "--p54j",str(paths[1]),"--p54k",str(paths[2]),
                  "--pieces-locales",str(f)]),2)
    def test_53_cli_no_fake_sources(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,rev,up,f,doc=setup(d)
            paths[2].write_text("{}","utf-8")
            self.assertEqual(m.main(["--p54i",str(paths[0]),
                  "--p54j",str(paths[1]),"--p54k",str(paths[2])]),2)

def guard_factory(key):
    def check(self):self.assertTrue(self.cfg["protections"][key])
    return check
for index,key in enumerate(sorted(m.GUARDS),54):
    setattr(TestP54L,"test_%02d_protection"%index,guard_factory(key))

if __name__=="__main__":
    unittest.main()
