#!/usr/bin/env python3
"""P55I — rapprochement arithmétique non certifiant du sommaire 2024 public."""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import sys

import acquerir_pdfs_publics_nova_p55h as p55h

p55g=p55h.p55g
p55f=p55h.p55g.p55f
p55b=p55h.p55b
p54z=p55h.p54z
BASE=p55h.BASE
CONFIG=BASE/"P55I_REFERENTIEL_ECARTS_BUDGET_REALISATION_2024.json"
NO_GO=p55h.NO_GO
SOURCE={
    "institution":"VILLE_DE_QUEBEC",
    "nom_document":"Rapport financier 2024",
    "url":"https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf",
    "pdf_index_zero":6,
    "page_imprimee":"7",
    "section":"SOMMAIRE_DES_VARIATIONS_BUDGETAIRES_SUR_LES_RESULTATS_CONSOLIDES",
    "qualification":"NON_AUDITE_SOURCE_WEB_TEXTE_NON_REPRODUITE_SUR_OCTETS_P55H",
}
ROWS=(
    ("REVENUS_FONCTIONNEMENT","recette_de_fonctionnement",
     2089556928,2186607854,97050926,"VARIATION_DE_REVENUS_NON_ECONOMIE"),
    ("REVENUS_INVESTISSEMENT","recette_d_investissement",
     403091050,262872891,-140218159,
     "RECETTES_D_INVESTISSEMENT_NON_RECURRENTES_NON_ECONOMIE"),
    ("CHARGES","charge_comptable",
     2092480059,2107478001,14997942,
     "ECART_DE_CHARGES_NON_EQUIVALENT_A_GASPILLAGE"),
    ("EXCEDENT_EXERCICE","solde_resultats",
     400167919,342002744,-58165175,"VARIATION_SOLDE_NON_ECONOMIE"),
)
EXPECTED={
    "budget_resultat_cad":400167919,
    "realisation_resultat_cad":342002744,
    "ecart_resultat_cad":-58165175,
}
CONTEXT={
    "redressement_2023_cad":1825176,
    "redressement_n_est_pas_economie":True,
    "autres_organismes_non_rapproches":True,
}
GUARDS={
    "source_publique_texte_non_authentification_octets",
    "source_2024_paginee_pdf_zero_6",
    "source_donnees_page_publique_indexee",
    "source_p55h_edition_verifier_avant_certification",
    "source_mamh_non_reconciliee",
    "quatre_lignes_sans_doublon",
    "arithmetique_entiers_sans_arrondis_cache",
    "tous_ecarts_egaux_realise_moins_budget",
    "identite_resultat_budget_verifiee",
    "identite_resultat_realise_verifiee",
    "identite_resultat_ecarts_verifiee",
    "deux_classes_recettes_non_interchangeables",
    "charges_conservees_signe_budgets_et_reels",
    "aucun_ecart_comptable_assimile_economie",
    "aucun_gaspillage_inferre_d_ecart_budgetaire",
    "aucune_recette_investissement_assimilee_recette_recurrente",
    "sommaire_non_audite_non_assimile_certification",
    "redressement_2023_hors_rapprochement_2024",
    "eliminations_ville_rtc_somhac_non_monetees",
    "aucune_deduction_depuis_une_seule_page",
    "aucun_nettoyage_optimiste_d_unites",
    "aucune_comparaison_inter_regimes_automatique",
    "aucune_reduction_effectifs_et_services",
    "protection_pouvoir_achat",
    "mandats_comptable_juridique_non_signes",
    "quatre_dossiers_p54e_et_date_ouverts",
    "p54n40_p54o10_p54b96_p54c8_non_attestes",
    "aucune_economie_certifiee_cad",
    "aucune_autorisation_de_depense_ou_contact",
    "aucune_modification_sinjira",
    "aucune_fusion_main",
    "no_go_automatique",
}
INITIAL={
    "lignes_reproduites_depuis_texte_public":4,
    "copies_pdf_actuelles_authentifiees":0,
    "pieces_comparatives_mamh_rapprochees":0,
    "avis_comptables_authentifies":0,
    "mandats_signes":0,
    "economies_certifiees_cad":None,
    "dossiers_p54e_ouverts":4,
    "date_probable_non_certifiee":1,
    "taches_p54n_non_attestees":40,
    "blocages_p54o_non_leves":10,
    "controles_p54b_non_attestes":96,
    "controles_p54c_non_attestes":8,
    "decision":NO_GO,
}


