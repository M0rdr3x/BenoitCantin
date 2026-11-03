#!/usr/bin/env python3
"""P55C — rapprochement local P54Q/P55A, jamais certification comptable ou légale."""
import argparse
import json
from pathlib import Path
import sys

import controler_acquisition_sources_nova_p55b as p55b
import reproduire_pdf_locaux_nova_p54q as p54q

p55a = p55b.p55a
p54z = p55a.p54z
ROOT = p55a.ROOT
BASE = p55a.BASE
CONFIG = BASE / "P55C_REGISTRE_RECONCILIATION_PIECES_2024.json"
NO_GO = p55a.NO_GO
ROWS = (
    ("P54E-V-001","ville",0,102,"FIN","INDETERMINE"),
    ("P54E-M-001","mamh",1,162,"DEBUT","INDETERMINE"),
    ("P54O-DATE-001","mamh",2,162,"FIN","ANNEE_DATE_PROBABLE"),
    ("P54E-M-002","mamh",3,162,"FIN","INDETERMINE"),
    ("P54E-M-003","mamh",4,162,"FIN","INDETERMINE"),
)
STATES = (
    "NON_EXAMINE","REPERE_DECLARE_NON_AUTHENTIFIE",
    "RESERVE_OUVERTE","SUSPENDU",
)
QUALIFICATIONS = (
    "NON_QUALIFIE","DATE_POSSIBLE_NON_CERTIFIEE",
    "FOLIO_POSSIBLE_NON_CERTIFIE",
    "REFERENCE_POSSIBLE_NON_CERTIFIEE",
    "IDENTIFIANT_POSSIBLE_NON_CERTIFIE",
    "VALEUR_A_EXAMINER_NON_CERTIFIEE",
)
COUNTER_REVIEWS = (
    "NON_EFFECTUEE","DECLAREE_DISTINCTE_NON_AUTHENTIFIEE",
    "DESACCORD_OUVERT",
)
GUARDS = {
    "deux_pdfs_originaux_historique_2024_exiges",
    "aucune_verification_officielle_de_l_emetteur_par_sha",
    "position_nfkc_n_est_pas_une_coordonnee_sur_page",
    "aucune_reproduction_si_edition_differente",
    "reutilise_p54q_et_p54p_sans_nouvel_extracteur",
    "aucune_lecture_reelle_en_ci",
    "cinq_references_ancres_p54e_p54o",
    "fiche_privee_0600_hors_depot",
    "liaison_fiche_aux_positions_reproduites",
    "validation_p54z_p55a_avant_revue_declaree",
    "suspensions_et_reserves_prioritaires",
    "contre_lecture_declaree_non_assimilee_independance",
    "zero_transmission_envoi_ou_contact",
    "pas_d_identite_ni_signature_en_github",
    "rapport_public_sans_offsets_ni_sha",
    "aucun_avis_pro_humain_authentifie",
    "aucune_economie_certifiee",
    "quatre_dossiers_p54e_non_clos",
    "date_probable_non_confirmee",
    "deux_mandats_p54h_non_signes",
    "quarante_taches_p54n_non_attestees",
    "dix_blocages_p54o_non_leves",
    "p54b_96_p54c_8_non_attestes",
    "pas_de_double_compte_ville_rtc_somhac",
    "emplois_services_pouvoir_achat_proteges",
    "deux_regimes_constitutionnels_separes",
    "aucun_changement_sinjira",
    "aucune_fusion_main",
    "no_go_automatique",
}
INITIAL = {
    "sources_pdf_locales_fournies":0,
    "copies_historiques_concordantes":0,
    "positions_nfkc_reproduites":0,
    "observations":5,
    "dossiers_p54e_ouverts":4,
    "date_probable_non_certifiee":1,
    "fiches_revue_humaine_authentifiees":0,
    "avis_professionnels_authentifies":0,
    "mandats_p54h_signes":0,
    "taches_p54n_non_attestees":40,
    "blocages_p54o_non_leves":10,
    "controles_p54b_non_attestes":96,
    "controles_p54c_non_attestes":8,
    "economies_certifiees_cad":None,
    "decision":NO_GO,
}


