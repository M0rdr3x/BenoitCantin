#!/usr/bin/env python3
"""P52H: bilan transversal de maturité fiscale, jamais un GO.

Recalcule P52A/B/C/D/E depuis leurs entrées sources. Les cas détaillés
restent en mémoire; seul un rapport agrégé est produit.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

MODULE_DIR=Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0,str(MODULE_DIR))
import evaluer_transition_fiscale_nova_p52b as p52b
import rapprocher_budget_quebec_nova_p52c as p52c
import comparer_incidence_fiscale_nova_p52d as p52d
import evaluer_garde_fous_revenu_nova_p52e as p52e

ROOT=MODULE_DIR.parent
STUDY=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
    "preuves":STUDY/"P52A_REGISTRE_PREUVES_FISCALES.json",
    "projection":STUDY/"P52B_GABARIT_MODELE_DECENNAL.json",
    "budget":STUDY/"P52C_REFERENTIEL_BUDGET_QUEBEC_2026_2027.json",
    "incidence":STUDY/"P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json",
}
VERSION="P52H-1"

def require(condition,code):
    if not condition:
        raise ValueError(code)

def load_inputs(paths=FILES):
    require(isinstance(paths,dict) and set(paths)==set(FILES),
            "QUATRE_SOURCES_REQUISES")
    result={}
    for key in FILES:
        path=Path(paths[key])
        require(path.is_file() and path.stat().st_size<1_500_000,
                "SOURCE_ABSENTE_OU_TROP_GRANDE_"+key)
        result[key]=json.loads(path.read_text(encoding="utf-8"))
        require(isinstance(result[key],dict),"SOURCE_JSON_INVALIDE_"+key)
    return result

def analyser(sources):
    require(isinstance(sources,dict) and set(sources)==set(FILES),
            "QUATRE_SOURCES_REQUISES")
    # Recompute; never trust user-authored or stale precomputed reports.
    projection=p52b.evaluate(sources["projection"],sources["preuves"])
    budget=p52c.reconcile(sources["budget"],sources["projection"])
    incidence=p52d.evaluate(sources["incidence"])
    protection=p52e.analyse(sources["incidence"])
    require(all(v.get("decision")=="NO_GO_AUTOMATIQUE" for v in (
        projection,budget,incidence,protection)),"DECISION_INCOHERENTE")
    require(projection["nombre_regimes"]==2 and
            projection["nombre_trajectoires"]==6 and
            projection["nombre_exercices"]==10,
            "HORIZON_FINANCIER_MODIFIE")
    require(incidence["nombre_regimes"]==2 and
            incidence["nombre_scenarios"]==6 and
            incidence["cas_menages"]==30 and
            incidence["cas_entreprises"]==12 and
            incidence["nombre_cas"]==42, "GRILLE_INCIDENCE_MODIFIEE")
    require(protection["nombre_cas"]==42 and
            protection["nombre_cas_menages"]==30 and
            protection["nombre_cas_entreprises"]==12 and
            protection["montants_manquants"]==incidence["montants_manquants"] and
            protection["cas_conditionnellement_calculables"]==
                incidence["cas_calculables_conditionnellement"],
            "INCIDENCE_ET_ALERTE_NON_CONCORDANTES")
    require(budget["annees_scenarios_2027_2036_renseignees_par_ce_controle"]==0
            and budget["nombre_postes_officiels_reconcilies"]==21
            and budget["transcription_source_verifiee_independamment"] is False,
            "BUDGET_REFERENCE_NON_CERTIFIE_OU_INCOHERENT")
    require(budget["revenus_totaux"]=="166.492" and
            budget["depenses_totales"]=="170.757" and
            budget["solde_budgetaire_prevu_selon_loi"]=="-8.612",
            "SOUS_TOTAUX_BUDGETAIRES_MODIFIES")
    require(projection["reference_ecart_non_assimilable_solde_budgetaire_officiel"]
            is True,"SOLDE_BRUT_ASSIMILE_DEFICIT")
    require(all(v.get("publication_autorisee") is False for v in
                (projection,budget,incidence,protection)), "PUBLICATION_NON_AUTORISEE")
    require(incidence["aucune_projection_population"] is True and
            incidence["impact_economique_causal_certifie"] is False and
            protection["preuves_representativite_obtenues"] is False and
            protection["repercussion_prix_salaires_emplois_mesuree"] is False,
            "REPRESENTATIVITE_OU_CAUSALITE_INVENTEE")
    observed_losses=protection["cas_a_risque_de_perte_dans_leur_propre_scenario"]
    require(type(observed_losses) is int and 0<=observed_losses<=42,
            "COMPTE_PERTES_INVALIDE")
    model_missing=projection["entrees_financieres_manquantes"]
    incidence_missing=incidence["montants_manquants"]
    pending=projection["preuves_P52A_encore_non_valides"]
    require(all(type(x) is int and x>=0 for x in
                (model_missing,incidence_missing,pending)),
            "COMPTE_INCONNU_NON_FIABLE")
    require(pending<=20 and model_missing<=600 and incidence_missing<=720,
            "COMPTE_SUPERIEUR_AU_GABARIT")

    blocks=[]
    if pending: blocks.append("PREUVES_FISCALES_INDEPENDANTES_NON_REUNIES")
    if model_missing: blocks.append("PROJECTIONS_DECENNALES_NON_DOCUMENTEES")
    if incidence_missing: blocks.append("INCIDENCE_MENAGES_ENTREPRISES_INCOMPLETE")
    if incidence["cas_calculables_conditionnellement"]<42:
        blocks.append("CAS_INCIDENCE_NON_CALCULABLES")
    if observed_losses:
        blocks.append("PERTES_A_EXAMINER_DANS_CERTAINS_CAS")
    blocks.extend((
        "BUDGET_TRANSCRIT_NON_CERTIFIE_INDEPENDAMMENT",
        "REPRESENTATIVITE_POPULATION_NON_ETABLIE",
        "EFFETS_PRIX_SALAIRES_SERVICES_NON_ETABLIS",
        "AUTORISATION_JURIDIQUE_DEMOCRATIQUE_ABSENTE",
    ))
    if not pending and not model_missing and not incidence_missing:
        blocks.append("COMPLETUDE_DECLARATIVE_NE_VAUT_PAS_AUDIT")
    if observed_losses==0 and incidence["cas_calculables_conditionnellement"]==0:
        losses_label="AUCUN_CAS_EVALUABLE_PAS_ZERO_PERTE_DEMONTREE"
    elif observed_losses==0:
        losses_label="AUCUNE_PERTE_OBSERVEE_DANS_CES_SEULS_CAS_NON_REPRESENTATIFS"
    else:
        losses_label="PERTES_SIGNALEES_SUR_CAS_NON_REPRESENTATIFS"
    # Whitelist-only report: never export per-case figures or reference URLs.
    return {
        "jalon":"P52H",
        "schema_version":VERSION,
        "statut":"RECONCILIATION_DES_PREUVES_NON_ADOPTEE",
        "regimes":["QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN"],
        "trajectoires_par_regime":3,
        "exercices_par_trajectoire":10,
        "lignes_projection":60,
        "champs_financiers_encore_inconnus":model_missing,
        "preuves_fiscales_P52A_encore_non_attestees":pending,
        "recettes_budget_2026_2027_reference_verifiees_arithmetiquement":True,
        "budget_source_originale_verifiee_independamment":False,
        "budget_reference_annee":"2026-2027",
        "budget_reference_non_extrapole_aux_annees_futures":True,
        "cas_menages":30,"cas_entreprises":12,
        "cas_incidence":42,
        "montants_individuels_encore_inconnus":incidence_missing,
        "cas_incidence_conditionnellement_calculables":
            incidence["cas_calculables_conditionnellement"],
        "pertes_signalees_dans_cas_calculables":observed_losses,
        "statut_conclusion_pertes":losses_label,
        "absence_appauvrissement_population_demontree":False,
        "causalite_fiscale_demontree":False,
        "reforme_deux_prelevements_financee":False,
        "pouvoir_provincial_sur_impots_federaux_presume":False,
        "souverainete_etablie":False,
        "revenus_anti_evasion_supplementaires_certifies":False,
        "tarif_fiscal_calcule_ou_adopte":False,
        "publication_autorisee":False,
        "fusion_autorisee":False,
        "rapport_sans_donnees_par_cas":True,
        "blocages":sorted(set(blocks)),
        "decision":"NO_GO_AUTOMATIQUE",
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for key,path in FILES.items():
        parser.add_argument("--"+key,type=Path,default=path)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--exiger-preparation",action="store_true",
                        help="Retourne 3: le contrôle ne confère aucun GO")
    args=parser.parse_args(argv)
    try:
        sources=load_inputs({k:getattr(args,k) for k in FILES})
        result=analyser(sources)
        status=3 if args.exiger_preparation else 0
    except (OSError,UnicodeError,ValueError,KeyError,TypeError,
            OverflowError) as exc:
        result={"jalon":"P52H","schema_version":VERSION,
                "statut":"ERREUR_VALIDATION",
                "erreur_type":type(exc).__name__,
                "publication_autorisee":False,
                "fusion_autorisee":False,
                "decision":"NO_GO_AUTOMATIQUE"}
        status=2
    payload=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True,exist_ok=True)
        args.rapport.write_text(payload,encoding="utf-8")
    else:
        print(payload,end="")
    return status

if __name__=="__main__":
    sys.exit(main())
