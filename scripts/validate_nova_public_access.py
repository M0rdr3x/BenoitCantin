#!/usr/bin/env python3
"""Contrat indépendant des liens vers les sondages Nova sur la source et _site.

Aucune connexion réseau, collecte d'opinions ou publication.
"""
from __future__ import annotations
import argparse
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
PAGES=("index.html","projets/projet-nova/index.html")
RESOURCES=("projets/projet-nova/resultats-sondages.html",
           "projets/projet-nova/assets/resultats-sondages.js",
           "projets/projet-nova/data/resultats-sondages-publics-v1.json",
           "projets/projet-nova/consultation-40.html",
           "projets/projet-nova/sondage.html",
           "projets/projet-nova/assets/nova-sondage-icone.webp")
ICON="/projets/projet-nova/assets/nova-sondage-icone.webp"

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
        self.anchors=[]
        self.current=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get("id"): self.ids.append(a["id"])
        if tag=="a":
            self.current={"href":a.get("href"),"id":a.get("id"),"images":[]}
            self.anchors.append(self.current)
        if tag=="img" and self.current is not None:
            self.current["images"].append(a.get("src"))
    def handle_endtag(self,tag):
        if tag=="a":self.current=None

def check_text(pages):
    errors=[]
    rules={
      PAGES[0]:(
        "sondages-nova",
        (("home-sondage-40","/projets/projet-nova/consultation-40.html"),
         ("home-sondage-64","/projets/projet-nova/sondage.html")),
        (("/projets/projet-nova/consultation-40.html",ICON),),
        "collecte des réponses désactivée",
      ),
      PAGES[1]:(
        "consultations",
        (("nova-survey-directory-40","consultation-40.html"),
         ("nova-survey-directory-64","sondage.html")),
        (("consultation-40.html","assets/nova-sondage-icone.webp"),
         ("sondage.html","assets/nova-sondage-icone.webp")),
        "collecte fermée",
      ),
    }
    for page,(section,targets,images,disclosure) in rules.items():
        if page not in pages:
            errors.append("Page d'accueil absente: "+page)
            continue
        source=pages[page]
        html=Links()
        html.feed(source)
        if html.ids.count(section)!=1:
            errors.append(f"Section de sondage absente/dupliquée: {page}#{section}")
        for key,url in targets:
            matches=[a for a in html.anchors if a["id"]==key]
            if len(matches)!=1 or matches[0]["href"]!=url:
                errors.append(f"Lien Nova absent/inexact: {page}#{key}")
        for url,img in images:
            if not any(a["href"]==url and img in a["images"] for a in html.anchors):
                errors.append(f"Icône Nova non cliquable: {page} → {url}")
        if disclosure not in source.lower():
            errors.append(f"Collecte désactivée non annoncée: {page}")
    if PAGES[1] in pages and 'id="nova-public-results-link"' not in pages[PAGES[1]]:
        errors.append("Accès aux résultats anonymisés absent de l'accueil Nova")
    if PAGES[0] in pages and "non officiel et non représentatif" not in pages[PAGES[0]].lower():
        errors.append("Caractère consultatif non officiel absent de l'accueil général")
    return errors

def read_pages(root):
    return {p:(root/p).read_text("utf-8") for p in PAGES if (root/p).is_file()}

def audit(root,built=None):
    errors=["Source: "+msg for msg in check_text(read_pages(root))]
    for p in RESOURCES:
        if not (root/p).is_file():errors.append("Ressource source absente: "+p)
    if built is not None:
        errors+=["Artefact: "+msg for msg in check_text(read_pages(built))]
        for p in (*PAGES,*RESOURCES):
            if not (built/p).is_file():errors.append("Ressource absente du build: "+p)
            elif (root/p).is_file() and (built/p).read_bytes()!=(root/p).read_bytes():
                errors.append("Ressource source/build divergente: "+p)
    return errors

def self_test():
    original=read_pages(ROOT)
    assert not check_text(original),check_text(original)
    mutations=(
       (PAGES[0],'id="sondages-nova"','id="sondage-masqué"'),
       (PAGES[0],'id="home-sondage-40"','id="erreur-40"'),
       (PAGES[0],'id="home-sondage-64"','id="erreur-64"'),
       (PAGES[0],'src="'+ICON+'"','src="/assets/icône-erronée.webp"'),
       (PAGES[0],'collecte des réponses désactivée','collecte ouverte'),
       (PAGES[1],'id="consultations"','id="section-absente"'),
       (PAGES[1],'id="nova-survey-directory-40"','id="erreur-40"'),
       (PAGES[1],'id="nova-survey-directory-64"','id="erreur-64"'),
       (PAGES[1],'assets/nova-sondage-icone.webp','assets/image-inconnue.webp'),
       (PAGES[1],'collecte fermée','collecte active'),
       (PAGES[1],'id="nova-public-results-link"','id="resultats-absents"'),
    )
    for p,needle,replacement in mutations:
        assert needle in original[p],(p,needle)
        copy=dict(original);copy[p]=copy[p].replace(needle,replacement)
        assert check_text(copy),(p,needle)
    with TemporaryDirectory() as tmp:
        built=Path(tmp)
        for p in (*PAGES,*RESOURCES):
            dest=built/p;dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes((ROOT/p).read_bytes())
        assert not audit(ROOT,built),audit(ROOT,built)
        for p in RESOURCES:
            dest=built/p;content=dest.read_bytes();dest.unlink()
            assert audit(ROOT,built),p
            dest.write_bytes(content)
    print("OK : 10 mutations de navigation et 3 pertes d'artefacts rejetées")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=ROOT)
    parser.add_argument("--built",type=Path)
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:self_test()
    errors=audit(args.source,args.built)
    for err in errors:print("ECHEC : "+err)
    if errors:return 1
    print("OK : double accès Nova 40/64 et icône validés sur les deux portails")
    return 0
if __name__=="__main__":raise SystemExit(main())
