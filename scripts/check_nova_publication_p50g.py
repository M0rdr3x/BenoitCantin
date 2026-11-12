#!/usr/bin/env python3
"""P50G — Contrôle statique en lecture seule; ne publie ni n'autorise rien."""
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

PAGES = ("participer.html","avis-legal.html","code-conduite.html","recrutement.html","contact.html","confidentialite.html")
REQUIRED = {
"participer.html":"La participation citoyenne commence par un contact volontaire et limité",
"avis-legal.html":"n’exploite actuellement pas de formulaire externe de participation ni de contact",
"code-conduite.html":"Gouvernance du Projet Nova",
"recrutement.html":"Participer sans créer un dossier inutile",
"contact.html":"contact direct par courriel",
"confidentialite.html":"Les anciens formulaires Formspree demeurent suspendus",
}
OLD = {
"participer.html":"qui contient le formulaire intégré de soutien et de préadhésion",
"avis-legal.html":"Les formulaires servent uniquement à communiquer avec le Projet Nova",
"code-conduite.html":"Gouvernance du Parti Nova | Projet Nova",
}
EXTERNAL = re.compile(r"(?:formspree\.io|forms\.gle|docs\.google\.com/forms|typeform\.com|jotform\.com|checkout\.stripe\.com|paypal\.com/donate)",re.I)

class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.forms=0; self.targets=[]; self.script=False; self.js=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=="form": self.forms+=1
        if tag=="script": self.script=True
        self.targets.extend(str(d[k]) for k in ("href","action","src","data-url","formaction") if d.get(k))
    def handle_endtag(self,tag):
        if tag=="script": self.script=False
    def handle_data(self,data):
        if self.script: self.js.append(data)

def inspect(page,html):
    parser=Scan(); parser.feed(html); errors=[]
    if parser.forms: errors.append("FORMULAIRE_PRESENT")
    if any(EXTERNAL.search(s) for s in parser.targets + parser.js): errors.append("COLLECTE_OU_PAIEMENT_EXTERNE")
    if REQUIRED[page] not in html: errors.append("TEXTE_ATTENDU_ABSENT")
    if OLD.get(page,"\x00") in html: errors.append("MENTION_OBSOLETE")
    return {"page":page,"statut":"OK_STATIQUE" if not errors else "ECART_STATIQUE",
            "sha256":hashlib.sha256(html.encode("utf-8")).hexdigest(),"ecarts":errors}

def report(root):
    site=Path(root)/"projets"/"projet-nova"; pages=[]
    for page in PAGES:
        try: pages.append(inspect(page,(site/page).read_text(encoding="utf-8")))
        except (OSError,UnicodeError): pages.append({"page":page,"statut":"INDETERMINE","ecarts":["FICHIER_INACCESSIBLE"]})
    try:
        checklist=(site/"VERIFICATION_AVANT_PUBLICATION.md").read_text(encoding="utf-8")
        guard=(("formulaires externes demeurent suspendus" in checklist.lower()) and
               ("NE PAS FUSIONNER la PR 640" in checklist) and
               not re.search(r"\[\s*\]\s*Configurer Formspree",checklist,re.I))
    except (OSError,UnicodeError): guard=False
    good=all(p["statut"]=="OK_STATIQUE" for p in pages) and guard
    return {"jalon":"P50G","date_utc":datetime.now(timezone.utc).isoformat(),
            "origine":"COPIE_LOCALE_NON_PRODUCTION","pages":pages,
            "checklist_conforme":guard,"controle_statique":"OK" if good else "ECART_OU_INDETERMINE",
            "decision_publication":"NO_GO_AUTOMATIQUE",
            "autorisation_juridique_confirmee":False,"deploiement_confirme":False,
            "limite":"Revue, décision GO humaine, exercice hébergeur et recette HTTP réelle sont des portes externes."}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--rapport",type=Path)
    a=p.parse_args(argv); r=report(a.repo); output=json.dumps(r,ensure_ascii=False,indent=2)+"\n"
    if a.rapport:
        a.rapport.parent.mkdir(parents=True,exist_ok=True); a.rapport.write_text(output,encoding="utf-8")
    else: print(output)
    return 0 if r["controle_statique"]=="OK" else 2

if __name__=="__main__": sys.exit(main())
