#!/usr/bin/env python3
"""P56Z — concordance des crédits remboursables historiques et besoins de rendement.

Ce script refuse les faux reclassements comptables et toute addition des
9 305 M$ de crédits 2023 aux besoins du régime Nova en 2027.
Il ne mesure PAS une prestation nette ou un taux futur.
"""
from __future__ import annotations
import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

SCHEMA="P56Z-1"
ROOT="projets/projet-nova/etudes/"
PATHS={
"P56W":ROOT+"P56W_CREDITS_REMBOURSABLES_2023_PAR_CATEGORIE_ET_TRANCHES_PROTECTION.json",
"P56Y":ROOT+"P56Y_RENDEMENT_BRUT_NECESSAIRE_DEUX_PRELEVEMENTS_2027_2031.json",
"P56X":ROOT+"P56X_ASSIETTES_HISTORIQUES_ET_VERROU_TAUX_NOVA_2027_2028.json",
"P56O":ROOT+"P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
"P55N":ROOT+"P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"}
OFFICIAL={
"A14":("https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/somm-impot-a-payer.asp","A.14"),
"A15":("https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/somm-credit-remb.asp","A.15")}
DEFINITION="https://www.budget.finances.gouv.qc.ca/budget/outils/depenses-fiscales/metho-definition.asp"
CREDIT_KEYS={"FAMILLE","SOLIDARITE","SOUTIEN_AINES","GARDE","MAINTIEN_DOMICILE","PRIME_TRAVAIL"}
YEARS=("2027-2028","2028-2029","2029-2030","2030-2031")
NULL_FIELDS=(
"base_fiscale_2027_homogene_mcad",
"reconciliation_comptable_credits_actuels_avec_recettes_et_charges_mcad",
"cout_beneficiaires_credit_reel_mcad",
"cout_incidence_nouvelle_reforme_mcad",
"cout_compensations_incremental_net_mcad",
"rendement_net_nova_certifie_mcad")
PROTECT={
"ne_pas_additionner_9305_mcad_2023_aux_116663_mcad_2027",
"ne_pas_confondre_revenu_total_2023_et_assiette_2027",
"ne_pas_confondre_credit_non_remboursable_et_prestation_en_especes",
"ne_pas_abolir_prestation_pour_afficher_un_gain",
"ne_pas_supprimer_deux_fois_prestations_des_comptes",
"ne_pas_prendre_les_sensibilites_fiscales_pour_taux_adoptes",
"ne_pas_imaginer_une_economie_de_baisse_de_services",
"ne_pas_count_transfer_as_saving",
"ne_pas_prolonger_2023_en_2036",
"ne_pas_presumer_recettes_fiscales_souveraines",
"aucun_gagnant_perdant_menage_certifie"}
RULES={
"si_credit_actuel_est_deja_deduit_des_recettes":
  "NE_PAS_LE_DEDUIRE_ENCORE_DES_RECETTES_NOUVELLES_SANS RECONCILIATION",
"si_credit_actuel_est_deja_charge_de_transfert":
  "NE_PAS_LE_COMPTER_COMME_NOUVELLE_DEPENSE_UNE_SECONDE_FOIS",
"si_credit_est_reclasse_comme_prestation_sans_changement_droit":
  "NE_PAS_COMPTABILISER_LA_RECLASSIFICATION_COMME_ECONOMIE_OU_DEPENSE_NETTE_AUTOMATIQUE",
"si_prestation_est_augmentée":
  "IMPUTER_SEULEMENT_COUT_INCREMENTAL_NET_FONDE_SUR_ASSIETTES_ET_BENEFICIAIRES_VALIDES"
}
def require(condition,problem):
    if not condition:
        raise ValueError(problem)
def cad(v):
    require(type(v) is str and v.isascii() and v.isdecimal() and
        (v=="0" or (not v.startswith("0") and len(v)<=9)),
        "ENTIER_M_CAD_OBLIGATOIRE")
    return Decimal(v)
def cad_signed(v):
    if isinstance(v,str) and v.startswith("-"):
        return -cad(v[1:])
    return cad(v)

