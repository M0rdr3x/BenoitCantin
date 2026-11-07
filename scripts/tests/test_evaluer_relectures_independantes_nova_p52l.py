"""P52L: tests adversariaux du journal de décisions non authentifiées."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"evaluer_relectures_independantes_nova_p52l.py"
spec=importlib.util.spec_from_file_location("nova_p52l",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
HASH="a"*64
REPORT="b"*64
N=0

def setup():
    d={key:m.load_json(path) for key,path in m.FILES.items()}
    refs=m.controler_referentiel(d)
    return d,refs

def event(i,operation,actor,role,doc=HASH,proof="F09",regime="TOUS",
          conflict=False,ref=REPORT):
    return {"index":i,"preuve_id":proof,"operation":operation,"acteur_ref":actor,
            "role":role,"date_utc":f"2026-10-19T20:{i:02d}:00Z",
            "document_sha256":doc,"piece_action_sha256":ref,
            "regime":regime,"conflit_signale":conflict}

def sequences():
    return [
       event(1,"DEPOSER","A-DEP001","DEPOSANT"),
       event(2,"CONTROLER","A-VER002","VERIFICATEUR"),
       event(3,"AVIS","A-EXP003","EXPERT_INDEPENDANT"),
       event(4,"PROPOSER_DECISION","A-AUT004","AUTORITE_PROPOSEE")
    ]

class ControleP52L(unittest.TestCase):
    def check_invalid(self,fn):
        data,refs=setup()
        ev=sequences()
        fn(data,ev)
        data["journal"]["evenements"]=ev
        with self.assertRaises(ValueError):m.evaluer_journal(refs,data["journal"])

    def test_01_20_unique_sources(self):
        d,r=setup();self.assertEqual(len({x["id"] for x in r}),20)
    def test_02_20_default_unreceived(self):
        d,r=setup();self.assertEqual(m.evaluer_journal(r,d["journal"])["stades_declaratifs"]["NON_RECUE"],20)
    def test_03_no_external_attestation(self):
        d,r=setup();self.assertEqual(m.evaluer_journal(r,d["journal"])["attestations_humaines_authentifiees"],0)
    def test_04_no_automatic_adoption(self):
        d,r=setup();self.assertEqual(m.evaluer_journal(r,d["journal"])["decision"],"NO_GO_AUTOMATIQUE")
    def test_05_no_ratings_or_savings(self):
        d,r=setup();self.assertFalse(m.evaluer_journal(r,d["journal"])["validation_juridique_et_budgetaire_demontrée"])
    def test_06_depot_advances_only_to_unverified(self):
        d,r=setup();d["journal"]["evenements"]=sequences()[:1]
        self.assertEqual(m.evaluer_journal(r,d["journal"])["stades_declaratifs"]["RECUE_A_CONTROLER"],1)
    def test_07_document_control_not_independent_attestation(self):
        d,r=setup();d["journal"]["evenements"]=sequences()[:2]
        self.assertEqual(m.evaluer_journal(r,d["journal"])["attestations_humaines_authentifiees"],0)
    def test_08_avis_declared_not_authentic(self):
        d,r=setup();d["journal"]["evenements"]=sequences()[:3]
        self.assertEqual(m.evaluer_journal(r,d["journal"])["stades_declaratifs"]["AVIS_INDEPENDANT_DECLARE"],1)
    def test_09_decision_proposed_never_authorizes(self):
        d,r=setup();d["journal"]["evenements"]=sequences()
        out=m.evaluer_journal(r,d["journal"])
        self.assertEqual(out["stades_declaratifs"]["PROPOSITION_DE_DECISION_NON_AUTHENTIFIEE"],1)
        self.assertFalse(out["fusion_autorisee"])
    def test_10_contestation_pauses_decision(self):
        d,r=setup();ev=sequences()[:3]
        ev.append(event(4,"CONTESTER","A-CON005","CONTRADICTEUR"))
        d["journal"]["evenements"]=ev
        self.assertEqual(m.evaluer_journal(r,d["journal"])["stades_declaratifs"]["EN_CONTESTATION"],1)
    def test_11_resolution_requires_new_review(self):
        d,r=setup();ev=sequences()[:3]
        ev.append(event(4,"CONTESTER","A-CON005","CONTRADICTEUR"))
        ev.append(event(5,"RESOUDRE","A-RES006","CONTROLEUR_CONTESTATION"))
        d["journal"]["evenements"]=ev
        self.assertEqual(m.evaluer_journal(r,d["journal"])["stades_declaratifs"]["REEXAMEN_REQUIS"],1)
    def test_12_reexamination_can_reenter_after_second_review(self):
        d,r=setup();ev=sequences()[:3]
        ev += [event(4,"CONTESTER","A-CON005","CONTRADICTEUR"),
               event(5,"RESOUDRE","A-RES006","CONTROLEUR_CONTESTATION"),
               event(6,"CONTROLER","A-VER007","VERIFICATEUR"),
               event(7,"AVIS","A-EXP008","EXPERT_INDEPENDANT")]
        d["journal"]["evenements"]=ev
        self.assertEqual(m.evaluer_journal(r,d["journal"])["stades_declaratifs"]["AVIS_INDEPENDANT_DECLARE"],1)
    def test_13_author_cannot_self_review(self):
        self.check_invalid(lambda d,e:e[1].update(acteur_ref="A-DEP001"))
    def test_14_author_cannot_self_give_opinion(self):
        self.check_invalid(lambda d,e:e[2].update(acteur_ref="A-DEP001"))
    def test_15_document_checker_cannot_give_opinion(self):
        self.check_invalid(lambda d,e:e[2].update(acteur_ref="A-VER002"))
    def test_16_proposer_cannot_be_same_as_opinion(self):
        self.check_invalid(lambda d,e:e[3].update(acteur_ref="A-EXP003"))
    def test_17_conflict_in_opinion_rejected(self):
        self.check_invalid(lambda d,e:e[2].update(conflit_signale=True))
    def test_18_conflict_in_proposal_rejected(self):
        self.check_invalid(lambda d,e:e[3].update(conflit_signale=True))
    def test_19_changed_document_hash_rejected(self):
        self.check_invalid(lambda d,e:e[2].update(document_sha256="c"*64))
    def test_20_changed_jurisdiction_rejected(self):
        self.check_invalid(lambda d,e:e[2].update(regime="QUEBEC_SOUVERAIN"))
    def test_21_sha_format_rejected(self):
        self.check_invalid(lambda d,e:e[0].update(document_sha256="abcd"))
    def test_22_event_extra_private_field_rejected(self):
        self.check_invalid(lambda d,e:e[0].update(email="personnel@example.com"))
    def test_23_unknown_proof_rejected(self):
        self.check_invalid(lambda d,e:e[0].update(preuve_id="F99"))
    def test_24_unknown_role_rejected(self):
        self.check_invalid(lambda d,e:e[0].update(role="SUPERUSER"))
    def test_25_nonsequential_index_rejected(self):
        self.check_invalid(lambda d,e:e[2].update(index=22))
    def test_26_invalid_time_rejected(self):
        self.check_invalid(lambda d,e:e[2].update(date_utc="2026-10-19T24:00:00Z"))
    def test_27_backward_time_rejected(self):
        self.check_invalid(lambda d,e:e[2].update(date_utc="2026-10-19T19:00:00Z"))
    def test_28_fictional_verified_expert_rejected(self):
        d,r=setup();d["matrice"]["exigences"][8]["identite_expert_authentifiee"]=True
        with self.assertRaises(ValueError):m.controler_referentiel(d)
    def test_29_fictional_signed_judgment_rejected(self):
        d,r=setup();d["matrice"]["exigences"][8]["decision_humaine_signee"]=True
        with self.assertRaises(ValueError):m.controler_referentiel(d)
    def test_30_mismatched_themes_rejected(self):
        d,r=setup();d["matrice"]["exigences"][8]["theme"]="autre"
        with self.assertRaises(ValueError):m.controler_referentiel(d)
    def test_31_p52a_faux_go_rejected(self):
        d,r=setup();d["preuves"]["automatic_go"]=True
        with self.assertRaises(ValueError):m.controler_referentiel(d)
    def test_32_p52i_faux_certification_rejected(self):
        d,r=setup();d["pistes"]["donnees_extraites_certifiees"]=True
        with self.assertRaises(ValueError):m.controler_referentiel(d)
    def test_33_p52k_faux_hash_rejected(self):
        d,r=setup();d["provenance"]["fichiers_source"][0]["empreinte_sha256_pdf_original"]="e"*64
        with self.assertRaises(ValueError):m.controler_referentiel(d)
    def test_34_journal_faux_human_authorization_rejected(self):
        d,r=setup();d["journal"]["autorisation_humaine_obtenue"]=True
        with self.assertRaises(ValueError):m.evaluer_journal(r,d["journal"])
    def test_35_privacy_no_actor_or_digest_in_output(self):
        d,r=setup();d["journal"]["evenements"]=sequences()
        out=json.dumps(m.evaluer_journal(r,d["journal"]),ensure_ascii=False)
        for x in ("A-DEP001","A-EXP003","https://",HASH,REPORT):
            self.assertNotIn(x,out)
    def test_36_cli_normal_gives_no_go(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"result.json"
            self.assertEqual(m.main(["--rapport",str(dest)]),0)
            self.assertEqual(json.loads(dest.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_37_cli_strict_returns_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(m.main(["--exiger-validation","--rapport",str(Path(tmp)/"r.json")]),3)
    def test_38_cli_missing_file_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(m.main(["--matrice",str(Path(tmp)/"no.json")]),2)
    def test_39_cli_never_overwrites_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"r.json"
            self.assertEqual(m.main(["--rapport",str(path)]),0)
            self.assertEqual(m.main(["--rapport",str(path)]),2)
    def test_40_resolution_by_depositor_refused(self):
        d,r=setup();ev=sequences()[:3]
        ev += [event(4,"CONTESTER","A-CON005","CONTRADICTEUR"),
               event(5,"RESOUDRE","A-DEP001","CONTROLEUR_CONTESTATION")]
        d["journal"]["evenements"]=ev
        with self.assertRaises(ValueError):m.evaluer_journal(r,d["journal"])
    def test_41_unresolved_contestation_cannot_propose(self):
        d,r=setup();ev=sequences()[:3]
        ev += [event(4,"CONTESTER","A-CON005","CONTRADICTEUR"),
               event(5,"PROPOSER_DECISION","A-AUT004","AUTORITE_PROPOSEE")]
        d["journal"]["evenements"]=ev
        with self.assertRaises(ValueError):m.evaluer_journal(r,d["journal"])
    def test_42_no_proposal_without_opinion(self):
        d,r=setup();ev=sequences()[:2]
        ev.append(event(3,"PROPOSER_DECISION","A-AUT004","AUTORITE_PROPOSEE"))
        d["journal"]["evenements"]=ev
        with self.assertRaises(ValueError):m.evaluer_journal(r,d["journal"])
    def test_43_no_f20_data_reclassified(self):
        d,r=setup()
        e=event(1,"DEPOSER","A-DEP001","DEPOSANT",
                proof="F20",regime="TOUS")
        d["journal"]["evenements"]=[e]
        out=m.evaluer_journal(r,d["journal"])
        self.assertEqual(out["stades_declaratifs"]["RECUE_A_CONTROLER"],1)
        self.assertEqual(out["decisions_formelles_authentifiees"],0)
    def test_44_no_synthetic_approval_through_proposal(self):
        d,r=setup();d["journal"]["evenements"]=sequences()
        result=m.evaluer_journal(r,d["journal"])
        self.assertFalse(result["autorisation_publique_et_adoption"])
        self.assertEqual(result["decision"],"NO_GO_AUTOMATIQUE")

if __name__=="__main__":
    unittest.main()
