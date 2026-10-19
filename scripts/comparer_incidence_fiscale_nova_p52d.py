#!/usr/bin/env python3
"""P52D: comparer des cas fiscaux sans inventer ménages, taux ou recettes.

Modèle analytique conditionnel, pas un calculateur de déclaration de revenus.
Les deux régimes sont juridiquement distincts; aucune extrapolation statistique.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys

VERSION="P52D-1"
REGIMES=("QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN")
SCENARIOS=("central","prudent","stress")
MENAGES=(
    "personne_seule_revenu_modeste",
    "famille_avec_enfants",
    "famille_monoparentale",
    "personne_retraitee",
    "personne_seule_revenu_moyen",
)
ENTREPRISES=("PME","GRANDE_ENTREPRISE")
HOUSE_FIELDS=(
    "revenu_brut",
    "prestations_federales",
    "prestations_quebec_ou_etat",
    "impot_revenu_federal",
    "impot_revenu_quebec_ou_etat",
    "cotisations_obligatoires",
    "prelevements_municipaux_directs",
    "taxes_consommation_supportees",
)
FIRM_FIELDS=(
    "chiffre_affaires",
    "couts_exploitation_hors_salaires",
    "masse_salariale",
    "impot_entreprise_federal",
    "impot_entreprise_quebec_ou_etat",
    "cotisations_employeur",
    "prelevements_municipaux",
    "taxes_consommation_non_recouvrables",
    "subventions_recues",
    "charge_additionnelle_anti_evasion",
)
STAGES=("actuel","propose")
CENT_RE=re.compile(r"^(?:0|[1-9]\d{0,8})(?:\.\d{1,2})?$")
SOURCE_TYPES=("document_public","hypothese_non_certifiee")
REFERENCE_SHA="9ed5f70cbe7022f25a679346a1288701f3b09067"


def demand(condition,code):
    if not condition:
        raise ValueError(code)


def amount(x):
    demand(isinstance(x,str) and CENT_RE.fullmatch(x) is not None,
           "MONTANT_CAD_INVALIDE")
    try:
        return Decimal(x)
    except InvalidOperation as exc:
        raise ValueError("MONTANT_CAD_INVALIDE") from exc


def check_source(item):
    demand(isinstance(item,dict) and
           set(item)=={"type","reference"} and
           item["type"] in SOURCE_TYPES and
           isinstance(item["reference"],str) and
           8<=len(item["reference"])<=300 and
           not any(c in item["reference"] for c in "\r\n<>"),
           "PROVENANCE_NON_RECEVABLE")
    if item["type"]=="document_public":
        demand(item["reference"].startswith("https://"),
               "URL_SOURCE_OFFICIELLE_REQUISE")


def check_phase(values,fields,source_map,stage):
    demand(isinstance(values,dict) and set(values)==set(fields),
           "CATEGORIES_INCOMPLETES_"+stage)
    out={}
    for name in fields:
        raw=values[name]
        key=stage+"."+name
        if raw is None:
            demand(key not in source_map,"SOURCE_SANS_MONTANT_"+key)
            out[name]=None
        else:
            out[name]=amount(raw)
            demand(key in source_map,"SOURCE_MANQUANTE_"+key)
            check_source(source_map[key])
    return out


def quantify_case(row,fields,regime,scenario,kind):
    demand(isinstance(row,dict) and
           set(row)=={"regime","scenario","categorie","actuel","propose",
                      "sources","classification_validee"},
           "CAS_INCOMPLET")
    demand(row["regime"]==regime and row["scenario"]==scenario,
           "REGIME_OU_SCENARIO_INCONFORME")
    demand(row["categorie"] in (MENAGES if kind=="menages" else ENTREPRISES),
           "CATEGORIE_INCONNUE")
    demand(row["classification_validee"] is False,
           "CLASSIFICATION_PRESUMEE_VALIDEE")
    sources=row["sources"]
    demand(isinstance(sources,dict) and
           set(sources).issubset({stage+"."+f for stage in STAGES for f in fields}),
           "SOURCES_HORS_PERIMETRE")
    before=check_phase(row["actuel"],fields,sources,"actuel")
    after=check_phase(row["propose"],fields,sources,"propose")
    # Under a provincial-only proposal, the Canadian federal tax/benefit
    # cannot be silently abolished by the province. Any such assumption
    # belongs to a separately authorized federal/constitutional scenario.
    if regime=="QUEBEC_DANS_CANADA":
        frozen=("impot_revenu_federal","prestations_federales") if kind=="menages" else (
            "impot_entreprise_federal",)
        for key in frozen:
            if before[key] is not None and after[key] is not None:
                demand(before[key]==after[key],
                       "POUVOIR_FEDERAL_PROVINCIAL_CONFONDU_"+key)
    missing=sum(x is None for stage in (before,after) for x in stage.values())
    hypothetical=any(src["type"]=="hypothese_non_certifiee"
                     for src in sources.values())
    if missing:
        return {"categorie":row["categorie"],"montants_manquants":missing,
                "solde_actuel_cad":None,"solde_propose_cad":None,
                "variation_cad":None,"completude":"INCOMPLETE",
                "presence_hypotheses":hypothetical,
                "attribution_causale_demontree":False}
    if kind=="menages":
        def net(x):
            direct=(x["revenu_brut"]+x["prestations_federales"]+
                    x["prestations_quebec_ou_etat"]-
                    x["impot_revenu_federal"]-
                    x["impot_revenu_quebec_ou_etat"]-
                    x["cotisations_obligatoires"]-
                    x["prelevements_municipaux_directs"])
            return direct,direct-x["taxes_consommation_supportees"]
        b_direct,b_after=net(before)
        a_direct,a_after=net(after)
        result={"solde_apres_prelevements_directs_actuel_cad":str(b_direct),
                "solde_apres_prelevements_directs_propose_cad":str(a_direct),
                "variation_solde_direct_cad":str(a_direct-b_direct),
                "solde_apres_taxes_conso_actuel_cad":str(b_after),
                "solde_apres_taxes_conso_propose_cad":str(a_after),
                "variation_apres_taxes_conso_cad":str(a_after-b_after)}
    else:
        def net(x):
            return (x["chiffre_affaires"]-
                    x["couts_exploitation_hors_salaires"]-
                    x["masse_salariale"]-
                    x["impot_entreprise_federal"]-
                    x["impot_entreprise_quebec_ou_etat"]-
                    x["cotisations_employeur"]-
                    x["prelevements_municipaux"]-
                    x["taxes_consommation_non_recouvrables"]+
                    x["subventions_recues"]-
                    x["charge_additionnelle_anti_evasion"])
        bv,av=net(before),net(after)
        result={"solde_operationnel_partiel_actuel_cad":str(bv),
                "solde_operationnel_partiel_propose_cad":str(av),
                "variation_solde_partiel_cad":str(av-bv)}
    return {"categorie":row["categorie"],"montants_manquants":0,
            "solde_actuel_cad":str(b_after if kind=="menages" else bv),
            "solde_propose_cad":str(a_after if kind=="menages" else av),
            "variation_cad":str(a_after-b_after if kind=="menages" else av-bv),
            "completude":"ILLUSTRATION_NON_CERTIFIEE" if hypothetical
                         else "CALCUL_CONDITIONNEL_A_AUDITER",
            "presence_hypotheses":hypothetical,
            "attribution_causale_demontree":False,**result}


def evaluate(template):
    demand(isinstance(template,dict) and
           template.get("schema_version")==VERSION and
           template.get("statut")=="ETUDE_NON_ADOPTEE" and
           template.get("reference_main_sha")==REFERENCE_SHA and
           template.get("unite")=="CAD_PAR_CAS_ANNUEL",
           "ENTETE_P52D_INVALIDE")
    demand(template.get("autorisations")=={
        "fiscalite":False,"publication":False,"fusion":False},
        "AUTORISATION_INTERDITE")
    demand(template.get("aucune_ponderation_population") is True,
           "FAUSSE_EXTRAPOLATION_POPULATION")
    parts=template.get("regimes")
    demand(isinstance(parts,dict) and set(parts)==set(REGIMES),
           "DEUX_REGIMES_REQUIS")
    cases=[];unknown=0;complete=0
    for regime in REGIMES:
        settings=parts[regime]
        demand(isinstance(settings,dict) and
               set(settings)=={"competence","scenarios"} and
               settings["competence"]==(
                   "PROVINCE_SANS_MODIFIER_FEDERAL"
                   if regime=="QUEBEC_DANS_CANADA"
                   else "ETAT_SOUVERAIN_HYPOTHETIQUE_NON_RECONNU"),
               "COMPETENCE_CONSTITUTIONNELLE_INVALIDE")
        trajectories=settings["scenarios"]
        demand(isinstance(trajectories,dict) and set(trajectories)==set(SCENARIOS),
               "SCENARIOS_INCOMPLETS")
        for scenario in SCENARIOS:
            classes=trajectories[scenario]
            demand(isinstance(classes,dict) and
                   set(classes)=={"menages","entreprises"},
                   "TYPES_DE_CAS_INCOMPLETS")
            for kind,names,fields in (
                ("menages",MENAGES,HOUSE_FIELDS),
                ("entreprises",ENTREPRISES,FIRM_FIELDS)):
                group=classes[kind]
                demand(isinstance(group,list) and len(group)==len(names),
                       "NOMBRE_DE_CAS_INATTENDU")
                seen=set()
                for row in group:
                    out=quantify_case(row,fields,regime,scenario,kind)
                    demand(out["categorie"] not in seen,"CAS_DUPLIQUE")
                    seen.add(out["categorie"])
                    cases.append({"regime":regime,"scenario":scenario,
                                  "type":kind,**out})
                    unknown+=out["montants_manquants"]
                    complete+=int(out["montants_manquants"]==0)
                demand(seen==set(names),"CATEGORIES_MANQUANTES")
    return {
        "jalon":"P52D","nombre_regimes":2,"nombre_scenarios":6,
        "cas_menages":len(REGIMES)*len(SCENARIOS)*len(MENAGES),
        "cas_entreprises":len(REGIMES)*len(SCENARIOS)*len(ENTREPRISES),
        "nombre_cas":len(cases),
        "montants_manquants":unknown,
        "cas_calculables_conditionnellement":complete,
        "resultats":cases,
        "source_officielle_sur_les_menages_representatifs":False,
        "aucune_projection_population":True,
        "aucun_taux_fiscal_propose":True,
        "impact_economique_causal_certifie":False,
        "budget_total_finance":False,
        "fusion_autorisee":False,
        "publication_autorisee":False,
        "decision":"NO_GO_AUTOMATIQUE",
        "limite":"Cas non representatifs sans poids demographique; des chiffres saisis pourraient etre uniquement illustratifs. Les taxes consommation sont distinctes du solde direct, non du revenu disponible officiel."
    }



def rapport_agrege(report):
    """Whitelist-only export for GitHub CI; excludes every case and all CAD values.

    Safe if future templates contain finely segmented or illustrative inputs:
    no raw stage, reference, amount, category or per-case output is copied.
    """
    demand(isinstance(report,dict) and
           report.get("decision")=="NO_GO_AUTOMATIQUE" and
           report.get("publication_autorisee") is False and
           report.get("aucune_projection_population") is True,
           "RAPPORT_PUBLIC_HORS_PERIMETRE")
    keys=(
        "jalon", "nombre_regimes", "nombre_scenarios",
        "cas_menages", "cas_entreprises", "nombre_cas",
        "montants_manquants", "cas_calculables_conditionnellement",
        "source_officielle_sur_les_menages_representatifs",
        "aucune_projection_population", "impact_economique_causal_certifie",
        "budget_total_finance", "fusion_autorisee",
        "publication_autorisee", "decision",
    )
    result={k:report[k] for k in keys}
    demand(type(result["nombre_cas"]) is int and
           result["nombre_cas"]==42 and
           all(type(result[k]) is int and result[k]>=0 for k in (
               "montants_manquants","cas_calculables_conditionnellement")),
           "COMPTEURS_AGREGES_INCOHERENTS")
    result["rapport_agrege_sans_details"]=True
    result["aucun_montant_individuel_exporte"]=True
    result["rappel"]="Observations sans valeurs par cas; aucune representativite, causalite ou autorisation."
    return result


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gabarit",type=Path,required=True)
    ap.add_argument("--rapport",type=Path)
    ap.add_argument("--exiger-completude",action="store_true")
    ap.add_argument("--rapport-agrege",action="store_true",
                    help="Exporter uniquement des compteurs globaux sans montants ni cas (CI)")
    args=ap.parse_args(argv)
    try:
        data=json.loads(args.gabarit.read_text(encoding="utf-8"))
        report=evaluate(data)
        code=3 if args.exiger_completude and report["montants_manquants"] else 0
        if args.rapport_agrege:
            report=rapport_agrege(report)
    except (OSError,UnicodeError,ValueError,KeyError,TypeError) as exc:
        report={"jalon":"P52D","statut":"INVALIDE","erreur_type":type(exc).__name__,
                "decision":"NO_GO_AUTOMATIQUE","publication_autorisee":False}
        code=2
    value=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True,exist_ok=True)
        args.rapport.write_text(value,encoding="utf-8")
    else:
        print(value,end="")
    return code


if __name__=="__main__":
    sys.exit(main())