def need(test,code):
    if not test:
        raise ValueError(code)


def expected_rows():
    return [
        {
            "reference":r,
            "source":s,
            "index_observation_p54d":i,
            "pdf_index_zero":p,
            "zone":z,
            "qualification_initiale_indicative":q,
        } for r,s,i,p,z,q in ROWS
    ]


def configuration():
    cfg = p54z.read_json(CONFIG)
    expected = {
        "schema_version":"P55C-1",
        "date_reference":"2026-11-03",
        "exercice":2024,
        "sources_jalons":["P54P","P54Q","P54Z","P55A","P55B"],
        "observations":expected_rows(),
        "etats_de_revue":list(STATES),
        "qualifications_declaratives":list(QUALIFICATIONS),
        "contre_revues_declaratives":list(COUNTER_REVIEWS),
        "protections":{guard:True for guard in GUARDS},
        "etat_initial":INITIAL,
    }
    need(cfg == expected, "P55C_CONFIGURATION_NON_CONFORME")
    previous = p55b.configuration()
    q = p54q.configuration()
    need(previous["schema_version"] == "P55B-1"
         and q["source_p54d_run"] == 40120462237
         and q["etat_initial"]["decision"] == NO_GO
         and [r["reference"] for r in expected_rows()] ==
             list(p55a.REFS),
         "P55C_CHAINAGE_P55B_P54Q_INCONFORME")
    observations = p54z.read_json(
        BASE/"P54P_REPRODUCTION_POSITIONS_PDF_2024.json")
    need(observations["schema_version"] == "P54P-1"
         and len(observations["observations_attendues"]) == 5,
         "P55C_P54P_SOURCE_INVALIDE")
    for row,old in zip(expected_rows(),observations["observations_attendues"]):
        need(old["source"] == row["source"]
             and old["index_p54d"] == row["index_observation_p54d"]
             and old["classe"] == row["qualification_initiale_indicative"]
             and old["zone"] == row["zone"]
             and old["dossier"] ==
                 (None if row["reference"] == "P54O-DATE-001"
                  else row["reference"])
             and q["copies"][row["source"]]["pdf_index_zero"] ==
                 row["pdf_index_zero"],
             "P55C_MAPPING_OBSERVATIONS_MODIFIE")
    return cfg


def local_sources(ville=None,mamh=None):
    """Return P55B statuses and P54Q attempt; PDFs are never returned or saved."""
    need(bool(ville) == bool(mamh), "DEUX_PDF_NECESSAIRES")
    statuses = dict.fromkeys(p55b.PDF_CODES,p55b.NON_FOURNIE)
    if not ville:
        return statuses,None
    paths = {"ville":ville,"mamh":mamh}
    validated = p54q.checked_local_paths(paths)
    need(len({p.resolve() for p in validated.values()}) == 2,
         "SOURCES_PDF_DUPLIQUEES")
    for code,_org,_url,qkey,_page,size,sha,_refs in p55b.SOURCE_DATA:
        statuses[code] = p55b.local_pdf_status(
            validated[qkey],size,sha)
    if not all(x == p55b.CONCORDANCE for x in statuses.values()):
        return statuses,None
    attempt = p54q.reproduce(validated,p54q.configuration()["copies"])
    p54q.p54p.validated_public_attempt(attempt)
    return statuses,attempt


def validate_positions(positions):
    """P54P guards the source/order and individual NFKC offsets."""
    need(type(positions) is list and len(positions) == 5,
         "CINQ_POSITIONS_TECHNIQUES_REQUISES")
    attempt = {
        "statut":"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION",
        "sources":{src:"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION"
                   for src in p54q.NAMES},
        "copies_verifiees_par_hachage":2,
        "cinq_positions_reproduites":True,
        "positions":positions,
    }
    p54q.p54p.validated_public_attempt(attempt)
    return positions


