#!/usr/bin/env python3
"""P55P : exposition conditionnelle des recettes 2026-2027 aux deux prélèvements.

Les chiffres proviennent des prévisions du budget actuel du Québec.
Ce n'est ni une projection Nova 2027-2036, ni un coût net de réforme.
Aucun taux n'est calculé, et aucune loi ou prestation n'est modifiée.
"""
import argparse
import json
from pathlib import Path
import sys

import auditer_couverture_financement_nova_p55o as p55o

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"projets"/"projet-nova"/"etudes"
CONFIG=BASE/"P55P_EXPOSITION_PRELEVEMENTS_BUDGET_2026_2027.json"
P52C=p55o.P52C
NO_GO="NO_GO_AUTOMATIQUE"
YEAR="2026-2027"
EXPECTED_REVENUES={
    "impot_particuliers":50800,"impot_societes":14527,
    "cotisations_sante":9412,"foncier_scolaire":1311,
    "consommation_total":30008,"entreprises_gouvernement":5853,
    "droits_permis_redevances":6542,"revenus_divers":15908,
    "transferts_federaux":32131,"revenus_totaux":166492,
    "recettes_impot_revenus_actuels":65327,
    "prelevements_hors_impot_revenus_etudies":40731,
    "autres_recettes_sans_reclassement_juridique":60434,
    "somme_taxes_actuelles_personnes_societes_et_autres":106058,
}
EXPECTED_EXPENSES={
    "depenses_portefeuilles":160489,"service_dette":10268,
    "depenses_totales":170757,"provision_eventualites":2000,
    "versement_fonds_generations":2347,"deficit_comptable":-6265,
    "solde_loi_equilibre_budgetaire":-8612,
}
SCENARIO={
    "condition":
        "ABOLITION_HYPOTHETIQUE_DE_TOUTES_LES_COTISATIONS_SANTE_FONCIER_SCOLAIRE_TAXES_CONSOMMATION_SANS_COMPENSATION",
    "reduction_recettes_mcad":40731,
    "recettes_apres_suppression_hypothetique_mcad":125761,
    "deficit_comptable_si_aucUNE_ADAPTATION":-46996,
    "solde_loi_si_aucUNE_ADAPTATION":-49343,
    "ressources_additionnelles_pour_revenir_au_solde_comptable_original_mcad":40731,
    "ressources_additionnelles_pour_solde_comptable_zero_mcad":46996,
    "ressources_additionnelles_pour_solde_au_sens_de_la_loi_zero_mcad":49343,
    "economisation_presumee_mcad":None,
    "rendement_prelevement_anti_paradis_fiscaux_mcad":None,
    "taux_sur_revenus_necessaire_pct":None,
    "assiette_revenus_a_taxer_mcad":None,
    "benefice_net_menages_cad":None,
    "prevision_validee":False,
}
GROUPS=(
    ("IMPOTS_REVENU_EXISTANTS",("impot_particuliers","impot_societes"),65327,
     "REFERENTIEL_DES_IMPOTS_ACTUELS_NON_ASSIETTE_IMPOSABLE_FUTURE"),
    ("PRELEVEMENTS_PROVINCIAUX_A_EXAMINER",
     ("cotisations_sante","foncier_scolaire","taxes_consommation"),40731,
     "EXPOSITION_STATIQUE_CONDITIONNELLE_SI_ABOLITION_INTEGRALE_TROIS_POSTES"),
    ("AUTRES_RECETTES_ET_TRANSFERTS",
     ("entreprises_gouvernement","droits_permis_redevances",
      "revenus_divers","transferts_federaux"),60434,
     "REGROUPEMENT_COMPTABLE_SANS_CONCLUSION_JURIDIQUE_SUR_PERENNITE"),
)
GUARDS={
    "LE_SCENARIO_STATIQUE_EST_UN_TEST_DE_RISQUE_PAS_UNE_PREVISION",
    "QUATRE_POSTES_FISCAUX_MAL_CLASSeS_NE_CREENT_PAS_UNE_NOUVELLE_TAXE",
    "NE_PAS_APPLIQUER_REDUCTION_DU_QUEBEC_AU_FEDERAL",
    "NE_PAS_SUPPRIMER_AUTOMATIQUEMENT_TAXES_MUNICIPALES",
    "NE_PAS_ANNONCER_TAUX_SANS_ASSIETTE_ET_INCIDENTE",
    "AUCUN_REVENU_ADDITIONNEL_ANTI_PARADIS_CERTIFIE",
    "DROITS_PERMIS_REDEVANCES_A_CLASSER_JURIDIQUEMENT",
    "RECETTES_DIVERSES_ET_FONDS_AFFECTES_A_EXAMINER",
    "SERVICES_ESSENTIELS_NON_COUPEs",
    "PROTECTION_EMPLOIS_ET_POUVOIR_ACHAT",
    "SOLDE_COMPTABLE_DISTINCT_SOLDE_LEGAL",
    "PROVISION_2000_ET_FONDS_GENERATIONS_2347_NON_DOUBLE_COMPTES",
    "RECETTES_DU_SYSTEME_ACTUEL_NON_ASSIETTE_FISCALE",
    "SOUVERAINETE_NE_HERITE_PAS_AUTOMATIQUEMENT_TRANSFERTS_FEDERAUX",
    "REGIMES_QUEBEC_CANADA_ET_QUEBEC_SOUVERAIN_DISTINCTS",
    "NO_GO_SANS_AVIS_INDEPENDANT",
    "MAINTENIR_P55N_53_POURCENT_SANS_NOUVELLE_PREUVE",
    "MAINTENIR_600_ENTREES_P52B_INCONNUES",
    "AUCUNE_TRANSMISSION_EXTERNE",
    "AUCUNE_DEPENSE","SINJIRA_INCHANGE","AUCUNE_FUSION_MAIN",
}
QUESTIONS={
    "P01","P02","P03","P04","P05","P06",
}
SOURCE={
    "gabarit":"P52C_REFERENTIEL_BUDGET_QUEBEC_2026_2027.json",
    "document_discours":
        "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_Discours.pdf",
    "page_imprimee_discours":27,
    "page_pdf_index_zero_discours":29,
    "document_plan":
        "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf",
    "table_plan":"F.2",
    "page_imprimee_plan":"F.9",
    "niveau_verification":
        "CAPTURE_VISUELLE_TABLEAU_3_DISCOURS_ET_TEXTE_TABLEAU_F2_PLAN_SANS_EMPREINTE_PDF",
}

