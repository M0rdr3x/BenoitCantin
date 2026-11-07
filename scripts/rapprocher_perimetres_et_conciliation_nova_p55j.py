#!/usr/bin/env python3
"""P55J — rapprocher périmètres Ville/organismes et pont fiscal sans économies."""
import argparse
import json
from pathlib import Path
import sys

import rapprocher_sommaire_budgetaire_nova_p55i as p55i

p55h=p55i.p55h
p55g=p55i.p55g
p55b=p55i.p55b
p54z=p55i.p54z
BASE=p55i.BASE
CONFIG=BASE/"P55J_RAPPROCHEMENT_PERIMETRES_ET_CONCILIATION_2024.json"
NO_GO=p55i.NO_GO
SOURCE={
    "institution":"VILLE_DE_QUEBEC",
    "url_officielle":
        "https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf",
    "pages_pdf_index_zero":[6,12],
    "pages_imprimees":[7,13],
    "attestation":"LECTURE_VISUELLE_PAGES_PDF_PAR_NAVIGATEUR_SANS_SHA_ACTUEL",
    "libelle_page_13":"SOMMAIRE_RESULTATS_A_FINS_FISCALES_CONSOLIDES",
    "note_perimetre":
        "TOTAL_CONSOLIDE_EXCLUT_OPERATIONS_ENTRE_ADMINISTRATION_ET_ORGANISMES",
}
ROWS=(
    ("REVENUS_FONCTIONNEMENT",2008356306,354693719,2186607854,
     -176442171,"RECETTES_FONCTIONNEMENT"),
    ("REVENUS_INVESTISSEMENT",152907248,110071948,262872891,
     -106305,"RECETTES_INVESTISSEMENT"),
    ("REVENUS_TOTAUX",2161263554,464765667,2449480745,
     -176548476,"SOMME_RECETTES"),
    ("CHARGES",1920652747,365431466,2107478001,
     -178606212,"CHARGES_COMPTABLES"),
    ("EXCEDENT_ACTIVITES",240610807,99334201,342002744,
     2057736,"RESULTAT_ACTIVITES"),
    ("FONCTIONNEMENT_AVANT_CONCILIATION",87703559,-10737747,79129853,
     2164041,"SOLDE_AVANT_CONCILIATION_FISCALE"),
    ("ELEMENTS_CONCILIATION_FISCALE",10556966,42376268,50206104,
     -2727130,"AJUSTEMENTS_FISCAUX"),
    ("EXCEDENT_FONCTIONNEMENT_FISCAL",98260525,31638521,129335957,
     -563089,"SOLDE_FISCAL_APRES_CONCILIATION"),
)
BRIDGE={
    "excedent_comptable_budget_cad":400167919,
    "revenus_investissement_budget_cad":403091050,
    "fonctionnement_avant_conciliation_budget_cad":-2923131,
    "elements_conciliation_budget_cad":2923131,
    "excedent_fonctionnement_fiscal_budget_cad":0,
    "excedent_comptable_realise_cad":342002744,
    "revenus_investissement_realises_cad":262872891,
    "fonctionnement_avant_conciliation_realise_cad":79129853,
    "elements_conciliation_realises_cad":50206104,
    "excedent_fonctionnement_fiscal_realise_cad":129335957,
    "variation_fonctionnement_avant_conciliation_cad":82052984,
    "variation_elements_conciliation_cad":47282973,
    "variation_fiscal_cad":129335957,
}
BLOCKED=(
    "RESIDU_CONSOLIDATION_EST_ECONOMIE",
    "RESIDU_EST_INTEGRALEMENT_UNE_ELIMINATION_CERTIFIEE",
    "EXCEDENT_FISCAL_EST_TRESORERIE_LIBRE",
    "SURPLUS_FISCAL_EST_GAIN_PROJET_NOVA",
)
GUARDS={
    "source_page_7_capture_visuelle_site_officiel",
    "source_page_13_capture_visuelle_site_officiel",
    "aucune_copie_pdf_sha_actuel_verifiee",
    "source_mamh_second_pdf_non_reliee",
    "colonnes_administration_organismes_total_distinctes",
    "tous_residus_calcules_total_moins_somme",
    "aucun_residu_presenté_economie",
    "aucun_residu_qualifie_automatiquement_elimination",
    "pas_de_double_compte_organismes_et_ville",
    "resultats_excedent_non_tresorerie_libre",
    "ecarts_fiscaux_non_assimiles_economies",
    "budget_municipal_non_additionne_au_consolide",
    "reconciliation_somme_revenus_verifiee",
    "reconciliation_somme_charges_verifiee",
    "reconciliation_excedent_activites_verifiee",
    "reconciliation_conciliation_verifiee",
    "reconciliation_fiscal_2024_verifiee",
    "reconciliation_budget_fiscal_2024_verifiee",
    "reconciliation_variations_budget_fiscal_verifiee",
    "rapport_p55i_en_amont_non_modifie",
    "trace_page_methode_non_certifiante",
    "document_pdf_non_copie_dans_git",
    "aucun_mandat_cpa_ni_juridique_signe",
    "dossiers_p54e_et_date_probable_ouverts",
    "p54n_40_p54o_10_p54b_96_p54c_8_non_attestes",
    "redressement_2023_non_economie_2024",
    "protection_effectifs_et_services",
    "protection_pouvoir_achat",
    "regimes_quebec_canada_et_souverain_distincts",
    "aucun_contact_ou_engagement_depense",
    "aucune_transmission_automatique",
    "aucune_fusion_main",
    "sinjira_inchange",
    "no_go_automatique",
}
INITIAL={
    "pages_controlees_visuellement_sur_site_officiel":2,
    "copies_pdf_verifiees_par_sha_actuel":0,
    "lignes_de_perimetre_a_qualifier":8,
    "avis_independants_authentifies":0,
    "mandats_professionnels_signes":0,
    "economies_certifiees_cad":None,
    "dossiers_p54e_ouverts":4,
    "date_probable_non_certifiee":1,
    "taches_p54n_non_attestees":40,
    "blocages_p54o_non_leves":10,
    "controles_p54b_non_attestes":96,
    "controles_p54c_non_attestes":8,
    "decision":NO_GO,
}


