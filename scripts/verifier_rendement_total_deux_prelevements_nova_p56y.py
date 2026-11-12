#!/usr/bin/env python3
"""P56Y : combien les deux nouveaux piliers devraient-ils rapporter ensemble ?

Ne confond pas l'ajout de recettes (ex. 48,570 G$ en 2027-28) avec le
rendement total des nouveaux piliers, qui remplacent AUSSI les anciens
impots sur les revenus des particuliers et des societes (68,093 G$).
Tous les montants sont des tests statiques de flux BUDGETAIRES APRES
CREDITS applicable au regime provincial, pas un taux Nova.
"""
from __future__ import annotations
import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

YEARS=("2027-2028","2028-2029","2029-2030","2030-2031")
SRC={
"P56R":"projets/projet-nova/etudes/P56R_INVENTAIRE_EXHAUSTIF_CATEGORIES_RECETTES_ET_PONT_FISCAL_2026_2031.json",
"P56Q":"projets/projet-nova/etudes/P56Q_PONT_CONTREFACTUEL_RECETTES_2027_2031_SIMULATEUR_AMENDE.json",
"P56X":"projets/projet-nova/etudes/P56X_ASSIETTES_HISTORIQUES_ET_VERROU_TAUX_NOVA_2027_2028.json",
"P56O":"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
"P55N":"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json",
"origine_budget":"https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf"}
FIELDS_NONE=(
"nouvelle_assiette_imposable_personnes_mcad","nouvelle_assiette_imposable_societes_mcad",
"rendement_net_fiscalite_revenu_nova_mcad","rendement_net_prelevement_anti_paradis_nova_mcad",
"compensations_sociales_nova_mcad","couts_transition_et_protection_emplois_nova_mcad",
"recettes_non_fiscales_requalifiees_certifiees_mcad",
"economie_administrative_reelle_certifiee_mcad","solde_final_nova_chiffre")
CAUTIONS=(
"cible_rendement_brut_n_est_pas_taux_imposition",
"cible_total_inclut_remplacement_des_impots_personnes_et_societes_existants",
"ne_pas_additionner_un_impot_nouveau_au_maintien_d_impots_remplaces",
"ne_pas_ajouter_les_42_875_deux_fois",
"recettes_souveraines_inconnues",
"trois_categories_ne_constituent_pas_toutes_les_taxes_et_cotisations",
"fonds_generations_deja_dans_solde_loi",
"ecarts_a_resorber_ne_sont_pas_gains_realises",
"revenus_anti_paradis_sont_inconnus_non_zero",
"credits_remboursables_et_pouvoir_achat_a_preserver",
"pas_de_suppression_de_postes_ou_services_automatique")
INT=re.compile(r"-?(?:0|[1-9][0-9]{0,12})\Z")

def require(ok,message):
    if not ok:
        raise ValueError(message)
def integer(value):
    require(type(value) is str and INT.fullmatch(value) is not None,
            "MONTANT_MCAD_ENTIER_REQUIS")
    return Decimal(value)

