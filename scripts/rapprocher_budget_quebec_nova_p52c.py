#!/usr/bin/env python3
"""P52C — rapprocher les PRÉVISIONS publiées de mars 2026 avec le modèle Nova.

Ce script valide la cohérence arithmétique et les catégories d'une transcription
locale de tableaux officiels. Il ne télécharge rien et ne certifie pas que la
transcription correspond à l'original : une lecture indépendante reste requise.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

SCHEMA="P52C-1"
GROUPS={
    "impots_sur_revenu_et_biens":76050,
    "taxes_consommation":30008,
    "entreprises_gouvernement":5853,
    "droits_permis_redevances":6542,
    "revenus_divers":15908,
    "transferts_federaux":32131,
}
NATURES={"impot_revenu_actuel","prelevement_distinct","revenu_non_fiscal",
         "revenu_non_fiscal_non_assimile","transfert_federal"}
EXPECTED={
    "impot_particuliers":("impots_sur_revenu_et_biens","impot_revenu_actuel",50800),
    "cotisations_sante":("impots_sur_revenu_et_biens","prelevement_distinct",9412),
    "impot_societes":("impots_sur_revenu_et_biens","impot_revenu_actuel",14527),
    "foncier_scolaire":("impots_sur_revenu_et_biens","prelevement_distinct",1311),
    "taxes_vente":("taxes_consommation","prelevement_distinct",26349),
    "carburants":("taxes_consommation","prelevement_distinct",2097),
    "tabac":("taxes_consommation","prelevement_distinct",830),
    "alcool":("taxes_consommation","prelevement_distinct",574),
    "consommation_autres":("taxes_consommation","prelevement_distinct",158),
    "hydro":("entreprises_gouvernement","revenu_non_fiscal",2445),
    "loto":("entreprises_gouvernement","revenu_non_fiscal",1557),
    "saq":("entreprises_gouvernement","revenu_non_fiscal",1406),
    "iq":("entreprises_gouvernement","revenu_non_fiscal",292),
    "sqdc":("entreprises_gouvernement","revenu_non_fiscal",146),
    "entreprises_autres":("entreprises_gouvernement","revenu_non_fiscal",7),
    "droits_redevances":("droits_permis_redevances",
                        "revenu_non_fiscal_non_assimile",6542),
    "revenus_divers":("revenus_divers","revenu_non_fiscal_non_assimile",15908),
    "perequation":("transferts_federaux","transfert_federal",13907),
    "sante_federal":("transferts_federaux","transfert_federal",9265),
    "social_federal":("transferts_federaux","transfert_federal",1392),
    "autres_federaux":("transferts_federaux","transfert_federal",7567),
}
EXPENSES={
    "depenses_portefeuilles":160489,"service_dette":10268,
    "depenses_totales":170757,"provision_eventualites":2000,
    "versements_fonds_generations":2347,
    "deficit_comptable":-6265,"solde_budgetaire_loi_equilibre":-8612,
}
SOURCES={
    "DISC2026_T3":("https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/"
                   "budget/documents/Budget2627_Discours.pdf","Tableau 3","27"),
    "PLAN2026_F2":("https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/"
                   "budget/documents/Budget2627_PlanBudgetaire.pdf","Tableau F.2","F.9")
}
REFERENCE_FIELDS={
    "revenus_consolides":"166.492",
    "depenses_consolidees":"170.757",
    "service_dette_indicatif":"10.268",
}
REQUIRED_SCOPE={
    "taxes_de_vente_aggregat_inclut_autres_taxations",
    "les_revenus_non_fiscaux_ne_sont_pas_des_impots_sur_le_revenu",
    "les_transferts_federaux_ne_sont_pas_des_taxes_provinciales",
    "ne_pas_ajouter_deux_fois_le_service_dette",
    "provision_et_fonds_generation_non_inclus_dans_total_depenses",
    "ce_n_est_pas_un_bilan_de_quebec_souverain",
    "ne_pas_injecter_automatiquement_dans_projections_2027_2036"
}
DIGITS=re.compile(r"^-?(0|[1-9]\d{0,8})$")
REFERENCE="projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json"


def insist(condition,code):
    if not condition:
        raise ValueError(code)


def number(value):
    insist(isinstance(value,str) and DIGITS.fullmatch(value) is not None,
           "MONTANT_EN_MILLIONS_INVALIDE")
    return int(value)


def reconcile(ledger, template):
    insist(isinstance(ledger,dict) and ledger.get("schema_version")==SCHEMA,
           "SCHEMA_P52C_INATTENDU")
    insist(ledger.get("statut")=="REFERENCE_OFFICIELLE_MARS_2026_PREVISION_NON_REALISEE"
           and ledger.get("periode")=="2026-2027" and ledger.get("unite")=="M_CAD",
           "PERIMETRE_OU_PERIODE_INATTENDU")
    sources=ledger.get("sources")
    insist(isinstance(sources,list) and len(sources)==2,"SOURCES_INCOMPLETES")
    source_ids={}
    for entry in sources:
        insist(isinstance(entry,dict) and entry.get("id") in SOURCES
               and entry["id"] not in source_ids,"SOURCE_INVALIDE")
        key=entry["id"]
        insist((entry.get("url"),entry.get("tableau"),entry.get("page_imprimee"))
               ==SOURCES[key],"SOURCE_OU_PAGE_MODIFIEE")
        source_ids[key]=entry
    insist(set(source_ids)==set(SOURCES),"SOURCES_MANQUANTES")
    rows=ledger.get("lignes_revenus")
    insist(isinstance(rows,list) and len(rows)==len(EXPECTED),
           "VINGT_ET_UN_POSTES_ATTENDUS")
    sums=defaultdict(int)
    seen=set()
    for line in rows:
        insist(isinstance(line,dict),"LIGNE_INVALIDE")
        key=line.get("id")
        insist(isinstance(key,str) and key in EXPECTED and key not in seen,
               "POSTE_DUPLIQUE_OU_INCONNU")
        seen.add(key)
        insist(line.get("source_id")=="DISC2026_T3","POSTE_SANS_SOURCE_VALIDE")
        group,kind,value=EXPECTED[key]
        insist(line.get("groupe")==group and line.get("nature")==kind and
               line.get("nature") in NATURES,"CLASSEMENT_FISCAL_INCOHERENT")
        actual=number(line.get("valeur_mcad"))
        insist(actual==value,"ECART_POSTE_OFFICIEL_"+key)
        sums[group]+=actual
    insist(seen==set(EXPECTED),"POSTE_MANQUANT")
    insist(dict(sums)==GROUPS,"SOUS_TOTAUX_NON_RECONCILIES")
    subtotal=ledger.get("sous_totaux_officiels_mcad")
    insist(isinstance(subtotal,dict) and
           set(subtotal)==set(GROUPS)|{"revenus_autonomes","revenus_totaux"},
           "SOUS_TOTAUX_INCOMPLETS")
    insist(all(number(subtotal[k])==v for k,v in GROUPS.items()),
           "SOUS_TOTAUX_SOURCE_INCORRECTS")
    autonomous=sum(v for k,v in sums.items() if k!="transferts_federaux")
    total=autonomous+sums["transferts_federaux"]
    insist(autonomous==number(subtotal["revenus_autonomes"])==134361,
           "REVENUS_AUTONOMES_NON_RECONCILIES")
    insist(total==number(subtotal["revenus_totaux"])==166492,
           "REVENUS_TOTAUX_NON_RECONCILIES")
    expenses=ledger.get("depenses_et_ajustements_officiels_mcad")
    insist(isinstance(expenses,dict) and set(expenses)==set(EXPENSES),
           "AJUSTEMENTS_INCOMPLETS")
    insist(all(number(expenses[k])==v for k,v in EXPENSES.items()),
           "ECART_TABLEAU_F2")
    insist(expenses["depenses_totales"]=="170757","DEPENSES_INCORRECTES")
    # IMPORTANT: 160489+10268 is already 170757: never add debt a second time.
    spend=number(expenses["depenses_portefeuilles"])+number(expenses["service_dette"])
    insist(spend==number(expenses["depenses_totales"]),"DETTE_OU_DEPENSES_DOUBLEES")
    arithmetic=total-spend
    accounting=arithmetic-number(expenses["provision_eventualites"])
    statutory=accounting-number(expenses["versements_fonds_generations"])
    insist(accounting==number(expenses["deficit_comptable"]) and
           statutory==number(expenses["solde_budgetaire_loi_equilibre"]),
           "SOLDE_BUDGETAIRE_MAL_RECONCILIE")
    reference=ledger.get("concordance_referentiel_nova")
    insist(isinstance(reference,dict) and reference.get("chemin")==REFERENCE
           and reference.get("modele_annee")=="2026-2027"
           and reference.get("rapprochement_attendu")=="EXACT_POUR_CES_3_AGREGATS"
           and reference.get("autres_champs_de_modele_non_certifies") is True,
           "CONCORDANCE_HORS_PERIMETRE")
    assert_source=reference.get("montants_en_gcad")
    insist(isinstance(assert_source,dict) and assert_source==REFERENCE_FIELDS,
           "MONTANTS_NOVA_NON_CONCORDANTS")
    insist(isinstance(template,dict) and template.get("statut")=="ETUDE_NON_ADOPTEE"
           and template.get("unite")=="G_CAD"
           and template.get("reference_2026_2027",{}).get("statut")
           =="MODELE_NON_CERTIFIE","GABARIT_NOVA_NON_VALIDABLE")
    baseline=template["reference_2026_2027"]
    insist(all(baseline.get(k)==v for k,v in REFERENCE_FIELDS.items()),
           "GABARIT_NOVA_DIVERGENT")
    scope=ledger.get("tests_de_perimetre")
    insist(isinstance(scope,dict) and set(scope)==REQUIRED_SCOPE
           and all(value is True for value in scope.values()),
           "FRONTIERES_COMPTABLES_NON_ATTESTEES")
    insist(all(ledger.get(k) is False for k in (
        "hypotheses_nova_certifiees","recettes_anti_evasion_nouvelles_certifiees",
        "taux_adoptes","adoption_programmatique","fusion_autorisee",
        "publication_autorisee")) and ledger.get("decision")=="NO_GO_AUTOMATIQUE",
        "GO_NON_AUTORISE")
    existing_income=(EXPECTED["impot_particuliers"][2]+EXPECTED["impot_societes"][2])
    other_autonomous=autonomous-existing_income
    return {
        "jalon":"P52C",
        "annee_reference":"2026-2027",
        "nature":"PREVISIONS_BUDGET_MARS_2026",
        "unite":"G_CAD",
        "revenus_autonomes":str(Decimal(autonomous)/1000),
        "transferts_federaux":str(Decimal(sums["transferts_federaux"])/1000),
        "revenus_totaux":str(Decimal(total)/1000),
        "impots_revenus_existants_particuliers_societes":str(Decimal(existing_income)/1000),
        "autres_revenus_autonomes_y_compris_autres_taxes":str(Decimal(other_autonomous)/1000),
        "taxes_consommation_dont_ventes_agregees":str(Decimal(sums["taxes_consommation"])/1000),
        "depenses_portefeuilles":str(Decimal(number(expenses["depenses_portefeuilles"]))/1000),
        "service_dette_compte_une_fois":str(Decimal(number(expenses["service_dette"]))/1000),
        "depenses_totales":str(Decimal(spend)/1000),
        "ecart_arithmetique_avant_ajustements":str(Decimal(arithmetic)/1000),
        "deficit_comptable_prevu":str(Decimal(accounting)/1000),
        "solde_budgetaire_prevu_selon_loi":str(Decimal(statutory)/1000),
        "nombre_postes_officiels_reconcilies":len(rows),
        "transcription_source_verifiee_independamment":False,
        "annees_scenarios_2027_2036_renseignees_par_ce_controle":0,
        "deux_taxes_financees":False,
        "nouveaux_impots_ou_taux_adoptes":False,
        "publication_autorisee":False,
        "decision":"NO_GO_AUTOMATIQUE",
        "limite":"Rapprochement arithmetique local de tableaux du budget 2026-2027; ne valide ni extrapolation, ni souverainete, ni cout des abolitions.",
    }


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--referentiel",type=Path,required=True)
    ap.add_argument("--gabarit",type=Path,required=True)
    ap.add_argument("--rapport",type=Path)
    ap.add_argument("--exiger-financement",action="store_true")
    args=ap.parse_args(argv)
    try:
        reference=json.loads(args.referentiel.read_text(encoding="utf-8"))
        template=json.loads(args.gabarit.read_text(encoding="utf-8"))
        report=reconcile(reference,template)
        code=3 if args.exiger_financement else 0
    except (OSError,UnicodeError,ValueError,TypeError,KeyError) as exc:
        report={"jalon":"P52C","decision":"NO_GO_AUTOMATIQUE",
                "statut":"INVALIDE","erreur_type":type(exc).__name__,
                "publication_autorisee":False}
        code=2
    output=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True,exist_ok=True)
        args.rapport.write_text(output,encoding="utf-8")
    else:
        print(output,end="")
    return code

if __name__=="__main__":
    sys.exit(main())
