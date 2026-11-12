#!/usr/bin/env python3
"""P54B : signaux de comparabilité non probants entre pages candidates.

Jamais d'extraction de montants dans les artefacts CI. Les jetons numériques
peuvent être des années, pages, codes, pourcentages ou montants : INDETERMINES.
"""
import argparse
from collections import Counter
from io import BytesIO
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

from pypdf import PdfReader

import analyser_ecarts_publications_nova_p54a as p54a
import verifier_resultats_observes_nova_p54a as observed
import acquerir_publications_nova_p53z as acquisition

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"projets"/"projet-nova"/"etudes"/"P54B_GRILLE_COMPARABILITE_POSTES_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
GATES=(
 "EXERCICE_ET_PERIODE_DES_VALEURS",
 "ORGANISME_ET_PERIMETRE_CONSOLIDE",
 "BASE_COMPTABLE_ET_POLITIQUES",
 "STATUT_AUDITE_VS_NON_AUDITE",
 "UNITES_CAD_MILLIERS_ET_SIGNE",
 "LIBELLE_RUBRIQUE_ET_NOTES",
 "OPERATIONS_RECIPROQUES_DEJA_ELIMINEES",
 "TRAVAIL_SERVICES_TIERS_ET_COUTS_COMPLETS",
)
FLAGS={
 "aucune_valeur_monnaie_exportee",
 "jetons_numeriques_ne_sont_pas_des_montants_certifies",
 "aucune_comparaison_transactionnelle_authentifiee",
 "aucune_conclusion_automatique_audit",
 "sources_octets_revérifiés_avant_mesure",
 "nouvelle_edition_interrompt_comparaison",
 "resultat_p54a_plafonne_a_douze_paires",
 "indices_pdf_zero_based",
 "controle_exercice_par_page_requis",
 "controle_base_et_perimetre_requis",
 "controle_devise_et_multiplicateurs_requis",
 "controle_etats_audites_non_audites_requis",
 "consolidation_quebec_rtc_pas_nouvelles_economies",
 "protections_travailleurs_services",
 "scenario_quebec_canada_separe_independance",
 "avis_expert_humain_independant_requis",
 "aucun_document_original_archive",
 "aucune_fusion_main",
}
METHODS=[
 "https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/presentation/normes-comptables",
 "https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier",
 "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/information_financiere/manuel_information_financiere/manuel_complet.pdf",
]
# A grouped number, or an integer, optionally with 1-2 decimal digits.
# Does not assert that any token is a monetary quantity.
NUMERIC=re.compile(
 r"(?<![\w])\(?-?(?:\d{1,3}(?:[ \u00a0\u202f]\d{3})+|\d{1,15})"
 r"(?:[.,]\d{1,2})?\)?(?![\w])"
)

def require(ok,message):
    if not ok:raise ValueError(message)

def config():
    prior=observed.validate(json.loads(observed.PATH.read_text("utf-8")))
    doc=json.loads(CFG.read_text("utf-8"))
    expected={
      "schema_version":"P54B-1","jalon":"P54B",
      "reference":"2026-10-24","exercice_source":2024,
      "statut":"TEST_COMPARABILITE_POSTES_SANS_AUTHENTIFICATION_DE_MONTANTS",
      "sources_p54a":{
         "run_id":40116065853,
         "source":"P54A_RESULTATS_REANALYSE_2026_10_24.json",
         "copies_sha256":{x:p54a.COPIES[x][2] for x in ("ville","mamh")},
      },
      "controles_comparabilite":list(GATES),
      "sources_methodologie":METHODS,
      "limitations":{k:True for k in FLAGS},
      "etat_initial":{
         "pages_candidates":12,"controles_en_attente":96,
         "copies_publications_observees_p53z_p54a":2,
         "captures_P54B_reussies":None,
         "scores_numeriques_mesures":None,
         "montants_comparables_certifies":0,
         "ecarts_comptables_demontres":0,
         "economie_certifiee_cad":None,
         "decision":NO_GO,
      },
    }
    require(doc==expected and len(prior["candidates"])==12,
            "CHAINAGE_P54A_GRILLE_NON_CONFORME")
    return doc,prior

