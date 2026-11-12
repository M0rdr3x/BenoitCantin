#!/usr/bin/env python3
"""P55L : corroborer 154 047 800 $ du RTC avec Ville, sans économie fictive."""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import sys

import ventiler_revenus_reciproques_nova_p55k as p55k

p55j=p55k.p55j
p54z=p55k.p54z
BASE=p55k.BASE
CONFIG=BASE/"P55L_RAPPROCHEMENT_RTC_QUOTES_PARTS_2024.json"
NO_GO=p55k.NO_GO
SOURCES={
    "ville":{
        "code":"VILLE_RF2024_S12",
        "url":"https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf",
        "rubrique":"S12_RESULTATS_DETAILLES_PAR_ORGANISMES",
        "page_imprimee":63,
        "qualification":"TEXTE_OFFICIEL_P55K_SANS_COPIE_ORIGINALE_SHA_ACTUEL",
    },
    "rtc":{
        "code":"RTC_RAPPORT_ACTIVITE_2024",
        "url":"https://www-api.rtcquebec.ca/sites/default/files/2025-06/RTC_Rapport_Activite%202024_0.pdf",
        "rubriques":[
            "ETAT_CONSOLIDE_DES_RESULTATS_S7",
            "NOTES_COMPLEMENTAIRES_NOTE_27_REVENUS_S11_P35",
            "NOTES_COMPLEMENTAIRES_NOTE_28_OPERATIONS_INTERENTITES_S11_P39",
        ],
        "date_depot":"2025-06",
        "qualification":
            "TEXTE_RAPPORT_PUBLIC_RTC_SANS_COPIE_ORIGINALE_SHA_ACTUEL_NI_CAPTURE_VISUELLE",
    },
}
AMOUNTS={
    "rtc_quotes_parts_realisees_2024_cad":154047800,
    "rtc_quotes_parts_budget_2024_cad":154047800,
    "rtc_quotes_parts_realisees_2023_cad":143131000,
    "rtc_note_28_contribution_agglomeration_2024_cad":154047800,
    "rtc_note_28_part_ville_approximative_pct":93,
    "rtc_note_28_part_ville_est_approximative":True,
    "rtc_total_revenus_realises_2024_cad":428758065,
    "rtc_total_charges_realisees_2024_cad":358727303,
    "rtc_excedent_activites_realise_2024_cad":70030762,
    "ville_s12_organismes_quotes_parts_2024_cad":154047800,
    "ville_s12_administration_quotes_parts_2024_cad":47353223,
    "ville_s12_total_consolide_quotes_parts_2024_cad":47353223,
    "ville_s12_residu_quotes_parts_2024_cad":-154047800,
    "variation_quotes_parts_rtc_2024_vs_2023_cad":10916800,
    "variation_quotes_parts_rtc_2024_vs_2023_pct_une_decimale":"7.6",
    "part_quotes_parts_revenus_rtc_2024_pct_une_decimale":"35.9",
}
MATCHES=(
    "IDENTITE_RTC_S7_ET_NOTE_27_ET_NOTE_28",
    "IDENTITE_RTC_QUOTES_PARTS_ET_VILLE_S12_ORGANISMES",
    "RESIDU_ARITHMETIQUE_VILLE_S12",
    "VARIATION_INTERANNUELLE_RTC_INFORMATIF_NON_ECONOMIE",
    "QUOTE_PARTS_RTC_DANS_REVENU_TOTAL_INFORMATIF_NON_ECONOMIE",
)
FORBIDDEN=(
    "154047800_EST_ECONOMIE_RECUPERABLE",
    "93_POURCENT_EST_CONTRIBUTION_EXACTE_NON_ARRONDIE",
    "JOURNAL_D_ELIMINATION_AUTHENTIFIE",
    "REVENUS_RTC_AJOUTABLES_AUX_REVENUS_CONSOLIDES_VILLE",
    "TOUS_RESIDUS_VILLE_SONT_RTC",
    "SOMHAC_QUOTE_PARTS_ZERO_PROUVEE_INDEPENDAMMENT",
    "TOUTES_OBLIGATIONS_RTC_SUPPRIMABLES",
)
GUARDS={
    "deux_publications_institutionnelles_distinctes",
    "rtc_contribution_2024_note_28",
    "rtc_quotes_parts_realisations_2024_s7",
    "rtc_quotes_parts_budget_2024_s7",
    "rtc_2023_comparatif_s7",
    "rtc_2023_note_28_arrondie_non_stricte",
    "ville_quotes_parts_p55k_source_textuelle",
    "egalite_exacte_rtc_ville_en_2024",
    "difference_ville_non_auto_certif_elimination",
    "ne_pas_confondre_93_percent_avec_montant_exact",
    "pct_environ_93_non_precis",
    "aucune_attribution_municipale_exacte",
    "reglement_agglomeration_2024_distinct_rtc",
    "reglement_2025_non_applique_a_2024",
    "recettes_rtc_non_sommees_au_consolide_ville",
    "aucun_double_compte_154m",
    "revenus_rtc_2024_et_charges_2024_reconcilies",
    "excedent_rtc_pas_economie",
    "reduction_couts_transport_non_derivee",
    "aucun_detriment_services_transport",
    "aucune_reduction_d_emplois",
    "aucun_effet_budgetaire_net_presume",
    "date_publication_2025_exercice_2024",
    "source_web_text_no_sha256",
    "screenshot_rtc_non_accompli",
    "pdf_rtc_plus_de_20mo_limite_p55h",
    "p55h_sources_deux_seulement",
    "pas_telechargement_automatique",
    "pas_de_donnees_personnelles",
    "pas_de_certification_professionnelle",
    "rtc_et_somhac_non_ventiles_sur_autres_postes",
    "p54e_et_date_probable_ouverts",
    "p54n40_p54o10_p54b96_p54c8_ouverts",
    "quebec_canada_souverain_deux_scenarios",
    "pas_de_contact_externe",
    "pas_de_depense",
    "pas_de_fusion_main",
    "pas_de_modification_sinjira",
    "no_go_automatique",
}
INITIAL={
    "rapports_officiels_comparables":2,
    "pdf_originaux_sha_actuels_verifies":0,
    "ecritures_reciproques_recueillies":0,
    "quote_part_rtc_montant_rapproche":154047800,
    "quote_part_rtc_qualifiee_economie":False,
    "repartition_reelle_exacte_par_municipalite_obtenue":False,
    "justificatif_somhac_distinct_obtenu":False,
    "expertises_professionnelles_authentifiees":0,
    "mandats_professionnels_signes":0,
    "observations_p54e_ouvertes":4,
    "date_probable_non_certifiee":1,
    "taches_p54n_non_attestees":40,
    "blocages_p54o_non_leves":10,
    "controles_p54b_non_attestes":96,
    "controles_p54c_non_attestes":8,
    "economies_certifiees_cad":None,
    "decision":NO_GO,
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def pct(numerator, denominator):
    require(type(numerator) is int and type(denominator) is int
            and numerator >= 0 and denominator > 0,
            "P55L_POURCENTAGE_INVALIDE")
    return str((Decimal(numerator)*100/Decimal(denominator)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP))


def verify_amounts(m):
    require(type(m) is dict and m==AMOUNTS,
            "P55L_MONTANTS_MODIFIES")
    q=m["rtc_quotes_parts_realisees_2024_cad"]
    require(type(q) is int and
            q==m["rtc_quotes_parts_budget_2024_cad"]
            ==m["rtc_note_28_contribution_agglomeration_2024_cad"]
            ==m["ville_s12_organismes_quotes_parts_2024_cad"]
            ==-m["ville_s12_residu_quotes_parts_2024_cad"],
            "P55L_QUOTES_PARTS_NE_CORRESPONDENT_PAS")
    require(m["ville_s12_administration_quotes_parts_2024_cad"]
            +m["ville_s12_organismes_quotes_parts_2024_cad"]
            +m["ville_s12_residu_quotes_parts_2024_cad"]
            ==m["ville_s12_total_consolide_quotes_parts_2024_cad"],
            "P55L_IDENTITE_VILLE_NON_VERIFIEE")
    require(q-m["rtc_quotes_parts_realisees_2023_cad"]
            ==m["variation_quotes_parts_rtc_2024_vs_2023_cad"]
            and pct(q-m["rtc_quotes_parts_realisees_2023_cad"],
                    m["rtc_quotes_parts_realisees_2023_cad"])
                ==m["variation_quotes_parts_rtc_2024_vs_2023_pct_une_decimale"],
            "P55L_VARIATION_INTERANNUELLE_INCOHERENTE")
    require(m["rtc_total_revenus_realises_2024_cad"]
            -m["rtc_total_charges_realisees_2024_cad"]
            ==m["rtc_excedent_activites_realise_2024_cad"]
            and pct(q,m["rtc_total_revenus_realises_2024_cad"])
                ==m["part_quotes_parts_revenus_rtc_2024_pct_une_decimale"],
            "P55L_RESULTAT_RTC_INCOHERENT")
    require(type(m["rtc_note_28_part_ville_approximative_pct"]) is int
            and m["rtc_note_28_part_ville_approximative_pct"] == 93
            and m["rtc_note_28_part_ville_est_approximative"] is True,
            "P55L_PART_DE_VILLE_DOIT_RESTER_APPROXIMATIVE")
    return True


def configuration():
    cfg=p54z.read_json(CONFIG)
    require(cfg=={
        "schema_version":"P55L-1",
        "date_reference":"2026-11-04",
        "exercice":2024,
        "sources":SOURCES,
        "montants":AMOUNTS,
        "rapprochements_autorises":list(MATCHES),
        "conclusions_interdites":list(FORBIDDEN),
        "protections":{x:True for x in GUARDS},
        "etat_initial":INITIAL,
    },"P55L_REFERENTIEL_NON_CONFORME")
    upstream=p55k.configuration()
    require(upstream["schema_version"]=="P55K-1"
            and upstream["etat_initial"]["decision"]==NO_GO
            and upstream["source"]["url"]==SOURCES["ville"]["url"]
            and upstream["totaux_et_concentration"]["residu_quotes_parts_cad"]
                ==AMOUNTS["ville_s12_residu_quotes_parts_2024_cad"],
            "P55L_CHAINAGE_P55K_INCOHERENT")
    upstream_row=next(r for r in upstream["lignes"]
                      if r["code"]=="QUOTES_PARTS")
    require(upstream_row["organismes_controles_partenariats_cad"]==
                AMOUNTS["ville_s12_organismes_quotes_parts_2024_cad"]
            and upstream_row["administration_municipale_cad"]==
                AMOUNTS["ville_s12_administration_quotes_parts_2024_cad"]
            and upstream_row["total_consolide_cad"]==
                AMOUNTS["ville_s12_total_consolide_quotes_parts_2024_cad"],
            "P55L_SOURCE_VILLE_MODIFIEE")
    verify_amounts(cfg["montants"])
    return cfg


def public_table():
    verify_amounts(AMOUNTS)
    return {
        "schema_version":"P55L-TABLE-PUBLIQUE-1","exercice":2024,
        "sources":SOURCES,
        "preuves_documentaires":[
            {"code":"RTC_S7_REALISATIONS","montant_cad":AMOUNTS["rtc_quotes_parts_realisees_2024_cad"],
             "qualification":"REVENU_RTC_PUBLIE_NON_GAINS"},
            {"code":"RTC_S11_NOTE27_REVENUS","montant_cad":AMOUNTS["rtc_quotes_parts_realisees_2024_cad"],
             "qualification":"CONTRIBUTION_AGGLOMERATION_PUBLIEE"},
            {"code":"RTC_S11_NOTE28_INTERENTITES","montant_cad":AMOUNTS["rtc_note_28_contribution_agglomeration_2024_cad"],
             "qualification":"CONTRIBUTION_RECUE_DE_AGGLOMERATION"},
            {"code":"VILLE_S12_ORGANISMES","montant_cad":AMOUNTS["ville_s12_organismes_quotes_parts_2024_cad"],
             "qualification":"COLONNE_ORGANISMES_NON_VENTILEE"},
        ],
        "montants":AMOUNTS,
        "niveau_confirmation":"EGALITE_ENTRE_MONTANTS_PUBLIES_PAR_DEUX_EMETTEURS",
        "ecriture_d_elimination_independamment_verifiee":False,
        "pourcentage_part_ville_exact":False,
        "montant_nouvelle_economie_demontre":None,
        "decision":NO_GO,
    }


def public_report():
    verify_amounts(AMOUNTS)
    return {
        "schema_version":"P55L-BILAN-PUBLIC-1","exercice":2024,
        "sources_publiques_organismes_distincts":2,
        "concordance_montant_quotes_parts_rtc_ville":True,
        "montant_quotes_parts_2024_cad":
            AMOUNTS["rtc_quotes_parts_realisees_2024_cad"],
        "augmentation_par_rapport_2023_cad":
            AMOUNTS["variation_quotes_parts_rtc_2024_vs_2023_cad"],
        "augmentation_par_rapport_2023_pourcent":
            AMOUNTS["variation_quotes_parts_rtc_2024_vs_2023_pct_une_decimale"],
        "part_recettes_rtc_pourcent":
            AMOUNTS["part_quotes_parts_revenus_rtc_2024_pct_une_decimale"],
        "part_contribution_ville_approximative_pourcent":93,
        "repartition_exacte_contribution_municipale_connue":False,
        "part_somhac_et_autres_ecarts_etablie":False,
        "rapprochement_ecritures_comptables_independamment_verifie":False,
        "copies_pdf_originales_sha_actuel_verifiees":0,
        "avis_professionnels_authentifies":0,
        "mandats_signes":0,
        "economies_nouvelles_cad":None,
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


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bilan-public")
    p.add_argument("--table-public")
    p.add_argument("--exiger-certification",action="store_true")
    a=p.parse_args(argv)
    try:
        configuration()
        destinations=[Path(value).expanduser().absolute() for value in
                      (a.bilan_public,a.table_public) if value]
        require(len({d.resolve() for d in destinations})==len(destinations),
                "P55L_DESTINATIONS_NON_DISTINCTES")
        for dest in destinations:
            require(dest.parent.is_dir() and not dest.parent.is_symlink()
                    and not dest.exists() and not dest.is_symlink(),
                    "P55L_DESTINATION_INVALIDE")
        report=public_report()
        if a.bilan_public:
            p54z.write_new(a.bilan_public,report)
        if a.table_public:
            p54z.write_new(a.table_public,public_table())
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 3 if a.exiger_certification else 0
    except (ValueError,OSError,KeyError,TypeError,
            json.JSONDecodeError,UnicodeError):
        print("P55L_REFUS: RAPPORT_RTC_OU_CHAINE_NON_CONFORME",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
