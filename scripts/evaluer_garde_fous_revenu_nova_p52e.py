#!/usr/bin/env python3
"""P52E — filtre de non-appauvrissement sur les 42 cas fictifs P52D.

Ce filtre ne mesure ni le bien-être national ni une variation causale des prix.
Il signale des pertes dans les cas fournis et refuse toute généralisation sans
microdonnées représentatives, sources indépendantes et bilan budgétaire.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

import comparer_incidence_fiscale_nova_p52d as model

SCHEMA="P52E-1"
# An unchanged non-tax base is needed even to ATTEMPT an attribution to fiscal
# parameters alone. Benefits and earnings can be affected by other policies;
# their movements must never be silently labelled "tax relief".
HOUSE_NON_TAX=("revenu_brut","prestations_federales","prestations_quebec_ou_etat")
FIRM_NON_TAX=("chiffre_affaires","couts_exploitation_hors_salaires",
              "masse_salariale","subventions_recues")
LIMIT_REGIMES=set(model.REGIMES)
LIMIT_SCENARIOS=set(model.SCENARIOS)
EXPECTED_HOUSE=len(model.REGIMES)*len(model.SCENARIOS)*len(model.MENAGES)
EXPECTED_FIRMS=len(model.REGIMES)*len(model.SCENARIOS)*len(model.ENTREPRISES)


def guard(cond,code):
    if not cond:
        raise ValueError(code)


def compare_case(raw, computed, group):
    complete=computed["montants_manquants"]==0
    if not complete:
        return "DONNEES_MANQUANTES", False
    before=raw["actuel"]
    after=raw["propose"]
    stable=HOUSE_NON_TAX if group=="menages" else FIRM_NON_TAX
    if any(before[k]!=after[k] for k in stable):
        return "CHANGEMENT_NON_FISCAL_A_ISOLER", False
    v=Decimal(computed["variation_cad"])
    if computed["presence_hypotheses"]:
        return ("PERTE_HYPOTHETIQUE_A_EXAMINER" if v<0 else
                "ILLUSTRATION_SANS_PERTE_A_CE_NIVEAU"), True
    if v<0:
        return ("PERTE_MONETAIRE_A_CORRIGER" if group=="menages"
                else "RISQUE_RESULTAT_ENTREPRISE"), True
    return "PAS_DE_PERTE_DANS_CE_CAS_NON_REPRESENTATIF", True


def analyse(data):
    # Re-evaluate the exact source, never rely on an independently supplied
    # report whose SHA, figures or categorization could have drifted.
    report=model.evaluate(data)
    guard(report["decision"]=="NO_GO_AUTOMATIQUE", "MODELE_NON_PRUDENT")
    rows={(r["regime"],r["scenario"],r["type"],r["categorie"]):r
          for r in report["resultats"]}
    guard(len(rows)==42, "CAS_DUPLIQUES_OU_INCOMPLETS")
    by_group={"menages":[],"entreprises":[]}
    count_loss=0
    count_hypothetical=0
    count_exogenous=0
    counts={}
    for regime in model.REGIMES:
        for scenario in model.SCENARIOS:
            families=data["regimes"][regime]["scenarios"][scenario]
            for group,names in (("menages",model.MENAGES),
                                ("entreprises",model.ENTREPRISES)):
                for raw in families[group]:
                    name=raw["categorie"]
                    key=(regime,scenario,group,name)
                    guard(name in names and key in rows,
                          "CAS_P52D_NON_CONCORDANT")
                    calculated=rows[key]
                    label,stable=compare_case(raw,calculated,group)
                    loss=label in ("PERTE_HYPOTHETIQUE_A_EXAMINER",
                                   "PERTE_MONETAIRE_A_CORRIGER",
                                   "RISQUE_RESULTAT_ENTREPRISE")
                    count_loss+=int(loss)
                    count_hypothetical+=int(calculated["presence_hypotheses"])
                    count_exogenous+=int(label=="CHANGEMENT_NON_FISCAL_A_ISOLER")
                    counts[label]=counts.get(label,0)+1
                    by_group[group].append({
                        "regime":regime,"scenario":scenario,
                        "categorie":name,"statut":label,
                        "variation_monetaire_cad":calculated["variation_cad"],
                        "perimetre_stable_pour_attribution_fiscale":stable,
                        "pret_a_generaliser":False,
                        "preuve_de_non_appauvrissement":False,
                    })
    guard(len(by_group["menages"])==EXPECTED_HOUSE and
          len(by_group["entreprises"])==EXPECTED_FIRMS,
          "NOMBRE_DE_CAS_INATTENDU")
    missing=report["montants_manquants"]
    complete=report["cas_calculables_conditionnellement"]
    guard(missing>=0 and complete<=42,"COMPTE_INVALIDE")
    return {
        "jalon":"P52E","schema_version":SCHEMA,
        "regimes":list(model.REGIMES),
        "nombre_cas_menages":EXPECTED_HOUSE,
        "nombre_cas_entreprises":EXPECTED_FIRMS,
        "nombre_cas":42,"cas_conditionnellement_calculables":complete,
        "montants_manquants":missing,
        "cas_avec_sources_hypothetiques":count_hypothetical,
        "cas_a_risque_de_perte_dans_leur_propre_scenario":count_loss,
        "cas_avec_variation_non_fiscale_non_isolee":count_exogenous,
        "repartition_des_statuts":counts,
        "cas":by_group,
        "montrable_comme_mesure_du_pouvoir_achat_du_quebec":False,
        "preuves_representativite_obtenues":False,
        "repercussion_prix_salaires_emplois_mesuree":False,
        "bilan_budgetaire_equilibre_et_finance":False,
        "norme_de_non_appauvrissement_adoptee":False,
        "loi_entree_en_vigueur":False,
        "taux_fiscal_adopte":False,
        "publication_autorisee":False,
        "decision":"NO_GO_AUTOMATIQUE",
        "limite":"Montants annuels de cas individuels, NON un indice de pouvoir d'achat: logement, inflation, services, effets indirects et représentativité ne sont pas évalués."
    }


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gabarit",required=True,type=Path)
    ap.add_argument("--rapport",type=Path)
    ap.add_argument("--exiger-non-appauvrissement-demontre",action="store_true")
    args=ap.parse_args(argv)
    try:
        source=json.loads(args.gabarit.read_text(encoding="utf-8"))
        result=analyse(source)
        # A populated scenario is not population evidence. Until independent
        # representativity and public budget funding exist, this gate cannot
        # be treated as satisfied even if every hypothetical case gains.
        code=3 if args.exiger_non_appauvrissement_demontre else 0
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        result={"jalon":"P52E","statut":"INVALIDE",
                "erreur_type":type(exc).__name__,
                "decision":"NO_GO_AUTOMATIQUE",
                "publication_autorisee":False}
        code=2
    output=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True,exist_ok=True)
        args.rapport.write_text(output,encoding="utf-8")
    else:
        print(output,end="")
    return code


if __name__=="__main__":
    sys.exit(main())
