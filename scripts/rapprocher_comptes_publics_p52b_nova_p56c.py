#!/usr/bin/env python3
"""Projet Nova P56C : rapprochement historique des comptes publics, sans projection automatique."""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

DIR = Path(__file__).resolve().parent
if str(DIR) not in sys.path:
    sys.path.insert(0, str(DIR))

import evaluer_transition_fiscale_nova_p52b as p52b
import rapprocher_versions_finances_nova_p56b as p56b

VERSION = "P56C-1"
SOURCE_URL = p56b.SOURCES["COMPTES_PUBLICS_AUDITES_2025_2026"]
# Source : Comptes publics 2025-2026, volume 1, sommaire p. PDF 11,
# et ventilation de l'impot sur les revenus et les biens p. PDF 18.
# Montants en M$, resultats constates, Quebec au Canada uniquement.
POSTES = {
    "impot_particuliers": ("RECETTE", "48969", 18, ("impot_revenu_net",)),
    "impots_societes": ("RECETTE", "14599", 18, ("impot_revenu_net",)),
    "cotisations_services_sante": ("RECETTE", "9304", 18, ("autres_prelevements_provinciaux_nets",)),
    "impot_foncier_scolaire": ("RECETTE", "1243", 18, ("autres_prelevements_provinciaux_nets",)),
    "taxes_consommation": ("RECETTE", "29639", 11, ("autres_prelevements_provinciaux_nets",)),
    "droits_permis_redevances": ("RECETTE", "6708", 11,
                                ("revenus_non_fiscaux_nets","autres_prelevements_provinciaux_nets")),
    "revenus_divers": ("RECETTE", "14922", 11,
                      ("revenus_non_fiscaux_nets","autres_prelevements_provinciaux_nets")),
    "revenus_entreprises_gouvernement": ("RECETTE", "5241", 11, ("revenus_non_fiscaux_nets",)),
    "transferts_gouvernement_federal": ("RECETTE", "29803", 11, ("transferts_federaux_nets",)),
    "depenses_portefeuilles": ("DEPENSE", "155782", 11,
                              ("services_existants_hors_dette_et_municipal_nets",
                               "transferts_municipaux_nets","couts_transition_nets")),
    "service_dette": ("DEPENSE", "10148", 11, ("service_dette_net",)),
}
NUM = re.compile(r"(?:0|[1-9][0-9]{0,8})\Z")


def check(ok, message):
    if not ok:
        raise ValueError(message)


