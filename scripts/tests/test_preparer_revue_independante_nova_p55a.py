import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import preparer_revue_independante_nova_p55a as m

class TestP55A(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=m.configuration()
    def setUp(self):
        self.upstream=m.p54z.blank_model()
        self.sha="a"*64
        self.local=m.model(self.sha)
    def prepared(self):
        for row in self.upstream["dossiers"]:
            for check in row["controles"]:
                check["etat"]="PREPARATION_DECLAREE_NON_VERIFIEE"
        return self.upstream
    def test_01_config(self):self.assertEqual(self.config["schema_version"],"P55A-1")
    def test_02_2024(self):self.assertEqual(self.config["exercice_source"],2024)
    def test_03_references(self):self.assertEqual(len(m.REFS),5)
    def test_04_gates(self):self.assertEqual(len(m.GATES),10)
    def test_05_count(self):self.assertEqual(sum(len(x["verifications"]) for x in self.local["dossiers"]),50)
    def test_06_protections(self):self.assertTrue(all(self.config["protections"].values()))
    def test_07_default(self):self.assertEqual(m.validate_local(self.local,self.upstream,self.sha)[0]["NON_INSTRUIT"],50)
    def test_08_no_go(self):self.assertEqual(m.report()["decision"],m.NO_GO)
    def test_09_money(self):self.assertIsNone(m.report()["economies_certifiees_cad"])
    def test_10_no_cert_expert(self):self.assertEqual(m.report()["avis_independants_authentifies"],0)
    def test_11_no_names(self):self.assertNotIn("identite",json.dumps(self.local).lower())
    def test_12_no_signature(self):self.assertNotIn("signature",json.dumps(self.local).lower())
    def test_13_no_go_sent(self):self.assertFalse(m.report()["autorisation_envoi_externe"])
    def test_14_no_go_close(self):self.assertFalse(m.report()["autorisation_fermeture_dossier"])
    def test_15_no_go_merge(self):self.assertFalse(m.report()["autorisation_fusion_main"])
    def test_16_inherited_stop(self):
        self.upstream["dossiers"][0]["controles"][0]["etat"]="SUSPENDU"
        self.assertEqual(m.validate_local(self.local,self.upstream,self.sha)[1],1)
    def test_17_inherited_priority(self):
        self.upstream["dossiers"][0]["controles"][0]["etat"]="SUSPENDU"
        t,s=m.validate_local(self.local,self.upstream,self.sha)
        self.assertEqual(m.report(t,s)["suspensions_p54z_heritees"],1)
    def test_18_status_prepared_rejected_without_p54z(self):
        self.local["dossiers"][0]["verifications"][0]["etat"]="PREPARE_NON_ATTESTE"
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_19_preparation_with_upstream_accepted_without_cert(self):
        self.prepared()
        self.local["dossiers"][0]["verifications"][0]["etat"]="PREPARE_NON_ATTESTE"
        totals,n=m.validate_local(self.local,self.upstream,self.sha)
        self.assertEqual(totals["PREPARE_NON_ATTESTE"],1)
        self.assertEqual(m.report(totals,n)["avis_independants_authentifies"],0)
    def test_20_suspend(self):
        self.local["dossiers"][0]["verifications"][0]["etat"]="SUSPENDU"
        totals,n=m.validate_local(self.local,self.upstream,self.sha)
        self.assertEqual(m.report(totals,n)["suspensions_p55a_declarees"],1)
    def test_21_reserve(self):
        self.local["dossiers"][0]["verifications"][0]["etat"]="RESERVE"
        totals,n=m.validate_local(self.local,self.upstream,self.sha)
        self.assertEqual(m.report(totals,n)["reserves_p55a_ouvertes"],1)
    def test_22_invalid_status(self):
        self.local["dossiers"][0]["verifications"][0]["etat"]="CERTIFIE"
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_23_unlisted_gate(self):
        self.local["dossiers"][0]["verifications"][0]["code"]="GO"
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_24_missing_gate(self):
        self.local["dossiers"][0]["verifications"].pop()
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_25_missing_case(self):
        self.local["dossiers"].pop()
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_26_duplicate_case(self):
        self.local["dossiers"][1]["reference"]=m.REFS[0]
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_27_signature_injection(self):
        self.local["dossiers"][0]["signature"]="fake"
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_28_identity_injection(self):
        self.local["dossiers"][0]["verifications"][0]["reviewer"]="name"
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_29_wrong_hash(self):
        self.local["sha256_declarations_p54z"]="b"*64
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_30_no_hash(self):
        self.local.pop("sha256_declarations_p54z")
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_31_2026_rejected(self):
        self.local["exercice"]=2026
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_32_boolean_year(self):
        self.local["exercice"]=True
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_33_invalid_model_sha(self):
        with self.assertRaises(ValueError):m.model("X"*64)
    def test_34_invalid_counter(self):
        with self.assertRaises(ValueError):m.report({"NON_INSTRUIT":50})
    def test_35_bad_inherited(self):
        with self.assertRaises(ValueError):m.report(inherited=41)
    def test_36_clean_public_report(self):
        d=json.dumps(m.report())
        self.assertNotIn(self.sha,d)
        self.assertNotIn("P54E-V-001",d)
    def test_37_read_write_private(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"src.json"
            m.p54z.write_new(p,self.upstream,private=True)
            doc,sha=m.upstream(p)
            self.assertEqual(doc,self.upstream)
            self.assertEqual(len(sha),64)
    def test_38_parent_path_symlink(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"source.json"
            m.p54z.write_new(p,self.upstream,private=True)
            alias=Path(t)/"alias";alias.symlink_to(t,target_is_directory=True)
            with self.assertRaises(ValueError):m.private_source(alias/"source.json")
    def test_39_invalid_perms(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"source.json";p.write_text(json.dumps(self.upstream))
            p.chmod(0o644)
            with self.assertRaises(ValueError):m.upstream(p)
    def test_40_public_cli(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/"bil.json"
            self.assertEqual(m.main(["--bilan-public",str(out)]),0)
            self.assertEqual(json.loads(out.read_text())["decision"],m.NO_GO)
    def test_41_cli_go_blocked(self):
        self.assertEqual(m.main(["--exiger-go"]),3)
    def test_42_cli_missing_source(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(m.main(["--creer-modele-prive",str(Path(t)/"local.json")]),2)
    def test_43_cli_source_and_model(self):
        with tempfile.TemporaryDirectory() as t:
            src=Path(t)/"src.json"
            dst=Path(t)/"local.json"
            m.p54z.write_new(src,self.upstream,private=True)
            self.assertEqual(m.main(["--declarations-p54z",str(src),"--creer-modele-prive",str(dst)]),0)
            self.assertEqual(dst.stat().st_mode&0o777,0o600)
    def test_44_cli_connected_relecture(self):
        with tempfile.TemporaryDirectory() as t:
            src=Path(t)/"src.json"
            local=Path(t)/"local.json"
            m.p54z.write_new(src,self.upstream,private=True)
            _doc,sha=m.upstream(src)
            m.p54z.write_new(local,m.model(sha),private=True)
            self.assertEqual(m.main(["--declarations-p54z",str(src),"--relecture-locale",str(local)]),0)
    def test_45_unrecognized_free_text(self):
        self.local["dossiers"][0]["verifications"][0]["comment"]="secret"
        with self.assertRaises(ValueError):m.validate_local(self.local,self.upstream,self.sha)
    def test_46_original_unchanged(self):
        self.assertEqual(self.config["etat_initial"]["economies_certifiees_cad"],None)
    def test_47_unverified_workflows(self):
        self.assertFalse(m.report()["independance_experts_authentifiee"])
    def test_48_no_cas_clos(self):
        self.assertEqual(m.report()["qualifications_definitives"],0)
    def test_49_suspendue_transmise_sans_fiche_p55a(self):
        self.upstream["dossiers"][0]["controles"][0]["etat"]="SUSPENDU"
        with tempfile.TemporaryDirectory() as t:
            src=Path(t)/"src.json"; out=Path(t)/"bilan.json"
            m.p54z.write_new(src,self.upstream,private=True)
            self.assertEqual(m.main(["--declarations-p54z",str(src),
                                     "--bilan-public",str(out)]),0)
            self.assertEqual(json.loads(out.read_text())["suspensions_p54z_heritees"],1)


if __name__=="__main__":
    unittest.main()
