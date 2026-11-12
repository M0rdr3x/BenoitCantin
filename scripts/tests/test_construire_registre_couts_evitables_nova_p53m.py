#!/usr/bin/env python3
"""Tests P53M : séparation des régimes et refus des économies inventées."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import construire_registre_couts_evitables_nova_p53m as m

def fictif():
    return {
        "schema_version":"P53M-FICHE-1",
        "id_fiche":"TEST-01","regime":"QUEBEC_DANS_LE_CANADA",
        "categorie":"ACHATS_REGROUPES_SANS_EXCLUSION",
        "perimetre_budgetaire":"ORG-TEST","poste_budgetaire":"BUDGET-TEST",
        "exercice_reference":2024,"projection":2027,
        "statut_source":"DECLARATION_NON_AUTHENTIFIEE",
        "preuves":{x:"NON_OBTENUE" for x in m.PREUVES},
        "protections":{x:"INCONNU" for x in m.precedent.PROTECTIONS},
        "scenario_p53l":None
    }

def scenario(f):
    f["scenario_p53l"]={
        "schema_version":"P53L-MESURE-1",
        "identifiant_mesure":f["id_fiche"],
        "categorie":f["categorie"],"annee_reference":2024,
        "annee_projection":2027,"prix_constants":"CAD_CONSTANTS_2024",
        "mois_comparables":12,"perimetre_reference":f["perimetre_budgetaire"],
        "perimetre_projection":f["perimetre_budgetaire"],
        "poste_budgetaire":f["poste_budgetaire"],"origine":"HYPOTHESE",
        "type_flux":"DEPENSE_FONCTIONNEMENT",
        "montants":{
            "cout_annuel_reference_cad":"100.00",
            "cout_annuel_projection_cad":"70.00",
            "cout_recurrent_additionnel_cad":"5",
            "cout_initial_transition_cad":"10",
            "cout_transfere_citoyens_cad":"0",
            "cout_transfere_entreprises_cad":"0",
            "cout_transfere_autres_organismes_cad":"0"
        },
        "protections":dict(f["protections"])
    }
    return f

class P53M(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.l,cls.cfg,cls.nb,cls.nd=m.sources()

    def exam(self,f):
        return m.examiner(f,self.l,self.cfg)

    def test_01_source_1344(self):self.assertEqual(self.nb,1344)
    def test_02_documents_26(self):self.assertEqual(self.nd,26)
    def test_03_twelve_entries(self):self.assertEqual(len(m.catalogue(self.cfg)),12)
    def test_04_two_regimes(self):self.assertEqual(
        set(x["regime"] for x in m.catalogue(self.cfg)),set(m.REGIMES))
    def test_05_six_categories(self):self.assertEqual(len(self.cfg["categories"]),6)
    def test_06_unique_fiches(self):self.assertEqual(
        len({(x["regime"],x["categorie"]) for x in m.catalogue(self.cfg)}),12)
    def test_07_no_fabricated_amounts(self):self.assertTrue(
        all(x["economie_certifiee_cad"] is None for x in m.catalogue(self.cfg)))
    def test_08_missing_is_not_zero(self):self.assertTrue(
        all(x["cout_reference_cad"] is None for x in m.catalogue(self.cfg)))
    def test_09_proof_not_obtained(self):self.assertTrue(
        all(set(x["preuves"].values())=={"NON_OBTENUE"} for x in m.catalogue(self.cfg)))
    def test_10_guard_unknown(self):self.assertTrue(
        all(set(x["protections"].values())=={"INCONNU"} for x in m.catalogue(self.cfg)))
    def test_11_default_status(self):self.assertEqual(
        self.exam(fictif())["etat"],"PROTECTIONS_NON_DEMONTREES")
    def test_12_workforce_block(self):
        f=fictif();f["protections"]["emplois_maintenus"]="NON"
        self.assertEqual(self.exam(f)["etat"],"PROTECTIONS_VIOLEES")
    def test_13_service_block(self):
        f=fictif();f["protections"]["services_essentiels_continus"]="NON"
        self.assertEqual(self.exam(f)["etat"],"PROTECTIONS_VIOLEES")
    def test_14_unknown_veto(self):
        f=fictif();f["preuves"]={k:"DECLAREE_NON_AUTHENTIFIEE" for k in m.PREUVES}
        self.assertEqual(self.exam(f)["etat"],"PROTECTIONS_NON_DEMONTREES")
    def test_15_missing_document(self):
        f=fictif();f["protections"]={k:"OUI" for k in m.precedent.PROTECTIONS}
        self.assertEqual(self.exam(f)["etat"],"PREUVES_MANQUANTES")
    def test_16_no_scenario(self):
        f=fictif();f["protections"]={k:"OUI" for k in m.precedent.PROTECTIONS}
        f["preuves"]={k:"DECLAREE_NON_AUTHENTIFIEE" for k in m.PREUVES}
        self.assertEqual(self.exam(f)["etat"],"SCENARIO_ABSENT")
    def test_17_positive_still_uncertified(self):
        f=fictif();f["protections"]={k:"OUI" for k in m.precedent.PROTECTIONS}
        f["preuves"]={k:"DECLAREE_NON_AUTHENTIFIEE" for k in m.PREUVES}
        self.assertEqual(self.exam(scenario(f))["etat"],"HYPOTHESE_POSITIVE_NON_CERTIFIEE")
    def test_18_certified_sum_always_null(self):
        f=fictif();f["protections"]={k:"OUI" for k in m.precedent.PROTECTIONS}
        f["preuves"]={k:"DECLAREE_NON_AUTHENTIFIEE" for k in m.PREUVES}
        self.assertIsNone(self.exam(scenario(f))["montant_certifie_cad"])
    def test_19_certification_claim_rejected(self):
        f=fictif();f["statut_source"]="CERTIFIE"
        with self.assertRaises(ValueError):self.exam(f)
    def test_20_wrong_regime_rejected(self):
        f=fictif();f["regime"]="NON_RECONNU"
        with self.assertRaises(ValueError):self.exam(f)
    def test_21_bad_year(self):
        f=fictif();f["exercice_reference"]=2025
        with self.assertRaises(ValueError):self.exam(f)
    def test_22_bad_projection(self):
        f=fictif();f["projection"]=2028
        with self.assertRaises(ValueError):self.exam(f)
    def test_23_unknown_category(self):
        f=fictif();f["categorie"]="REDUIRE_HOPITAUX"
        with self.assertRaises(ValueError):self.exam(f)
    def test_24_fake_authenticated_proof(self):
        f=fictif();f["preuves"]["avis_independant"]="VALIDEE"
        with self.assertRaises(ValueError):self.exam(f)
    def test_25_missing_proof_key(self):
        f=fictif();del f["preuves"]["base_comptable"]
        with self.assertRaises(ValueError):self.exam(f)
    def test_26_missing_protection_key(self):
        f=fictif();del f["protections"]["acces_humain_maintenu"]
        with self.assertRaises(ValueError):self.exam(f)
    def test_27_scenario_different_id(self):
        f=scenario(fictif());f["scenario_p53l"]["identifiant_mesure"]="AUTRE"
        with self.assertRaises(ValueError):self.exam(f)
    def test_28_scenario_different_scope(self):
        f=scenario(fictif());f["scenario_p53l"]["perimetre_reference"]="AUTRE"
        with self.assertRaises(ValueError):self.exam(f)
    def test_29_scenario_different_protection(self):
        f=scenario(fictif());f["scenario_p53l"]["protections"]["emplois_maintenus"]="OUI"
        with self.assertRaises(ValueError):self.exam(f)
    def test_30_summary_no_go(self):
        self.assertEqual(m.bilan(self.cfg,self.nb,self.nd,[])["decision"],"NO_GO_AUTOMATIQUE")
    def test_31_regime_never_summed(self):
        self.assertEqual(m.bilan(self.cfg,self.nb,self.nd,[])["economies_certifiees_par_regime_cad"],
                         {x:None for x in m.REGIMES})
    def test_32_report_no_private_id(self):
        self.assertNotIn("TEST-01",json.dumps(m.bilan(self.cfg,self.nb,self.nd,[self.exam(fictif())])))
    def test_33_cli_generates(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"bilan.json",Path(td)/"registre.json"
            self.assertEqual(m.main(["--bilan",str(a),"--registre",str(b)]),0)
            self.assertEqual(len(json.loads(b.read_text(encoding="utf-8"))["fiches"]),12)
    def test_34_cli_strict_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(m.main(["--exiger-certification","--bilan",
                                     str(Path(td)/"bilan.json")]),3)
    def test_35_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"bilan.json";p.write_text("garder",encoding="utf-8")
            self.assertEqual(m.main(["--bilan",str(p)]),2)
            self.assertEqual(p.read_text(encoding="utf-8"),"garder")
    def test_36_cli_local_input_not_leaked(self):
        with tempfile.TemporaryDirectory() as td:
            f=fictif();f["protections"]={k:"OUI" for k in m.precedent.PROTECTIONS}
            f["preuves"]={k:"DECLAREE_NON_AUTHENTIFIEE" for k in m.PREUVES}
            p=Path(td)/"fiche.json";p.write_text(json.dumps(scenario(f)),encoding="utf-8")
            dest=Path(td)/"sortie.json"
            self.assertEqual(m.main(["--fiche",str(p),"--bilan",str(dest)]),0)
            s=dest.read_text(encoding="utf-8")
            self.assertNotIn("TEST-01",s);self.assertNotIn("100.00",s)
    def test_37_cli_duplicate_id(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            f=fictif();a.write_text(json.dumps(f),encoding="utf-8")
            f["poste_budgetaire"]="POSTE2";b.write_text(json.dumps(f),encoding="utf-8")
            self.assertEqual(m.main(["--fiche",str(a),"--fiche",str(b)]),2)
    def test_38_cli_duplicate_scope(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            f=fictif();a.write_text(json.dumps(f),encoding="utf-8")
            f["id_fiche"]="TEST-02";b.write_text(json.dumps(f),encoding="utf-8")
            self.assertEqual(m.main(["--fiche",str(a),"--fiche",str(b)]),2)
    def test_39_compare_two_regimes_without_merging(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            f=fictif();a.write_text(json.dumps(f),encoding="utf-8")
            f["id_fiche"]="TEST-02";f["regime"]="QUEBEC_SOUVERAIN_HYPOTHETIQUE"
            b.write_text(json.dumps(f),encoding="utf-8")
            self.assertEqual(m.main(["--fiche",str(a),"--fiche",str(b)]),0)

if __name__=="__main__":
    unittest.main()
