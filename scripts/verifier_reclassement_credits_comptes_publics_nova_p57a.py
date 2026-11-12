#!/usr/bin/env python3
"""P57A — comptes publics 2025-26 : crédits transférés versus dégrèvement TVQ.

La preuve historique est partielle. Ne jamais ajouter automatiquement 11 578 M$
ou 1 996 M$ aux coûts de 2027 ni y soustraire les crédits 2023.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from decimal import Decimal

SRC="https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Comptes-publics/FR/CPTFR_vol1-2025-2026.pdf"
METH="https://www.budget.finances.gouv.qc.ca/budget/outils/depenses-fiscales/metho-definition.asp"
VOLS="https://www.quebec.ca/gouvernement/finances-publiques/budget-comptes-publics/comptes-publics/volumes-comptes-publics"
ROOT="projets/projet-nova/etudes/"
DEPENDENCIES={
"p56p":"P56P_BASE_BUDGET_PREELECTORALE_2026_2031_VGQ_ET_ECARTS.json",
"p56w":"P56W_CREDITS_REMBOURSABLES_2023_PAR_CATEGORIE_ET_TRANCHES_PROTECTION.json",
"p56y":"P56Y_RENDEMENT_BRUT_NECESSAIRE_DEUX_PRELEVEMENTS_2027_2031.json",
"p56z":"P56Z_CONCORDANCE_CREDITS_2023_ET_RENDEMENT_2027_2031_SANS_DOUBLE_COMPTE.json",
"p56o":"P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
"p55n":"P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"}
REVENUE={
"personnes":(40678,8291,48969),
"societes":(11312,3287,14599),
"cotisations_services_sante":(9304,0,9304),
"foncier_scolaire":(1243,0,1243),
"total_revenus_impot_biens":(62537,11578,74115)}
CATS={
"particuliers":{
"FAMILLE":3941,"SOUTIEN_AINES":1710,"GARDE":965,
"MAINTIEN_DOMICILE":760,"PRIME_TRAVAIL":330,"AIDANTES":243,
"EPARGNE_ETUDES":150,"AUTRES_PART":192},
"societes":{
"CINEMA":631,"INVESTISSEMENT":629,"AFFAIRES_ELECTRONIQUES":600,
"RECHERCHE":549,"MULTIMEDIA":432,"POURBOIRES":133,"AUTRES_SOCIETES":313}}
PORTFOLIOS={
"SANTE_SERVICES_SOCIAUX":2810,"FAMILLE":4906,"EMPLOI_SOLIDARITE":405,
"ECONOMIE_INNOVATION_ENERGIE":2292,"CULTURE_COMMUNICATIONS":701,"AUTRES":464}
PRIOR={"credits_transferts_total":11130,"credits_transferts_particuliers":8059,
"credits_transferts_societes":3071,"credit_solidarite_reduction_taxes_ventes":1944,
"recettes_impot_sur_revenu_et_biens_consolidees":69081}
DEFINITION_FLAGS={
"compensation_entre_revenus_et_depenses_sans_gain_budgetaire",
"ce_reclassement_ne_cree_pas_d_argent_public_nouveau",
"les_credits_ne_sont_pas_tous_comptabilises_en_transferts",
"credit_solidarite_est_degrevement_sur_taxes_ventes"}
FORECAST_FLAGS={
"cible_budgetaire_2027_ne_s_ajuste_pas_automatiquement_de_11578_mcad",
"cible_budgetaire_2027_ne_s_ajuste_pas_automatiquement_de_1996_mcad",
"distinction_2026_observe_2027_prevu"}
def require(expr,code):
    if not expr:
        raise ValueError(code)
def n(value):
    require(type(value) is str and value.isascii() and value.isdecimal()
            and (value=="0" or (not value.startswith("0") and len(value)<10)),
            "MONTANT_ENTIER_MCAD_INVALID")
    return Decimal(value)

def verifier(d,p,w,y,z,o,b):
    require(isinstance(d,dict) and d.get("schema_version")=="P57A-1" and
       d.get("date_revision")=="2026-11-08" and
       d.get("objet")==
          "PREUVE_HISTORIQUE_TRAITEMENT_COMPTABLE_CREDITS_REMISES_VS_TRANSFERTS_PAS_SIMULATION_NOVA_2027" and
       d.get("decision")=="NO_GO_AUTOMATIQUE",
       "SCHEMA_OU_STATUT_NON_CONFORME")
    sources=d.get("sources")
    require(isinstance(sources,dict) and
       sources.get("comptes_publics_volume_1",{}).get("url")==SRC and
       sources["comptes_publics_volume_1"].get("annee_financiere")=="2025-2026" and
       sources["comptes_publics_volume_1"].get("pages_pdf_index_zero")==[108,109,110] and
       sources["comptes_publics_volume_1"].get("pages_imprimees")==[102,103,104] and
       sources["comptes_publics_volume_1"].get("verification_visuelle_effectuee") is True and
       sources["comptes_publics_volume_1"].get("empreinte_fichier_original_sha256") is None and
       sources.get("methodologie_depenses_fiscales",{}).get("url")==METH and
       sources["methodologie_depenses_fiscales"].get("non_equivalent_aux_comptes_consolides") is True and
       sources.get("publication_du_registre",{}).get("url")==VOLS and
       sources["publication_du_registre"].get("ne_pas_consolider_volume_1_plus_volume_2") is True,
       "SOURCE_COMPTABLE_NON_AUTHENTIFIEE")
    dep=sources.get("travaux_nova")
    require(isinstance(dep,dict) and
       set(dep)==set(DEPENDENCIES) and
       all(dep[key]==ROOT+filename for key,filename in DEPENDENCIES.items()),
       "DEPENDANCES_NON_CONCORDANTES")
    require(p.get("schema_version")=="P56P-1" and
       w.get("schema_version")=="P56W-1" and
       y.get("schema_version")=="P56Y-1" and
       z.get("schema_version")=="P56Z-1" and
       o.get("schema_version")=="P56O-1" and
       b.get("schema_version")=="P55N-1" and
       all(x.get("decision")=="NO_GO_AUTOMATIQUE" for x in (p,w,y,z,o)),
       "PREDECESSEURS_NON_VALIDES")
    method=d.get("regle_comptable_verifiee")
    require(isinstance(method,dict) and
       all(method.get(flag) is True for flag in DEFINITION_FLAGS) and
       method.get("verification_exhaustive_classification_par_programme_2027_absente") is True and
       method.get("classification_individuelle_des_beneficiaires_absente") is True,
       "CLASSIFICATION_DES_CREDITS_CONFONDUE")
    entries=d.get("revenus_et_reclassement_2025_2026_mcad")
    require(isinstance(entries,dict) and set(REVENUE).issubset(entries),
       "PRESENTATION_REVENUS_NON_COMPLETE")
    for key,triplet in REVENUE.items():
        record=entries[key]
        amounts=[n(record.get(k)) for k in (
          "revenus_fiscaux_nets_credits_remboursables",
          "credits_transferts_reclasses","revenus_consolides")]
        require(tuple(amounts)==tuple(Decimal(x) for x in triplet) and
           amounts[0]+amounts[1]==amounts[2],
           "RECLASSEMENT_INCORRECT_"+key)
    require(sum((n(entries[key]["revenus_fiscaux_nets_credits_remboursables"])
                 for key in REVENUE if key!="total_revenus_impot_biens"),Decimal(0))==62537 and
            sum((n(entries[key]["credits_transferts_reclasses"])
                 for key in REVENUE if key!="total_revenus_impot_biens"),Decimal(0))==11578,
            "SOUS_TOTAUX_REVENUS_NON_CONCILIES")
    solidarity=entries.get("credit_solidarite")
    require(isinstance(solidarity,dict) and
       n(solidarity.get("montant_degrevement_taxes_ventes"))==1996 and
       solidarity.get("inclure_dans_somme_transferts_impot_biens_11578") is False and
       solidarity.get("reductions_consom_deja_comprises_dans_revenus_net_publiés") is True,
       "SOLIDARITE_INCORRECTEMENT_AJOUTEE_AUX_TRANSFERTS")
    baseline=p["annees_historique_et_previsions"][0]
    require(baseline["exercice"]=="2025-2026" and
       n(entries["taxes_consommation_revenues_consolides"])==
           n(baseline["revenus"]["taxes_consommation"]) and
       all(n(entries[key]["revenus_consolides"])==n(baseline["revenus"][pkey])
           for key,pkey in (
               ("personnes","impot_particuliers"),("societes","impots_societes"),
               ("cotisations_services_sante","cotisations_services_sante"),
               ("foncier_scolaire","impot_foncier_scolaire"))),
       "COMPTES_CONSOLIDES_ET_P56P_NON_CONCILIES")
    parts=d.get("transferts_2025_2026_par_programme_mcad")
    require(isinstance(parts,dict),"PROGRAMMES_ABSENTS")
    for group,expected in CATS.items():
        items=parts.get(group)
        require(isinstance(items,list) and len(items)==len(expected) and
                {i.get("id") for i in items if isinstance(i,dict)}==set(expected),
                "LISTE_PROGRAMMES_NON_EXHAUSTIVE")
        for item in items:
            require(n(item.get("montant"))==expected[item["id"]] and
                isinstance(item.get("portefeuille"),str) and len(item["portefeuille"])>=5,
                "CREDIT_PROGRAMME_INCORRECT")
        require(sum(n(item["montant"]) for item in items)==
                n(parts["total_"+group]),"TOTAL_CREDITS_PROGRAMMES_INCORRECT")
    portfolio=parts.get("ventilation_consolidee_par_portefeuille")
    require(isinstance(portfolio,dict) and set(portfolio)==set(PORTFOLIOS) and
            all(n(portfolio[k])==v for k,v in PORTFOLIOS.items()) and
            sum(n(v) for v in portfolio.values())==11578 and
            n(parts.get("total_general"))==11578 and
            n(parts["total_particuliers"])+n(parts["total_societes"])==11578,
            "VENTILATION_PAR_MINISTERE_NON_CONCILIEE")
    prior=d.get("comparatif_2024_2025_mcad")
    require(isinstance(prior,dict) and
       all(n(prior.get(k))==v for k,v in PRIOR.items()) and
       n(prior["credits_transferts_particuliers"])+
       n(prior["credits_transferts_societes"])==
       n(prior["credits_transferts_total"]) and
       prior.get("source_volume_1_colonne_comparative") is True,
       "PRECEDENT_2024_25_NON_FIABLE")
    stat=d.get("distinction_statistique_2023")
    require(isinstance(stat,dict) and
       n(stat.get("statistiques_p56w_total_credit_remboursables_individus"))==
       n(w["controle_arrondis"]["ligne_totale_officielle_mcad"])==9305 and
       all(stat.get(flag) is True for flag in (
         "statistique_fiscale_2023_non_directement_comparable_au_8291_2026",
         "ne_pas_soustraire_9305_de_8291_pour_conclure_a_reduction_aides",
         "ecarts_annees_population_perimetre_et_imputation")) and
       stat.get("revenu_disponible_menage_nova_2027_certifie") is None,
       "SERIES_FISCALES_NON_COMPARABLES")
    forecast=d.get("risque_pour_scenarios_fiscaux_nova")
    require(isinstance(forecast,dict) and
       n(forecast.get("rendements_bruts_2027_2028_deux_piliers_p56y_mcad"))==
       n(y["annees"][0]["rendement_nouveaux_piliers_pour_solde_zero_sans_resorption_mcad"])==
       116663 and
       all(forecast.get(k) is True for k in FORECAST_FLAGS) and
       forecast.get("revenu_nouveau_impot_nova_reellement_certain_mcad") is None and
       forecast.get("credits_et_transferts_2027_deja_dans_cadre_reference_exactement_reconcilies") is False and
       forecast.get("classification_comptable_degrèvement_2027_verifiee") is False and
       forecast.get("droits_2027_des_beneficiaires_finances") is False and
       all(forecast.get(k) is None for k in (
         "cout_incremental_compensations_2027_mcad","economie_apparente_par_reclassement_mcad")),
       "FONDS_2027_FICTIFS_AJOUTES")
    proof=d.get("preuve_partiellement_obtenue")
    require(isinstance(proof,dict) and
       proof.get("niveau")=="PARTIEL_HISTORIQUE" and
       proof.get("preuve_methode_historique") is True and
       proof.get("preuve_tous_programmes_2027") is False and
       proof.get("condition_Z01_fermee") is False and
       proof.get("condition_P56O_FIN_INC_fermee") is False and
       proof.get("contre_expertise_humaine_externe_obtenue") is False and
       z.get("portes",[])[0].get("statut")=="NON_DEMONTRE",
       "PREUVE_HISTORIQUE_NON_FERMETURE_DE_PORTE")
    tasks=d.get("etapes_suivantes")
    require(isinstance(tasks,list) and len(tasks)==6 and
       {t.get("id") for t in tasks}=={f"A{i:02d}" for i in range(1,7)} and
       all(t.get("statut")=="OUVERT" and len(t.get("objectif",""))>=60 for t in tasks),
       "LISTE_PREUVES_COMPLEMENTAIRES_INCOMPLETE")
    adv=d.get("avancement")
    require(isinstance(adv,dict) and
       adv.get("score_estime_p55n")==b.get("score_estimatif")==53 and
       adv.get("points_restants_estimes")==47 and
       adv.get("p52b_montants_inconnus")==600 and
       adv.get("p52d_incidences_manquantes")==720 and
       adv.get("p52a_preuves_non_validees")==20 and
       adv.get("portes_p56o_demonstrees")==0 and
       adv.get("avis_independants_signes")==0 and
       adv.get("programme_nova_termine") is False and
       adv.get("changements_apportes_p52b")==0 and
       adv.get("pourcentage_non_majore_par_test_ou_nouvelle_source") is True and
       adv.get("main_et_sinjira_non_modifies") is True,
       "SCORE_NON_ETAYE")
    return {
       "jalon":"P57A",
       "exercice_preuve":"2025-2026",
       "total_reclassement_transferts_mcad":"11578",
       "particuliers_transferts_mcad":"8291",
       "societes_transferts_mcad":"3287",
       "degrevement_solidarite_taxes_consommation_mcad":"1996",
       "reclassement_revenus_avant_mcad":"62537",
       "reclassement_revenus_apres_mcad":"74115",
       "une_reclassification_n_est_pas_une_economie":True,
       "credits_de_2023_non_projetes_en_2027":True,
       "condition_Z01_preuve_partielle_historique":True,
       "condition_Z01_validee_pour_2027":False,
       "budget_Nova_2027_certifie":False,
       "score_estime_pourcent":53,"points_restants":47,
       "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("preuve","p56p","p56w","p56y","p56z","p56o","p55n"):
        parser.add_argument("--"+key,type=Path,required=True)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--exiger-preuve-2027-validee",action="store_true")
    args=parser.parse_args(argv)
    if args.exiger_preuve_2027_validee:
        print("REFUS: preuve historique 2025-2026, pas une simulation 2027",file=sys.stderr)
        return 3
    try:
        def load(path):return json.loads(path.read_text(encoding="utf-8"))
        vals=[load(getattr(args,k)) for k in ("preuve","p56p","p56w","p56y","p56z","p56o","p55n")]
        output=json.dumps(verifier(*vals),ensure_ascii=False,indent=2)+"\n"
        if args.rapport:
            with args.rapport.open("x",encoding="utf-8") as file:
                file.write(output)
        else:
            print(output,end="")
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
