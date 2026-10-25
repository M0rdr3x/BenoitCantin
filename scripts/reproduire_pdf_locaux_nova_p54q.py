#!/usr/bin/env python3
"""P54Q — Reproduction PDF strictement locale, sans réseau et sans attestation.

Les deux copies publiques 2024 doivent être fournies par chemin extérieur
au dépôt. Aucune copie, aucun jeton, aucun chemin n'entre dans le bilan.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

import reproduire_localisations_pdf_nova_p54p as p54p

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54Q_SOURCES_PDF_LOCALES_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
NAMES=p54p.NAMES
GUARDS={
 "deux_pdf_locaux_obligatoires","aucune_requete_reseau",
 "chemins_fichiers_hors_depot","liens_symboliques_refuses",
 "fichiers_reguliers_uniquement","empreintes_et_tailles_exigees",
 "pypdf_version_epinglee","p54p_source_de_verite",
 "aucune_position_si_copie_manquante",
 "aucune_position_si_edition_differente",
 "aucun_jeton_ou_contexte_publie",
 "aucun_chemin_local_publie","aucune_signature_authentifiee",
 "aucune_anomalie_monetaire_inferree","date_probable_non_certifiee",
 "quatre_dossiers_p54e_ouverts",
 "pas_de_double_compte_ville_rtc_somhac",
 "emplois_services_proteges","scenarios_constitutionnels_separes",
 "main_non_fusionnee","sinjira_inchange","no_go_automatique",
}
INITIAL={
 "copies_locales_soumises":0,
 "copies_verifiees_par_sha":0,
 "positions_reproduites":0,
 "dossiers_p54e_ouverts":4,
 "occurrence_date_probable_non_certifiee":1,
 "controles_p54b_non_attestes":96,
 "controles_p54c_non_attestes":8,
 "avis_professionnels_authentifies":0,
 "economies_certifiees_cad":None,
 "decision":NO_GO,
}

def need(condition,message):
    if not condition:raise ValueError(message)

def configuration():
    parent=p54p.configuration()
    expected={
      "schema_version":"P54Q-1",
      "date_reference":"2026-10-24","exercice":2024,
      "source_jalon":"P54P","source_p54d_run":40120462237,
      "copies":parent["sources"],
      "protections":{key:True for key in GUARDS},
      "etat_initial":INITIAL,
    }
    need(json.loads(CONFIG.read_text("utf-8"))==expected
         and parent["source_run_p54d"]==40120462237
         and set(parent["sources"])==set(NAMES),
         "CONFIGURATION_P54Q_OU_SOURCE_P54P_ALTEREE")
    return expected

def checked_local_paths(paths):
    """Reject hidden symlinks, duplicates, directories and any repo copy."""
    need(type(paths) is dict and set(paths)==set(NAMES),
         "DEUX_COPIES_PDF_OBLIGATOIRES")
    validated={}
    seen=set()
    for key in NAMES:
        userpath=paths[key]
        need(isinstance(userpath,(str,Path)) and str(userpath),
             "CHEMIN_PDF_INVALIDE")
        original=Path(userpath).expanduser().absolute()
        need(not any(part.is_symlink() for part in
                     (original,*original.parents)),
             "SYMLINK_SOURCE_INTERDIT")
        resolved=original.resolve(strict=True)
        need(resolved not in seen and ROOT not in (
             resolved,*resolved.parents),
             "CHEMIN_DUPLIQUE_OU_FICHIER_DANS_GIT")
        seen.add(resolved)
        info=resolved.stat()
        need(stat.S_ISREG(info.st_mode) and info.st_size>=5,
             "PDF_LOCAL_NON_REGULIER")
        validated[key]=resolved
    return validated

def read_copy(source,path,expected):
    """Read an exact-size local file with no remote calls or retained copies."""
    ref=expected[source]
    info=path.stat()
    if info.st_size!=ref["taille_octets"]:
        return b"",{
          "source_id":source,"taille_octets":0,
          "sha256_fichier_copie_publique":"AUCUNE_COPIE_CONFORME",
        }
    fd=os.open(path,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0))
    try:
        opened=os.fstat(fd)
        need(stat.S_ISREG(opened.st_mode)
             and opened.st_dev==info.st_dev
             and opened.st_ino==info.st_ino
             and opened.st_size==info.st_size,
             "SOURCE_MODIFIEE_PENDANT_OUVERTURE")
        with os.fdopen(fd,"rb",closefd=False) as stream:
            raw=stream.read(info.st_size+1)
        need(len(raw)==info.st_size and raw.startswith(b"%PDF-"),
             "PDF_LOCAL_CORROMPU_OU_INSTABLE")
    finally:
        os.close(fd)
    checksum=hashlib.sha256(raw).hexdigest()
    return raw,{
      "source_id":source,
      "taille_octets":len(raw),
      "sha256_fichier_copie_publique":checksum,
    }

def reproduce(paths,expected,extractor=None):
    """Use P54P's full audit and five-position guards on local sources."""
    files=checked_local_paths(paths)
    need(type(expected) is dict and set(expected)==set(NAMES)
         and all(type(expected[k]) is dict
                 and set(expected[k])=={
                   "pdf_index_zero","taille_octets","sha256"}
                 for k in NAMES),
         "REFERENCES_PDF_INCOMPLETES")
    def fetch(key):
        return read_copy(key,files[key],expected)
    return p54p.verify_captures(fetch,extractor or p54p.context.page,expected)

