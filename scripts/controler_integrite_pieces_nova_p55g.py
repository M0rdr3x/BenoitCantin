#!/usr/bin/env python3
"""P55G — empreintes locales et reçu privé; aucune authentification humaine."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

import verifier_interpretation_sources_nova_p55f as p55f

p55e=p55f.p55e
p55d=p55f.p55d
p55c=p55f.p55c
p55b=p55f.p55b
p55a=p55f.p55a
p54z=p55f.p54z
BASE=p55d.BASE
CONFIG=BASE/"P55G_REFERENTIEL_RECU_INTEGRITE_2024.json"
NO_GO=p55d.NO_GO
CODES=p55b.PDF_CODES
MISSING="NON_FOURNIE"
MATCH="CONCORDANCE_OCTETS_HISTORIQUES_NON_AUTHENTIFIANTE"
DIVERGENT="EDITION_DIVERGENTE_A_INSTRUIRE"
STATES=(MISSING,MATCH,DIVERGENT)
GUARDS={
    "aucun_telechargement_automatique",
    "aucun_contact_avec_institutions",
    "controle_uniquement_fichiers_locaux",
    "deux_pdfs_ou_aucun",
    "sources_0600_et_hors_git",
    "liens_symboliques_interdits",
    "lecture_sans_modifier_octets",
    "limite_taille_pdfs_vingt_mo",
    "verification_sha256_par_flux",
    "verification_stabilite_fichiers",
    "refs_historiques_p54q_immuables",
    "edition_differente_mise_en_reserve",
    "pas_de_substitution_silencieuse",
    "pas_de_reproduction_nkfc_si_edition_differe",
    "cinq_positions_p55c_obligatoires_pour_reproduction",
    "controle_apres_reproduction_pour_eviter_changement_octets",
    "recu_prive_nouveaute_non_ecrasante",
    "recu_prive_ancre_fichiers_par_sha",
    "aucune_signature_dans_recu",
    "aucun_texte_pdf_dans_recu",
    "aucun_chemin_prive_dans_recu",
    "bilan_public_sans_sha_ni_chemin",
    "aucun_avis_professionnel_cree",
    "aucune_reception_institutionnelle_attestee",
    "pas_de_double_compte_ville_rtc_somhac",
    "redressement_2023_non_comptabilise_economie_2024",
    "emplois_services_pouvoir_achat_proteges",
    "deux_scenarios_constitutionnels_distincts",
    "deux_mandats_non_signes",
    "quatre_dossiers_et_date_ouverts",
    "p54n_40_p54o_10_p54b_96_p54c_8_ouverts",
    "aucune_economie_certifiee",
    "aucune_transmission_automatique",
    "aucune_fusion_main",
    "aucune_modification_sinjira",
    "no_go_automatique",
}
INITIAL={
    "documents_attendus":2,
    "documents_fournis":0,
    "sha256_actuels_calcules":0,
    "copies_correspondantes_aux_references_historiques":0,
    "positions_nfkc_reproduites":0,
    "avis_independants_authentifies":0,
    "mandats_professionnels_signes":0,
    "dossiers_p54e_ouverts":4,
    "date_probable_non_certifiee":1,
    "taches_p54n_non_attestees":40,
    "blocages_p54o_non_leves":10,
    "controles_p54b_non_attestes":96,
    "controles_p54c_non_attestes":8,
    "economies_certifiees_cad":None,
    "decision":NO_GO,
}


def need(condition,reason):
    if not condition:
        raise ValueError(reason)


def configuration():
    config=p54z.read_json(CONFIG)
    need(config=={
        "schema_version":"P55G-1","date_reference":"2026-11-03",
        "exercice":2024,
        "sources":["P54Q","P55B","P55C","P55D","P55E","P55F"],
        "codes_documents":list(CODES),
        "etats":list(STATES),
        "type_recu":"P55G-RECU-PRIVE-1",
        "protections":{key:True for key in GUARDS},
        "etat_initial":INITIAL,
    },"P55G_REFERENCE_ALTEREE")
    previous=p55f.configuration()
    need(previous["schema_version"]=="P55F-1"
         and previous["etat_initial"]["decision"]==NO_GO
         and previous["verrous_interpretation"]
             ["redressement_comparatif_2023_cad"]==1825176
         and len(p55b.SOURCE_DATA)==2
         and tuple(r[0] for r in p55b.SOURCE_DATA)==CODES,
         "P55G_CHAINAGE_P55F_P55B_INVALIDE")
    return config


def checksum_pdf(path,max_size=20_000_000):
    """Read one private regular PDF, fail closed on replacement or modification."""
    f=p55a.private_source(path)
    first=f.stat()
    need(stat.S_ISREG(first.st_mode)
         and 5<=first.st_size<=max_size,"P55G_TAILLE_OU_TYPE_INTERDIT")
    flags=os.O_RDONLY
    if hasattr(os,"O_NOFOLLOW"):
        flags|=os.O_NOFOLLOW
    fd=os.open(f,flags)
    with os.fdopen(fd,"rb") as stream:
        before=os.fstat(stream.fileno())
        identity=lambda st:(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
        need(stat.S_ISREG(before.st_mode)
             and (before.st_mode & 0o777)==0o600
             and identity(before)==identity(first),
             "P55G_FICHIER_REMPLACE_AVANT_LECTURE")
        need(stream.read(5)==b"%PDF-","P55G_SIGNATURE_ENTETE_PDF_ABSENTE")
        stream.seek(0)
        digest=hashlib.sha256()
        length=0
        while True:
            chunk=stream.read(1024*1024)
            if not chunk:break
            length+=len(chunk)
            need(length<=max_size,"P55G_TAILLE_DEPASSEE")
            digest.update(chunk)
        after=os.fstat(stream.fileno())
        need(identity(before)==identity(after)
             and length==first.st_size,
             "P55G_FICHIER_MODIFIE_PENDANT_LECTURE")
    on_path=f.stat()
    need(identity(before)==identity(on_path),
         "P55G_FICHIER_REMPLACE_APRES_LECTURE")
    return length,digest.hexdigest()


def capture_pair(ville,mamh):
    need(bool(ville) and bool(mamh),"P55G_DEUX_COPIES_REQUISES")
    source_paths=(p55a.private_source(ville),p55a.private_source(mamh))
    need(source_paths[0].resolve()!=source_paths[1].resolve(),
         "P55G_SOURCES_DUPLIQUEES")
    rows=[]
    for file,(code,_org,_url,_key,_page,size,sha,_refs) in zip(
            source_paths,p55b.SOURCE_DATA):
        count,calculated=checksum_pdf(file)
        rows.append({
            "code":code,
            "taille_octets_lus":count,
            "sha256_octets_lus":calculated,
            "statut":MATCH if count==size and calculated==sha else DIVERGENT,
        })
    need(len(rows)==2 and [r["code"] for r in rows]==list(CODES),
         "P55G_SOURCES_DEPLACEES")
    return rows


def joint_hash(rows):
    # Metadata digest: protection against accidental change, not a signature.
    payload=json.dumps(rows,sort_keys=True,separators=(",",":"),
                       ensure_ascii=True).encode("utf8")
    return hashlib.sha256(payload).hexdigest()


def make_receipt(rows,reproduced=False,checked_at=None):
    valid_rows(rows)
    need(type(reproduced) is bool
         and (not reproduced or all(r["statut"]==MATCH for r in rows)),
         "P55G_REPRODUCTION_INCOHERENTE")
    if checked_at is None:
        checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds")
    need(type(checked_at) is str
         and re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\+00:00",
                          checked_at) is not None
         and datetime.fromisoformat(checked_at).tzinfo is not None,
         "P55G_DATE_CONTROLE_INVALIDE")
    return {
        "schema_version":"P55G-RECU-PRIVE-1","exercice":2024,
        "controle_informatique_utc":checked_at,
        "sources":rows,
        "sha256_ensemble_metadonnees":joint_hash(rows),
        "positions_nfkc_reproduites_techniquement":5 if reproduced else 0,
        "absence_authentification_emetteur":True,
        "absence_signature_professionnelle":True,
        "absence_attestation_de_provenance":True,
        "absence_certification_comptable":True,
        "decision":NO_GO,
    }


def valid_rows(rows):
    need(type(rows) is list and len(rows)==2,
         "P55G_DEUX_ENREGISTREMENTS_REQUIS")
    for row,code in zip(rows,CODES):
        need(type(row) is dict
             and set(row)=={
                 "code","taille_octets_lus","sha256_octets_lus","statut"}
             and row["code"]==code
             and type(row["taille_octets_lus"]) is int
             and 5<=row["taille_octets_lus"]<=20_000_000
             and type(row["sha256_octets_lus"]) is str
             and re.fullmatch("[0-9a-f]{64}",row["sha256_octets_lus"]) is not None
             and row["statut"] in (MATCH,DIVERGENT),
             "P55G_LIGNE_SOURCE_INVALIDE")
        expected=next((s for s in p55b.SOURCE_DATA if s[0]==code),None)
        need(expected is not None,"P55G_SOURCE_INCONNUE")
        should=MATCH if (
            row["taille_octets_lus"]==expected[5]
            and row["sha256_octets_lus"]==expected[6]
        ) else DIVERGENT
        need(row["statut"]==should,"P55G_STATUT_NON_CONFORME_AUX_OCTETS")
    return rows


def verify_receipt(data,rows,reproduced):
    need(type(data) is dict and set(data)=={
         "schema_version","exercice","controle_informatique_utc",
         "sources","sha256_ensemble_metadonnees",
         "positions_nfkc_reproduites_techniquement",
         "absence_authentification_emetteur",
         "absence_signature_professionnelle",
         "absence_attestation_de_provenance",
         "absence_certification_comptable","decision"},
         "P55G_RECU_CHAMPS_INCONNUS")
    need(data["schema_version"]=="P55G-RECU-PRIVE-1"
         and type(data["exercice"]) is int and data["exercice"]==2024,
         "P55G_RECU_EXERCICE_INVALIDE")
    expected=make_receipt(rows,reproduced,
                          checked_at=data["controle_informatique_utc"])
    need(data==expected,"P55G_RECU_OU_OCTETS_MODIFIES")
    return True


def public_report(rows=None,reproduced=False,receipt_checked=False):
    need(type(reproduced) is bool and type(receipt_checked) is bool,
         "P55G_FLAGS_INVALIDES")
    if rows is None:
        states={key:p55b.NON_FOURNIE for key in CODES}
        need(not reproduced and not receipt_checked,
             "P55G_AUCUN_RECU_SANS_COPIES")
    else:
        valid_rows(rows)
        states={r["code"]:p55b.CONCORDANCE
                if r["statut"]==MATCH else p55b.EDITION for r in rows}
    parent=p55e.report(states,reproduced)
    need(parent["decision"]==NO_GO
         and parent["economies_certifiees_cad"] is None
         and not parent["transmission_externe_autorisee"],
         "P55G_PARENT_NON_NEUTRE")
    return {
        "schema_version":"P55G-BILAN-PUBLIC-1","exercice":2024,
        "copies_attendues":2,
        "copies_locales_fournies":0 if rows is None else 2,
        "copies_concordantes_historique_non_authentifiees":
            sum(r["statut"]==MATCH for r in rows) if rows else 0,
        "editions_divergentes_a_instruire":
            sum(r["statut"]==DIVERGENT for r in rows) if rows else 0,
        "positions_nfkc_reproduites_techniquement":5 if reproduced else 0,
        "recu_prive_recontrole_octets":receipt_checked,
        "recu_prive_est_attestation_de_provenance":False,
        "source_actuelle_authentifiee_par_emetteur":False,
        "avis_professionnels_authentifies":0,
        "mandats_professionnels_signes":0,
        "etape_prioritaire_p55e":parent["phase_prioritaire"],
        "prochaines_actions_p55e":parent["prochaines_actions_codes"],
        "dossiers_p54e_ouverts":4,
        "date_probable_non_certifiee":1,
        "taches_p54n_non_attestees":40,
        "blocages_p54o_non_leves":10,
        "controles_p54b_non_attestes":96,
        "controles_p54c_non_attestes":8,
        "redressement_comparatif_2023_est_economie_2024":False,
        "eliminations_ville_rtc_somhac_sont_gains_nouveaux":False,
        "economies_certifiees_cad":None,
        "transmission_externe_autorisee":False,
        "fusion_main_autorisee":False,
        "decision":NO_GO,
    }


def public_plan():
    return {
        "schema_version":"P55G-PLAN-PUBLIC-1","exercice":2024,
        "sources_officielles_a_obtenir":[
            {"code":s["code"],"url_officielle":s["url_officielle"]}
            for s in p55b.expected_sources()
        ],
        "procedure":[
            "OBTENIR_LEGALEMENT_DEUX_VERSIONS_HORS_GIT",
            "CONSERVER_LA_PROVENANCE_AU_DOSSIER_HUMAIN",
            "CONTROLER_0600_ET_LIENS_SYMBOLIQUES",
            "CALCULER_SHA256_TAILLE_ET_STABILITE",
            "CONFRONTER_REFERENCES_IMMUABLES_P54Q",
            "REPRODUIRE_CINQ_POSITIONS_SI_CONCORDANCE",
            "REVERIFIER_LES_OCTETS_APRES_REPRODUCTION",
            "CREER_RECU_PRIVE_ET_CONSERVER_SANS_ECRASER",
            "EXAMINER_VISUELLEMENT_ET_MANDATER_HUMAINS",
        ],
        "recu_n_est_pas_signature":True,
        "aucun_pdf_telecharge_automatiquement":True,
        "aucune_economie_certifiee":True,
        "decision":NO_GO,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ville-pdf")
    parser.add_argument("--mamh-pdf")
    parser.add_argument("--creer-recu-prive")
    parser.add_argument("--verifier-recu-prive")
    parser.add_argument("--bilan-public")
    parser.add_argument("--plan-public")
    parser.add_argument("--exiger-authenticite",action="store_true")
    a=parser.parse_args(argv)
    try:
        configuration()
        need(bool(a.ville_pdf)==bool(a.mamh_pdf),
             "P55G_COPIES_INSEPARABLES")
        need(not (a.creer_recu_prive and a.verifier_recu_prive),
             "P55G_RECU_LECTURE_CREATION_EXCLUSIVES")
        need(not (a.creer_recu_prive or a.verifier_recu_prive)
             or bool(a.ville_pdf),"P55G_RECU_EXIGE_PDF")
        p55e.validate_inputs(
            [a.ville_pdf,a.mamh_pdf,a.verifier_recu_prive],
            [a.creer_recu_prive,a.bilan_public,a.plan_public])
        if a.creer_recu_prive:
            p54z.outside_repo(a.creer_recu_prive)
        rows=None
        reproduced=False
        checked=False
        failed_reproduction=False
        if a.ville_pdf:
            rows=capture_pair(a.ville_pdf,a.mamh_pdf)
            if all(row["statut"]==MATCH for row in rows):
                try:
                    statuses,attempt=p55c.local_sources(a.ville_pdf,a.mamh_pdf)
                    reproduced=(all(st==p55b.CONCORDANCE
                                    for st in statuses.values())
                                and attempt is not None
                                and attempt["cinq_positions_reproduites"] is True)
                except (ValueError,KeyError,TypeError,OSError):
                    # A parser failure is a technical obstruction, not a finance finding.
                    failed_reproduction=True
                # Second stream verifies originals weren't swapped after parsing.
                again=capture_pair(a.ville_pdf,a.mamh_pdf)
                need(rows==again,"P55G_SOURCE_MODIFIEE_APRES_REPRODUCTION")
            if a.verifier_recu_prive:
                received=p54z.read_json(
                    p55a.private_source(a.verifier_recu_prive),100000)
                verify_receipt(received,rows,reproduced)
                checked=True
        result=public_report(rows,reproduced,checked)
        if a.creer_recu_prive:
            p54z.write_new(a.creer_recu_prive,
                           make_receipt(rows,reproduced),private=True)
        if a.bilan_public:
            p54z.write_new(a.bilan_public,result)
        if a.plan_public:
            p54z.write_new(a.plan_public,public_plan())
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        if a.exiger_authenticite:
            return 3
        return 4 if (a.ville_pdf and
                     (not reproduced or failed_reproduction)) else 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError,
            json.JSONDecodeError,ImportError):
        print("P55G_REFUS: COPIES_OU_RECU_NON_CONFORMES",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