def audit(d,r,q,x,o,b):
    require(isinstance(d,dict) and d.get("schema_version")=="P56Y-1" and
        d.get("date_revision")=="2026-11-08" and
        d.get("statut")=="TEST_DE_CONTRAINTES_FINANCIERES_SANS_ASSIETTES_NOVA" and
        d.get("decision")=="NO_GO_AUTOMATIQUE",
        "ENTETE_MODELE_DEUX_PILIERS_NON_CONFORME")
    require(all(isinstance(z,dict) for z in (r,q,x,o,b)) and
        r.get("schema_version")=="P56R-1" and
        r.get("decision")=="NO_GO_AUTOMATIQUE" and
        q.get("schema_version")=="P56Q-1" and
        q.get("decision")=="NO_GO_AUTOMATIQUE" and
        x.get("schema_version")=="P56X-1" and
        x.get("decision")=="NO_GO_AUTOMATIQUE" and
        o.get("schema_version")=="P56O-1" and
        o.get("definition_terminee",{}).get("etat_actuel_termine") is False and
        b.get("schema_version")=="P55N-1" and
        b.get("score_estimatif")==53,
        "REGISTRES_SOURCES_NON_VALIDEES")
    require(d.get("sources")==SRC,"SOURCES_RECONCILIATION_MODIFIEES")
    formulas=d.get("deux_formules")
    require(isinstance(formulas,dict) and
        formulas.get("replacement_total")==
        "RENDEMENT_BRUT_CIBLE_NOUVEAUX_PILIERS = IMPOTS_REVENU_ACTUELS + TROIS_RECETTES_RETIREES" and
        formulas.get("objectif_solde_zero_conditionnel")==
        "RENDEMENT_CIBLE_POUR_SOLDE_ZERO = IMPOTS_REVENU_ACTUELS + TROIS_RECETTES_RETIREES - SOLDE_LEGAL_DE_REFERENCE + ECART_NON_RESORBE" and
        all(formulas.get(k) is True for k in (
           "ne_pas_confondre_nouvel_impot_total_avec_recettes_additionnelles",
           "recettes_pilier_antiparadis_et_impot_sur_revenu_non_decomposees",
           "transformation_formelle_sans_effets_comportementaux_et_sans_couts_transition")),
        "FORMULE_REMPLACEMENT_FISCAL_FALSIFIEE")
    source_q={z["exercice"]:z for z in q["annees_reconciliees"]}
    source_r={z["exercice"]:z for z in r["rapprochement_annees"]}
    require(set(YEARS).issubset(source_q) and set(YEARS).issubset(source_r),
            "PREVISIONS_GOUVERNEMENTALES_INCOMPLETES")
    rows=d.get("annees")
    require(isinstance(rows,list) and
        [z.get("exercice") for z in rows]==list(YEARS),
        "QUATRE_EXERCICES_REQUIS")
    summary={}
    for row in rows:
        fy=row["exercice"]
        qy=source_q[fy]
        ry=source_r[fy]
        incomes=integer(ry["impots_sur_revenu_actuels_mcad"])
        at_risk=integer(ry["trois_categories_a_remplacer_si_supprimees_mcad"])
        total=integer(ry["revenus_consolides_regime_actuel_mcad"])
        legal=integer(qy["solde_budgetaire_initial_au_sens_de_la_loi_mcad"])
        gap=integer(qy["ecart_gouvernemental_a_resorber_mcad"])
        add=incomes+at_risk
        residual=total-add
        require(incomes==integer(qy["revenus_existants_impots_personnes_et_societes_mcad"]) and
                at_risk==integer(qy["trois_categories_risque_suppression_mcad"]) and
                total==integer(qy["revenus_publics_initiaux_mcad"]),
                "PRELEVEMENTS_BUDGETAIRES_DECONCILIES")
        expected={
          "recettes_publiques_de_reference_mcad":total,
          "impots_personnes_societes_actuels_que_nova_remplacerait_mcad":incomes,
          "trois_autres_prelevements_que_nova_pourrait_remplacer_mcad":at_risk,
          "recettes_total_a_substituer_si_deux_nouveaux_piliers_mcad":add,
          "recettes_restant_hors_impots_et_trois_prelevements_mcad":residual,
          "solde_legal_reference_avec_resorption_mcad":legal,
          "ecart_a_resorber_non_finance_mcad":gap,
          "solde_legal_reference_sans_resorption_mcad":legal-gap,
          "rendement_nouveaux_piliers_pour_conserver_solde_existant_mcad":add,
          "rendement_nouveaux_piliers_pour_solde_zero_avec_resorption_mcad":add-legal,
          "rendement_nouveaux_piliers_pour_solde_zero_sans_resorption_mcad":add-legal+gap,
          "minimum_nouvelles_recettes_seulement_par_rapport_aux_impots_actuels_si_conserves_mcad":
             max(Decimal(0),at_risk-legal+gap)
        }
        for key,correct in expected.items():
            require(integer(row.get(key))==correct,
                    "BUDGET_DOUBLE_COMPTAGE_"+fy+"_"+key)
        require(row.get("classification")=="TEST_STATIQUE_REGIME_CANADA_SANS_NOUVELLES_ASSIETTES" and
                all(row.get(k) is None for k in FIELDS_NONE) and
                row.get("suffisance_qualite_services_nova_certifiee") is False and
                row.get("taux_nova_2027_2036_adopte") is False,
                "RECETTES_NOVA_ET_PROTECTION_NON_VERIFIEES")
        summary[fy]={
          "autres_recettes_conservees_mcad":str(residual),
          "rendement_nouveaux_piliers_memes_recettes_mcad":str(add),
          "rendement_nouveaux_piliers_pour_solde_zero_prudent_mcad":str(add-legal+gap),
          "besoin_additionnel_si_impots_existants_conserves_mcad":
            str(max(Decimal(0),at_risk-legal+gap))}
    require(summary["2027-2028"]=={
       "autres_recettes_conservees_mcad":"63257",
       "rendement_nouveaux_piliers_memes_recettes_mcad":"110968",
       "rendement_nouveaux_piliers_pour_solde_zero_prudent_mcad":"116663",
       "besoin_additionnel_si_impots_existants_conserves_mcad":"48570"} and
       integer(x["repere_2027_2028"]["impots_revenu_existants_mcad"])==68093 and
       integer(x["repere_2027_2028"]["besoin_financement_arithmetique_pour_solde_legal_zero_si_retrait_integral_mcad"])==48570,
       "REPERE_2027_NE_PAS_CONFONDRE_REVENUS_BRUTS_ET_ADDITIONNELS")
    scopes=d.get("regimes")
    require(isinstance(scopes,dict) and set(scopes)=={
       "QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN"},"CONSTITUTION_REGIMES_FUSIONNES")
    canada=scopes["QUEBEC_DANS_CANADA"]
    sovereign=scopes["QUEBEC_SOUVERAIN"]
    require(canada.get("classification")=="TEST_REMPLACEMENT_PRELEVEMENTS_PROVINCIAUX" and
        canada.get("transferts_federaux_dans_reference_publique") is True and
        canada.get("recettes_federales_additionnelles_au_budget_nova") is None and
        canada.get("impots_federaux_non_abrogeables_par_quebec") is True and
        canada.get("simulation_incidence_familles_realisee") is False and
        sovereign.get("classification")=="MODELE_DISTINCT_NON_CALCULE" and
        sovereign.get("transferts_federaux_de_reference_conserves_automatiquement") is False and
        all(sovereign.get(k) is None for k in (
           "recettes_federales_additionnelles_au_budget_nova",
           "nouveaux_couts_competences_federales_mcad",
           "couts_repartition_dette_pensions_actifs_mcad")) and
        sovereign.get("budget_souverain_certifie") is False,
        "REGIME_SOUVERAIN_FICTIF")
    limits=d.get("precautions")
    require(isinstance(limits,dict) and set(limits)==set(CAUTIONS) and
        all(limits.get(k) is True for k in CAUTIONS),
        "IMPOTS_DOUBLE_COMPTE_OU_DROITS_NON_RESPECTES")
    tasks=d.get("blocages")
    require(isinstance(tasks,list) and len(tasks)==6 and
        {z.get("id") for z in tasks}=={f"Y{i:02d}" for i in range(1,7)} and
        all(z.get("statut")=="NON_DEMONTRE" and
            len(z.get("condition",""))>=75 for z in tasks),
        "PREUVES_DE_FISCALITE_NON_OBTENUES")
    done=d.get("avancement")
    required={"score_p55n":53,"points_estimes_manquants":47,
      "portes_p56o_closes":0,"p52b_inconnus":600,"p52d_incidences_inconnues":720,
      "p52a_preuves_a_valider":20,"taux_nova_certifies":0,
      "modele_souverain_calcule":False,"loi_fiscale_adoptee":False,
      "decision":"NO_GO_AUTOMATIQUE"}
    require(isinstance(done,dict) and all(type(done.get(k)) is type(v) and
       done.get(k)==v for k,v in required.items()),"COMPLETUDE_SUR_DECLAREE")
    return {"jalon":"P56Y","score_estime_pourcent":53,
      "annees":summary,"objectif_2027_2028_mcad":"116663",
      "objectif_seulement_additionnel_2027_2028_mcad":"48570",
      "taux_fiscal_nova_choisi":False,"recettes_fiscales_nova_nouvelles_validees":False,
      "budget_decennal_nova_certifie":False,"decision":"NO_GO_AUTOMATIQUE"}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("pont","p56r","p56q","p56x","p56o","barometre"):
        ap.add_argument("--"+name,required=True,type=Path)
    ap.add_argument("--rapport",type=Path)
    ap.add_argument("--exiger-taux-adoptes",action="store_true")
    a=ap.parse_args(argv)
    if a.exiger_taux_adoptes:
        print("REFUS: rendement cible n'est pas un taux Nova certifie",file=sys.stderr)
        return 3
    try:
        def rd(path):
            return json.loads(path.read_text(encoding="utf-8"))
        result=audit(*[rd(getattr(a,k)) for k in (
          "pont","p56r","p56q","p56x","p56o","barometre")])
        serial=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as f:
                f.write(serial)
        else:
            print(serial,end="")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
