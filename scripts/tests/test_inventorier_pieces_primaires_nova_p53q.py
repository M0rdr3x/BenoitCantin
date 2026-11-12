#!/usr/bin/env python3
"""P53Q — Tests de complétude et de refus de certification."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import inventorier_pieces_primaires_nova_p53q as m

def exemple(code="66023",piece=None):
    return {
        "schema_version":"P53Q-DECLARATION-1",
        "code_organisme":code,
        "type_piece":piece or m.DOCUMENTS[0],
        "etat_declaratif":"NON_OBTENUE",
        "acces_legal":"INCONNU",
        "garanties_emplois_services":"INCONNU",
        "perimetre_comptable":"INCONNU",
    }

class ControleP53Q(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c,cls.dossiers=m.sources()
        cls.lines=m.registre(cls.c,cls.dossiers)
        cls.by={(x["code_organisme"],x["type_piece"]):x for x in cls.lines}
    def status(self,d):return m.evaluer_declaration(d)["statut"]
    def test_01_six_organisations(self):self.assertEqual(len(self.dossiers),6)
    def test_02_tops_cinq(self):self.assertEqual([x["code_organisme"] for x in self.dossiers[:5]],list(m.precedent.CODES[:5]))
    def test_03_saint_valere_last(self):self.assertEqual(self.dossiers[-1]["code_organisme"],"39135")
    def test_04_17_types(self):self.assertEqual(len(m.DOCUMENTS),17)
    def test_05_102_records(self):self.assertEqual(len(self.lines),102)
    def test_06_no_duplicated_records(self):self.assertEqual(len(self.by),102)
    def test_07_17_each(self):
        self.assertTrue(all(sum(x["code_organisme"]==k for x in self.lines)==17 for k in m.precedent.CODES))
    def test_08_six_first_documents(self):self.assertEqual(sum(x["est_premiere_piece_a_chercher"] for x in self.lines),6)
    def test_09_priorite_montreal(self):self.assertTrue(self.by["66023","perimetre_de_consolidation_2024"]["est_premiere_piece_a_chercher"])
    def test_10_priorite_artm(self):self.assertTrue(self.by["T1025","entente_resolution_et_avenants"]["est_premiere_piece_a_chercher"])
    def test_11_priorite_quebec(self):self.assertTrue(self.by["23027","eliminations_deja_comptabilisees"]["est_premiere_piece_a_chercher"])
    def test_12_priorite_stm(self):self.assertTrue(self.by["T0081","indicateurs_qualite_accessibilite_service"]["est_premiere_piece_a_chercher"])
    def test_13_priorite_rtc(self):self.assertTrue(self.by["T0088","eliminations_deja_comptabilisees"]["est_premiere_piece_a_chercher"])
    def test_14_priorite_stvalere(self):self.assertTrue(self.by["39135","etats_financiers_2024_version_originelle"]["est_premiere_piece_a_chercher"])
    def test_15_one_priority_rank_each(self):
        self.assertTrue(all(sorted(x["priorite_locale"] for x in self.lines if x["code_organisme"]==k)==list(range(1,18)) for k in m.precedent.CODES))
    def test_16_no_auth(self):self.assertTrue(all(not x["preuve_originale_authentifiee"] for x in self.lines))
    def test_17_no_amount(self):self.assertTrue(all(x["montant_economie_certifiee_cad"] is None for x in self.lines))
    def test_18_missing_not_zero(self):self.assertTrue(all(x["statut_acquisition"]=="NON_OBTENUE" for x in self.lines))
    def test_19_no_owner_invented(self):self.assertTrue(all(x["detenteur_legal"]=="A_IDENTIFIER" for x in self.lines))
    def test_20_no_ledger_references(self):self.assertTrue(all(x["numero_ecriture"]=="NON_RÉCOLTÉ" for x in self.lines))
    def test_21_rtc_legal_guard(self):self.assertTrue(self.by["T0088","eliminations_deja_comptabilisees"]["double_elimination_risque_connue"])
    def test_22_quebec_legal_guard(self):self.assertTrue(self.by["23027","eliminations_deja_comptabilisees"]["double_elimination_risque_connue"])
    def test_23_no_false_other_double(self):self.assertFalse(self.by["66023","eliminations_deja_comptabilisees"]["double_elimination_risque_connue"])
    def test_24_same_p53p_sources(self):self.assertTrue(all(x["source_de_reperage_p53p"] for x in self.lines))
    def test_25_default_status(self):self.assertEqual(self.status(exemple()),"PERIMETRE_EN_ATTENTE")
    def test_26_quebec_guard_precedes_unknown(self):self.assertEqual(self.status(exemple("23027")),"VERIFICATION_DOUBLE_ELIMINATION_PRIORITAIRE")
    def test_27_rtc_guard_precedes_unknown(self):self.assertEqual(self.status(exemple("T0088")),"VERIFICATION_DOUBLE_ELIMINATION_PRIORITAIRE")
    def test_28_non_authorized_access(self):
        x=exemple();x["acces_legal"]="NON_AUTORISE"
        self.assertEqual(self.status(x),"ARRET_ACCES_NON_AUTORISE")
    def test_29_jobs_violation(self):
        x=exemple();x["garanties_emplois_services"]="NON"
        self.assertEqual(self.status(x),"ARRET_EMPLOIS_SERVICES")
    def test_30_social_unknown(self):
        x=exemple();x["perimetre_comptable"]="DECLARE_NON_VERIFIE"
        self.assertEqual(self.status(x),"GARANTIES_SOCIALES_A_VERIFIER")
    def test_31_not_obtained(self):
        x=exemple();x["perimetre_comptable"]="DECLARE_NON_VERIFIE"
        x["garanties_emplois_services"]="OUI_DECLARE_NON_VERIFIE"
        self.assertEqual(self.status(x),"PIECE_NON_OBTENUE")
    def test_32_prepared_not_sent(self):
        x=exemple();x["perimetre_comptable"]="DECLARE_NON_VERIFIE"
        x["garanties_emplois_services"]="OUI_DECLARE_NON_VERIFIE"
        x["etat_declaratif"]="DEMANDE_PREPAREE_NON_ENVOYEE"
        self.assertEqual(self.status(x),"DEMANDE_NON_TRANSMISE")
    def test_33_response_not_authenticated(self):
        x=exemple();x["perimetre_comptable"]="DECLARE_NON_VERIFIE"
        x["garanties_emplois_services"]="OUI_DECLARE_NON_VERIFIE"
        x["etat_declaratif"]="RECEPTION_DECLAREE_NON_VERIFIEE"
        self.assertEqual(self.status(x),"RECEPTION_NON_AUTHENTIFIEE")
    def test_34_declared_refusal(self):
        x=exemple();x["perimetre_comptable"]="DECLARE_NON_VERIFIE"
        x["garanties_emplois_services"]="OUI_DECLARE_NON_VERIFIE"
        x["etat_declaratif"]="REFUS_DECLARE_NON_VERIFIE"
        self.assertEqual(self.status(x),"REFUS_DECLARATIF_A_EXAMINER")
    def test_35_denied_fake_certification(self):
        x=exemple();x["etat_declaratif"]="DOCUMENT_CERTIFIE"
        with self.assertRaises(ValueError):self.status(x)
    def test_36_denied_fake_legal_ok(self):
        x=exemple();x["acces_legal"]="ACCES_AUTORISE_CERTIFIE"
        with self.assertRaises(ValueError):self.status(x)
    def test_37_denied_fake_services_ok(self):
        x=exemple();x["garanties_emplois_services"]="OUI_CERTIFIE"
        with self.assertRaises(ValueError):self.status(x)
    def test_38_denied_fake_scope(self):
        x=exemple();x["perimetre_comptable"]="VERIFIE"
        with self.assertRaises(ValueError):self.status(x)
    def test_39_denied_unknown_code(self):
        x=exemple("99999")
        with self.assertRaises(ValueError):self.status(x)
    def test_40_denied_unknown_piece(self):
        x=exemple(piece="FAUSSE_ECONOMIE")
        with self.assertRaises(ValueError):self.status(x)
    def test_41_denied_private_account(self):
        x=exemple();x["compte_bancaire"]="SECRET"
        with self.assertRaises(ValueError):self.status(x)
    def test_42_no_go_bilan(self):
        d=m.bilan(self.c,self.dossiers,[])
        self.assertEqual(d["decision"],"NO_GO_AUTOMATIQUE")
        self.assertIsNone(d["economies_certifiees_cad"])
    def test_43_bilan_102(self):self.assertEqual(m.bilan(self.c,self.dossiers,[])["emplacements_documentaires"],102)
    def test_44_zero_originals(self):self.assertEqual(m.bilan(self.c,self.dossiers,[])["originaux_transactionnels_authentifies"],0)
    def test_45_cli_generates(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"b.json",Path(td)/"i.json"
            self.assertEqual(m.main(["--bilan",str(a),"--inventaire",str(b)]),0)
            self.assertEqual(json.loads(a.read_text("utf-8"))["emplacements_documentaires"],102)
            self.assertEqual(len(json.loads(b.read_text("utf-8"))["entrees"]),102)
    def test_46_cli_forbidden_cert(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(m.main(["--exiger-preuves-certifiees","--bilan",str(Path(td)/"r.json")]),3)
    def test_47_no_overwrite_either(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            b.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(a),"--inventaire",str(b)]),2)
            self.assertFalse(a.exists())
            self.assertEqual(b.read_text("utf-8"),"keep")
    def test_48_same_outputs_denied(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/"same.json"
            self.assertEqual(m.main(["--bilan",str(a),"--inventaire",str(a)]),2)
    def test_49_safe_declared_output(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"declaration.json";f.write_text(json.dumps(exemple()),"utf-8")
            b=Path(td)/"bilan.json"
            self.assertEqual(m.main(["--declaration",str(f),"--bilan",str(b)]),0)
            s=b.read_text("utf-8")
            self.assertNotIn("66023",s)
            self.assertNotIn("competence_et_identite_juridique",s)
            self.assertIn("PERIMETRE_EN_ATTENTE",s)
    def test_50_duplicate_declaration_denied(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"e.json";f.write_text(json.dumps(exemple()),"utf-8")
            self.assertEqual(m.main(["--declaration",str(f),"--declaration",str(f)]),2)
    def test_51_two_pieces_same_org_are_separate(self):
        with tempfile.TemporaryDirectory() as td:
            f,g=Path(td)/"f.json",Path(td)/"g.json"
            f.write_text(json.dumps(exemple()),"utf-8")
            g.write_text(json.dumps(exemple(piece=m.DOCUMENTS[1])),"utf-8")
            self.assertEqual(m.main(["--declaration",str(f),"--declaration",str(g)]),0)
    def test_52_saint_valere_missing_not_2027(self):
        self.assertTrue(all(x["exercice"]==2024 for x in self.lines if x["code_organisme"]=="39135"))

if __name__=="__main__":
    unittest.main()
