#!/usr/bin/env python3
"""Valider une photographie de comparaison documentaire P54A, sans certification."""
import argparse
import json
from pathlib import Path
import sys

import analyser_ecarts_publications_nova_p54a as p54a

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"projets"/"projet-nova"/"etudes"/"P54A_RESULTATS_REANALYSE_2026_10_24.json"
NO_GO="NO_GO_AUTOMATIQUE"
EXPECTED=[
 (14,173,0.9511,350),(51,30,0.925,469),(62,44,0.9106,591),
 (75,57,0.9219,496),(102,162,0.9156,347),(104,164,0.9128,272),
 (133,136,0.92,345),(139,140,0.9083,297),(145,146,0.9366,325),
 (146,147,0.9256,311),(147,148,0.9172,399),(170,155,0.9167,286),
]
FLAGS={
 "maximum_12_pas_nombre_total_correspondances",
 "indices_pdf_zero_based_pas_pages_imprimees",
 "ressemblance_textuelle_pas_identite_juridique",
 "forme_des_pdfs_peut_differer",
 "pages_sans_texte_non_comparees",
 "organes_emetteurs_non_authentifies_par_hash",
 "consolidation_rtc_deja_effectuee",
 "emplois_et_services_garantis",
 "pas_de_fusion_automatique",
}

def need(ok,message):
    if not ok:raise ValueError(message)

def validate(doc):
    baseline=p54a.original_snapshot()
    need(type(doc) is dict
         and set(doc)=={
           "schema_version","exercice","capture_source_p53z_run_id",
           "rapport_validation_run_id","rapport_validation_artifact_id",
           "rapport_validation_artifact_sha256","provenance",
           "date_reanalyse_utc","copies","methode","minimum_score",
           "plafonnement_candidates","candidates_affichees","candidates",
           "resultats","limites"},
         "RAPPORT_OBSERVE_STRUCTURE_INVALIDE")
    need(doc["schema_version"]=="P54A-OBSERVATIONS-CI-1"
         and doc["exercice"]==2024
         and doc["capture_source_p53z_run_id"]==p54a.RUN
         and doc["rapport_validation_run_id"]==40116065853
         and doc["rapport_validation_artifact_id"]==12568158622
         and doc["rapport_validation_artifact_sha256"]==
            "c973b8558bc05ec4f4d572da66a700548b7ba835e88cd4208c2c96f6fbea86dc"
         and doc["provenance"]=="CONTROLE_TECHNIQUE_DES_COPIES_HTTPS_NON_SIGNATURE_EMETTEUR"
         and doc["date_reanalyse_utc"]=="2026-10-24"
         and doc["methode"]=="NGRAMMES_4_MOTS_SCORE_JACCARD_ET_MATCHING_1_A_1"
         and doc["minimum_score"]==0.35
         and doc["plafonnement_candidates"]==12
         and doc["candidates_affichees"]==12,
         "ORIGINE_RAPPORT_NON_VERIFIABLE")
    need(set(doc["copies"])=={"ville","mamh"},"COPIES_MANQUANTES")
    expected_time={"ville":"2026-10-24T17:26:58+00:00",
                   "mamh":"2026-10-24T17:26:59+00:00"}
    for source,ref in baseline["sources"].items():
        observed=doc["copies"][source]
        need(observed=={
            "capture_utc":expected_time[source],
            "taille":ref["octets"],"sha256":ref["sha256"],
            "sha_identique_capture_p53z":True,
        },"EMPREINTE_OU_TAILLE_MODIFIEE")
    rows=doc["candidates"]
    need(type(rows) is list and len(rows)==12,"CANDIDATS_NON_COMPLETS")
    for row,ref in zip(rows,EXPECTED):
        need(type(row) is dict and set(row)=={
            "page_index_pdf_ville","page_index_pdf_mamh",
            "score_jaccard","ngrams_communs","conclusion"}
            and type(row["page_index_pdf_ville"]) is int
            and type(row["page_index_pdf_mamh"]) is int
            and type(row["score_jaccard"]) is float
            and type(row["ngrams_communs"]) is int
            and row["conclusion"]=="CANDIDAT_DOCUMENTAIRE_NON_CERTIFIE"
            and tuple(row[k] for k in (
              "page_index_pdf_ville","page_index_pdf_mamh",
              "score_jaccard","ngrams_communs"))==ref,
            "CORRESPONDANCES_MODIFIEES")
    need(doc["resultats"]=={
       "recapacquisition_reussie":True,"captures_actualisees":2,
       "nombres_pages_verifies_p53z":{"ville":230,"mamh":177},
       "pages_exactement_identiques_selon_p53x":0,
       "pages_similaires_identifiees_en_tete_de_classement":12,
       "rapprochements_comptables_authentifies":0,
       "avis_independants_signes":0,
       "economies_certifiees_cad":None,"decision":NO_GO},
       "CONCLUSION_P53Z_P54A_CONTREDITE")
    need(doc["limites"]=={k:True for k in FLAGS},
         "RESERVES_EXPLICITES_MANQUANTES")
    return doc

def summary(doc):
    doc=validate(doc)
    return {
      "schema_version":"P54A-CONTROLE-OBSERVATIONS-1",
      "jalon":"P54A","run_p53z":p54a.RUN,
      "run_p54a":doc["rapport_validation_run_id"],
      "captures_reréussies":2,"empreintes_stables_sur_deux_runs":True,
      "candidats_affiches":len(doc["candidates"]),
      "nombre_total_de_pages_equivalentes_certifiees":0,
      "expertises_independantes_certifiees":0,
      "economies_certifiees_cad":None,
      "decision":NO_GO,
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bilan")
    ap.add_argument("--exiger-comparabilite-comptable",action="store_true")
    a=ap.parse_args(argv)
    try:
        data=json.loads(PATH.read_text("utf-8"))
        report=summary(data)
        if a.bilan:
            p=Path(a.bilan)
            need(not p.exists() and not p.is_symlink(),"SORTIE_EXISTANTE")
            with p.open("x",encoding="utf-8") as f:
                json.dump(report,f,sort_keys=True,ensure_ascii=False,indent=2)
                f.write("\n")
        print(json.dumps(report,sort_keys=True,ensure_ascii=False))
        return 3 if a.exiger_comparabilite_comptable else 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,
            json.JSONDecodeError) as e:
        print("P54A_CONTROLE_REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
