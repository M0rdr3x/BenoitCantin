#!/usr/bin/env python3
"""P56T: rapprochement des dépenses par portefeuille et séparation des budgets Nova.

Source : Ministère des Finances, rapport préélectoral 17 août 2026,
tableau 25, page imprimée 81 (PDF index zéro 83), visuellement vérifié.
Aucune ligne du budget gouvernemental n'est une économie Nova.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

YEARS=("2025-2026","2026-2027","2027-2028","2028-2029")
CAT={
"SANTE":(65945,69991,72744,75389),
"EDUCATION":(23541,24411,25068,25561),
"SUPERIEUR":(11183,11847,12339,12588),
"FAMILLE":(9633,10067,10282,10238),
"TRANSPORTS":(9176,7869,8843,8516),
"EMPLOI":(5811,6358,5939,5808),
"MUNICIPAL":(5253,5863,5442,4794),
"ECONOMIE":(4365,4506,4165,3566),
"ENVIRONNEMENT":(1802,1979,2168,2131),
"AUTRES":(19073,18790,18659,18675),
"REALLOCATION":(0,-600,-600,-600)
}
TOTAL=(155782,161081,165049,166666)
CORE4=("SANTE","EDUCATION","SUPERIEUR","FAMILLE")
CORE7=CORE4+("TRANSPORTS","EMPLOI","MUNICIPAL")
PDF="https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf"
LINKS={
"p56p":"projets/projet-nova/etudes/P56P_BASE_BUDGET_PREELECTORALE_2026_2031_VGQ_ET_ECARTS.json",
"p56s":"projets/projet-nova/etudes/P56S_TROIS_OPTIONS_FISCALES_2027_2031_ET_CONDITIONS_PROTECTION.json",
"p56o":"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
"p55n":"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
}
FUTURE=("2029-2030","2030-2031","2031-2032","2032-2033",
        "2033-2034","2034-2035","2035-2036","2036-2037")

def must(condition,message):
    if not condition:
        raise ValueError(message)

def number(value):
    must(type(value) is str and (
        value=="0" or (value.isdecimal() and not value.startswith("0")) or
        (value.startswith("-") and value[1:].isdecimal() and
         not value[1:].startswith("0"))), "ENTIER_MCAD_EXPLICITE_REQUIS")
    return int(value)

def auditer(d,p56p,p56s,p56o,p55n):
    must(isinstance(d,dict) and d.get("schema_version")=="P56T-1" and
         d.get("date_revision")=="2026-11-08" and
         d.get("objet")=="ANCRAGE_DEPENSES_PAR_PORTEFEUILLE_POUR_GARANTIES_SERVICES_PUBLICS_NOVA" and
         d.get("statut")=="BUDGET_GOUVERNEMENTAL_EXISTANT_QUATRE_EXERCICES_NON_BUDGET_NOVA" and
         d.get("decision")=="NO_GO_AUTOMATIQUE" and
         d.get("decision_finale")=="NO_GO_AUTOMATIQUE", "ENTETE_NON_CONFORME")
    src=d.get("source")
    must(isinstance(src,dict) and src.get("url")==PDF and
         src.get("date_publication")=="2026-08-17" and
         src.get("tableau")==25 and
         src.get("page_pdf_index_zero")==83 and
         src.get("page_imprimee")==81 and
         src.get("statut_verification")=="TABLEAU_25_EXAMINE_VISUELLEMENT_2026_11_08" and
         src.get("source_octets_hash_sha256") is None,
         "PROVENANCE_PDF_NON_TRAÇABLE")
    must(isinstance(p56p,dict) and p56p.get("schema_version")=="P56P-1" and
         isinstance(p56p.get("annees_historique_et_previsions"),list) and
         p56s.get("schema_version")=="P56S-1" and
         p56s.get("decision")=="NO_GO_AUTOMATIQUE" and
         p56o.get("schema_version")=="P56O-1" and
         p56o.get("definition_terminee",{}).get("etat_actuel_termine") is False and
         p55n.get("schema_version")=="P55N-1" and
         p55n.get("score_estimatif")==53,
         "REFERENCES_NOVA_NON_COHERENTES")
    rows=d.get("categories")
    must(isinstance(rows,list) and len(rows)==11 and
         {r.get("id") for r in rows if isinstance(r,dict)}==set(CAT),
         "CATEGORIES_OFFICIELLES_INCOMPLETES")
    must([r["id"] for r in rows]==list(CAT),"ORDRE_TABLEAU_25_NON_RESPECTE")
    for entry in rows:
        code=entry["id"]
        expected=CAT[code]
        amounts=entry.get("montants_par_exercice_mcad")
        must(isinstance(amounts,dict) and set(amounts)==set(YEARS) and
             all(number(amounts[y])==expected[i] for i,y in enumerate(YEARS)),
             "POSTE_OFFICIEL_FAUX_"+code)
        must(entry.get("critere_continuite")==
             "LE_POSTE_EST_UNE_DEPENSE_DU_GOUVERNEMENT_ACTUEL_ET_NON_UNE_ECONOMIE_NOVA" and
             entry.get("date_revision_juridique") is None and
             entry.get("cout_reforme_nova_mcad") is None and
             entry.get("service_renforce_ou_reduit_par_nova") is False and
             entry.get("statut")=="REFERENCE_NON_RECONCILIEE_A_LA_POLITIQUE_NOVA" and
             len(entry.get("nom",""))>=6 and
             len(entry.get("risque_de_continuite",""))>=22,
             "BUDGET_OFFICIEL_DEVENU_ENGAGEMENT_NOVA")
    years=d.get("annees")
    must(isinstance(years,list) and [x.get("exercice") for x in years]==list(YEARS),
         "PERIODES_SECTORIELLES_INCOMPLETES")
    sourceyear={x["exercice"]:x for x in p56p["annees_historique_et_previsions"]}
    summaries={}
    for i,row in enumerate(years):
        y=YEARS[i]
        comp=row.get("depenses_portefeuilles_mcad")
        must(isinstance(comp,dict) and set(comp)==set(CAT),"GRILLE_DEPENSES_INCOMPLETE")
        for code,amounts in CAT.items():
            must(number(comp[code])==amounts[i],"CHIFFRE_PORTFEUILLE_NON_CONFORME_"+code)
        subtotal=sum(number(v) for v in comp.values())
        c4=sum(number(comp[k]) for k in CORE4)
        c7=sum(number(comp[k]) for k in CORE7)
        must(subtotal==TOTAL[i] and
             number(row.get("total_portefeuilles_publie_mcad"))==subtotal and
             number(row.get("somme_postes_y_compris_reallocation_mcad"))==subtotal and
             number(row.get("noyau_sante_education_superieur_famille_mcad"))==c4 and
             number(row.get("noyau_sept_services_sante_education_superieur_famille_transport_emploi_municipal_mcad"))==c7,
             "SOUS_TOTAL_SECTORIEL_NON_RECONCILIE")
        must(sourceyear[y]["depenses_portefeuilles_mcad"]==str(subtotal),
             "DEPENSES_P56P_NON_CONCORDANTES")
        must(row.get("statut")==(
             "COMPTES_PUBLICS_2025_2026_AUDITES" if i==0 else
             "PREVISIONS_GOUVERNEMENT_AOUT_2026") and
             row.get("service_de_la_dette_deja_dans_p56p_non_ajoute_ici") is True and
             row.get("transfert_et_depense_organisme_consolide_non_double_compte") is True and
             row.get("cout_de_continuite_nova_propre_non_mesure_mcad") is None and
             row.get("economies_nova_reelles_certifiees_mcad") is None and
             row.get("emploi_public_maintenu_economiquement_demontre") is False,
             "PROMESSES_SERVICES_INJUSTIFIEES")
        summaries[y]={
            "total_portefeuilles_publics_mcad":str(subtotal),
            "quatre_portefeuilles_sante_education_superieur_famille_mcad":str(c4),
            "sept_portefeuilles_services_mcad":str(c7),
            "reallocation_mcad":comp["REALLOCATION"]}
    scope=d.get("perimetre")
    must(isinstance(scope,dict) and
         scope.get("regime")=="QUEBEC_DANS_CANADA" and
         scope.get("annees_detail_budget_officiel")==list(YEARS) and
         scope.get("annees_horizon_nova_non_couvertes")==list(FUTURE) and
         scope.get("annees_provenance_comptes_publics")==["2025-2026"] and
         scope.get("annees_de_previsions")==list(YEARS[1:]) and
         scope.get("services_regime_souverain_estimes") is False and
         all(scope.get(x) is True for x in (
           "previsions_2029_2031_totaux_p56p_disponibles_sans_decomposition_porte_feuille",
           "portefeuilles_ne_sont_pas_un_bilan_de_cout_sous_services",
           "ajustement_reallocation_est_une_ligne_negative",
           "non_suppression_services_au_debut_de_la_transition")),
         "ANNEES_OU_PERIMETRE_DE_PORTFEUILLES_TROMPEURS")
    tasks=d.get("points_critiques")
    must(isinstance(tasks,list) and len(tasks)==10 and
         {t.get("code") for t in tasks if isinstance(t,dict)}==
           {f"T{i:02d}" for i in range(1,11)} and
         all(t.get("validation")=="NON_DEMONTREE" and
             t.get("piece_id") is None and len(t.get("tache",""))>=65 for t in tasks),
         "PREUVES_HUMAINES_NOVA_NON_OBTENUES")
    info=d.get("validation")
    must(isinstance(info,dict) and
         all(info.get(k)==v for k,v in LINKS.items()) and
         info.get("p52b_inconnus")==600 and
         info.get("p52d_inconnus")==720 and
         info.get("p52a_preuves_non_validees")==20 and
         info.get("score_estime")==53 and
         info.get("points_estimes_restants")==47 and
         info.get("portes_p56o_demontrees")==0 and
         info.get("previsions_nova_2027_2036_calculees")==0 and
         info.get("remplacement_recettes_certifie") is False and
         info.get("avis_externes_nova_signes")==0 and
         info.get("programme_nova_termine") is False,
         "BAROMETRE_ET_FINANCEMENT_NOVA_NONT_VALIDES")
    pivot=summaries["2027-2028"]
    require_total=sum(int(p56s["options"][i]["resultats_par_exercice"][0][
              "recettes_retirees_uniquement_dans_le_test_mcad"].split(".")[0])
              for i in (0,2))
    must(require_total==42875,"P56S_RECETTES_EXPOSEES_NON_CONCORDANTES")
    return {
        "jalon":"P56T","score_estime_pourcent":53,"points_estimés_restants":47,
        "annees":summaries,"annee_pivot":"2027-2028",
        "sante_education_superieur_famille_mcad":pivot[
          "quatre_portefeuilles_sante_education_superieur_famille_mcad"],
        "depenses_portefeuilles_totales_mcad":pivot["total_portefeuilles_publics_mcad"],
        "chiffres_source_certifies_comme_depenses_nova":False,
        "politique_fiscale_nova_chiffree":False,
        "services_publics_proteges_et_finances_par_nova_demontres":False,
        "budgets_nova_p52b_manquants":600,
        "incidences_p52d_manquantes":720,
        "preuves_p52a_non_validees":20,
        "conditions_non_demontrees":10,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("secteurs","p56p","p56s","p56o","barometre"):
        parser.add_argument("--"+key,type=Path,required=True)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--declarer-services-finances",action="store_true")
    a=parser.parse_args(argv)
    if a.declarer_services_finances:
        print("REFUS: les prévisions de référence ne sont pas un budget Nova",file=sys.stderr)
        return 3
    try:
        def load(p):
            return json.loads(p.read_text(encoding="utf-8"))
        result=auditer(load(a.secteurs),load(a.p56p),load(a.p56s),
                       load(a.p56o),load(a.barometre))
        serial=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as out:
                out.write(serial)
        else:
            print(serial,end="")
        return 0
    except (OSError,TypeError,KeyError,ValueError,json.JSONDecodeError) as e:
        print("REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