def need(cond,reason):
    if not cond:
        raise ValueError(reason)


def reference_lines():
    return [
        {"code":code,"nature":kind,"budget_cad":budget,
         "realisation_cad":real,
         "ecart_realisation_moins_budget_cad":delta,
         "limite_interpretation":warning}
        for code,kind,budget,real,delta,warning in ROWS
    ]


def configuration():
    cfg=p54z.read_json(CONFIG)
    must={
        "schema_version":"P55I-1","date_reference":"2026-11-04",
        "exercice":2024,
        "source":SOURCE,
        "source_amont":["P54Q","P55F","P55G","P55H"],
        "lignes":reference_lines(),
        "identites_attendues":EXPECTED,
        "faits_contextuels_exclus":CONTEXT,
        "protections":{code:True for code in GUARDS},
        "etat_initial":INITIAL,
    }
    need(cfg==must,"P55I_REFERENTIEL_MODIFIE")
    h=p55h.configuration()
    need(h["schema_version"]=="P55H-1"
         and h["etat_initial"]["decision"]==NO_GO
         and h["etat_initial"]["copies_pdf_acquises_et_verifiees_dans_ce_jalon"]==0
         and SOURCE["url"]==p55b.expected_sources()[0]["url_officielle"]
         and p55f.configuration()["verrous_interpretation"]
             ["redressement_comparatif_2023_cad"]==1825176,
         "P55I_CHAINAGE_ET_PROVENANCE_INCOMPATIBLES")
    validate_rows(cfg["lignes"])
    return cfg


def validate_rows(rows):
    need(type(rows) is list and len(rows)==4,
         "P55I_QUATRE_LIGNES_EXIGEES")
    need(rows==reference_lines(),
         "P55I_CHAMPS_OU_VALEURS_NON_CONFORMES_AU_TEXTE_PUBLIE")
    for row in rows:
        need(type(row["budget_cad"]) is int
             and type(row["realisation_cad"]) is int
             and type(row["ecart_realisation_moins_budget_cad"]) is int
             and row["budget_cad"]>0 and row["realisation_cad"]>=0
             and row["realisation_cad"]-row["budget_cad"]==
                 row["ecart_realisation_moins_budget_cad"],
             "P55I_ECART_BRUT_NON_REPRODUCTIBLE")
    b,r,e=({x["code"]:x[key] for x in rows} for key in (
        "budget_cad","realisation_cad",
        "ecart_realisation_moins_budget_cad"))
    for values,expected in [
        (b,EXPECTED["budget_resultat_cad"]),
        (r,EXPECTED["realisation_resultat_cad"]),
        (e,EXPECTED["ecart_resultat_cad"]),
    ]:
        calc=(values["REVENUS_FONCTIONNEMENT"]
              +values["REVENUS_INVESTISSEMENT"]-values["CHARGES"])
        need(calc==expected==values["EXCEDENT_EXERCICE"],
             "P55I_IDENTITE_REVENUS_CHARGES_RESULTAT_NON_REPRODUCTIBLE")
    need(r["EXCEDENT_EXERCICE"]-b["EXCEDENT_EXERCICE"]==
         e["EXCEDENT_EXERCICE"],"P55I_IDENTITE_SOLDE_NON_REPRODUCTIBLE")
    return True


def percent(delta,budget):
    need(type(delta) is int and type(budget) is int
         and budget>0,"P55I_DIVISION_INVALIDE")
    return str((Decimal(delta)*Decimal("100")/Decimal(budget)).quantize(
        Decimal("0.1"),rounding=ROUND_HALF_UP))


