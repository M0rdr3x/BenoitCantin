#!/usr/bin/env python3
"""P54D — classifier contextuellement cinq jetons numériques NON comptables.

Une catégorie automatique est un indice de revue; jamais une attestation.
Les tokens et leur contexte ne peuvent être conservés que dans un fichier
privé hors dépôt, à la demande explicite de l'opérateur.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import unicodedata

import acquerir_publications_nova_p53z as capture
import analyser_contexte_audit_depenses_nova_p54c as p54c
import comparer_postes_financiers_nova_p54b as p54b
import verifier_observations_audit_nova_p54c as verify_c

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54D_TYPOLOGIE_JETONS_NON_APPARIES_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
PAGES={"ville":102,"mamh":162}
REFERENCE={"ville":10,"mamh":13,"communes":9,
 "non_appariees_ville":1,"non_appariees_mamh":4,
 "total_non_appariees":5,"score_dice":0.7826}
CATEGORIES=(
 "ANNEE_DATE_PROBABLE","PAGINATION_FOLIO_PROBABLE",
 "REFERENCE_REGLEMENTAIRE_PROBABLE",
 "COORDONNEE_IDENTIFIANT_PROBABLE","VALEUR_CHIFFREE_A_QUALIFIER",
 "INDETERMINE",
)
GATES=(
 "DOUBLE_HASH_SHA256_OCTETS_RECALCULE","TYPE_DE_RAPPORT_COMMUN_P54C",
 "EGALITE_OCCURRENCES_P54B","CINQ_OCCURRENCES_NON_APPARIEES",
 "REGLES_DE_CLASSIFICATION_CONSERVATRICES","EXTRAITS_BRUTS_HORS_GIT",
 "DIFFERENCE_NUMERIQUE_PAS_ECART_COMPTABLE",
 "SEPARATION_VALIDATION_HUMAINE",
)
GUARDS={
 "empreintes_source_recalculees","editions_changees_refusees",
 "comptes_p54b_devant_etre_reproduits",
 "classification_contextuelle_tentative",
 "aucun_montant_publie","aucun_token_brut_publie",
 "diagnostic_prive_uniquement_hors_git",
 "aucune_preuve_certification_comptable",
 "pages_pdf_zero_based","doctrine_2024_audit_specialise",
 "emplois_et_services_maintenus",
 "eliminations_deja_consolidees_protegees",
 "regimes_quebec_canada_et_souverain_distincts",
 "aucune_fusion_main",
}
DAYS=r"\b(?:janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)\b"
REGULATION=re.compile(r"(?:r\s*\.?\s*a\s*\.?\s*v\s*\.?\s*q|reglement|article\s+|norme\s+)",re.I)
FOLIO=re.compile(r"(?:\bpage\b|\bfolio\b|\bp\.\s*$|\bannexe\s+)",re.I)
CONTACT=re.compile(r"(?:\btel(?:ephone)?\b|\btelecopieur\b|\bfax\b|\bposte\b|\bcode\b|\badresse\b|\bnumero\s+de\b|\bno\.\s*$)",re.I)
VALUE=re.compile(r"(?:\$\s*$|\b(?:cad|dollars|milliers|m\$)\b|%\s*$)",re.I)

def need(ok,msg):
    if not ok:raise ValueError(msg)

def config():
    p54c.cfg()
    origin=verify_c.validate(json.loads(verify_c.SOURCE.read_text("utf-8")))
    d=json.loads(CONFIG.read_text("utf-8"))
    expect={
      "schema_version":"P54D-1","jalon":"P54D",
      "date_reference":"2026-10-24","exercice":2024,
      "source_p54c_run":40119313052,
      "pair_pdf_index_zero":PAGES,
      "reference_occurrences":REFERENCE,
      "categories":list(CATEGORIES),"controls":list(GATES),
      "guards":{x:True for x in GUARDS},
      "baseline":{
        "candidats_numeriques_non_apparies":5,
        "classifications_observees_en_p54d":None,
        "montant_comptable_authentifie":0,
        "anomalies_comptables_demontrees":0,
        "avis_independant_signe_nova":0,
        "economie_certifiee_cad":None,
        "decision":NO_GO,
      },
    }
    need(d==expect and origin["comparaison_lexicale"][
        "score_dice"]==REFERENCE["score_dice"],"CONFIG_OU_CHAINAGE_MODIFIE")
    return d

def normalize_context(s):
    s=unicodedata.normalize("NFKD",s.casefold())
    return "".join(c for c in s if not unicodedata.combining(c)).replace("’","'")

def instances(text):
    """Replicate precisely the P54B lexical parser and preserve occurrence offsets."""
    need(type(text) is str and len(text)<=1000000,"TEXTE_EXCESSIF")
    normalized=unicodedata.normalize("NFKC",text).replace("\u202f"," ")
    rows=[]
    for match in p54b.NUMERIC.finditer(normalized):
        raw=match.group(0).strip("()").replace("\u00a0","").replace(" ","")
        # Context is ephemeral; never returned as a public report.
        window=normalized[max(0,match.start()-55):
                          min(len(normalized),match.end()+55)]
        rows.append({"token":raw,"context":window,
                     "pos":match.start(),
                     "zone":("DEBUT" if match.start()<len(normalized)/3
                             else "MILIEU" if match.start()<2*len(normalized)/3
                             else "FIN")})
    need(Counter(r["token"] for r in rows)==p54b.tokens(text),
         "PARSEUR_P54B_NON_REPRODUIT")
    return rows

def unmatched(left,right):
    """One-for-one token removal: 1 city + 4 ministry occurrences expected."""
    l=instances(left);r=instances(right)
    cl=Counter(x["token"] for x in l);cr=Counter(x["token"] for x in r)
    common=cl & cr
    def residual(rows,remove):
        used=Counter();found=[]
        for item in rows:
            t=item["token"]
            if used[t]<remove[t]:used[t]+=1
            else:found.append(item)
        return found
    extra_l=residual(l,common);extra_r=residual(r,common)
    total_common=sum(common.values())
    need(len(l)==REFERENCE["ville"] and len(r)==REFERENCE["mamh"]
         and total_common==REFERENCE["communes"]
         and len(extra_l)==REFERENCE["non_appariees_ville"]
         and len(extra_r)==REFERENCE["non_appariees_mamh"],
         "MESURES_REELLES_NE_CONCORDENT_PAS_A_P54B")
    return {"ville":extra_l,"mamh":extra_r}

def classify(item):
    """Avoid inferring a financial discrepancy from surrounding numbers."""
    n=item["token"]
    context=normalize_context(item["context"])
    before=context.split(n,1)[0] if n in context else context[:55]
    # Numbers near regulatory labels can be folio references too; names indicate
    # only a probable textual category and no certified purpose.
    if REGULATION.search(before[-36:]):
        return "REFERENCE_REGLEMENTAIRE_PROBABLE"
    if (re.fullmatch(r"(?:19|20)\d{2}",n) or
            re.search(DAYS,before[-30:])):
        return "ANNEE_DATE_PROBABLE"
    if FOLIO.search(before[-27:]):
        return "PAGINATION_FOLIO_PROBABLE"
    if CONTACT.search(before[-37:]):
        return "COORDONNEE_IDENTIFIANT_PROBABLE"
    if VALUE.search(before[-12:]) or VALUE.search(context[-17:]):
        return "VALEUR_CHIFFREE_A_QUALIFIER"
    return "INDETERMINE"

def classify_extras(extras):
    public=[];private=[]
    for source in ("ville","mamh"):
        for item in extras[source]:
            category=classify(item)
            public.append({
              "source":source,
              "categorie_indicative":category,
              "zone_approximative":item["zone"],
              "qualification":"NON_CERTIFIEE",
            })
            private.append({
              "source":source,"token_brut":item["token"],
              "contexte_local":item["context"],
              "categorie_indicative":category,
            })
    need(len(public)==5 and
         Counter(x["source"] for x in public)=={"ville":1,"mamh":4},
         "INVENTAIRE_INCOMPLET")
    return public,private

def fetch_pair(fetcher=capture.capture,extract=p54c.page):
    observations={};texts={}
    for source in ("ville","mamh"):
        try:
            raw,meta=fetcher(source)
            reference=p54b.p54a.COPIES[source]
            ok=(type(raw) is bytes
                and len(raw)==reference[1]
                and hashlib.sha256(raw).hexdigest()==reference[2]
                and meta["source_id"]==source
                and meta["taille_octets"]==reference[1]
                and meta["sha256_fichier_copie_publique"]==reference[2])
            observations[source]={
                "capture":True,
                "version_p53z_identique":bool(ok)}
            if ok:texts[source]=extract(raw,PAGES[source])
        except (ValueError,KeyError,TypeError,OSError,IndexError):
            observations[source]={"capture":False,
                 "version_p53z_identique":False}
    if len(texts)!=2:
        return observations,None,None
    if not (p54c.analyze_text(texts["ville"],texts["mamh"])[
           "sections_se_rapportent_probablement_au_meme_audit"]):
        return observations,None,None
    try:
        extras=unmatched(texts["ville"],texts["mamh"])
        classified,private=classify_extras(extras)
        return observations,classified,private
    except (ValueError,KeyError,TypeError):
        return observations,None,None

def summary(observed,classes):
    ready=classes is not None
    counts=Counter(x["categorie_indicative"] for x in (classes or []))
    need(not ready or
         len(classes)==5 and
         sum(counts.values())==5 and
         all(x["qualification"]=="NON_CERTIFIEE" for x in classes),
         "RAPPORT_INCOMPLET")
    return {
      "schema_version":"P54D-BILAN-1",
      "source_p54c_run":40119313052,
      "source_exercice":2024,
      "pages_pdf_index_zero":PAGES,
      "sources":observed,
      "cinq_occurrences_verifiees":ready,
      "occurrences_non_appariees_reference":5,
      "categories_observees":dict(sorted(counts.items())) if ready else None,
      "observations_individuelles_sans_jets_bruts":classes,
      "expertise_comptable_independante_signee":False,
      "causes_documentaires_prouvees":0,
      "ecarts_de_montants_comptables_authentifies":0,
      "economie_certifiee_cad":None,
      "emploi_et_services_reduits_autorises":False,
      "fusion_autorisee":False,
      "decision":NO_GO,
    }

def write_json(path,obj,private=False):
    p=Path(path)
    need(not p.exists() and not p.is_symlink(),"REFUS_ECRASEMENT")
    if private:
        need(not p.resolve().is_relative_to(ROOT.resolve()) and
             p.parent.is_dir() and not p.parent.is_symlink(),
             "DIAGNOSTIC_PRIVE_DANS_DEPOT")
        fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as out:
            json.dump(obj,out,ensure_ascii=False,indent=2,sort_keys=True)
            out.write("\n")
    else:
        with p.open("x",encoding="utf-8") as out:
            json.dump(obj,out,ensure_ascii=False,indent=2,sort_keys=True)
            out.write("\n")

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reanalyser-copies",action="store_true")
    p.add_argument("--bilan")
    p.add_argument("--diagnostic-prive")
    p.add_argument("--exiger-preuve-comptable",action="store_true")
    a=p.parse_args(argv)
    try:
        need(not a.diagnostic_prive or a.reanalyser_copies,
             "DIAGNOSTIC_PRIVE_EXIGE_ACQUISITION")
        cfg=config()
        obs,rows,raw=(fetch_pair() if a.reanalyser_copies else ({},None,None))
        report=summary(obs,rows)
        if a.bilan:write_json(a.bilan,report)
        if a.diagnostic_prive and raw is not None:
            write_json(a.diagnostic_prive,{
             "schema_version":"P54D-DIAGNOSTIC-STRICTEMENT-LOCAL",
             "statut":"NON_CERTIFIE_CONTIENT_JETONS_ET_CONTEXTES",
             "donnees_brutes_non_diffusables":raw,
             "decision":NO_GO},private=True)
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        if a.exiger_preuve_comptable:return 3
        if a.reanalyser_copies and rows is None:return 4
        return 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as ex:
        print("P54D_REFUS: "+str(ex),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
