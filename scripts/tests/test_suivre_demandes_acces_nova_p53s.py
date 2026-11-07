#!/usr/bin/env python3
"""P53S : sécurité du journal de suivi, intégrité de séquence et absence de certification."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import suivre_demandes_acces_nova_p53s as m

H="a"*64

def event(typ="PREPARATION_SANS_DEPOT",code="66023",day=None):
    first=typ=="PREPARATION_SANS_DEPOT"
    ident=typ=="IDENTIFICATION_RESPONSABLE_DECLAREE"
    return {
        "schema_version":"P53S-EVENEMENT-1",
        "code_organisme":code,
        "phase":typ,
        "date_declaree":None if first else
            ("2026-10-22" if day is None else day),
        "classe_justificatif":m.CLASSES[typ],
        "reference_conservation_externe_presente":not (first or ident),
        "empreinte_sha256_declaree":None if first or ident else H,
        "examen_humain":"NON_EFFECTUE",
        "droit_acces":"INCONNU",
        "protections_emplois_services":"INCONNU",
    }

def declared_chain(code="66023"):
    return [event("PREPARATION_SANS_DEPOT",code),
            event("IDENTIFICATION_RESPONSABLE_DECLAREE",code),
            event("ENVOI_DECLARE_NON_VERIFIE",code),
            event("RECEPTION_DECLAREE_NON_VERIFIEE",code)]

class TestP53S(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.prior=m.sources()
        cls.plan=m.plan(cls.cfg,cls.prior)
    def inspect(self,items):
        return m.inspect_events(items)
    def test_01_six_dossiers(self):self.assertEqual(len(self.plan),6)
    def test_02_registre_unique(self):self.assertEqual(len({x["code_organisme"] for x in self.plan}),6)
    def test_03_11_types(self):self.assertEqual(len(m.TYPES),11)
    def test_04_66_slots(self):self.assertEqual(sum(len(x["evenements_a_tracer"]) for x in self.plan),66)
    def test_05_18_requests(self):self.assertEqual(sum(len(x["documents_recherches"]) for x in self.plan),18)
    def test_06_not_sent(self):self.assertTrue(all(x["statut_reel"]=="AUCUNE_DEMANDE_EFFECTIVEMENT_ENVOYEE" for x in self.plan))
    def test_07_no_real_date(self):self.assertTrue(all(x["date_reception_reelle"] is None for x in self.plan))
    def test_08_no_real_due(self):self.assertTrue(all(x["echeance_reponse_reelle"] is None for x in self.plan))
    def test_09_no_real_appeal_date(self):self.assertTrue(all(x["date_ouverture_recours_reelle"] is None for x in self.plan))
    def test_10_no_originals(self):self.assertTrue(all(not any(s["document_original_authentifie"] for s in x["evenements_a_tracer"]) for x in self.plan))
    def test_11_no_money(self):self.assertTrue(all(x["economie_certifiee_cad"] is None for x in self.plan))
    def test_12_quebec_rtc_guard(self):self.assertTrue(all(x["preuve_consolidation_quebec_rtc"]=="A_RAPPROCHER_SANS_DOUBLE_ELIMINATION" for x in self.plan if x["code_organisme"] in ("23027","T0088")))
    def test_13_legal_days_20(self):self.assertEqual(self.cfg["base_legale"]["delai_initial_jours_civils"],20)
    def test_14_extension_10(self):self.assertEqual(self.cfg["base_legale"]["prolongation_max_jours"],10)
    def test_15_appeal_30(self):self.assertEqual(self.cfg["base_legale"]["recours_indicatif_jours"],30)
    def test_16_zero_journal(self):self.assertEqual(self.inspect([])["evenements_examines"],0)
    def test_17_prep(self):self.assertEqual(self.inspect([event()])["evenements_examines"],1)
    def test_18_ident_after_prep(self):self.assertEqual(self.inspect(declared_chain()[:2])["evenements_examines"],2)
    def test_19_send_only_after_ident(self):self.assertEqual(self.inspect(declared_chain()[:3])["evenements_examines"],3)
    def test_20_recv_only_after_sent(self):self.assertEqual(self.inspect(declared_chain())["evenements_examines"],4)
    def test_21_declared_recv_is_not_attested(self):
        s=self.inspect(declared_chain())
        self.assertEqual(s["statuts_agreges"]["ETAPE_DECLAREE_NON_AUTHENTIFIEE"],4)
    def test_22_extension_after_recv(self):
        self.assertEqual(self.inspect(declared_chain()+[event("PROLONGATION_DECLAREE_NON_VERIFIEE")])["evenements_examines"],5)
    def test_23_part_response_after_recv(self):
        self.assertEqual(self.inspect(declared_chain()+[event("REPONSE_PARTIELLE_DECLAREE_NON_VERIFIEE")])["evenements_examines"],5)
    def test_24_complete_response_after_recv(self):
        self.assertEqual(self.inspect(declared_chain()+[event("REPONSE_COMPLETE_DECLAREE_NON_VERIFIEE")])["evenements_examines"],5)
    def test_25_refusal_after_recv(self):
        self.assertEqual(self.inspect(declared_chain()+[event("REFUS_DECLARE_NON_VERIFIE")])["evenements_examines"],5)
    def test_26_silence_after_recv(self):
        self.assertEqual(self.inspect(declared_chain()+[event("SILENCE_DECLARE_SANS_DELAI_VERIFIE")])["evenements_examines"],5)
    def test_27_appeal_after_refusal(self):
        self.assertEqual(self.inspect(declared_chain()+[event("REFUS_DECLARE_NON_VERIFIE"),event("RECOURS_DECLARE_NON_VERIFIE")])["evenements_examines"],6)
    def test_28_appeal_after_silence(self):
        self.assertEqual(self.inspect(declared_chain()+[event("SILENCE_DECLARE_SANS_DELAI_VERIFIE"),event("RECOURS_DECLARE_NON_VERIFIE")])["evenements_examines"],6)
    def test_29_archival_after_response(self):
        self.assertEqual(self.inspect(declared_chain()+[event("REPONSE_COMPLETE_DECLAREE_NON_VERIFIEE"),event("ARCHIVAGE_DECLARE_NON_VERIFIE")])["evenements_examines"],6)
    def test_30_no_appeal_no_response(self):
        with self.assertRaises(ValueError):self.inspect(declared_chain()+[event("RECOURS_DECLARE_NON_VERIFIE")])
    def test_31_no_receipt_without_sent(self):
        with self.assertRaises(ValueError):self.inspect([event("RECEPTION_DECLAREE_NON_VERIFIEE")])
    def test_32_no_send_without_preparation(self):
        with self.assertRaises(ValueError):self.inspect([event("ENVOI_DECLARE_NON_VERIFIE")])
    def test_33_no_extension_without_receipt(self):
        with self.assertRaises(ValueError):self.inspect([event("PROLONGATION_DECLAREE_NON_VERIFIEE")])
    def test_34_no_duplicate(self):
        with self.assertRaises(ValueError):self.inspect([event(),event()])
    def test_35_two_different_codes(self):self.assertEqual(self.inspect([event(),event(code="T1025")])["organismes_avec_declarations"],2)
    def test_36_bad_date(self):
        e=event("ENVOI_DECLARE_NON_VERIFIE",day="2026-02-30")
        with self.assertRaises(ValueError):m.validate_event(e)
    def test_37_bad_date_shape(self):
        e=event("ENVOI_DECLARE_NON_VERIFIE",day="22/10/2026")
        with self.assertRaises(ValueError):m.validate_event(e)
    def test_38_wrong_hash(self):
        e=event("ENVOI_DECLARE_NON_VERIFIE");e["empreinte_sha256_declaree"]="wrong"
        with self.assertRaises(ValueError):m.validate_event(e)
    def test_39_missing_hash(self):
        e=event("ENVOI_DECLARE_NON_VERIFIE");e["empreinte_sha256_declaree"]=None
        with self.assertRaises(ValueError):m.validate_event(e)
    def test_40_missing_extern_ref(self):
        e=event("ENVOI_DECLARE_NON_VERIFIE");e["reference_conservation_externe_presente"]=False
        with self.assertRaises(ValueError):m.validate_event(e)
    def test_41_false_class(self):
        e=event("RECEPTION_DECLAREE_NON_VERIFIEE");e["classe_justificatif"]="TRACE_ENVOI"
        with self.assertRaises(ValueError):m.validate_event(e)
    def test_42_fake_attested(self):
        e=event();e["examen_humain"]="AUTHENTIFIE"
        with self.assertRaises(ValueError):m.validate_event(e)
    def test_43_personal_info(self):
        e=event();e["courriel"]="private@example.invalid"
        with self.assertRaises(ValueError):m.validate_event(e)
    def test_44_bad_code(self):
        e=event(code="fake")
        with self.assertRaises(ValueError):m.validate_event(e)
    def test_45_prep_fake_date(self):
        e=event();e["date_declaree"]="2026-10-22"
        with self.assertRaises(ValueError):m.validate_event(e)
    def test_46_bool_presence(self):
        e=event();e["reference_conservation_externe_presente"]="false"
        with self.assertRaises(ValueError):m.validate_event(e)
    def test_47_stop_no_permission(self):
        e=event();e["droit_acces"]="NON_AUTORISE"
        self.assertEqual(self.inspect([e])["statuts_agreges"]["ARRET_DECLARE_NON_VERIFIE"],1)
    def test_48_stop_jobs_services(self):
        e=event();e["protections_emplois_services"]="RISQUE_SIGNALE"
        self.assertEqual(self.inspect([e])["statuts_agreges"]["ARRET_DECLARE_NON_VERIFIE"],1)
    def test_49_no_progress_after_stop(self):
        items=declared_chain()[:2]
        items[0]["droit_acces"]="NON_AUTORISE"
        with self.assertRaises(ValueError):self.inspect(items)
    def test_50_chronology_backward(self):
        items=declared_chain()
        items[2]["date_declaree"]="2026-10-22"
        items[3]["date_declaree"]="2026-10-21"
        with self.assertRaises(ValueError):self.inspect(items)
    def test_51_no_early_document(self):
        e=event("ENVOI_DECLARE_NON_VERIFIE",day="2023-12-31")
        with self.assertRaises(ValueError):m.validate_event(e)
    def test_52_bilan_no_go(self):
        b=m.bilan(self.cfg,self.plan,self.inspect(declared_chain()))
        self.assertEqual(b["decision"],"NO_GO_AUTOMATIQUE")
        self.assertEqual(b["demandes_reellement_envoyees_verifiees"],0)
    def test_53_bilan_deadline_zero(self):self.assertEqual(m.bilan(self.cfg,self.plan,self.inspect(declared_chain()))["echeances_reponse_calculables"],0)
    def test_54_bilan_proves_no_savings(self):self.assertIsNone(m.bilan(self.cfg,self.plan,self.inspect(declared_chain()))["economies_certifiees_cad"])
    def test_55_cli_two_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/"bilan.json",Path(tmp)/"plan.json"
            self.assertEqual(m.main(["--bilan",str(a),"--registre",str(b)]),0)
            self.assertEqual(json.loads(a.read_text("utf-8"))["positions_de_suivi"],66)
            self.assertEqual(len(json.loads(b.read_text("utf-8"))["dossiers"]),6)
    def test_56_cli_strict_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(m.main(["--exiger-envoi-ou-reception-verifie","--bilan",str(Path(tmp)/"b.json")]),3)
    def test_57_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/"b.json",Path(tmp)/"plan.json"
            b.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(a),"--registre",str(b)]),2)
            self.assertFalse(a.exists())
            self.assertEqual(b.read_text("utf-8"),"keep")
    def test_58_cli_duplicate_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/"b.json"
            self.assertEqual(m.main(["--bilan",str(a),"--registre",str(a)]),2)
    def test_59_cli_declared_meta_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/"e.json";f.write_text(json.dumps(event()),"utf-8")
            p=Path(tmp)/"b.json"
            self.assertEqual(m.main(["--evenement",str(f),"--bilan",str(p)]),0)
            s=p.read_text("utf-8")
            self.assertNotIn("66023",s)
            self.assertNotIn("2026-10-22",s)
            self.assertNotIn(H,s)
            self.assertIn("evenements_declares_non_authentifies",s)
    def test_60_cli_bad_sequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/"e.json";f.write_text(json.dumps(event("RECEPTION_DECLAREE_NON_VERIFIEE")),"utf-8")
            self.assertEqual(m.main(["--evenement",str(f)]),2)
    def test_61_legal_unknown_when_no_verified_receipt(self):
        b=m.bilan(self.cfg,self.plan,self.inspect(declared_chain()))
        self.assertEqual(b["delais_legaux_declenches"],0)
        self.assertEqual(b["echeances_recours_calculables"],0)
    def test_62_no_appeal_certified_with_declared_journal(self):
        records=declared_chain()+[event("REFUS_DECLARE_NON_VERIFIE"),event("RECOURS_DECLARE_NON_VERIFIE")]
        b=m.bilan(self.cfg,self.plan,self.inspect(records))
        self.assertEqual(b["recours_reellement_deposes_verifies"],0)
    def test_63_no_public_personal_or_hash(self):
        serialized=json.dumps(self.plan)
        self.assertNotIn(H,serialized)
        self.assertNotIn("private@example.invalid",serialized)
    def test_64_no_authority_to_merge(self):
        self.assertFalse(m.bilan(self.cfg,self.plan,self.inspect([]))["fusion_autorisee"])

if __name__=="__main__":
    unittest.main()