def need(ok,why):
    if not ok:
        raise ValueError(why)

def expected_groups():
    return [
        {"groupe":name,"ids":list(ids),"montant_mcad":amount,
         "portee":scope,"suppression_presumee":False}
        for name,ids,amount,scope in GROUPS
    ]

def verify(cfg):
    need(type(cfg) is dict
         and cfg.get("schema_version")=="P55P-1"
         and cfg.get("date_reference")=="2026-11-05"
         and cfg.get("exercice_base")==YEAR
         and cfg.get("unite")=="M_CAD"
         and cfg.get("nature")==
             "TEST_DE_SENSIBILITE_ARITHMETIQUE_STATIQUE_NON_PREVISION_POLITIQUE"
         and cfg.get("statut")=="ETUDE_CANDIDATE_NON_ADOPTEE"
         and cfg.get("decision")==NO_GO
         and cfg.get("source_ref")==SOURCE
         and cfg.get("recettes")==EXPECTED_REVENUES
         and cfg.get("depenses_et_solde")==EXPECTED_EXPENSES
         and cfg.get("classification_exposition")==expected_groups()
         and cfg.get("exposition_sensibilite_statique")==SCENARIO,
         "P55P_REFERENTIEL_CHANGE")
    guards=cfg.get("garde_fous")
    need(type(guards) is list and len(guards)==len(GUARDS)
         and set(guards)==GUARDS
         and len(guards)==len(set(guards)),
         "P55P_GARANTIES_NON_CONFORMES")
    questions=cfg.get("questions_a_resoudre")
    need(type(questions) is list
         and len(questions)==len(QUESTIONS)
         and {q.get("id") for q in questions}==QUESTIONS
         and all(type(q) is dict and set(q)=={
             "id","objet","preuve","statut"}
             and q["statut"]=="OUVERT"
             and type(q["objet"]) is str and len(q["objet"])>10
             and type(q["preuve"]) is str and len(q["preuve"])>10
             for q in questions),
         "P55P_QUESTIONS_CLOTUREES_SANS_PREUVE")
    r=cfg["recettes"]
    d=cfg["depenses_et_solde"]
    s=cfg["exposition_sensibilite_statique"]
    need(r["impot_particuliers"]+r["impot_societes"]==
         r["recettes_impot_revenus_actuels"]==65327
         and r["cotisations_sante"]+r["foncier_scolaire"]
           +r["consommation_total"]==
           r["prelevements_hors_impot_revenus_etudies"]==40731
         and r["entreprises_gouvernement"]+r["droits_permis_redevances"]
           +r["revenus_divers"]+r["transferts_federaux"]==
           r["autres_recettes_sans_reclassement_juridique"]==60434
         and sum(v for k,v in r.items() if k in (
             "recettes_impot_revenus_actuels",
             "prelevements_hors_impot_revenus_etudies",
             "autres_recettes_sans_reclassement_juridique"))==
             r["revenus_totaux"]==166492
         and r["recettes_impot_revenus_actuels"]+
             r["prelevements_hors_impot_revenus_etudies"]==
             r["somme_taxes_actuelles_personnes_societes_et_autres"]==106058,
         "P55P_RECETTES_PAS_RECONCILIEES")
    need(d["depenses_portefeuilles"]+d["service_dette"]==
         d["depenses_totales"]==170757
         and r["revenus_totaux"]-d["depenses_totales"]
             -d["provision_eventualites"]==
             d["deficit_comptable"]==-6265
         and d["deficit_comptable"]-d["versement_fonds_generations"]==
             d["solde_loi_equilibre_budgetaire"]==-8612,
         "P55P_SOLDE_BUDGETAIRE_INEXACT")
    need(r["revenus_totaux"]-s["reduction_recettes_mcad"]==
         s["recettes_apres_suppression_hypothetique_mcad"]==125761
         and s["recettes_apres_suppression_hypothetique_mcad"]
             -d["depenses_totales"]-d["provision_eventualites"]==
             s["deficit_comptable_si_aucUNE_ADAPTATION"]==-46996
         and s["deficit_comptable_si_aucUNE_ADAPTATION"]
             -d["versement_fonds_generations"]==
             s["solde_loi_si_aucUNE_ADAPTATION"]==-49343
         and s["ressources_additionnelles_pour_revenir_au_solde_comptable_original_mcad"]==
             40731
         and s["ressources_additionnelles_pour_solde_comptable_zero_mcad"]==
             -s["deficit_comptable_si_aucUNE_ADAPTATION"]==46996
         and s["ressources_additionnelles_pour_solde_au_sens_de_la_loi_zero_mcad"]==
             -s["solde_loi_si_aucUNE_ADAPTATION"]==49343
         and all(s[key] is None for key in (
             "economisation_presumee_mcad",
             "rendement_prelevement_anti_paradis_fiscaux_mcad",
             "taux_sur_revenus_necessaire_pct",
             "assiette_revenus_a_taxer_mcad",
             "benefice_net_menages_cad"))
         and s["prevision_validee"] is False,
         "P55P_HYPOTHESE_STATIQUE_ASSEMBLEE_A_TORT")
    return True

