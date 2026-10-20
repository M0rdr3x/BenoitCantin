#!/usr/bin/env python3
"""P52U: controle texte des deux pages budgétaires officielles. Toujours NO_GO."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import ssl
import sys
import time
import unicodedata
from urllib import request
try:
 from pypdf import PdfReader
except ImportError:
 PdfReader=None

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "manifest":D/"P52U_INSTRUCTION_HUMAINE_F09.json",
 "p52j":D/"P52J_RELECTURE_PRIMAIRE_BUDGET_2026_2027.json",
 "p52s":D/"P52S_RECEPISSES_HTTPS_OBSERVES_2026_10_20.json",
 "p52k":D/"P52K_REGISTRE_PROVENANCE_BUDGET.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
 "p52t":D/"P52T_PROCEDURE_DOUBLE_CAPTURE.json",
}
URLS=(
 "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_Discours.pdf",
 "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf")
class NoRedirect(request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):return None
def need(v,why):
 if not v:raise ValueError(why)
def read_json(path):
 p=Path(path)
 need(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<500000,
      "FICHIER_REFERENCE_INVALIDE")
 d=json.loads(p.read_text(encoding="utf-8"))
 need(type(d) is dict,"JSON_OBJET_ATTENDU")
 return d
def validate(files):
 need(type(files) is dict and set(files)==set(FILES),"SIX_REFERENCES_REQUISES")
 m,j,s,k,a,t=(files[key] for key in FILES)
 need(m.get("schema_version")=="P52U-1" and
      m.get("date_reference")=="2026-10-20" and
      m.get("statut")=="RELECTURE_AUTOMATISEE_DES_PAGES_A_VERIFIER" and
      m.get("decision")=="NO_GO_AUTOMATIQUE","MANIFESTE_INVALIDE")
 need(m.get("references")=={
      x:str(FILES[x].relative_to(ROOT)) for x in FILES if x!="manifest"},
      "REFERENCES_INCONCORDANTES")
 need(j.get("schema_version")=="P52J-1" and
      j.get("validation_de_nature",{}).get("preuve_F09_independamment_attestee") is False and
      j["validation_de_nature"].get("decision")=="NO_GO_AUTOMATIQUE",
      "P52J_FAUSSE_ATTESTATION")
 need(s.get("schema_version")=="P52S-RECU-1" and
      s.get("run_id")==39491881661 and
      s.get("gouvernance",{}).get("decision")=="NO_GO_AUTOMATIQUE",
      "RECU_P52S_FAUX")
 need(k.get("schema_version")=="P52K-1" and
      k.get("decision")=="NO_GO_AUTOMATIQUE" and
      all(x.get("empreinte_sha256_pdf_original") is None for x in k["fichiers_source"]),
      "P52K_NON_ARCHIVE_ATTENDUE")
 need(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
      a.get("required_evidence",[])[8].get("id")=="F09" and
      a["required_evidence"][8].get("statut")=="NON_VALIDE" and
      a["required_evidence"][8].get("preuve_independante_obtenue") is False,
      "F09_NON_VALIDE_ATTENDU")
 need(t.get("schema_version")=="P52T-1" and
      t.get("etat",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
      t["etat"].get("avis_signes")==0,"P52T_NO_GO_ATTENDU")
 ref1=j["transcription_discours_tableau3"]
 expected=[
  ref1["lignes_revenus"]+[
    {"id":v,"valeur_mcad":amount} for v,amount in
      ref1["sous_totaux_officiels_mcad"].items()],
  [{"id":v,"valeur_mcad":amount} for v,amount in
      j["transcription_plan_budgetaire_f2"]["montants_signes_comme_affiches_mcad"].items()]
 ]
 docs=m.get("documents")
 need(type(docs) is list and len(docs)==2 and
      [x.get("id") for x in docs]==["DISC2026_T3","PLAN2026_F2"],
      "DEUX_DOCUMENTS_F09_REQUIS")
 for i,(doc,old,jref) in enumerate(zip(docs,s["sources"],j["source_primaires"])):
  need(doc.get("id")==old["id"]==jref["id"] and
       doc.get("url")==jref["url"]==URLS[i] and
       doc.get("pages_attendues")==[34,426][i] and
       doc.get("page_tableau_pdf_zero")==jref["page_pdf_index_zero"] and
       doc.get("titre_tableau")==["TABLEAU 3","TABLEAU F.2"][i] and
       doc.get("taille_attendue_octets")==old["taille_octets"] and
       doc.get("sha256_attendu_octets_recus")==old["sha256_octets_recus"] and
       doc.get("valeurs_attendues")==expected[i] and
       len(doc["valeurs_attendues"])==[29,10][i] and
       doc.get("statut")=="A_VERIFIER_DANS_OCTETS_PDF",
       "DOCUMENT_ET_TRANSCRIPTION_DIVERGENTS")
 review=m.get("relecture_humaine",{})
 need(review.get("statut")=="A_MANDATER" and
      review.get("nom_du_relecteur") is None and
      all(review.get(field) is False for field in (
         "mandat_reel_verifie","declaration_interets_recue",
         "avis_independant_signe","relecture_contradictoire_terminee",
         "decision_competente_obtenue")) and
      set(m.get("autorisations",{}))=={"publication","fusion","adoption"} and
      all(x is False for x in m["autorisations"].values()),
      "REVUE_HUMAINE_FICTIVE")
 return docs
def tokens(text):
 text=unicodedata.normalize("NFKC",text).replace("−","-").replace("–","-")
 text=re.sub(r"(?<=\d)[ \t\u00a0\u202f](?=\d{3}(?!\d))","",text)
 text=re.sub(r"-\s+(?=\d)","-",text)
 return set(re.findall(r"(?<![\w])[-+]?\d+(?![\w])",text)),re.sub(r"\s+"," ",text).casefold()
def check_text(text,doc):
 values,norm=tokens(text)
 need(doc["titre_tableau"].casefold() in norm,"TITRE_TABLEAU_ABSENT")
 need(("2026-2027" in norm or "2026‑2027" in norm) and
      "revenus" in norm,"EXERCICE_OU_COLONNE_ABSENTS")
 missing=[x["id"] for x in doc["valeurs_attendues"]
          if str(int(x["valeur_mcad"])) not in values]
 return {"lignes_attendues":len(doc["valeurs_attendues"]),
         "lignes_retrouvees":len(doc["valeurs_attendues"])-len(missing),
         "lignes_absentes":missing,"relecture_humaine_independante":False}
def inspect_octets(data,doc):
 need(type(data) is bytes and len(data)==doc["taille_attendue_octets"],
      "TAILLE_PDF_DIFFERENTE")
 need(data.startswith(b"%PDF-") and b"%%EOF" in data[-4096:],
      "ENVELOPPE_PDF_INVALIDE")
 need(hashlib.sha256(data).hexdigest()==doc["sha256_attendu_octets_recus"],
      "EMPREINTE_PDF_DIFFERENTE")
 need(PdfReader is not None,"MODULE_PDF_ABSENT")
 pdf=PdfReader(BytesIO(data),strict=False)
 need(not pdf.is_encrypted and len(pdf.pages)==doc["pages_attendues"],
      "COMPTE_PAGES_INCONCORDANT")
 details=check_text(pdf.pages[doc["page_tableau_pdf_zero"]].extract_text() or "",doc)
 need(not details["lignes_absentes"],"MONTANTS_PDF_ABSENTS")
 return {"id":doc["id"],"pages_observees":len(pdf.pages),
         "page_tableau_index":doc["page_tableau_pdf_zero"],
         **details,"sha256_octets_confirme":True,
         "signature_editeur_verifiee":False}
def fetch_pdf(url):
 need(url in URLS,"URL_NON_AUTORISEE")
 opener=request.build_opener(
   request.HTTPSHandler(context=ssl.create_default_context()),NoRedirect())
 req=request.Request(url,headers={"Accept":"application/pdf",
                                   "User-Agent":"ProjetNova-P52U/1.0"})
 with opener.open(req,timeout=30) as r:
  need(r.status==200 and r.geturl()==url,"HTTP_REDIRECTION_REFUSEE")
  mimetype=(r.headers.get("Content-Type") or "").split(";")[0].lower().strip()
  need(mimetype in ("application/pdf","application/octet-stream"),"MIME_NON_PDF")
  announced=r.headers.get("Content-Length")
  need(announced is None or
       (announced.isdecimal() and int(announced)<=50_000_000),
       "LONGUEUR_PDF_INVALIDE")
  content=bytearray()
  while True:
   chunk=r.read(1024*1024)
   if not chunk:break
   content.extend(chunk)
   need(len(content)<=50_000_000,"LIMITE_PDF_DEPASSEE")
  need(announced is None or len(content)==int(announced),
       "TRANSFERT_TRONQUE")
  return bytes(content)
def audit(data,network=False,downloader=fetch_pdf):
 docs=validate(data)
 results=[]
 if network:
  for doc in docs:
   ok=False
   for idx in range(3):
    try:
     results.append(inspect_octets(downloader(doc["url"]),doc))
     ok=True
     break
    except (OSError,TimeoutError,ValueError):
     if idx<2:time.sleep(3)
   need(ok,"RECUPERATION_OU_PAGES_NON_VERIFIEES")
 return {"jalon":"P52U","decision":"NO_GO_AUTOMATIQUE",
         "mode":"pages_PDF_reellement_verifiees" if network else "schema_seul",
         "documents_controles":len(results),
         "valeurs_attendues":sum(x["lignes_attendues"] for x in results),
         "valeurs_retrouvees":sum(x["lignes_retrouvees"] for x in results),
         "details":results,"expert_independant_mandate":False,
         "signature_officielle_verifiee":False,
         "publication_autorisee":False,"fusion_autorisee":False,
         "adoption_autorisee":False}
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 for k,path in FILES.items():p.add_argument("--"+k,type=Path,default=path)
 p.add_argument("--reseau",action="store_true")
 p.add_argument("--exiger-expertise",action="store_true")
 p.add_argument("--rapport",type=Path)
 args=p.parse_args(argv)
 try:
  out=audit({k:read_json(getattr(args,k)) for k in FILES},args.reseau)
  code=3 if args.exiger_expertise else 0
 except (OSError,ValueError,KeyError,TypeError,UnicodeError) as e:
  out={"jalon":"P52U","decision":"NO_GO_AUTOMATIQUE",
       "etat":"CONTROLE_REJETE","categorie_erreur":type(e).__name__,
       "publication_autorisee":False,"fusion_autorisee":False,
       "adoption_autorisee":False}
  code=2
 try:
  outstr=json.dumps(out,ensure_ascii=False,indent=2)+"\n"
  if args.rapport:
   args.rapport.parent.mkdir(parents=True,exist_ok=True)
   with args.rapport.open("x",encoding="utf-8") as f:f.write(outstr)
  else:print(outstr,end="")
 except OSError:return 2
 return code
if __name__=="__main__":
 sys.exit(main())
