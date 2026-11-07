#!/usr/bin/env python3
"""P54C : examiner la nature d'une paire de pages d'audit; aucun audit Nova."""
import argparse
from collections import Counter
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys
import unicodedata
import re

from pypdf import PdfReader
import acquerir_publications_nova_p53z as p53z
import comparer_postes_financiers_nova_p54b as p54b

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"projets/projet-nova/etudes/P54C_EXAMEN_AUDIT_DEPENSES_MIXTES_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
PAGES={"ville":102,"mamh":162}
GATES=("SECTION_ET_NATURE_RAPPORT_AUDIT","EXERCICE_ET_DATE_REFERENCES",
       "PERIMETRE_DEPENSES_MIXTES_LOCALES_AGGLOMERATION",
       "REFERENTIEL_RAVQ_1435_ET_USAGE",
       "CONCORDANCE_ENTRE_PUBLICATIONS",
       "DIFFERENCES_JETONS_NUMERIQUES_NON_QUALIFIES",
       "SIGNATURES_AVIS_ET_LIMITES",
       "EFFETS_EMPLOIS_SERVICES_CONTREPARTIES")
GUARDS={
 "captures_P53Z_obligatoires","empreintes_recalculees_sur_octets",
 "changement_edition_bloquant","pages_pdf_zero_based",
 "page_auditee_ne_certifie_pas_economies",
 "seules_sections_de_meme_perimetre_comparables",
 "ecart_de_jetons_n_est_pas_anomalie",
 "signature_document_differe_expertise_nova",
 "aucunes_pieces_origines_dans_git","aucun_texte_brut_des_pages_exporte",
 "pas_de_pii_de_signataires_dans_bilan","protection_emplois_services",
 "elimination_reciproque_pas_nouveau_gain",
 "scenarios_quebec_canada_independant_separes",
 "zero_economie_certifiee","aucune_fusion_automatique"}
EVIDENCE={
 "document":"RAPPORT_DES_AUDITEURS_INDEPENDANTS_VENTILATION_DEPENSES_MIXTES",
 "perimetre":"COMPETENCES_AGGLOMERATION_ET_LOCALES",
 "exercice":"31_DECEMBRE_2024",
 "referentiel_cite":"R.A.V.Q. 1435",
 "provenance":"RAPPORT_MUNICIPAL_PAGE_PDF_102_INSPECTEE"
}
MARKERS={
 "rapport_auditeurs":("rapport des auditeurs independants",),
 "ventilation_depenses_mixtes":("ventilation des depenses mixtes",),
 "competences_locales":("competences de nature locale",),
 "competences_agglomeration":("competences d agglomeration","competences d'agglomeration"),
 "exercice_2024":("31 decembre 2024",),
 "referentiel_ravq":("ravq 1435","r a v q 1435","r.a.v.q. 1435"),
 "opinion":("opinion",),
}
def need(check,code):
    if not check:raise ValueError(code)

def normalize(s):
    s=unicodedata.normalize("NFKD",s.casefold())
    s="".join(x for x in s if not unicodedata.combining(x))
    return re.sub(r"\s+"," ",s).strip()

def cfg():
    earlier,pairs=p54b.config()
    d=json.loads(FILE.read_text("utf-8"))
    expected={
      "schema_version":"P54C-1","jalon":"P54C","exercice":2024,
      "date_reference":"2026-10-24",
      "titre":"EXAMEN_CIBLE_RAPPORT_AUDITEURS_DEPENSES_MIXTES",
      "source_p54b_run":40118178035,
      "pair_prioritaire":{
         "page_index_pdf_ville":102,"page_index_pdf_mamh":162,
         "score_dice_p54b":0.7826,
         "jetons_numeriques_ville":10,"jetons_numeriques_mamh":13,
         "jetons_numeriques_communs":9},
      "contexte_documente_ville":EVIDENCE,
      "sources":p53z.SOURCE,
      "controle_points":list(GATES),
      "verrous":{x:True for x in GUARDS},
      "etat_initial":{
        "pages_ciblees":2,"analyses_contextuelles_effectuees":0,
        "controles_pros_a_instruire":8,
        "examen_professionnel_independant_signe":0,
        "montants_certifies":0,
        "economies_certifiees_cad":None,
        "conclusion":NO_GO,
      },
    }
    need(d==expected and
         any(x["page_index_pdf_ville"]==102 and
             x["page_index_pdf_mamh"]==162 for x in pairs["candidates"])
         and earlier["etat_initial"]["montants_comparables_certifies"]==0,
         "CHAINAGE_2024_MODIFIE")
    return d

