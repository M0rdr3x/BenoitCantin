"""P52E — 23 tests contre les faux gains, faux cas représentatifs et GO."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
SCRIPT=ROOT/"scripts/evaluer_garde_fous_revenu_nova_p52e.py"
GAB=ROOT/"projets/projet-nova/etudes/P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json"
spec=importlib.util.spec_from_file_location("nova_p52e",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def source():
    return json.loads(GAB.read_text(encoding="utf-8"))

def case(doc,kind="menages",regime="QUEBEC_DANS_CANADA",scenario="central",i=0):
    return doc["regimes"][regime]["scenarios"][scenario][kind][i]

H={
 "revenu_brut":"40000","prestations_federales":"1000",
 "prestations_quebec_ou_etat":"1500","impot_revenu_federal":"2500",
 "impot_revenu_quebec_ou_etat":"3000","cotisations_obligatoires":"1000",
 "prelevements_municipaux_directs":"500","taxes_consommation_supportees":"2000"}
F={
 "chiffre_affaires":"100000","couts_exploitation_hors_salaires":"30000",
 "masse_salariale":"40000","impot_entreprise_federal":"5000",
 "impot_entreprise_quebec_ou_etat":"6000","cotisations_employeur":"3000",
 "prelevements_municipaux":"2000","taxes_consommation_non_recouvrables":"1000",
 "subventions_recues":"500","charge_additionnelle_anti_evasion":"0"}

def filled(row,kind="menages",source_type="hypothese_non_certifiee"):
    initial=H if kind=="menages" else F
    for phase in ("actuel","propose"):
        for key,value in initial.items():
            row[phase][key]=value
            row["sources"][phase+"."+key]={
                "type":source_type,
                "reference":"HYPOTHESE_FICTIVE_TEST_NON_REPRESENTATIF"
                if source_type=="hypothese_non_certifiee"
                else "https://example.org/doc-source-de-test-non-verifiee"
            }

def output(data,kind="menages",category=None):
    r=m.analyse(data)
    values=r["cas"][kind]
    return next(v for v in values if v["regime"]=="QUEBEC_DANS_CANADA"
                and v["scenario"]=="central"
                and (category is None or v["categorie"]==category))


class GuardrailsP52E(unittest.TestCase):
    def test_01_no_invented_incomes_or_declared_benefits(self):
        x=m.analyse(source())
        self.assertEqual(x["montants_manquants"],720)
        self.assertEqual(x["cas_conditionnellement_calculables"],0)
        self.assertEqual(x["cas_a_risque_de_perte_dans_leur_propre_scenario"],0)
    def test_02_all_households_firms_covered(self):
        x=m.analyse(source())
        self.assertEqual((x["nombre_cas_menages"],x["nombre_cas_entreprises"],
                          x["nombre_cas"]),(30,12,42))
    def test_03_no_population_aggregation_claim(self):
        x=m.analyse(source())
        self.assertFalse(x["montrable_comme_mesure_du_pouvoir_achat_du_quebec"])
        self.assertFalse(x["preuves_representativite_obtenues"])
        self.assertFalse(x["repercussion_prix_salaires_emplois_mesuree"])
    def test_04_no_go_and_no_fiscal_law(self):
        x=m.analyse(source())
        self.assertEqual(x["decision"],"NO_GO_AUTOMATIQUE")
        self.assertFalse(x["norme_de_non_appauvrissement_adoptee"])
        self.assertFalse(x["loi_entree_en_vigueur"])
        self.assertFalse(x["publication_autorisee"])
    def test_05_missing_case_never_assumed_winner(self):
        x=output(source())
        self.assertEqual(x["statut"],"DONNEES_MANQUANTES")
        self.assertIsNone(x["variation_monetaire_cad"])
        self.assertFalse(x["preuve_de_non_appauvrissement"])
    def test_06_hypothetical_positive_tax_change_not_certified(self):
        d=source();r=case(d);filled(r)
        r["propose"]["impot_revenu_quebec_ou_etat"]="2000"
        x=output(d)
        self.assertEqual(x["statut"],"ILLUSTRATION_SANS_PERTE_A_CE_NIVEAU")
        self.assertEqual(x["variation_monetaire_cad"],"1000")
        self.assertFalse(x["pret_a_generaliser"])
    def test_07_hypothetical_loss_flagged(self):
        d=source();r=case(d);filled(r)
        r["propose"]["taxes_consommation_supportees"]="2500"
        x=output(d)
        self.assertEqual(x["statut"],"PERTE_HYPOTHETIQUE_A_EXAMINER")
        self.assertEqual(x["variation_monetaire_cad"],"-500")
        self.assertEqual(m.analyse(d)["cas_a_risque_de_perte_dans_leur_propre_scenario"],1)
    def test_08_apparent_gain_by_salary_not_a_tax_reform_gain(self):
        d=source();r=case(d);filled(r)
        r["propose"]["revenu_brut"]="50000"
        x=output(d)
        self.assertEqual(x["statut"],"CHANGEMENT_NON_FISCAL_A_ISOLER")
        self.assertFalse(x["perimetre_stable_pour_attribution_fiscale"])
    def test_09_apparent_gain_by_benefits_not_exclusively_tax(self):
        d=source();r=case(d);filled(r)
        r["propose"]["prestations_quebec_ou_etat"]="8000"
        x=output(d)
        self.assertEqual(x["statut"],"CHANGEMENT_NON_FISCAL_A_ISOLER")
    def test_10_federal_benefits_cannot_change_in_province(self):
        d=source();r=case(d);filled(r)
        r["propose"]["prestations_federales"]="2000"
        with self.assertRaisesRegex(ValueError,"POUVOIR_FEDERAL"):
            m.analyse(d)
    def test_11_taxes_consumption_cannot_disappear_without_input(self):
        d=source();r=case(d);filled(r)
        r["propose"]["taxes_consommation_supportees"]=None
        del r["sources"]["propose.taxes_consommation_supportees"]
        x=output(d)
        self.assertEqual(x["statut"],"DONNEES_MANQUANTES")
    def test_12_document_reference_not_a_published_result(self):
        d=source();r=case(d);filled(r,source_type="document_public")
        x=output(d)
        self.assertEqual(x["statut"],"PAS_DE_PERTE_DANS_CE_CAS_NON_REPRESENTATIF")
        self.assertFalse(x["preuve_de_non_appauvrissement"])
    def test_13_documented_negative_household_requires_remedy(self):
        d=source();r=case(d);filled(r,source_type="document_public")
        r["propose"]["impot_revenu_quebec_ou_etat"]="3100"
        x=output(d)
        self.assertEqual(x["statut"],"PERTE_MONETAIRE_A_CORRIGER")
    def test_14_firm_apparent_gain_from_revenue_not_tax_relief(self):
        d=source();r=case(d,kind="entreprises");filled(r,"entreprises")
        r["propose"]["chiffre_affaires"]="120000"
        x=output(d,kind="entreprises")
        self.assertEqual(x["statut"],"CHANGEMENT_NON_FISCAL_A_ISOLER")
    def test_15_firm_real_burden_loss_flagged_not_job_loss_assumed(self):
        d=source();r=case(d,kind="entreprises");filled(r,"entreprises", "document_public")
        r["propose"]["cotisations_employeur"]="4000"
        x=output(d,kind="entreprises")
        self.assertEqual(x["statut"],"RISQUE_RESULTAT_ENTREPRISE")
        self.assertFalse(m.analyse(d)["repercussion_prix_salaires_emplois_mesuree"])
    def test_16_firm_hypothetical_loss_not_certified(self):
        d=source();r=case(d,kind="entreprises");filled(r,"entreprises")
        r["propose"]["charge_additionnelle_anti_evasion"]="200"
        x=output(d,kind="entreprises")
        self.assertEqual(x["statut"],"PERTE_HYPOTHETIQUE_A_EXAMINER")
    def test_17_sovereign_scenario_not_claimed_legally_active(self):
        d=source();r=case(d,regime="QUEBEC_SOUVERAIN");filled(r)
        x=m.analyse(d)
        self.assertFalse(x["loi_entree_en_vigueur"])
    def test_18_shuffled_input_groups_remain_matched_by_category(self):
        d=source()
        arr=d["regimes"]["QUEBEC_DANS_CANADA"]["scenarios"]["central"]["menages"]
        arr.reverse()
        x=m.analyse(d)
        self.assertEqual(len(x["cas"]["menages"]),30)
    def test_19_duplicate_category_rejected_by_source_validator(self):
        d=source()
        arr=d["regimes"]["QUEBEC_DANS_CANADA"]["scenarios"]["central"]["menages"]
        arr[1]["categorie"]=arr[0]["categorie"]
        with self.assertRaisesRegex(ValueError,"CAS_DUPLIQUE"):
            m.analyse(d)
    def test_20_forged_adoption_refused_by_source_validator(self):
        d=source();d["autorisations"]["fiscalite"]=True
        with self.assertRaisesRegex(ValueError,"AUTORISATION_INTERDITE"):
            m.analyse(d)
    def test_21_cli_report_complete_as_a_document_but_no_go(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"r.json"
            self.assertEqual(m.main(["--gabarit",str(GAB),"--rapport",str(target)]),0)
            self.assertEqual(json.loads(target.read_text())["decision"],"NO_GO_AUTOMATIQUE")
    def test_22_cli_strict_rejects_even_with_no_real_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"r.json"
            self.assertEqual(m.main(["--gabarit",str(GAB),"--rapport",str(target),
                                     "--exiger-non-appauvrissement-demontre"]),3)
            self.assertFalse(json.loads(target.read_text())["preuves_representativite_obtenues"])
    def test_24_loss_when_gross_income_falls_is_not_hidden(self):
        d=source();r=case(d);filled(r)
        r["propose"]["revenu_brut"]="38000"
        x=output(d)
        self.assertEqual(x["statut"],"PERTE_AVEC_CHANGEMENT_NON_FISCAL_A_EXAMINER")
        self.assertEqual(x["variation_monetaire_cad"],"-2000")
        self.assertTrue(x["risque_de_perte_dans_ce_cas"])
        self.assertFalse(x["perimetre_stable_pour_attribution_fiscale"])
    def test_25_loss_when_quebec_benefit_falls_is_not_hidden(self):
        d=source();r=case(d);filled(r)
        r["propose"]["prestations_quebec_ou_etat"]="1000"
        x=output(d)
        self.assertEqual(x["statut"],"PERTE_AVEC_CHANGEMENT_NON_FISCAL_A_EXAMINER")
        self.assertEqual(x["variation_monetaire_cad"],"-500")
        self.assertEqual(m.analyse(d)["cas_a_risque_de_perte_dans_leur_propre_scenario"],1)
    def test_26_loss_when_firm_revenue_falls_is_not_hidden(self):
        d=source();r=case(d,kind="entreprises");filled(r,"entreprises")
        r["propose"]["chiffre_affaires"]="99000"
        x=output(d,kind="entreprises")
        self.assertEqual(x["statut"],"PERTE_AVEC_CHANGEMENT_NON_FISCAL_A_EXAMINER")
        self.assertEqual(x["variation_monetaire_cad"],"-1000")
        self.assertTrue(x["risque_de_perte_dans_ce_cas"])
    def test_27_loss_when_salaries_cost_more_is_not_hidden(self):
        d=source();r=case(d,kind="entreprises");filled(r,"entreprises")
        r["propose"]["masse_salariale"]="42000"
        x=output(d,kind="entreprises")
        self.assertEqual(x["statut"],"PERTE_AVEC_CHANGEMENT_NON_FISCAL_A_EXAMINER")
        self.assertEqual(x["decomposition_comptable"]["variation_postes_non_fiscaux_cad"],"-2000")
    def test_28_apparent_gain_exogenous_still_not_called_tax_gain(self):
        d=source();r=case(d);filled(r)
        r["propose"]["revenu_brut"]="42000"
        x=output(d)
        self.assertEqual(x["statut"],"CHANGEMENT_NON_FISCAL_A_ISOLER")
        self.assertFalse(x["risque_de_perte_dans_ce_cas"])
        self.assertEqual(x["decomposition_comptable"]["variation_postes_non_fiscaux_cad"],"2000")
    def test_29_household_mixed_loss_decomposed_without_causal_claim(self):
        d=source();r=case(d);filled(r)
        r["propose"]["prestations_quebec_ou_etat"]="1000"
        r["propose"]["impot_revenu_quebec_ou_etat"]="3200"
        x=output(d)
        self.assertEqual(x["variation_monetaire_cad"],"-700")
        decomp=x["decomposition_comptable"]
        self.assertEqual(decomp["variation_postes_non_fiscaux_cad"],"-500")
        self.assertEqual(decomp["variation_autres_postes_comptables_cad"],"-200")
        self.assertTrue(decomp["somme_verifiee"])
        self.assertFalse(x["preuve_de_non_appauvrissement"])
    def test_30_firm_mixed_loss_decomposed_without_causal_claim(self):
        d=source();r=case(d,kind="entreprises");filled(r,"entreprises")
        r["propose"]["chiffre_affaires"]="98000"
        r["propose"]["cotisations_employeur"]="3500"
        x=output(d,kind="entreprises")
        self.assertEqual(x["variation_monetaire_cad"],"-2500")
        self.assertEqual(x["decomposition_comptable"]["variation_postes_non_fiscaux_cad"],"-2000")
        self.assertEqual(x["decomposition_comptable"]["variation_autres_postes_comptables_cad"],"-500")
        self.assertTrue(x["decomposition_comptable"]["somme_verifiee"])
    def test_31_fiscal_only_loss_has_zero_non_fiscal_delta(self):
        d=source();r=case(d);filled(r)
        r["propose"]["taxes_consommation_supportees"]="2500"
        x=output(d)
        self.assertEqual(x["statut"],"PERTE_HYPOTHETIQUE_A_EXAMINER")
        self.assertEqual(x["decomposition_comptable"]["variation_postes_non_fiscaux_cad"],"0")
        self.assertEqual(x["decomposition_comptable"]["variation_autres_postes_comptables_cad"],"-500")
    def test_32_missing_case_has_no_fictional_decomposition(self):
        x=output(source())
        self.assertIsNone(x["decomposition_comptable"]["variation_postes_non_fiscaux_cad"])
        self.assertIsNone(x["decomposition_comptable"]["variation_autres_postes_comptables_cad"])
        self.assertFalse(x["decomposition_comptable"]["somme_verifiee"])
    def test_33_count_exogenous_changes_even_when_loss(self):
        d=source();r=case(d);filled(r)
        r["propose"]["revenu_brut"]="30000"
        out=m.analyse(d)
        self.assertEqual(out["cas_avec_variation_non_fiscale_non_isolee"],1)
        self.assertEqual(out["cas_avec_perte_et_variation_non_fiscale"],1)
        self.assertEqual(out["cas_a_risque_de_perte_dans_leur_propre_scenario"],1)
    def test_34_hypothetical_loss_with_exogenous_change_not_certified(self):
        d=source();r=case(d,kind="entreprises");filled(r,"entreprises")
        r["propose"]["subventions_recues"]="0"
        x=output(d,kind="entreprises")
        self.assertEqual(x["statut"],"PERTE_AVEC_CHANGEMENT_NON_FISCAL_A_EXAMINER")
        self.assertFalse(x["pret_a_generaliser"])
        self.assertFalse(x["preuve_de_non_appauvrissement"])
    def test_35_initial_empty_gabarit_has_no_hidden_losses_or_gains(self):
        out=m.analyse(source())
        self.assertEqual(out["cas_avec_perte_et_variation_non_fiscale"],0)
        self.assertEqual(out["cas_a_risque_de_perte_dans_leur_propre_scenario"],0)
        self.assertEqual(out["montants_manquants"],720)
        self.assertEqual(out["decision"],"NO_GO_AUTOMATIQUE")
    def test_23_cli_missing_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"r.json"
            self.assertEqual(m.main(["--gabarit",str(Path(tmp)/"absent.json"),
                                     "--rapport",str(target)]),2)
            self.assertEqual(json.loads(target.read_text())["decision"],"NO_GO_AUTOMATIQUE")


    def test_36_aggregate_preserves_global_loss_counts_no_case_rows(self):
        report=m.rapport_agrege(m.analyse(source()))
        self.assertEqual(report["nombre_cas"],42)
        self.assertEqual(report["montants_manquants"],720)
        self.assertEqual(report["repartition_des_statuts"],{"DONNEES_MANQUANTES":42})
        self.assertNotIn("cas",report)
        self.assertTrue(report["rapport_agrege_sans_details"])

    def test_37_aggregate_redacts_realistic_synthetic_loss(self):
        d=source();item=case(d);filled(item)
        item["propose"]["impot_revenu_quebec_ou_etat"]="10777.77"
        detailed=m.analyse(d)
        individual=next(x for x in detailed["cas"]["menages"]
                        if x["regime"]=="QUEBEC_DANS_CANADA" and
                        x["scenario"]=="central" and
                        x["categorie"]==item["categorie"])
        self.assertEqual(individual["variation_monetaire_cad"],"-7777.77")
        public=m.rapport_agrege(detailed)
        encoded=json.dumps(public,ensure_ascii=False)
        self.assertEqual(public["cas_a_risque_de_perte_dans_leur_propre_scenario"],1)
        for sensitive in ("-7777.77","10777.77","personne_seule_revenu_modeste",
                          "variation_monetaire_cad","decomposition_comptable"):
            self.assertNotIn(sensitive,encoded)

    def test_38_public_export_ignores_unexpected_private_payload(self):
        detailed=m.analyse(source())
        detailed["injected_data"]="private-ident-test"
        public=m.rapport_agrege(detailed)
        self.assertNotIn("private-ident-test",json.dumps(public))
        self.assertNotIn("injected_data",public)

    def test_39_cli_aggregate_contains_only_global_counts(self):
        with tempfile.TemporaryDirectory() as p:
            dest=Path(p)/"summary.json"
            code=m.main(["--gabarit",str(GAB),"--rapport",str(dest),
                         "--rapport-agrege"])
            self.assertEqual(code,0)
            report=json.loads(dest.read_text(encoding="utf-8"))
            self.assertEqual(report["nombre_cas_menages"],30)
            self.assertEqual(report["nombre_cas_entreprises"],12)
            self.assertNotIn("cas",report)

    def test_40_cli_strict_aggregate_refuses_no_proof(self):
        with tempfile.TemporaryDirectory() as p:
            dest=Path(p)/"summary.json"
            status=m.main(["--gabarit",str(GAB),"--rapport",str(dest),
                           "--rapport-agrege","--exiger-non-appauvrissement-demontre"])
            self.assertEqual(status,3)
            report=json.loads(dest.read_text(encoding="utf-8"))
            self.assertEqual(report["decision"],"NO_GO_AUTOMATIQUE")
            self.assertFalse(report["publication_autorisee"])

    def test_41_aggregate_fails_closed_on_claim_of_representativity(self):
        report=m.analyse(source())
        report["preuves_representativite_obtenues"]=True
        with self.assertRaisesRegex(ValueError,"RAPPORT_PUBLIC_NON_CONFIDENTIEL_NON_ATTESTE"):
            m.rapport_agrege(report)


if __name__=="__main__":
    unittest.main()