def compare_source(ref):
    need(type(ref) is dict
         and ref.get("schema_version")=="P52C-1"
         and ref.get("periode")==YEAR
         and ref.get("unite")=="M_CAD"
         and ref.get("hypotheses_nova_certifiees") is False
         and ref.get("taux_adoptes") is False,
         "P55P_SOURCE_P52C_INVALIDE")
    records=ref.get("lignes_revenus")
    need(type(records) is list and len(records)==21,
         "P55P_LIGNES_HISTORIQUES_MANQUANTES")
    data={}
    by_group={}
    for row in records:
        need(type(row) is dict
             and row.get("id") not in data
             and type(row.get("valeur_mcad")) is str
             and row["valeur_mcad"].isdigit()
             and row.get("source_id")=="DISC2026_T3",
             "P55P_LIGNES_BUDGET_ALTÉRÉES")
        amount=int(row["valeur_mcad"])
        data[row["id"]]=amount
        by_group[row["groupe"]]=by_group.get(row["groupe"],0)+amount
    subtotals=ref.get("sous_totaux_officiels_mcad")
    need(type(subtotals) is dict and
         {k:int(v) for k,v in subtotals.items()}=={
             "impots_sur_revenu_et_biens":76050,
             "taxes_consommation":30008,
             "entreprises_gouvernement":5853,
             "droits_permis_redevances":6542,
             "revenus_divers":15908,
             "transferts_federaux":32131,
             "revenus_autonomes":134361,
             "revenus_totaux":166492,
         } and all(by_group.get(g)==int(subtotals[g]) for g in by_group),
         "P55P_TOTAUX_SOURCE_NON_CONCILIES")
    need(data.get("impot_particuliers")==50800
         and data.get("impot_societes")==14527
         and data.get("cotisations_sante")==9412
         and data.get("foncier_scolaire")==1311
         and sum(by_group.values())==166492,
         "P55P_COMPOSANTES_REVENU_SOURCE_INCOHERENTES")
    costs=ref.get("depenses_et_ajustements_officiels_mcad")
    need(type(costs) is dict and
         {k:int(v) for k,v in costs.items()}=={
             "depenses_portefeuilles":160489,"service_dette":10268,
             "depenses_totales":170757,"provision_eventualites":2000,
             "versements_fonds_generations":2347,"deficit_comptable":-6265,
             "solde_budgetaire_loi_equilibre":-8612},
         "P55P_DEPENSES_SOURCE_NON_CONFORMES")
    return True