def private_model(positions):
    validate_positions(positions)
    return {
        "schema_version":"P55C-FICHE-PRIVEE-1",
        "exercice":2024,
        "observations":[
            {
                "reference":ref,
                "source":src,
                "pdf_index_zero":page,
                "index_observation_p54d":idx,
                "offset_texte_nfkc":position["offset_texte_extrait"],
                "longueur_texte_nfkc":position["longueur_texte_normalise_nfkc"],
                "etat_revue":"NON_EXAMINE",
                "qualification_declaree":"NON_QUALIFIE",
                "contre_revue_declaree":"NON_EFFECTUEE",
            }
            for (ref,src,idx,page,_zone,_class),position in zip(
                ROWS,positions)
        ],
    }


def upstream_claims(path_z=None,path_a=None):
    need(bool(path_z) == bool(path_a),
         "P54Z_ET_P55A_EXIGES_ENSEMBLE")
    if not path_z:
        return None,None,{name:0 for name in p55a.STATES},0
    p54z_doc,sha = p55a.upstream(path_z)
    p55a_doc = p54z.read_json(p55a.private_source(path_a),100000)
    counts,inherited = p55a.validate_local(
        p55a_doc,p54z_doc,sha)
    return p54z_doc,p55a_doc,counts,inherited


def ready_for_visual(ref_index,upstream_z,upstream_a):
    if upstream_z is None or upstream_a is None:
        return False
    return (
        all(row["etat"] == "PREPARATION_DECLAREE_NON_VERIFIEE"
            for row in upstream_z["dossiers"][ref_index]["controles"])
        and all(row["etat"] == "PREPARE_NON_ATTESTE"
                for row in upstream_a["dossiers"][ref_index]["verifications"])
    )


def validate_private(doc,positions,upstream_z=None,upstream_a=None):
    standard = private_model(positions)
    need(type(doc) is dict and set(doc) == set(standard)
         and doc["schema_version"] == "P55C-FICHE-PRIVEE-1"
         and type(doc["exercice"]) is int and doc["exercice"] == 2024
         and type(doc["observations"]) is list
         and len(doc["observations"]) == 5,
         "P55C_FICHE_SCHEMA_INVALIDE")
    totals = {name:0 for name in STATES}
    counter = {name:0 for name in COUNTER_REVIEWS}
    qualifiers = {name:0 for name in QUALIFICATIONS}
    for index,(record,expected) in enumerate(zip(
            doc["observations"],standard["observations"])):
        fixed = (
            "reference","source","pdf_index_zero","index_observation_p54d",
            "offset_texte_nfkc","longueur_texte_nfkc",
        )
        need(type(record) is dict and set(record) == set(expected)
             and all(record[k] == expected[k] for k in fixed)
             and all(type(record[k]) is int for k in (
                 "pdf_index_zero","index_observation_p54d",
                 "offset_texte_nfkc","longueur_texte_nfkc")),
             "P55C_REPERES_MODIFIES_OU_CHAMPS_LIBRES")
        state = record["etat_revue"]
        kind = record["qualification_declaree"]
        second = record["contre_revue_declaree"]
        need(type(state) is str and state in STATES
             and type(kind) is str and kind in QUALIFICATIONS
             and type(second) is str and second in COUNTER_REVIEWS,
             "P55C_QUALIFICATION_OU_STATUT_INVALIDE")
        if state == "NON_EXAMINE":
            need(kind == "NON_QUALIFIE" and second == "NON_EFFECTUEE",
                 "P55C_AUCUNE_QUALIFICATION_SANS_REVUE")
        if state == "REPERE_DECLARE_NON_AUTHENTIFIE":
            need(ready_for_visual(index,upstream_z,upstream_a),
                 "P55C_REVUE_SANS_PREPARATION_P54Z_P55A")
        if second == "DECLAREE_DISTINCTE_NON_AUTHENTIFIEE":
            need(state == "REPERE_DECLARE_NON_AUTHENTIFIE"
                 and ready_for_visual(index,upstream_z,upstream_a),
                 "P55C_CONTRE_REVUE_SANS_BASE")
        if second == "DESACCORD_OUVERT":
            need(state in ("RESERVE_OUVERTE","SUSPENDU"),
                 "P55C_DESACCORD_SANS_RESERVE")
        totals[state] += 1
        counter[second] += 1
        qualifiers[kind] += 1
    need(sum(totals.values()) == 5
         and sum(counter.values()) == 5
         and sum(qualifiers.values()) == 5,
         "P55C_COUVERTURE_INCOMPLETE")
    return totals,counter,qualifiers


