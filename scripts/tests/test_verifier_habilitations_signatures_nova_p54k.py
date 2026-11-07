#!/usr/bin/env python3
"""P54K : tests entièrement synthétiques des limites d'authentification."""
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
import verifier_habilitations_signatures_nova_p54k as m

CITY="P54E-V-001"
MAMH="P54E-M-001"
CPA="MANDAT-COMPTABLE-2024"
LAW="MANDAT-JURIDIQUE-2024"

def synthetic(tmp,mandates=(CPA,),reserve="AUCUNE_DECLAREE_NON_VERIFIEE",
              conclusion="NON_CONCLUANT"):
    root=Path(tmp)
    proofs=root/"preuves"
    proofs.mkdir()
    i=m.p54i.local_template(m.p54i.configuration())
    for k,mandate in enumerate(mandates,1):
        b=("FICHIER AVIS TEST SYNTHETIQUE %d"%k).encode()
        file=proofs/("piece%d.bin"%k)
        file.write_bytes(b);os.chmod(file,0o600)
        ident="PIECE-%03d"%k
        i["pieces"].append({
          "id":ident,"type":"AVIS_PROFESSIONNEL_NON_ATTESTE",
          "relative_path":"preuves/piece%d.bin"%k,
          "sha256":hashlib.sha256(b).hexdigest()})
        i["receptions"].append({
          "mandat":mandate,"code_reception":"REC-TEST%04d"%k,
          "documents":[ident],
          "nature_declaree":"AVIS_PROFESSIONNEL_NON_AUTHENTIFIE",
          "reserve_declaree":reserve,"portee_dossiers":[CITY],
          "controles_declaratifs":[],
          "contact_effectif_verifie":False,
          "contrat_signe_authentifie":False,
          "signature_avis_authentifiee":False,
          "independance_verifiee":False,
          "montant_financier_certifie":False})
    f_i=root/"p54i.json"
    f_i.write_text(json.dumps(i),encoding="utf-8")
    os.chmod(f_i,0o600)
    raw_i=f_i.read_bytes()
    v_i=m.p54i.validate_private(i,f_i,m.p54i.configuration())
    j=m.p54j.local_template(m.p54j.configuration(),hashlib.sha256(raw_i).hexdigest())
    for mandate in mandates:
        j["conclusions"].append({
          "dossier_id":CITY,"mandat":mandate,
          "code_relecture":"REV-TEST0001",
          "conclusion_declaree":conclusion,
          "contradiction_declaree":"NON_SIGNALEE",
          "controles_declares":[],
          "reserve_maintenue":reserve,
          "authenticite_professionnelle_certifiee":False,
          "signature_professionnelle_authentifiee":False,
          "economie_monetaire_certifiee":False,
          "decision_institutionnelle_autorisee":False})
    f_j=root/"p54j.json"
    f_j.write_text(json.dumps(j),encoding="utf-8")
    os.chmod(f_j,0o600)
    raw_j=f_j.read_bytes()
    opinions=m.p54j.validate_locals(j,raw_i,i,v_i)
    k=m.template(hashlib.sha256(raw_i).hexdigest(),hashlib.sha256(raw_j).hexdigest())
    return f_i,f_j,k,i,opinions,raw_i,raw_j

def row(role="VERIFICATEUR_DECLARE",code="CONTROLE-TEST0001",
        mandate=CPA,case=CITY,progress="EXAMINE_NON_ATTESTE",
        anomaly="AUCUNE_DECLAREE_NON_VERIFIEE",checks=None):
    return {
      "dossier_id":case,"mandat":mandate,
      "role":role,"code_opaque":code,
      "controles_declares":list([m.CHECKS[0]] if checks is None else checks),
      "etat_declare":progress,"anomalie_declaree":anomaly,
      "preuve_originale_authentifiee":False,
      "statut_professionnel_certifie":False,
      "signature_authentifiee":False,
      "independance_certifiee":False,
      "avis_certifie":False,
      "decision_institutionnelle_autorisee":False}

