#!/usr/bin/env python3
"""P56V: verifie le pont finances-services 2027-2029 et reserves du VGQ.

Les previsions gouvernementales ne constituent ni un plan Nova finance,
ni une assurance de maintien de service. Les efforts du VGQ sont deja
supposes dans le cadre publie: ne jamais les additionner aux depenses.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys

YEARS=("2027-2028","2028-2029")
FUTURE=("2029-2030","2030-2031","2031-2032","2032-2033",
        "2033-2034","2034-2035","2035-2036","2036-2037")
OPTS={"S1_CONTINUITE":0,"S2_TRANSITION_CONDITIONNELLE":1,
      "S3_CIBLE_DEUX_PRELEVEMENTS":4}
LINKS={
 "p56p":"projets/projet-nova/etudes/P56P_BASE_BUDGET_PREELECTORALE_2026_2031_VGQ_ET_ECARTS.json",
 "p56s":"projets/projet-nova/etudes/P56S_TROIS_OPTIONS_FISCALES_2027_2031_ET_CONDITIONS_PROTECTION.json",
 "p56t":"projets/projet-nova/etudes/P56T_BASE_OFFICIELLE_DEPENSES_PORTEFEUILLES_2025_2029_PROTECTION_SERVICES.json",
 "p56o":"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
 "p55n":"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
}
VGQ="https://www.vgq.qc.ca/fr/communique/C2026-3"
PDF="https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf"
ASSUMPTIONS=(
 "avis_vgq_sur_cadre_actuel_ne_valide_pas_nova",
 "effort_budgetaire_vgq_deja_integre_au_cadre_reference_estime",
 "effort_vgq_ne_pas_ajouter_une_seconde_fois_au_total_depenses",
 "minimum_vgq_ne_pas_convertir_en_cout_supplémentaire_nova",
 "ecart_a_resorber_de_p56p_reste_distinct_des_efforts_de_depenses",
 "pas_de_garantie_de_services_par_niveau_depenses_agrege",
 "service_dette_ne_pas_doubler",
 "montants_souverainete_restant_inconnus"
)
CENTS=re.compile(r"-?(?:0|[1-9][0-9]{0,10})\.[0-9]{2}\Z")
NUMBER=re.compile(r"-?(?:0|[1-9][0-9]{0,10})\Z")

def require(value,code):
    if not value:
        raise ValueError(code)

def decimal(value,cents=False):
    require(type(value) is str and
            (CENTS if cents else NUMBER).fullmatch(value) is not None,
            "MONTANT_MCAD_NON_CANONIQUE")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("MONTANT_NON_NUMERIQUE") from exc

def audit(d,p,s,t,o,b):
    require(isinstance(d,dict) and d.get("schema_version")=="P56V-1" and
       d.get("date_revision")=="2026-11-08" and
       d.get("statut")=="COMPARAISON_STATIQUE_DONNEES_PUBLIQUES_ET_CANDIDATS_NOVA_NON_ADOPTES" and
       d.get("decision")=="NO_GO_AUTOMATIQUE",
       "P56V_N_EST_PAS_UNE_BASE_CANDIDATE_PRUDENTE")
    require(all(isinstance(x,dict) for x in (p,s,t,o,b)) and
       p.get("schema_version")=="P56P-1" and
       s.get("schema_version")=="P56S-1" and
       t.get("schema_version")=="P56T-1" and
       o.get("schema_version")=="P56O-1" and
       b.get("schema_version")=="P55N-1" and
       b.get("score_estimatif")==53 and
       o.get("definition_terminee",{}).get("etat_actuel_termine") is False,
       "BASE_DE_CONTROLE_NOVA_NON_CERTIFIEE")
    provenance=d.get("provenance")
    require(isinstance(provenance,dict) and
       all(provenance.get(k)==v for k,v in LINKS.items()),"SOURCE_NON_ATTESTEE")
    mfq=provenance.get("rapport_public")
    require(isinstance(mfq,dict) and mfq.get("url")==PDF and
       mfq.get("date")=="2026-08-17" and
       mfq.get("tableau_budget")==2 and
       mfq.get("tableau_services")==25,"TABLEAUX_ORIGINE_NON_VERIFIES")
    vgq=provenance.get("vgq")
    require(isinstance(vgq,dict) and vgq.get("url")==VGQ and
       vgq.get("date")=="2026-08-17" and
       vgq.get("limite_examen")==["2026-2027","2027-2028","2028-2029"] and
       decimal(vgq.get("efforts_minimum_2027_2028_mcad"))==2000 and
       decimal(vgq.get("efforts_minimum_2028_2029_mcad"))==3000 and
       decimal(vgq.get("ecart_additionnel_possible_2028_2029_mcad"))==1850 and
       vgq.get("publication_externe_pas_audit_nova") is True and
       vgq.get("efforts_budgetaires_secteurs_non_ventiles_dans_pont") is True and
       vgq.get("examen_qualite_ou_adequation_services") is False,
       "EFFORTS_VGQ_PRESENTES_COMME_ECONOMIES_NOVA")
    scope=d.get("perimetre")
    require(isinstance(scope,dict) and
       scope.get("regime_actuel")=="QUEBEC_DANS_CANADA" and
       scope.get("autre_regime")=="QUEBEC_SOUVERAIN_NON_SIMULE" and
       scope.get("annees_sources_fiscales_et_services")==list(YEARS) and
       scope.get("annees_decennales_sans_ventilation_services_officielle_rapport")==list(FUTURE) and
       all(scope.get(k) is True for k in ASSUMPTIONS),
       "PERIMETRE_VGQ_OU_SOUVERAINETE_FAUSSE")
    rows=d.get("comptes_par_annee")
    require(isinstance(rows,list) and [x.get("exercice") for x in rows]==list(YEARS),
       "MANQUE_ANNEES_FINANCES_SERVICES")
    pyear={x["exercice"]:x for x in p["annees_historique_et_previsions"]}
    tyear={x["exercice"]:x for x in t["annees"]}
    sopts={x["id"]:x for x in s["options"]}
    require(set(sopts)==set(OPTS) and set(YEARS).issubset(pyear) and
       set(YEARS).issubset(tyear),"DONNEES_FISCALES_SOURCE_INCOMPLETES")
    summary={}
    for i,r in enumerate(rows):
        fy=r["exercice"]
        budget=pyear[fy]
        portfolio=tyear[fy]
        expected={
          "revenus_consolides_publics_mcad":budget["total_revenus_mcad"],
          "depenses_portefeuilles_publics_mcad":budget["depenses_portefeuilles_mcad"],
          "service_dette_deja_compte_dans_total_mcad":budget["service_dette_deja_inclus_mcad"],
          "depenses_totales_hors_provision_mcad":budget["total_depenses_hors_provision_mcad"],
          "provision_eventualites_mcad":budget["provision_eventualites_mcad"],
          "fonds_generations_mcad":budget["fonds_generations_mcad"],
          "ecart_a_resorber_non_prouve_mcad":budget["ecart_a_resorber_non_finance_par_mesures_identifiees_mcad"],
          "solde_legal_avec_ecart_a_resorber_mcad":budget["solde_budgetaire_selon_loi_mcad"],
          "sous_total_sante_education_superieur_famille_inclus_portefeuilles_mcad":portfolio["noyau_sante_education_superieur_famille_mcad"],
          "sous_total_sept_portefeuilles_inclus_portefeuilles_mcad":portfolio["noyau_sept_services_sante_education_superieur_famille_transport_emploi_municipal_mcad"],
          "trois_categories_recettes_exposees_mcad":
           next(x for x in sopts["S3_CIBLE_DEUX_PRELEVEMENTS"]["resultats_par_exercice"] if x["exercice"]==fy)["exposition_officielle_trois_postes_mcad"].split(".")[0],
          "effort_budgetaire_minimum_estime_vgq_mcad":("2000" if i==0 else "3000")
        }
        for key,value in expected.items():
            require(decimal(r.get(key))==decimal(value),
                    "ECART_FINANCIER_"+fy+"_"+key)
        revenues=decimal(r["revenus_consolides_publics_mcad"])
        portfolios=decimal(r["depenses_portefeuilles_publics_mcad"])
        debt=decimal(r["service_dette_deja_compte_dans_total_mcad"])
        spend=decimal(r["depenses_totales_hors_provision_mcad"])
        contingency=decimal(r["provision_eventualites_mcad"])
        generation=decimal(r["fonds_generations_mcad"])
        gap=decimal(r["ecart_a_resorber_non_prouve_mcad"])
        original=decimal(r["solde_legal_avec_ecart_a_resorber_mcad"])
        require(portfolios+debt==spend and
                revenues-spend-contingency+gap-generation==original and
                decimal(r.get("solde_legal_sans_ecart_a_resorber_mcad"))==original-gap and
                decimal(r["sous_total_sante_education_superieur_famille_inclus_portefeuilles_mcad"])<=
                   decimal(r["sous_total_sept_portefeuilles_inclus_portefeuilles_mcad"])<=portfolios,
                "SOLDE_OU_DEPENSES_DOUBLE_COMPTEES_"+fy)
        require(r.get("origine")=="CADRE_FINANCIER_QUEBEC_DANS_CANADA_AOUT_2026" and
           r.get("unite")=="MILLIONS_CAD" and
           r.get("effort_vgq_indication")=="MINIMUM_ESTIME_BASE_EXISTANTE_PAS_COUT_ADDITIONNEL_NOVA" and
           all(r.get(x) is False for x in (
             "qualite_et_quantite_services_suffisantes_demonstrees",
             "effort_budgetaire_reconcilie_sur_chaque_programme")) and
           all(r.get(x) is None for x in (
             "cible_de_reduction_de_postes_nova",
             "economie_nova_certifiee_mcad",
             "contrepartie_financement_nova_certifiee_mcad",
             "budget_souverain_cette_annee")),
           "PRETENTIONS_DE_FINANCEMENT_CERTIFIE")
        options=r.get("options")
        require(isinstance(options,list) and len(options)==3 and
            [x.get("id") for x in options]==list(OPTS),"OPTIONS_ABSENTES")
        this_summary={}
        for option in options:
            code=option["id"]
            prior=next(x for x in sopts[code]["resultats_par_exercice"]
                       if x["exercice"]==fy)
            fraction=OPTS[code]
            loss=decimal(r["trois_categories_recettes_exposees_mcad"])*fraction/4
            expected_decimals={
              "retrait_recettes_fictif_mcad":loss,
              "revenus_publics_statiques_apres_retrait_mcad":revenues-loss,
              "solde_loi_sans_remplacement_avec_ecart_prevus_mcad":original-loss,
              "solde_loi_sans_remplacement_ni_resorption_mcad":original-loss-gap,
              "ressources_minimales_statiques_pour_revenir_au_solde_reference_mcad":loss,
              "ressources_minimales_statiques_pour_solde_loi_zero_sans_resorption_mcad":max(Decimal(0),loss-original+gap)
            }
            for key,val in expected_decimals.items():
                require(decimal(option.get(key),cents=True)==val,
                        "MANQUE_RESSOURCE_OPTION_"+code+"_"+fy+"_"+key)
            require(option.get("part_quart_trois_recettes")==fraction and
                decimal(option["retrait_recettes_fictif_mcad"],True)==
                    decimal(prior["recettes_retirees_uniquement_dans_le_test_mcad"],True) and
                decimal(option["solde_loi_sans_remplacement_ni_resorption_mcad"],True)==
                    decimal(prior["solde_loi_sans_nouveau_financement_et_sans_resorption_mcad"],True),
                "SOURCE_P56S_NON_RECONCILIEE")
            require(all(option.get(k) is None for k in (
              "montant_reel_prelevement_revenu_nova_mcad",
              "montant_reel_prelevement_anti_paradis_nova_mcad",
              "cout_reel_compensations_menages_nova_mcad",
              "economies_reelles_services_nova_mcad")) and
                option.get("qualite_services_nova_demonstree") is False and
                option.get("option_autorisee") is False,
                "SOLUTION_NON_CERTIFIEE_PRESENTEE_COMME_ADOPTEE")
            this_summary[code]={
                "perte_illustrative_recettes_mcad":str(loss),
                "solde_sans_financement_ni_resorption_mcad":str(original-loss-gap),
                "financement_additionnel_pour_solde_zero_sans_resorption_mcad":
                 str(max(Decimal(0),loss-original+gap))}
        summary[fy]={
            "depenses_portefeuilles_mcad":str(portfolios),
            "depenses_totales_hors_provision_mcad":str(spend),
            "quatre_portefeuilles_services_mcad":
              r["sous_total_sante_education_superieur_famille_inclus_portefeuilles_mcad"],
            "efforts_budgetaires_vgq_minimum_estime_mcad":
              r["effort_budgetaire_minimum_estime_vgq_mcad"],
            "ecart_a_resorber_mcad":str(gap),
            "options":this_summary}
    tasks=d.get("conditions_d_acception")
    require(isinstance(tasks,list) and len(tasks)==10 and
       {x.get("id") for x in tasks if isinstance(x,dict)}==
            {f"V{i:02d}" for i in range(1,11)} and
       all(len(x.get("description",""))>=65 and
           x.get("axe") in ("FISCALITE","SECTEURS","TRANSITION","EXPERTISE","ADOPTION") and
           x.get("statut")=="NON_DEMONTRE" and
           x.get("piece_justificative_id") is None and
           x.get("responsable_revue_externe") is None and
           x.get("validation_humaine_independante") is False and
           x.get("controle_qualite_requis") is True for x in tasks),
       "PREUVES_VGQ_ET_CONTINUITE_NON_CLOTUREES")
    indicators=d.get("indicateurs")
    must={
        "score_p55n_estime":53,"points_estimes_a_completer":47,
        "completude_ten_gates_p56o":0,
        "postes_financiers_p52b_a_renseigner":600,
        "incidences_fiscales_p52d_non_obtenues":720,
        "preuves_p52a_non_validees":20,
        "taux_nova_certifies":0,
        "budgets_nova_2027_2036_certifies":0,
        "montants_de_cout_supplementaire_nova_chiffres":0,
        "avis_externes_nova_signes":0,"main_modifie":False,
        "sinjira_modifie":False,"decision":"NO_GO_AUTOMATIQUE",
        "deux_taxes_nova_proposees_non_adoptees":True
    }
    require(isinstance(indicators,dict) and
       all(type(indicators.get(k)) is type(v) and indicators.get(k)==v
           for k,v in must.items()),"SCORE_OU_DECISION_SURDE_DECLARES")
    return {
      "jalon":"P56V","score_estime_pourcent":53,"points_restants_estimes":47,
      "annees_couvertes":list(YEARS),
      "financement":summary,
      "efforts_vgq_non_additionnes_aux_depenses":True,
      "aucune_garantie_de_services_automatiquement_etablie":True,
      "pertes_fictives_recettes_non_converties_en_taux_nova":True,
      "dix_conditions_documentaires_non_demontrees":10,
      "budget_souverain_certifie":False,
      "budget_nova_certifie":False,
      "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    for x in ("pont","p56p","p56s","p56t","p56o","barometre"):
        ap.add_argument("--"+x,type=Path,required=True)
    ap.add_argument("--rapport",type=Path)
    ap.add_argument("--certifier-financement-nova",action="store_true")
    a=ap.parse_args(argv)
    if a.certifier_financement_nova:
        print("REFUS: aucun financement ni audit independant Nova obtenu",file=sys.stderr)
        return 3
    try:
        def load(path):
            return json.loads(path.read_text(encoding="utf-8"))
        result=audit(load(a.pont),load(a.p56p),load(a.p56s),
                     load(a.p56t),load(a.p56o),load(a.barometre))
        serial=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as output:
                output.write(serial)
        else:
            print(serial,end="")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as e:
        print("REFUS: "+str(e),file=sys.stderr)
        return 2
if __name__=="__main__":
    sys.exit(main())
