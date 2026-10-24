#!/usr/bin/env python3
"""P54A: examiner les écarts entre deux publications publiques sans audit financier."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
import re
import sys

from pypdf import PdfReader
import acquerir_publications_nova_p53z as p53z
import comparer_versions_pdf_nova_p53x as p53x

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"projets"/"projet-nova"/"etudes"/"P54A_CAPTURES_REELLES_P53Z_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
RUN=40113700739
ARCHIVE="972cedafe5dd51c0f78f3b0c581fafd4cb0b652583c08627ca7178c755db4fba"
COPIES={
  "ville":("2026-10-24T16:58:03+00:00",8984919,
           "b3ee3e671f7bf98e56c7d42b5e8b6c34de02a96c9dc1c96469819fa4dbfa7399",
           230,27),
  "mamh":("2026-10-24T16:58:05+00:00",10818312,
           "4323c87d2114b58cf7a093c08f3b30327e949db91b9beb46a627eac1ecb4fc00",
           177,3),
}
ISSUES=(
 "EDITION_ET_COMPOSITION_DES_PUBLICATIONS",
 "DISTINCTION_SECTION_AUDITEE_NON_AUDITEE",
 "ETATS_FINANCIERS_ET_PERIMETRES_COMPARABLES",
 "RAPPROCHEMENT_CONTREPARTIES_QUEBEC_RTC",
 "ELIMINATIONS_ANTERIEURES_ET_COUTS_COMPLETS",
 "GARANTIES_EMPLOIS_ET_SERVICES",
 "AVIS_JURIDIQUE_ET_COMPTABLE_INDEPENDANTS",
)
GUARDS={
 "publication_mamh_potentiellement_assemblee",
 "difference_octets_pas_erreur_comptable",
 "zero_pages_identiques_texte_pas_zero_pages_similaires",
 "pages_non_extractibles_indeterminees",
 "empreintes_copies_pas_signatures_officielles",
 "original_pdf_non_archive_dans_git",
 "aucun_montant_derivé_de_recettes",
 "double_compte_quebec_rtc_interdit",
 "maintien_emplois_services",
 "regimes_constitutionnels_separes",
 "avis_independants_requis",
 "aucune_fusion_automatique",
}

def need(ok,message):
    if not ok: raise ValueError(message)

def original_snapshot():
    p53z.config()
    cfg=json.loads(SOURCE.read_text("utf-8"))
    need(type(cfg) is dict
         and cfg["schema_version"]=="P54A-SNAPSHOT-P53Z-1"
         and cfg["jalon"]=="P54A"
         and cfg["date_analyse"]=="2026-10-24"
         and cfg["run_id"]==RUN
         and cfg["job_id"]==120930498332
         and cfg["artifact_id"]==12567252796
         and cfg["archive_sha256"]==ARCHIVE
         and cfg["exercice"]==2024
         and cfg["provenance_outil"]=="GITHUB_ACTIONS_RESULTAT_P53Z_NON_SIGNATURE_INSTITUTIONNELLE"
         and set(cfg["sources"])==set(COPIES),
         "SOURCE_P53Z_NON_RECEVABLE")
    for key,fields in COPIES.items():
        item=cfg["sources"][key]
        need(item=={
          "url":p53z.SOURCE[key],
          "capture_utc":fields[0],
          "octets":fields[1],
          "sha256":fields[2],
          "pages":fields[3],
          "pages_sans_texte_extractible":fields[4]},
          "EMPREINTE_P53Z_ALTEREE")
    need(cfg["comparaison_p53z"]=={
      "captures_reussies":2,
      "comparateur_p53x_execute":True,
      "fichiers_strictement_identiques":False,
      "meme_nombre_pages":False,
      "pages_textes_normalises_identiques_appariees":0,
      "pages_ville_textes_non_apparies":203,
      "ancrages_p53w_textuellement_identiques":{
        "0":False,"34":False,"196":False},
      "avis_professionnels_signes":0,
      "economies_certifiees_cad":None,
      "decision":NO_GO,
    } and cfg["sujets_a_expertiser"]==list(ISSUES)
      and cfg["verrous"]=={g:True for g in GUARDS},
      "CONCLUSIONS_NON_CORROBOREES")
    return cfg

def fingerprints(blob):
    """Signatures de mots sur chaque page, sans enregistrer le texte."""
    reader=PdfReader(BytesIO(blob),strict=True)
    need(not reader.is_encrypted and 1<=len(reader.pages)<=p53x.PAGES_MAX,
         "PDF_CHIFFRE_OU_HORS_LIMITE")
    rows=[]
    for page in reader.pages:
        words=re.findall(r"\w+",p53x.normalized(page.extract_text() or ""))
        # A page with little extractable text is indeterminate, not erroneous.
        if len(words)<60:
            rows.append(set())
            continue
        words=words[:6500]
        shingles={" ".join(words[i:i+4]) for i in range(len(words)-3)}
        rows.append(shingles if len(shingles)>=30 else set())
    return rows

def probable_pages(left,right,threshold=0.35,max_results=12):
    """Candidates only: Jaccard de séquences de quatre mots, not a legal review."""
    need(type(left) is list and type(right) is list
         and type(threshold) is float and 0.2<=threshold<=0.95
         and type(max_results) is int and 1<=max_results<=30,
         "PARAMETRES_NON_ADMIS")
    # Ignore ubiquitous page headers: too many repeated instances mislead.
    reverse=defaultdict(list)
    for j,page in enumerate(right):
        for shingle in page:
            reverse[shingle].append(j)
    candidates=[]
    for i,page in enumerate(left):
        if not page:continue
        overlap=Counter()
        for token in page:
            ids=reverse.get(token,())
            if len(ids)<=8:
                overlap.update(ids)
        best=None
        for j,shared in overlap.items():
            if shared<20:continue
            denom=len(page)+len(right[j])-shared
            if denom<=0:continue
            score=shared/denom
            if score>=threshold and (
                best is None or (score,shared,-j)>(best[0],best[1],-best[2])):
                best=(score,shared,j)
        if best is not None:
            candidates.append((best[0],best[1],i,best[2]))
    # Unique page on both sides, strongest candidate first.
    pairs=[];used_right=set()
    for score,shared,i,j in sorted(candidates,reverse=True):
        if j in used_right:continue
        used_right.add(j)
        pairs.append({"page_pdf_ville":i,"page_pdf_mamh":j,
                      "score_jaccard":round(score,4),
                      "ngrams_communs":shared,
                      "statut":"CORRESPONDANCE_HEURISTIQUE_NON_CERTIFIEE"})
        if len(pairs)>=max_results:break
    return sorted(pairs,key=lambda r:r["page_pdf_ville"])

def run_analysis(fetcher=p53z.capture):
    observations={};binaries={}
    for src in ("ville","mamh"):
        try:
            content,meta=fetcher(src)
            binaries[src]=content
            observations[src]={
              "capture_effective":True,
              "horodatage_utc":meta["date_capture_utc"],
              "sha256":meta["sha256_fichier_copie_publique"],
              "taille_octets":meta["taille_octets"],
              "concordance_empreinte_P53Z":
                meta["sha256_fichier_copie_publique"]==COPIES[src][2],
              "etiquette":"COPIE_PUBLIQUE_OBSERVEE_NON_CERTIFIEE"}
        except (ValueError,KeyError,TypeError,OSError) as exc:
            observations[src]={"capture_effective":False,
               "statut":"ACQUISITION_IMPOSSIBLE_SANS_FAUSSE_PREUVE"}
    pairs=[]
    parse_ok=False
    if len(binaries)==2:
        try:
            l=fingerprints(binaries["ville"])
            r=fingerprints(binaries["mamh"])
            pairs=probable_pages(l,r)
            parse_ok=True
        except (ValueError,TypeError,IndexError,KeyError):
            parse_ok=False
    return observations,pairs,parse_ok

def report(cfg,observations,pairs,parse_ok):
    status=(
        "REANALYSE_2_PDF_PUBLIQUES_EFFECTUEE"
        if parse_ok else
        "REANALYSE_INCOMPLETE_SOURCES_OU_PAGES_INDISPONIBLES")
    return {
      "schema_version":"P54A-BILAN-1",
      "date_reference_p53z":"2026-10-24",
      "run_original_p53z":RUN,
      "etat_reanalyse":status,
      "capture_p53z_sources":2,
      "pages_capture_p53z":{"ville":230,"mamh":177},
      "octets_capture_p53z_identiques":False,
      "pages_texte_strictement_identique_p53z":0,
      "pages_sans_texte_extractible_p53z":{"ville":27,"mamh":3},
      "references_sha256_capture_p53z":{
         src:COPIES[src][2] for src in COPIES},
      "captures_actualisees":sum(x["capture_effective"] for x in observations.values()),
      "observations":observations,
      "reanalyse_textuelle_reussie":parse_ok,
      "pages_approximativement_appariees_heuristique":
         len(pairs) if parse_ok else None,
      "appariements_candidates_pour_examen_humain":pairs,
      "sujets_a_expertiser":cfg["sujets_a_expertiser"],
      "anomalies_comptables_certifiees":0,
      "conclusions_sur_version_officielle_authentifiees":0,
      "avis_comptables_juridiques_signes":0,
      "economies_certifiees_cad":None,
      "diminution_emplois_services_autorisee":False,
      "fusion_autorisee":False,
      "decision":NO_GO,
    }

def write_new(path,obj):
    target=Path(path)
    need(not target.exists() and not target.is_symlink(),"ECRASEMENT_INTERDIT")
    with target.open("x",encoding="utf-8") as f:
        json.dump(obj,f,indent=2,sort_keys=True,ensure_ascii=False)
        f.write("\n")

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bilan")
    ap.add_argument("--reanalyser-publications",action="store_true")
    ap.add_argument("--exiger-anomalie-certifiee",action="store_true")
    args=ap.parse_args(argv)
    try:
        cfg=original_snapshot()
        data=run_analysis() if args.reanalyser_publications else ({},[],False)
        summary=report(cfg,*data)
        if args.bilan:write_new(args.bilan,summary)
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        if args.exiger_anomalie_certifiee:return 3
        if args.reanalyser_publications and not summary["reanalyse_textuelle_reussie"]:
            return 4
        return 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P54A_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
