"""P52B — 28 contrôles adversariaux du modèle fiscal décennal Nova."""
from __future__ import annotations
import copy
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/evaluer_transition_fiscale_nova_p52b.py"
TEMPLATE = ROOT / "projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json"
REGISTER = ROOT / "projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json"
spec = importlib.util.spec_from_file_location("nova_p52b", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def read_data():
    return (json.loads(TEMPLATE.read_text(encoding="utf-8")),
            json.loads(REGISTER.read_text(encoding="utf-8")))


def year(d, regime="QUEBEC_DANS_CANADA", scenario="central", pos=0):
    return d["regimes"][regime]["trajectoires"][scenario][pos]


def complete_all(d):
    revenues = {
        "impot_revenu_net":"160.000",
        "anti_evasion_additionnelle_nette":"0",
        "revenus_non_fiscaux_nets":"10.000",
        "transferts_federaux_nets":"0",
        "autres_prelevements_provinciaux_nets":"0",
    }
    expenses = {
        "services_existants_hors_dette_et_municipal_nets":"140",
        "service_dette_net":"10",
        "transferts_municipaux_nets":"10",
        "fonctions_souveraines_nouvelles_nettes":"0",
        "couts_transition_nets":"0",
        "provision_crises_nette":"5",
    }
    for regime in m.REGIMES:
        for scenario in m.TRAJECTOIRES:
            for item in d["regimes"][regime]["trajectoires"][scenario]:
                item["recettes"] = copy.deepcopy(revenues)
                item["depenses"] = copy.deepcopy(expenses)
                item["sources"] = {k:("HYPOTHESE_PRUDENTE_ZERO_NON_CERTIFIEE"
                     if k=="anti_evasion_additionnelle_nette" else
                     "HYPOTHESE_PUREMENT_FICTIVE_DE_TEST")
                     for k in m.ALL}
                item["solde_budgetaire_precedent"]="0"
                item["ratio_dette_nette_pib_pct"]="45"
                item["perimetre_reconcilie"]=True
                item["incidence_menages_validee"]=True
                item["emplois_et_services_valides"]=True
                item["inventaire_prelevements_valide"]=True


class FinanceNova(unittest.TestCase):
    def test_01_20_proofs_initially_unvalidated(self):
        d,r=read_data()
        self.assertEqual(m.validate_evidence_register(r),20)

    def test_02_exactly_60_scenario_years(self):
        d,r=read_data()
        x=m.evaluate(d,r)
        self.assertEqual((x["nombre_regimes"],x["nombre_trajectoires"],
                          x["nombre_exercices"]),(2,6,10))

    def test_03_all_600_unknown_values_retained(self):
        d,r=read_data()
        x=m.evaluate(d,r)
        self.assertEqual(x["entrees_financieres_manquantes"],600)
        self.assertTrue(all(row["annees_calculables"]==0 for row in x["resultats"]))

    def test_04_baseline_not_official_deficit(self):
        d,r=read_data()
        x=m.evaluate(d,r)
        self.assertEqual(Decimal(x["reference_ecart_arithmetique_gcad"]),Decimal("-4.265"))
        self.assertTrue(x["reference_ecart_non_assimilable_solde_budgetaire_officiel"])

    def test_05_no_invented_tax_rates_or_legal_go(self):
        d,r=read_data()
        x=m.evaluate(d,r)
        self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")
        self.assertFalse(x["taux_fiscal_adopte"])
        self.assertFalse(x["publication_autorisee"])
        self.assertTrue(all(v["taux_fiscal_propose"] is None for v in x["resultats"]))

    def test_06_federal_limitation_is_explicit(self):
        d,r=read_data()
        self.assertEqual(d["regimes"]["QUEBEC_DANS_CANADA"]
                         ["objectif_deux_prelevements"],
                         "PROVINCIAL_SEULEMENT_FEDERAL_DEMEURE")
        self.assertTrue(all(not x["deux_taxes_sur_toute_economie_realisees"]
                            for x in m.evaluate(d,r)["resultats"]))

    def test_07_floating_point_dollars_rejected(self):
        with self.assertRaises(ValueError):
            m.decimal_gcad(1.5)

    def test_08_bool_rejected_as_amount(self):
        with self.assertRaises(ValueError):
            m.decimal_gcad(True)

    def test_09_negative_income_rejected(self):
        with self.assertRaises(ValueError):
            m.decimal_gcad("-1")

    def test_10_nan_and_exponent_rejected(self):
        for value in ("NaN","Infinity","1e4","0x20","+10"):
            with self.subTest(value=value),self.assertRaises(ValueError):
                m.decimal_gcad(value)

    def test_11_previous_budget_may_be_negative(self):
        self.assertEqual(m.decimal_gcad("-1.25",signed=True),Decimal("-1.25"))

    def test_12_unknown_income_not_silently_zero(self):
        d,r=read_data()
        a=year(d)
        self.assertIsNone(a["recettes"]["impot_revenu_net"])
        self.assertIsNone(m.verify_row(a,2027)["solde_simule_gcad"])

    def test_13_assumed_extra_anti_evasion_must_remain_zero(self):
        d,r=read_data()
        a=year(d)
        a["recettes"]["anti_evasion_additionnelle_nette"]="5"
        with self.assertRaisesRegex(ValueError,"RECETTE_ANTI_EVASION"):
            m.evaluate(d,r)

    def test_14_assumed_zero_source_must_be_labeled(self):
        d,r=read_data()
        a=year(d)
        a["sources"]["anti_evasion_additionnelle_nette"]="CERTIFIE_SANS_PREUVE"
        with self.assertRaisesRegex(ValueError,"RECETTE_ANTI_EVASION"):
            m.evaluate(d,r)

    def test_15_new_amount_without_source_rejected(self):
        d,r=read_data()
        a=year(d)
        a["recettes"]["impot_revenu_net"]="4.2"
        with self.assertRaisesRegex(ValueError,"PREUVE_SOURCE_REQUISE"):
            m.evaluate(d,r)

    def test_16_source_for_missing_amount_rejected(self):
        d,r=read_data()
        year(d)["sources"]["impot_revenu_net"]="REFERENCE"
        with self.assertRaisesRegex(ValueError,"SOURCE_SANS_MONTANT"):
            m.evaluate(d,r)

    def test_17_missing_revenue_category_rejected(self):
        d,r=read_data()
        del year(d)["recettes"]["transferts_federaux_nets"]
        with self.assertRaisesRegex(ValueError,"ASSIETTES_INCOMPLETES"):
            m.evaluate(d,r)

    def test_18_missing_year_rejected(self):
        d,r=read_data()
        d["regimes"]["QUEBEC_SOUVERAIN"]["trajectoires"]["stress"].pop()
        with self.assertRaisesRegex(ValueError,"HORIZON_DECENNAL"):
            m.evaluate(d,r)

    def test_19_duplicate_year_rejected(self):
        d,r=read_data()
        year(d,pos=1)["exercice_debut"]=2027
        with self.assertRaisesRegex(ValueError,"EXERCICE_INATTENDU"):
            m.evaluate(d,r)

    def test_20_missing_stress_trajectory_rejected(self):
        d,r=read_data()
        del d["regimes"]["QUEBEC_SOUVERAIN"]["trajectoires"]["stress"]
        with self.assertRaisesRegex(ValueError,"TROIS_TRAJECTOIRES"):
            m.evaluate(d,r)

    def test_21_change_regime_scope_rejected(self):
        d,r=read_data()
        d["regimes"]["QUEBEC_DANS_CANADA"]["objectif_deux_prelevements"]="TOUTES_TAXES_ABOLIES"
        with self.assertRaisesRegex(ValueError,"COMPETENCES_FISCALES"):
            m.evaluate(d,r)

    def test_22_tampered_budget_snapshot_rejected(self):
        d,r=read_data()
        d["reference_2026_2027"]["depenses_consolidees"]="0"
        with self.assertRaisesRegex(ValueError,"REFERENCE_NOVA_INATTENDUE"):
            m.evaluate(d,r)

    def test_23_wrong_main_sha_rejected(self):
        d,r=read_data()
        d["reference_main_sha"]="f"*40
        with self.assertRaisesRegex(ValueError,"SHA_REFERENCE"):
            m.evaluate(d,r)

    def test_24_formal_go_or_publication_in_register_rejected(self):
        d,r=read_data()
        r["automatic_go"]=True
        with self.assertRaisesRegex(ValueError,"AUTORISATION_INTERDITE"):
            m.evaluate(d,r)

    def test_25_duplicate_evidence_id_rejected(self):
        d,r=read_data()
        r["required_evidence"][1]["id"]=r["required_evidence"][0]["id"]
        with self.assertRaisesRegex(ValueError,"PREUVES_NON_UNIQUES"):
            m.evaluate(d,r)

    def test_26_conditional_numbers_never_prove_financing(self):
        d,r=read_data()
        complete_all(d)
        x=m.evaluate(d,r)
        self.assertEqual(x["entrees_financieres_manquantes"],0)
        self.assertEqual(x["preuves_P52A_encore_non_valides"],20)
        self.assertEqual(x["resultats"][0]["soldes_gcad"][0],"5.000")
        self.assertTrue(all(s["etat"]=="NON_VALIDABLE" for s in x["resultats"]))
        self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")

    def test_27_even_if_proofs_marked_valid_no_automatic_go(self):
        d,r=read_data()
        complete_all(d)
        for row in r["required_evidence"]:
            row["statut"]="VALIDE"
        x=m.evaluate(d,r)
        self.assertEqual(x["resultats"][0]["etat"],"CALCUL_CONDITIONNEL_A_AUDITER")
        self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")
        self.assertFalse(x["taux_fiscal_adopte"])

    def test_28_debt_over_45_blocks_qualified_trajectory(self):
        d,r=read_data()
        complete_all(d)
        for row in r["required_evidence"]:
            row["statut"]="VALIDE"
        year(d)["ratio_dette_nette_pib_pct"]="45.1"
        x=m.evaluate(d,r)
        self.assertEqual(x["resultats"][0]["etat"],"NON_VALIDABLE")

    def test_29_other_provincial_levies_block_two_tax_target(self):
        d,r=read_data()
        complete_all(d)
        for row in r["required_evidence"]:
            row["statut"]="VALIDE"
        a=year(d)
        a["recettes"]["autres_prelevements_provinciaux_nets"]="1"
        x=m.evaluate(d,r)
        self.assertEqual(x["resultats"][0]["etat"],"NON_VALIDABLE")

    def test_30_missing_legal_inventory_blocks_qualification(self):
        d,r=read_data()
        complete_all(d)
        for row in r["required_evidence"]:
            row["statut"]="VALIDE"
        year(d)["inventaire_prelevements_valide"]=False
        x=m.evaluate(d,r)
        self.assertEqual(x["resultats"][0]["etat"],"NON_VALIDABLE")

    def test_31_cli_report_can_be_generated_while_incomplete(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/"audit.json"
            status=m.main(["--gabarit",str(TEMPLATE),"--registre",str(REGISTER),
                           "--rapport",str(out)])
            self.assertEqual(status,0)
            report=json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["decision"],"NO_GO_AUTOMATIQUE")

    def test_32_cli_strict_fails_with_code_three(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/"audit.json"
            status=m.main(["--gabarit",str(TEMPLATE),"--registre",str(REGISTER),
                           "--rapport",str(out),"--exiger-completude"])
            self.assertEqual(status,3)
            self.assertEqual(json.loads(out.read_text())["entrees_financieres_manquantes"],600)

    def test_33_cli_missing_data_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/"audit.json"
            status=m.main(["--gabarit",str(Path(folder)/"not-found.json"),
                           "--registre",str(REGISTER),"--rapport",str(out)])
            self.assertEqual(status,2)
            report=json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["decision"],"NO_GO_AUTOMATIQUE")
            self.assertFalse(report["publication_autorisee"])


if __name__ == "__main__":
    unittest.main()
