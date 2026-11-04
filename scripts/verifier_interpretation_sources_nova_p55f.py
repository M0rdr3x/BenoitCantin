#!/usr/bin/env python3
"""P55F — contextualisation financière 2024 sans authentification ni économie."""
import argparse
import json
from pathlib import Path
import sys

import prioriser_pieces_manquantes_nova_p55e as p55e

p55d = p55e.p55d
p55c = p55e.p55c
p55b = p55e.p55b
p54z = p55e.p54z
p55a = p55e.p55a
BASE = p55d.BASE
CONFIG = BASE / "P55F_CONSTATS_PUBLICS_ET_VERROUS_2024.json"
NO_GO = p55d.NO_GO
SOURCES = (
    ("VILLE_QUEBEC_2024",
     "https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf",
     "LECTURE_TEXTE_PUBLIC_EN_LIGNE",
     "NON_VERIFIES_DANS_CE_JALON"),
    ("MAMH_23027_2024",
     "https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf",
     "INDEXATION_TEXTE_PUBLIC_ET_REFERENCE_P54Q",
     "NON_VERIFIES_DANS_CE_JALON"),
    ("DONNEES_QUEBEC_MAMH",
     "https://www.donneesquebec.ca/recherche/dataset/rapport-financier-des-organismes-municipaux-et-autres-documents",
     "NOTICE_PUBLIQUE_SUR_RETRANSMISSION",
     "SANS_OBJET_AVIS_DE_VERSION"),
)
NOTES = (
    ("CONTEXTE_DEPENSES_MIXTES","VILLE_QUEBEC_2024",
     "PAGE_NOTES_COMPLEMENTAIRES_106",
     "VENTILATION_SELON_RAVQ_1435",
     "CONTEXTE_LEGAL_NON_CONCLUSION_D_ECONOMIE"),
    ("REDRESSEMENT_COMPARATIF","VILLE_QUEBEC_2024",
     "PAGE_NOTES_COMPLEMENTAIRES_106",
     "EXERCICE_COMPARATIF_DIMINUE_1825176_CAD",
     "REDRESSEMENT_2023_PAS_ECONOMIE_NOUVELLE_2024"),
    ("COLONNE_ELIMINATIONS","MAMH_23027_2024",
     "TABLE_VENTILATION_DEPENSES_MIXTES_S50",
     "COLONNE_ELIMINATIONS_PRESENTE",
     "NE_PAS_RECOMPTER_LES_ELIMINATIONS_EXISTANTES"),
    ("RETRANSMISSIONS_POSSIBLES","DONNEES_QUEBEC_MAMH",
     "NOTICE_JEU_DONNEES_OUVERTES",
     "RAPPORTS_ET_DONNEES_PEUVENT_ETRE_MODIFIES",
     "UNE_URL_NE_PROUVE_PAS_UNE_VERSION_IDENTIQUE"),
)
GUARDS = {
    "liens_publics_et_textes_ne_certifient_pas_octets",
    "lecture_textuelle_ne_remplace_pas_page_visuelle",
    "sha_historiques_p54q_ne_provent_pas_emetteur",
    "actualite_des_versions_reste_a_reverifier",
    "redressement_2023_non_assimile_economie_nouvelle",
    "eliminations_existantes_ne_sont_pas_nouvelles_economies",
    "unites_dates_exercices_perimetres_distincts",
    "meme_montant_sur_deux_publications_pas_deux_gains",
    "seuil_preuves_originales_2_avec_sha",
    "reproduction_nfkc_cinq_observations_prealable",
    "rapprochement_p55e_reutilise",
    "aucune_reduction_d_effectifs_ou_de_services",
    "protection_pouvoir_achat",
    "deux_scenarios_constitutionnels_separes",
    "aucun_telechargement_automatique",
    "aucune_communication_avec_institutions",
    "aucune_piece_origine_dans_git",
    "aucun_identifiant_ou_texte_prive_dans_rapports",
    "aucune_economie_certifiee_cad",
    "mandats_p54h_non_signes",
    "quatre_dossiers_p54e_ouverts",
    "date_probable_non_certifiee",
    "p54n_40_p54o_10_en_attente",
    "p54b_96_p54c_8_non_attestes",
    "aucune_fusion_main",
    "sinjira_inchange",
    "no_go_automatique",
}
INTERPRETATION = {
    "redressement_comparatif_2023_cad":1825176,
    "economies_certifiees_cad":None,
    "eliminations_comme_gain_autorisees":False,
    "correction_comparative_comme_gain_autorisee":False,
    "comparaison_sans_edition_exacte_autorisee":False,
}
INITIAL = {
    "textes_publics_contextualises":4,
    "copies_2024_verifiees_par_nouveau_sha":0,
    "positions_nfkc_reproduites_p55f":0,
    "avis_independants_authentifies":0,
    "mandats_signes":0,
    "dossiers_p54e_ouverts":4,
    "date_probable_non_certifiee":1,
    "taches_p54n_non_attestees":40,
    "blocages_p54o_non_leves":10,
    "controles_p54b_non_attestes":96,
    "controles_p54c_non_attestes":8,
    "economies_certifiees_cad":None,
    "decision":NO_GO,
}


