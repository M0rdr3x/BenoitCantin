#!/usr/bin/env python3
"""P54J: vérifications synthétiques d'avis déclarés, sans attestation."""
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
import qualifier_contradictions_avis_nova_p54j as m

CITY="P54E-V-001"
MINISTRY="P54E-M-001"
CPA="MANDAT-COMPTABLE-2024"
LAW="MANDAT-JURIDIQUE-2024"

def opinion(mandate=CPA,case=CITY,conclusion="NON_CONCLUANT",
            contradiction="NON_SIGNALEE",
            reserve="AUCUNE_DECLAREE_NON_VERIFIEE"):
    return {"dossier_id":case,"mandat":mandate,
            "code_relecture":"REV-TEST0001",
            "conclusion_declaree":conclusion,
            "contradiction_declaree":contradiction,
            "controles_declares":[],
            "reserve_maintenue":reserve,
            "authenticite_professionnelle_certifiee":False,
            "signature_professionnelle_authentifiee":False,
            "economie_monetaire_certifiee":False,
            "decision_institutionnelle_autorisee":False}

def receipt(mandate=CPA,evidence="PIECE-001",reserve="AUCUNE_DECLAREE_NON_VERIFIEE",
            covered=None,nature="AVIS_PROFESSIONNEL_NON_AUTHENTIFIE"):
    return {
       "mandat":mandate,"code_reception":"REC-DEMO0001",
       "documents":[evidence],"nature_declaree":nature,
       "reserve_declaree":reserve,
       "portee_dossiers":list(covered or [CITY]),
       "controles_declaratifs":[],
       "contact_effectif_verifie":False,"contrat_signe_authentifie":False,
       "signature_avis_authentifiee":False,"independance_verifiee":False,
       "montant_financier_certifie":False}

def bundle(folder,mandates=None,reserve="AUCUNE_DECLAREE_NON_VERIFIEE"):
    root=Path(folder);evidence=root/"preuves";evidence.mkdir()
    manifest=m.parent.local_template(m.parent.configuration())
    requested=list(mandates if mandates is not None else [CPA])
    for i,mandate in enumerate(requested,1):
        file=evidence/("avis%d.bin"%i)
        body=("AVIS SYNTHETIQUE %d SANS VALEUR MONETAIRE"%i).encode()
        file.write_bytes(body);os.chmod(file,0o600)
        num="PIECE-%03d"%i
        manifest["pieces"].append({
           "id":num,"type":"AVIS_PROFESSIONNEL_NON_ATTESTE",
           "relative_path":"preuves/avis%d.bin"%i,
           "sha256":hashlib.sha256(body).hexdigest()})
        manifest["receptions"].append(receipt(mandate,num,reserve))
    mf=root/"manifest.json"
    mf.write_text(json.dumps(manifest),encoding="utf-8")
    os.chmod(mf,0o600)
    verified=m.parent.validate_private(manifest,mf,m.parent.configuration())
    doc=m.local_template(m.configuration(),hashlib.sha256(mf.read_bytes()).hexdigest())
    return mf,manifest,verified,doc

