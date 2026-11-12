"""P52C — vérification adversariale des prévisions officielles de mars 2026."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/rapprocher_budget_quebec_nova_p52c.py"
REF=ROOT/"projets/projet-nova/etudes/P52C_REFERENTIEL_BUDGET_QUEBEC_2026_2027.json"
GAB=ROOT/"projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json"
spec=importlib.util.spec_from_file_location("nova_p52c",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return (json.loads(REF.read_text(encoding="utf-8")),
            json.loads(GAB.read_text(encoding="utf-8")))

def row(ledger,id):
    return next(x for x in ledger["lignes_revenus"] if x["id"]==id)

class RapprochementBudget(unittest.TestCase):
    def test_01_reference_has_21_unique_rows(self):
        d,g=fixture()
        self.assertEqual(len(d["lignes_revenus"]),21)
        self.assertEqual(len({v["id"] for v in d["lignes_revenus"]}),21)
    def test_02_official_revenue_total(self):
        d,g=fixture()
        r=m.reconcile(d,g)
        self.assertEqual(r["revenus_totaux"],"166.492")
    def test_03_official_autonomous_and_transfers(self):
        d,g=fixture()
        r=m.reconcile(d,g)
        self.assertEqual(r["revenus_autonomes"],"134.361")
        self.assertEqual(r["transferts_federaux"],"32.131")
    def test_04_personal_plus_corporate_not_total_taxes(self):
        d,g=fixture()
        r=m.reconcile(d,g)
        self.assertEqual(r["impots_revenus_existants_particuliers_societes"],"65.327")
        self.assertEqual(r["autres_revenus_autonomes_y_compris_autres_taxes"],"69.034")
    def test_05_consumption_tax_aggregation(self):
        d,g=fixture()
        r=m.reconcile(d,g)
        self.assertEqual(r["taxes_consommation_dont_ventes_agregees"],"30.008")
        self.assertEqual(row(d,"taxes_vente")["valeur_mcad"],"26349")
    def test_06_debt_counted_exactly_once(self):
        d,g=fixture()
        r=m.reconcile(d,g)
        self.assertEqual(r["depenses_portefeuilles"],"160.489")
        self.assertEqual(r["service_dette_compte_une_fois"],"10.268")
        self.assertEqual(r["depenses_totales"],"170.757")
    def test_07_arithmetic_gap_is_not_accounting_deficit(self):
        d,g=fixture()
        r=m.reconcile(d,g)
        self.assertEqual(r["ecart_arithmetique_avant_ajustements"],"-4.265")
        self.assertEqual(r["deficit_comptable_prevu"],"-6.265")
        self.assertEqual(r["solde_budgetaire_prevu_selon_loi"],"-8.612")
    def test_08_frozen_fiscal_scope_preserved(self):
        d,g=fixture()
        r=m.reconcile(d,g)
        self.assertFalse(r["deux_taxes_financees"])
        self.assertFalse(r["nouveaux_impots_ou_taux_adoptes"])
        self.assertFalse(r["publication_autorisee"])
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")
    def test_09_not_certified_source_transcription(self):
        d,g=fixture()
        self.assertFalse(m.reconcile(d,g)["transcription_source_verifiee_independamment"])
    def test_10_forecast_year_not_projected_into_decade(self):
        d,g=fixture()
        self.assertEqual(m.reconcile(d,g)["annees_scenarios_2027_2036_renseignees_par_ce_controle"],0)
    def test_11_wrong_year_rejected(self):
        d,g=fixture();d["periode"]="2025-2026"
        with self.assertRaises(ValueError):m.reconcile(d,g)
    def test_12_change_original_revenue_rejected(self):
        d,g=fixture();row(d,"impot_particuliers")["valeur_mcad"]="50801"
        with self.assertRaisesRegex(ValueError,"ECART_POSTE_OFFICIEL"):m.reconcile(d,g)
    def test_13_numeric_float_rejected(self):
        d,g=fixture();row(d,"tabac")["valeur_mcad"]=830.0
        with self.assertRaises(ValueError):m.reconcile(d,g)
    def test_14_ambiguous_exponential_notation_rejected(self):
        d,g=fixture();row(d,"tabac")["valeur_mcad"]="8.3e2"
        with self.assertRaises(ValueError):m.reconcile(d,g)
    def test_15_duplicate_row_rejected(self):
        d,g=fixture();d["lignes_revenus"][1]["id"]="impot_particuliers"
        with self.assertRaisesRegex(ValueError,"POSTE_DUPLIQUE"):m.reconcile(d,g)
    def test_16_missing_row_rejected(self):
        d,g=fixture();d["lignes_revenus"].pop()
        with self.assertRaisesRegex(ValueError,"VINGT_ET_UN"):m.reconcile(d,g)
    def test_17_federal_transfer_reclassified_as_tax_rejected(self):
        d,g=fixture();row(d,"perequation")["nature"]="impot_revenu_actuel"
        with self.assertRaisesRegex(ValueError,"CLASSEMENT"):m.reconcile(d,g)
    def test_18_taxes_vente_mislabeled_as_income_rejected(self):
        d,g=fixture();row(d,"taxes_vente")["groupe"]="impots_sur_revenu_et_biens"
        with self.assertRaisesRegex(ValueError,"CLASSEMENT"):m.reconcile(d,g)
    def test_19_page_location_changes_rejected(self):
        d,g=fixture();d["sources"][0]["page_imprimee"]="28"
        with self.assertRaisesRegex(ValueError,"SOURCE_OU_PAGE"):m.reconcile(d,g)
    def test_20_external_website_source_rejected(self):
        d,g=fixture();d["sources"][1]["url"]="https://example.com/faux-budget.pdf"
        with self.assertRaisesRegex(ValueError,"SOURCE_OU_PAGE"):m.reconcile(d,g)
    def test_21_row_without_source_rejected(self):
        d,g=fixture();row(d,"sante_federal")["source_id"]="INCONNU"
        with self.assertRaisesRegex(ValueError,"POSTE_SANS_SOURCE"):m.reconcile(d,g)
    def test_22_false_revenue_subtotal_rejected(self):
        d,g=fixture();d["sous_totaux_officiels_mcad"]["revenus_totaux"]="166493"
        with self.assertRaises(ValueError):m.reconcile(d,g)
    def test_23_wrong_debt_expense_rejected(self):
        d,g=fixture();d["depenses_et_ajustements_officiels_mcad"]["service_dette"]="20536"
        with self.assertRaisesRegex(ValueError,"ECART_TABLEAU_F2"):m.reconcile(d,g)
    def test_24_accounting_balance_cannot_equal_simple_gap(self):
        d,g=fixture();d["depenses_et_ajustements_officiels_mcad"]["deficit_comptable"]="-4265"
        with self.assertRaisesRegex(ValueError,"ECART_TABLEAU_F2"):m.reconcile(d,g)
    def test_25_model_baseline_drift_rejected(self):
        d,g=fixture();g["reference_2026_2027"]["revenus_consolides"]="170.000"
        with self.assertRaisesRegex(ValueError,"GABARIT_NOVA_DIVERGENT"):m.reconcile(d,g)
    def test_26_missing_essential_scope_flag_rejected(self):
        d,g=fixture()
        d["tests_de_perimetre"]["les_transferts_federaux_ne_sont_pas_des_taxes_provinciales"]=False
        with self.assertRaisesRegex(ValueError,"FRONTIERES_COMPTABLES"):m.reconcile(d,g)
    def test_27_claimed_go_or_adoption_rejected(self):
        d,g=fixture();d["taux_adoptes"]=True
        with self.assertRaisesRegex(ValueError,"GO_NON_AUTORISE"):m.reconcile(d,g)
    def test_28_base_case_report_cli_success_not_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"rapport.json"
            code=m.main(["--referentiel",str(REF),"--gabarit",str(GAB),
                         "--rapport",str(out)])
            self.assertEqual(code,0)
            self.assertEqual(json.loads(out.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_29_strict_funding_gate_always_fails_current_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"rapport.json"
            code=m.main(["--referentiel",str(REF),"--gabarit",str(GAB),
                         "--rapport",str(out),"--exiger-financement"])
            self.assertEqual(code,3)
            r=json.loads(out.read_text())
            self.assertFalse(r["deux_taxes_financees"])
    def test_30_missing_reference_returns_two_and_no_go(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"rapport.json"
            code=m.main(["--referentiel",str(Path(tmp)/"missing.json"),
                         "--gabarit",str(GAB),"--rapport",str(out)])
            self.assertEqual(code,2)
            self.assertEqual(json.loads(out.read_text())["decision"],"NO_GO_AUTOMATIQUE")

if __name__=="__main__":
    unittest.main()
