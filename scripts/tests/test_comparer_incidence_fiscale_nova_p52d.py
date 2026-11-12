"""P52D — 30 tests pour l'incidence fiscale non représentative de ménages/entreprises."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/comparer_incidence_fiscale_nova_p52d.py"
GAB=ROOT/"projets/projet-nova/etudes/P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json"
spec=importlib.util.spec_from_file_location("nova_p52d",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def data():
    return json.loads(GAB.read_text(encoding="utf-8"))

def one(d,regime="QUEBEC_DANS_CANADA",scenario="central",kind="menages",pos=0):
    return d["regimes"][regime]["scenarios"][scenario][kind][pos]

def fill(row,kind="menages"):
    h={
        "revenu_brut":"40000","prestations_federales":"1000",
        "prestations_quebec_ou_etat":"1500","impot_revenu_federal":"2500",
        "impot_revenu_quebec_ou_etat":"3000","cotisations_obligatoires":"1000",
        "prelevements_municipaux_directs":"500",
        "taxes_consommation_supportees":"2000"
    }
    f={
        "chiffre_affaires":"100000","couts_exploitation_hors_salaires":"30000",
        "masse_salariale":"40000","impot_entreprise_federal":"5000",
        "impot_entreprise_quebec_ou_etat":"6000","cotisations_employeur":"3000",
        "prelevements_municipaux":"2000","taxes_consommation_non_recouvrables":"1000",
        "subventions_recues":"500","charge_additionnelle_anti_evasion":"0"
    }
    values=h if kind=="menages" else f
    for stage in m.STAGES:
        for k,v in values.items():
            row[stage][k]=v
            row["sources"][stage+"."+k]={
                "type":"hypothese_non_certifiee",
                "reference":"HYPOTHESE_PURE_TEST_NON_REPRESENTATIVE"
            }

class IncidenceNova(unittest.TestCase):
    def test_01_all_cases_and_dimensions(self):
        x=m.evaluate(data())
        self.assertEqual((x["nombre_regimes"],x["nombre_scenarios"],
                          x["cas_menages"],x["cas_entreprises"],x["nombre_cas"]),
                         (2,6,30,12,42))
    def test_02_unknown_values_never_zero(self):
        x=m.evaluate(data())
        self.assertEqual(x["montants_manquants"],720)
        self.assertEqual(x["cas_calculables_conditionnellement"],0)
        self.assertTrue(all(r["variation_cad"] is None for r in x["resultats"]))
    def test_03_no_go_unconditionally(self):
        x=m.evaluate(data())
        self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")
        self.assertFalse(x["publication_autorisee"])
        self.assertFalse(x["budget_total_finance"])
        self.assertTrue(x["aucune_projection_population"])
    def test_04_no_automatic_representativity(self):
        x=m.evaluate(data())
        self.assertFalse(x["source_officielle_sur_les_menages_representatifs"])
        self.assertFalse(x["impact_economique_causal_certifie"])
    def test_05_single_household_after_direct_and_consumption(self):
        d=data();r=one(d);fill(r)
        r["propose"]["impot_revenu_quebec_ou_etat"]="2000"
        r["propose"]["taxes_consommation_supportees"]="1800"
        result=m.evaluate(d)["resultats"][0]
        self.assertEqual(result["solde_apres_prelevements_directs_actuel_cad"],"35500")
        self.assertEqual(result["solde_apres_prelevements_directs_propose_cad"],"36500")
        self.assertEqual(result["solde_apres_taxes_conso_actuel_cad"],"33500")
        self.assertEqual(result["variation_apres_taxes_conso_cad"],"1200")
        self.assertEqual(result["completude"],"ILLUSTRATION_NON_CERTIFIEE")
    def test_06_firm_partial_operational_balance(self):
        d=data();r=one(d,kind="entreprises");fill(r,kind="entreprises")
        r["propose"]["impot_entreprise_quebec_ou_etat"]="5500"
        result=next(x for x in m.evaluate(d)["resultats"] if x["type"]=="entreprises")
        self.assertEqual(result["solde_operationnel_partiel_actuel_cad"],"13500")
        self.assertEqual(result["variation_solde_partiel_cad"],"500")
        self.assertFalse(result["attribution_causale_demontree"])
    def test_07_federal_tax_change_in_provincial_mode_rejected(self):
        d=data();r=one(d);fill(r)
        r["propose"]["impot_revenu_federal"]="0"
        with self.assertRaisesRegex(ValueError,"POUVOIR_FEDERAL"):
            m.evaluate(d)
    def test_08_federal_benefit_change_in_provincial_mode_rejected(self):
        d=data();r=one(d);fill(r)
        r["propose"]["prestations_federales"]="0"
        with self.assertRaisesRegex(ValueError,"POUVOIR_FEDERAL"):
            m.evaluate(d)
    def test_09_federal_corporation_tax_change_in_provincial_mode_rejected(self):
        d=data();r=one(d,kind="entreprises");fill(r,"entreprises")
        r["propose"]["impot_entreprise_federal"]="0"
        with self.assertRaisesRegex(ValueError,"POUVOIR_FEDERAL"):
            m.evaluate(d)
    def test_10_sovereign_federal_model_still_requires_explicit_value(self):
        d=data();r=one(d,regime="QUEBEC_SOUVERAIN");fill(r)
        r["propose"]["impot_revenu_federal"]="0"
        result=m.evaluate(d)
        self.assertEqual(result["montants_manquants"],704)
        self.assertEqual(result["decision"],"NO_GO_AUTOMATIQUE")
    def test_11_no_positive_tax_automatically_assumed(self):
        self.assertIsNone(one(data())["actuel"]["impot_revenu_federal"])
        self.assertIsNone(one(data())["propose"]["impot_revenu_quebec_ou_etat"])
    def test_12_float_rejected(self):
        d=data();one(d)["actuel"]["revenu_brut"]=40000.0
        with self.assertRaisesRegex(ValueError,"MONTANT_CAD_INVALIDE"):
            m.evaluate(d)
    def test_13_negative_input_rejected(self):
        d=data();one(d)["actuel"]["revenu_brut"]="-2"
        with self.assertRaisesRegex(ValueError,"MONTANT_CAD_INVALIDE"):
            m.evaluate(d)
    def test_14_exponent_nan_and_bool_rejected(self):
        for val in ["NaN","Infinity","1e5",True]:
            with self.subTest(value=val):
                d=data();one(d)["actuel"]["revenu_brut"]=val
                with self.assertRaises(ValueError):
                    m.evaluate(d)
    def test_15_excessive_decimal_precision_rejected(self):
        d=data();one(d)["actuel"]["revenu_brut"]="34.567"
        with self.assertRaisesRegex(ValueError,"MONTANT_CAD_INVALIDE"):
            m.evaluate(d)
    def test_16_amount_without_source_rejected(self):
        d=data();one(d)["actuel"]["revenu_brut"]="1000"
        with self.assertRaisesRegex(ValueError,"SOURCE_MANQUANTE"):
            m.evaluate(d)
    def test_17_source_without_amount_rejected(self):
        d=data();one(d)["sources"]["actuel.revenu_brut"]={
            "type":"document_public","reference":"https://example.org/fixture"
        }
        with self.assertRaisesRegex(ValueError,"SOURCE_SANS_MONTANT"):
            m.evaluate(d)
    def test_18_document_source_must_be_https(self):
        d=data();r=one(d);fill(r)
        r["sources"]["actuel.revenu_brut"]={
            "type":"document_public","reference":"http://example.org/fixture"
        }
        with self.assertRaisesRegex(ValueError,"URL_SOURCE"):
            m.evaluate(d)
    def test_19_extra_source_field_rejected(self):
        d=data();one(d)["sources"]["actuel.numero_assurance_sociale"]={
            "type":"hypothese_non_certifiee","reference":"TEST_NON_REPRESENTATIF"
        }
        with self.assertRaisesRegex(ValueError,"SOURCES_HORS_PERIMETRE"):
            m.evaluate(d)
    def test_20_unbounded_text_in_reference_rejected(self):
        d=data();r=one(d);fill(r)
        r["sources"]["actuel.revenu_brut"]["reference"]="EXEMPLE\nPRIVATE"
        with self.assertRaisesRegex(ValueError,"PROVENANCE_NON_RECEVABLE"):
            m.evaluate(d)
    def test_21_no_new_unknown_category_accepted(self):
        d=data();one(d)["actuel"]["dons"]="0"
        with self.assertRaisesRegex(ValueError,"CATEGORIES_INCOMPLETES"):
            m.evaluate(d)
    def test_22_duplicate_household_type_rejected(self):
        d=data()
        arr=d["regimes"]["QUEBEC_DANS_CANADA"]["scenarios"]["central"]["menages"]
        arr[1]["categorie"]=arr[0]["categorie"]
        with self.assertRaisesRegex(ValueError,"CAS_DUPLIQUE"):
            m.evaluate(d)
    def test_23_missing_household_category_rejected(self):
        d=data()
        d["regimes"]["QUEBEC_DANS_CANADA"]["scenarios"]["central"]["menages"].pop()
        with self.assertRaisesRegex(ValueError,"NOMBRE_DE_CAS"):
            m.evaluate(d)
    def test_24_no_missing_scenario_allowed(self):
        d=data();del d["regimes"]["QUEBEC_SOUVERAIN"]["scenarios"]["stress"]
        with self.assertRaisesRegex(ValueError,"SCENARIOS_INCOMPLETS"):
            m.evaluate(d)
    def test_25_unauthorized_change_of_regime_flag_rejected(self):
        d=data();d["regimes"]["QUEBEC_DANS_CANADA"]["competence"]="DEUX_IMPOTS_DANS_TOUTE_ECONOMIE"
        with self.assertRaisesRegex(ValueError,"COMPETENCE_CONSTITUTIONNELLE"):
            m.evaluate(d)
    def test_26_false_validation_claim_rejected(self):
        d=data();one(d)["classification_validee"]=True
        with self.assertRaisesRegex(ValueError,"CLASSIFICATION_PRESUMEE"):
            m.evaluate(d)
    def test_27_no_population_weight_claim(self):
        d=data();d["aucune_ponderation_population"]=False
        with self.assertRaisesRegex(ValueError,"FAUSSE_EXTRAPOLATION"):
            m.evaluate(d)
    def test_28_go_attempt_rejected(self):
        d=data();d["autorisations"]["publication"]=True
        with self.assertRaisesRegex(ValueError,"AUTORISATION_INTERDITE"):
            m.evaluate(d)
    def test_29_cli_report_success_not_policy_success(self):
        with tempfile.TemporaryDirectory() as p:
            out=Path(p)/"report.json"
            code=m.main(["--gabarit",str(GAB),"--rapport",str(out)])
            self.assertEqual(code,0)
            self.assertEqual(json.loads(out.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_30_cli_strict_returns_three_on_unknowns(self):
        with tempfile.TemporaryDirectory() as p:
            out=Path(p)/"report.json"
            code=m.main(["--gabarit",str(GAB),"--rapport",str(out),
                         "--exiger-completude"])
            self.assertEqual(code,3)
            self.assertEqual(json.loads(out.read_text())["montants_manquants"],720)
    def test_31_cli_missing_template_fails_closed(self):
        with tempfile.TemporaryDirectory() as p:
            out=Path(p)/"report.json"
            code=m.main(["--gabarit",str(Path(p)/"absent.json"),"--rapport",str(out)])
            self.assertEqual(code,2)
            self.assertEqual(json.loads(out.read_text())["decision"],"NO_GO_AUTOMATIQUE")



    def test_32_public_report_omits_all_individual_cases(self):
        r=m.rapport_agrege(m.evaluate(data()))
        self.assertEqual(r["nombre_cas"],42)
        self.assertEqual(r["montants_manquants"],720)
        self.assertNotIn("resultats",r)
        self.assertNotIn("categorie",r)
        self.assertTrue(r["rapport_agrege_sans_details"])
        self.assertEqual(r["decision"],"NO_GO_AUTOMATIQUE")

    def test_33_public_report_redacts_filled_case_variation(self):
        doc=data()
        item=one(doc)
        fill(item)
        item["propose"]["impot_revenu_quebec_ou_etat"]="10777.77"
        full=m.evaluate(doc)
        variation=next(x["variation_cad"] for x in full["resultats"]
                       if x["categorie"]==item["categorie"] and
                       x["regime"]=="QUEBEC_DANS_CANADA" and x["scenario"]=="central")
        self.assertEqual(variation,"-7777.77")
        public=m.rapport_agrege(full)
        output=json.dumps(public,ensure_ascii=False)
        self.assertNotIn("7777.77",output)
        self.assertNotIn("10777.77",output)
        self.assertNotIn("personne_seule_revenu_modeste",output)
        self.assertNotIn("resultats",public)
        self.assertEqual(public["cas_calculables_conditionnellement"],1)

    def test_34_public_export_ignores_arbitrary_suspect_metadata(self):
        full=m.evaluate(data())
        full["injected_private_data"]="secret-identifier-test"
        self.assertNotIn("secret-identifier-test",
                         json.dumps(m.rapport_agrege(full)))

    def test_35_cli_aggregate_has_no_cases(self):
        with tempfile.TemporaryDirectory() as p:
            dest=Path(p)/"public.json"
            status=m.main(["--gabarit",str(GAB),"--rapport",str(dest),
                           "--rapport-agrege"])
            self.assertEqual(status,0)
            obj=json.loads(dest.read_text(encoding="utf-8"))
            self.assertEqual(obj["nombre_cas"],42)
            self.assertNotIn("resultats",obj)
            self.assertTrue(obj["aucun_montant_individuel_exporte"])

    def test_36_cli_strict_aggregate_still_returns_three(self):
        with tempfile.TemporaryDirectory() as p:
            dest=Path(p)/"public.json"
            status=m.main(["--gabarit",str(GAB),"--rapport",str(dest),
                           "--rapport-agrege","--exiger-completude"])
            self.assertEqual(status,3)
            self.assertEqual(json.loads(dest.read_text())["decision"],
                             "NO_GO_AUTOMATIQUE")

    def test_37_public_report_refuses_tampered_permission(self):
        full=m.evaluate(data())
        full["publication_autorisee"]=True
        with self.assertRaisesRegex(ValueError,"RAPPORT_PUBLIC_HORS_PERIMETRE"):
            m.rapport_agrege(full)


if __name__=="__main__":
    unittest.main()
