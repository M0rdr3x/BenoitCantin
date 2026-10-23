#!/usr/bin/env python3
"""P53T : contrôles locaux d'intégrité, sans données confidentielles ni certification."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verifier_integrite_locale_nova_p53t as m

BODY=b"jeu synthétique sans information gouvernementale\n"
HASH=hashlib.sha256(BODY).hexdigest()

def evidence(code="66023",typ=None,rel="synthetique.txt"):
    return {
      "code_organisme":code,
      "type_piece":typ or m.p53q.DOCUMENTS[0],
      "categorie_justificatif":"PIECE_FINANCIERE",
      "fichier_relatif":rel,
      "sha256_reference":HASH,
      "date_capture_declaree_utc":"2026-10-22T14:00:00Z",
      "role_collecte":"COLLECTE_DOCUMENTAIRE",
      "role_relecture":"CONTROLE_TECHNIQUE",
      "droits_acces":"PUBLIC",
      "origine_declaree":"INCONNUE",
      "journal_declare":[
        {"action":"RECEPTION","role":"COLLECTE_DOCUMENTAIRE",
         "date_utc":"2026-10-22T14:00:00Z","but":"RECEPTION"},
        {"action":"CONSULTATION","role":"CONTROLE_TECHNIQUE",
         "date_utc":"2026-10-22T15:00:00Z","but":"CONTROLE"},
      ],
    }
def setup_tmp():
    dir=tempfile.TemporaryDirectory()
    p=Path(dir.name);(p/"synthetique.txt").write_bytes(BODY)
    return dir,p

class CheckP53T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.q_cfg,cls.parents=m.setup()
        cls.rows=m.inventory(cls.q_cfg,cls.parents)
    def test_01_six_dossiers(self):self.assertEqual(len(self.parents),6)
    def test_02_102_slots(self):self.assertEqual(len(self.rows),102)
    def test_03_unique_slots(self):self.assertEqual(len({(r["code_organisme"],r["type_piece"]) for r in self.rows}),102)
    def test_04_missing(self):self.assertTrue(all(r["statut"]=="NON_PRESENTE" for r in self.rows))
    def test_05_no_hash_assumed(self):self.assertTrue(all(not r["empreinte_locale_verifiee"] for r in self.rows))
    def test_06_no_provenance(self):self.assertTrue(all(not r["provenance_authentifiee"] for r in self.rows))
    def test_07_no_independent_review(self):self.assertTrue(all(not r["independance_revue_validee"] for r in self.rows))
    def test_08_no_savings(self):self.assertTrue(all(r["economie_certifiee_cad"] is None for r in self.rows))
    def test_09_no_sensitive_files(self):self.assertTrue(all(not r["piece_confidentielle_dans_git"] for r in self.rows))
    def test_10_all_6_codes(self):self.assertEqual(set(r["code_organisme"] for r in self.rows),set(m.CODE))
    def test_11_17_per_code(self):self.assertTrue(all(sum(r["code_organisme"]==code for r in self.rows)==17 for code in m.CODE))
    def test_12_no_go_initial(self):self.assertEqual(m.result(self.cfg,self.rows,{"enregistrements_exam":0,"statuts_techniques":{}})["decision"],"NO_GO_AUTOMATIQUE")
    def test_13_metadata_valid(self):self.assertEqual(m.metadata(evidence()),("66023",m.p53q.DOCUMENTS[0]))
    def test_14_sha_match(self):
        tmp,p=setup_tmp()
        with tmp:
            x=m.check_local(p,[evidence()])
            self.assertEqual(x["statuts_techniques"]["CONCORDANCE_OCTETS_LOCAUX_NON_AUTHENTIFICATION"],1)
            self.assertEqual(x["authentifications_provenance"],0)
    def test_15_sha_mismatch_is_observed_not_certified(self):
        tmp,p=setup_tmp()
        with tmp:
            e=evidence();e["sha256_reference"]="a"*64
            if e["sha256_reference"]==HASH:e["sha256_reference"]="b"*64
            x=m.check_local(p,[e])
            self.assertEqual(x["statuts_techniques"]["ECHEC_CONTROLE_OCTETS"],1)
    def test_16_different_codes_allowed(self):
        tmp,p=setup_tmp()
        with tmp:
            x=m.check_local(p,[evidence(),evidence("T1025")])
            self.assertEqual(x["enregistrements_exam"],2)
    def test_17_same_doc_type_diff_organism(self):
        tmp,p=setup_tmp()
        with tmp:
            x=m.check_local(p,[evidence("66023"),evidence("T1025")])
            self.assertEqual(x["pieces_uniques_declares"],2)
    def test_18_duplicate_blocked(self):
        tmp,p=setup_tmp()
        with tmp:
            with self.assertRaises(ValueError):m.check_local(p,[evidence(),evidence()])
    def test_19_unknown_code(self):
        e=evidence("INVALID")
        with self.assertRaises(ValueError):m.metadata(e)
    def test_20_unknown_type(self):
        e=evidence();e["type_piece"]="INVALID"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_21_extra_sensitive_field(self):
        e=evidence();e["nom_employe"]="secret"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_22_hash_wrong_size(self):
        e=evidence();e["sha256_reference"]="abc"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_23_hash_uppercase_denied(self):
        e=evidence();e["sha256_reference"]="A"*64
        with self.assertRaises(ValueError):m.metadata(e)
    def test_24_claim_origin_authenticated_denied(self):
        e=evidence();e["origine_declaree"]="OFFICIELLE_CERTIFIEE"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_25_claim_independent_role_same(self):
        e=evidence();e["role_relecture"]=e["role_collecte"]
        with self.assertRaises(ValueError):m.metadata(e)
    def test_26_fake_role_person_name(self):
        e=evidence();e["role_collecte"]="Nom et prenom"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_27_missing_log(self):
        e=evidence();e["journal_declare"]=[]
        with self.assertRaises(ValueError):m.metadata(e)
    def test_28_missing_review_role(self):
        e=evidence();e["journal_declare"]=e["journal_declare"][:1]
        with self.assertRaises(ValueError):m.metadata(e)
    def test_29_wrong_first_event(self):
        e=evidence();e["journal_declare"][0]["action"]="TRANSFERT"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_30_wrong_first_role(self):
        e=evidence();e["journal_declare"][0]["role"]="CONTROLE_TECHNIQUE"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_31_backwards_time(self):
        e=evidence();e["journal_declare"][1]["date_utc"]="2026-10-22T13:00:00Z"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_32_wrong_z_time(self):
        e=evidence();e["date_capture_declaree_utc"]="2026-10-22 14:00"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_33_wrong_clock(self):
        e=evidence();e["date_capture_declaree_utc"]="2026-02-30T14:00:00Z"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_34_before_reference(self):
        e=evidence();e["date_capture_declaree_utc"]="2023-12-31T14:00:00Z"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_35_wrong_journal_operation(self):
        e=evidence();e["journal_declare"][1]["action"]="SIGNATURE_CERTIFIEE"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_36_custody_extra_private_data(self):
        e=evidence();e["journal_declare"][1]["courriel"]="test@example.invalid"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_37_dir_traversal(self):
        e=evidence(rel="../out.txt")
        with self.assertRaises(ValueError):m.metadata(e)
    def test_38_absolute_path(self):
        e=evidence(rel="/tmp/foo.txt")
        with self.assertRaises(ValueError):m.metadata(e)
    def test_39_backslash(self):
        e=evidence(rel="safe\\bad.txt")
        with self.assertRaises(ValueError):m.metadata(e)
    def test_40_html_path(self):
        e=evidence(rel="test.html")
        with self.assertRaises(ValueError):m.metadata(e)
    def test_41_symlink_denied(self):
        tmp,p=setup_tmp()
        with tmp:
            (p/"link.txt").symlink_to(p/"synthetique.txt")
            with self.assertRaises(ValueError):m.check_local(p,[evidence(rel="link.txt")])
    def test_42_missing_file(self):
        tmp,p=setup_tmp()
        with tmp:
            with self.assertRaises(OSError):m.check_local(p,[evidence(rel="missing.txt")])
    def test_43_restricted_skips_file(self):
        tmp,p=setup_tmp()
        with tmp:
            e=evidence(rel="missing.txt");e["droits_acces"]="RESTREINT"
            x=m.check_local(p,[e])
            self.assertEqual(x["statuts_techniques"]["ACCES_RESTREINT_NON_TRAITE"],1)
    def test_44_large_file_denied(self):
        tmp,p=setup_tmp()
        with tmp:
            (p/"large.txt").write_bytes(b"x"*(m.MAX_FILE+1))
            with self.assertRaises(ValueError):m.check_local(p,[evidence(rel="large.txt")])
    def test_45_invalid_access(self):
        e=evidence();e["droits_acces"]="AUTORISE_CERTIFIE"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_46_unknown_category(self):
        e=evidence();e["categorie_justificatif"]="ECONOMIES"
        with self.assertRaises(ValueError):m.metadata(e)
    def test_47_report_suppresses_hash_and_identifiers(self):
        tmp,p=setup_tmp()
        with tmp:
            control=m.check_local(p,[evidence()])
            report=m.result(self.cfg,self.rows,control)
            encoded=json.dumps(report)
            self.assertNotIn(HASH,encoded)
            self.assertNotIn("66023",encoded)
            self.assertNotIn("synthetique.txt",encoded)
    def test_48_cli_generates_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/"a.json",Path(tmp)/"b.json"
            self.assertEqual(m.main(["--bilan",str(a),"--inventaire",str(b)]),0)
            self.assertEqual(len(json.loads(b.read_text("utf-8"))["positions"]),102)
    def test_49_cli_local_manifest(self):
        tmp,p=setup_tmp()
        with tmp:
            manifest=p/"manifest.json"
            manifest.write_text(json.dumps({"schema_version":"P53T-MANIFESTE-1",
                                             "pieces":[evidence()]}),"utf-8")
            report=p/"report.json"
            self.assertEqual(m.main(["--manifeste",str(manifest),"--racine-preuves",
                                     str(p),"--bilan",str(report)]),0)
            d=json.loads(report.read_text("utf-8"))
            self.assertEqual(d["statuts_techniques_agreges"]["CONCORDANCE_OCTETS_LOCAUX_NON_AUTHENTIFICATION"],1)
            self.assertEqual(d["preuves_origine_certifiees"],0)
    def test_50_manifest_without_root(self):
        self.assertEqual(m.main(["--manifeste","test.json"]),2)
    def test_51_root_without_manifest(self):
        self.assertEqual(m.main(["--racine-preuves","/tmp"]),2)
    def test_52_strict_never_certify(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(m.main(["--exiger-authentification-ou-economie",
                                     "--bilan",str(Path(tmp)/"out.json")]),3)
    def test_53_outputs_same_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"out.json"
            self.assertEqual(m.main(["--bilan",str(p),"--inventaire",str(p)]),2)
    def test_54_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,q=Path(tmp)/"p.json",Path(tmp)/"q.json"
            q.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(p),"--inventaire",str(q)]),2)
            self.assertFalse(p.exists())
    def test_55_no_savings_after_hash_match(self):
        tmp,p=setup_tmp()
        with tmp:
            control=m.check_local(p,[evidence()])
            s=m.result(self.cfg,self.rows,control)
            self.assertIsNone(s["economie_operationnelle_certifiee_cad"])
            self.assertEqual(s["revues_independantes_certifiees"],0)
    def test_56_no_go_after_hash_match(self):
        tmp,p=setup_tmp()
        with tmp:
            s=m.result(self.cfg,self.rows,m.check_local(p,[evidence()]))
            self.assertEqual(s["decision"],"NO_GO_AUTOMATIQUE")

if __name__=="__main__":
    unittest.main()
