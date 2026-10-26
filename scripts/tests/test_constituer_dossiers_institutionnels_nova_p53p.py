#!/usr/bin/env python3
"""P53P: sources réelles, périmètres consolidés et refus de l'économie fictive."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import constituer_dossiers_institutionnels_nova_p53p as m

def declaration(code="66023"):
    return {
        "schema_version":"P53P-DECLARATION-1",
        "code_organisme":code,
        "etat_reperage":"NON_CONSULTE",
        "perimetre_verifie":"INCONNU",
        "transaction_2024_documentee":"INCONNU",
        "elimination_anterieure_verifiee":"INCONNU",
        "protection_emplois_services":"INCONNU",
        "acces_aux_pieces":"INCONNU",
    }

class P53P(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.rows,cls.h,cls.i=m.load()
        cls.cases=m.build(cls.cfg,cls.rows,cls.h,cls.i)
        cls.by={d["code_organisme"]:d for d in cls.cases}
    def state(self,d):
        return m.evaluer(d,self.cfg)["statut"]

    def test_01_six_dossiers(self):self.assertEqual(len(self.cases),6)
    def test_02_source_1344(self):self.assertEqual(len(self.rows),1344)
    def test_03_top25_stable(self):self.assertEqual(len(self.h["priorites_relecture"]),25)
    def test_04_top5_exact(self):self.assertEqual([r["code_organisme"] for r in self.cases[:5]],list(m.CODES[:5]))
    def test_05_rangs(self):self.assertEqual([r["rang_historique_p53h"] for r in self.cases[:5]],[1,2,3,4,5])
    def test_06_saint_valere_exception(self):self.assertEqual(self.cases[-1]["code_organisme"],"39135")
    def test_07_saint_valere_hors_rang(self):self.assertIsNone(self.cases[-1]["rang_historique_p53h"])
    def test_08_saint_valere_zero(self):self.assertEqual(self.cases[-1]["quotes_parts_recues_2024_cad"],"0")
    def test_09_saint_valere_transfers(self):self.assertEqual(self.cases[-1]["transferts_recus_2024_cad"],"503955")
    def test_10_garder_blanc_stm(self):self.assertIsNone(self.by["T0081"]["quotes_parts_recues_2024_cad"])
    def test_11_montreal_rang(self):self.assertEqual(self.by["66023"]["rang_historique_p53h"],1)
    def test_12_organisme_artm(self):self.assertEqual(self.by["T1025"]["nom_organisme"],"Autorité régionale de transport métropolitain")
    def test_13_organisme_rtc(self):self.assertEqual(self.by["T0088"]["nom_organisme"],"Réseau de transport de la Capitale")
    def test_14_consolidation_quebec(self):self.assertEqual(self.by["23027"]["constat_documentaire"],"RTC_CONSOLIDE_ET_RECIPROQUES_DEJA_ELIMINEES")
    def test_15_consolidation_rtc(self):self.assertEqual(self.by["T0088"]["constat_documentaire"],"RTC_CONSOLIDE_ET_RECIPROQUES_DEJA_ELIMINEES")
    def test_16_same_official_pdf_quebec_rtc(self):self.assertTrue(all(
        any(s["id"]=="QUEBEC_RF_2024" for s in self.by[code]["sources_publiques_candidats"])
        for code in ("23027","T0088")))
    def test_17_non_double_elimination(self):self.assertTrue(all(
        self.by[c]["controle_double_elimination"]=="OBLIGATOIRE_DEJA_SIGNALEE_DANS_RF_QUEBEC_2024"
        for c in ("23027","T0088")))
    def test_18_eight_allowed_links(self):self.assertEqual(len(m.SOURCES),8)
    def test_19_all_urls_official(self):self.assertTrue(all(s["url"] in m.SOURCES.values() for r in self.cases for s in r["sources_publiques_candidats"]))
    def test_20_every_case_mamh(self):self.assertTrue(all(
        "MAMH_PORTAIL" in (s["id"] for s in r["sources_publiques_candidats"]) for r in self.cases))
    def test_21_no_primary_piece(self):self.assertTrue(all(
        all(not s["authentification_transactionnelle"] for s in r["sources_publiques_candidats"]) for r in self.cases))
    def test_22_missing_twelve(self):self.assertTrue(all(
        len(r["pieces_p53n"])==12 and set(r["pieces_p53n"].values())=={"NON_OBTENUE"} for r in self.cases))
    def test_23_no_money_certified(self):self.assertTrue(all(r["economie_budgetaire_certifiee_cad"] is None for r in self.cases))
    def test_24_no_matching(self):self.assertTrue(all(r["appariement_transactionnel_certifie"] is False for r in self.cases))
    def test_25_guard_employment(self):self.assertTrue(all(r["garde_fous_emplois_et_services"]=="A_DEMONTRER" for r in self.cases))
    def test_26_default_undetermined(self):self.assertEqual(self.state(declaration()),"PERIMETRE_NON_ETABLI")
    def test_27_access_block(self):
        d=declaration();d["acces_aux_pieces"]="NON"
        self.assertEqual(self.state(d),"ACCES_AUX_PIECES_NON_AUTORISE")
    def test_28_employment_block(self):
        d=declaration();d["protection_emplois_services"]="NON"
        self.assertEqual(self.state(d),"REFUS_EMPLOIS_SERVICES")
    def test_29_quebec_specific_guard(self):
        d=declaration("23027");d["perimetre_verifie"]="DECLARE_NON_VERIFIE"
        self.assertEqual(self.state(d),"CONTROLE_CONSOLIDATION_DEJA_PUBLIEE_A_RECONCILIER")
    def test_30_rtc_specific_guard(self):
        d=declaration("T0088");d["perimetre_verifie"]="DECLARE_NON_VERIFIE"
        self.assertEqual(self.state(d),"CONTROLE_CONSOLIDATION_DEJA_PUBLIEE_A_RECONCILIER")
    def test_31_pending_transaction(self):
        d=declaration();d["perimetre_verifie"]="DECLARE_NON_VERIFIE"
        self.assertEqual(self.state(d),"CONTREPARTIES_TRANSACTIONNELLES_NON_ETABLIES")
    def test_32_declared_data_not_certified(self):
        d=declaration();d["perimetre_verifie"]="DECLARE_NON_VERIFIE"
        d["transaction_2024_documentee"]="DECLARE_NON_VERIFIE"
        self.assertEqual(self.state(d),"DECLARATIONS_NON_AUTHENTIFIEES_A_REVISER")
    def test_33_claim_certification_refused(self):
        d=declaration();d["perimetre_verifie"]="CERTIFIE"
        with self.assertRaises(ValueError):self.state(d)
    def test_34_claim_2024_proof_refused(self):
        d=declaration();d["transaction_2024_documentee"]="AUTHENTIFIE"
        with self.assertRaises(ValueError):self.state(d)
    def test_35_banned_extra_metadata(self):
        d=declaration();d["grand_livre_id"]="SECRET"
        with self.assertRaises(ValueError):self.state(d)
    def test_36_unknown_code_refused(self):
        d=declaration("12345")
        with self.assertRaises(ValueError):self.state(d)
    def test_37_status_no_go(self):self.assertEqual(
        m.summary(self.cfg,self.cases,[])["decision"],"NO_GO_AUTOMATIQUE")
    def test_38_no_financial_certification(self):self.assertIsNone(
        m.summary(self.cfg,self.cases,[])["economies_certifiees_cad"])
    def test_39_two_already_consolidated(self):self.assertEqual(
        m.summary(self.cfg,self.cases,[])["cas_consolidation_reciproque_deja_signalee"],2)
    def test_40_test_cli_generates(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"bilan.json",Path(td)/"dossiers.json"
            self.assertEqual(m.main(["--bilan",str(a),"--dossiers",str(b)]),0)
            self.assertEqual(json.loads(a.read_text("utf-8"))["dossiers_institutionnels_p53p"],6)
            self.assertEqual(len(json.loads(b.read_text("utf-8"))["dossiers"]),6)
    def test_41_test_cli_refuses_certification(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(m.main(["--exiger-economies-certifiees","--bilan",
                                     str(Path(td)/"r.json")]),3)
    def test_42_never_overwrite_existing(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            b.write_text("keep","utf-8")
            self.assertEqual(m.main(["--bilan",str(a),"--dossiers",str(b)]),2)
            self.assertFalse(a.exists());self.assertEqual(b.read_text("utf-8"),"keep")
    def test_43_same_output_path_denied(self):
        with tempfile.TemporaryDirectory() as td:
            x=Path(td)/"dup.json"
            self.assertEqual(m.main(["--bilan",str(x),"--dossiers",str(x)]),2)
    def test_44_declared_input_aggregates_only(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"d.json";f.write_text(json.dumps(declaration()),"utf-8")
            out=Path(td)/"b.json"
            self.assertEqual(m.main(["--declaration",str(f),"--bilan",str(out)]),0)
            text=out.read_text("utf-8")
            self.assertNotIn("66023",text);self.assertIn("PERIMETRE_NON_ETABLI",text)
    def test_45_duplicate_code_refused(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"d.json";f.write_text(json.dumps(declaration()),"utf-8")
            self.assertEqual(m.main(["--declaration",str(f),"--declaration",str(f)]),2)
    def test_46_two_distinct_codes_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            a.write_text(json.dumps(declaration("66023")),"utf-8")
            b.write_text(json.dumps(declaration("T1025")),"utf-8")
            self.assertEqual(m.main(["--declaration",str(a),"--declaration",str(b)]),0)

if __name__=="__main__":
    unittest.main()