def tokens(text):
    """Return a multiset of numeric lexical tokens, not accounting entries."""
    require(type(text) is str and len(text)<=2000000,
            "TEXTE_NON_RECEVABLE")
    normalized=unicodedata.normalize("NFKC",text).replace("\u202f"," ")
    result=Counter()
    for match in NUMERIC.finditer(normalized):
        word=match.group(0).strip("()")
        # Thousands-space normalized, no inference of currency, period or sign.
        word=word.replace("\u00a0","").replace(" ","")
        result[word]+=1
    return result

def scores(left,right):
    require(type(left) is Counter and type(right) is Counter,
            "COMPTEURS_ATTENDUS")
    a=sum(left.values());b=sum(right.values())
    common=sum((left&right).values())
    return {
      "jetons_numeriques_extraits_ville":a,
      "jetons_numeriques_extraits_mamh":b,
      "occurrences_lexicales_communes":common,
      "occurrences_sans_contrepartie_ville":a-common,
      "occurrences_sans_contrepartie_mamh":b-common,
      "recouvrement_dice":round(2*common/(a+b),4) if a+b else None,
      "statut":"RECOUVREMENT_LEXICAL_NON_MONETAIRE",
    }

def matrix(doc):
    rows=[]
    for line in doc["candidates"]:
        i=line["page_index_pdf_ville"];j=line["page_index_pdf_mamh"]
        rows.append({
          "index_pdf_ville":i,"index_pdf_mamh":j,
          "similarite_p54a":line["score_jaccard"],
          "nature_paire":"CANDIDAT_HEURISTIQUE_NON_EXHAUSTIF",
          "exercice_source":2024,
          "jetons":None,
          "statut_comparabilite":"NON_ETABLI",
          "controles":[{"code":gate,"statut":"NON_INSTRUIT",
                        "validation_independante":False} for gate in GATES],
          "montants_rubrique_certifies":0,
          "ecarts_monetaires_authentifies":0,
          "economie_certifiee_cad":None,
          "decision":NO_GO,
        })
    require(len(rows)==12 and
            len({(r["index_pdf_ville"],r["index_pdf_mamh"]) for r in rows})==12
            and sum(len(r["controles"]) for r in rows)==96,
            "MATRICE_12_X_8_INCOMPLETE")
    return rows

def page_tokens(blob,indices):
    """Only extract fixed page indices from a PDF already acquired by HTTPS."""
    require(type(blob) is bytes and 0<len(blob)<=acquisition.MAX,
            "OCTETS_PDF_NON_ADMISSIBLES")
    reader=PdfReader(BytesIO(blob),strict=True)
    require(not reader.is_encrypted and len(reader.pages)<=1200,
            "PDF_CHIFFRE_OU_HORS_LIMITE")
    require(type(indices) is set and
            all(type(i) is int and 0<=i<len(reader.pages) for i in indices),
            "INDICES_PDF_HORS_BORNES")
    return {i:tokens(reader.pages[i].extract_text() or "") for i in indices}

