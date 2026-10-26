#!/usr/bin/env python3
"""P53Y : validations de versions déclaratives et fausses certifications."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import enregistrer_versions_documentaires_nova_p53y as m

A="a"*64
B="b"*64

def fiche(src="ville"):
    return {
      "schema_version":"P53Y-FICHE-1",
      "source_id":src,"type_acquisition":"TELECHARGEMENT_DECLARE",
      "date_declaree":"2026-10-23",
      "role_collecte":"COLLECTE_DOCUMENTAIRE",
      "role_relecture":"REVUE_QUALITE_INDEPENDANTE",
      "sha256_declare":A if src=="ville" else B,
      "taille_octets":100 if src=="ville" else 120,
      "nombre_pages":2 if src=="ville" else 3,
      "droit_acces":"A_VERIFIER",
      "statut_provenance":"INCONNUE",
      "avis_professionnel":"NON_OBTENU",
      "sauvegarde_emplois_services":"A_VERIFIER",
    }

def detail(identique=False):
    return {
      "schema_version":"P53X-DETAIL-LOCAL-1",
      "statut":"EMPREINTES_DE_FICHIERS_FOURNIS_SANS_PREUVE_DE_SOURCE",
      "comparaison":{
        "taille_octets_ville":100,"taille_octets_mamh":100 if identique else 120,
        "sha256_ville":A,"sha256_mamh":A if identique else B,
        "octets_strictement_identiques":identique,
        "pages_ville":2,"pages_mamh":2 if identique else 3,
        "meme_nombre_pages":identique,
        "pages_textuellement_appariees":2,
        "correspondances_indices":[[0,0],[1,1]],
        "ancrages_p53w_textuellement_retrouves":{"0":True,"34":None,"196":None},
        "textes_ville_non_apparies":0,
        "pages_ville_sans_texte_exploitable":0,
        "pages_mamh_sans_texte_exploitable":0,
        "audit_comptable_effectue":False,
        "provenance_institutionnelle_authentifiee":False,
        "comparaison_version_source_certifiee":False,
        "economie_certifiee_cad":None,
      },
      "decision":"NO_GO_AUTOMATIQUE",
    }

class TestsP53Y(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.sources()
        cls.reg=m.register(cls.cfg)

    def test_01_codes(self):self.assertEqual(self.cfg["organisme_ville"],"23027")
    def test_02_rtc(self):self.assertEqual(self.cfg["organisme_rtc"],"T0088")
    def test_03_two_sources(self):self.assertEqual(len(self.reg),2)
    def test_04_six_controls(self):self.assertEqual(len(m.CHECKS),6)
    def test_05_twelve_controls(self):self.assertEqual(sum(len(s["controles"]) for s in self.reg),12)
    def test_06_year(self):self.assertEqual(self.cfg["exercice_reference"],2024)
    def test_07_guard_integrity(self):self.assertTrue(self.cfg["verrous"]["hash_pas_provenance"])
    def test_08_guard_qc_rtc(self):self.assertTrue(self.cfg["verrous"]["pas_de_seconde_elimination_quebec_rtc"])
    def test_09_guard_jobs(self):self.assertTrue(self.cfg["verrous"]["maintien_emplois_et_services"])
    def test_10_no_hashed_official(self):self.assertTrue(all(s["sha256_officiel_authentifie"] is None for s in self.reg))
    def test_11_no_real_date(self):self.assertTrue(all(s["date_obtention_certifiee"] is None for s in self.reg))
    def test_12_no_auth_issuer(self):self.assertTrue(all(s["source_institutionnelle_authentifiee"] is False for s in self.reg))
    def test_13_no_signed_advice(self):self.assertTrue(all(s["avis_independant_original_signe"] is False for s in self.reg))
    def test_14_no_savings_initial(self):self.assertTrue(all(s["economie_certifiee_cad"] is None for s in self.reg))
    def test_15_two_target_codes(self):self.assertEqual(set(s["source_id"] for s in self.reg),set(m.SOURCES))
    def test_16_ville_source(self):self.assertEqual(m.SOURCES["ville"],m.p53x.URL_VILLE)
    def test_17_mamh_source(self):self.assertEqual(m.SOURCES["mamh"],m.p53x.URL_MAMH)
    def test_18_good_record(self):self.assertEqual(m.validate_record(fiche())["source"],"ville")
    def test_19_second_record(self):self.assertEqual(m.validate_record(fiche("mamh"))["pages"],3)
    def test_20_declared_access_allowed(self):
        f=fiche();f["droit_acces"]="DECLARE_NON_VERIFIE"
        self.assertFalse(m.validate_record(f)["bloque"])
    def test_21_block_access(self):
        f=fiche();f["droit_acces"]="INTERDIT"
        self.assertTrue(m.validate_record(f)["bloque"])
    def test_22_block_service(self):
        f=fiche();f["sauvegarde_emplois_services"]="RISQUE_DECLARE"
        self.assertTrue(m.validate_record(f)["bloque"])
    def test_23_status_declarative(self):
        self.assertEqual(m.validate_set([fiche()],None)["etats"]["COPIE_DECLAREE_NON_AUTHENTIFIEE"],1)
    def test_24_suspended_status(self):
        f=fiche();f["droit_acces"]="INTERDIT"
        self.assertEqual(m.validate_set([f],None)["etats"]["SUSPENDUE_DROITS_OU_SERVICES"],1)
    def test_25_both_sources(self):self.assertEqual(m.validate_set([fiche(),fiche("mamh")],None)["fiches"],2)
    def test_26_dup_denied(self):
        with self.assertRaises(ValueError):m.validate_set([fiche(),fiche()],None)
    def test_27_empty(self):self.assertEqual(m.validate_set([],None)["fiches"],0)
    def test_28_valid_detail(self):self.assertEqual(m.validate_detail(detail())["pages_mamh"],3)
    def test_29_equal_detail(self):self.assertTrue(m.validate_detail(detail(True))["octets_strictement_identiques"])
    def test_30_mismatched_sha_flag(self):
        d=detail();d["comparaison"]["octets_strictement_identiques"]=True
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_31_mismatched_pagination_flag(self):
        d=detail();d["comparaison"]["meme_nombre_pages"]=True
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_32_mismatched_identical_size(self):
        d=detail(True);d["comparaison"]["taille_octets_mamh"]=120
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_33_duplicate_page_to_right(self):
        d=detail();d["comparaison"]["correspondances_indices"]=[[0,0],[1,0]]
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_34_duplicate_page_to_left(self):
        d=detail();d["comparaison"]["correspondances_indices"]=[[0,0],[0,1]]
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_35_bad_page_index(self):
        d=detail();d["comparaison"]["correspondances_indices"]=[[0,0],[2,1]]
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_36_bad_page_count(self):
        d=detail();d["comparaison"]["pages_textuellement_appariees"]=3
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_37_bad_text_totals(self):
        d=detail();d["comparaison"]["textes_ville_non_apparies"]=1
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_38_hidden_anchor(self):
        d=detail();d["comparaison"]["ancrages_p53w_textuellement_retrouves"]["0"]=False
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_39_false_far_anchor(self):
        d=detail();d["comparaison"]["ancrages_p53w_textuellement_retrouves"]["34"]=True
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_40_denies_auto_certification(self):
        d=detail();d["comparaison"]["comparaison_version_source_certifiee"]=True
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_41_denies_audit_claim(self):
        d=detail();d["comparaison"]["audit_comptable_effectue"]=True
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_42_denies_saving(self):
        d=detail();d["comparaison"]["economie_certifiee_cad"]=12
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_43_denies_signature(self):
        d=detail();d["comparaison"]["provenance_institutionnelle_authentifiee"]=True
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_44_denies_personal_metadata(self):
        d=detail();d["comparaison"]["identite_agent"]="private"
        with self.assertRaises(ValueError):m.validate_detail(d)
    def test_45_matches_one_fiche(self):
        self.assertEqual(m.validate_set([fiche()],m.validate_detail(detail()))["fiches"],1)
    def test_46_matches_both_fiches(self):
        self.assertEqual(m.validate_set([fiche(),fiche("mamh")],m.validate_detail(detail()))["fiches"],2)
    def test_47_rejects_fiche_mismatch(self):
        f=fiche();f["sha256_declare"]="c"*64
        with self.assertRaises(ValueError):m.validate_set([f],m.validate_detail(detail()))
    def test_48_rejects_page_mismatch(self):
        f=fiche();f["nombre_pages"]=3
        with self.assertRaises(ValueError):m.validate_set([f],m.validate_detail(detail()))
    def test_49_rejects_size_mismatch(self):
        f=fiche();f["taille_octets"]=110
        with self.assertRaises(ValueError):m.validate_set([f],m.validate_detail(detail()))
    def test_50_summary_no_go(self):
        report=m.report(self.cfg,m.validate_set([],None))
        self.assertEqual(report["decision"],m.NO_GO)
        self.assertIsNone(report["economie_certifiee_cad"])
    def test_51_summary_aggregate_only(self):
        report=m.report(self.cfg,m.validate_set([fiche()],m.validate_detail(detail())))
        serialized=json.dumps(report)
        self.assertNotIn(A,serialized)
        self.assertNotIn(m.SOURCES["ville"],serialized)
        self.assertNotIn("2026-10-23",serialized)
    def test_52_private_input_rejected_in_repo(self):
        with self.assertRaises(ValueError):m.private_file(m.CONFIG)
    def test_53_cli_initial_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=Path(d)/"bilan.json",Path(d)/"registre.json"
            self.assertEqual(m.main(["--rapport",str(a),"--registre",str(b)]),0)
            self.assertEqual(len(json.loads(b.read_text("utf-8"))["sources"]),2)
    def test_54_cli_refuse_certification(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"bilan.json"
            self.assertEqual(m.main(["--rapport",str(a),"--exiger-authentification"]),3)
    def test_55_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=Path(d)/"a.json",Path(d)/"b.json"
            b.write_text("original","utf-8")
            self.assertEqual(m.main(["--rapport",str(a),"--registre",str(b)]),2)
            self.assertFalse(a.exists())
    def test_56_cli_same_paths(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"a.json"
            self.assertEqual(m.main(["--rapport",str(a),"--registre",str(a)]),2)
    def test_57_cli_with_synthetic_p53x(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"detail.json";f.write_text(json.dumps(detail()),"utf-8")
            c=Path(d)/"fiche.json";c.write_text(json.dumps(fiche()),"utf-8")
            a=Path(d)/"r.json"
            self.assertEqual(m.main(["--detail-p53x",str(f),"--fiche",str(c),"--rapport",str(a)]),0)
            self.assertTrue(json.loads(a.read_text("utf-8"))["detail_p53x_non_signe_importe"])
    def test_58_cli_rejects_duplicate_fiche(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"fiche.json";f.write_text(json.dumps(fiche()),"utf-8")
            self.assertEqual(m.main(["--fiche",str(f),"--fiche",str(f)]),2)
    def test_59_cli_no_certificates_from_p53x(self):
        r=m.report(self.cfg,m.validate_set([fiche()],m.validate_detail(detail())))
        self.assertEqual(r["copies_officielles_authentifiees"],0)
        self.assertEqual(r["comparaisons_certifiees"],0)
    def test_60_semantics_unknown_is_not_zero(self):
        self.assertIsNone(self.cfg["etat_initial"]["economie_certifiee_cad"])

BAD_CASES=[["source_id","INCONNU"],["type_acquisition","AUTHENTIFIE"],["date_declaree","2999-01-01"],["date_declaree","2023-12-31"],["date_declaree","2026-02-30"],["role_collecte","SIGNATAIRE"],["role_relecture","COLLECTE_DOCUMENTAIRE"],["sha256_declare","aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],["sha256_declare","AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"],["taille_octets",0],["taille_octets",True],["nombre_pages",0],["droit_acces","AUTORISE_CERTIFIE"],["avis_professionnel","SIGNE"]]

def _make_bad_test(field,value):
    def test(self):
        data=fiche()
        data[field]=value
        with self.assertRaises(ValueError):m.validate_record(data)
    return test

for index,(field,value) in enumerate(BAD_CASES,61):
    setattr(TestsP53Y,"test_%02d_rejet_%s"%(index,field),
            _make_bad_test(field,value))

if __name__=="__main__":
    unittest.main()
