#!/usr/bin/env python3
"""P54D: contrôler la transcription du résultat d'acquisition, non sa certification."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import classer_ecarts_numeriques_nova_p54d as p54d

SOURCE=p54d.ROOT/"projets/projet-nova/etudes/P54D_OBSERVATIONS_REELLES_2026_10_24.json"
NO_GO="NO_GO_AUTOMATIQUE"
PROVENANCE={
 "run_id":40120462237,
 "job_id":120950677964,
 "artifact_id":12570359704,
 "artifact_sha256":"0ca689bb9769954b44b0db0014266ec3daf774032d13913685bfb89af061bbd5",
}
SAFETY={
 "classification_date_est_probable_pas_certaine",
 "aucun_token_numerique_brut_publie",
 "aucun_contexte_nominatif_publie",
 "absence_de_preuve_ne_signifie_pas_identite",
 "aucune_economie_calculee",
 "protection_emploi_services",
 "operation_reciproque_deja_eliminee_non_gain",
 "pas_de_fusion_main",
}
def need(ok,msg):
    if not ok:raise ValueError(msg)

def validate(d):
    p54d.config()
    need(type(d) is dict and set(d)=={
      "schema_version","exercice","run_id","job_id","artifact_id",
      "artifact_sha256","date_observation","provenance","source_documents",
      "pages","source_version_originale_compatible","occurrences",
      "classifications","observations","etat","limites",
    },"CHAMPS_OBSERVATION_INCORRECTS")
    need(d["schema_version"]=="P54D-OBSERVATIONS-CI-1"
         and type(d["exercice"]) is int and d["exercice"]==2024
         and all(type(d[k]) is int and d[k]==val for k,val in PROVENANCE.items()
                 if k!="artifact_sha256")
         and d["artifact_sha256"]==PROVENANCE["artifact_sha256"]
         and d["date_observation"]=="2026-10-24"
         and d["provenance"]==
           "CAPTURE_HTTPS_PDF_ET_COMPARAISON_P54B_NON_ATTESTATION_EMETTEUR"
         and d["source_documents"]=={
           k:p54d.p54b.p54a.COPIES[k][2] for k in ("ville","mamh")}
         and d["pages"]==p54d.PAGES
         and d["source_version_originale_compatible"] is True,
         "PROVENANCE_OU_EDITION_INCOHERENTE")
    need(d["occurrences"]=={"ville":1,"mamh":4,"total":5}
         and d["classifications"]=={
           "ANNEE_DATE_PROBABLE":1,"INDETERMINE":4}
         and type(d["observations"]) is list
         and len(d["observations"])==5,
         "COMPTAGE_OBSERVATIONS_ALTERE")
    expected=[
      ("ville","INDETERMINE","FIN"),
      ("mamh","INDETERMINE","DEBUT"),
      ("mamh","ANNEE_DATE_PROBABLE","FIN"),
      ("mamh","INDETERMINE","FIN"),
      ("mamh","INDETERMINE","FIN"),
    ]
    for row,ref in zip(d["observations"],expected):
        need(type(row) is dict and set(row)=={
          "source","categorie_indicative",
          "zone_approximative","qualification"}
          and (row["source"],row["categorie_indicative"],
               row["zone_approximative"])==ref
          and row["qualification"]=="NON_CERTIFIEE",
          "CLASSEMENT_BRUT_OU_FALSIFIE")
    need(d["etat"]=={
        "categories_documentaires_definitivement_etablies":0,
        "quatre_occurrences_indeterminees":4,
        "causes_de_differences_demontrees":0,
        "ecarts_monetaires_comptables_certifies":0,
        "avis_independants_signes":0,
        "economies_certifiees_cad":None,
        "controles_comptables_p54b_en_attente":96,
        "controles_contexte_p54c_en_attente":8,
        "decision":NO_GO}
        and d["limites"]=={k:True for k in SAFETY},
        "FAUSSE_CONCLUSION_FINANCIERE")
    return d

def result(data):
    d=validate(data)
    return {
      "schema_version":"P54D-CONTROLE-OBSERVATIONS-1",
      "run_id":d["run_id"],
      "copies_officielles_observees":2,
      "occurrences_non_appariees":5,
      "date_ou_annee_probable":1,
      "occurrences_indeterminees":4,
      "causes_de_differences_comptables_demontrees":0,
      "expertises_independantes":0,
      "economies_certifiees_cad":None,
      "decision":NO_GO,
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bilan")
    ap.add_argument("--exiger-preuve-comptable",action="store_true")
    a=ap.parse_args(argv)
    try:
        data=json.loads(SOURCE.read_text("utf-8"))
        report=result(data)
        if a.bilan:
            p=Path(a.bilan)
            need(not p.exists() and not p.is_symlink(),"REFUS_ECRASEMENT")
            with p.open("x",encoding="utf-8") as f:
                json.dump(report,f,indent=2,sort_keys=True,ensure_ascii=False)
                f.write("\n")
        print(json.dumps(report,sort_keys=True,ensure_ascii=False))
        return 3 if a.exiger_preuve_comptable else 0
    except (OSError,ValueError,KeyError,TypeError,
            UnicodeError,json.JSONDecodeError) as ex:
        print("P54D_VERIFICATION_REFUS: "+str(ex),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