def public_report(states=None,attempt=None,claimed=None,
                  upstream_counts=None,inherited=0):
    if states is None:
        states = dict.fromkeys(p55b.PDF_CODES,p55b.NON_FOURNIE)
    need(type(states) is dict
         and set(states) == set(p55b.PDF_CODES)
         and all(v in (p55b.NON_FOURNIE,p55b.CONCORDANCE,p55b.EDITION)
                 for v in states.values()),"P55C_STATUTS_SOURCES_INVALIDES")
    if attempt is not None:
        p54q.p54p.validated_public_attempt(attempt)
        need(all(v == p55b.CONCORDANCE for v in states.values()),
             "P55C_REPRODUCTION_SANS_DEUX_COPIES")
    reproduced = (attempt is not None and
                  attempt["cinq_positions_reproduites"] is True)
    if claimed is None:
        claimed = ({name:(5 if name == "NON_EXAMINE" else 0)
                    for name in STATES},
                   {name:(5 if name == "NON_EFFECTUEE" else 0)
                    for name in COUNTER_REVIEWS},
                   {name:(5 if name == "NON_QUALIFIE" else 0)
                    for name in QUALIFICATIONS})
    totals,seconds,qualifiers = claimed
    for data,names in ((totals,STATES),(seconds,COUNTER_REVIEWS),
                       (qualifiers,QUALIFICATIONS)):
        need(type(data) is dict and set(data) == set(names)
             and all(type(v) is int and v >= 0 for v in data.values())
             and sum(data.values()) == 5,
             "P55C_COMPTEURS_INVALIDES")
    if upstream_counts is None:
        upstream_counts = {name:(50 if name == "NON_INSTRUIT" else 0)
                           for name in p55a.STATES}
    need(type(upstream_counts) is dict
         and set(upstream_counts) == set(p55a.STATES)
         and all(type(v) is int and v >= 0 for v in upstream_counts.values())
         and sum(upstream_counts.values()) == 50
         and type(inherited) is int and 0 <= inherited <= 40,
         "P55C_SOURCE_P55A_INVALIDE")
    need(reproduced or claimed[0] == {
         name:(5 if name == "NON_EXAMINE" else 0) for name in STATES},
         "P55C_REVUE_SANS_REPRODUCTION")
    need(reproduced or claimed[1] == {
         name:(5 if name == "NON_EFFECTUEE" else 0)
         for name in COUNTER_REVIEWS},
         "P55C_CONTRE_REVUE_SANS_REPRODUCTION")
    need(reproduced or claimed[2] == {
         name:(5 if name == "NON_QUALIFIE" else 0)
         for name in QUALIFICATIONS},
         "P55C_QUALIFICATION_SANS_REPRODUCTION")
    return {
        "schema_version":"P55C-BILAN-1","exercice":2024,
        "sources_pdf_locales_soumises":
            sum(s != p55b.NON_FOURNIE for s in states.values()),
        "copies_concordantes_historiques_non_authentifiees":
            sum(s == p55b.CONCORDANCE for s in states.values()),
        "editions_divergentes_a_instruire":
            sum(s == p55b.EDITION for s in states.values()),
        "positions_nfkc_reproduites_techniquement":5 if reproduced else 0,
        "observations_humaines_non_certifiees":5,
        "etats_revue_locaux_non_authentifies":dict(totals),
        "etats_contre_revues_non_authentifies":dict(seconds),
        "qualifications_declarees_non_certifiees":dict(qualifiers),
        "suspensions_p54z_heritees":inherited,
        "suspensions_p55a_non_levees":upstream_counts["SUSPENDU"],
        "reserves_p55a_non_levees":upstream_counts["RESERVE"],
        "suspensions_p55c_non_levees":totals["SUSPENDU"],
        "reserves_p55c_non_levees":totals["RESERVE_OUVERTE"],
        "desaccords_ouverts_p55c":seconds["DESACCORD_OUVERT"],
        "avis_independants_authentifies":0,
        "qualifications_definitives":0,
        "dossiers_p54e_ouverts":4,
        "date_probable_non_certifiee":1,
        "mandats_p54h_signes":0,
        "taches_p54n_non_attestees":40,
        "blocages_p54o_non_leves":10,
        "controles_p54b_non_attestes":96,
        "controles_p54c_non_attestes":8,
        "economies_certifiees_cad":None,
        "transmission_externe_autorisee":False,
        "cloture_des_dossiers_autorisee":False,
        "fusion_main_autorisee":False,
        "decision":NO_GO,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ville-pdf")
    parser.add_argument("--mamh-pdf")
    parser.add_argument("--declarations-p54z")
    parser.add_argument("--relecture-p55a")
    parser.add_argument("--creer-fiche-privee")
    parser.add_argument("--fiche-privee-p55c")
    parser.add_argument("--bilan-public")
    parser.add_argument("--exiger-go",action="store_true")
    opts=parser.parse_args(argv)
    try:
        configuration()
        need(not (opts.creer_fiche_privee and opts.fiche_privee_p55c),
             "P55C_CREATION_ET_RELECTURE_EXCLUSIVES")
        need(not (opts.creer_fiche_privee or opts.fiche_privee_p55c)
             or (opts.ville_pdf and opts.mamh_pdf),
             "P55C_FICHE_REQUIERT_DEUX_PDF")
        need(not opts.fiche_privee_p55c or
             (opts.declarations_p54z and opts.relecture_p55a),
             "P55C_FICHE_REQUIERT_P54Z_P55A")
        inputs = [x for x in (
            opts.ville_pdf,opts.mamh_pdf,
            opts.declarations_p54z,opts.relecture_p55a,
            opts.fiche_privee_p55c) if x]
        outputs = [x for x in (
            opts.creer_fiche_privee,opts.bilan_public) if x]
        read_paths = [p55a.private_source(p) for p in inputs]
        output_paths = [Path(p).expanduser().absolute() for p in outputs]
        need(len({p.resolve() for p in read_paths+output_paths}) ==
             len(read_paths+output_paths),
             "P55C_ENTREES_SORTIES_DUPLIQUEES")
        for path in output_paths:
            need(not path.exists() and not path.is_symlink()
                 and path.parent.is_dir() and not path.parent.is_symlink(),
                 "P55C_SORTIE_NON_AUTORISEE")
        if opts.creer_fiche_privee:
            p54z.outside_repo(opts.creer_fiche_privee)
        upstream_z,upstream_a,upstream_counts,inherited = upstream_claims(
            opts.declarations_p54z,opts.relecture_p55a)
        states,attempt = local_sources(opts.ville_pdf,opts.mamh_pdf)
        reproduced = attempt is not None and attempt["cinq_positions_reproduites"]
        if (opts.creer_fiche_privee or opts.fiche_privee_p55c) and not reproduced:
            return 4
        claimed = None
        if opts.fiche_privee_p55c:
            private = p54z.read_json(
                p55a.private_source(opts.fiche_privee_p55c),100000)
            claimed = validate_private(
                private,attempt["positions"],upstream_z,upstream_a)
        public = public_report(states,attempt,claimed,
                               upstream_counts,inherited)
        if opts.creer_fiche_privee:
            p54z.write_new(
                opts.creer_fiche_privee,
                private_model(attempt["positions"]),private=True)
        if opts.bilan_public:
            p54z.write_new(opts.bilan_public,public)
        print(json.dumps(public,ensure_ascii=False,sort_keys=True))
        if opts.exiger_go:
            return 3
        if opts.ville_pdf and not reproduced:
            return 4
        return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,
            json.JSONDecodeError,ImportError):
        print("P55C_REFUS: COPIES_OU_FICHE_NON_CONFORMES",
              file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
