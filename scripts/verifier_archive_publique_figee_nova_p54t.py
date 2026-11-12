#!/usr/bin/env python3
"""P54T : conserver les octets JSON publics P54P dans le dépôt, à SHA exact.

Les artefacts Actions expirent; les deux bilans publics P54P sont suffisamment
petits et sans jetons ni contextes pour en conserver les octets identiques dans
Git. Leur présence ne prouve ni une nouvelle capture PDF ni une expertise.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import verifier_provenance_artifact_nova_p54r as p54r

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54T_ARCHIVAGE_DURABLE_PREUVE_2024.json"
FROZEN=ROOT/"projets/projet-nova/etudes/p54t_archive_durable_p54p"
NAMES=(
 "p54p_avant_acquisition.json",
 "p54p_reproduction_conditionnelle.json",
)
NO_GO="NO_GO_AUTOMATIQUE"
GUARDS={
 "fichiers_membres_figes_a_sha256_identique",
 "pas_de_zip_original_reconstitue",
 "pas_de_relecture_pdf_ce_jalon",
 "octets_identiques_aux_artefacts_historique",
 "origine_institutionnelle_non_authentifiee",
 "aucune_anomalie_comptable_inferree",
 "aucun_jeton_brut_ou_contexte",
 "cinq_offsets_nfkc_non_visuels",
 "date_probable_non_certifiee",
 "quatre_dossiers_p54e_ouverts",
 "controles_p54b_p54c_non_attestes",
 "aucune_economie_certifiee",
 "emplois_services_proteges",
 "double_compte_ville_rtc_somhac_interdit",
 "deux_scenarios_constitutionnels_distincts",
 "aucune_transmission_externe",
 "main_non_fusionnee",
 "sinjira_inchange",
}

def need(condition,reason):
    if not condition:raise ValueError(reason)

def configuration():
    prior=p54r.configuration()
    expected={
      "schema_version":"P54T-1","date_reference":"2026-10-24",
      "source_jalon":"P54R","reference_run_p54p":prior["source_run_id"],
      "reference_artifact_p54p":prior["artifact_id"],
      "source_zip_sha256_historique":prior["artifact_sha256"],
      "copies_figees":{name:{
          "chemin":str((FROZEN/name).relative_to(ROOT)),
          "sha256":prior["pieces_archive"][name]["sha256"],
          "taille_octets":prior["pieces_archive"][name]["taille_octets"],
      } for name in NAMES},
      "position_ref_count":5,
      "protections":{name:True for name in GUARDS},
      "etat_initial":{
          "copies_figees_recontrolees":0,"positions_historiques":5,
          "positions_pdf_reextraites_ce_jalon":0,"pdf_reacquis_ce_jalon":0,
          "archive_zip_reverifiee_ce_jalon":False,
          "dossiers_p54e_ouverts":4,
          "controles_p54b_non_attestes":96,
          "controles_p54c_non_attestes":8,
          "economies_certifiees_cad":None,
          "decision":NO_GO,
      },
    }
    need(json.loads(CONFIG.read_text("utf-8"))==expected
         and set(prior["pieces_archive"])==set(NAMES)
         and prior["positions_historiques"]==p54r.known_rows(),
         "ANCRAGE_P54T_P54R_MODIFIE")
    return expected

def verify_frozen(cfg,files=None):
    """Verify member bytes independently of any ZIP/download/new PDF."""
    sources=files or {name:FROZEN/name for name in NAMES}
    need(type(sources) is dict and set(sources)==set(NAMES),
         "DEUX_BILANS_ORIGINAUX_OBLIGATOIRES")
    parsed={}
    for name in NAMES:
        file=Path(sources[name])
        rec=cfg["copies_figees"][name]
        need(file.is_file() and not file.is_symlink()
             and file.stat().st_size==rec["taille_octets"],
             "FICHIER_FIGE_ABSENT_OU_TAILLE_DIFFERENTE")
        data=file.read_bytes()
        need(len(data)==rec["taille_octets"]
             and hashlib.sha256(data).hexdigest()==rec["sha256"],
             "FICHIER_FIGE_SHA256_NON_CONFORME")
        parsed[name]=json.loads(data.decode("utf-8"))
    old=parsed[NAMES[0]]
    final=parsed[NAMES[1]]
    expected_old=p54r.p54p.report(p54r.p54p.configuration())
    need(old==expected_old,"BILAN_INITIAL_FALSIFIE")
    attempt={
       "statut":final["statut_capture"],
       "sources":final["sources"],
       "copies_verifiees_par_hachage":final["copies_exactes_verifiees"],
       "cinq_positions_reproduites":final[
          "occurrences_localisees_automatiquement"]==5,
       "positions":final["positions_caracteres_sur_texte_extrait"],
    }
    need(final==p54r.p54p.report(p54r.p54p.configuration(),attempt)
         and final["positions_caracteres_sur_texte_extrait"]==
             p54r.known_rows()
         and final["copies_exactes_verifiees"]==2,
         "BILAN_FINAL_OU_OFFSETS_NON_CONFORMES")
    return {
      "bilans_figes_verifies":2,
      "tailles_octets_verifiees":sum(cfg["copies_figees"][n]["taille_octets"]
                                   for n in NAMES),
      "positions_historiques_hachees":5,
      "positions_de_reference":p54r.known_rows(),
    }

def report(cfg,verified=None):
    v=verified or {}
    return {
      "schema_version":"P54T-BILAN-1",
      "source_artifact_id":cfg["reference_artifact_p54p"],
      "source_zip_sha256_historique":cfg["source_zip_sha256_historique"],
      "bilans_publics_fixes_reverifies_ce_run":v.get("bilans_figes_verifies",0),
      "octets_bilans_reverifies_ce_run":v.get("tailles_octets_verifiees",0),
      "positions_historiques_de_reference":5,
      "positions_des_bilans_figes_reverifiees_ce_run":
        v.get("positions_historiques_hachees",0),
      "positions_nfkc_texte_source":v.get("positions_de_reference"),
      "zip_archive_originale_relue_ce_run":False,
      "pdf_originaux_relus_ce_run":0,
      "pdf_emetteurs_authentifies":0,
      "contre_expertises_independantes":0,
      "dossiers_p54e_ouverts":4,
      "date_probable_non_certifiee":True,
      "controles_p54b_non_attestes":96,
      "controles_p54c_non_attestes":8,
      "economies_certifiees_cad":None,
      "main_fusion_autorisee":False,
      "decision":NO_GO,
    }

def write_new(path,data):
    p=Path(path)
    need(not p.exists() and not p.is_symlink()
         and p.parent.is_dir() and not p.parent.is_symlink(),
         "DESTINATION_INTERDITE_OU_EXISTANTE")
    with p.open("x",encoding="utf-8") as stream:
        json.dump(data,stream,sort_keys=True,ensure_ascii=False,indent=2)
        stream.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verifier-fichiers-figes",action="store_true")
    parser.add_argument("--bilan")
    parser.add_argument("--exiger-certification",action="store_true")
    a=parser.parse_args(argv)
    try:
        cfg=configuration()
        v=verify_frozen(cfg) if a.verifier_fichiers_figes else None
        out=report(cfg,v)
        if a.bilan:write_new(a.bilan,out)
        print(json.dumps(out,ensure_ascii=False,sort_keys=True))
        return 3 if a.exiger_certification else 0
    except (KeyError,TypeError,ValueError,OSError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P54T_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