def need(cond,why):
    if not cond:
        raise ValueError(why)


def reference_rows():
    return [
        {
            "code":code,"categorie":kind,
            "administration_municipale_cad":administration,
            "organismes_controles_partenariats_cad":organismes,
            "total_consolide_cad":total,
            "residu_consolidation_cad":residual,
        }
        for code,administration,organismes,total,residual,kind in ROWS
    ]


def must_match_source():
    parent=p55i.configuration()
    h=p55h.configuration()
    need(parent["schema_version"]=="P55I-1"
         and h["schema_version"]=="P55H-1"
         and parent["etat_initial"]["decision"]==NO_GO
         and parent["identites_attendues"]["realisation_resultat_cad"]
             ==342002744
         and parent["source"]["pdf_index_zero"]==6
         and h["etat_initial"]["copies_pdf_acquises_et_verifiees_dans_ce_jalon"]==0
         and SOURCE["url_officielle"]==parent["source"]["url"],
         "P55J_CHAINAGE_P55I_ET_P55H_INVALIDES")
    return parent


def configuration():
    cfg=p54z.read_json(CONFIG)
    expected={
        "schema_version":"P55J-1",
        "date_reference":"2026-11-04","exercice":2024,
        "source":SOURCE,
        "dependances":["P54Q","P55H","P55I"],
        "lignes":reference_rows(),
        "pont_fiscal_budget_realise":BRIDGE,
        "interpretations_bloquees":list(BLOCKED),
        "protections":{guard:True for guard in GUARDS},
        "etat_initial":INITIAL,
    }
    need(cfg==expected,"P55J_REFERENTIEL_MODIFIE")
    must_match_source()
    validate_table(cfg["lignes"],cfg["pont_fiscal_budget_realise"])
    return cfg


