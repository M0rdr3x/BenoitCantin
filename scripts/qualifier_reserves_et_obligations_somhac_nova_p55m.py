#!/usr/bin/env python3
"""P55M — protections des réserves SOMHAC et des engagements collectifs 2024."""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import sys

import recouper_quotes_parts_rtc_ville_nova_p55l as p55l

p55k=p55l.p55k
p54z=p55l.p54z
BASE=p55l.BASE
CONFIG=BASE/"P55M_RESTRICTIONS_SOMHAC_ET_ENGAGEMENTS_2024.json"
NO_GO=p55l.NO_GO

SOURCE_VILLE={
    "id":"VILLE_FINANCES_2024",
    "url":"https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf",
    "notes":[
        "7_PLACEMENTS_DE_PORTEFEUILLE_S11_PAGE_46",
        "19_OBLIGATIONS_CONTRACTUELLES_S11_PAGE_54",
        "20_DROITS_CONTRACTUELS_S11_PAGE_55",
    ],
    "type_verification":
        "EXTRACTION_TEXTE_SOURCE_OFFICIELLE_SANS_SCREENSHOT_ET_SANS_COPIE_LOCALE",
}
SOURCE_OMHQ={
    "id":"OMHQ_SOMHAC_MANDAT",
    "url":"https://www.omhq.qc.ca/omhq-somhac",
    "notes":["OMHQ_GERE_HABITATIONS_ABORDABLES_SOMHAC"],
    "type_verification":"PAGE_INSTITUTIONNELLE_PUBLIQUE",
}
RESERVE={
    "exercice":2024,
    "placements_affectes_reparations_majeures_cad":4689663,
    "comparatif_2023_cad":4676844,
    "variation_2024_moins_2023_cad":12819,
    "variation_pct_une_decimale":"0.3",
    "fonds_libres_disponibles_cad":None,
}
CONVENTION={
    "existe":True,
    "organisme_partenaire":"ORGANISME_PROVINCIAL_NON_IDENTIFIE_DANS_LA_NOTE",
    "annee_fin_indiquee":2039,
    "montant_annuel_cad":None,
    "peut_etre_resilie_sans_frais":None,
}
DUE=(
    ("2025",10961000,335521000),
    ("2026",10301000,126874000),
    ("2027",9806000,75687000),
    ("2028",9124000,46215000),
    ("2029",1331000,12831000),
    ("2030_ET_SUIVANTES",333000,32556000),
)
DEBTS={
    "perimetre":"ORGANISMES_CONTROLES_ET_PARTENARIATS_RTC_SOMHAC_NON_VENTILES",
    "periodicite":"ECHEANCES_FUTURES_PRESENTEES_AU_31_12_2024",
    "annees":[{"periode":p,
               "organismes_controles_et_partenariats_cad":o,
               "total_consolide_cad":t} for p,o,t in DUE],
    "total_groupe_cad":41856000,
    "total_consolide_cad":629684000,
    "attribution_somhac_cad":None,
}
RIGHTS={
    "perimetre":"ORGANISMES_CONTROLES_ET_PARTENAIRES_RTC_SOMHAC_NON_VENTILES",
    "periode":"2025",
    "montant_groupe_cad":8591000,
    "total_toutes_periodes_groupe_cad":8591000,
    "attribution_somhac_cad":None,
}
FORBIDDEN=(
    "RESERVE_4689663_EST_ECONOMIE",
    "RESERVE_4689663_EST_CAISSE_LIBRE",
    "TOTAL_41856000_EXCLUSIVEMENT_SOMHAC",
    "DROITS_8591000_EXCLUSIVEMENT_SOMHAC",
    "ENGAGEMENT_JUSQU_2039_SANS_OBLIGATION",
    "SOLDE_NET_ENGAGEMENTS_MOINS_DROITS_EST_ECONOMIE",
    "OMHQ_ET_SOMHAC_COMPTES_IDENTIQUES",
    "FINANCEMENT_RTC_154M_EST_RECETTE_ADDITIONNELLE",
    "REDUCTION_LOYERS_OU_ENTRETIEN_DEDUITE",
    "SOMHAC_ETATS_INDIVIDUELS_2024_OBTENUS",
)
TASKS=(
    ("M01","OBTENIR_ETATS_FINANCIERS_AUTONOMES_SOMHAC_2024",
     "BILAN_RESULTATS_FLUX_TRESORERIE_NOTES_OPINION_SIGNATURES"),
    ("M02","QUALIFIER_RESERVE_ENTRETIEN_2024",
     "DETAIL_RESTRICTIONS_PLACEMENTS_PLAN_DE_MAINTIEN_DE_L_ETAT_DES_IMMEUBLES"),
    ("M03","LIRE_CONVENTION_PROVINCIALE_2039",
     "CONVENTION_SIGNEE_AVENANTS_OBLIGATIONS_RESSOURCES"),
    ("M04","VENTILER_OBLIGATIONS_ET_DROITS_RTC_SOMHAC",
     "ECHEANCIER_CONTRACTUEL_PAR_ENTITE_AVEC_ECRITURES"),
    ("M05","VERIFIER_GESTION_OMHQ_ET_CONSOLIDATION",
     "MANDATS_OMHQ_SOMHAC_OPERATIONS_RECIPROQUES_RAPPROCHEMENTS"),
    ("M06","MESURER_IMPACT_SOCIAL_AVANT_OPTIMISATION",
     "INDICATEURS_QUALITE_LOGEMENT_SECURITE_ENTRETIEN_EMPLOIS_LOYERS"),
)
GUARDS={
    "rapport_ville_2024_identifie",
    "notes_7_19_20_consultees_par_texte",
    "capture_visuelle_notes_en_echec",
    "pdf_historique_non_reacquis",
    "somhac_omqh_personnes_distinctes",
    "omqh_mandat_gestion_somhac",
    "reserve_remplacement_2024_destinee_reparations_majeures",
    "reserve_remplacement_2023_comparatif",
    "reserve_variation_non_economie",
    "reserve_n_est_pas_liquidite_libre",
    "convention_exploitation_en_vigueur_jusqu_2039",
    "pas_de_conclusion_rupture_convention",
    "pas_de_montant_annuel_de_convention_invente",
    "obligations_publiees_sont_regroupees_rtc_somhac",
    "aucune_obligation_attribuee_exclusivement_somhac",
    "droits_contractuels_groupes_non_attribues_somhac",
    "obligations_non_decommittees",
    "droits_non_convertis_en_economies",
    "aucune_compensation_automatique_droits_obligations",
    "total_six_periodes_obligations_verifie",
    "distinction_2025_futur_et_2024_cloture",
    "donnees_2024_pas_2025_ou_2026_confondus",
    "aucun_etat_individuel_somhac_certifie",
    "aucun_sous_total_rtc_reduit_pour_inferer_somhac",
    "rtc_contrepartie_p55l_non_readditionnee",
    "ecarts_p55k_restent_non_attribues",
    "logements_abordables_proteges",
    "entretien_majeur_protege",
    "emploi_et_services_proteges",
    "pouvoir_achat_et_loyers_proteges",
    "deux_regimes_constitutionnels_distincts",
    "attestation_expert_comptable_manquante",
    "justificatifs_originaux_non_recus",
    "quatre_p54e_et_date_non_certifiee",
    "p54n40_p54o10_p54b96_p54c8_non_attestes",
    "aucun_contact_ou_mandat",
    "aucune_depense_autorisee",
    "aucune_fusion_main",
    "sindjira_non_modifie",
    "no_go_automatique",
}
INITIAL={
    "rapports_somhac_individuels_2024_obtenus":0,
    "copies_pdf_origines_sha_actuel_verifiees":0,
    "ecritures_reciproques_obtenues":0,
    "avis_comptables_et_juridiques_authentifies":0,
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

def require(statement,reason):
    if not statement:
        raise ValueError(reason)

def percent(numerator, denominator):
    require(type(numerator) is int and type(denominator) is int
            and numerator >= 0 and denominator > 0,
            "P55M_VARIATION_NON_DEFINIE")
    return str((Decimal(numerator)*100/Decimal(denominator)).quantize(
        Decimal("0.1"),rounding=ROUND_HALF_UP))

def review_tasks():
    return [{"code":code,"objet":subject,"document_requis":proof,"statut":"NON_OBTENU"}
            for code,subject,proof in TASKS]

def validate_financials(reserve,convention,debts,rights):
    require(reserve==RESERVE and convention==CONVENTION
            and debts==DEBTS and rights==RIGHTS,
            "P55M_MONTANTS_OU_QUALIFICATIONS_MODIFIES")
    require(type(reserve["placements_affectes_reparations_majeures_cad"]) is int
            and reserve["placements_affectes_reparations_majeures_cad"]
            -reserve["comparatif_2023_cad"]
            ==reserve["variation_2024_moins_2023_cad"]
            and reserve["fonds_libres_disponibles_cad"] is None,
            "P55M_RESERVE_NON_AFFECTEE_OU_ERRONEE")
    require(percent(reserve["variation_2024_moins_2023_cad"],
                    reserve["comparatif_2023_cad"])
            ==reserve["variation_pct_une_decimale"],
            "P55M_VARIATION_RESERVE_INCOHERENTE")
    require(convention["existe"] is True
            and type(convention["annee_fin_indiquee"]) is int
            and convention["annee_fin_indiquee"]==2039
            and convention["montant_annuel_cad"] is None
            and convention["peut_etre_resilie_sans_frais"] is None,
            "P55M_CONVENTION_NON_AUTHENTIFIEE")
    periods=debts["annees"]
    require(type(periods) is list and len(periods)==6
            and [p["periode"] for p in periods]==[x[0] for x in DUE],
            "P55M_OBLIGATIONS_SIX_PERIODES_EXIGEES")
    require(all(type(p["organismes_controles_et_partenariats_cad"]) is int
                and type(p["total_consolide_cad"]) is int
                and p["total_consolide_cad"]>=p["organismes_controles_et_partenariats_cad"]>=0
                for p in periods),
            "P55M_MONTANTS_GROUPES_INCOHERENTS")
    require(sum(p["organismes_controles_et_partenariats_cad"] for p in periods)
            ==debts["total_groupe_cad"]==41856000
            and sum(p["total_consolide_cad"] for p in periods)
            ==debts["total_consolide_cad"]==629684000,
            "P55M_ECHEANCIER_NE_BOUCLE_PAS")
    require(debts["attribution_somhac_cad"] is None
            and rights["attribution_somhac_cad"] is None
            and rights["montant_groupe_cad"]==
                 rights["total_toutes_periodes_groupe_cad"]==8591000,
            "P55M_ATTRIBUTION_INDIVIDUELLE_INVENTEE")
    return True

def configuration():
    cfg=p54z.read_json(CONFIG)
    expected={
        "schema_version":"P55M-1",
        "reference_date":"2026-11-05",
        "exercice_source":2024,
        "sources":[SOURCE_VILLE,SOURCE_OMHQ],
        "reserve_somhac":RESERVE,
        "convention_somhac":CONVENTION,
        "obligations_contractuelles_groupe_organismes":DEBTS,
        "droits_contractuels_groupe_organismes":RIGHTS,
        "hypotheses_interdites":list(FORBIDDEN),
        "actions_humaines":review_tasks(),
        "protections":{name:True for name in GUARDS},
        "etat_initial":INITIAL,
    }
    require(cfg==expected,"P55M_REFERENTIEL_MODIFIE")
    upstream=p55l.configuration()
    require(upstream["schema_version"]=="P55L-1"
            and upstream["etat_initial"]["decision"]==NO_GO
            and upstream["sources"]["ville"]["url"]==SOURCE_VILLE["url"]
            and upstream["etat_initial"]["quote_part_rtc_qualifiee_economie"] is False
            and upstream["etat_initial"]["justificatif_somhac_distinct_obtenu"] is False,
            "P55M_PARENT_P55L_MODIFIE")
    validate_financials(
        cfg["reserve_somhac"],cfg["convention_somhac"],
        cfg["obligations_contractuelles_groupe_organismes"],
        cfg["droits_contractuels_groupe_organismes"])
    return cfg

def public_report():
    validate_financials(RESERVE,CONVENTION,DEBTS,RIGHTS)
    return {
        "schema_version":"P55M-BILAN-PUBLIC-1",
        "exercice":2024,
        "sources_publiques_institutionnelles":2,
        "reserve_somhac_affectee_cad":
            RESERVE["placements_affectes_reparations_majeures_cad"],
        "variation_reserve_2024_2023_cad":RESERVE["variation_2024_moins_2023_cad"],
        "variation_reserve_pct":RESERVE["variation_pct_une_decimale"],
        "reserve_somhac_est_tresorerie_libre":False,
        "convention_somhac_annee_fin_indiquee":2039,
        "contrat_individuel_2039_montant_documente":False,
        "obligations_groupe_organismes_cad":DEBTS["total_groupe_cad"],
        "droits_groupe_organismes_cad":RIGHTS["montant_groupe_cad"],
        "obligations_groupe_sont_somhac_seulement":False,
        "droits_groupe_sont_somhac_seulement":False,
        "bilan_somhac_autonome_obtenu":False,
        "ecritures_interorganismes_obtenues":False,
        "pdf_originaux_verifies_par_sha_actuel":0,
        "nombre_actions_humaines_ouvertes":len(TASKS),
        "avis_professionnels_authentifies":0,
        "mandats_signes":0,
        "economies_nouvelles_demontrees_cad":None,
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
    validate_financials(RESERVE,CONVENTION,DEBTS,RIGHTS)
    return {
        "schema_version":"P55M-TABLE-PUBLIQUE-1",
        "exercice":2024,
        "sources":[SOURCE_VILLE,SOURCE_OMHQ],
        "reserve_somhac":RESERVE,
        "convention_somhac":CONVENTION,
        "obligations_groupe":DEBTS,
        "droits_groupe":RIGHTS,
        "travaux_humains_requis":review_tasks(),
        "regle_interpretation":
            "RESERVES_AFFECTEES_ET_POSTES_GROUPES_NON_REQUALIFIES_EN_GAINS",
        "aucune_economie_affirmee":True,
        "decision":NO_GO,
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bilan-public")
    parser.add_argument("--table-public")
    parser.add_argument("--exiger-certification",action="store_true")
    args=parser.parse_args(argv)
    try:
        configuration()
        dest=[Path(x).expanduser().absolute() for x in
              (args.bilan_public,args.table_public) if x]
        require(len({p.resolve() for p in dest})==len(dest),
                "P55M_SORTIES_CONFONDUES")
        for target in dest:
            require(target.parent.is_dir()
                    and not target.parent.is_symlink()
                    and not target.exists() and not target.is_symlink(),
                    "P55M_SORTIE_REFUSEE")
        report=public_report()
        if args.bilan_public:
            p54z.write_new(args.bilan_public,report)
        if args.table_public:
            p54z.write_new(args.table_public,public_table())
        print(json.dumps(report,sort_keys=True,ensure_ascii=False))
        return 3 if args.exiger_certification else 0
    except (ValueError,OSError,KeyError,TypeError,
            json.JSONDecodeError,UnicodeError):
        print("P55M_REFUS: RESERVE_OU_CONTRATS_NON_CONFORMES",file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
