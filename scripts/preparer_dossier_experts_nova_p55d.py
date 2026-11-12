#!/usr/bin/env python3
"""P55D — dossier de recevabilité non certifiant, hors Git et sans contacts."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import rapprocher_pieces_documentaires_nova_p55c as p55c

p55b = p55c.p55b
p55a = p55c.p55a
p54z = p55c.p54z
BASE = p55c.BASE
CONFIG = BASE / "P55D_REGISTRE_RECEVABILITE_EXPERTS_2024.json"
NO_GO = p55c.NO_GO
REFS = p55a.REFS
GATES = (
    ("ORIGINAL_VERSIONNE","Copie source 2024, provenance et edition",
     "GARANT_DOCUMENTAIRE"),
    ("PAGE_VISUELLE","Page PDF revue visuellement","LECTEUR_DOCUMENTAIRE"),
    ("EXTRACTION_ET_CONTEXTE","Occurrence NFKC confrontee au contexte",
     "LECTEUR_DOCUMENTAIRE"),
    ("QUALIFICATION_UNITE_EXERCICE","Unite, exercice, signe et colonne",
     "CPA_SI_MONETAIRE"),
    ("PORTEE_JURIDIQUE_AUDIT","Portee RAVQ 1435 et limites de l avis",
     "JURISTE_SI_NECESSAIRE"),
    ("PERIMETRE_ET_CONSOLIDATION","Rapprochement Ville RTC SOMHAC sans double compte",
     "CPA"),
    ("CONTRE_REVUE_ET_RESERVES","Contre revue et contradictions",
     "CONTRE_LECTEUR"),
    ("EMPLOIS_SERVICES_POUVOIR_ACHAT","Continuite des services et effet social",
     "RESPONSABLE_POLITIQUES_PUBLIQUES"),
)
STATES = (
    "A_COLLECTER","PREPARATION_DECLAREE_NON_ATTESTEE",
    "RESERVE","INACCESSIBLE","SUSPENDU",
)
MANDATES = p55b.MANDATES
GUARDS = {
    "deux_pdfs_historiques_concordants_requis",
    "cinq_positions_p55c_reproduites_obligatoires",
    "p54z_p55a_p55c_sources_privees_0600",
    "ancrage_sha256_fiche_p55c",
    "aucun_offset_sha_prive_ou_texte_bilan",
    "aucune_identite_signature_devis_dans_git",
    "pas_de_reseau_ni_contact_tiers",
    "schema_ferme_sans_texte_libre",
    "declarations_non_authentifiantes",
    "aucune_qualification_definitive_automatique",
    "aucun_expert_engage",
    "deux_mandats_p54h_non_transmis",
    "suspensions_reserves_contradictions_non_levees",
    "edition_changee_bloque",
    "quatre_dossiers_p54e_ouverts",
    "date_probable_non_qualifiee",
    "p54n_40_non_attestees",
    "p54o_10_blocages",
    "p54b_96_p54c_8_non_attestes",
    "aucune_economie_certifiee",
    "pas_de_double_compte_ville_rtc_somhac",
    "emplois_services_pouvoir_achat_proteges",
    "deux_regimes_constitutionnels_distincts",
    "aucune_transmission_ni_depense",
    "aucun_changement_sinjira",
    "aucune_fusion_main",
    "no_go_automatique",
}
INITIAL = {
    "observations":5,"exigences_par_observation":8,
    "positions_a_instruire":40,
    "copies_pdf_verifiees_sur_place":0,"reproductions_nfkc":0,
    "pieces_authentifiees":0,"contre_revues_authentifiees":0,
    "mandats_professionnels_signes":0,"avis_authentifies":0,
    "dossiers_p54e_ouverts":4,"date_probable_non_certifiee":1,
    "taches_p54n_non_attestees":40,"blocages_p54o_non_leves":10,
    "controles_p54b_non_attestes":96,"controles_p54c_non_attestes":8,
    "economies_certifiees_cad":None,"decision":NO_GO,
}


def need(condition,reason):
    if not condition:
        raise ValueError(reason)


def expected_gates():
    return [
        {"code":code,"livrable_attendu":livrable,"role_requis_a_designer":role}
        for code,livrable,role in GATES
    ]


def configuration():
    cfg = p54z.read_json(CONFIG)
    expected = {
        "schema_version":"P55D-1","date_reference":"2026-11-03",
        "exercice":2024,
        "chaines_precedentes":[
            "P54H","P54N","P54O","P54Q","P54Z","P55A","P55B","P55C"],
        "references":list(REFS),
        "controles":expected_gates(),
        "statuts_declaratifs":list(STATES),
        "mandats_sans_engagement":list(MANDATES),
        "protections":{key:True for key in GUARDS},
        "etat_initial":INITIAL,
    }
    need(cfg == expected,"P55D_CONFIGURATION_MODIFIEE")
    parent = p55c.configuration()
    need(parent["schema_version"] == "P55C-1"
         and parent["etat_initial"]["decision"] == NO_GO
         and [x["reference"] for x in parent["observations"]] == list(REFS)
         and p55b.configuration()["mandats_p54h_non_transmis"] == list(MANDATES),
         "P55D_CHAINAGE_INVALIDE")
    return cfg


def empty_counts():
    return {state:(40 if state == "A_COLLECTER" else 0) for state in STATES}


def private_model(raw_p55c):
    need(type(raw_p55c) is bytes and 0 < len(raw_p55c) <= 100000,
         "P55C_OCTETS_PRIVEs_INCORRECTS")
    return {
        "schema_version":"P55D-SUIVI-LOCAL-1",
        "exercice":2024,
        "sha256_fiche_p55c":hashlib.sha256(raw_p55c).hexdigest(),
        "observations":[
            {"reference":ref,
             "exigences":[{"code":code,"etat":"A_COLLECTER"}
                          for code,_livrable,_role in GATES]}
            for ref in REFS
        ],
    }


def is_prepared(index,z,a,c):
    if z is None or a is None or c is None:
        return False
    return (p55c.ready_for_visual(index,z,a)
            and c["observations"][index]["etat_revue"] ==
                "REPERE_DECLARE_NON_AUTHENTIFIE"
            and c["observations"][index]["contre_revue_declaree"] ==
                "DECLAREE_DISTINCTE_NON_AUTHENTIFIEE")


def validate_followup(doc,raw_p55c,z,a,c):
    expected=private_model(raw_p55c)
    need(type(doc) is dict and set(doc)==set(expected)
         and doc["schema_version"]=="P55D-SUIVI-LOCAL-1"
         and type(doc["exercice"]) is int and doc["exercice"]==2024
         and type(doc["sha256_fiche_p55c"]) is str
         and doc["sha256_fiche_p55c"]==expected["sha256_fiche_p55c"]
         and type(doc["observations"]) is list
         and len(doc["observations"])==len(REFS),
         "P55D_SCHEMA_OU_ANCRAGE_FICHE_INVALIDE")
    totals={name:0 for name in STATES}
    for i,(case,template) in enumerate(
            zip(doc["observations"],expected["observations"])):
        need(type(case) is dict and set(case)==set(template)
             and case["reference"]==REFS[i]
             and type(case["exigences"]) is list
             and len(case["exigences"])==len(GATES),
             "P55D_DOSSIER_OU_GRILLE_INVALIDE")
        for j,(cell,baseline) in enumerate(
                zip(case["exigences"],template["exigences"])):
            need(type(cell) is dict and set(cell)=={"code","etat"}
                 and cell["code"]==baseline["code"]
                 and type(cell["etat"]) is str
                 and cell["etat"] in STATES,
                 "P55D_CHAMP_OU_ETAT_INVALIDE")
            if cell["etat"]=="PREPARATION_DECLAREE_NON_ATTESTEE":
                need(is_prepared(i,z,a,c),
                     "P55D_PREPARATION_SANS_P55C_ET_DOUBLE_CONTROLE")
            totals[cell["etat"]]+=1
    need(sum(totals.values())==40,"P55D_COUVERTURE_INCOMPLETE")
    return totals


def upstream(path_z=None,path_a=None,path_c=None,positions=None):
    supplied=(path_z,path_a,path_c)
    need(not any(supplied) or all(supplied),
         "P55D_FICHES_P54Z_P55A_P55C_INDISSOCIABLES")
    if not all(supplied):
        return None,None,None,None,{
            name:(50 if name=="NON_INSTRUIT" else 0)
            for name in p55a.STATES},0,(5,0,0)
    need(positions is not None,"P55D_REPRODUCTION_CINQ_POSITIONS_REQUISE")
    z,a,counts,inherited=p55c.upstream_claims(path_z,path_a)
    sheet=p55a.private_source(path_c)
    raw=sheet.read_bytes()
    need(len(raw)<=100000,"P55D_FICHE_P55C_TROP_GRANDE")
    c=p54z.read_json(sheet,100000)
    local=p55c.validate_private(c,positions,z,a)
    return z,a,c,raw,counts,inherited,(
        local[0]["NON_EXAMINE"],
        local[0]["SUSPENDU"],
        local[0]["RESERVE_OUVERTE"] + local[1]["DESACCORD_OUVERT"])


def public_report(states=None,reproduced=False,followup=None,
                  inherited_z=0,upstream_a=None,upstream_c=None):
    if states is None:
        states=dict.fromkeys(p55b.PDF_CODES,p55b.NON_FOURNIE)
    need(type(states) is dict and set(states)==set(p55b.PDF_CODES)
         and all(s in (p55b.NON_FOURNIE,p55b.CONCORDANCE,p55b.EDITION)
                 for s in states.values())
         and type(reproduced) is bool
         and (not reproduced or all(s==p55b.CONCORDANCE for s in states.values())),
         "P55D_SOURCES_OU_REPRODUCTION_INCOHERENTES")
    if followup is None:
        followup=empty_counts()
    need(type(followup) is dict and set(followup)==set(STATES)
         and all(type(n) is int and n>=0 for n in followup.values())
         and sum(followup.values())==40,
         "P55D_COMPTEURS_INCOHERENTS")
    if upstream_a is None:
        upstream_a={name:(50 if name=="NON_INSTRUIT" else 0)
                    for name in p55a.STATES}
    if upstream_c is None:
        upstream_c=(5,0,0)
    need(type(upstream_a) is dict and set(upstream_a)==set(p55a.STATES)
         and all(type(n) is int and n>=0 for n in upstream_a.values())
         and sum(upstream_a.values())==50
         and type(inherited_z) is int and 0<=inherited_z<=40
         and type(upstream_c) is tuple and len(upstream_c)==3
         and all(type(n) is int and n>=0 for n in upstream_c)
         and upstream_c[0]+upstream_c[1]<=5,
         "P55D_HERITAGE_INVALIDE")
    need(reproduced or followup==empty_counts(),
         "P55D_SUIVI_SANS_PDF_REPRODUITS")
    return {
        "schema_version":"P55D-BILAN-PUBLIC-1","exercice":2024,
        "copies_pdf_concordantes_octets_non_authentifiees":
            sum(s==p55b.CONCORDANCE for s in states.values()),
        "editions_differentes_a_instruire":
            sum(s==p55b.EDITION for s in states.values()),
        "sources_non_fournies":
            sum(s==p55b.NON_FOURNIE for s in states.values()),
        "positions_nfkc_reproduites":5 if reproduced else 0,
        "observations_2024_non_certifiees":5,
        "exigences_preparatoires":40,
        "suivi_local_declaratif_non_authentifie":dict(followup),
        "suspensions_p54z_heritees":inherited_z,
        "reserves_p55a_heritees":upstream_a["RESERVE"],
        "suspensions_p55a_heritees":upstream_a["SUSPENDU"],
        "relectures_p55c_non_examinees":upstream_c[0],
        "suspensions_p55c_heritees":upstream_c[1],
        "reserves_et_desaccords_p55c":upstream_c[2],
        "exigences_p55d_inaccessibles":followup["INACCESSIBLE"],
        "exigences_p55d_reserves":followup["RESERVE"],
        "exigences_p55d_suspendues":followup["SUSPENDU"],
        "pieces_professionnelles_authentifiees":0,
        "avis_independants_authentifies":0,
        "mandats_p54h_reels_signes":0,
        "dossiers_p54e_ouverts":4,
        "date_probable_non_certifiee":1,
        "taches_p54n_non_attestees":40,
        "blocages_p54o_non_leves":10,
        "controles_p54b_non_attestes":96,
        "controles_p54c_non_attestes":8,
        "economies_certifiees_cad":None,
        "envoi_dossier_a_expert_autorise":False,
        "engagement_de_depense_autorise":False,
        "cloture_dossier_autorisee":False,
        "fusion_main_autorisee":False,
        "decision":NO_GO,
    }


def public_plan():
    return {
        "schema_version":"P55D-PLAN-PUBLIC-1","exercice":2024,
        "references_non_certifiees":list(REFS),
        "sources_officielles_a_obtenir":[
            {"code":entry["code"],
             "url_officielle":entry["url_officielle"],
             "pdf_index_zero":entry["pdf_index_zero"]}
            for entry in p55b.expected_sources()],
        "exigences_par_observation":expected_gates(),
        "mandats_projets_non_transmis":list(MANDATES),
        "total_exigences":40,
        "expert_mandate":False,
        "envoi_autorise":False,
        "decision":NO_GO,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ville-pdf")
    parser.add_argument("--mamh-pdf")
    parser.add_argument("--declarations-p54z")
    parser.add_argument("--relecture-p55a")
    parser.add_argument("--fiche-p55c")
    parser.add_argument("--creer-suivi-prive")
    parser.add_argument("--suivi-prive")
    parser.add_argument("--bilan-public")
    parser.add_argument("--plan-public")
    parser.add_argument("--exiger-transmission",action="store_true")
    a=parser.parse_args(argv)
    try:
        configuration()
        need(not (a.creer_suivi_prive and a.suivi_prive),
             "P55D_CREATION_ET_LECTURE_EXCLUSIVES")
        need(bool(a.ville_pdf)==bool(a.mamh_pdf),
             "P55D_DEUX_PDF_REQUIS_ENSEMBLE")
        need(not any((a.creer_suivi_prive,a.suivi_prive))
             or all((a.ville_pdf,a.mamh_pdf,
                     a.declarations_p54z,a.relecture_p55a,a.fiche_p55c)),
             "P55D_DOSSIER_PRIVE_REQUIERT_CHAINE_COMPLETE")
        need(not any((a.declarations_p54z,a.relecture_p55a,a.fiche_p55c))
             or all((a.declarations_p54z,a.relecture_p55a,a.fiche_p55c,
                     a.ville_pdf,a.mamh_pdf)),
             "P55D_SOURCES_PRIVEES_INCOMPLETES")
        sources=[x for x in (
            a.ville_pdf,a.mamh_pdf,a.declarations_p54z,a.relecture_p55a,
            a.fiche_p55c,a.suivi_prive) if x]
        targets=[x for x in (
            a.creer_suivi_prive,a.bilan_public,a.plan_public) if x]
        inp=[p55a.private_source(x) for x in sources]
        out=[Path(x).expanduser().absolute() for x in targets]
        need(len({x.resolve() for x in inp+out})==len(inp+out),
             "P55D_CHEMINS_CONFONDUS")
        for path in out:
            need(path.parent.is_dir() and not path.parent.is_symlink()
                 and not path.exists() and not path.is_symlink(),
                 "P55D_SORTIE_EXISTANTE_OU_INVALIDE")
        if a.creer_suivi_prive:
            p54z.outside_repo(a.creer_suivi_prive)
        states,attempt=p55c.local_sources(a.ville_pdf,a.mamh_pdf)
        reproduced=(attempt is not None and
                    attempt["cinq_positions_reproduites"] is True)
        if any((a.creer_suivi_prive,a.suivi_prive)) and not reproduced:
            return 4
        positions=attempt["positions"] if reproduced else None
        z,up_a,c,raw,counts,inherited,review=upstream(
            a.declarations_p54z,a.relecture_p55a,a.fiche_p55c,positions)
        followup=None
        if a.suivi_prive:
            doc=p54z.read_json(p55a.private_source(a.suivi_prive),100000)
            followup=validate_followup(doc,raw,z,up_a,c)
        summary=public_report(states,reproduced,followup,inherited,counts,review)
        if a.creer_suivi_prive:
            p54z.write_new(a.creer_suivi_prive,private_model(raw),private=True)
        if a.bilan_public:
            p54z.write_new(a.bilan_public,summary)
        if a.plan_public:
            p54z.write_new(a.plan_public,public_plan())
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        if a.exiger_transmission:
            return 3
        if a.ville_pdf and not reproduced:
            return 4
        return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,
            json.JSONDecodeError,ImportError):
        print("P55D_REFUS: DOSSIER_OU_SOURCES_NON_CONFORMES",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
