#!/usr/bin/env python3
"""P53N: tests de gouvernance documentaire, sans connexion aux organismes."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import preparer_acquisition_preuves_nova_p53n as m

def exemple(memo):
    return {
        "schema_version":"P53N-DECLARATION-1",
        "regime":m.REGIMES[0],
        "categorie":memo["categories"][0],
        "reference_exercice":2024,
        "nature_source":"INCONNUE",
        "documents":{p:"NON_DEMANDE" for p in m.TYPES},
        "garanties":{g:"INCONNU" for g in m.GARANTIES},
        "acces_licite":"INCONNU",
    }

class ControleP53N(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous,cls.cfg,cls.n,cls.k=m.sources()
        cls.rows=m.construire_registre(cls.cfg)
    def etat(self,d):
        return m.evaluer_declaration(d,self.cfg)["statut"]

    def test_01_source_1344(self):self.assertEqual(self.n,1344)
    def test_02_p53k_26(self):self.assertEqual(self.k,26)
    def test_03_twelve_cases(self):self.assertEqual(len(self.rows),12)
    def test_04_distinct_regimes(self):self.assertEqual(set(x["regime"] for x in self.rows),set(m.REGIMES))
    def test_05_six_categories(self):self.assertEqual(len(self.cfg["categories"]),6)
    def test_06_all_unique(self):self.assertEqual(len({(x["regime"],x["categorie"]) for x in self.rows}),12)
    def test_07_144_slots(self):self.assertEqual(sum(len(x["etat_pieces"]) for x in self.rows),144)
    def test_08_none_requested(self):self.assertTrue(all(set(x["etat_pieces"].values())=={"NON_DEMANDE"} for x in self.rows))
    def test_09_no_originals(self):self.assertTrue(all(x["originaux_authentifies"]==0 for x in self.rows))
    def test_10_all_guards_unknown(self):self.assertTrue(all(set(x["garanties"].values())=={"INCONNU"} for x in self.rows))
    def test_11_no_savings(self):self.assertTrue(all(x["economie_certifiee_cad"] is None for x in self.rows))
    def test_12_no_sent_claim(self):self.assertTrue(all(not x["envoi_reel_atteste"] for x in self.rows))
    def test_13_no_independent_review(self):self.assertTrue(all(not x["avis_independant_signe_valide"] for x in self.rows))
    def test_14_default_unknown_legal(self):self.assertEqual(self.etat(exemple(self.cfg)),"BASE_JURIDIQUE_ACCES_NON_DEMONTREE")
    def test_15_no_authorization(self):
        d=exemple(self.cfg);d["acces_licite"]="NON"
        self.assertEqual(self.etat(d),"ACCES_NON_AUTORISE_A_EXCLURE")
    def test_16_labor_violation(self):
        d=exemple(self.cfg);d["acces_licite"]="OUI_DECLARATIF";d["garanties"]["emplois_maintenus"]="NON"
        self.assertEqual(self.etat(d),"GARANTIES_VIOLEES")
    def test_17_services_violation(self):
        d=exemple(self.cfg);d["acces_licite"]="OUI_DECLARATIF";d["garanties"]["services_essentiels_continus"]="NON"
        self.assertEqual(self.etat(d),"GARANTIES_VIOLEES")
    def test_18_unknown_protection(self):
        d=exemple(self.cfg);d["acces_licite"]="OUI_DECLARATIF"
        self.assertEqual(self.etat(d),"PROTECTIONS_NON_DEMONTREES")
    def test_19_not_requested(self):
        d=exemple(self.cfg);d["acces_licite"]="OUI_DECLARATIF"
        d["garanties"]={k:"OUI" for k in m.GARANTIES}
        self.assertEqual(self.etat(d),"PIECES_NON_DEMANDEES")
    def test_20_prepared_not_sent(self):
        d=exemple(self.cfg);d["acces_licite"]="OUI_DECLARATIF"
        d["garanties"]={k:"OUI" for k in m.GARANTIES}
        d["documents"]={k:"DEMANDE_PREPAREE_NON_ENVOYEE" for k in m.TYPES}
        self.assertEqual(self.etat(d),"DEMANDES_PREPAREES_NON_TRANSMISES")
    def test_21_declared_sent_unverified(self):
        d=exemple(self.cfg);d["acces_licite"]="OUI_DECLARATIF"
        d["garanties"]={k:"OUI" for k in m.GARANTIES}
        d["documents"]={k:"ENVOI_DECLARE_NON_VERIFIE" for k in m.TYPES}
        self.assertEqual(self.etat(d),"ENVOI_DECLARE_A_VERIFIER")
    def test_22_response_claim_not_authenticated(self):
        d=exemple(self.cfg);d["acces_licite"]="OUI_DECLARATIF"
        d["garanties"]={k:"OUI" for k in m.GARANTIES}
        d["documents"]={k:"REPONSE_DECLAREE_NON_VERIFIEE" for k in m.TYPES}
        self.assertEqual(self.etat(d),"REPONSES_DECLAREES_A_AUTHENTIFIER")
    def test_23_declared_refusal_not_verification(self):
        d=exemple(self.cfg);d["acces_licite"]="OUI_DECLARATIF"
        d["garanties"]={k:"OUI" for k in m.GARANTIES}
        d["documents"]={k:"REFUS_DECLARE_NON_VERIFIE" for k in m.TYPES}
        self.assertEqual(self.etat(d),"REFUS_D_ACCES_DECLARE_A_EXAMINER")
    def test_24_found_public_still_declarative(self):
        d=exemple(self.cfg);d["acces_licite"]="OUI_DECLARATIF"
        d["garanties"]={k:"OUI" for k in m.GARANTIES}
        d["documents"]={k:"REPERE_PUBLIC_DECLARATIF" for k in m.TYPES}
        self.assertEqual(self.etat(d),"REPERAGE_PUBLIC_DECLARATIF_A_VERIFIER")
    def test_25_certified_state_refused(self):
        d=exemple(self.cfg);d["documents"][m.TYPES[0]]="CERTIFIEE"
        with self.assertRaises(ValueError):m.evaluer_declaration(d,self.cfg)
    def test_26_sent_claim_as_fact_refused(self):
        d=exemple(self.cfg);d["documents"][m.TYPES[0]]="DEMANDE_ENVOYEE_VERIFIEE"
        with self.assertRaises(ValueError):m.evaluer_declaration(d,self.cfg)
    def test_27_unexpected_private_attribute(self):
        d=exemple(self.cfg);d["adresse"]="Adresse test"
        with self.assertRaises(ValueError):m.evaluer_declaration(d,self.cfg)
    def test_28_missing_piece(self):
        d=exemple(self.cfg);del d["documents"][m.TYPES[0]]
        with self.assertRaises(ValueError):m.evaluer_declaration(d,self.cfg)
    def test_29_missing_guard(self):
        d=exemple(self.cfg);del d["garanties"][m.GARANTIES[0]]
        with self.assertRaises(ValueError):m.evaluer_declaration(d,self.cfg)
    def test_30_bad_exercise(self):
        d=exemple(self.cfg);d["reference_exercice"]=2027
        with self.assertRaises(ValueError):m.evaluer_declaration(d,self.cfg)
    def test_31_bad_regime(self):
        d=exemple(self.cfg);d["regime"]="AUTRE"
        with self.assertRaises(ValueError):m.evaluer_declaration(d,self.cfg)
    def test_32_bad_category(self):
        d=exemple(self.cfg);d["categorie"]="LICENCIEMENTS"
        with self.assertRaises(ValueError):m.evaluer_declaration(d,self.cfg)
    def test_33_bilan_no_go(self):
        self.assertEqual(m.bilan(self.cfg,self.n,self.k,[])["decision"],"NO_GO_AUTOMATIQUE")
    def test_34_never_proves_money(self):
        b=m.bilan(self.cfg,self.n,self.k,[m.evaluer_declaration(exemple(self.cfg),self.cfg)])
        self.assertIsNone(b["economies_certifiees_cad"])
        self.assertEqual(b["pieces_primaires_authentifiees"],0)
        self.assertEqual(b["demandes_effectivement_envoyees_verifiees"],0)
    def test_35_cli_generate(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,q=Path(tmp)/"a.json",Path(tmp)/"b.json"
            self.assertEqual(m.main(["--rapport",str(p),"--registre",str(q)]),0)
            self.assertEqual(json.loads(p.read_text())["emplacements_de_pieces_non_obtenues"],144)
            self.assertEqual(len(json.loads(q.read_text())["fiches"]),12)
    def test_36_cli_strict_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(m.main(["--exiger-preuves-certifiees","--rapport",
                                     str(Path(tmp)/"r.json")]),3)
    def test_37_never_overwrite_either_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,q=Path(tmp)/"a.json",Path(tmp)/"b.json"
            q.write_text("important",encoding="utf-8")
            self.assertEqual(m.main(["--rapport",str(p),"--registre",str(q)]),2)
            self.assertFalse(p.exists())
            self.assertEqual(q.read_text(encoding="utf-8"),"important")
    def test_38_declared_input_privacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"declaration.json"
            p.write_text(json.dumps(exemple(self.cfg)),encoding="utf-8")
            q=Path(tmp)/"rapport.json"
            self.assertEqual(m.main(["--declaration",str(p),"--rapport",str(q)]),0)
            txt=q.read_text(encoding="utf-8")
            self.assertNotIn(self.cfg["categories"][0],txt)
            self.assertNotIn("Adresse",txt)
    def test_39_duplicate_declared_regime_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"d.json"
            p.write_text(json.dumps(exemple(self.cfg)),encoding="utf-8")
            self.assertEqual(m.main(["--declaration",str(p),"--declaration",str(p)]),2)
    def test_40_same_regime_different_category_permitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=exemple(self.cfg)
            a,b=Path(tmp)/"a.json",Path(tmp)/"b.json"
            a.write_text(json.dumps(d),encoding="utf-8")
            d["categorie"]=self.cfg["categories"][1]
            b.write_text(json.dumps(d),encoding="utf-8")
            self.assertEqual(m.main(["--declaration",str(a),"--declaration",str(b)]),0)
    def test_41_same_category_different_regime_permitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=exemple(self.cfg)
            a,b=Path(tmp)/"a.json",Path(tmp)/"b.json"
            a.write_text(json.dumps(d),encoding="utf-8")
            d["regime"]=m.REGIMES[1]
            b.write_text(json.dumps(d),encoding="utf-8")
            self.assertEqual(m.main(["--declaration",str(a),"--declaration",str(b)]),0)
    def test_42_no_same_output_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"duplicate.json"
            self.assertEqual(m.main(["--rapport",str(p),"--registre",str(p)]),2)
            self.assertFalse(p.exists())

if __name__=="__main__":
    unittest.main()
