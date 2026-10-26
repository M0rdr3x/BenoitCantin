#!/usr/bin/env python3
"""P54V : tests synthétiques des notes privées, aucune lecture réseau."""
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
import preparer_contextes_prives_nova_p54v as m
from test_reproduire_localisations_pdf_nova_p54p import synthetic_texts

def fixture():
    texts=synthetic_texts()
    with patch.object(m.p54q.p54p.context,"analyze_text",
      return_value={"sections_se_rapportent_probablement_au_meme_audit":True}):
        positions=m.p54q.p54p.localize(texts)
    return texts,positions

def sheet(texts=None,positions=None):
    t,p=fixture()
    with patch.object(m.p54t.p54r,"known_rows",return_value=p):
        return m.private_sheet(texts if texts is not None else t,
                               positions if positions is not None else p)

def files_fixture(folder):
    t,p=fixture()
    paths={}
    raws={}
    refs={}
    for key in m.p54q.NAMES:
        raw=("%%PDF-1.4\nTEST LOCAL %s\n"%key).encode()
        file=Path(folder)/(key+".pdf")
        file.write_bytes(raw)
        paths[key]=file;raws[key]=raw
        refs[key]={"pdf_index_zero":m.p54q.p54p.p54d.PAGES[key],
                   "taille_octets":len(raw),
                   "sha256":hashlib.sha256(raw).hexdigest()}
    def extractor(raw,index):
        key=next(key for key,value in raws.items() if value==raw)
        if index!=refs[key]["pdf_index_zero"]:
            raise ValueError("Mauvaise page")
        return t[key]
    return t,p,paths,raws,refs,extractor

