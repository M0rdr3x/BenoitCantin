#!/usr/bin/env python3
"""P56P — contrôler le cadre financier québécois publié en août 2026.

Provenance : Rapport préélectoral 2026, tableau 2, PDF page index 19;
rapport trimestriel du 25-09-2026, PDF page index 2.
Ne constitue PAS une simulation du Projet Nova ni un budget souverain.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys

YEARS=("2025-2026","2026-2027","2027-2028","2028-2029","2029-2030","2030-2031")
FIELDS={
"impot_particuliers":(48969,50942,52841,54861,56867,59006),
"cotisations_services_sante":(9304,9538,9876,10327,10628,10962),
"impots_societes":(14599,14698,15252,15240,15835,16875),
"impot_foncier_scolaire":(1243,1301,1367,1426,1479,1531),
"taxes_consommation":(29639,30682,31632,32416,33206,34035),
"droits_permis_redevances":(6708,6484,6928,7278,7586,7823),
"revenus_divers":(14922,15790,16110,16744,17385,17988),
"entreprises_gouvernement":(5241,5908,6208,6909,6653,7035)
}
METRICS={
"revenus_autonomes_mcad":(130625,135343,140214,145201,149639,155255),
"transferts_federaux_mcad":(29803,33046,34011,33643,32802,33757),
"total_revenus_mcad":(160428,168389,174225,178844,182441,189012),
"depenses_portefeuilles_mcad":(155782,161081,165049,166666,168291,173584),
"service_dette_deja_inclus_mcad":(10148,10516,10870,11402,11860,12749),
"total_depenses_hors_provision_mcad":(165930,171597,175919,178068,180151,186333),
"provision_eventualites_mcad":(0,2000,1500,1500,1500,1500),
"solde_comptable_avant_ecart_resorber_mcad":(-5502,-5208,-3194,-724,790,1179),
"ecart_a_resorber_non_finance_par_mesures_identifiees_mcad":(0,0,0,1850,2000,2000),
"fonds_generations_mcad":(2289,2482,2501,2626,2790,2929),
"solde_budgetaire_selon_loi_mcad":(-7791,-7690,-5695,-1500,0,250)
}
SOURCE={
"RAPPORT_PREELECTORAL":(
 "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf",
 "2026-08-17"),
"RAPPORT_TRIMESTRIEL":(
 "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/rapport/TRIMFR_SIFIN_1T_26-27.pdf",
 "2026-09-25"),
"EXAMEN_VGQ":("https://www.vgq.qc.ca/fr/communique/C2026-3","2026-08-17"),
"OUTIL_SIMULATION_AMENDE":(
 "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/RPE2026_simulateur_amende.xlsx",
 "2026-09-03")
}
AUDIT_FLAGS={
"annees_2025_2026_auditees":True,
"annees_2026_2027_a_2028_2029_vgq_plausibilite_non_garantie":True,
"annees_2029_2030_et_2030_2031_non_couvertes_par_l_examen_vgq":True,
"exercices_2031_2032_a_2036_2037_non_documentes_par_ce_rapport":True,
"prelevements_societes_personnes_neo_tax_nova_non_modelises":True,
"fonctions_federales_souverainete_non_projetees":True,
"provisions_eventualites_ne_sont_pas_depenses_services_ajoutees_deux_fois":True,
"fonds_generations_ne_fait_pas_partie_des_depenses_portefeuilles":True,
"service_dette_deja_inclus_dans_total_depenses":True,
"revenus_federaux_non_conserves_par_defaut_en_souverainete":True,
"mesures_fiscales_annoncees_apres_publication_a_reconcilier":True,
"rapport_budgetaire_n_est_pas_engagement_financier_nova":True
}
RISKS={
"RISQUE_PIB_NOMINAL":("impact_revenus_autonomes_annuel_mcad","-1200"),
"RISQUE_POPULATION":("impact_depenses_portefeuilles_annuel_mcad","1270"),
"RISQUE_PRIX":("impact_depenses_portefeuilles_annuel_mcad","760"),
"RISQUE_INTERETS":("impact_service_dette_annuel_mcad","640"),
"RISQUE_TRANSFERTS_POP":("impact_transferts_federaux_annuel_mcad","-255")
}
PATHS={
"barometre_p55n":"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json",
"p52b":"projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json",
"p56o":"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json"
}

def ensure(cond,message):
    if not cond:
        raise ValueError(message)

def integer(v):
    ensure(type(v) is str and len(v)<=10 and
           (v=="0" or (v.isdecimal() and not v.startswith("0")) or
            (v.startswith("-") and len(v)>1 and v[1:].isdecimal()
             and v[1]!="0")), "MONTANT_ENTIER_MCAD_INVALIDE")
    try:
        return Decimal(v)
    except InvalidOperation as error:
        raise ValueError("MONTANT_NON_DECIMAL") from error

def assess(base,model,bar,finish):
    ensure(isinstance(base,dict) and base.get("schema_version")=="P56P-1" and
           base.get("date_revision")=="2026-11-08" and
           base.get("objet")=="POINT_DE_DEPART_BUDGETAIRE_OFFICIEL_PLUS_RECENT_POUR_COMPARAISONS_NOVA_2027_2031" and
           base.get("statut")=="BASE_PUBLIQUE_PREVISIONS_GOUVERNEMENT_AOUT_2026_PAS_BUDGET_NOVA" and
           base.get("decision")=="NO_GO_AUTOMATIQUE" and
           base.get("unite")=="M_CAD" and
           base.get("origine")=="QUEBEC_DANS_CANADA",
           "SOURCE_BUDGETAIRE_NON_AUTORISEE")
    sources=base.get("sources")
    ensure(isinstance(sources,dict) and set(sources)==set(SOURCE),
           "SOURCES_OFFICIELLES_NON_EXHAUSTIVES")
    for key,(uri,dat) in SOURCE.items():
        row=sources[key]
        datekey="date_amendement" if key=="OUTIL_SIMULATION_AMENDE" else "date_publication"
        ensure(row.get("url")==uri and row.get(datekey)==dat,
               "SOURCE_DATE_OU_URL_INCORRECTE_"+key)
    report=sources["RAPPORT_PREELECTORAL"]
    ensure(report.get("tableau")=="TABLEAU_2_CADRE_FINANCIER_2025_2026_A_2030_2031" and
           report.get("page_pdf_indice_zero")==19 and
           report.get("page_imprimee")==17 and
           report.get("autres_pages_pdf_indices_zero")==[9,45] and
           report.get("octets_source_cryptographiquement_authentifies") is False,
           "TRACE_TABLEAU_PDF_MANQUANTE")
    quarter=sources["RAPPORT_TRIMESTRIEL"]
    ensure(quarter.get("page_pdf_indice_zero")==2 and
           quarter.get("donnees_trimestrielles_non_auditees") is True and
           quarter.get("meme_prevision_annuelle_2026_2027_que_rapport_aout") is True,
           "TRIMESTRE_NE_RECONCILIE_PAS")
    vgq=sources["EXAMEN_VGQ"]
    ensure(vgq.get("portee_annees")==list(YEARS[1:4]) and
           vgq.get("date_plausibilite")=="2026-07-10" and
           vgq.get("conclusion")=="PLAUSIBLES_AVEC_DEFIS_ET_RESERVES_DE_PRESENTATION" and
           vgq.get("ne_certifie_pas_realisation_previsions") is True and
           vgq.get("ne_certifie_pas_budget_nova") is True,
           "AVIS_VGQ_ETENDU_A_TORT")
    amend=sources["OUTIL_SIMULATION_AMENDE"]
    ensure(amend.get("elements_corriges")==[
            "SERVICE_DETTE_IMPACT_ELEMENT_DETTE",
            "TABLEAUX_DETTE_NETTE_ET_BRUTE"] and
           amend.get("contenu_tableur_verifie_par_P56P") is False and
           amend.get("reproduction_des_resultats_via_tableur_amende_validee") is False,
           "AMENDEMENT_SIMULATEUR_NON_REPRODUIT")
    rows=base.get("annees_historique_et_previsions")
    ensure(isinstance(rows,list) and len(rows)==len(YEARS) and
           [x.get("exercice") for x in rows]==list(YEARS),
           "SIX_EXERCICES_PREELECTORAUX_REQUIS")
    deficits={}
    conditional={}
    for i,row in enumerate(rows):
        expected="ETATS_FINANCIERS_2025_2026_AUDITES" if i==0 else (
            "HYPOTHESES_ET_PREVISIONS_PLAUSIBLES_AU_10_JUILLET_2026_NON_GARANTIES"
            if i<=3 else "HORS_PERIMETRE_EXAMEN_VGQ_TROIS_ANS")
        ensure(row.get("portee_certification_vgq")==expected and
               row.get("categorie")==(
                "COMPTE_PUBLIC_AUDITE_2025_2026" if i==0 else
                "PREVISION_GOUVERNEMENT_AOUT_2026") and
               row.get("reforme_nova_incluse") is False and
               row.get("deux_taxes_nova_autorisees") is False,
               "PROJECTION_PUBLIQUE_CONFONDUE_AVEC_NOVA")
        revenue=row.get("revenus")
        ensure(isinstance(revenue,dict) and set(revenue)==set(FIELDS),
               "SOUS_POSTES_REVENUS_NON_EXHAUSTIFS")
        for k,all_values in FIELDS.items():
            ensure(integer(revenue[k])==all_values[i],
                   "POSTE_REVENUS_INCORRECT_"+k)
        for k,all_values in METRICS.items():
            ensure(integer(row.get(k))==all_values[i],
                   "COMPTE_BUDGET_ERRONE_"+k)
        own=sum((integer(v) for v in revenue.values()),Decimal(0))
        ensure(own==integer(row["revenus_autonomes_mcad"]),
               "REVENUS_AUTONOMES_NON_RECONCILIES")
        combined=own+integer(row["transferts_federaux_mcad"])
        ensure(combined==integer(row["total_revenus_mcad"]),
               "TRANSFERTS_FEDERAUX_DOUBLE_COMPTES")
        totalspend=integer(row["depenses_portefeuilles_mcad"])+integer(
            row["service_dette_deja_inclus_mcad"])
        ensure(totalspend==integer(row["total_depenses_hors_provision_mcad"]),
               "SERVICE_DETTE_DOUBLE_COMPTE")
        without=combined-totalspend-integer(row["provision_eventualites_mcad"])
        ensure(without==integer(row["solde_comptable_avant_ecart_resorber_mcad"]),
               "SOLDE_COMPTABLE_NON_CONCILIE")
        after=without+integer(
            row["ecart_a_resorber_non_finance_par_mesures_identifiees_mcad"])
        legal=after-integer(row["fonds_generations_mcad"])
        ensure(legal==integer(row["solde_budgetaire_selon_loi_mcad"]),
               "SOLDE_SELON_LOI_NON_CONCILIE")
        deficits[row["exercice"]]=str(legal)
        conditional[row["exercice"]]=str(integer(
            row["ecart_a_resorber_non_finance_par_mesures_identifiees_mcad"]))
    facts=base.get("observations_pertinentes")
    ensure(isinstance(facts,dict) and
           facts.get("solde_2028_2029_avant_resorption_mcad")=="-724" and
           facts.get("ecart_2028_2029_a_resorber_mcad")=="1850" and
           facts.get("solde_comptable_2028_2029_apres_resorption_theorique_mcad")=="1126" and
           facts.get("solde_budgetaire_2028_2029_si_resorption_mcad")=="-1500" and
           facts.get("ecarts_a_resorber_2029_2030_et_2030_2031_mcad")==["2000","2000"] and
           facts.get("equilibre_2029_2030_conditionnel_a_resorption") is True and
           facts.get("economie_nova_non_identifiee_pour_les_ecarts_mcad") is None and
           facts.get("ne_pas_ajouter_les_sensibilites_sans_scenario_coherent") is True and
           facts.get("depenses_services_civiques_non_reduites_par_simple_elimination_de_taxes") is True,
           "ECARTS_A_RESORBER_PAS_DES_ECONOMIES_NOVA")
    ensure(integer(rows[3]["solde_comptable_avant_ecart_resorber_mcad"])+
           integer(rows[3]["ecart_a_resorber_non_finance_par_mesures_identifiees_mcad"])==
           integer(facts["solde_comptable_2028_2029_apres_resorption_theorique_mcad"]),
           "OBSERVATION_VGQ_2028_29_NON_CONCILIEE")
    risks=facts.get("sensibilites_risques_publics_rapport_tableau_13")
    ensure(isinstance(risks,list) and len(risks)==len(RISKS) and
           {x.get("id") for x in risks if isinstance(x,dict)}==set(RISKS),
           "SENSIBILITES_SOURCE_NON_EXHAUSTIVES")
    for r in risks:
        field,value=RISKS[r["id"]]
        ensure(r.get(field)==value and len(r.get("variation",""))>=20 and
               len(r.get("limite",""))>=22,
               "SENSIBILITES_NON_HOMOGENES")
    observation=base.get("observation_trimestrielle_au_30_juin_2026")
    ensure(isinstance(observation,dict) and
           observation.get("type")=="DONNEES_TRIMESTRIELLES_NON_AUDITEES" and
           observation.get("revenus_avril_juin_mcad")=="41759" and
           observation.get("depenses_avril_juin_mcad")=="42226" and
           observation.get("deficit_comptable_avril_juin_mcad")=="-467" and
           observation.get("n_est_pas_un_quart_de_la_prevision_annuelle") is True and
           observation.get("rapport_septembre_confirme_prevision_2026_2027") is True and
           integer(observation["revenus_avril_juin_mcad"])-
           integer(observation["depenses_avril_juin_mcad"])==
           integer(observation["deficit_comptable_avril_juin_mcad"]),
           "DONNEES_TRIMESTRIELLES_TROMPEUSES")
    old=base.get("reconciliation_mars_vs_aout_2026_2027")
    ensure(isinstance(old,dict) and
           old.get("source_mars")=="projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json" and
           old.get("reference_mars_modifiee_dans_P52B") is False and
           old.get("nouvelle_base_2027_2036_certifiee_nova") is False,
           "P52B_MODIFIE_SANS_REVUE")
    march=old.get("ancienne_reference_mars_2026_2027")
    aug=old.get("nouvelle_reference_aout_2026_2027")
    delta=old.get("variations_aout_moins_mars")
    originals=model.get("reference_2026_2027")
    requirekeys={"revenus_consolides_mcad":"revenus_consolides",
                 "depenses_consolidees_mcad":"depenses_consolidees",
                 "service_dette_indicatif_mcad":"service_dette_indicatif"}
    requireaug={"revenus_consolides_mcad":"total_revenus_mcad",
                "depenses_consolidees_mcad":"total_depenses_hors_provision_mcad",
                "service_dette_indicatif_mcad":"service_dette_deja_inclus_mcad"}
    ensure(isinstance(originals,dict) and isinstance(march,dict) and
           isinstance(aug,dict) and isinstance(delta,dict),
           "RECONCILIATION_MARS_AOUT_ABSENTE")
    for field,pfield in requirekeys.items():
        ensure(integer(march.get(field))==Decimal(originals[pfield])*1000 and
               integer(aug.get(field))==integer(rows[1][requireaug[field]]),
               "REFERENCE_MARS_OU_AOUT_ERRONEE")
    ensure(integer(delta["revenus_consolides_mcad"])==
           integer(aug["revenus_consolides_mcad"])-integer(march["revenus_consolides_mcad"]) and
           integer(delta["depenses_consolidees_mcad"])==
           integer(aug["depenses_consolidees_mcad"])-integer(march["depenses_consolidees_mcad"]) and
           integer(delta["service_dette_mcad"])==
           integer(aug["service_dette_indicatif_mcad"])-integer(march["service_dette_indicatif_mcad"]) and
           delta=={"revenus_consolides_mcad":"1897",
                   "depenses_consolidees_mcad":"840","service_dette_mcad":"248"},
           "ECART_MARS_AOUT_NON_RECONCILIE")
    limits=base.get("perimetres_et_limites")
    ensure(isinstance(limits,dict) and set(limits)==set(AUDIT_FLAGS) and
           limits==AUDIT_FLAGS,"LIMITES_AUDIT_MANQUANTES")
    jobs=base.get("livrables_manquants")
    ensure(isinstance(jobs,list) and len(jobs)==8 and
           {x.get("id") for x in jobs}=={f"P{i:02d}" for i in range(1,9)} and
           all(x.get("statut")=="MANQUANT" and x.get("preuve_id") is None and
               len(x.get("preuve",""))>=65 for x in jobs),
           "PREUVES_FISCALES_FICTIVES")
    integration=base.get("integration_nova")
    ensure(isinstance(integration,dict) and
           all(integration.get(k)==v for k,v in PATHS.items()) and
           integration.get("score_estimatif_pourcent")==53 and
           integration.get("postes_financiers_P52B_a_renseigner")==600 and
           integration.get("incidences_P52D_a_renseigner")==720 and
           integration.get("preuves_fiscales_P52A_non_validees")==20 and
           integration.get("portes_completes_P56O")==0 and
           integration.get("budget_nova_chiffre_et_valide") is False and
           integration.get("nombre_cellules_P52B_modifiees")==0 and
           integration.get("montants_nova_certifies_mcad") is None and
           integration.get("avis_independants_nova_signes")==0 and
           integration.get("main_modifiee") is False and
           integration.get("sinjira_modifie") is False,
           "BASE_PUBLIQUE_DEGUISEE_EN_RESULTAT_NOVA")
    ensure(isinstance(bar,dict) and bar.get("schema_version")=="P55N-1" and
           bar.get("score_estimatif")==53 and
           sum(x["points_estimes"] for x in bar["axes"])==53 and
           isinstance(finish,dict) and finish.get("schema_version")=="P56O-1" and
           finish.get("metadonnees_qualification",{}).get("estimation_centrale_pourcent")==53 and
           len([x for x in finish["portes"] if x["statut"]=="PROUVE"])==0,
           "100_POURCENT_NON_ETAYE")
    return {
        "jalon":"P56P",
        "source":"RAPPORT_PREELECTORAL_2026_AOUT_TABLEAU_2",
        "annees_source":list(YEARS),
        "annees_source_count":6,
        "donnees_2025_2026_auditees":True,
        "annees_previsions_considerees_plausibles_vgq":list(YEARS[1:4]),
        "annees_2029_2031_hors_examens_vgq":list(YEARS[4:]),
        "previsions_gouv_2026_2027_revenus_mcad":"168389",
        "previsions_gouv_2026_2027_depenses_sans_provision_mcad":"171597",
        "previsions_gouv_2027_2028_revenus_mcad":"174225",
        "previsions_gouv_2027_2028_depenses_sans_provision_mcad":"175919",
        "solde_loi_par_annee_mcad":deficits,
        "ecarts_a_resorber_par_annee_mcad":conditional,
        "ecarts_conditionnels_2028_2031_mcad":"5850",
        "ecart_Mars_Aout_revenus_2026_27_mcad":"1897",
        "ecart_Mars_Aout_depenses_2026_27_mcad":"840",
        "rapport_trimestriel_2026_27_confirme_cadre_aout":True,
        "p52b_montants_encore_inconnus":600,
        "p52d_incidences_encore_inconnues":720,
        "p52a_preuves_encore_non_validees":20,
        "score_estime_pourcent":53,
        "budget_nova_adopte":False,
        "aucun_bilan_souverain_p56p":True,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    for x in ("base","p52b","barometre","p56o"):
        ap.add_argument("--"+x,required=True,type=Path)
    ap.add_argument("--rapport",type=Path)
    ap.add_argument("--exiger-budget-nova-certifie",action="store_true")
    a=ap.parse_args(argv)
    if a.exiger_budget_nova_certifie:
        print("NO_GO_AUTOMATIQUE: les projections du gouvernement ne sont pas des engagements Nova",file=sys.stderr)
        return 3
    try:
        def get(p):
            return json.loads(p.read_text(encoding="utf-8"))
        result=assess(get(a.base),get(a.p52b),get(a.barometre),get(a.p56o))
        serial=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as file:
                file.write(serial)
        else:
            print(serial,end="")
        return 0
    except (ValueError,KeyError,TypeError,OSError,InvalidOperation,json.JSONDecodeError) as error:
        print("REFUS: "+str(error),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
