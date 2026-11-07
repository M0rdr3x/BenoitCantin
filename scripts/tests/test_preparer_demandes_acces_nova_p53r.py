#!/usr/bin/env python3
"""Tests P53R — six brouillons personnalisés et verrouillage absolu de l'envoi."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import preparer_demandes_acces_nova_p53r as m

def revue(code="66023"):
    return {
        "schema_version":"P53R-REVUE-1",
        "code_organisme":code,
        "procedure_responsable":"NON_EXAMINE",
        "reperage_public_preexistant":"NON_EXAMINE",
        "precision_documents":"NON_EXAMINE",
        "confidentialite_tiers":"NON_EXAMINE",
        "perimetre_juridique":"NON_EXAMINE",
        "services_et_emplois":"NON_EXAMINE",
        "autorisation_envoi":False,
    }

class TestP53R(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.parents=m.sources()
        cls.drafts=m.generate(cls.cfg,cls.parents)
        cls.by={r["code_organisme"]:r for r in cls.drafts}
    def status(self,x):return m.review(x)["statut"]

    def test_01_dossiers_6(self):self.assertEqual(len(self.parents),6)
    def test_02_six_brouillons(self):self.assertEqual(len(self.drafts),6)
    def test_03_codes_uniques(self):self.assertEqual(set(self.by),set(m.CODES))
    def test_04_exact_urls(self):self.assertTrue(all(self.by[k]["page_officielle_procedure"]==m.ACCESS[k][1] for k in m.CODES))
    def test_05_18_pieces_descriptives(self):self.assertEqual(sum(len(x["type_pieces_recherchees"]) for x in self.drafts),18)
    def test_06_3_par_organisme(self):self.assertTrue(all(len(x["type_pieces_recherchees"])==3 for x in self.drafts))
    def test_07_first_by_p53q(self):self.assertTrue(all(self.by[k]["type_pieces_recherchees"][0]==m.FIRST[k] for k in m.CODES))
    def test_08_drafts_never_sent(self):self.assertTrue(all(x["statut"]=="PROJET_NON_TRANSMIS" for x in self.drafts))
    def test_09_header_not_send(self):self.assertTrue(all(x["courrier_modele"].startswith("PROJET DE DEMANDE — NE PAS TRANSMETTRE") for x in self.drafts))
    def test_10_footer_not_send(self):self.assertTrue(all(x["courrier_modele"].endswith("FIN DU PROJET — NON ENVOYE\n") for x in self.drafts))
    def test_11_no_real_submission(self):self.assertTrue(all(x["date_depot_reel"] is None for x in self.drafts))
    def test_12_no_deadline_started(self):self.assertTrue(all(x["debut_delai_reponse"] is None for x in self.drafts))
    def test_13_no_named_recipient(self):self.assertTrue(all(x["destinataire_nominatif"] is None for x in self.drafts))
    def test_14_no_requester_address(self):self.assertTrue(all(x["adresse_personnelle_demandeur"] is None for x in self.drafts))
    def test_15_no_signature(self):self.assertTrue(all(x["signature"] is None for x in self.drafts))
    def test_16_no_authenticated_docs(self):self.assertTrue(all(x["preuves_recues_authentifiees"]==0 for x in self.drafts))
    def test_17_no_savings(self):self.assertTrue(all(x["economies_certifiees_cad"] is None for x in self.drafts))
    def test_18_no_go_by_letter(self):self.assertTrue(all(x["decision"]=="NO_GO_AUTOMATIQUE" for x in self.drafts))
    def test_19_mentions_documents_existants(self):self.assertTrue(all("documents existants" in x["courrier_modele"] for x in self.drafts))
    def test_20_mention_privacy(self):self.assertTrue(all("renseignements protégés" in x["courrier_modele"] for x in self.drafts))
    def test_21_no_new_calculation(self):self.assertTrue(all("aucun nouveau calcul" in x["courrier_modele"] for x in self.drafts))
    def test_22_review_default(self):self.assertEqual(self.status(revue()),"REVUE_HUMAINE_INCOMPLETE")
    def test_23_risk_blocks(self):
        x=revue();x["confidentialite_tiers"]="BLOCAGE_SIGNALE"
        self.assertEqual(self.status(x),"ARRET_REVUE_POUR_RISQUE_DECLARE")
    def test_24_services_risk_blocks(self):
        x=revue();x["services_et_emplois"]="BLOCAGE_SIGNALE"
        self.assertEqual(self.status(x),"ARRET_REVUE_POUR_RISQUE_DECLARE")
    def test_25_wrong_procedure_blocks(self):
        x=revue();x["procedure_responsable"]="BLOCAGE_SIGNALE"
        self.assertEqual(self.status(x),"ARRET_REVUE_POUR_RISQUE_DECLARE")
    def test_26_all_declared_still_no_send(self):
        x=revue()
        for k in ("procedure_responsable","reperage_public_preexistant",
                  "precision_documents","confidentialite_tiers",
                  "perimetre_juridique","services_et_emplois"):
            x[k]="VERIFICATION_DECLARATIVE_NON_AUTHENTIFIEE"
        self.assertEqual(self.status(x),"RELECTURE_DECLAREE_NON_AUTHENTIFIEE_SANS_DROIT_ENVOI")
    def test_27_no_send_flag_true(self):
        x=revue();x["autorisation_envoi"]=True
        with self.assertRaises(ValueError):self.status(x)
    def test_28_no_send_flag_missing(self):
        x=revue();del x["autorisation_envoi"]
        with self.assertRaises(ValueError):self.status(x)
    def test_29_bad_code(self):
        x=revue("AUTRE")
        with self.assertRaises(ValueError):self.status(x)
    def test_30_added_address_refused(self):
        x=revue();x["adresse"]="private"
        with self.assertRaises(ValueError):self.status(x)
    def test_31_fake_certification_refused(self):
        x=revue();x["precision_documents"]="CERTIFIE"
        with self.assertRaises(ValueError):self.status(x)
    def test_32_summary_six(self):self.assertEqual(m.summary(self.cfg,self.drafts,[])["projets_courriers_prepares"],6)
    def test_33_summary_18(self):self.assertEqual(m.summary(self.cfg,self.drafts,[])["descriptions_precises_documents"],18)
    def test_34_summary_102(self):self.assertEqual(m.summary(self.cfg,self.drafts,[])["emplacements_p53q_encore_a_documenter"],102)
    def test_35_no_respondent(self):self.assertEqual(m.summary(self.cfg,self.drafts,[])["accuses_de_reception_verifies"],0)
    def test_36_no_go(self):self.assertEqual(m.summary(self.cfg,self.drafts,[])["decision"],"NO_GO_AUTOMATIQUE")
    def test_37_no_money(self):self.assertIsNone(m.summary(self.cfg,self.drafts,[])["economies_certifiees_cad"])
    def test_38_cli_create_six(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"bilan.json",Path(td)/"courriers.json"
            self.assertEqual(m.main(["--bilan",str(a),"--courriers",str(b)]),0)
            self.assertEqual(len(json.loads(b.read_text("utf-8"))["courriers"]),6)
            self.assertEqual(json.loads(a.read_text("utf-8"))["descriptions_precises_documents"],18)
    def test_39_cli_strict_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(m.main(["--exiger-depot-confirme","--bilan",
                                     str(Path(td)/"result.json")]),3)
    def test_40_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            b.write_text("important","utf-8")
            self.assertEqual(m.main(["--bilan",str(a),"--courriers",str(b)]),2)
            self.assertFalse(a.exists());self.assertEqual(b.read_text("utf-8"),"important")
    def test_41_same_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"same.json"
            self.assertEqual(m.main(["--bilan",str(p),"--courriers",str(p)]),2)
    def test_42_declaration_safe(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"d.json";p.write_text(json.dumps(revue()),"utf-8")
            b=Path(td)/"b.json"
            self.assertEqual(m.main(["--revue",str(p),"--bilan",str(b)]),0)
            out=b.read_text("utf-8")
            self.assertNotIn("66023",out)
            self.assertNotIn("montreal.ca",out)
            self.assertIn("REVUE_HUMAINE_INCOMPLETE",out)
    def test_43_duplicate_declared_review(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"d.json";p.write_text(json.dumps(revue()),"utf-8")
            self.assertEqual(m.main(["--revue",str(p),"--revue",str(p)]),2)
    def test_44_two_independent_cases(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            a.write_text(json.dumps(revue("66023")),"utf-8")
            b.write_text(json.dumps(revue("T1025")),"utf-8")
            self.assertEqual(m.main(["--revue",str(a),"--revue",str(b)]),0)
    def test_45_different_letters(self):self.assertEqual(len({x["courrier_modele"] for x in self.drafts}),6)
    def test_46_quebec_rtc_double_count(self):self.assertTrue(all(
        "écritures réciproques" in self.by[code]["courrier_modele"]
        for code in ("23027","T0088")))
    def test_47_saint_valere_2024(self):self.assertIn("Saint-Valère",self.by["39135"]["courrier_modele"])
    def test_48_no_go_past_all_reviews(self):
        x=revue()
        for k in ("procedure_responsable","reperage_public_preexistant",
                  "precision_documents","confidentialite_tiers",
                  "perimetre_juridique","services_et_emplois"):
            x[k]="VERIFICATION_DECLARATIVE_NON_AUTHENTIFIEE"
        r=m.summary(self.cfg,self.drafts,[m.review(x)])
        self.assertIsNone(r["economies_certifiees_cad"])
        self.assertEqual(r["demandes_effectivement_envoyees"],0)

if __name__=="__main__":
    unittest.main()