class TestsP54V(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=m.configuration()

    def test_01_schema(self):self.assertEqual(self.config["schema_version"],"P54V-1")
    def test_02_source_chain(self):self.assertEqual(self.config["source_jalons"],["P54Q","P54T","P54U"])
    def test_03_exercice(self):self.assertEqual(self.config["exercice"],2024)
    def test_04_run(self):self.assertEqual(self.config["reference_p54p_run"],40151185184)
    def test_05_artifact(self):self.assertEqual(self.config["reference_p54p_artifact"],12583661231)
    def test_06_mode(self):self.assertEqual(self.config["mode"],"LOCAL_PRIVE_HORS_GIT_SANS_RESEAU")
    def test_07_8_checks(self):self.assertEqual(len(m.CHECKS),8)
    def test_08_observations(self):self.assertEqual(self.config["observations"],5)
    def test_09_pdf_pages(self):self.assertEqual(self.config["indices_pdf_zero_based"],{"ville":102,"mamh":162})
    def test_10_baseline_no_go(self):self.assertEqual(m.public_summary()["decision"],m.NO_GO)
    def test_11_baseline_no_money(self):self.assertIsNone(m.public_summary()["economies_certifiees_cad"])
    def test_12_baseline_no_leak(self):self.assertEqual(m.public_summary()["contenus_jetons_extraits_publies"],0)
    def test_13_baseline_zero_pdfs(self):self.assertEqual(m.public_summary()["copies_pdf_verifiees_ce_run"],0)
    def test_14_baseline_zero_context(self):self.assertEqual(m.public_summary()["fiches_contextuelles_privees_creees"],0)
    def test_15_historical_open(self):
        b=m.public_summary()
        self.assertEqual((b["dossiers_p54e_ouverts"],b["taches_p54n_non_attestees"],
            b["blocages_p54o_non_leves"]),(4,40,10))
    def test_16_form_synthetic_five(self):
        self.assertEqual(len(sheet()["occurrences"]),5)
    def test_17_four_case_one_date(self):
        data=sheet()
        self.assertEqual([x["reference"] for x in data["occurrences"]],
           ["P54E-V-001","P54E-M-001","P54O-DATE-001","P54E-M-002","P54E-M-003"])
    def test_18_all_8_unattested(self):
        doc=sheet()
        self.assertEqual(sum(len(x["controles_a_instruire"]) for x in doc["occurrences"]),40)
        self.assertTrue(all(c["etat"]=="NON_ATTESTE"
            for x in doc["occurrences"] for c in x["controles_a_instruire"]))
    def test_19_no_human_signoff(self):
        self.assertTrue(all(not x["qualification_humaine_confirmee"]
                            for x in sheet()["occurrences"]))
    def test_20_noncertified(self):
        self.assertIsNone(sheet()["economies_certifiees_cad"])
        self.assertEqual(sheet()["decision"],m.NO_GO)
    def test_21_raw_private_only(self):
        self.assertTrue(all(x["jeton_brut_STRICTEMENT_PRIVE"]
                   for x in sheet()["occurrences"]))
    def test_22_context_private_only(self):
        self.assertTrue(all(x["extrait_contextuel_STRICTEMENT_PRIVE"]
                   for x in sheet()["occurrences"]))
    def test_23_all_characters_stay_in_context(self):
        x=sheet()["occurrences"]
        self.assertTrue(all(y["debut_extrait_nfkc"]<=y["offset_caractere_nfkc"]
                            for y in x))
    def test_24_no_raw_in_public(self):
        doc=sheet()
        s=json.dumps(m.public_summary(True))
        self.assertNotIn("jeton_brut_STRICTEMENT_PRIVE",s)
        self.assertNotIn("extrait_contextuel_STRICTEMENT_PRIVE",s)
        self.assertTrue(all(item["extrait_contextuel_STRICTEMENT_PRIVE"] not in s
                            for item in doc["occurrences"]))
    def test_25_one_bad_offset_refused(self):
        t,p=fixture()
        p[0]["offset_texte_extrait"]+=1
        with self.assertRaises(ValueError):sheet(t,p)
    def test_26_missing_one_position_refused(self):
        t,p=fixture()
        with self.assertRaises(ValueError):sheet(t,p[:4])
    def test_27_wrong_pdf_text_refused(self):
        t,p=fixture()
        t["ville"]=t["ville"][:-10]
        with self.assertRaises(ValueError):sheet(t,p)
    def test_28_missing_pdf_text_refused(self):
        t,p=fixture();t.pop("mamh")
        with self.assertRaises(ValueError):sheet(t,p)
    def test_29_extra_text_refused(self):
        t,p=fixture();t["faux"]="secret"
        with self.assertRaises(ValueError):sheet(t,p)
    def test_30_wrong_date_refused(self):
        t,p=fixture();t["mamh"]=t["mamh"].replace(";2024;",";9999;")
        with self.assertRaises(ValueError):sheet(t,p)
    def test_31_bad_nfkc_length_refused(self):
        t,p=fixture();p[1]["longueur_texte_normalise_nfkc"]+=3
        with self.assertRaises(ValueError):sheet(t,p)
    def test_32_normalize_unicode(self):
        self.assertEqual(m.nfkc("\u2160\u202f"),"I ")
    def test_33_reject_empty_text(self):
        with self.assertRaises(ValueError):m.nfkc("")
    def test_34_reject_object_text(self):
        with self.assertRaises(ValueError):m.nfkc({"sensitive":"data"})
    def test_35_file_private_0600(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"confidential.json"
            m.private_write_new(target,sheet())
            self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o600)
            self.assertEqual(len(json.loads(target.read_text("utf-8"))["occurrences"]),5)
    def test_36_private_reject_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"private.json";f.write_text("PRESERVE","utf-8")
            with self.assertRaises(ValueError):m.private_write_new(f,sheet())
            self.assertEqual(f.read_text("utf-8"),"PRESERVE")
    def test_37_private_reject_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            old=Path(d)/"original.json";old.write_text("KEEP","utf-8")
            alias=Path(d)/"alias.json";alias.symlink_to(old)
            with self.assertRaises(ValueError):m.private_write_new(alias,sheet())
    def test_38_private_reject_git(self):
        target=m.ROOT/"scripts"/"P54V_INTERDIT.json"
        with self.assertRaises(ValueError):m.safe_private_target(target)
    def test_39_private_missing_parent(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                m.safe_private_target(Path(d)/"absent"/"local.json")
    def test_40_public_new_and_neutral(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"bilan.json"
            m.write_public_new(file,m.public_summary())
            self.assertEqual(json.loads(file.read_text("utf-8"))["copies_pdf_verifiees_ce_run"],0)
    def test_41_public_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"bilan.json";file.write_text("PRESERVE","utf-8")
            with self.assertRaises(ValueError):m.write_public_new(file,m.public_summary())
    def test_42_verify_synthetic_exact_pair(self):
        with tempfile.TemporaryDirectory() as d:
            t,p,paths,raw,refs,ex=files_fixture(d)
            real_t_config=m.p54t.configuration()
            with patch.object(m.p54q,"configuration",return_value={"copies":refs}), \
                 patch.object(m.p54t,"configuration",return_value=real_t_config), \
                 patch.object(m.p54t,"verify_frozen",return_value={
                  "bilans_figes_verifies":2,"positions_historiques_hachees":5,
                  "positions_de_reference":p}), \
                 patch.object(m.p54t.p54r,"known_rows",return_value=p), \
                 patch.object(m.p54q.p54p.context,"analyze_text",
                    return_value={"sections_se_rapportent_probablement_au_meme_audit":True}):
                doc,_=m.verify_local(paths,self.config,extractor=ex)
            self.assertEqual(len(doc["occurrences"]),5)
    def test_43_verify_bad_digest_refused(self):
        with tempfile.TemporaryDirectory() as d:
            t,p,paths,raw,refs,ex=files_fixture(d)
            refs["ville"]["sha256"]="0"*64
            with patch.object(m.p54q,"configuration",return_value={"copies":refs}), \
                 patch.object(m.p54t,"verify_frozen",return_value={
                    "bilans_figes_verifies":2,"positions_historiques_hachees":5,
                    "positions_de_reference":p}):
                with self.assertRaises(ValueError):m.verify_local(paths,self.config,extractor=ex)
    def test_44_verify_one_file_missing_refused(self):
        with tempfile.TemporaryDirectory() as d:
            t,p,paths,raw,refs,ex=files_fixture(d)
            paths["mamh"].unlink()
            with self.assertRaises((ValueError,FileNotFoundError)):
                m.verify_local(paths,self.config,extractor=ex)
    def test_45_verify_symlink_input_refused(self):
        with tempfile.TemporaryDirectory() as d:
            t,p,paths,raw,refs,ex=files_fixture(d)
            alias=Path(d)/"fake.pdf";alias.symlink_to(paths["ville"])
            paths["ville"]=alias
            with self.assertRaises(ValueError):m.verify_local(paths,self.config,extractor=ex)
    def test_46_verify_different_historic_offset_refused(self):
        with tempfile.TemporaryDirectory() as d:
            t,p,paths,raw,refs,ex=files_fixture(d)
            bad=copy.deepcopy(p);bad[0]["offset_texte_extrait"]+=2
            real_t_config=m.p54t.configuration()
            with patch.object(m.p54q,"configuration",return_value={"copies":refs}), \
                 patch.object(m.p54t,"configuration",return_value=real_t_config), \
                 patch.object(m.p54t,"verify_frozen",return_value={
                    "bilans_figes_verifies":2,"positions_historiques_hachees":5,
                    "positions_de_reference":bad}), \
                 patch.object(m.p54q.p54p.context,"analyze_text",
                    return_value={"sections_se_rapportent_probablement_au_meme_audit":True}):
                with self.assertRaises(ValueError):m.verify_local(paths,self.config,extractor=ex)
    def test_47_cli_neutral(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"status.json"
            self.assertEqual(m.main(["--bilan-public",str(file)]),0)
            self.assertEqual(json.loads(file.read_text("utf-8"))["decision"],m.NO_GO)
    def test_48_cli_certification_explicit_refusal(self):
        self.assertEqual(m.main(["--exiger-certification"]),3)
    def test_49_cli_single_pdf_refused(self):
        self.assertEqual(m.main(["--ville-pdf","/tmp/not-real.pdf"]),2)
    def test_50_cli_prive_requires_pair(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.main(["--fiche-privee",str(Path(d)/"new.json")]),2)
    def test_51_cli_pair_requires_private_output(self):
        self.assertEqual(m.main(["--ville-pdf","/tmp/a.pdf",
                  "--mamh-pdf","/tmp/b.pdf"]),2)
    def test_52_cli_source_unavailable_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"context.json"
            self.assertEqual(m.main(["--ville-pdf","/tmp/no-city.pdf",
                "--mamh-pdf","/tmp/no-mamh.pdf","--fiche-privee",str(f)]),2)
            self.assertFalse(f.exists())
    def test_53_cli_no_private_secret_in_output(self):
        with tempfile.TemporaryDirectory() as d:
            status=Path(d)/"public.json"
            self.assertEqual(m.main(["--bilan-public",str(status)]),0)
            dumped=status.read_text("utf-8")
            self.assertNotIn("jeton_brut_STRICTEMENT_PRIVE",dumped)
            self.assertNotIn("extrait_contextuel_STRICTEMENT_PRIVE",dumped)
    def test_54_trusted_source_is_not_author_signature(self):
        self.assertEqual(m.public_summary(True)["avis_independants_authentifies"],0)
        self.assertFalse(m.public_summary(True)["pret_a_transmettre"])

def protection(name):
    def test(self):
        self.assertTrue(self.config["protections"][name])
    return test
for n,key in enumerate(sorted(m.GUARDS),55):
    setattr(TestsP54V,"test_%02d_guard"%n,protection(key))

if __name__=="__main__":
    unittest.main()