def validate_table(rows,bridge):
    need(type(rows) is list and rows==reference_rows()
         and type(bridge) is dict and bridge==BRIDGE,
         "P55J_TABLEAU_OU_PONT_NON_CONFORME")
    fields=(
        "administration_municipale_cad",
        "organismes_controles_partenariats_cad",
        "total_consolide_cad",
        "residu_consolidation_cad",
    )
    for row in rows:
        need(all(type(row[k]) is int for k in fields)
             and row["total_consolide_cad"]-
                 row["administration_municipale_cad"]-
                 row["organismes_controles_partenariats_cad"]==
                 row["residu_consolidation_cad"],
             "P55J_RESIDU_CONSOLIDATION_ERRONE")
    r={row["code"]:row for row in rows}
    for col in fields:
        need(r["REVENUS_FONCTIONNEMENT"][col]
             +r["REVENUS_INVESTISSEMENT"][col]==r["REVENUS_TOTAUX"][col],
             "P55J_RECETTES_SOMME_INCORRECTE")
        need(r["REVENUS_TOTAUX"][col]-r["CHARGES"][col]==
             r["EXCEDENT_ACTIVITES"][col],
             "P55J_IDENTITE_ACTIVITES_INCORRECTE")
        need(r["EXCEDENT_ACTIVITES"][col]-r["REVENUS_INVESTISSEMENT"][col]==
             r["FONCTIONNEMENT_AVANT_CONCILIATION"][col],
             "P55J_IDENTITE_FONCTIONNEMENT_INCORRECTE")
        need(r["FONCTIONNEMENT_AVANT_CONCILIATION"][col]
             +r["ELEMENTS_CONCILIATION_FISCALE"][col]==
             r["EXCEDENT_FONCTIONNEMENT_FISCAL"][col],
             "P55J_IDENTITE_FISCALE_INCORRECTE")
    # The fiscal bridge has distinct budget and actual perimeters.
    need(all(type(v) is int for v in bridge.values()),
         "P55J_PONT_NON_ENTIER")
    need(bridge["excedent_comptable_budget_cad"]
         -bridge["revenus_investissement_budget_cad"]==
         bridge["fonctionnement_avant_conciliation_budget_cad"],
         "P55J_PONT_BUDGET_COMPTABLE_INCORRECT")
    need(bridge["fonctionnement_avant_conciliation_budget_cad"]
         +bridge["elements_conciliation_budget_cad"]==
         bridge["excedent_fonctionnement_fiscal_budget_cad"]==0,
         "P55J_PONT_BUDGET_FISCAL_INCORRECT")
    need(bridge["excedent_comptable_realise_cad"]
         -bridge["revenus_investissement_realises_cad"]==
         bridge["fonctionnement_avant_conciliation_realise_cad"],
         "P55J_PONT_REEL_COMPTABLE_INCORRECT")
    need(bridge["fonctionnement_avant_conciliation_realise_cad"]
         +bridge["elements_conciliation_realises_cad"]==
         bridge["excedent_fonctionnement_fiscal_realise_cad"],
         "P55J_PONT_REEL_FISCAL_INCORRECT")
    need(bridge["fonctionnement_avant_conciliation_realise_cad"]
         -bridge["fonctionnement_avant_conciliation_budget_cad"]==
         bridge["variation_fonctionnement_avant_conciliation_cad"],
         "P55J_VARIATION_FONCTIONNEMENT_INCORRECTE")
    need(bridge["elements_conciliation_realises_cad"]
         -bridge["elements_conciliation_budget_cad"]==
         bridge["variation_elements_conciliation_cad"],
         "P55J_VARIATION_CONCILIATION_INCORRECTE")
    need(bridge["variation_fonctionnement_avant_conciliation_cad"]
         +bridge["variation_elements_conciliation_cad"]==
         bridge["variation_fiscal_cad"]==
         bridge["excedent_fonctionnement_fiscal_realise_cad"]-
         bridge["excedent_fonctionnement_fiscal_budget_cad"],
         "P55J_PONT_VARIATIONS_INCORRECT")
    need(
        r["REVENUS_FONCTIONNEMENT"]["total_consolide_cad"]==
            p55i.ROWS[0][3]
        and r["REVENUS_INVESTISSEMENT"]["total_consolide_cad"]==
            p55i.ROWS[1][3]
        and r["CHARGES"]["total_consolide_cad"]==p55i.ROWS[2][3]
        and r["EXCEDENT_ACTIVITES"]["total_consolide_cad"]==
            p55i.ROWS[3][3],
        "P55J_SOLDES_DIVERGENTS_P55I",
    )
    return True