def load():
    cfg=p55o.read_json(CONFIG)
    verify(cfg)
    compare_source(p55o.read_json(P52C))
    upstream,coverage=p55o.load()
    need(upstream["decision"]==NO_GO
         and sum(coverage["frequence_par_champ"].values())==600,
         "P55P_CHAINAGE_P55O_INCOHERENT")
    return cfg

def public_report(cfg):
    verify(cfg)
    return {
        "schema_version":"P55P-BILAN-PUBLIC-1",
        "exercice":YEAR,"unite":"M_CAD",
        "score_maturite_estimatif_inchange_pct":53,
        "recettes_actuelles_imputs_revenus_mcad":65327,
        "recettes_actuelles_hors_impot_revenus_exposees_mcad":40731,
        "autres_recettes_et_transferts_hors_classement_mcad":60434,
        "recettes_total_actuel_mcad":166492,
        "deficit_actuel_comptable_mcad":-6265,
        "solde_actuel_au_sens_loi_mcad":-8612,
        "recettes_restantes_contrefactuelles_statiques_mcad":125761,
        "deficit_contrefactuel_comptable_mcad":-46996,
        "solde_contrefactuel_au_sens_loi_mcad":-49343,
        "ressources_requises_hypothetiquement_equilibre_comptable_mcad":46996,
        "ressources_requises_hypothetiquement_equilibre_loi_mcad":49343,
        "scenario_est_prevision":False,
        "suppression_de_taxes_proposee_comme_actee":False,
        "montant_anti_evasion_certifie_mcad":None,
        "taux_impot_revenus_recommande_pct":None,
        "assiette_taxable_deux_prelevements_mcad":None,
        "benefice_net_pouvoir_achat_demontre":False,
        "montants_financiers_nova_2027_2036_inconnus":600,
        "questions_a_resoudre_ouvertes":6,
        "avis_independents_recus":0,
        "economies_certifiees_mcad":None,
        "decision":NO_GO,
    }

def public_table(cfg):
    verify(cfg)
    return {
        "schema_version":"P55P-TABLE-PUBLIQUE-1",
        "sources":cfg["source_ref"],
        "composantes":cfg["recettes"],
        "solde_budget_source":cfg["depenses_et_solde"],
        "classification_exposition":cfg["classification_exposition"],
        "contrefactuel_statique":cfg["exposition_sensibilite_statique"],
        "questions_non_resolues":cfg["questions_a_resoudre"],
        "mesure_non_certifiante":True,"decision":NO_GO,
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bilan-public")
    parser.add_argument("--table-public")
    parser.add_argument("--exiger-faisabilite",action="store_true")
    args=parser.parse_args(argv)
    try:
        cfg=load()
        dest=[Path(s).expanduser().absolute()
              for s in (args.bilan_public,args.table_public) if s]
        need(len(set(x.resolve() for x in dest))==len(dest),
             "P55P_SORTIES_IDENTIQUES")
        for target in dest:
            need(target.parent.is_dir()
                 and not target.parent.is_symlink()
                 and not target.exists()
                 and not target.is_symlink(),
                 "P55P_SORTIE_EXISTANTE")
        result=public_report(cfg)
        if args.bilan_public:
            p55o.p55n.write_new(args.bilan_public,result)
        if args.table_public:
            p55o.p55n.write_new(args.table_public,public_table(cfg))
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if args.exiger_faisabilite else 0
    except (OSError,ValueError,TypeError,KeyError,
            UnicodeError,json.JSONDecodeError):
        print("P55P_REFUS: RECONCILIATION_BUDGETAIRE_INCORRECTE",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
