#!/usr/bin/env python3
"""P55K — décomposer les revenus de fonctionnement 2024 sans gains inventés."""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import sys

import rapprocher_perimetres_et_conciliation_nova_p55j as p55j

p55i=p55j.p55i
p54z=p55j.p54z
BASE=p55j.BASE
CONFIG=BASE/"P55K_DETAIL_REVENUS_RECIPROQUES_2024.json"
NO_GO=p55j.NO_GO

SOURCE={
    "document":"RAPPORT_FINANCIER_VILLE_QUEBEC_2024",
    "url":"https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf",
    "page_pdf_index_zero_ventilation":62,
    "page_imprimee_ventilation":63,
    "page_pdf_index_zero_methodes":34,
    "page_imprimee_methodes":35,
    "page_pdf_index_zero_budget":196,
    "page_imprimee_budget":197,
    "niveau_preuve_ventilation":
        "EXTRACTION_TEXTE_DU_PDF_OFFICIEL_NON_CONTROLEE_VISUELLEMENT_S12",
    "niveau_preuve_methodes":"CAPTURE_VISUELLE_PDF_OFFICIEL",
    "etat_original_local":"NON_ACQUIS_NON_AUTHENTIFIE",
}
ROWS=(
    ("TAXES",1296686206,0,1295208647,-1477559,"A_QUALIFIER_SUR_ECRITURES"),
    ("COMPENSATIONS_TENANT_LIEU_TAXES",134445067,0,132702160,
     -1742907,"A_QUALIFIER_SUR_ECRITURES"),
    ("QUOTES_PARTS",47353223,154047800,47353223,
     -154047800,"COMPATIBLE_NEUTRALISATION_RECIPROQUE_A_VERIFIER"),
    ("TRANSFERTS",228223969,100926706,319764739,
     -9385936,"A_QUALIFIER_SUR_ECRITURES"),
    ("SERVICES_RENDUS",96508463,95138908,188160353,
     -3487018,"A_QUALIFIER_SUR_ECRITURES"),
    ("IMPOSITION_DE_DROITS",97261483,0,97261483,0,"AUCUN_RESIDU_CALCULE"),
    ("AMENDES_ET_PENALITES",19294230,0,19294230,0,"AUCUN_RESIDU_CALCULE"),
    ("REVENUS_PLACEMENTS",46576373,350943,46927316,0,
     "AUCUN_RESIDU_CALCULE"),
    ("AUTRES_REVENUS_INTERETS",21438065,3754116,23941951,
     -1250230,"A_QUALIFIER_SUR_ECRITURES"),
    ("AUTRES_REVENUS",20569227,475246,15993752,
     -5050721,"A_QUALIFIER_SUR_ECRITURES"),
)
TOTALS={
    "administration_revenus_fonctionnement_cad":2008356306,
    "organismes_revenus_fonctionnement_cad":354693719,
    "total_revenus_fonctionnement_consolides_cad":2186607854,
    "residu_revenus_fonctionnement_cad":-176442171,
    "residu_quotes_parts_cad":-154047800,
    "part_quotes_parts_dans_abs_residu_pourcent_arrondi_une_decimale":"87.3",
    "autres_residus_cad":-22394371,
    "organismes_individuels_rtc_somhac_ventiles":False,
}
TASKS=[
    ("K01","Relever_la_nature_des_quotes_parts_154047800",
     "DETAIL_TRANSACTIONS_RECIPROQUES_ET_NOTES_COMPTABLES",
     "A_EXAMINER_PAR_COMPTABLE"),
    ("K02","Ventiler_les_quotes_parts_par_RTC_et_SOMHAC",
     "GRAND_LIVRE_ET_ETATS_SEPARES_DE_CHAQUE_ORGANISME",
     "A_EXAMINER_PAR_COMPTABLE"),
    ("K03","Identifier_autres_residus_22394371",
     "ECRITURES_D_ELIMINATION_RECLASSEMENT_ET_BOUCLAGE",
     "A_EXAMINER_PAR_COMPTABLE"),
    ("K04","Etablir_perimetre_legal_et_comptabilite_agglomeration_local",
     "REGLES_MAMH_ET_RESOLUTIONS_BUDGETAIRES_2024",
     "A_EXAMINER_PAR_JURISTE_ET_COMPTABLE"),
    ("K05","Qualifier_effet_net_et_recurrence_sans_emplois_services",
     "BUDGET_OPERATIONS_SERVICES_AFFECTATIONS_ET_CONTROLE_INDEPENDANT",
     "A_EXAMINER_PAR_COMPTABLE"),
]
GUARDS={
    "premiere_source_pdf_2024_officielle",
    "page_63_imprimee_pdf_62_extraction_texte",
    "screenshot_page_62_non_obtenu",
    "methodes_comptables_page_35_capture_visuelle",
    "note_budget_197_capture_visuelle",
    "rtc_somhac_seuls_organismes_controles_declares",
    "agglomeration_et_local_ne_sont_pas_deux_societes",
    "regroupement_organismes_non_ventile_par_rtc_somhac",
    "dix_lignes_revenus_fonctionnement_reproduites",
    "total_admin_somme_des_dix_lignes",
    "total_org_somme_des_dix_lignes",
    "total_consolide_somme_des_dix_lignes",
    "residu_calcul_respecte_trois_perimetres",
    "residu_176442171_doit_egaler_p55j",
    "quotes_parts_154047800_egal_org_colonne",
    "concentration_87_3_pourcent_avec_decimal",
    "aucune_attribution_sans_ecriture_reciproque",
    "aucune_attribution_rtc_vs_somhac",
    "residus_de_taxes_sans_org_identifie_non_qualifies",
    "residus_zero_ne_prouvent_pas_absence_transactions",
    "aucune_economie_certifiee_sur_residus",
    "p55i_p55j_herites_et_controles",
    "pas_d_absorption_du_budget_d_agglomeration",
    "aucun_nouveau_gain_depuis_elimination_existante",
    "surplus_fiscal_n_est_pas_tresorerie_libre",
    "aucune_copie_pdf_locale_sha_authentifiee",
    "notes_visuelles_ne_certifient_pas_ligne_s12",
    "exiger_avis_cpa_et_pieces_justificatives",
    "avis_juridiques_non_signes",
    "protections_emplois_services",
    "protection_pouvoir_achat",
    "distinction_deux_scenarios_politiques",
    "p54e_quatre_dossiers_et_date_non_clos",
    "p54n40_p54o10_p54b96_p54c8_en_suspens",
    "pas_de_contact_avec_institutions",
    "pas_de_contrat_ni_depense",
    "ne_pas_modifier_sinjira",
    "aucune_fusion_main",
    "no_go_automatique",
}
INITIAL={
    "operations_reciproques_detaillees_obtenues":0,
    "organismes_separes_et_expertises":0,
    "copies_pdf_origine_verifiees_sha_2024":0,
    "tests_avec_chiffres_publies_non_certifiant":0,
    "attestations_professionnelles":0,
    "mandats_signes":0,
    "economies_certifiees_cad":None,
    "observations_p54e_ouvertes":4,
    "date_probable_non_certifiee":1,
    "taches_p54n_non_attestees":40,
    "blocages_p54o_non_leves":10,
    "controles_p54b_non_attestes":96,
    "controles_p54c_non_attestes":8,
    "decision":NO_GO,
}

