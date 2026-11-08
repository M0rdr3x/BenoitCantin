#!/usr/bin/env python3
"""P56Q — calculer le risque de remplacement de trois recettes, jamais un taux Nova.

Mode : continuation comptable du Québec dans le Canada, sans changement de
comportement, de services, de transfert fédéral ni de financement des crédits.
La présence d'un fichier sur Github et les tests n'authentifient pas les
octets du simulateur officiel Excel amendé (encore inaccessible).

Seul résultat autorisé : contre-factuel mécanique de finances du gouvernement.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
import rapprocher_rapport_preelectoral_2026_nova_p56p as old

VERSION="P56Q-1"
YEARS=("2025-2026","2026-2027","2027-2028","2028-2029","2029-2030","2030-2031")
RISKS=("revenus_fss_mcad","revenus_impot_foncier_scolaire_mcad",
       "revenus_taxes_consommation_mcad")
INCOME="revenus_existants_impots_personnes_et_societes_mcad"
TRIPLE="trois_categories_risque_suppression_mcad"
REPORT="projets/projet-nova/etudes/P56P_BASE_BUDGET_PREELECTORALE_2026_2031_VGQ_ET_ECARTS.json"
CLOSURE="projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json"
P52B="projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json"
P55N="projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
SOURCE_INFO={
"TABLEAU_PDF_OFFICIEL":"https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf",
"SIMULATEUR_AMENDE_OFFICIEL":"https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/RPE2026_simulateur_amende.xlsx",
"BULLETIN_FISCAL_2026_7":"https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Bulletins/FR/BULFR_2026-7.pdf"
}
CONTROLS=[
"trois_categories_fss_scolaire_consommation_et_non_toutes_taxes_ou_prelevements",
"conserver_cotisations_et_autres_paiements_non_classes",
"aucun_transfert_inter_gouvernemental_compte_comme_economie",
"aucune_suppression_reelle_de_recettes_ou_de_services",
"ne_pas_doubler_service_dette",
"ecart_a_resorber_non_compte_comme_economie_reelle",
"ne_pas_confondre_revenu_impots_existants_et_assiette_imposable",
"aucun_taux_nova_derive_par_division_sur_assiette_inconnue",
"ne_pas_extrapoler_exercice_2031_2032_a_2036_2037",
"ne_pas_compter_postrapport_bulletin_2026_7_comme_loi_en_vigueur",
"statut_excel_amende_non_verifie_bloque_validation_dette"
]

def require(condition,err):
    if not condition:
        raise ValueError(err)

def integer(value):
    return old.integer(value)

def audit(data,baseline,model,bar,closure):
    previous=old.assess(baseline,model,bar,closure)
    require(isinstance(data,dict) and data.get("schema_version")==VERSION and
            data.get("date_revision")=="2026-11-08" and
            data.get("objet")==
            "EXPOSITION_PROVINCIALE_STATIQUE_TROIS_PRELEVEMENTS_2027_2031_ET_ETAT_VERIFICATION_SIMULATEUR_OFFICIEL" and
            data.get("statut")==
            "CONTRE_FACTUEL_PUREMENT_ARITHMETIQUE_NON_PROPOSITION_DE_SUPPRESSION" and
            data.get("decision")=="NO_GO_AUTOMATIQUE",
            "SCHEMA_P56Q_NON_CONFORME")
    sources=data.get("sources")
    require(isinstance(sources,dict) and set(sources)==set(SOURCE_INFO)|{"P56P"},
            "PROVENANCE_NON_EXHAUSTIVE")
    require(sources["P56P"].get("path")==REPORT and
            sources["P56P"].get("statut")=="RECONCILIATION_GITHUB_P56P_SUCCESS" and
            sources["P56P"].get("tableau")=="2" and
            sources["P56P"].get("page_pdf_index_zero")==19,
            "SOURCE_P56P_NON_GARANTIE")
    for k,url in SOURCE_INFO.items():
        require(isinstance(sources.get(k),dict) and sources[k].get("url")==url,
                "SOURCE_URL_OU_ABSENCE_"+k)
    pdf=sources["TABLEAU_PDF_OFFICIEL"]
    require(pdf.get("page_pdf_index_zero")==19 and
            pdf.get("page_imprimee")==17 and
            pdf.get("consultation_visuelle") is True and
            pdf.get("tableau")==2,"PDF_OFFICIEL_NON_VISUELLEMENT_VERIFIE")
    xlsx=sources["SIMULATEUR_AMENDE_OFFICIEL"]
    require(xlsx.get("page_index")==
            "https://www.quebec.ca/gouvernement/ministeres-organismes/finances/publications" and
            xlsx.get("date_amendement")=="2026-09-03" and
            xlsx.get("statut")=="LIEN_OFFICIEL_CONFIRME_CONTENU_XLSX_NON_ACCESSIBLE" and
            xlsx.get("fichier_binaire_telecharge") is False and
            xlsx.get("empreinte_sha256") is None and
            xlsx.get("feuille_amendement_lue") is False and
            xlsx.get("formules_recalculees") is False and
            xlsx.get("impact_final_sur_modele_dette_valide") is False,
            "XLSX_AMENDE_NON_EXAMINE_NE_PAS_CERTIFIER")
    bulletin=sources["BULLETIN_FISCAL_2026_7"]
    require(bulletin.get("date")=="2026-11-05" and
            bulletin.get("page_pdf_index_zero")==0 and
            bulletin.get("topics")==[
                "MASSOTHERAPIE","APPAREILS_THERAPIE_CHAMPS_ELECTRIQUES_ALTERNATIFS"] and
            bulletin.get("consultation_visuelle") is True and
            bulletin.get("mesures_adoptees_et_en_vigueur") is False and
            bulletin.get("courant_budget_2027_2031_revise_mcad") is None,
            "BULLETIN_POSTRAPPORT_NE_PAS_PRESUMER_EN_VIGUEUR")
    scopes=data.get("perimetres")
    require(isinstance(scopes,dict) and set(scopes)=={
            "QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN"},"REGIMES_NON_SEPARES")
    provincial=scopes["QUEBEC_DANS_CANADA"]
    sovereign=scopes["QUEBEC_SOUVERAIN"]
    require(provincial.get("regime")=="QUEBEC_DANS_CANADA" and
            all(provincial.get(k) is True for k in (
              "recettes_federales_non_supprimables_unilateralement",
              "transferts_federaux_publics_conserves_dans_illustration",
              "service_dette_deja_compris_dans_depenses",
              "prestations_crédits_et_services_non_supprimes_par_hypothese")),
            "CADRE_CANADIEN_MODIFIE")
    require(sovereign.get("regime")=="QUEBEC_SOUVERAIN_HYPOTHETIQUE" and
            sovereign.get("transferts_federaux_montants_automatiquement_conserves") is False and
            sovereign.get("budget_souverain_decennal_etabli") is False and
            all(sovereign.get(k) is None for k in (
              "assiettes_federales_nouvelles_mcad",
              "couts_fonctions_federales_mcad",
              "revenus_nouveau_prelevement_anti_paradis_mcad")),
            "FONCTIONS_SOUVERAINES_OU_TRANSFERTS_INVENTES")
    require(isinstance(data.get("regles_usage"),dict) and
            set(data["regles_usage"])==set(CONTROLS) and
            all(data["regles_usage"][k] is True for k in CONTROLS),
            "DOUBLES_COMPTES_ET_DROITS_NON_PROTEGES")
    actual=data.get("annees_reconciliees")
    baseline_rows=baseline.get("annees_historique_et_previsions")
    require(isinstance(actual,list) and
            [r.get("exercice") for r in actual]==list(YEARS) and
            isinstance(baseline_rows,list) and
            [r.get("exercice") for r in baseline_rows]==list(YEARS),
            "SIX_EXERCICES_COHERENTS_REQUIS")
    totals={}
    for i,(r,p) in enumerate(zip(actual,baseline_rows)):
        require(r.get("projection_p52b") is (i>=2) and
                r.get("classement")==(
                  "OBSERVE_COMPTE_PUBLIC_2025_2026" if i==0 else
                  "PREVISION_GOUV_AOUT_2026") and
                all(r.get(flag) is True for flag in (
                  "hypothese_statique_revenus_autres_inchanges",
                  "hypothese_statique_depenses_services_inchangees",
                  "gouvernement_federal_dans_le_canada_pouvoirs_inchanges",
                  "calcul_n_est_pas_un_budget_nova")) and
                r.get("nouveaux_taux_fiscaux_nova") is None and
                r.get("recettes_nouveau_prelevement_anti_paradis_mcad") is None,
                "CONCEPT_CONTREFACTUEL_DEVENU_PROPOSITION_NOVA")
        expected_income=integer(p["revenus"]["impot_particuliers"])+integer(
            p["revenus"]["impots_societes"])
        expected_risk=(
            integer(p["revenus"]["cotisations_services_sante"])+
            integer(p["revenus"]["impot_foncier_scolaire"])+
            integer(p["revenus"]["taxes_consommation"]))
        require(integer(r[INCOME])==expected_income,
                "IMPOTS_ACTUELS_PERSONNES_SOCIETES_NON_RECONCILIES")
        for label,source in zip(RISKS,(
              "cotisations_services_sante","impot_foncier_scolaire","taxes_consommation")):
            require(integer(r[label])==integer(p["revenus"][source]),
                    "POSTE_SUPPRIME_INVALIDE_"+label)
        require(integer(r[TRIPLE])==expected_risk,
                "TROIS_CATEGORIES_SANS_DOUBLE_COMPTE")
        total=integer(p["total_revenus_mcad"])
        initial=integer(p["solde_budgetaire_selon_loi_mcad"])
        mitigation=integer(p["ecart_a_resorber_non_finance_par_mesures_identifiees_mcad"])
        expected={
          "revenus_publics_initiaux_mcad":total,
          "revenus_restants_si_retrait_purement_theorique_mcad":total-expected_risk,
          "solde_budgetaire_initial_au_sens_de_la_loi_mcad":initial,
          "ecart_gouvernemental_a_resorber_mcad":mitigation,
          "solde_budgetaire_theorique_sans_recettes_remplacement_avec_ecart_a_resorber_mcad":initial-expected_risk,
          "solde_budgetaire_theorique_sans_recettes_remplacement_sans_ecart_a_resorber_mcad":initial-expected_risk-mitigation,
          "remplacement_pour_maintenir_revenus_observes_ou_prevus_mcad":expected_risk,
          "ressources_theoriques_additionnelles_pour_solde_loi_zero_si_ecart_resorbe_mcad":max(0,expected_risk-initial),
          "ressources_theoriques_additionnelles_pour_solde_loi_zero_sans_resorption_mcad":max(0,expected_risk-initial+mitigation)
        }
        for key,val in expected.items():
            require(integer(r.get(key))==val,"RECONCILIATION_CONTREFACTUELLE_"+key)
        totals[r["exercice"]]={
          "risque_trois_catégories_mcad":str(expected_risk),
          "revenus_restants_mcad":str(total-expected_risk),
          "solde_statique_si_retrait_sans_remplacement_avec_ecart_mcad":str(initial-expected_risk),
          "solde_statique_si_retrait_sans_remplacement_sans_ecart_mcad":str(initial-expected_risk-mitigation),
          "besoin_remplacement_revenus_mcad":str(expected_risk),
          "ressources_pour_equilibre_loi_avec_ecart_mcad":str(max(0,expected_risk-initial)),
          "ressources_pour_equilibre_loi_sans_ecart_mcad":str(max(0,expected_risk-initial+mitigation))
        }
    require(integer(actual[0][TRIPLE])==40186 and
            integer(actual[2][TRIPLE])==42875 and
            integer(actual[2]["solde_budgetaire_theorique_sans_recettes_remplacement_avec_ecart_a_resorber_mcad"])==-48570,
            "POINT_DE_DEPART_P56J_OU_2027_28_ERRONE")
    tasks=data.get("preuves_suivantes")
    require(isinstance(tasks,list) and len(tasks)==10 and
            {x.get("id") for x in tasks if isinstance(x,dict)}==
              {f"Q{i:02d}" for i in range(1,11)} and
            all(x.get("statut")=="OUVERT" and x.get("preuve") is None and
                len(x.get("objet",""))>=65 for x in tasks),
            "PORTES_DE_PREUVE_NON_FERMABLES_AUTOMATIQUEMENT")
    integ=data.get("integration")
    required={
      "p56p":REPORT,"p56o":CLOSURE,"p52b":P52B,"barometre":P55N,
      "p52b_budget_nova_cellules_modifiees":0,"p52b_montants_manquants":600,
      "p52d_incidences_manquantes":720,"p52a_preuves_non_validees":20,
      "p55n_score_estimatif_pourcent":53,"avis_independants_signes":0,
      "portes_cloture_completees":0,"taux_nova_candidats_renseignes":0,
      "resultats_reels_nova_certifies":0,"decision":"NO_GO_AUTOMATIQUE"
    }
    require(isinstance(integ,dict) and
            all(integ.get(k)==v for k,v in required.items()),
            "P56Q_NON_RECONCILIE_AVEC_INCONNUES")
    require(previous["p52b_montants_encore_inconnus"]==600 and
            previous["score_estime_pourcent"]==53 and
            closure.get("definition_terminee",{}).get("etat_actuel_termine") is False,
            "AVANCEMENT_FICTIF")
    unknown=sum(v is None for region in model["regimes"].values()
                for scen in region["trajectoires"].values()
                for fy in scen for group in ("recettes","depenses")
                for v in fy[group].values())
    require(unknown==600,"BASE_NOVA_P52B_PAS_PROJETEE")
    return {
      "jalon":"P56Q","schema_version":VERSION,
      "controle":"CONTREFACTUEL_STATIQUE_NON_AUTORISATION_FISCALE",
      "annees_reconciliees":list(YEARS),
      "fiscal_2027_2028":totals["2027-2028"],
      "montants_par_exercice":totals,
      "nombre_exercices_chiffres_source":len(YEARS),
      "nombre_exercices_2027_2036_source_disponibles":4,
      "nombre_exercices_2027_2036_non_couverts":6,
      "simulateur_officiel_amende_feuille_verifiee":False,
      "mesures_bulletin_2026_7_chiffrees_et_en_vigueur":False,
      "budget_nova_2027_2036_valide":False,
      "budget_souverain_valide":False,
      "suppressions_fiscales_adoptees":False,
      "taux_nova_issus_de_ces_calculs":None,
      "conditions_fermees":0,
      "p52b_montants_manquants":600,
      "p52d_incidences_manquantes":720,
      "score_estime_p55n":53,
      "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("pont","p56p","p52b","barometre","p56o"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--exiger-budget-nova-certifie",action="store_true")
    a=parser.parse_args(argv)
    if a.exiger_budget_nova_certifie:
        print("REFUS: cas statique et simulateur officiel Excel non vérifié",file=sys.stderr)
        return 3
    try:
        def load(path):
            return json.loads(path.read_text(encoding="utf-8"))
        result=audit(load(a.pont),load(a.p56p),load(a.p52b),
                     load(a.barometre),load(a.p56o))
        serialized=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as target:
                target.write(serialized)
        else:
            print(serialized,end="")
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