def actualize(rows,fetcher=acquisition.capture):
    """Only compute metadata when BOTH downloaded bytes equal the P53Z hashes."""
    facts={};data={}
    for src in ("ville","mamh"):
        try:
            binary,obs=fetcher(src)
            valid=(type(binary) is bytes
                   and hashlib.sha256(binary).hexdigest()==p54a.COPIES[src][2]
                   and len(binary)==p54a.COPIES[src][1]
                   and obs["sha256_fichier_copie_publique"]==p54a.COPIES[src][2]
                   and obs["taille_octets"]==p54a.COPIES[src][1]
                   and obs["source_id"]==src)
            facts[src]={
               "capture_reussie":True,
               "octets_coherents_avec_P53Z":bool(valid),
               "classification":"COPIE_CONFORME_REFERENCE_P53Z"
                  if valid else "EDITION_DIFFERENTE_OU_INTEGRITE_NON_VERIFIEE",
            }
            if valid:data[src]=binary
        except (ValueError,TypeError,KeyError,OSError) as exc:
            facts[src]={"capture_reussie":False,
                        "octets_coherents_avec_P53Z":False,
                        "classification":"ACQUISITION_NON_VERIFIABLE"}
    if len(data)!=2:
        return {"comparaison_possible":False,"sources":facts,
                "lignes":rows,"statut":"CAPTURE_OU_VERSION_NON_COMPARABLE"}
    try:
        l=page_tokens(data["ville"],{r["index_pdf_ville"] for r in rows})
        r=page_tokens(data["mamh"],{r["index_pdf_mamh"] for r in rows})
        for item in rows:
            item["jetons"]=scores(
                l[item["index_pdf_ville"]],r[item["index_pdf_mamh"]])
        return {"comparaison_possible":True,"sources":facts,
                "lignes":rows,"statut":"JETONS_NUMERIQUES_COMPAREES_NON_QUALIFIES"}
    except (ValueError,IndexError,KeyError,TypeError):
        return {"comparaison_possible":False,"sources":facts,
                "lignes":rows,"statut":"EXTRACTION_PDF_NON_CONCLUANTE"}

def summary(assessment):
    rows=assessment["lignes"]
    done=assessment["comparaison_possible"]
    require(type(done) is bool and len(rows)==12,"COMPARAISON_INCOHERENTE")
    return {
      "schema_version":"P54B-BILAN-1",
      "source_exercice":2024,
      "source_p54a_run":40116065853,
      "paires_p54a_cibles":12,
      "controles_comptables_requis":96,
      "deux_copies_conformes_aux_empreintes_P53Z":
         done and all(x["octets_coherents_avec_P53Z"]
                      for x in assessment["sources"].values()),
      "comparaison_lexicale_des_nombres_executee":done,
      "statut":assessment["statut"],
      "observations_sources":assessment["sources"],
      "pages":{
        str(row["index_pdf_ville"])+":"+str(row["index_pdf_mamh"]):row["jetons"]
        for row in rows
      },
      "concordances_comptables_certifiees":0,
      "ecarts_financiers_reels_authentifies":0,
      "economies_certifiees_cad":None,
      "reductions_emplois_services_autorisees":False,
      "fusion_autorisee":False,
      "decision":NO_GO,
    }

def write_new(path,data):
    p=Path(path)
    require(not p.exists() and not p.is_symlink(),"SORTIE_EXISTANTE")
    with p.open("x",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bilan")
    ap.add_argument("--matrice")
    ap.add_argument("--comparer-publications",action="store_true")
    ap.add_argument("--exiger-concordance-comptable",action="store_true")
    a=ap.parse_args(argv)
    try:
        paths=[Path(x) for x in (a.bilan,a.matrice) if x]
        require(len({p.resolve() for p in paths})==len(paths)
                and all(not p.exists() and not p.is_symlink() for p in paths),
                "SORTIES_EXISTANTES_OU_DUPLIQUEES")
        cfg,observed_cfg=config()
        rows=matrix(observed_cfg)
        result=(actualize(rows) if a.comparer_publications else
            {"comparaison_possible":False,"sources":{},"lignes":rows,
             "statut":"NON_TENTE"})
        bilan=summary(result)
        if a.bilan:write_new(a.bilan,bilan)
        if a.matrice:write_new(a.matrice,{
           "schema_version":"P54B-MATRICE-1","statut":result["statut"],
           "lignes":result["lignes"],"decision":NO_GO})
        print(json.dumps(bilan,sort_keys=True,ensure_ascii=False))
        if a.exiger_concordance_comptable:return 3
        if a.comparer_publications and not result["comparaison_possible"]:return 4
        return 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as err:
        print("P54B_REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