def audit(d,w,y,x,o,b):
    require(isinstance(d,dict) and d.get("schema_version")==SCHEMA and
      d.get("date_revision")=="2026-11-08" and
      d.get("objet")=="VERROU_ANTI_DOUBLE_COMPTE_CREDITS_REMBOURSABLES_HISTORIQUES_ET_CIBLES_DEUX_TAXES" and
      d.get("statut")=="CONCORDANCE_DOCUMENTAIRE_DIFFERENTS_EXERCICES_NON_BUDGET_NOVA" and
      d.get("decision")=="NO_GO_AUTOMATIQUE","REGISTRE_Z_NON_CONFORME")
    sources=d.get("sources")
    require(isinstance(sources,dict) and all(sources.get(k)==v for k,v in PATHS.items()),
       "SOURCES_DE_DEPENDANCES_MODIFIEES")
    for k,(url,t) in OFFICIAL.items():
        require(sources.get(k,{}).get("url")==url and
           sources[k].get("annee")==2023 and
           sources[k].get("tableau")==t and
           sources[k].get("statut")=="DONNEES_OFFICIELLES_HISTORIQUES",
           "SOURCE_FISCALE_NON_OFFICIELLE_"+k)
    require(sources.get("DEFINITION",{}).get("url")==DEFINITION and
        sources["DEFINITION"].get("ne_definit_pas_reclassement_comptes_nova") is True,
        "METHODOLOGIE_NON_CONFORME")
    require(w.get("schema_version")=="P56W-1" and
        y.get("schema_version")=="P56Y-1" and
        x.get("schema_version")=="P56X-1" and
        o.get("schema_version")=="P56O-1" and
        b.get("schema_version")=="P55N-1" and
        all(g.get("decision")=="NO_GO_AUTOMATIQUE" for g in (w,y,x,o)),
        "DEPOT_PROVENANCE_NON_COMPATIBLE")
    tax=d.get("exercice_observation")
    hist=x.get("donnees_historiques",{}).get("personnes_2023",{})
    require(isinstance(tax,dict) and tax.get("annee")==2023 and
        tax.get("unite")=="MILLIONS_CAD" and
        tax.get("population")=="DECLARANTS_QUEBECOIS_NON_MENAGES" and
        tax.get("ce_solde_est_un_indicateur_statistique_non_recette_comptable_consolidee") is True and
        tax.get("revenu_total_n_est_pas_assiette_imposable") is True and
        tax.get("crédits_non_remboursables_et_remboursables_non_interchangeables") is True,
        "ANNEE_OU_POPULATION_STATISTIQUE_MODIFIEE")
    require(cad(tax.get("revenu_total_declarants_mcad"))==427915 and
        cad(tax.get("impot_sur_revenu_imposable_avant_credits_non_remboursables_mcad"))==62148 and
        cad(tax.get("credits_non_remboursables_mcad"))==21358 and
        cad(tax.get("impot_a_payer_apres_non_remboursables_mcad"))==40790 and
        cad(tax.get("credits_remboursables_mcad"))==9305 and
        cad(tax.get("impot_a_payer_moins_credits_remboursables_arithmetique_mcad"))==31485 and
        cad(tax["impot_sur_revenu_imposable_avant_credits_non_remboursables_mcad"])-
        cad(tax["credits_non_remboursables_mcad"])==
        cad(tax["impot_a_payer_apres_non_remboursables_mcad"]) and
        cad(tax["impot_a_payer_apres_non_remboursables_mcad"])-
        cad(tax["credits_remboursables_mcad"])==
        cad(tax["impot_a_payer_moins_credits_remboursables_arithmetique_mcad"]) and
        cad(tax["revenu_total_declarants_mcad"])==
        cad(hist["revenu_total_mcad"]) and
        cad(tax["impot_a_payer_apres_non_remboursables_mcad"])==
        cad(hist["impot_a_payer_mcad"]) and
        cad(tax["credits_remboursables_mcad"])==
        cad(hist["credits_remboursables_mcad"]) and
        cad(tax["impot_a_payer_moins_credits_remboursables_arithmetique_mcad"])==
        cad(hist["net_apres_credits_remboursables_mcad"]),
        "STATISTIQUES_A14_OU_A17_NON_RECONCILIEES")
    cr=d.get("credits_remboursables_2023")
    source_cr=w.get("controle_arrondis",{})
    require(isinstance(cr,dict) and
        cad(cr.get("total_officiel_mcad"))==9305 and
        cad(cr.get("somme_categories_arrondies_mcad"))==9306 and
        cad_signed(cr.get("ecart_arrondi_categories_moins_total_mcad"))==1 and
        cad(cr.get("somme_tranches_arrondies_mcad"))==9304 and
        cad_signed(cr.get("ecart_arrondi_tranches_moins_total_mcad"))==-1 and
        cad(source_cr["ligne_totale_officielle_mcad"])==9305 and
        cad(source_cr["somme_totaux_par_categorie_publies_mcad"])==9306 and
        cad(source_cr["somme_credits_total_officielle_par_tranche_mcad"])==9304 and
        cr.get("montants_2023_non_projetés_comme_prestations_2027") is True and
        cr.get("zero_publie_peut_signifier_moins_de_0_5_mcad") is True and
        cr.get("ecarts_arrondis_non_corriges_artificiellement") is True,
        "CREDITS_2023_OU_ARRONDIS_MODIFIES")
    items=cr.get("categories_extraites_pertinentes")
    require(isinstance(items,list) and len(items)==6 and
        {r.get("id") for r in items if isinstance(r,dict)}==CREDIT_KEYS,
        "SIX_CREDITS_A_PROTEGER_INCOMPLETS")
    existing={r["id"]:r for r in w["credits_par_categorie"]}
    for r in items:
        key=r["id"]
        require(cad(r.get("total_mcad"))==cad(existing[key]["total_publie_mcad"]) and
            r.get("annee")==2023 and
            isinstance(r.get("intitule"),str) and len(r["intitule"])>=12 and
            r.get("remboursement_reel_nova_2027_mcad") is None and
            r.get("maintien_droit_apres_reforme_non_demontre") is True,
            "PRESTATION_NON_RECONCILIEE_"+key)
    low=cr.get("moins_30000_cad")
    original=w.get("menages_plus_vulnerables_observations_a14",{})
    require(isinstance(low,dict) and
        low.get("tranches")==original.get("groupe_six_tranches") and
        low.get("montants_arrondis_mcad")==["777","1118","2306"] and
        sum(cad(z) for z in low["montants_arrondis_mcad"])==4201 and
        cad(low.get("somme_mcad"))==cad(original["credits_remboursables_tous_types_mcad"])==4201 and
        cad(low.get("impot_a_payer_mcad"))==cad(original["impot_a_payer_mcad"])==285 and
        cad_signed(low.get("impot_apres_credits_indicateur_arithmetique_mcad"))==-3916 and
        low.get("population_menages_vivants_representatifs") is False and
        low.get("montant_compensation_nova_2027_mcad") is None,
        "TRANCHES_MODESTES_NON_RECONCILIEES")
    lines=d.get("rapprochement_decennal_amorce")
    require(isinstance(lines,list) and
        [r.get("exercice") for r in lines]==list(YEARS) and
        [r.get("exercice") for r in y.get("annees",[])]==list(YEARS),
        "MILLESMES_2027_2031_INCOMPATIBLES")
    for r,s in zip(lines,y["annees"]):
        for here,there in (
          ("remplacement_total_recettes_existantes_mcad",
            "recettes_total_a_substituer_si_deux_nouveaux_piliers_mcad"),
          ("rendement_conditionnel_pour_solde_zero_avec_resorption_mcad",
            "rendement_nouveaux_piliers_pour_solde_zero_avec_resorption_mcad"),
          ("rendement_conditionnel_pour_solde_zero_sans_resorption_mcad",
            "rendement_nouveaux_piliers_pour_solde_zero_sans_resorption_mcad")):
            require(cad(r.get(here))==cad(s[there]),
                   "OBJECTIF_RENDEMENT_NOVA_NON_RECONCILIE_"+here)
        require(all(r.get(k) is None for k in NULL_FIELDS) and
                r.get("aucun_9305_historique_ajoute_aux_cibles") is True and
                r.get("solde_final_nova_certifie") is False,
                "PRESTATIONS_2023_AJOUTEES_DEUX_FOIS_EN_2027")
    policies=d.get("conventions_reclassement")
    require(isinstance(policies,dict) and
        policies.get("regle_formelle")==
         "INCREMENT_DE_COUT_A_JOUTER_SEULEMENT_SI_MESURE_NOUVELLE_NON_DEJA_COMPRISE_DANS_ASSIETTE_FISCALE_OU_DEPENSES_DE_REFERENCE" and
        all(policies.get(k)==v for k,v in RULES.items()) and
        policies.get("regime_actuel_comptabilisation_exacte_2027_connue") is False and
        policies.get("reclassification_2027_faite") is False and
        policies.get("economies_comptables_identifiees_mcad") is None and
        policies.get("cout_protection_2027_2036_certifie_mcad") is None,
        "CREDITS_TRANSFERTS_COMPTES_DEUX_FOIS")
    jurisdictions=d.get("juridictions")
    require(isinstance(jurisdictions,dict) and
        set(jurisdictions)=={"QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN"} and
        jurisdictions["QUEBEC_DANS_CANADA"].get("mesures_federales_non_modifiables_unilateralement") is True and
        jurisdictions["QUEBEC_DANS_CANADA"].get("droits_credits_provinciaux_a_verifier") is True and
        jurisdictions["QUEBEC_DANS_CANADA"].get("financement_services_non_reduit_par_hypothese") is True and
        jurisdictions["QUEBEC_SOUVERAIN"].get("transferts_federaux_continues_presumes") is False and
        jurisdictions["QUEBEC_SOUVERAIN"].get("reclassification_fiscale_validée") is False and
        jurisdictions["QUEBEC_SOUVERAIN"].get("budget_different_exige") is True,
        "SOUVERAINETE_OU_COMPETENCES_CONFONDUES")
    protect=d.get("garde_fous")
    require(isinstance(protect,dict) and set(protect)==PROTECT and
        all(protect[k] is True for k in PROTECT),
        "VERROU_ANTI_DOUBLE_COMPTE_DESACTIVE")
    gates=d.get("portes")
    require(isinstance(gates,list) and len(gates)==10 and
        {g.get("id") for g in gates if isinstance(g,dict)}==
        {f"Z{i:02d}" for i in range(1,11)} and
        all(g.get("statut")=="NON_DEMONTRE" and
          g.get("preuve_documentaire") is None and
          g.get("avis_independant_signe") is False and
          len(g.get("exigence",""))>=65 for g in gates),
        "PORTES_DE_PREUVE_FALSIFIEES")
    completion=d.get("completude")
    require(isinstance(completion,dict) and
        completion.get("score_p55n")==b.get("score_estimatif")==53 and
        completion.get("points_restants")==47 and
        completion.get("portes_p56o_demontrees")==0 and
        completion.get("p52b_montants_inconnus")==600 and
        completion.get("p52d_incidences_inconnues")==720 and
        completion.get("p52a_preuves_non_validees")==20 and
        completion.get("avis_experts_signes")==0 and
        completion.get("donnees_2027_menages_validees")==0 and
        completion.get("reforme_fiscale_adoptee") is False and
        completion.get("decision")=="NO_GO_AUTOMATIQUE" and
        o.get("definition_terminee",{}).get("etat_actuel_termine") is False,
        "FAUSSE_COMPLETUDE")
    return {
      "jalon":"P56Z",
      "donnees_historiques_2023":"OBSERVATIONS_DECLARANTS_NON_MENAGES",
      "impot_2023_avant_credits_non_remboursables_mcad":"62148",
      "credits_non_remboursables_2023_mcad":"21358",
      "impot_2023_apres_non_remboursables_mcad":"40790",
      "credits_remboursables_2023_mcad":"9305",
      "indicateur_arithmetique_apres_credits_mcad":"31485",
      "credit_tranches_moins_30000_cad_mcad":"4201",
      "credits_arrondis_somme_categories_mcad":"9306",
      "credits_arrondis_somme_tranches_mcad":"9304",
      "besoin_rendement_2027_2028_sans_resorption_mcad":
        lines[0]["rendement_conditionnel_pour_solde_zero_sans_resorption_mcad"],
      "credits_2023_supposes_cout_additionnel_en_2027":False,
      "couverture_menages_protection_2027_demontree":False,
      "reclassement_credits_2027_certifie":False,
      "cibles_de_rendement_2027_2031":
        {r["exercice"]:r["rendement_conditionnel_pour_solde_zero_sans_resorption_mcad"] for r in lines},
      "previsions_nova_validees":False,
      "portes_non_demontrees":len(gates),
      "score_estime_p55n":53,
      "points_restants":47,
      "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("concordance","p56w","p56y","p56x","p56o","barometre"):
        parser.add_argument("--"+key,type=Path,required=True)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--exiger-protection-certifiee",action="store_true")
    args=parser.parse_args(argv)
    if args.exiger_protection_certifiee:
        print("NO_GO : les prestations 2027 et la concordance comptable ne sont pas établies",file=sys.stderr)
        return 3
    try:
        def read(path):
            return json.loads(path.read_text(encoding="utf-8"))
        result=audit(read(args.concordance),read(args.p56w),read(args.p56y),
                     read(args.p56x),read(args.p56o),read(args.barometre))
        output=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if args.rapport:
            with args.rapport.open("x",encoding="utf-8") as f:
                f.write(output)
        else:
            print(output,end="")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as e:
        print("REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