class TestsP54J(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cfg=m.configuration()
    def test_01_schema(self):self.assertEqual(self.cfg["schema_version"],"P54J-1")
    def test_02_year(self):self.assertEqual(self.cfg["exercice_source"],2024)
    def test_03_two_mandates(self):self.assertEqual(len(self.cfg["mandats"]),2)
    def test_04_four_cases(self):self.assertEqual(len(self.cfg["dossiers"]),4)
    def test_05_ten_controls(self):self.assertEqual(len(m.CHECKS),10)
    def test_06_20_unverified(self):self.assertEqual(self.cfg["etat_initial"]["points_de_controle_non_attestes"],20)
    def test_07_protections(self):self.assertTrue(all(self.cfg["protections"].values()))
    def test_08_no_go(self):self.assertEqual(m.public_report(self.cfg)["decision"],m.NO_GO)
    def test_09_initial_cases_open(self):
        r=m.public_report(self.cfg)
        self.assertEqual(len(r["dossiers"]),4)
        self.assertEqual(r["situations"],{"AUCUN_AVIS_LOCAL":4})
    def test_10_no_money(self):self.assertIsNone(m.public_report(self.cfg)["economies_certifiees_cad"])
    def test_11_no_signed(self):self.assertEqual(m.public_report(self.cfg)["signatures_professionnelles_verifiees"],0)
    def test_12_no_closure(self):self.assertEqual(m.public_report(self.cfg)["dossiers_clos"],0)
    def test_13_no_workers_cut(self):self.assertFalse(m.public_report(self.cfg)["emploi_services_reduits_autorises"])
    def test_14_no_merge(self):self.assertFalse(m.public_report(self.cfg)["fusion_main_autorisee"])
    def test_15_model_without_receipt(self):
        self.assertEqual(m.local_template(self.cfg)["sha256_manifest_p54i"],"0"*64)
    def test_16_valid_manifest_linked(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            doc["conclusions"]=[opinion()]
            actual=m.validate_locals(doc,mf.read_bytes(),man,ver)
            self.assertIn((CITY,CPA),actual)
    def test_17_one_case_one_mandate(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            doc["conclusions"]=[opinion()]
            r=m.public_report(self.cfg,m.validate_locals(doc,mf.read_bytes(),man,ver),ver,{CPA:{CITY}})
            self.assertEqual(r["situations"]["AVIS_UNIQUE_DECLARATIF_NON_AUTHENTIFIE"],1)
            self.assertEqual(r["situations"]["AUCUN_AVIS_LOCAL"],3)
    def test_18_two_different_disciplines_not_automatically_disagreement(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d,[CPA,LAW])
            doc["conclusions"]=[opinion(CPA,conclusion="PAS_D_ECART_DEMONTRE"),
                opinion(LAW,conclusion="HORS_PORTEE_MANDAT")]
            data=m.validate_locals(doc,mf.read_bytes(),man,ver)
            r=m.public_report(self.cfg,data,ver,{CPA:{CITY},LAW:{CITY}})
            self.assertEqual(r["situations"]["DEUX_VOLETS_NON_AUTHENTIFIES"],1)
            self.assertEqual(r["dossiers_clos"],0)
    def test_19_conflict_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d,[CPA,LAW])
            doc["conclusions"]=[opinion(CPA),
             opinion(LAW,contradiction="DIVERGENCE_DE_PORTEE_OUVERTE")]
            r=m.public_report(self.cfg,m.validate_locals(doc,mf.read_bytes(),man,ver),ver,{CPA:{CITY},LAW:{CITY}})
            self.assertEqual(r["situations"]["CONTRADICTION_DECLAREE"],1)
    def test_20_reserved_kept(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d,reserve="SIGNATURE_A_VERIFIER")
            doc["conclusions"]=[opinion(reserve="SIGNATURE_A_VERIFIER")]
            result=m.public_report(self.cfg,m.validate_locals(doc,mf.read_bytes(),man,ver),ver,{CPA:{CITY}})
            self.assertEqual(result["situations"]["RESERVE_DOCUMENTAIRE_OUVERTE"],1)
    def test_21_suspension_prio(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d,reserve="SUSPENSION_EXPLICITE")
            doc["conclusions"]=[opinion(reserve="SUSPENSION_EXPLICITE",
                  contradiction="QUESTION_PROBATOIRE_OUVERTE")]
            out=m.public_report(self.cfg,m.validate_locals(doc,mf.read_bytes(),man,ver),ver,{CPA:{CITY}})
            self.assertEqual(out["situations"]["SUSPENSION_MAINTENUE"],1)
    def test_22_suspension_scope_only(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d,reserve="SUSPENSION_EXPLICITE")
            r=m.public_report(self.cfg,None,ver,{CPA:{CITY}})
            self.assertEqual(r["situations"]["SUSPENSION_MAINTENUE"],1)
            self.assertEqual(r["situations"]["AUCUN_AVIS_LOCAL"],3)
    def test_23_missing_local_opinion_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d,[])
            doc["conclusions"]=[opinion()]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_24_allowed_no_conclusion(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d,[])
            doc["conclusions"]=[opinion(conclusion="AUCUNE_CONCLUSION")]
            self.assertEqual(len(m.validate_locals(doc,mf.read_bytes(),man,ver)),1)
    def test_25_corrupted_manifest_digest_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            doc["sha256_manifest_p54i"]="0"*64
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_26_corrupted_manifest_bytes_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes()+b"\n",man,ver)
    def test_27_wrong_mandate_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            doc["conclusions"]=[opinion("FAUX")]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_28_wrong_case_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            doc["conclusions"]=[opinion(case="CASE-UNKNOWN")]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_29_duplicate_conclusions_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            doc["conclusions"]=[opinion(),opinion()]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_30_doc_scope_required(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            doc["conclusions"]=[opinion(case=MINISTRY)]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_31_nonopinion_type_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            man["receptions"][0]["nature_declaree"]="DOCUMENT_MANDAT_DECLARATIF"
            doc["sha256_manifest_p54i"]=hashlib.sha256(json.dumps(man).encode()).hexdigest()
            with self.assertRaises(ValueError):m.validate_locals(doc,json.dumps(man).encode(),man,ver)
    def test_32_refuse_clear_reserve(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d,reserve="PORTEE_LIMITEE")
            doc["conclusions"]=[opinion()]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_33_fake_signature_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            o=opinion();o["signature_professionnelle_authentifiee"]=True
            doc["conclusions"]=[o]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_34_fake_monetary_cert_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            o=opinion();o["economie_monetaire_certifiee"]=True
            doc["conclusions"]=[o]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_35_fake_go_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            o=opinion();o["decision_institutionnelle_autorisee"]=True
            doc["conclusions"]=[o]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_36_fake_professional_auth_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            o=opinion();o["authenticite_professionnelle_certifiee"]=True
            doc["conclusions"]=[o]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_37_extra_raw_text_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            o=opinion();o["texte_avis"]="confidentiel";doc["conclusions"]=[o]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_38_duplicate_check_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            o=opinion();o["controles_declares"]=[m.CHECKS[0],m.CHECKS[0]]
            doc["conclusions"]=[o]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_39_unknown_contradiction_denied(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            o=opinion();o["contradiction_declaree"]="CLOTUREE"
            doc["conclusions"]=[o]
            with self.assertRaises(ValueError):m.validate_locals(doc,mf.read_bytes(),man,ver)
    def test_40_private_digest_never_in_report(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            doc["conclusions"]=[opinion()]
            res=m.public_report(self.cfg,m.validate_locals(doc,mf.read_bytes(),man,ver),ver,{CPA:{CITY}})
            s=json.dumps(res)
            self.assertNotIn(doc["sha256_manifest_p54i"],s)
            self.assertNotIn("REV-TEST0001",s)
            self.assertNotIn("avis1.bin",s)
    def test_41_cli_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"public.json"
            self.assertEqual(m.main(["--bilan",str(out)]),0)
            self.assertEqual(json.loads(out.read_text("utf-8"))["situations"],{"AUCUN_AVIS_LOCAL":4})
    def test_42_cli_go_refusal(self):
        self.assertEqual(m.main(["--exiger-go"]),3)
    def test_43_cli_no_manifest_for_conclusion(self):
        self.assertEqual(m.main(["--conclusions-locales","/tmp/nonexistent.json"]),2)
    def test_44_cli_private_model_linked(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            dest=Path(d)/"model.json"
            self.assertEqual(m.main(["--fiche-reception-p54i",str(mf),
                                     "--modele-prive",str(dest)]),0)
            self.assertEqual(stat.S_IMODE(dest.stat().st_mode),0o600)
            self.assertEqual(json.loads(dest.read_text("utf-8"))["sha256_manifest_p54i"],
                             hashlib.sha256(mf.read_bytes()).hexdigest())
    def test_45_cli_local_conclusion(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            doc["conclusions"]=[opinion()]
            private=Path(d)/"conclusions.json"
            private.write_text(json.dumps(doc),encoding="utf-8")
            os.chmod(private,0o600)
            target=Path(d)/"public.json"
            self.assertEqual(m.main(["--fiche-reception-p54i",str(mf),
                 "--conclusions-locales",str(private),"--bilan",str(target)]),0)
            self.assertEqual(json.loads(target.read_text("utf-8"))["conclusions_locales_declares"],1)
    def test_46_cli_refuse_unprotected(self):
        with tempfile.TemporaryDirectory() as d:
            mf,man,ver,doc=bundle(d)
            os.chmod(mf,0o644)
            self.assertEqual(m.main(["--fiche-reception-p54i",str(mf)]),2)
    def test_47_cli_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            t=Path(d)/"existing.json";t.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(t)]),2)
            self.assertEqual(t.read_text("utf-8"),"keep")
    def test_48_cli_same_destinations(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"same.json"
            self.assertEqual(m.main(["--bilan",str(p),"--modele-prive",str(p)]),2)

def safety_case(code):
    def check(self):
        self.assertTrue(self.cfg["protections"][code])
    return check
for n,code in enumerate(sorted(m.GUARDS),49):
    setattr(TestsP54J,"test_%02d_guard"%n,safety_case(code))

if __name__=="__main__":
    unittest.main()