def explanations():
    return [
        {
            "action":"VERIFIER_PERIMETRES_RTC_SOMHAC_ET_PARTENARIATS",
            "statut":"A_INSTRUIRE_HUMAINEMENT",
            "preuve":"DETAIL_ENTITES_ET_OPERATIONS_RECIPROQUES",
        },
        {
            "action":"QUALIFIER_RESIDUS_AJUSTEMENTS_ELIMINATIONS",
            "statut":"A_INSTRUIRE_HUMAINEMENT",
            "preuve":"GRAND_LIVRE_ET_ECRITURES_CONSOLIDATION",
        },
        {
            "action":"QUALIFIER_AFFECTATIONS_ET_RESTRICTIONS_EXCEDENT_FISCAL",
            "statut":"A_INSTRUIRE_HUMAINEMENT",
            "preuve":"ETAT_DES_RESERVES_ET_MANDATS",
        },
        {
            "action":"OBTENIR_ET_VERIFIER_LES_DEUX_EDITIONS_PDF_P55H",
            "statut":"A_INSTRUIRE_HUMAINEMENT",
            "preuve":"SHA_ACTUEL_ET_REVUE_VISUELLE",
        },
    ]


def public_report():
    validate_table(reference_rows(),BRIDGE)
    return {
        "schema_version":"P55J-BILAN-PUBLIC-1",
        "exercice":2024,
        "pages_officielles_controlees_visuellement":2,
        "copies_pdf_verifiees_par_sha_actuel":0,
        "lignes_de_perimetre_rapprochees":8,
        "ecart_recettes_consolidation_derive_cad":
            reference_rows()[2]["residu_consolidation_cad"],
        "ecart_charges_consolidation_derive_cad":
            reference_rows()[3]["residu_consolidation_cad"],
        "ecart_resultat_consolidation_derive_cad":
            reference_rows()[4]["residu_consolidation_cad"],
        "residus_expliques_et_attestes_par_expert":0,
        "total_resultat_comptable_consolide_cad":342002744,
        "resultat_fonctionnement_avant_conciliation_cad":79129853,
        "conciliation_fiscale_consolidee_cad":50206104,
        "excedent_fonctionnement_a_fins_fiscales_consolide_cad":129335957,
        "variation_budget_resultat_fiscal_cad":129335957,
        "excedent_fiscal_equivaut_economie_certifiee":False,
        "excedent_fiscal_equivaut_tresorerie_libre":False,
        "ecarts_consolidation_equivalent_eliminations_certifiees":False,
        "engagement_professionnel_authentifie":0,
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
    validate_table(reference_rows(),BRIDGE)
    return {
        "schema_version":"P55J-TABLE-PUBLIQUE-1",
        "exercice":2024,
        "source_officielle":SOURCE,
        "lignes":reference_rows(),
        "pont_fiscal_budget_realise":BRIDGE,
        "statut_residus":"DIFFERENCES_ARITHMETIQUES_A_QUALIFIER_NON_ECONOMIES",
        "etapes_humaines":explanations(),
        "chiffres_non_certifies_par_cette_revue":True,
        "decision":NO_GO,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bilan-public")
    parser.add_argument("--table-public")
    parser.add_argument("--exiger-cloture",action="store_true")
    opts=parser.parse_args(argv)
    try:
        configuration()
        out=[Path(p).expanduser().absolute() for p in (
            opts.bilan_public,opts.table_public) if p]
        need(len({p.resolve() for p in out})==len(out),
             "P55J_SORTIES_CONFONDUES")
        for dest in out:
            need(dest.parent.is_dir() and not dest.parent.is_symlink()
                 and not dest.exists() and not dest.is_symlink(),
                 "P55J_SORTIE_EXISTANTE_OU_INVALIDE")
        report=public_report()
        table=public_table()
        if opts.bilan_public:
            p54z.write_new(opts.bilan_public,report)
        if opts.table_public:
            p54z.write_new(opts.table_public,table)
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 3 if opts.exiger_cloture else 0
    except (OSError,ValueError,TypeError,KeyError,
            json.JSONDecodeError,UnicodeError):
        print("P55J_REFUS: RAPPORT_OU_PERIMETRE_INCOHERENT",
              file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