def indicators(text):
    need(type(text) is str and len(text)<=1000000,"PAGE_TEXTE_NON_RECEVABLE")
    s=normalize(text).replace("’","'")
    return {k:any(term in s for term in terms) for k,terms in MARKERS.items()}

def page(blob,index):
    need(type(blob) is bytes and 0<len(blob)<=p53z.MAX and
         type(index) is int and index>=0 and blob.startswith(b"%PDF-"),
         "PDF_NON_RECEVABLE")
    reader=PdfReader(BytesIO(blob),strict=True)
    need(not reader.is_encrypted and index<len(reader.pages)
         and len(reader.pages)<=p53z.p53x.PAGES_MAX,
         "PAGE_NON_ACCESSIBLE")
    return reader.pages[index].extract_text() or ""

def analyze_text(ville,mamh):
    a=indicators(ville);b=indicators(mamh)
    x=p54b.tokens(ville);y=p54b.tokens(mamh)
    nums=p54b.scores(x,y)
    # Diagnostic page scope; not a legal statement about the source PDFs.
    scores={k:sum(z.values()) for k,z in (("ville",a),("mamh",b))}
    both=(a["rapport_auditeurs"] and b["rapport_auditeurs"]
          and a["ventilation_depenses_mixtes"] and b["ventilation_depenses_mixtes"])
    return {
      "index_pdf_ville":102,"index_pdf_mamh":162,
      "indices_contextuels":{"ville":a,"mamh":b},
      "marqueurs_detectes":{"ville":scores["ville"],"mamh":scores["mamh"]},
      "sections_se_rapportent_probablement_au_meme_audit":both,
      "comparaison_lexicale":nums,
      "comparabilite_comptable_certifiee":False,
      "ecarts_financiers_verifies":0,
      "statut":"EXAMEN_CONTEXTE_DOCUMENTAIRE_NON_CERTIFIE",
    }

def capture_pair(fetcher=p53z.capture,extract=page):
    source_results={};blobs={}
    for origin in PAGES:
        try:
            content,meta=fetcher(origin)
            ref=p54b.p54a.COPIES[origin]
            ok=(type(content) is bytes and
                len(content)==ref[1] and
                hashlib.sha256(content).hexdigest()==ref[2] and
                meta["source_id"]==origin and
                meta["taille_octets"]==ref[1] and
                meta["sha256_fichier_copie_publique"]==ref[2])
            source_results[origin]={
              "capture":True,"copie_reference_P53Z_identique":bool(ok)}
            if ok:blobs[origin]=content
        except (ValueError,TypeError,KeyError,OSError):
            source_results[origin]={
              "capture":False,"copie_reference_P53Z_identique":False}
    if len(blobs)!=2:
        return source_results,None
    try:
        pair=analyze_text(extract(blobs["ville"],102),
                          extract(blobs["mamh"],162))
        return source_results,pair
    except (ValueError,TypeError,IndexError,KeyError):
        return source_results,None

def report(results,details):
    return {
      "schema_version":"P54C-RESULTAT-1",
      "exercice":2024,
      "pages_reference":{"ville":102,"mamh":162},
      "copies_observees":len(results),
      "references_octets_ok":bool(len(results)==2 and
         all(t["copie_reference_P53Z_identique"] for t in results.values())),
      "contexte_examine":details is not None,
      "contexte":details,
      "controle_qualitatifs_restant_a_attester":8,
      "expertise_independante_Nova_signature_valide":False,
      "concordance_comptable_certifiee":False,
      "montants_certifies":0,
      "economie_certifiee_cad":None,
      "reductions_emplois_services_autorisees":False,
      "fusion_autorisee":False,
      "decision":NO_GO,
    }

def write_new(path,obj):
    p=Path(path)
    need(not p.exists() and not p.is_symlink(),"REFUS_ECRASEMENT")
    with p.open("x",encoding="utf-8") as f:
        json.dump(obj,f,sort_keys=True,indent=2,ensure_ascii=False)
        f.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bilan")
    parser.add_argument("--reanalyser-copies",action="store_true")
    parser.add_argument("--exiger-audit-certifie",action="store_true")
    opts=parser.parse_args(argv)
    try:
        cfg()
        sources,observations=(
            capture_pair() if opts.reanalyser_copies else ({},None))
        summary=report(sources,observations)
        if opts.bilan:write_new(opts.bilan,summary)
        print(json.dumps(summary,sort_keys=True,ensure_ascii=False))
        if opts.exiger_audit_certifie:return 3
        if opts.reanalyser_copies and observations is None:return 4
        return 0
    except (ValueError,TypeError,KeyError,OSError,
            UnicodeError,json.JSONDecodeError) as err:
        print("P54C_REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