def need(value,reason):
    if not value:
        raise ValueError(reason)


def reference_lines():
    return [{
        "code":code,"administration_municipale_cad":a,
        "organismes_controles_partenariats_cad":o,
        "total_consolide_cad":t,
        "residu_total_moins_somme_cad":d,
        "interpretation_provisoire":kind,
    } for code,a,o,t,d,kind in ROWS]


def review_tasks():
    return [{
        "code":code,"titre":title,"preuve_attendue":evidence,
        "statut":status,
    } for code,title,evidence,status in TASKS]


def percent_rounded(numerator,denominator):
    need(type(numerator) is int and type(denominator) is int
         and numerator>=0 and denominator>0,
         "P55K_DIVISION_INVALIDE")
    return str((Decimal(numerator)*100/Decimal(denominator)).quantize(
        Decimal("0.1"),rounding=ROUND_HALF_UP))


def validate_lines(rows,totals):
    need(type(rows) is list and rows==reference_lines()
         and type(totals) is dict and totals==TOTALS,
         "P55K_LIGNES_OU_TOTAUX_NON_CONFORMES")
    fields=("administration_municipale_cad",
            "organismes_controles_partenariats_cad",
            "total_consolide_cad","residu_total_moins_somme_cad")
    need(len({r["code"] for r in rows})==10,"P55K_CODES_DUPLIQUES")
    for r in rows:
        need(all(type(r[k]) is int for k in fields)
             and r["total_consolide_cad"]-
                 r["administration_municipale_cad"]-
                 r["organismes_controles_partenariats_cad"]==
                 r["residu_total_moins_somme_cad"],
             "P55K_RESIDU_INCOHERENT")
    sums={key:sum(r[key] for r in rows) for key in fields}
    need(sums["administration_municipale_cad"]==
         totals["administration_revenus_fonctionnement_cad"]
         and sums["organismes_controles_partenariats_cad"]==
         totals["organismes_revenus_fonctionnement_cad"]
         and sums["total_consolide_cad"]==
         totals["total_revenus_fonctionnement_consolides_cad"]
         and sums["residu_total_moins_somme_cad"]==
         totals["residu_revenus_fonctionnement_cad"],
         "P55K_TOTAUX_NE_BOUGLENT_PAS")
    quotes=next(r for r in rows if r["code"]=="QUOTES_PARTS")
    need(quotes["residu_total_moins_somme_cad"]==
         totals["residu_quotes_parts_cad"]
         ==-quotes["organismes_controles_partenariats_cad"],
         "P55K_QUOTES_PARTS_NON_RECONCILIEES")
    need(sums["residu_total_moins_somme_cad"]-
         quotes["residu_total_moins_somme_cad"]==
         totals["autres_residus_cad"],"P55K_AUTRES_RESIDUS_INCOHERENTS")
    need(percent_rounded(abs(quotes["residu_total_moins_somme_cad"]),
         abs(sums["residu_total_moins_somme_cad"]))==
         totals["part_quotes_parts_dans_abs_residu_pourcent_arrondi_une_decimale"],
         "P55K_CONCENTRATION_INCOHERENTE")
    return sums