def verifier(data, observations_p56b, modele_p52b, preuves_p52a):
    check(isinstance(data, dict) and data.get("schema_version")==VERSION, "SCHEMA_P56C_INVALIDE")
    check(data.get("territoire")=="QUEBEC_DANS_CANADA" and
          data.get("exercice")=="2025-2026" and
          data.get("date_cloture")=="2026-03-31", "EXERCICE_OU_COMPETENCE_INVALIDE")
    check(data.get("nature")=="OBSERVATION_HISTORIQUE_COMPTES_PUBLICS_AUDITES",
          "DONNEES_NON_AUDITEES_INTERDITES")
    check(data.get("decision")=="NO_GO_AUTOMATIQUE", "FAUX_GO_INTERDIT")
    check(data.get("unite_montant")=="M_CAD", "UNITE_INVALIDE")
    check(data.get("postes_budgetaires_p52b_inconnus_maintenus")==600 and
          data.get("incidences_p52d_inconnues_maintenues")==720 and
          data.get("p55n_maturite_estimee")==53, "FAUSSE_COMPLETUDE")
    check(data.get("transposition_aux_projections_automatique") is False, "TRANSFERT_AUTOMATIQUE_INTERDIT")
    s=data.get("source")
    check(isinstance(s,dict) and s.get("url")==SOURCE_URL and
          s.get("pages_pdf_zero_index")==[11,18], "SOURCE_OFFICIELLE_INVALIDE")
    items=data.get("poste_sources")
    check(isinstance(items,list) and len(items)==len(POSTES), "NOMBRE_POSTES_INVALIDE")
    found=set()
    totals=Counter()
    candidats=set(p52b.ALL)
    for x in items:
        check(isinstance(x,dict), "POSTE_INVALIDE")
        k=x.get("id")
        check(isinstance(k,str) and k in POSTES and k not in found, "POSTE_DUPLIQUE_OU_INCONNU")
        found.add(k)
        nature, amount, page, targets = POSTES[k]
        v=x.get("montant_audite_mcad")
        check(isinstance(v,str) and NUM.fullmatch(v) and v==amount, "MONTANT_NON_ATTESTE")
        check(x.get("nature")==nature, "NATURE_INVALIDE")
        check(type(x.get("page_pdf_zero_index")) is int and
              x["page_pdf_zero_index"]==page, "PAGE_PROVENANCE_INVALIDE")
        raw_targets=x.get("postes_candidats_p52b")
        check(isinstance(raw_targets,list) and tuple(raw_targets)==targets and
              set(raw_targets).issubset(candidats), "POSTE_P52B_NON_RECONCILIE")
        check(isinstance(x.get("explication"),str) and len(x["explication"])>=30 and
              isinstance(x.get("restriction"),str) and len(x["restriction"])>10,
              "RAISON_DE_PASSAGE_INCOMPLETE")
        check(x.get("transposition_directe_autorisee") is False and
              x.get("exercice_cible_p52b_2027_2036") is None, "TRANSPOSITION_NON_AUTORISEE")
        check(x.get("source_validation_p56b")=="P56B_SNAPSHOTS_FINANCES_2025_2026_SOURCES_OFFICIELLES.json",
              "CHAINE_PROVENANCE_INVALIDE")
        totals[nature]+=Decimal(amount)
    check(found==set(POSTES), "POSTE_SOURCE_MANQUANT")
    group_income=sum((Decimal(POSTES[k][1]) for k in (
        "impot_particuliers","impots_societes","cotisations_services_sante","impot_foncier_scolaire")), Decimal(0))
    check(group_income==Decimal("74115"), "DOUBLON_FISCAL_OU_MAUVAIS_TOTAL")
    check(totals["RECETTE"]==Decimal("160428") and
          totals["DEPENSE"]==Decimal("165930"), "TOTAUX_OFFICIELS_INCOHERENTS")
    check(totals["RECETTE"]-totals["DEPENSE"]==Decimal("-5502"), "SOLDE_INCOHERENT")
    r=p56b.audit(observations_p56b)
    reported=r["donnees_auditees_references_mcad"]
    check(Decimal(reported["revenus_totaux"])==totals["RECETTE"] and
          Decimal(reported["depenses_totales"])==totals["DEPENSE"] and
          Decimal(reported["solde_comptable"])==totals["RECETTE"]-totals["DEPENSE"],
          "P56B_ET_P56C_DIVERGENT")
    existing=p52b.evaluate(modele_p52b, preuves_p52a)
    check(existing["entrees_financieres_manquantes"]==600 and
          existing["preuves_P52A_encore_non_valides"]==20,
          "MODELE_DECENNAL_NON_CONCORDE")
    for item in existing["resultats"]:
        check(item["annees_calculables"]==0 and item["entrees_manquantes"]==100,
              "UN_BUDGET_NON_AUDITE_A_ETE_RAPPELE")
    return {
        "jalon":"P56C", "schema_version":VERSION,
        "exercice_historique":"2025-2026", "territoire":"QUEBEC_DANS_CANADA",
        "statut":"RAPPROCHEMENT_HISTORIQUE_CONDITIONNEL_SANS_PROJECTION",
        "source_comptes_publics": SOURCE_URL,
        "nb_postes_source_audites":len(found),
        "nb_postes_de_recettes":sum(1 for v in POSTES.values() if v[0]=="RECETTE"),
        "nb_postes_de_depenses":sum(1 for v in POSTES.values() if v[0]=="DEPENSE"),
        "revenus_audites_mcad":str(totals["RECETTE"]),
        "depenses_auditees_mcad":str(totals["DEPENSE"]),
        "solde_comptable_audite_mcad":str(totals["RECETTE"]-totals["DEPENSE"]),
        "regroupement_impot_sur_revenu_et_biens_mcad":str(group_income),
        "impots_particuliers_et_societes_historiques_mcad":
            str(Decimal(POSTES["impot_particuliers"][1])+Decimal(POSTES["impots_societes"][1])),
        "ce_sous_total_ne_vaut_pas_recette_nova":True,
        "service_dette_deja_inclus_dans_depenses_mcad":POSTES["service_dette"][1],
        "aucun_double_compte_service_dette":True,
        "ventilation_services_municipalites_encore_requise":True,
        "chiffres_historiques_importables_directement_p52b":0,
        "montants_p52b_2027_2036_renseignes_par_ce_jalon":0,
        "montants_p52b_manquants":existing["entrees_financieres_manquantes"],
        "preuves_p52a_manquantes":existing["preuves_P52A_encore_non_valides"],
        "incidences_p52d_manquantes":720,
        "maturite_p55n_estimative_pourcent":53,
        "effets_emplois_services_menages":None,
        "solde_previsionnel_nova_2036":None,
        "economies_publiques_nova_certifiees":None,
        "validation_independante_nova":False,
        "decision":"NO_GO_AUTOMATIQUE"
    }


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--table",type=Path,required=True)
    ap.add_argument("--snapshots",type=Path,required=True)
    ap.add_argument("--gabarit",type=Path,required=True)
    ap.add_argument("--registre",type=Path,required=True)
    ap.add_argument("--rapport",type=Path)
    ap.add_argument("--exiger-budget-certifie",action="store_true")
    args=ap.parse_args(argv)
    if args.exiger_budget_certifie:
        print("NO_GO_AUTOMATIQUE: aucun budget Nova certifie", file=sys.stderr)
        return 3
    try:
        def read(p):
            return json.loads(p.read_text(encoding="utf-8"))
        result=verifier(read(args.table),read(args.snapshots),read(args.gabarit),read(args.registre))
        out=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if args.rapport:
            with args.rapport.open("x",encoding="utf-8") as fh:
                fh.write(out)
        else:
            print(out,end="")
        return 0
    except (OSError,ValueError,KeyError,TypeError,AssertionError,json.JSONDecodeError) as exc:
        print("REFUS: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