def need(cond,reason):
    if not cond:
        raise ValueError(reason)


def sources_expected():
    return [
        {"code":code,"url":url,"mode":mode,"etat_octets_actuels":status}
        for code,url,mode,status in SOURCES
    ]


def notes_expected():
    return [
        {
            "code":code,"source":source,"localisation":page,
            "fait_descriptif":description,"limite":warning,
            "niveau_preuve":"TEXTE_PUBLIC_NON_AUTHENTIFIANT",
        }
        for code,source,page,description,warning in NOTES
    ]


def configuration():
    cfg=p54z.read_json(CONFIG)
    expected={
        "schema_version":"P55F-1","date_reference":"2026-11-03",
        "exercice":2024,
        "ancrages":["P54Q","P55B","P55C","P55D","P55E"],
        "sources_publiques":sources_expected(),
        "constats_contextuels":notes_expected(),
        "verrous_interpretation":INTERPRETATION,
        "protections":{guard:True for guard in GUARDS},
        "etat_initial":INITIAL,
    }
    need(cfg==expected,"P55F_CONFIGURATION_MODIFIEE")
    e=p55e.configuration()
    q=p54z.read_json(BASE/"P54Q_SOURCES_PDF_LOCALES_2024.json")
    sources=p55b.expected_sources()
    need(e["schema_version"]=="P55E-1"
         and e["etat_initial"]["economies_certifiees_cad"] is None
         and e["etat_initial"]["decision"]==NO_GO
         and q["schema_version"]=="P54Q-1"
         and len(sources)==2
         and sources[0]["url_officielle"]==SOURCES[0][1]
         and sources[1]["url_officielle"]==SOURCES[1][1],
         "P55F_CHAINAGE_DES_SOURCES_ALTERE")
    need(INTERPRETATION["redressement_comparatif_2023_cad"]==1825176
         and INTERPRETATION["economies_certifiees_cad"] is None
         and all(v is False for k,v in INTERPRETATION.items()
                 if k.endswith("_autorisees") or
                    k.endswith("_autorisee")),
         "P55F_INTERPRETATION_NON_NEUTRE")
    return cfg


