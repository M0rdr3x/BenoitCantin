#!/usr/bin/env python3
"""P54R — ancrage reproductible de l'artefact P54P observé sur GitHub.

Archive publique, sans PDF/jetons. SHA-256 de l'archive ne certifie pas
l'identité de l'émetteur ni la matérialité des observations financières.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import reproduire_localisations_pdf_nova_p54p as p54p

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"projets/projet-nova/etudes/P54R_PREUVES_TECHNIQUES_OBSERVEES_P54P_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
RUN_ID=40151185184
JOB_ID=121042887853
ARTIFACT_ID=12583661231
ARCHIVE_SHA="d87562662c4c82176e02bdcb28035bb704f2734eb998e0161ef17a21e268c42e"
PIECES={
 "p54p_avant_acquisition.json":("73856ddd9284acec7a0a5edcf538ff5f7c387ab28429e736cfeb85a1c92914dd",795),
 "p54p_reproduction_conditionnelle.json":("ebfae307f375519b5921358af70b624991f9a3f6a383eb91139d64c399620fb1",2631),
}
OBS=[
 ("ville",0,"P54E-V-001","INDETERMINE","FIN",102,2359,2364),
 ("mamh",1,"P54E-M-001","INDETERMINE","DEBUT",162,18,2439),
 ("mamh",2,None,"ANNEE_DATE_PROBABLE","FIN",162,2420,2439),
 ("mamh",3,"P54E-M-002","INDETERMINE","FIN",162,2430,2439),
 ("mamh",4,"P54E-M-003","INDETERMINE","FIN",162,2436,2439),
]
GUARDS={
 "aucune_attestation_professionnelle","aucun_montant_infere",
 "fichiers_zips_sans_extraction","archive_epinglee_sha256",
 "fichiers_internes_epingles_sha256","aucun_texte_source_publie",
 "aucun_pdf_original_publie","pas_de_zip_traversal","pas_de_zip_bomb",
 "aucune_sortie_certifiante","offsets_nfkc_non_visuels",
 "aucun_echec_acquisition_transforme_en_succes",
 "preuve_technique_ne_authentifie_pas_emetteur",
 "historique_ci_distinct_de_reverification",
 "quatre_dossiers_p54e_ouverts","une_date_probable_non_certifiee",
 "pas_de_double_compte_ville_rtc_somhac","emplois_services_proteges",
 "deux_scenarios_constitutionnels_separes","main_non_fusionnee",
 "sinjira_inchange",
}

def need(ok,code):
    if not ok: raise ValueError(code)

def known_rows():
    return [{
       "source":source,"index_observation_p54d":index,
       "dossier":case,"classification_indicative":classif,
       "zone_confirmee_par_parseur":zone,
       "pdf_index_zero":page,"offset_texte_extrait":offset,
       "longueur_texte_normalise_nfkc":length,
       "aucune_conclusion_financiere":True,
    } for source,index,case,classif,zone,page,offset,length in OBS]

def configuration():
    parent=p54p.configuration()
    expected={
      "schema_version":"P54R-1","date_reference":"2026-10-24",
      "source_jalon":"P54P","source_run_id":RUN_ID,
      "source_job_id":JOB_ID,"artifact_id":ARTIFACT_ID,
      "artifact_sha256":ARCHIVE_SHA,"archive_size_octets":1533,
      "pieces_archive":{k:{"sha256":v[0],"taille_octets":v[1]} for k,v in PIECES.items()},
      "sha256_sources_p54d":{k:v["sha256"] for k,v in parent["sources"].items()},
      "positions_historiques":known_rows(),
      "protections":{k:True for k in GUARDS},
      "decision":NO_GO,
    }
    data=json.loads(CFG.read_text("utf-8"))
    need(data==expected and parent["source_run_p54d"]==40120462237
         and parent["etats"][-1]=="REPRODUCTION_TECHNIQUE_SANS_ATTESTATION",
         "REGISTRE_PROVENANCE_OU_SOURCES_MODIFIES")
    return data

def examine_archive(path,cfg):
    """Validate ZIP bytes and contained JSON only; never extract to disk."""
    f=Path(path)
    need(f.is_file() and not f.is_symlink()
         and f.stat().st_size==cfg["archive_size_octets"],
         "ARCHIVE_ABSENTE_OU_TAILLE_INATTENDUE")
    content=f.read_bytes()
    need(hashlib.sha256(content).hexdigest()==cfg["artifact_sha256"],
         "ARCHIVE_SHA256_NON_CONFORME")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names=archive.namelist()
            need(len(names)==2 and set(names)==set(PIECES)
                 and all(z.filename in PIECES and not z.is_dir()
                         and z.file_size==PIECES[z.filename][1]
                         and z.compress_size<=cfg["archive_size_octets"]
                         and not z.flag_bits & 1
                         for z in archive.infolist()),
                 "ARCHIVE_STRUCTURE_OU_MEMBRES_INATTENDUS")
            documents={}
            for name in PIECES:
                blob=archive.read(name)
                digest,size=PIECES[name]
                need(len(blob)==size and hashlib.sha256(blob).hexdigest()==digest,
                     "MEMBRE_SHA256_NON_CONFORME")
                documents[name]=json.loads(blob.decode("utf-8"))
    except (zipfile.BadZipFile,EOFError,RuntimeError,UnicodeError) as exc:
        raise ValueError("ARCHIVE_INVALIDE") from exc
    initial=documents["p54p_avant_acquisition.json"]
    final=documents["p54p_reproduction_conditionnelle.json"]
    need(p54p.validated_public_attempt({
            "statut":initial["statut_capture"],"sources":initial["sources"],
            "copies_verifiees_par_hachage":initial["copies_exactes_verifiees"],
            "cinq_positions_reproduites":False,"positions":None,
         })["statut"]=="NON_TENTE",
         "BILAN_INITIAL_NON_NEUTRE")
    need(initial==p54p.report(p54p.configuration()),"BILAN_INITIAL_INATTENDU")
    attempt={
      "statut":final["statut_capture"],"sources":final["sources"],
      "copies_verifiees_par_hachage":final["copies_exactes_verifiees"],
      "cinq_positions_reproduites":final["occurrences_localisees_automatiquement"]==5,
      "positions":final["positions_caracteres_sur_texte_extrait"],
    }
    need(p54p.report(p54p.configuration(),attempt)==final,
         "BILAN_FINAL_CHAMPS_OU_VALEURS_INATTENDUS")
    need(attempt["cinq_positions_reproduites"] is True
         and attempt["positions"]==cfg["positions_historiques"]
         and attempt["copies_verifiees_par_hachage"]==2,
         "OBSERVATIONS_DIFFERENTES_DU_JOURNAL_CI")
    return True

def report(cfg,archive_verified=False):
    return {
      "schema_version":"P54R-BILAN-1",
      "source_run_p54p":RUN_ID,
      "artifact_id":ARTIFACT_ID,
      "empreinte_archive_referencee":cfg["artifact_sha256"],
      "archive_verifiee_par_octets_dans_cette_execution":archive_verified,
      "statut":"ARCHIVE_EXACTE_CONTROLEE_SANS_ATTESTATION" if archive_verified
              else "POSITIONS_HISTORIQUES_A_CONFIRMATION_D_ARCHIVE",
      "cinq_positions_de_reference":cfg["positions_historiques"],
      "positions_reverifiees_dans_cette_execution":5 if archive_verified else 0,
      "copies_pdf_referencees_dans_ci_p54p":2,
      "sources_pdf_physiquement_relues_dans_cette_execution":0,
      "qualification_professionnelle":False,
      "statut_date_probable_certifie":False,
      "dossiers_p54e_ouverts":4,
      "controles_p54b_non_attestes":96,
      "controles_p54c_non_attestes":8,
      "economies_certifiees_cad":None,
      "decision":NO_GO,
    }

def save(path,value):
    dest=Path(path)
    need(not dest.exists() and not dest.is_symlink()
         and dest.parent.is_dir() and not dest.parent.is_symlink(),
         "SORTIE_EXISTANTE_OU_NON_AUTORISEE")
    with dest.open("x",encoding="utf-8") as handle:
        json.dump(value,handle,ensure_ascii=False,sort_keys=True,indent=2)
        handle.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive")
    parser.add_argument("--bilan")
    parser.add_argument("--exiger-certification",action="store_true")
    options=parser.parse_args(argv)
    try:
        need(not options.archive or
             not options.bilan or Path(options.archive).resolve()!=Path(options.bilan).resolve(),
             "ENTREE_ET_SORTIE_IDENTIQUES")
        cfg=configuration()
        verified=examine_archive(options.archive,cfg) if options.archive else False
        result=report(cfg,verified)
        if options.bilan:save(options.bilan,result)
        print(json.dumps(result,sort_keys=True,ensure_ascii=False))
        return 3 if options.exiger_certification else 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P54R_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
