#!/usr/bin/env python3
"""P54M : cas synthétiques de recevabilité sans authentification ni décision."""
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
import evaluer_recevabilite_authentifications_nova_p54m as m
from test_recevoir_preuves_externes_nova_p54l import (
    setup as prior_setup, proof as add_proof,
    observation as add_observation)

CITY="P54E-V-001"
CPA="MANDAT-COMPTABLE-2024"

def context(folder,number=0):
    paths,raw,reviewed,upstream,file,prior=prior_setup(folder)
    for i,cat in enumerate(m.CATEGORIES[:number]):
        ident="PIECE-%03d"%(i+2)
        filename="attestation%d.bin"%(i+2)
        add_proof(folder,prior,name=filename,ident=ident)
        prior["observations"].append(add_observation(
          category=cat,proof=ident))
    file.write_text(json.dumps(prior),encoding="utf-8")
    raw_l,manifest,validated,states=m.load_chain(
       *[str(p) for p in paths],str(file))
    evaluation=m.local_template(raw_l)
    return (paths,file),raw_l,manifest,validated,states,evaluation

def evaluation(outcome="DEMANDER_COMPLEMENT",reason="PIECES_INCOMPLETES",
               checks=None,case=CITY,mandate=CPA):
    return {
      "dossier_id":case,"mandat":mandate,
      "decision_preparatoire":outcome,
      "reserve_declaree":reason,
      "controles_declares":list(checks or []),
      "autorite_professionnelle_contactee":False,
      "statut_permis_officiellement_authentifie":False,
      "signature_officiellement_authentifiee":False,
      "mandat_juridiquement_valide_certifie":False,
      "absence_conflit_interets_certifiee":False,
      "avis_financier_certifie":False,
      "decision_institutionnelle_autorisee":False,
    }

