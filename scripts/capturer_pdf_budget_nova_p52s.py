#!/usr/bin/env python3
"""P52S: capture HTTPS éphémère de PDF publics, SHA-256 des octets et NO_GO constant."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import ssl
import sys
from datetime import datetime, timezone
from urllib import request
from urllib.error import HTTPError, URLError

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
  "p52s":STUDY/"P52S_PROTOCOLE_RECUPERATION_PDF_2026_2027.json",
  "p52j":STUDY/"P52J_RELECTURE_PRIMAIRE_BUDGET_2026_2027.json",
  "p52k":STUDY/"P52K_REGISTRE_PROVENANCE_BUDGET.json",
  "p52r":STUDY/"P52R_RECONCILIATION_ET_RECEPTION_ORIGINAUX.json",
  "p52a":STUDY/"P52A_REGISTRE_PREUVES_FISCALES.json"
}
IDS=("DISC2026_T3","PLAN2026_F2")
URLS=(
 "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_Discours.pdf",
 "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf"
)
MAX=50_000_000
SOURCE_FIELDS={"id","url","pages_attendues_source_lecture_web","page_tableau_pdf_zero","tableau",
               "preuve","statut_provenance","sha256_pdf_officiel_atteste","taille_octets_archivee",
               "document_archivage_effectue","signature_editeur_verifiee","avis_expert_independant"}
FLAGS=(
 "telechargement_sans_redirection_externe",
 "TLS_chaine_systeme_verifiee_sans_attestation_editeur",
 "source_hostname_et_URL_strictement_listees",
 "aucun_pdf_original_enregistre_dans_git",
 "aucun_pdf_original_conserve_en_artefact",
 "rapport_hash_octets_et_taille_sans_certification",
 "saisie_manuelle_des_horodatages_interdite",
 "reponse_html_refusee","toute_erreur_de_reseau_ne_produit_pas_de_hash",
 "statut_Actions_reussi_ne_prouve_pas_F09",
 "fournir_empreintes_a_l_archive_independante_sans_adoption_automatique"
)

def must(value,why):
    if not value:raise ValueError(why)

def read(path):
    p=Path(path)
    must(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=450000,
         "FICHIER_DE_REFERENCE_INVALIDE")
    obj=json.loads(p.read_text(encoding="utf-8"))
    must(type(obj) is dict,"FICHIER_JSON_NON_OBJET")
    return obj

def validate(d):
    must(type(d) is dict and set(d)==set(FILES),"CINQ_REFERENCES_ATTENDUES")
    s,j,k,r,a=(d[x] for x in FILES)
    must(s.get("schema_version")=="P52S-1" and
         s.get("jalon")=="P52S" and s.get("date_reference")=="2026-10-20" and
         s.get("statut")=="PROTOCOLE_ACQUISITION_TRANSITOIRE_SANS_ARCHIVE_PERMANENTE",
         "MANIFESTE_P52S_INVALIDE")
    must(s.get("references")=={
      key:str(FILES[key].relative_to(ROOT)) for key in FILES if key!="p52s"
    },"CHEMINS_MANIFESTE_NON_CONCORDANTS")
    must(j.get("schema_version")=="P52J-1" and
         j.get("validation_de_nature",{}).get("verification_hash_pdf_original") is False and
         j["validation_de_nature"].get("preuve_F09_independamment_attestee") is False and
         j["validation_de_nature"].get("decision")=="NO_GO_AUTOMATIQUE",
         "P52J_NE_DOIT_PAS_ETRE_CERTIFIE")
    must(k.get("schema_version")=="P52K-1" and
         k.get("decision")=="NO_GO_AUTOMATIQUE" and
         r.get("schema_version")=="P52R-1" and
         r.get("etat_dossiers",{}).get("F09")=="NON_VALIDE" and
         r["etat_dossiers"].get("decision")=="NO_GO_AUTOMATIQUE",
         "P52K_P52R_NE_DOIVENT_PAS_ETRE_CERTIFIES")
    must(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
         a.get("automatic_go") is False and a.get("rates_selected") is False and
         a.get("financial_model_certified") is False and
         [x.get("id") for x in a.get("required_evidence",[])]==
         [f"F{i:02d}" for i in range(1,21)] and
         all(x.get("statut")=="NON_VALIDE" and
             x.get("preuve_independante_obtenue") is False for x in a["required_evidence"]),
         "P52A_PREUVES_NON_AUTORISEES")
    records=s.get("sources")
    earlier=[j.get("source_primaires"),k.get("fichiers_source"),r.get("origine_constats")]
    must(type(records) is list and len(records)==2 and
         all(type(z) is list and len(z)==2 for z in earlier),
         "DEUX_SOURCES_REQUISES")
    for i,record in enumerate(records):
        must(type(record) is dict and set(record)==SOURCE_FIELDS and
             record.get("id")==IDS[i] and record.get("url")==URLS[i] and
             record.get("pages_attendues_source_lecture_web")==[34,426][i] and
             record.get("page_tableau_pdf_zero")==[29,277][i] and
             record.get("tableau")==["Tableau 3","Tableau F.2"][i] and
             record.get("preuve")=="F09" and
             record.get("statut_provenance")=="LIEN_OFFICIEL_CONSULTE_PAS_FICHIER_ARCHIVE" and
             record.get("sha256_pdf_officiel_atteste") is None and
             record.get("taille_octets_archivee") is None and
             all(record.get(z) is False for z in (
                 "document_archivage_effectue","signature_editeur_verifiee",
                 "avis_expert_independant")),
             "SOURCE_INTENTION_OU_FAUSSE_PREUVE")
        for list_ in earlier:
            must(list_[i].get("id")==IDS[i] and list_[i].get("url")==URLS[i],
                 "P52J_K_R_REFERENCES_INCOHERENTES")
        must(j["source_primaires"][i].get("empreinte_sha256_pdf") is None and
             k["fichiers_source"][i].get("empreinte_sha256_pdf_original") is None and
             k["fichiers_source"][i].get("acquisition_document_origine")=="NON_EFFECTUEE" and
             r["origine_constats"][i].get("sha256_original") is None,
             "PDF_ORIGINAL_FAUSSEMENT_ACQUIS")
    c=s.get("conditions")
    must(type(c) is dict and set(c)==set(FLAGS)|{"taille_octets_maximum"} and
         all(c[f] is True for f in FLAGS) and
         type(c.get("taille_octets_maximum")) is int and
         c["taille_octets_maximum"]==MAX,
         "GARDES_HTTPS_RELACHEES")
    state=s.get("etat")
    must(type(state) is dict and
         all(type(state.get(k)) is int and state[k]==0 for k in (
             "originaux_pdf_archives_avec_preuve",
             "hashes_sources_officielles_certifies",
             "attestations_F09_independantes",
             "preuves_F01_F20_validees")) and
         all(state.get(k) is False for k in (
             "modele_financier_Nova_certifie","fonds_publics_engages",
             "publication_autorisee","fusion_autorisee","adoption_autorisee")) and
         state.get("decision")=="NO_GO_AUTOMATIQUE",
         "GO_INVENTE")
    return records

class RefuserRedirections(request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

def fetch_one(url,opener=None):
    must(url in URLS and url.startswith("https://"),
         "URL_SOURCE_NON_AUTORISEE")
    if opener is None:
        opener=request.build_opener(
            request.HTTPSHandler(context=ssl.create_default_context()),
            RefuserRedirections())
    req=request.Request(url,headers={
        "User-Agent":"ProjetNova-P52S-source-integrity/1.0",
        "Accept":"application/pdf"
    },method="GET")
    with opener.open(req,timeout=20) as res:
        must(res.geturl()==url and res.status==200,
             "REPONSE_REDIRECTION_OU_HTTP_INVALIDE")
        h=res.headers
        typ=(h.get("Content-Type") or "").split(";")[0].strip().lower()
        must(typ in ("application/pdf","application/octet-stream"),
             "TYPE_MEDIATIQUE_NON_PDF")
        content_size=h.get("Content-Length")
        if content_size:
            must(content_size.isdecimal() and int(content_size)<=MAX,
                 "TAILLE_DECLAREE_INVALIDE")
        digest=hashlib.sha256()
        size=0
        header=b""
        tail=b""
        while True:
            block=res.read(1_048_576)
            if not block:break
            must(type(block) is bytes,"REPONSE_NON_BINAIRE")
            size+=len(block)
            must(size<=MAX,"TAILLE_REELLE_DEPASSEE")
            digest.update(block)
            if len(header)<8:header=(header+block)[:8]
            tail=(tail+block)[-4096:]
        must(size>=32 and header.startswith(b"%PDF-") and
             b"%%EOF" in tail,
             "SIGNATURE_PDF_SOMMAIRE_ABSENTE")
        return {
            "statut":"OCTETS_PDF_RECUS_HTTPS_NON_AUTHENTIFIES",
            "sha256_octets_recus":digest.hexdigest(),
            "taille_octets":size,
            "type_mime_recu":typ,
            "validation_tls_client_standard":True,
            "controle_structurel_pdf_complet":False,
            "archive_permanente_obtenue":False,
            "signature_ministerielle_verifiee":False
        }

def run(d,mode="bilan",opener=None):
    rows=validate(d)
    source_out=[]
    for item in rows:
        obs={
            "id":item["id"],
            "statut":"NON_TESTE_CETTE_EXECUTION",
            "sha256_octets_recus":None,
            "taille_octets":None,
            "date_utc_tentative":None,
            "categorie_echec":None,
            "archive_permanente_obtenue":False,
            "signature_ministerielle_verifiee":False
        }
        if mode=="sonde":
            obs["date_utc_tentative"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
            try:
                receipt=fetch_one(item["url"],opener=opener)
                obs.update(receipt)
            except (HTTPError,URLError,TimeoutError,OSError,ValueError,TypeError) as exc:
                obs["statut"]="SOURCE_NON_RECUPEREE"
                obs["categorie_echec"]=type(exc).__name__
        source_out.append(obs)
    acquired=sum(x["statut"]=="OCTETS_PDF_RECUS_HTTPS_NON_AUTHENTIFIES"
                 for x in source_out)
    return {
        "jalon":"P52S","schema_version":"P52S-1",
        "mode":mode,
        "sources_attendues":2,
        "tentatives_reseau_effectuees":2 if mode=="sonde" else 0,
        "flux_pdf_recus_non_authentifies":acquired,
        "sources_non_recuperees":sum(
            x["statut"]=="SOURCE_NON_RECUPEREE" for x in source_out),
        "reçus_techniques":source_out,
        "archives_officielles_certifiees":0,
        "avis_independants_F09_obtenus":0,
        "preuves_F01_F20_validees":0,
        "publication_autorisee":False,
        "fusion_autorisee":False,
        "adoption_autorisee":False,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for key,f in FILES.items():p.add_argument("--"+key,type=Path,default=f)
    p.add_argument("--mode",choices=("bilan","sonde"),default="bilan")
    p.add_argument("--rapport",type=Path)
    p.add_argument("--exiger-originaux",action="store_true")
    p.add_argument("--exiger-expertise",action="store_true")
    args=p.parse_args(argv)
    try:
        result=run({key:read(getattr(args,key)) for key in FILES},args.mode)
        code=3 if args.exiger_expertise or (
            args.exiger_originaux and result["flux_pdf_recus_non_authentifies"]!=2
        ) else 0
    except (OSError,ValueError,TypeError,UnicodeError,KeyError) as exc:
        result={
            "jalon":"P52S","statut":"ECHEC_CONTROLE",
            "categorie_erreur":type(exc).__name__,
            "publication_autorisee":False,
            "fusion_autorisee":False,
            "adoption_autorisee":False,
            "decision":"NO_GO_AUTOMATIQUE"
        }
        code=2
    payload=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.rapport:
        try:
            args.rapport.parent.mkdir(parents=True,exist_ok=True)
            with args.rapport.open("x",encoding="utf-8") as f:f.write(payload)
        except OSError:return 2
    else:print(payload,end="")
    return code

if __name__=="__main__":
    sys.exit(main())