def detail_rows():
    values=reference_lines()
    validate_rows(values)
    out=[]
    for x in values:
        item=dict(x)
        item["ecart_pourcentage_arrondi_une_decimale"]=percent(
            x["ecart_realisation_moins_budget_cad"],x["budget_cad"])
        item["contribution_variation_resultat_cad"]=(
            -x["ecart_realisation_moins_budget_cad"]
            if x["code"]=="CHARGES"
            else x["ecart_realisation_moins_budget_cad"]
            if x["code"]!="EXCEDENT_EXERCICE"
            else None
        )
        item["economie_nouvelle_demontree"]=False
        out.append(item)
    need(sum(row["contribution_variation_resultat_cad"] for row in out[:3])
         ==EXPECTED["ecart_resultat_cad"],
         "P55I_CONTRIBUTIONS_INCOHERENTES")
    return out


def public_report():
    rows=detail_rows()
    by={x["code"]:x for x in rows}
    return {
        "schema_version":"P55I-BILAN-PUBLIC-1","exercice":2024,
        "source_publique_texte_et_non_pieces_pdf_authentifiees":True,
        "sommaire_budget_realisation_non_audite":True,
        "lignes_reconciliees_arithmetiquement":4,
        "revenus_fonctionnement_ecart_cad":
            by["REVENUS_FONCTIONNEMENT"]["ecart_realisation_moins_budget_cad"],
        "revenus_investissement_ecart_cad":
            by["REVENUS_INVESTISSEMENT"]["ecart_realisation_moins_budget_cad"],
        "charges_ecart_cad":
            by["CHARGES"]["ecart_realisation_moins_budget_cad"],
        "variation_excédent_exercice_cad":
            by["EXCEDENT_EXERCICE"]["ecart_realisation_moins_budget_cad"],
        "concordance_identite_budget_realise":True,
        "copies_originales_authentifiees_p55h":0,
        "comparaison_mamh_expertisee":False,
        "ecarts_sont_economies_certifiees":False,
        "redressement_comparatif_2023_est_gain_2024":False,
        "eliminations_existantes_sont_economies_nouvelles":False,
        "experts_professionnels_engages":0,
        "mandats_signes":0,
        "dossiers_p54e_ouverts":4,
        "date_probable_non_certifiee":1,
        "taches_p54n_non_attestees":40,
        "blocages_p54o_non_leves":10,
        "controles_p54b_non_attestes":96,
        "controles_p54c_non_attestes":8,
        "economies_certifiees_cad":None,
        "transmission_externe_autorisee":False,
        "fusion_main_autorisee":False,
        "decision":NO_GO,
    }


def public_table():
    result={
        "schema_version":"P55I-TABLE-PUBLIQUE-1","exercice":2024,
        "source_officielle":SOURCE,
        "lignes":detail_rows(),
        "identites_comptables":EXPECTED,
        "qualification_resultat":"CALCUL_ARITHMETIQUE_SUR_TEXTE_PUBLIC_NON_AUDITE",
        "aucune_economie_affirmee":True,
        "decision":NO_GO,
    }
    need(result["identites_comptables"]["ecart_resultat_cad"]==
         sum(x["contribution_variation_resultat_cad"] for x in result["lignes"][:3]),
         "P55I_TABLE_SANS_IDENTITE")
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bilan-public")
    parser.add_argument("--table-public")
    parser.add_argument("--exiger-certification",action="store_true")
    a=parser.parse_args(argv)
    try:
        configuration()
        dest=[Path(x).expanduser().absolute() for x in (
            a.bilan_public,a.table_public) if x]
        need(len({x.resolve() for x in dest})==len(dest),
             "P55I_CHEMINS_DE_SORTIE_CONFONDUS")
        for out in dest:
            need(out.parent.is_dir() and not out.parent.is_symlink()
                 and not out.exists() and not out.is_symlink(),
                 "P55I_SORTIE_REFUSEE")
        result=public_report()
        if a.bilan_public:
            p54z.write_new(a.bilan_public,result)
        if a.table_public:
            p54z.write_new(a.table_public,public_table())
        print(json.dumps(result,sort_keys=True,ensure_ascii=False))
        return 3 if a.exiger_certification else 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError,
            json.JSONDecodeError):
        print("P55I_REFUS: ARITHMETIQUE_OU_PROVENANCE_NON_CONFORME",
              file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
