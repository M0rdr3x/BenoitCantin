#!/usr/bin/env python3
"""P54W : tests purement synthétiques de l'instruction humaine non certifiée."""
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
import qualifier_occurrences_privees_nova_p54w as m

def source():
    reference=m.p54v.p54t.p54r.known_rows()
    cards=[]
    for i,item in enumerate(reference):
        offset=item["offset_texte_extrait"]
        start=max(0,offset-3)
        snippet="a"*(offset-start)+"123"+"b"*7
        cards.append({
            "reference":m.REFS[i],
            "source":item["source"],
            "page_pdf_index_zero":item["pdf_index_zero"],
            "offset_caractere_nfkc":offset,
            "zone_indicative":item["zone_confirmee_par_parseur"],
            "classification_automatique_non_attestee":
                item["classification_indicative"],
            "jeton_brut_STRICTEMENT_PRIVE":"123",
            "extrait_contextuel_STRICTEMENT_PRIVE":snippet,
            "debut_extrait_nfkc":start,
            "etat":"A_EXAMINER_PAR_PERSONNE_HABILITEE",
            "controles_a_instruire":[
                {"code":c,"etat":"NON_ATTESTE"} for c in m.CHECKS],
            "revue_contradictoire_effectuee":False,
            "qualification_humaine_confirmee":False,
        })
    return {
        "schema_version":"P54V-FICHE-PRIVEE-1",
        "confidentialite":"NE_PAS_DEPLOYER_OU_PUBLIER",
        "source":"PDF_2024_SHA256_CONFORMES_LOCALEMENT_PLUS_P54T",
        "occurrences":cards,
        "signatures_professionnelles_authentifiees":0,
        "economies_certifiees_cad":None,
        "decision":m.NO_GO,
    }

def review(ref=None,role="LECTEUR_DECLARE",code="REV-TEST0001",
           nature="INDETERMINE",progress="NON_EXAMINE",
           reserve="AUCUNE_DECLAREE_NON_VERIFIEE",checks=None):
    return {
        "reference":ref or m.REFS[0],
        "role":role,"code_lecteur":code,
        "nature_declaree":nature,"etat_declare":progress,
        "reserve_declaree":reserve,"controles_declares":list(checks or []),
        **{flag:False for flag in m.FLAGS},
    }

def examined(ref=None,role="LECTEUR_DECLARE",code="REV-TEST0001",
             nature="IDENTIFIANT_POSSIBLE",reserve="AUCUNE_DECLAREE_NON_VERIFIEE"):
    return review(ref,role,code,nature,"EXAMINE_SUR_PIECE_NON_ATTESTE",
                  reserve,["QUALIFIER_NATURE_SUR_PIECE"])

def local_documents(folder):
    s=source()
    f=Path(folder)/"p54v.json"
    f.write_text(json.dumps(s,ensure_ascii=False),encoding="utf-8")
    os.chmod(f,0o600)
    raw=f.read_bytes()
    return f,s,raw,m.private_template(raw)