def configuration():
    cfg=p54z.read_json(CONFIG)
    required={
        "schema_version":"P55K-1",
        "date_reference":"2026-11-04",
        "exercice":2024,
        "source":SOURCE,
        "references":["P54Q","P55H","P55I","P55J"],
        "lignes":reference_lines(),
        "totaux_et_concentration":TOTALS,
        "travaux_humains_requis":review_tasks(),
        "protections":{k:True for k in GUARDS},
        "etat_initial":INITIAL,
    }
    need(cfg==required,"P55K_REFERENTIEL_MODIFIE")
    parent=p55j.configuration()
    need(parent["schema_version"]=="P55J-1"
         and parent["source"]["url_officielle"]==SOURCE["url"]
         and parent["lignes"][0]["administration_municipale_cad"]==
             TOTALS["administration_revenus_fonctionnement_cad"]
         and parent["lignes"][0]["organismes_controles_partenariats_cad"]==
             TOTALS["organismes_revenus_fonctionnement_cad"]
         and parent["lignes"][0]["total_consolide_cad"]==
             TOTALS["total_revenus_fonctionnement_consolides_cad"]
         and parent["lignes"][0]["residu_consolidation_cad"]==
             TOTALS["residu_revenus_fonctionnement_cad"]
         and parent["etat_initial"]["decision"]==NO_GO
         and parent["etat_initial"]["copies_pdf_verifiees_par_sha_actuel"]==0,
         "P55K_PARENT_P55J_NON_CONFORME")
    validate_lines(cfg["lignes"],cfg["totaux_et_concentration"])
    return cfg


