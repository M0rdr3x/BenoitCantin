#!/usr/bin/env python3
"""Tests P53L: arithmetique indicative seulement, aucun gain certifie."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import evaluer_hypotheses_economies_nova_p53l as m

def modele():
    return {
        "schema_version":"P53L-MESURE-1",
        "identifiant_mesure":"EXEMPLE-SYNTHETIQUE-01",
        "categorie":"ACHATS_REGROUPES_SANS_EXCLUSION",
        "annee_reference":2024,"annee_projection":2027,
        "prix_constants":"CAD_CONSTANTS_2024","mois_comparables":12,
        "perimetre_reference":"PERIMETRE-TEST",
        "perimetre_projection":"PERIMETRE-TEST",
        "poste_budgetaire":"POSTE-TEST","origine":"HYPOTHESE",
        "type_flux":"DEPENSE_FONCTIONNEMENT",
        "montants":{
            "cout_annuel_reference_cad":"100.00",
            "cout_annuel_projection_cad":"70.00",
            "cout_recurrent_additionnel_cad":"5.00",
            "cout_initial_transition_cad":"10.00",
            "cout_transfere_citoyens_cad":"0",
            "cout_transfere_entreprises_cad":"0",
            "cout_transfere_autres_organismes_cad":"0"},
        "protections":{k:"OUI" for k in m.PROTECTIONS},
    }

class VerificationsP53L(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules, cls.orgs, cls.dossiers = m.ouvrir_sources()

    def evaluer(self, item):
        return m.evaluer(item, self.rules)

    def test_01_organismes(self):
        self.assertEqual(self.orgs,1344)

    def test_02_dossiers_anterieurs(self):
        self.assertEqual(self.dossiers,26)

    def test_03_six_pistes(self):
        self.assertEqual(len(self.rules["categories"]),6)

    def test_04_catalogue_no_false_data(self):
        d=m.catalogue(self.rules)
        self.assertEqual(len(d["pistes"]),6)
        self.assertTrue(all(x["economies_certifiees_cad"] is None for x in d["pistes"]))

    def test_05_positive_only_hypothetical(self):
        status, values=self.evaluer(modele())
        self.assertEqual(status,"HYPOTHESE_POSITIVE_NON_CERTIFIEE")
        self.assertEqual(values,(m.Decimal("25"),m.Decimal("15")))

    def test_06_zero_transition_baseline(self):
        d=modele()
        d["montants"]["cout_initial_transition_cad"]="0"
        self.assertEqual(self.evaluer(d)[1][1],m.Decimal("25"))

    def test_07_negative_real_balance(self):
        d=modele()
        d["montants"]["cout_recurrent_additionnel_cad"]="32"
        self.assertEqual(self.evaluer(d)[0],"AUCUN_GAIN_RECURRENT_INDICATIF")

    def test_08_transition_larger_than_first_year(self):
        d=modele()
        d["montants"]["cout_initial_transition_cad"]="100"
        self.assertEqual(self.evaluer(d)[0],"COUT_INITIAL_NON_COUVERT_PREMIER_EXERCICE")

    def test_09_missing_amount_not_zero(self):
        d=modele()
        d["montants"]["cout_initial_transition_cad"]=None
        self.assertEqual(self.evaluer(d)[0],"COUT_COMPLET_INCONNU")

    def test_10_missing_baseline(self):
        d=modele()
        d["montants"]["cout_annuel_reference_cad"]=None
        self.assertEqual(self.evaluer(d)[0],"COUT_COMPLET_INCONNU")

    def test_11_no_layoffs(self):
        d=modele()
        d["protections"]["emplois_maintenus"]="NON"
        self.assertEqual(self.evaluer(d)[0],"GARANTIE_SOCIALE_OU_SERVICE_VIOLEE")

    def test_12_no_reduced_hours(self):
        d=modele()
        d["protections"]["heures_contractuelles_maintenues"]="NON"
        self.assertEqual(self.evaluer(d)[0],"GARANTIE_SOCIALE_OU_SERVICE_VIOLEE")

    def test_13_wages_safe(self):
        d=modele()
        d["protections"]["salaires_et_conditions_maintenus"]="NON"
        self.assertEqual(self.evaluer(d)[0],"GARANTIE_SOCIALE_OU_SERVICE_VIOLEE")

    def test_14_services_safe(self):
        d=modele()
        d["protections"]["qualite_service_maintenue"]="NON"
        self.assertEqual(self.evaluer(d)[0],"GARANTIE_SOCIALE_OU_SERVICE_VIOLEE")

    def test_15_timeliness_safe(self):
        d=modele()
        d["protections"]["delais_service_non_degrades"]="NON"
        self.assertEqual(self.evaluer(d)[0],"GARANTIE_SOCIALE_OU_SERVICE_VIOLEE")

    def test_16_human_access(self):
        d=modele()
        d["protections"]["acces_humain_maintenu"]="NON"
        self.assertEqual(self.evaluer(d)[0],"GARANTIE_SOCIALE_OU_SERVICE_VIOLEE")

    def test_17_essential_services(self):
        d=modele()
        d["protections"]["services_essentiels_continus"]="NON"
        self.assertEqual(self.evaluer(d)[0],"GARANTIE_SOCIALE_OU_SERVICE_VIOLEE")

    def test_18_rights_preserved(self):
        d=modele()
        d["protections"]["droits_et_recours_maintenus"]="NON"
        self.assertEqual(self.evaluer(d)[0],"GARANTIE_SOCIALE_OU_SERVICE_VIOLEE")

    def test_19_unknown_not_accepted(self):
        d=modele()
        d["protections"]["emplois_maintenus"]="INCONNU"
        self.assertEqual(self.evaluer(d)[0],"GARANTIE_SOCIALE_OU_SERVICE_INCONNUE")

    def test_20_transfer_to_households(self):
        d=modele()
        d["montants"]["cout_transfere_citoyens_cad"]="1"
        self.assertEqual(self.evaluer(d)[0],"TRANSFERT_DE_COUTS_INTERDIT")

    def test_21_transfer_to_business(self):
        d=modele()
        d["montants"]["cout_transfere_entreprises_cad"]="1"
        self.assertEqual(self.evaluer(d)[0],"TRANSFERT_DE_COUTS_INTERDIT")

    def test_22_transfer_to_municipalities(self):
        d=modele()
        d["montants"]["cout_transfere_autres_organismes_cad"]="1"
        self.assertEqual(self.evaluer(d)[0],"TRANSFERT_DE_COUTS_INTERDIT")

    def test_23_accounting_elimination(self):
        d=modele()
        d["type_flux"]="ELIMINATION_COMPTABLE"
        self.assertEqual(self.evaluer(d)[0],"SIMPLE_ECRITURE_OU_TRANSFERT_NON_ECONOMIE")

    def test_24_transfer_not_savings(self):
        d=modele()
        d["type_flux"]="TRANSFERT_INTERORGANISMES"
        self.assertEqual(self.evaluer(d)[0],"SIMPLE_ECRITURE_OU_TRANSFERT_NON_ECONOMIE")

    def test_25_year_mismatch(self):
        d=modele()
        d["annee_reference"]=2025
        with self.assertRaises(ValueError):self.evaluer(d)

    def test_26_price_mismatch(self):
        d=modele()
        d["prix_constants"]="CAD_NOMINAL_2027"
        with self.assertRaises(ValueError):self.evaluer(d)

    def test_27_scope_mismatch(self):
        d=modele()
        d["perimetre_projection"]="AUTRE"
        with self.assertRaises(ValueError):self.evaluer(d)

    def test_28_unknown_category(self):
        d=modele()
        d["categorie"]="SUPPRESSION_DE_POSTES"
        with self.assertRaises(ValueError):self.evaluer(d)

    def test_29_bad_amount(self):
        d=modele()
        d["montants"]["cout_annuel_reference_cad"]="-1"
        with self.assertRaises(ValueError):self.evaluer(d)

    def test_30_wrong_amount_structure(self):
        d=modele()
        del d["montants"]["cout_initial_transition_cad"]
        with self.assertRaises(ValueError):self.evaluer(d)

    def test_31_report_remains_no_go(self):
        s=m.synthese(self.rules,self.orgs,self.dossiers,["HYPOTHESE_POSITIVE_NON_CERTIFIEE"])
        self.assertEqual(s["decision"],"NO_GO_AUTOMATIQUE")
        self.assertIsNone(s["economies_annuelles_certifiees_cad"])

    def test_32_no_monies_in_report(self):
        s=m.synthese(self.rules,self.orgs,self.dossiers,["HYPOTHESE_POSITIVE_NON_CERTIFIEE"])
        self.assertNotIn("25.00",json.dumps(s))
        self.assertEqual(s["postes_supprimes_autorises"],0)

    def test_33_cli_generated_catalogue(self):
        with tempfile.TemporaryDirectory() as td:
            report=Path(td)/"bilan.json"
            catalog=Path(td)/"pistes.json"
            self.assertEqual(m.main(["--rapport",str(report),"--catalogue",str(catalog)]),0)
            self.assertEqual(json.loads(report.read_text())["pistes_non_documentees"],6)
            self.assertEqual(len(json.loads(catalog.read_text())["pistes"]),6)

    def test_34_cli_strict_code_3(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(m.main(["--exiger-economies-certifiees",
                                     "--rapport",str(Path(td)/"strict.json")]),3)

    def test_35_cli_refuses_existing_file(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"existant.json"
            path.write_text("intact",encoding="utf-8")
            self.assertEqual(m.main(["--rapport",str(path)]),2)
            self.assertEqual(path.read_text(encoding="utf-8"),"intact")

    def test_36_cli_hypothesis_not_public_money(self):
        with tempfile.TemporaryDirectory() as td:
            measure=Path(td)/"test.json"
            measure.write_text(json.dumps(modele()),encoding="utf-8")
            report=Path(td)/"agg.json"
            self.assertEqual(m.main(["--mesure",str(measure),"--rapport",str(report)]),0)
            r=report.read_text(encoding="utf-8")
            self.assertIn("HYPOTHESE_POSITIVE_NON_CERTIFIEE",r)
            self.assertNotIn("EXEMPLE-SYNTHETIQUE-01",r)
            self.assertNotIn("25.00",r)

    def test_37_cli_duplicate_budget_line(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            x,y=modele(),modele()
            y["identifiant_mesure"]="EXEMPLE-SYNTHETIQUE-02"
            a.write_text(json.dumps(x),encoding="utf-8")
            b.write_text(json.dumps(y),encoding="utf-8")
            self.assertEqual(m.main(["--mesure",str(a),"--mesure",str(b)]),2)

    def test_38_cli_duplicate_measure_id(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            x,y=modele(),modele()
            y["poste_budgetaire"]="LIGNE-DIFFERENTE"
            a.write_text(json.dumps(x),encoding="utf-8")
            b.write_text(json.dumps(y),encoding="utf-8")
            self.assertEqual(m.main(["--mesure",str(a),"--mesure",str(b)]),2)

if __name__=="__main__":
    unittest.main()
