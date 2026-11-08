#!/usr/bin/env python3
"""P56X : verrou de preuve pour un taux Nova, pas une proposition de taux.

Rapproche les bases fiscales historiques observees (particuliers 2023,
societes 2021), recettes gouvernementales 2027-2028, couts des services
et credits 2023. Interdit d'additionner les deux assiettes de millesimes
differents ou de transposer leurs ratios en taux Nova 2027-2028.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import re
import sys

FILES={
"P56K":"projets/projet-nova/etudes/P56K_ASSIETTES_PARTICULIERS_SOCIETES_CREDITS_SOURCES_OFFICIELLES.json",
"P56R":"projets/projet-nova/etudes/P56R_INVENTAIRE_EXHAUSTIF_CATEGORIES_RECETTES_ET_PONT_FISCAL_2026_2031.json",
"P56V":"projets/projet-nova/etudes/P56V_PONT_FINANCEMENT_SERVICES_OPTIONS_FISCALES_VGQ_2027_2029.json",
"P56W":"projets/projet-nova/etudes/P56W_CREDITS_REMBOURSABLES_2023_PAR_CATEGORIE_ET_TRANCHES_PROTECTION.json",
"P56O":"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
"P55N":"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"}
A17="https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/somm-evo-historique.asp"
CORP="https://www.quebec.ca/gouvernement/finances-publiques/revenus/donnees-fiscales/statistiques-fiscales-societes"
DEC=re.compile(r"(?:0|[1-9][0-9]{0,12})\Z")
NULL_KEYS=(
"assiette_personnes_imposable_2027_2028_mcad",
"assiette_societes_imposable_2027_2028_mcad",
"assiette_anti_paradis_legale_2027_2028_mcad",
"rendement_antiparadis_net_additionnel_2027_2028_mcad",
"taux_personnes_candidat_pourcent",
"taux_societes_candidat_pourcent",
"deciles_cout_menages_2027_2028",
"couts_credits_remboursables_2027_2028_mcad",
"cout_maintien_integral_services_2027_2028_mcad",
"cout_transition_salaries_PME_2027_2028_mcad",
"avis_juridique_fiscal_independant_signe",
"avis_comptable_independant_signe")
RULES=(
"pas_de_taux_nova_par_division_du_besoin_2027_par_des_recettes_publiques",
"pas_de_taux_nova_par_division_2027_sur_assiette_particuliers_2023",
"pas_de_taux_nova_sur_assiette_societes_2021",
"pas_addition_assiettes_2023_2021",
"ne_pas_compter_credits_remboursables_2023_comme_recettes_2027",
"ne_pas_compter_activites_antifraude_actuelles_comme_revenu_anti_paradis_nouveau",
"pas_de_taux_nova_universel_presume_sans_progressivite_et_incidences",
"aucun_impot_federal_supprime_par_loi_provinciale",
"aucune_economie_sante_ecoles_municipalites_automatique",
"aucune_suppression_effectifs_presumee",
"ne_pas_compter_efforts_VGQ_comme_ressources_supplementaires",
"ne_pas_presumer_du_revenu_souverain_sans_depenses_federales",
"aucune_recette_nova_certifiee")

def demand(test,reason):
    if not test:
        raise ValueError(reason)
def num(v):
    demand(type(v) is str and DEC.fullmatch(v) is not None,
           "MONTANT_EXIGE_ENTIER_POSITIF_MCAD")
    return Decimal(v)
def ratio(a,b):
    demand(b>0,"ASSIETTE_NULLE")
    return str((a*100/b).quantize(Decimal(".01"),rounding=ROUND_HALF_UP))

def audit(x,k,r,v,w,o,b):
    demand(isinstance(x,dict) and x.get("schema_version")=="P56X-1" and
           x.get("date_revision")=="2026-11-08" and
           x.get("statut")=="ASSIETTES_HISTORIQUES_HETEROGENES_NON_MODELISATION_FISCALE_NOVA" and
           x.get("decision")=="NO_GO_AUTOMATIQUE",
           "P56X_FAUSSE_CERTIFICATION")
    demand(all(isinstance(a,dict) for a in (k,r,v,w,o,b)) and
           k.get("schema_version")=="P56K-1" and
           k.get("decision")=="NO_GO_AUTOMATIQUE" and
           r.get("schema_version")=="P56R-1" and
           r.get("decision")=="NO_GO_AUTOMATIQUE" and
           v.get("schema_version")=="P56V-1" and
           v.get("decision")=="NO_GO_AUTOMATIQUE" and
           w.get("schema_version")=="P56W-1" and
           w.get("decision")=="NO_GO_AUTOMATIQUE" and
           o.get("schema_version")=="P56O-1" and
           o.get("definition_terminee",{}).get("etat_actuel_termine") is False and
           b.get("schema_version")=="P55N-1" and
           b.get("score_estimatif")==53,
           "DEPENDANCES_NON_VERIFIEES")
    sources=x.get("sources")
    demand(isinstance(sources,dict) and
           all(sources.get(name)==path for name,path in FILES.items()) and
           sources.get("officiel_a17",{}).get("url")==A17 and
           sources["officiel_a17"].get("date_donnee")==2023 and
           sources["officiel_a17"].get("tableau")=="A.17" and
           sources["officiel_a17"].get("verifie_sur_page_officielle") is True and
           sources.get("officiel_societes",{}).get("url")==CORP and
           sources["officiel_societes"].get("date_donnee")==2021 and
           sources["officiel_societes"].get("verifie_par_reference_p56k") is True,
           "SOURCES_OU_MILLESIMES_NON_CONCORDANTS")
    data=x.get("donnees_historiques")
    demand(isinstance(data,dict),"MANQUE_BLOC_HISTORIQUE")
    pit=data.get("personnes_2023")
    corp=data.get("societes_2021")
    demand(isinstance(pit,dict) and isinstance(corp,dict),
           "BASES_FISCALES_HISTORIQUES_ABSENTES")
    refpit=k["particuliers_2023"]
    refcorp=k["societes_2021"]
    historical={
       "revenu_total_mcad":refpit["revenu_total_mcad"],
       "revenu_imposable_mcad":refpit["revenu_imposable_mcad"],
       "impot_a_payer_mcad":refpit["impot_a_payer_mcad"],
       "credits_remboursables_mcad":refpit["credits_remboursables_mcad"],
       "net_apres_credits_remboursables_mcad":
         refpit["impot_a_payer_net_credits_remboursables_mcad"]}
    for key,source in historical.items():
        demand(num(pit.get(key))==num(source),"IMPOT_PERSONNES_2023_"+key)
    taxable=num(pit["revenu_imposable_mcad"])
    total=num(pit["revenu_total_mcad"])
    tax=num(pit["impot_a_payer_mcad"])
    credits=num(pit["credits_remboursables_mcad"])
    demand(tax-credits==num(pit["net_apres_credits_remboursables_mcad"]) and
           pit.get("ratio_observe_impot_a_payer_sur_revenu_total_pourcent")==ratio(tax,total)=="9.53" and
           pit.get("ratio_observe_impot_a_payer_sur_revenu_imposable_pourcent")==ratio(tax,taxable)=="10.96" and
           pit.get("taux_moyen_officiel_a17_arrondi_pourcent")=="9.5" and
           pit.get("difference_entre_les_deux_denominateurs_essentielle") is True and
           pit.get("ratio_historique_n_est_pas_taux_nova") is True,
           "TAUX_MOYEN_HISTORIQUE_DISTORDU")
    fiscal={
        "revenu_imposable_quebec_mcad":refcorp["revenu_imposable_quebec_mcad"],
        "impot_revenu_societes_mcad":refcorp["impot_revenu_societes_mcad"],
        "cotisations_fss_societes_mcad":refcorp["cotisations_fss_societes_mcad"],
        "credits_impot_societes_mcad":refcorp["credits_impot_societes_mcad"]}
    for key,source in fiscal.items():
        demand(num(corp.get(key))==num(source),"SOCIETES_2021_"+key)
    demand(corp.get("ratio_observe_impot_revenu_societes_sur_revenu_imposable_pourcent")==
           ratio(num(corp["impot_revenu_societes_mcad"]),num(corp["revenu_imposable_quebec_mcad"]))=="10.44" and
           corp.get("ratio_historique_n_est_pas_taux_nova") is True and
           corp.get("credits_et_fss_ne_sont_pas_un_impot_proportionnel_sur_benefice") is True and
           data.get("millesimes_comparables") is False and
           data.get("assiettes_personnes_et_societes_agregees_mcad") is None and
           data.get("assiettes_legales_2027_2028_validees") is False and
           data.get("assiettes_souveraines_2027_2028_validees") is False,
           "ASSIETTES_D_ANNEES_INCOMPATIBLES_FUSIONNEES")
    need=x.get("repere_2027_2028")
    y=next(a for a in r["rapprochement_annees"] if a["exercice"]=="2027-2028")
    z=next(a for a in v["comptes_par_annee"] if a["exercice"]=="2027-2028")
    s3=next(a for a in z["options"] if a["id"]=="S3_CIBLE_DEUX_PRELEVEMENTS")
    demand(isinstance(need,dict),"COUT_FINANCEMENT_ABSENT")
    numbers={
      "revenus_officiels_totaux_mcad":num(z["revenus_consolides_publics_mcad"]),
      "impot_particuliers_existant_mcad":Decimal(52841),
      "impot_societes_existant_mcad":Decimal(15252),
      "impots_revenu_existants_mcad":num(y["impots_sur_revenu_actuels_mcad"]),
      "trois_recettes_exposees_si_abrogation_mcad":num(y["trois_categories_a_remplacer_si_supprimees_mcad"]),
      "solde_legal_gouvernemental_avant_reforme_mcad":Decimal(-5695),
      "besoin_remplacement_pour_conserver_solde_de_reference_mcad":Decimal(42875),
      "besoin_financement_arithmetique_pour_solde_legal_zero_si_retrait_integral_mcad":Decimal(48570)
    }
    demand(numbers["impots_revenu_existants_mcad"]==
           numbers["impot_particuliers_existant_mcad"]+numbers["impot_societes_existant_mcad"] and
           numbers["impots_revenu_existants_mcad"]==Decimal(68093) and
           numbers["trois_recettes_exposees_si_abrogation_mcad"]==Decimal(42875) and
           num(z["solde_legal_avec_ecart_a_resorber_mcad"])==Decimal(-5695) and
           Decimal(s3["retrait_recettes_fictif_mcad"])==Decimal(42875) and
           Decimal(s3["ressources_minimales_statiques_pour_solde_loi_zero_sans_resorption_mcad"])==Decimal(48570),
           "COUTS_2027_NON_RECONCILIES")
    for key,amount in numbers.items():
        if key=="solde_legal_gouvernemental_avant_reforme_mcad":
            demand(need.get(key)==str(amount),"SOLDE_LEGAL_INVALIDE")
        else:
            demand(num(need.get(key))==amount,"RECETTE_OU_BESOIN_NON_RECONCILIE_"+key)
    demand(need.get("ratio_recettes_a_remplacer_sur_recettes_impots_actuels_pourcent")==
           ratio(Decimal(42875),Decimal(68093))=="62.97" and
           need.get("ratio_62_97_ne_constitue_pas_un_taux_de_taxation") is True and
           need.get("besoin_chiffre_pour_regime_québec_souverain") is None,
           "TAUX_NOVA_DEDUIT_DE_RECETTES_PUBLIQUES")
    demand(num(w["controle_arrondis"]["ligne_totale_officielle_mcad"])==num(pit["credits_remboursables_mcad"]),
           "CREDITS_2023_COHERENCE_P56W")
    demand(isinstance(x.get("regles"),dict) and
           set(x["regles"])==set(RULES) and
           all(x["regles"].get(k) is True for k in RULES),
           "REGLES_CONSTITUTIONNELLES_OU_FISCALES_BRISEES")
    scopes=x.get("etude_taux_candidat_bloquee")
    demand(isinstance(scopes,dict) and
           set(scopes)=={"QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN"},
           "DEUX_REGIMES_NON_SEPARES")
    for name,scope in scopes.items():
        demand(isinstance(scope,dict) and
               all(scope.get(k) is None for k in NULL_KEYS) and
               scope.get("politique_fiscale_nova_validee") is False,
               "ASSIETTES_2027_OU_TAUX_FICTIFS_"+name)
    sovereign=scopes["QUEBEC_SOUVERAIN"]
    demand(all(sovereign.get(k) is None for k in (
      "revenus_competences_federales_nets_mcad","depenses_nouvelles_competences_mcad",
      "pensions_dette_actifs_de_transition_mcad")) and
      sovereign.get("transferts_federaux_mis_a_zero_ou_maintenus_automatiquement") is False,
      "RECETTES_FEDERALES_GRATUITES")
    tasks=x.get("preuves_prioritaires")
    demand(isinstance(tasks,list) and len(tasks)==8 and
           {t.get("id") for t in tasks}=={f"X{i:02d}" for i in range(1,9)} and
           all(t.get("statut")=="NON_OBTENU" and
               t.get("piece") is None and
               len(t.get("necessaire",""))>=78 for t in tasks),
           "PREUVES_FISCALES_NON_OBTENUES_DECLAREES_RECUES")
    status=x.get("completude")
    truth={
      "score_p55n_estime":53,"points_restants":47,"portes_cloture_demontrees":0,
      "p52b_montants_manquants":600,"p52d_incidences_non_mesurees":720,
      "p52a_preuves_non_validees":20,"taux_fiscaux_nova_adoptes":0,
      "avis_independants_signes":0,"programme_termine":False,
      "decision":"NO_GO_AUTOMATIQUE"}
    demand(isinstance(status,dict) and all(
           type(status.get(key)) is type(value) and status.get(key)==value
           for key,value in truth.items()),"BAROMETRE_ARTIFICIELLEMENT_MODIFIE")
    return {
      "jalon":"P56X","personnes_2023_assiette_imposable_mcad":str(taxable),
      "societes_2021_assiette_imposable_mcad":str(num(corp["revenu_imposable_quebec_mcad"])),
      "personnes_2023_taux_observe_revenu_total_pourcent":"9.53",
      "personnes_2023_taux_observe_revenu_imposable_pourcent":"10.96",
      "societes_2021_ratio_observe_pourcent":"10.44",
      "recettes_reference_2027_revenu_mcad":"68093",
      "recettes_a_remplacer_scenario_integral_mcad":"42875",
      "financement_statique_equilibre_2027_mcad":"48570",
      "taux_2027_nova_certifie":False,
      "assiettes_2027_nova_connues":False,
      "comparabilite_assiettes_historique":False,
      "deux_regimes_budgetises":False,
      "score_estime_pourcent":53,"points_restants_estimes":47,
      "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__)
    for name in ("assiettes","p56k","p56r","p56v","p56w","p56o","barometre"):
        a.add_argument("--"+name,required=True,type=Path)
    a.add_argument("--rapport",type=Path)
    a.add_argument("--publier-taux-nova",action="store_true")
    opts=a.parse_args(argv)
    if opts.publier_taux_nova:
        print("REFUS: bases 2027 et avis indépendants non obtenus",file=sys.stderr)
        return 3
    try:
        def rd(p):
            return json.loads(p.read_text(encoding="utf-8"))
        out=audit(*[rd(getattr(opts,k)) for k in (
            "assiettes","p56k","p56r","p56v","p56w","p56o","barometre")])
        serial=json.dumps(out,ensure_ascii=False,indent=2)+"\n"
        if opts.rapport:
            with opts.rapport.open("x",encoding="utf-8") as f:
                f.write(serial)
        else:
            print(serial,end="")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