def public_report():
    validate_lines(reference_lines(),TOTALS)
    return {
        "schema_version":"P55K-BILAN-PUBLIC-1",
        "exercice":2024,
        "lignes_revenus_fonctionnement_reconciliees":10,
        "administration_municipale_revenus_cad":
            TOTALS["administration_revenus_fonctionnement_cad"],
        "organismes_groupes_revenus_cad":
            TOTALS["organismes_revenus_fonctionnement_cad"],
        "total_consolide_revenus_cad":
            TOTALS["total_revenus_fonctionnement_consolides_cad"],
        "residu_global_revenus_cad":
            TOTALS["residu_revenus_fonctionnement_cad"],
        "residu_quotes_parts_cad":TOTALS["residu_quotes_parts_cad"],
        "concentration_quotes_parts_pourcent":
            TOTALS["part_quotes_parts_dans_abs_residu_pourcent_arrondi_une_decimale"],
        "residu_hors_quotes_parts_cad":TOTALS["autres_residus_cad"],
        "quotes_parts_qualifiees_par_ecritures":False,
        "part_rtc_et_somhac_seperee_disponible":False,
        "nombre_categories_a_qualifier_humainement":
            sum(row["residu_total_moins_somme_cad"]!=0
                for row in reference_lines()),
        "pages_methodes_visuelles":2,
        "page_ventilation_s12_verifiee_visuellement":False,
        "copies_pdf_authentifiees_sha_actuel":0,
        "rapprochement_d_ecritures_reelles_obtenu":False,
        "attestations_professionnelles":0,
        "mandats_signes":0,
        "dossiers_p54e_ouverts":4,
        "date_probable_non_certifiee":1,
        "taches_p54n_non_attestees":40,
        "blocages_p54o_non_leves":10,
        "controles_p54b_non_attestes":96,
        "controles_p54c_non_attestes":8,
        "ecarts_sont_economies_certifiees":False,
        "economies_certifiees_cad":None,
        "transmission_externe_autorisee":False,
        "fusion_main_autorisee":False,
        "decision":NO_GO,
    }


def public_table():
    validate_lines(reference_lines(),TOTALS)
    return {
        "schema_version":"P55K-TABLE-PUBLIQUE-1",
        "exercice":2024,
        "source":SOURCE,
        "lignes":reference_lines(),
        "totaux_et_concentration":TOTALS,
        "travaux_humains_requis":review_tasks(),
        "interpretation":
            "DIFFERENCES_ENTRE_PERIMETRES_A_QUALIFIER_SANS_GAINS_AUTOMATIQUES",
        "confirmation_comptable_recue":False,
        "decision":NO_GO,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bilan-public")
    parser.add_argument("--table-public")
    parser.add_argument("--exiger-certification",action="store_true")
    a=parser.parse_args(argv)
    try:
        configuration()
        outputs=[Path(x).expanduser().absolute() for x in (
            a.bilan_public,a.table_public) if x]
        need(len(set(p.resolve() for p in outputs))==len(outputs),
             "P55K_SORTIES_DUPLIQUEES")
        for p in outputs:
            need(p.parent.is_dir() and not p.parent.is_symlink()
                 and not p.exists() and not p.is_symlink(),
                 "P55K_SORTIE_EXISTANTE_OU_INVALIDE")
        summary=public_report()
        if a.bilan_public:
            p54z.write_new(a.bilan_public,summary)
        if a.table_public:
            p54z.write_new(a.table_public,public_table())
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        return 3 if a.exiger_certification else 0
    except (ValueError,OSError,KeyError,TypeError,
            json.JSONDecodeError,UnicodeError):
        print("P55K_REFUS: DONNEES_OU_CHAINE_NON_CONFORMES",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