class TestsP54K(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cfg=m.configuration()

    def test_01_schema(self):self.assertEqual(self.cfg["schema_version"],"P54K-1")
    def test_02_year(self):self.assertEqual(self.cfg["exercice_source"],2024)
    def test_03_chain(self):self.assertEqual(self.cfg["chaine"],["P54I","P54J"])
    def test_04_mandates(self):self.assertEqual(len(m.MANDATS),2)
    def test_05_cases(self):self.assertEqual(len(m.DOSSIERS),4)
    def test_06_roles(self):self.assertEqual(len(m.ROLES),2)
    def test_07_slots(self):self.assertEqual(self.cfg["etat_initial"]["roles_possibles"],16)
    def test_08_checks(self):self.assertEqual(len(m.CHECKS),12)
    def test_09_no_licensing_claim(self):self.assertEqual(m.public_report(self.cfg)["statuts_professionnels_certifies"],0)
    def test_10_no_signed(self):self.assertEqual(m.public_report(self.cfg)["signatures_verifiees_par_ordre"],0)
    def test_11_no_external_contact(self):self.assertEqual(m.public_report(self.cfg)["avis_externes_officiels_sollicites"],0)
    def test_12_zero_money(self):self.assertIsNone(m.public_report(self.cfg)["economies_certifiees_cad"])
    def test_13_no_go(self):self.assertEqual(m.public_report(self.cfg)["decision"],m.NO_GO)
    def test_14_no_merge(self):self.assertFalse(m.public_report(self.cfg)["fusion_main_autorisee"])
    def test_15_no_closure(self):self.assertEqual(m.public_report(self.cfg)["dossiers_clos"],0)
    def test_16_initial_waiting(self):self.assertEqual(m.public_report(self.cfg)["etats"],{"AUCUNE_REVUE_PROFESSIONNELLE":4})
    def test_17_cpa_register(self):self.assertTrue(any(x["metier"]=="COMPTABILITE" for x in m.REFERENCES))
    def test_18_barreau_signature_reference(self):self.assertTrue(any("barreau.qc.ca" in x["source"] for x in m.REFERENCES))
    def test_19_zero_primary_identity(self):self.assertFalse(m.public_report(self.cfg)["emplois_services_reduits_autorises"])
    def test_20_zero_certification_even_full(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[
              row(checks=m.CHECKS),
              row("CONTRE_REVISEUR_DECLARE","CONTROLE-TEST0002",checks=m.CHECKS)]
            observed=m.validate_reviews(doc,rawi,rawj,opinions,man)
            out=m.public_report(self.cfg,opinions,observed)
            self.assertEqual(out["etats"]["DEUX_REVUES_DECLAREES_NON_AUTHENTIFIEES"],1)
            self.assertEqual(out["avis_professionnels_authentifies"],0)
    def test_21_one_reviewer_remains_partial(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row()]
            observed=m.validate_reviews(doc,rawi,rawj,opinions,man)
            self.assertEqual(m.public_report(self.cfg,opinions,observed)["etats"]["REVUE_PARTIELLE_NON_AUTHENTIFIEE"],1)
    def test_22_one_non_examined(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(progress="NON_EXAMINE",checks=[])]
            observed=m.validate_reviews(doc,rawi,rawj,opinions,man)
            self.assertEqual(m.public_report(self.cfg,opinions,observed)["etats"]["REVUE_PARTIELLE_NON_AUTHENTIFIEE"],1)
    def test_23_anomaly_priority(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(anomaly="SIGNATURE_A_VERIFIER")]
            observed=m.validate_reviews(doc,rawi,rawj,opinions,man)
            self.assertEqual(m.public_report(self.cfg,opinions,observed)["etats"]["ALERTE_VERIFICATION"],1)
    def test_24_conflict_priority(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(anomaly="DESACCORD_DOCUMENTAIRE")]
            observed=m.validate_reviews(doc,rawi,rawj,opinions,man)
            self.assertEqual(m.public_report(self.cfg,opinions,observed)["etats"]["CONTRADICTION_OUVERTE"],1)
    def test_25_suspension_priority_even_one(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(progress="SUSPENDU",anomaly="SUSPENSION_DEMANDEE")]
            observed=m.validate_reviews(doc,rawi,rawj,opinions,man)
            self.assertEqual(m.public_report(self.cfg,opinions,observed)["etats"]["SUSPENSION_PRIORITAIRE"],1)
    def test_26_upstream_reserve(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t,reserve="SIGNATURE_A_VERIFIER")
            scope={CPA:{CITY}}
            upstream=m.p54j.public_report(m.p54j.configuration(),opinions,
                     m.p54i.validate_private(man,fi,m.p54i.configuration()),scope)
            statuses={d["dossier_id"]:d["situation"] for d in upstream["dossiers"]}
            self.assertEqual(m.public_report(self.cfg,opinions,None,statuses)["etats"]["RESERVE_OUVERTE"],1)
    def test_27_upstream_suspension(self):
        self.assertEqual(m.matrix({},None,{CITY:"SUSPENSION_MAINTENUE"})[1]["SUSPENSION_PRIORITAIRE"],1)
    def test_28_upstream_contradiction(self):
        self.assertEqual(m.matrix({},None,{CITY:"CONTRADICTION_DECLAREE"})[1]["CONTRADICTION_OUVERTE"],1)
    def test_29_sha_p54i_mismatch(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["sha256_fiche_p54i"]="0"*64
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_30_sha_p54j_mismatch(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["sha256_fiche_p54j"]="0"*64
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_31_no_local_opinion(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row()]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,{},man)
    def test_32_wrong_scope(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(case=MAMH)]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_33_same_role_duplicate(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(),row(code="CONTROLE-TEST0002")]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_34_same_person_two_roles(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(),row("CONTRE_REVISEUR_DECLARE")]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_35_two_roles_distinct(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(),row("CONTRE_REVISEUR_DECLARE","CONTROLE-TEST0002")]
            self.assertEqual(len(m.validate_reviews(doc,rawi,rawj,opinions,man)),2)
    def test_36_false_signature_flag(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            x=row();x["signature_authentifiee"]=True;doc["declarations"]=[x]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_37_false_identity_flag(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            x=row();x["statut_professionnel_certifie"]=True;doc["declarations"]=[x]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_38_false_independence_flag(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            x=row();x["independance_certifiee"]=True;doc["declarations"]=[x]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_39_false_go_flag(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            x=row();x["decision_institutionnelle_autorisee"]=True;doc["declarations"]=[x]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_40_freeform_identity_denied(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            x=row();x["nom"] = "Nom personnel";doc["declarations"]=[x]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_41_unknown_checks_denied(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(checks=["GO_AUTOMATIQUE"])]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_42_duplicate_checks_denied(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(checks=[m.CHECKS[0],m.CHECKS[0]])]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_43_suspension_requires_reason(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(progress="SUSPENDU")]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_44_suspension_reason_requires_state(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(anomaly="SUSPENSION_DEMANDEE")]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_45_exam_requires_check(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row(checks=[])]
            with self.assertRaises(ValueError):m.validate_reviews(doc,rawi,rawj,opinions,man)
    def test_46_no_personal_data_in_public(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row()]
            out=m.public_report(self.cfg,opinions,m.validate_reviews(doc,rawi,rawj,opinions,man))
            b=json.dumps(out)
            self.assertNotIn("CONTROLE-TEST0001",b)
            self.assertNotIn(doc["sha256_fiche_p54i"],b)
            self.assertNotIn("piece1.bin",b)
    def test_47_cli_baseline(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/"summary.json"
            self.assertEqual(m.main(["--bilan",str(target)]),0)
            self.assertEqual(json.loads(target.read_text("utf-8"))["etats"],{"AUCUNE_REVUE_PROFESSIONNELLE":4})
    def test_48_cli_go_refusal(self):self.assertEqual(m.main(["--exiger-authenticite"]),3)
    def test_49_cli_requires_both_inputs(self):
        self.assertEqual(m.main(["--revue-locale","/tmp/notreal.json"]),2)
    def test_50_cli_priv_model(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"private.json"
            self.assertEqual(m.main(["--modele-prive",str(path)]),0)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o600)
    def test_51_cli_manifest_and_p54j(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            output=Path(t)/"public.json"
            self.assertEqual(m.main(["--fiche-p54i",str(fi),"--fiche-p54j",str(fj),"--bilan",str(output)]),0)
            self.assertEqual(json.loads(output.read_text("utf-8"))["avis_professionnels_authentifies"],0)
    def test_52_cli_private_human_review(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["declarations"]=[row()]
            r=Path(t)/"review.json"
            r.write_text(json.dumps(doc),encoding="utf-8")
            os.chmod(r,0o600)
            report=Path(t)/"public.json"
            self.assertEqual(m.main(["--fiche-p54i",str(fi),"--fiche-p54j",str(fj),
                            "--revue-locale",str(r),"--bilan",str(report)]),0)
            self.assertEqual(json.loads(report.read_text("utf-8"))["declarations_humaines_non_attestees"],1)
    def test_53_cli_private_tampered(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            doc["sha256_fiche_p54j"]="0"*64
            r=Path(t)/"review.json";r.write_text(json.dumps(doc),"utf-8");os.chmod(r,0o600)
            self.assertEqual(m.main(["--fiche-p54i",str(fi),"--fiche-p54j",str(fj),
                            "--revue-locale",str(r)]),2)
    def test_54_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"report.json";path.write_text("PRESERVE","utf-8")
            self.assertEqual(m.main(["--bilan",str(path)]),2)
            self.assertEqual(path.read_text("utf-8"),"PRESERVE")
    def test_55_cli_no_world_readable(self):
        with tempfile.TemporaryDirectory() as t:
            fi,fj,doc,man,opinions,rawi,rawj=synthetic(t)
            os.chmod(fi,0o644)
            self.assertEqual(m.main(["--fiche-p54i",str(fi),"--fiche-p54j",str(fj)]),2)

def guard_case(name):
    def run(self):
        self.assertTrue(self.cfg["protections"][name])
    return run
for n,name in enumerate(sorted(m.GUARDS),56):
    setattr(TestsP54K,"test_%02d_guard"%n,guard_case(name))

if __name__=="__main__":
    unittest.main()