class TestsP54W(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=m.configuration()
        cls.src=source()
    def test_01_schema(self):self.assertEqual(self.config["schema_version"],"P54W-1")
    def test_02_year(self):self.assertEqual(self.config["exercice"],2024)
    def test_03_source_chain(self):self.assertEqual(self.config["source_jalons"],["P54T","P54U","P54V"])
    def test_04_provenance_run(self):self.assertEqual(self.config["source_p54p_run"],40151185184)
    def test_05_five_refs(self):self.assertEqual(len(m.REFS),5)
    def test_06_date_outside_p54e(self):self.assertEqual(m.REFS[2],"P54O-DATE-001")
    def test_07_two_roles(self):self.assertEqual(len(m.ROLES),2)
    def test_08_eight_checks(self):self.assertEqual(len(m.CHECKS),8)
    def test_09_twenty_guards(self):self.assertEqual(len(m.GUARDS),20)
    def test_10_no_go(self):self.assertEqual(m.report(self.config)["decision"],m.NO_GO)
    def test_11_no_certs(self):self.assertEqual(m.report(self.config)["signatures_authentifiees"],0)
    def test_12_no_savings(self):self.assertIsNone(m.report(self.config)["economies_certifiees_cad"])
    def test_13_initial_five_open(self):self.assertEqual(m.report(self.config)["statuts"],{"NON_EXAMINE":5})
    def test_14_no_raw_context_in_public(self):self.assertNotIn("jeton_brut_STRICTEMENT_PRIVE",json.dumps(m.report(self.config)))
    def test_15_p54b_still_open(self):self.assertEqual(m.report(self.config)["controles_p54b_non_attestes"],96)
    def test_16_p54c_still_open(self):self.assertEqual(m.report(self.config)["controles_p54c_non_attestes"],8)
    def test_17_p54v_synthetic_valid(self):
        self.assertTrue(m.validate_p54v(self.src,m.p54v.p54t.p54r.known_rows()))
    def test_18_p54v_wrong_source_page(self):
        a=copy.deepcopy(self.src);a["occurrences"][0]["page_pdf_index_zero"]=99
        with self.assertRaises(ValueError):m.validate_p54v(a,m.p54v.p54t.p54r.known_rows())
    def test_19_p54v_wrong_offset(self):
        a=copy.deepcopy(self.src);a["occurrences"][1]["offset_caractere_nfkc"]+=1
        with self.assertRaises(ValueError):m.validate_p54v(a,m.p54v.p54t.p54r.known_rows())
    def test_20_p54v_missing_occurrence(self):
        a=copy.deepcopy(self.src);a["occurrences"].pop()
        with self.assertRaises(ValueError):m.validate_p54v(a,m.p54v.p54t.p54r.known_rows())
    def test_21_p54v_modified_token_refused(self):
        a=copy.deepcopy(self.src);a["occurrences"][2]["jeton_brut_STRICTEMENT_PRIVE"]="999"
        with self.assertRaises(ValueError):m.validate_p54v(a,m.p54v.p54t.p54r.known_rows())
    def test_22_p54v_extra_sensitive_field(self):
        a=copy.deepcopy(self.src);a["occurrences"][0]["identite"]="PRIVEE"
        with self.assertRaises(ValueError):m.validate_p54v(a,m.p54v.p54t.p54r.known_rows())
    def test_23_p54v_false_human_review(self):
        a=copy.deepcopy(self.src);a["occurrences"][0]["qualification_humaine_confirmee"]=True
        with self.assertRaises(ValueError):m.validate_p54v(a,m.p54v.p54t.p54r.known_rows())
    def test_24_p54v_changed_checklist(self):
        a=copy.deepcopy(self.src);a["occurrences"][0]["controles_a_instruire"][0]["etat"]="ATTESTE"
        with self.assertRaises(ValueError):m.validate_p54v(a,m.p54v.p54t.p54r.known_rows())
    def test_25_empty_template(self):
        self.assertEqual(m.private_template()["sha256_fiche_p54v"],"0"*64)
    def test_26_sha_real_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            self.assertEqual(doc["sha256_fiche_p54v"],hashlib.sha256(raw).hexdigest())
            self.assertEqual(m.validate_reviews(doc,raw,s),{})
    def test_27_one_non_examined_still_non_examined(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[review()]
            v=m.validate_reviews(doc,raw,s)
            self.assertEqual(m.report(self.config,v)["statuts"],{"NON_EXAMINE":5})
    def test_28_one_examined_partial(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[examined()]
            v=m.validate_reviews(doc,raw,s)
            self.assertEqual(m.report(self.config,v)["statuts"]["REVUE_PARTIELLE_NON_ATTESTEE"],1)
    def test_29_two_declared_still_uncertified(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[examined(),examined(
                role="CONTRE_LECTEUR_DECLARE",code="REV-TEST0002")]
            v=m.validate_reviews(doc,raw,s)
            report=m.report(self.config,v)
            self.assertEqual(report["statuts"]["DEUX_REVUES_DECLARATIVES_NON_ATTESTEES"],1)
            self.assertEqual(report["qualifications_definitives"],0)
    def test_30_conflicting_findings_remain_open(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[examined(),examined(
                role="CONTRE_LECTEUR_DECLARE",code="REV-TEST0002",
                nature="MONTANT_POTENTIEL_NON_ATTESTE")]
            v=m.validate_reviews(doc,raw,s)
            self.assertEqual(m.report(self.config,v)["statuts"]["CONTRADICTION_DECLAREE_NON_RESOLUE"],1)
    def test_31_suspension_has_priority(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[review(
                 progress="SUSPENDU",reserve="SUSPENSION_DEMANDEE")]
            v=m.validate_reviews(doc,raw,s)
            self.assertEqual(m.report(self.config,v)["statuts"]["SUSPENSION_MAINTENUE"],1)
    def test_32_explicit_reserve_remains(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[examined(reserve="CONTEXTE_INSUFFISANT")]
            v=m.validate_reviews(doc,raw,s)
            self.assertEqual(m.report(self.config,v)["statuts"]["RESERVE_OUVERTE"],1)
    def test_33_date_possible_not_certified(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[examined(
                ref="P54O-DATE-001",nature="ANNEE_DATE_POSSIBLE")]
            v=m.validate_reviews(doc,raw,s)
            self.assertEqual(m.report(self.config,v)["occurrence_date_probable_non_certifiee"],1)
    def test_34_monetary_possible_not_certified(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[examined(nature="MONTANT_POTENTIEL_NON_ATTESTE")]
            v=m.validate_reviews(doc,raw,s)
            self.assertEqual(m.report(self.config,v)["valeurs_monetaires_certifiees"],0)
    def test_35_duplicate_role_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[examined(),examined(code="REV-TEST0002")]
            with self.assertRaises(ValueError):m.validate_reviews(doc,raw,s)
    def test_36_same_reader_twice_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[examined(),examined(role="CONTRE_LECTEUR_DECLARE")]
            with self.assertRaises(ValueError):m.validate_reviews(doc,raw,s)
    def test_37_wrong_reference_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[examined(ref="P54E-UNKNOWN")]
            with self.assertRaises(ValueError):m.validate_reviews(doc,raw,s)
    def test_38_no_conclusion_if_not_examined(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[review(nature="IDENTIFIANT_POSSIBLE")]
            with self.assertRaises(ValueError):m.validate_reviews(doc,raw,s)
    def test_39_examination_needs_targeted_control(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            a=examined();a["controles_declares"]=["RETROUVER_OCCURRENCE_NFKC"]
            doc["declarations"]=[a]
            with self.assertRaises(ValueError):m.validate_reviews(doc,raw,s)
    def test_40_suspension_requires_status(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["declarations"]=[examined(reserve="SUSPENSION_DEMANDEE")]
            with self.assertRaises(ValueError):m.validate_reviews(doc,raw,s)
    def test_41_fake_signature_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            a=examined();a["signature_professionnelle_authentifiee"]=True
            doc["declarations"]=[a]
            with self.assertRaises(ValueError):m.validate_reviews(doc,raw,s)
    def test_42_fake_money_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            a=examined();a["valeur_financiere_certifiee"]=True
            doc["declarations"]=[a]
            with self.assertRaises(ValueError):m.validate_reviews(doc,raw,s)
    def test_43_raw_notes_field_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            a=examined();a["extrait_ou_nom"]="SENSIBLE"
            doc["declarations"]=[a]
            with self.assertRaises(ValueError):m.validate_reviews(doc,raw,s)
    def test_44_bad_sha_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            doc["sha256_fiche_p54v"]="0"*64
            with self.assertRaises(ValueError):m.validate_reviews(doc,raw,s)
    def test_45_private_permissions_must_be_0600(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            self.assertEqual(m.private_file(f),f)
            os.chmod(f,0o644)
            with self.assertRaises(ValueError):m.private_file(f)
    def test_46_private_symlink_forbidden(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            alias=Path(d)/"alias.json";alias.symlink_to(f)
            with self.assertRaises(ValueError):m.private_file(alias)
    def test_47_private_inside_repo_forbidden(self):
        with self.assertRaises(ValueError):m.private_file(m.CONFIG)
    def test_48_cli_empty_public(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"public.json"
            self.assertEqual(m.main(["--bilan-public",str(target)]),0)
            self.assertEqual(json.loads(target.read_text("utf-8"))["statuts"],{"NON_EXAMINE":5})
    def test_49_cli_private_model_linked(self):
        with tempfile.TemporaryDirectory() as d:
            f,s,raw,doc=local_documents(d)
            out=Path(d)/"model.json"
            self.assertEqual(m.main(["--fiche-privee-p54v",str(f),
                                    "--modele-prive",str(out)]),0)
            self.assertEqual(stat.S_IMODE(out.stat().st_mode),0o600)
            self.assertEqual(json.loads(out.read_text("utf-8"))["sha256_fiche_p54v"],hashlib.sha256(raw).hexdigest())
    def test_50_cli_explicit_no_closure(self):
        self.assertEqual(m.main(["--exiger-cloture"]),3)

def guard_factory(name):
    def t(self):self.assertTrue(self.config["protections"][name])
    return t
for n,name in enumerate(sorted(m.GUARDS),51):
    setattr(TestsP54W,"test_%02d_guard"%n,guard_factory(name))

if __name__=="__main__":
    unittest.main()