def public_report(states=None,reproduced=False):
    prior=p55e.report(states,reproduced)
    need(prior["decision"]==NO_GO
         and prior["economies_certifiees_cad"] is None
         and prior["avis_independants_authentifies"]==0
         and not prior["transmission_externe_autorisee"]
         and not prior["fusion_main_autorisee"],
         "P55F_PARENT_NON_NEUTRE")
    need(prior["positions_nfkc_reproduites_techniquement"] in (0,5),
         "P55F_NOMBRE_POSITIONS_NON_ADMISSIBLE")
    return {
        "schema_version":"P55F-BILAN-PUBLIC-1","exercice":2024,
        "phase_prioritaire_p55e":prior["phase_prioritaire"],
        "prochaines_actions_p55e":prior["prochaines_actions_codes"],
        "documents_publics_references":2,
        "notice_versions_referencee":1,
        "contextes_textuels_publics_references":len(NOTES),
        "copies_pdf_manquantes":prior["copies_publiques_absentes"],
        "editions_divergentes_a_instruire":
            prior["editions_divergentes_a_instruire"],
        "copies_concordantes_a_reference_historique_non_authentifiees":
            prior["copies_concordantes_p54q_non_authentifiees"],
        "positions_nfkc_reproduites_techniquement":
            prior["positions_nfkc_reproduites_techniquement"],
        "redressement_comparatif_2023_cad":1825176,
        "redressement_2023_est_economie_2024":False,
        "colonne_eliminations_est_gain_nouveau":False,
        "version_pdf_officielle_actuelle_authentifiee":False,
        "qualification_professionnelle_independante":False,
        "dossiers_p54e_ouverts":4,"date_probable_non_certifiee":1,
        "taches_p54n_non_attestees":40,"blocages_p54o_non_leves":10,
        "controles_p54b_non_attestes":96,"controles_p54c_non_attestes":8,
        "mandats_professionnels_signes":0,
        "avis_independants_authentifies":0,
        "economies_certifiees_cad":None,
        "transmission_externe_autorisee":False,
        "cloture_automatique_autorisee":False,
        "fusion_main_autorisee":False,"decision":NO_GO,
    }


def public_plan(summary):
    need(type(summary) is dict
         and summary.get("schema_version")=="P55F-BILAN-PUBLIC-1"
         and summary.get("decision")==NO_GO
         and summary.get("economies_certifiees_cad") is None
         and summary.get("redressement_2023_est_economie_2024") is False
         and summary.get("colonne_eliminations_est_gain_nouveau") is False,
         "P55F_BILAN_FICTIVEMENT_CERTIFIANT")
    return {
        "schema_version":"P55F-PLAN-PUBLIC-1","exercice":2024,
        "sources_et_notice":[
            {"code":src["code"],"url":src["url"],
             "statut":"REFERENCE_PUBLIQUE_SANS_AUTHENTIFICATION_OCTETS"}
            for src in sources_expected()
        ],
        "constats_prudence":[
            {"code":note["code"],
             "limite_interpretation":note["limite"],
             "niveau_preuve":note["niveau_preuve"]}
            for note in notes_expected()
        ],
        "prochaines_actions_techniques":summary["prochaines_actions_p55e"],
        "avis_comptable_ou_juridique_recu":False,
        "revision_humaine_exigee":True,
        "decision":NO_GO,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ville-pdf")
    parser.add_argument("--mamh-pdf")
    parser.add_argument("--bilan-public")
    parser.add_argument("--plan-public")
    parser.add_argument("--exiger-certification",action="store_true")
    a=parser.parse_args(argv)
    try:
        configuration()
        need(bool(a.ville_pdf)==bool(a.mamh_pdf),
             "P55F_DEUX_PDF_EXIGES_ENSEMBLE")
        p55e.validate_inputs(
            [a.ville_pdf,a.mamh_pdf],
            [a.bilan_public,a.plan_public])
        states,attempt=p55c.local_sources(a.ville_pdf,a.mamh_pdf)
        reproduced=(attempt is not None
                    and attempt["cinq_positions_reproduites"] is True)
        report=public_report(states,reproduced)
        if a.bilan_public:
            p54z.write_new(a.bilan_public,report)
        if a.plan_public:
            p54z.write_new(a.plan_public,public_plan(report))
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        if a.exiger_certification:
            return 3
        return 4 if a.ville_pdf and not reproduced else 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError,
            json.JSONDecodeError,ImportError):
        print("P55F_REFUS: SOURCE_OU_INTERPRETATION_NON_CONFORME",
              file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