def report(cfg,attempt=None):
    prior=p54p.report(p54p.configuration(),attempt)
    need(prior["economies_certifiees_cad"] is None
         and prior["decision"]==NO_GO,
         "BILAN_PARENT_NON_NEUTRE")
    result={
      "schema_version":"P54Q-BILAN-1",
      "exercice":2024,
      "mode":"COPIES_LOCALES_HORS_GIT_SANS_RESEAU",
      "statut_reproduction":prior["statut_capture"],
      "statuts_copies":prior["sources"],
      "copies_exactes_controlees":prior["copies_exactes_verifiees"],
      "occurrences_localisees":prior["occurrences_localisees_automatiquement"],
      "positions_nfkc":prior["positions_caracteres_sur_texte_extrait"],
      "originaux_et_chemins_publies":0,
      "tokens_et_contextes_publies":0,
      "signature_emetteur_authentifiee":False,
      "avis_professionnels_certifies":0,
      "dossiers_p54e_ouverts":4,
      "date_probable_certifiee":False,
      "controles_p54b_non_attestes":96,
      "controles_p54c_non_attestes":8,
      "economies_certifiees_cad":None,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }
    return result

def save_new(filename,result):
    dest=Path(filename)
    need(not dest.exists() and not dest.is_symlink()
         and dest.parent.is_dir() and not dest.parent.is_symlink(),
         "SORTIE_INVALIDE_OU_EXISTANTE")
    with dest.open("x",encoding="utf-8") as out:
        json.dump(result,out,ensure_ascii=False,sort_keys=True,indent=2)
        out.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ville-pdf")
    parser.add_argument("--mamh-pdf")
    parser.add_argument("--bilan")
    parser.add_argument("--exiger-certification",action="store_true")
    args=parser.parse_args(argv)
    try:
        need(bool(args.ville_pdf)==bool(args.mamh_pdf),
             "DEUX_PDF_NECESSAIRES")
        cfg=configuration()
        attempt=None
        if args.ville_pdf:
            sources={"ville":args.ville_pdf,"mamh":args.mamh_pdf}
            files=checked_local_paths(sources)
            if args.bilan:
                dest=Path(args.bilan).absolute()
                need(dest.resolve() not in files.values(),
                     "FICHIER_SORTIE_EGALE_A_SOURCE")
            attempt=reproduce(files,cfg["copies"])
        result=report(cfg,attempt)
        if args.bilan:save_new(args.bilan,result)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        if args.exiger_certification:return 3
        return 4 if attempt is not None and not attempt["cinq_positions_reproduites"] else 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,
            json.JSONDecodeError) as err:
        print("P54Q_REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