class TestsP54M(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cfg=m.config()
    def test_01_config_version(self):self.assertEqual(self.cfg["schema_version"],"P54M-1")
    def test_02_year(self):self.assertEqual(self.cfg["exercice_source"],2024)
    def test_03_source(self):self.assertEqual(self.cfg["source_jalon"],"P54L")
    def test_04_four_cases(self):self.assertEqual(len(self.cfg["dossiers"]),4)
    def test_05_two_disciplines(self):self.assertEqual(len(self.cfg["mandats"]),2)
    def test_06_four_categories(self):self.assertEqual(len(m.CATEGORIES),4)
    def test_07_eight_gates(self):self.assertEqual(len(m.GATES),8)
    def test_08_noncertifying(self):self.assertEqual(m.report(self.cfg)["decision"],m.NO_GO)
    def test_09_none_authenticated(self):self.assertEqual(m.report(self.cfg)["signatures_authentifiees"],0)
    def test_10_no_savings(self):self.assertIsNone(m.report(self.cfg)["economies_certifiees_cad"])
    def test_11_no_close(self):self.assertEqual(m.report(self.cfg)["dossiers_clos"],0)
    def test_12_no_merge(self):self.assertFalse(m.report(self.cfg)["fusion_main_autorisee"])
    def test_13_employment_safe(self):self.assertFalse(m.report(self.cfg)["effectifs_services_reduits_autorises"])
    def test_14_open_p54b(self):self.assertEqual(m.report(self.cfg)["controles_p54b_restants"],96)
    def test_15_open_p54c(self):self.assertEqual(m.report(self.cfg)["controles_p54c_restants"],8)
    def test_16_blank_status(self):self.assertEqual(m.report(self.cfg)["statuts_recevabilite"],{"NON_INSTRUIT":4})
    def test_17_template_empty(self):self.assertEqual(m.local_template()["evaluations"],[])
    def test_18_empty_private_evaluations(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            self.assertEqual(m.validate_local(doc,raw,man,validated,states),{})
    def test_19_four_evidence_categories(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d,4)
            self.assertEqual(m.available_categories(man)[(CITY,CPA)],set(m.CATEGORIES))
            self.assertEqual(validated["pieces_verifiees"],4)
    def test_20_preparatory_formal_complete_not_certified(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d,4)
            doc["evaluations"]=[evaluation(
              outcome="EXAMEN_FORMEL_NON_ATTESTE",
              reason="AUCUNE_DECLAREE_NON_VERIFIEE",
              checks=m.GATES)]
            found=m.validate_local(doc,raw,man,validated,states)
            public=m.report(self.cfg,found,states)
            self.assertEqual(public["statuts_recevabilite"],
                             {"EXAMEN_FORMEL_DECLARATIF_NON_ATTESTE":1,"NON_INSTRUIT":3})
            self.assertEqual(public["authentifications_officielles_executees"],0)
            self.assertEqual(public["avis_independants_certifies"],0)
    def test_21_formal_without_categories_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d,3)
            doc["evaluations"]=[evaluation("EXAMEN_FORMEL_NON_ATTESTE",
               "AUCUNE_DECLAREE_NON_VERIFIEE",m.GATES)]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_22_formal_without_checks_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d,4)
            doc["evaluations"]=[evaluation("EXAMEN_FORMEL_NON_ATTESTE",
                "AUCUNE_DECLAREE_NON_VERIFIEE",m.GATES[:-1])]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_23_formal_with_reservation_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d,4)
            doc["evaluations"]=[evaluation("EXAMEN_FORMEL_NON_ATTESTE",
                "SIGNATURE_A_CONTROLER",m.GATES)]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_24_duplicate_case_mandate_refused(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            doc["evaluations"]=[evaluation(),evaluation()]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_25_unknown_case_refused(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            doc["evaluations"]=[evaluation(case="P54E-FAUX")]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_26_unknown_mandate_refused(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            doc["evaluations"]=[evaluation(mandate="FAUX")]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_27_bad_sha_p54l_refused(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            doc["sha256_fiche_p54l"]="0"*64
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_28_changed_sha_source_refused(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            with self.assertRaises(ValueError):m.validate_local(doc,raw+b"\n",man,validated,states)
    def test_29_bad_period(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            doc["exercice"]=2025
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_30_unknown_check(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            doc["evaluations"]=[evaluation(checks=["CERTIFICATION_AUTO"])]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_31_duplicate_check(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            doc["evaluations"]=[evaluation(checks=[m.GATES[0],m.GATES[0]])]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_32_unauthorized_free_text(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            r=evaluation();r["nom_professionnel"]="Nom Prive"
            doc["evaluations"]=[r]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_33_fake_official_phone_call(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            r=evaluation();r["autorite_professionnelle_contactee"]=True
            doc["evaluations"]=[r]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_34_fake_official_signature(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            r=evaluation();r["signature_officiellement_authentifiee"]=True
            doc["evaluations"]=[r]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_35_fake_financial_certification(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            r=evaluation();r["avis_financier_certifie"]=True
            doc["evaluations"]=[r]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_36_fake_approval(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            r=evaluation();r["decision_institutionnelle_autorisee"]=True
            doc["evaluations"]=[r]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_37_bad_outcome(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            doc["evaluations"]=[evaluation(outcome="APPROUVE")]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_38_need_reason_for_complement(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d)
            doc["evaluations"]=[evaluation(reason="AUCUNE_DECLAREE_NON_VERIFIEE")]
            with self.assertRaises(ValueError):m.validate_local(doc,raw,man,validated,states)
    def test_39_suspension_priority(self):
        source={CITY:"SUSPENSION_PRIORITAIRE"}
        values={(CITY,CPA):{"decision_preparatoire":"IRRECEVABILITE_PROVISOIRE",
             "reserve_declaree":"PIECES_INCOMPLETES"}}
        self.assertEqual(m.matrix(values,source)[1]["SUSPENSION_PRIORITAIRE"],1)
    def test_40_conflict_priority(self):
        source={CITY:"CONTRADICTION_OUVERTE"}
        values={(CITY,CPA):{"decision_preparatoire":"DEMANDER_COMPLEMENT",
             "reserve_declaree":"PIECES_INCOMPLETES"}}
        self.assertEqual(m.matrix(values,source)[1]["CONTRADICTION_OUVERTE"],1)
    def test_41_reservation_priority(self):
        source={CITY:"RESERVE_OUVERTE"}
        self.assertEqual(m.matrix(None,source)[1]["RESERVE_OUVERTE"],1)
    def test_42_provisional_refusal_noncertifying(self):
        values={(CITY,CPA):{"decision_preparatoire":"IRRECEVABILITE_PROVISOIRE",
             "reserve_declaree":"PIECES_INCOMPLETES"}}
        self.assertEqual(m.matrix(values)[1]["IRRECEVABILITE_PROVISOIRE_DECLAREE"],1)
    def test_43_no_private_id_in_public(self):
        with tempfile.TemporaryDirectory() as d:
            paths,raw,man,validated,states,doc=context(d,4)
            doc["evaluations"]=[evaluation(outcome="EXAMEN_FORMEL_NON_ATTESTE",
               reason="AUCUNE_DECLAREE_NON_VERIFIEE",checks=m.GATES)]
            r=m.report(self.cfg,m.validate_local(doc,raw,man,validated,states),states)
            dumped=json.dumps(r)
            self.assertNotIn(doc["sha256_fiche_p54l"],dumped)
            self.assertNotIn("PIECE-002",dumped)
            self.assertNotIn("attestation2.bin",dumped)
    def test_44_cli_neutral_report(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"public.json"
            self.assertEqual(m.main(["--bilan",str(path)]),0)
            self.assertEqual(json.loads(path.read_text("utf-8"))["statuts_recevabilite"],{"NON_INSTRUIT":4})
    def test_45_cli_express_refusal(self):
        self.assertEqual(m.main(["--exiger-decision"]),3)
    def test_46_cli_no_sources_for_eval(self):
        self.assertEqual(m.main(["--evaluations-locales","/tmp/nonexistent.json"]),2)
    def test_47_cli_generate_private_template(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"private.json"
            self.assertEqual(m.main(["--modele-prive",str(path)]),0)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o600)
    def test_48_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"public.json";path.write_text("preserve","utf-8")
            self.assertEqual(m.main(["--bilan",str(path)]),2)
            self.assertEqual(path.read_text("utf-8"),"preserve")
    def test_49_cli_full_chain_and_private_eval(self):
        with tempfile.TemporaryDirectory() as d:
            (files,p_l),raw,man,v,states,doc=context(d,4)
            doc["evaluations"]=[evaluation("EXAMEN_FORMEL_NON_ATTESTE",
               "AUCUNE_DECLAREE_NON_VERIFIEE",m.GATES)]
            local=Path(d)/"evaluation.json"
            local.write_text(json.dumps(doc),encoding="utf-8");os.chmod(local,0o600)
            out=Path(d)/"public.json"
            args=["--p54i",str(files[0]),"--p54j",str(files[1]),
                  "--p54k",str(files[2]),"--p54l",str(p_l),
                  "--evaluations-locales",str(local),"--bilan",str(out)]
            self.assertEqual(m.main(args),0)
            result=json.loads(out.read_text("utf-8"))
            self.assertEqual(result["evaluations_preparatoires_non_certifiantes"],1)
            self.assertEqual(result["signatures_authentifiees"],0)
    def test_50_cli_deny_public_local_eval(self):
        with tempfile.TemporaryDirectory() as d:
            (files,p_l),raw,man,v,states,doc=context(d)
            local=Path(d)/"eval.json"
            local.write_text(json.dumps(doc),encoding="utf-8");os.chmod(local,0o644)
            args=["--p54i",str(files[0]),"--p54j",str(files[1]),
                  "--p54k",str(files[2]),"--p54l",str(p_l),
                  "--evaluations-locales",str(local)]
            self.assertEqual(m.main(args),2)
    def test_51_cli_no_duplicate_source_alias(self):
        with tempfile.TemporaryDirectory() as d:
            (files,p_l),raw,man,v,states,doc=context(d)
            args=["--p54i",str(files[0]),"--p54j",str(files[1]),
                  "--p54k",str(files[2]),"--p54l",str(files[2])]
            self.assertEqual(m.main(args),2)

def guard_test(name):
    def check(self):self.assertTrue(self.cfg["protections"][name])
    return check
for i,name in enumerate(sorted(m.GUARDS),52):
    setattr(TestsP54M,"test_%02d_protection"%i,guard_test(name))

if __name__=="__main__":
    unittest.main()
