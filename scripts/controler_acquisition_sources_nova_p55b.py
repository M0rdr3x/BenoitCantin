#!/usr/bin/env python3
"""P55B — contrôler les éditions de deux PDF publics sans authentifier une expertise."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

import preparer_revue_independante_nova_p55a as p55a

p54z = p55a.p54z
BASE = p55a.BASE
CONFIG = BASE / "P55B_SOURCES_ET_PLAN_ACQUISITION_2024.json"
NO_GO = p55a.NO_GO
PDF_CODES = ("VILLE_2024", "MAMH_23027_2024")
SOURCE_DATA = (
    ("VILLE_2024", "VILLE_DE_QUEBEC",
     "https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf",
     "ville", 102, 8984919,
     "b3ee3e671f7bf98e56c7d42b5e8b6c34de02a96c9dc1c96469819fa4dbfa7399",
     ("P54E-V-001",)),
    ("MAMH_23027_2024", "MAMH",
     "https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf",
     "mamh", 162, 10818312,
     "4323c87d2114b58cf7a093c08f3b30327e949db91b9beb46a627eac1ecb4fc00",
     ("P54E-M-001","P54O-DATE-001","P54E-M-002","P54E-M-003")),
)
MANDATES = ("MANDAT-COMPTABLE-2024", "MANDAT-JURIDIQUE-2024")
PHASES = (
    ("A01_ACQUISITION_OFFICIELLE","RESPONSABLE_DOCUMENTAIRE_A_DESIGNER",
     "DEUX_COPIES_PUBLIQUES_LOCALES_HORS_DEPOT",()),
    ("A02_CONFRONTATION_EDITIONS","RESPONSABLE_DOCUMENTAIRE_A_DESIGNER",
     "SHA256_ET_TAILLE_COMPARES_A_P54Q",("A01_ACQUISITION_OFFICIELLE",)),
    ("A03_DROITS_ET_PROVENANCE","AUTORITE_HUMAINE_A_DESIGNER",
     "FICHE_DROITS_PROVENANCE_MISES_A_JOUR",("A02_CONFRONTATION_EDITIONS",)),
    ("A04_LOCALISATION_ET_QUALIFICATION","LECTEUR_ET_CONTRE_LECTEUR_A_DESIGNER",
     "CINQ_EXAMENS_VISUELS_CONTRADICTOIRES",("A03_DROITS_ET_PROVENANCE",)),
    ("A05_RESERVES_ET_SUSPENSIONS","GARANT_QUALITE_A_DESIGNER",
     "REGISTRE_DESACCORDS_ET_SUSPENSIONS",("A04_LOCALISATION_ET_QUALIFICATION",)),
    ("A06_MANDATS_COMPTABLE_ET_JURIDIQUE","GOUVERNANCE_A_DESIGNER",
     "DEUX_MANDATS_ECRITS_NON_TRANSMIS",("A03_DROITS_ET_PROVENANCE",)),
    ("A07_EXPERTISES_INDEPENDANTES","CPA_ET_JURISTE_A_MANDATER",
     "AVIS_AUTHENTIFIES_HORS_CODE",
     ("A05_RESERVES_ET_SUSPENSIONS","A06_MANDATS_COMPTABLE_ET_JURIDIQUE")),
    ("A08_DECISION_INSTITUTIONNELLE","AUTORITE_COMPETENTE_EXTERNE_AU_CODE",
     "DECISION_HUMAINE_DISTINCTE",("A07_EXPERTISES_INDEPENDANTES",)),
)
GUARDS = {
    "source_officielle_url_non_assimilee_a_octets_verifies",
    "empreinte_historique_p54q_non_assimilee_authenticite",
    "aucun_telechargement_ou_envoi_reseau",
    "aucun_contact_aux_institutions",
    "interdiction_soumission_mandats",
    "deux_pdfs_requis_pour_reproduction",
    "aucun_document_protege_dans_git",
    "fichiers_locaux_0600_et_hors_depot",
    "liens_symboliques_interdits",
    "controle_signature_pdf_impossible_par_sha_seul",
    "source_pdf_reference_2024",
    "quatre_dossiers_p54e_ouverts",
    "date_probable_non_confirmee",
    "deux_mandats_p54h_non_transmis",
    "aucun_expert_recrute",
    "conservation_reserves_p54z_et_p55a",
    "aucun_resultat_monetarise",
    "absence_double_compte_ville_rtc_somhac",
    "protection_emplois_services",
    "protection_pouvoir_achat",
    "deux_regimes_constitutionnels_separes",
    "quarante_taches_p54n_non_attestees",
    "dix_blocages_p54o_non_leves",
    "p54b_96_p54c_8_non_attestes",
    "aucune_modification_sinjira",
    "aucune_fusion_main",
    "aucun_go_automatique",
}
INITIAL = {
    "sources_officielles_identifiees":2, "copies_locales_verifiees":0,
    "observations_a_revoir":5, "dossiers_p54e_ouverts":4,
    "date_probable_non_certifiee":1, "mandats_a_preparer":2,
    "mandats_reels_signes":0, "experts_independants_authentifies":0,
    "avis_signes_authentifies":0, "taches_p54n_non_attestees":40,
    "blocages_p54o_non_leves":10, "controles_p54b_non_attestes":96,
    "controles_p54c_non_attestes":8, "economies_certifiees_cad":None,
    "decision":NO_GO,
}
NON_FOURNIE = "NON_FOURNIE"
CONCORDANCE = "CONCORDANCE_OCTETS_P54Q_NON_AUTHENTIFIANTE"
EDITION = "EDITION_DIFFERENTE_NON_REPRODUITE"


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def expected_sources():
    return [
        {"code":c, "institution":org, "url_officielle":url,
         "pdf_index_zero":page,
         "taille_octets_historique":size,
         "sha256_historique":sha,
         "observations":list(refs)}
        for (c,org,url,_q,page,size,sha,refs) in SOURCE_DATA
    ]


def expected_phases():
    return [
        {"code":code, "role":role, "livrable":livrable,
         "prerequis":list(deps)}
        for code,role,livrable,deps in PHASES
    ]


def configuration():
    cfg = p54z.read_json(CONFIG)
    expected = {
        "schema_version":"P55B-1", "date_reference":"2026-11-03",
        "exercice":2024,
        "ancrages":["P54E","P54H","P54O","P54Q","P54Z","P55A"],
        "sources":expected_sources(),
        "mandats_p54h_non_transmis":list(MANDATES),
        "phases_humaines":expected_phases(),
        "protections":{x:True for x in GUARDS},
        "etat_initial":INITIAL,
    }
    need(cfg == expected, "CONFIG_P55B_NON_CONFORME")
    a = p55a.configuration()
    q = p54z.read_json(BASE/"P54Q_SOURCES_PDF_LOCALES_2024.json")
    e = p54z.read_json(BASE/"P54E_PLAN_REVUE_HUMAINE_2024.json")
    o = p54z.read_json(BASE/"P54O_CONTROLE_QUALITE_PASSATION_2024.json")
    h = p54z.read_json(BASE/"P54H_MANDATS_EXPERTS_INDEPENDANTS_2024.json")
    need(a["dossier_references"] == list(p55a.REFS)
         and a["etat_initial"]["decision"] == NO_GO
         and q.get("schema_version") == "P54Q-1"
         and q.get("exercice") == 2024
         and e.get("schema_version") == "P54E-1"
         and o.get("schema_version") == "P54O-1"
         and h.get("schema_version") == "P54H-1",
         "CHAINAGE_P54_P55_INVALIDE")
    for code,_org,_url,qkey,page,size,sha,refs in SOURCE_DATA:
        historical = q["copies"].get(qkey,{})
        need(historical.get("pdf_index_zero") == page
             and historical.get("taille_octets") == size
             and historical.get("sha256") == sha,
             "REFERENCE_HISTORIQUE_P54Q_DIVERGENTE")
    need({case["id"] for case in e["cases"]} ==
         {"P54E-V-001","P54E-M-001","P54E-M-002","P54E-M-003"}
         and o["observation_date_probable"]["id"] == "P54O-DATE-001"
         and o["etat_initial"]["conditions_non_levees"] == 10
         and [row["code"] for row in h["mandats"]] == list(MANDATES)
         and all(set(row["dossiers"]) ==
                 {"P54E-V-001","P54E-M-001","P54E-M-002","P54E-M-003"}
                 for row in h["mandats"]),
         "OBSERVATIONS_OU_MANDATS_DIVERGENTS")
    return cfg


def local_pdf_status(path, expected_size, expected_sha):
    """Compare only locally; return historical byte match, never legal authenticity."""
    p = p55a.private_source(path)
    need(type(expected_size) is int and 5 <= expected_size <= 20_000_000,
         "TAILLE_REFERENCE_INVALIDE")
    need(type(expected_sha) is str and len(expected_sha) == 64
         and all(c in "0123456789abcdef" for c in expected_sha),
         "SHA_REFERENCE_INVALIDE")
    st = p.stat()
    need(stat.S_ISREG(st.st_mode), "SOURCE_NON_REGULIERE")
    if st.st_size != expected_size:
        return EDITION
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(p,flags)
    with os.fdopen(fd,"rb") as stream:
        after = os.fstat(stream.fileno())
        need(stat.S_ISREG(after.st_mode)
             and (after.st_mode & 0o777) == 0o600
             and (after.st_dev,after.st_ino,after.st_size) ==
                 (st.st_dev,st.st_ino,st.st_size), "SOURCE_MODIFIEE_OU_REMPLACEE")
        if stream.read(5) != b"%PDF-":
            return EDITION
        stream.seek(0)
        digest = hashlib.sha256()
        n = 0
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            digest.update(chunk)
            n += len(chunk)
        need(n == expected_size, "SOURCE_MODIFIEE_PENDANT_LECTURE")
    return CONCORDANCE if digest.hexdigest() == expected_sha else EDITION


def declared_checks(p54z_path=None,p55a_path=None):
    need(not p55a_path or p54z_path, "P55A_REQUIERT_P54Z")
    need(not p54z_path or p55a_path, "P54Z_REQUIERT_P55A_POUR_RECAPITULATIF")
    if not p54z_path:
        return None,0
    original,sha = p55a.upstream(p54z_path)
    dossier = p54z.read_json(p55a.private_source(p55a_path),100000)
    counts,inherited = p55a.validate_local(dossier,original,sha)
    return counts,inherited


def operation_plan():
    return {
        "schema_version":"P55B-PLAN-PUBLIC-1", "exercice":2024,
        "sources_officielles_a_consulter":[
            {"code":s["code"],"url_officielle":s["url_officielle"],
             "pdf_index_zero":s["pdf_index_zero"]}
            for s in expected_sources()
        ],
        "references_non_certifiees":list(p55a.REFS),
        "mandats_prepares_non_transmis":list(MANDATES),
        "operations_humaines":[
            {"code":p["code"],"role_a_designer":p["role"],
             "livrable_attendu":p["livrable"],
             "prerequis":p["prerequis"],
             "etat_reel":"NON_REALISE_PAR_CE_PROGRAMME"}
            for p in expected_phases()
        ],
        "aucune_transmission_externe":True,
        "aucune_decision_autorisee":True,
        "decision":NO_GO,
    }


def public_report(source_states=None,declarations=None,inherited=0):
    if source_states is None:
        source_states = {c:NON_FOURNIE for c in PDF_CODES}
    need(type(source_states) is dict
         and set(source_states) == set(PDF_CODES)
         and all(s in (NON_FOURNIE,CONCORDANCE,EDITION)
                 for s in source_states.values()),
         "STATUT_SOURCES_NON_CONFORME")
    if declarations is None:
        declarations = {name:0 for name in p55a.STATES}
        declarations["NON_INSTRUIT"] = 50
    need(type(declarations) is dict
         and set(declarations) == set(p55a.STATES)
         and all(type(v) is int and v >= 0 for v in declarations.values())
         and sum(declarations.values()) == 50
         and type(inherited) is int and 0 <= inherited <= 40,
         "DECLARATIONS_RECAPITULATIVES_INVALIDES")
    return {
        "schema_version":"P55B-BILAN-PUBLIC-1","exercice":2024,
        "sources_officielles_referencees":2,
        "copies_locales_concordantes_p54q_non_authentifiees":
            sum(x == CONCORDANCE for x in source_states.values()),
        "editions_divergentes_a_instruire":
            sum(x == EDITION for x in source_states.values()),
        "sources_non_fournies":
            sum(x == NON_FOURNIE for x in source_states.values()),
        "statuts_par_source":dict(source_states),
        "declarations_p55a_non_authentifiees":dict(declarations),
        "suspensions_p54z_heritees":inherited,
        "suspensions_p55a_declarees":declarations["SUSPENDU"],
        "reserves_p55a_ouvertes":declarations["RESERVE"],
        "observations_non_qualifiees":5,
        "dossiers_p54e_ouverts":4,"date_probable_non_certifiee":1,
        "mandats_p54h_prepares_non_transmis":2,
        "mandats_reels_signes":0,
        "sources_authentifiees_par_emetteur":0,
        "avis_independants_authentifies":0,
        "signatures_professionnelles_verifiees":0,
        "taches_p54n_non_attestees":40,
        "blocages_p54o_non_leves":10,
        "controles_p54b_non_attestes":96,
        "controles_p54c_non_attestes":8,
        "economies_certifiees_cad":None,
        "envoi_externe_autorise":False,
        "engagement_depense_autorise":False,
        "validation_constitutionnelle_autorisee":False,
        "fusion_main_autorisee":False,"decision":NO_GO,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ville-pdf")
    parser.add_argument("--mamh-pdf")
    parser.add_argument("--declarations-p54z")
    parser.add_argument("--relecture-p55a")
    parser.add_argument("--bilan-public")
    parser.add_argument("--plan-public")
    parser.add_argument("--exiger-go",action="store_true")
    a = parser.parse_args(argv)
    try:
        configuration()
        sources = [x for x in (a.ville_pdf,a.mamh_pdf,
                                a.declarations_p54z,a.relecture_p55a) if x]
        targets = [x for x in (a.bilan_public,a.plan_public) if x]
        source_paths = [p55a.private_source(x) for x in sources]
        target_paths = [Path(x).expanduser().absolute() for x in targets]
        need(len(set(x.resolve() for x in source_paths+target_paths))
             == len(source_paths+target_paths), "ENTREES_SORTIES_CONFLONDUES")
        for dest in target_paths:
            need(dest.parent.is_dir() and not dest.parent.is_symlink()
                 and not dest.exists() and not dest.is_symlink(),
                 "SORTIE_NON_AUTORISEE")
        # Each SHA is historical, not a statement about current source URLs.
        files = dict(zip(PDF_CODES,(a.ville_pdf,a.mamh_pdf)))
        statuses = {}
        for i,(code,_org,_url,_q,_page,size,sha,_refs) in enumerate(SOURCE_DATA):
            statuses[code] = (local_pdf_status(files[code],size,sha)
                              if files[code] else NON_FOURNIE)
        counts,inherited = declared_checks(a.declarations_p54z,a.relecture_p55a)
        summary = public_report(statuses,counts,inherited)
        if a.bilan_public:
            p54z.write_new(a.bilan_public,summary)
        if a.plan_public:
            p54z.write_new(a.plan_public,operation_plan())
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        if a.exiger_go:
            return 3
        return 4 if EDITION in statuses.values() else 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError,
            json.JSONDecodeError):
        print("P55B_REFUS: FICHIER_OU_CHAINE_PROBATOIRE_NON_CONFORME",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
