#!/usr/bin/env python3
"""P53Y — traçabilité déclarative de deux versions documentaires."""
import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
import sys

import comparer_versions_pdf_nova_p53x as p53x

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P53Y_REGISTRE_VERSIONS_DOCUMENTAIRES.json"
NO_GO="NO_GO_AUTOMATIQUE"
SOURCES={"ville":p53x.URL_VILLE,"mamh":p53x.URL_MAMH}
CHECKS=(
 "PROVENANCE_SOURCE","INTEGRITE_REFERENCE","PAGINATION_ET_TEXTES",
 "ACCES_CONFIDENTIALITE","CONTREPARTIES_CONSOLIDATION",
 "AVIS_INDEPENDANTS_EMPLOIS_SERVICES",
)
GUARDS={
 "aucun_original_dans_git","hash_pas_provenance","metadonnees_non_signees",
 "comparaison_p53x_importee_non_reexecutee","incoherence_texte_pas_erreur_comptable",
 "pages_sans_texte_indeterminees","mamh_pdf_compose_de_documents_multiples",
 "aucun_taux_fiscal_adopte","pas_de_seconde_elimination_quebec_rtc",
 "maintien_emplois_et_services","avis_expert_independant_requis",
 "regimes_Quebec_Canada_et_souverain_separes","aucune_economie_certifiee",
 "aucune_fusion_automatique",
}
ROLES=("COLLECTE_DOCUMENTAIRE","REVUE_QUALITE_INDEPENDANTE")
TYPES=("TELECHARGEMENT_DECLARE","COPIE_REMIS_DECLAREE")
DATE=re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA=re.compile(r"^[a-f0-9]{64}$")
RECORD={
 "schema_version","source_id","type_acquisition","date_declaree",
 "role_collecte","role_relecture","sha256_declare","taille_octets",
 "nombre_pages","droit_acces","statut_provenance","avis_professionnel",
 "sauvegarde_emplois_services",
}
DETAIL={
 "taille_octets_ville","taille_octets_mamh","sha256_ville","sha256_mamh",
 "octets_strictement_identiques","pages_ville","pages_mamh",
 "meme_nombre_pages","pages_textuellement_appariees",
 "correspondances_indices","ancrages_p53w_textuellement_retrouves",
 "textes_ville_non_apparies","pages_ville_sans_texte_exploitable",
 "pages_mamh_sans_texte_exploitable","audit_comptable_effectue",
 "provenance_institutionnelle_authentifiee",
 "comparaison_version_source_certifiee","economie_certifiee_cad",
}

def require(valid,message):
    if not valid:raise ValueError(message)

def read(path,limit=200000):
    p=Path(path)
    require(p.is_file() and not p.is_symlink()
            and 0<p.stat().st_size<=limit,"FICHIER_REFUSE")
    obj=json.loads(p.read_text("utf-8"))
    require(type(obj) is dict,"OBJET_ATTENDU")
    return obj

def private_file(path):
    p=Path(path)
    require(not p.is_symlink() and
            not p.resolve().is_relative_to(ROOT.resolve()),
            "ENTREE_PRIVEE_DANS_DEPOT_GIT")
    return p

def sources():
    previous=p53x.sources()
    cfg=read(CONFIG,24000)
    base={
       "sources_suivies":2,"controles_en_attente":12,
       "fiches_versions_declares":0,
       "originaux_publiques_verifies_en_octets":0,
       "analyses_P53X_institutionnelles_certifiees":0,
       "versions_authentifiees_par_emetteur":0,
       "avis_professionnels_independants_signes":0,
       "faits_comptables_2024_certifies":0,
       "questions_P53W_bloquantes":6,
       "economie_certifiee_cad":None,
       "decision":NO_GO,
    }
    expected={
       "schema_version":"P53Y-1","jalon":"P53Y",
       "date_reference":"2026-10-24",
       "statut":"REGISTRE_VERSIONS_DECLARATIF_SANS_AUTHENTIFICATION",
       "exercice_reference":2024,
       "organisme_ville":"23027","organisme_rtc":"T0088",
       "sources":SOURCES,"controles":list(CHECKS),
       "categorie_acquisition":list(TYPES),"roles":list(ROLES),
       "verrous":{k:True for k in GUARDS},
       "etat_initial":base,
    }
    require(cfg==expected and
            previous["sources_p53w"]==SOURCES and
            previous["etat_initial"]["originaux_octets_disponibles_dans_git"]==0 and
            previous["etat_initial"]["economies_certifiees_cad"] is None,
            "CHAINAGE_P53X_INCOHERENT")
    return cfg

def register(cfg):
    rows=[]
    for source,url in cfg["sources"].items():
        rows.append({
          "source_id":source,"publication_reference":url,
          "exercice":2024,"statut":"AUCUNE_COPIE_AUTHENTIFIEE",
          "date_obtention_certifiee":None,
          "sha256_officiel_authentifie":None,
          "source_institutionnelle_authentifiee":False,
          "avis_independant_original_signe":False,
          "economie_certifiee_cad":None,
          "controles":[{"categorie":x,"statut":"A_VERIFIER"}
                       for x in CHECKS],
          "decision":NO_GO,
        })
    require(len(rows)==2 and
            sum(len(r["controles"]) for r in rows)==12,
            "REGISTRE_INCOMPLET")
    return rows

def validate_record(record):
    require(type(record) is dict and set(record)==RECORD
            and record.get("schema_version")=="P53Y-FICHE-1",
            "FICHE_NON_CONFORME")
    src=record["source_id"]
    require(type(src) is str and src in SOURCES and
            record["type_acquisition"] in TYPES,
            "SOURCE_OU_ACQUISITION_INVALIDE")
    day=record["date_declaree"]
    require(type(day) is str and DATE.fullmatch(day) is not None,
            "DATE_MAL_FORMEE")
    when=date.fromisoformat(day)
    require(date(2024,1,1)<=when<=date.today(),"DATE_HORS_PERIMETRE")
    require(record["role_collecte"]==ROLES[0]
            and record["role_relecture"]==ROLES[1],
            "ROLES_NON_SEPARES")
    digest=record["sha256_declare"]
    size=record["taille_octets"]
    pages=record["nombre_pages"]
    require(type(digest) is str and SHA.fullmatch(digest) is not None,
            "EMPREINTE_INVALIDE")
    require(type(size) is int and 0<size<=p53x.SIZE_MAX
            and type(pages) is int and 1<=pages<=p53x.PAGES_MAX,
            "TAILLE_OU_PAGES_INVALIDE")
    require(record["droit_acces"] in ("A_VERIFIER","DECLARE_NON_VERIFIE",
                                      "INTERDIT")
            and record["statut_provenance"] in ("INCONNUE",
                           "PUBLICATION_CANDIDATE_NON_AUTHENTIFIEE")
            and record["avis_professionnel"] in ("NON_OBTENU",
                           "DECLARE_NON_AUTHENTIFIE")
            and record["sauvegarde_emplois_services"] in ("A_VERIFIER",
                        "DECLAREE_NON_VERIFIEE","RISQUE_DECLARE"),
            "DECLARATION_DE_CERTIFICATION_INTERDITE")
    return {
      "source":src,"sha":digest,"size":size,"pages":pages,
      "bloque":record["droit_acces"]=="INTERDIT"
               or record["sauvegarde_emplois_services"]=="RISQUE_DECLARE",
    }

def validate_detail(raw):
    require(type(raw) is dict and
            set(raw)=={"schema_version","statut","comparaison","decision"}
            and raw["schema_version"]=="P53X-DETAIL-LOCAL-1"
            and raw["statut"]=="EMPREINTES_DE_FICHIERS_FOURNIS_SANS_PREUVE_DE_SOURCE"
            and raw["decision"]==NO_GO,
            "DETAIL_P53X_NON_RECEVABLE")
    d=raw["comparaison"]
    require(type(d) is dict and set(d)==DETAIL
            and d["economie_certifiee_cad"] is None
            and all(d[key] is False for key in (
              "audit_comptable_effectue","provenance_institutionnelle_authentifiee",
              "comparaison_version_source_certifiee")),
            "CERTIFICATION_FICTIVE_DANS_DETAIL")
    for source in SOURCES:
        digest=d["sha256_"+source]
        size=d["taille_octets_"+source]
        pages=d["pages_"+source]
        require(type(digest) is str and SHA.fullmatch(digest) is not None
                and type(size) is int and 0<size<=p53x.SIZE_MAX
                and type(pages) is int and 1<=pages<=p53x.PAGES_MAX,
                "META_SOURCE_NON_CONFORME")
    identical=d["sha256_ville"]==d["sha256_mamh"]
    page_equal=d["pages_ville"]==d["pages_mamh"]
    require(type(d["octets_strictement_identiques"]) is bool
            and d["octets_strictement_identiques"]==identical
            and type(d["meme_nombre_pages"]) is bool
            and d["meme_nombre_pages"]==page_equal
            and (not identical or (
                page_equal and
                d["taille_octets_ville"]==d["taille_octets_mamh"])),
            "CONTRADICTION_ENTRE_SHA_ET_PAGINATION")
    pairs=d["correspondances_indices"]
    require(type(pairs) is list and len(pairs)<=p53x.PAGES_MAX,
            "PAIRES_INCORRECTES")
    left=set();right=set();last=-1
    for pair in pairs:
        require(type(pair) is list and len(pair)==2
                and all(type(v) is int for v in pair),
                "PAIRE_DE_PAGE_INVALIDE")
        a,b=pair
        require(last<a<d["pages_ville"] and 0<=b<d["pages_mamh"]
                and b not in right,
                "APPARIEMENT_DE_PAGE_NON_UNIVOQUE")
        left.add(a);right.add(b);last=a
    count=d["pages_textuellement_appariees"]
    unmatched=d["textes_ville_non_apparies"]
    nontextleft=d["pages_ville_sans_texte_exploitable"]
    nontextright=d["pages_mamh_sans_texte_exploitable"]
    require(type(count) is int and count==len(pairs)
            and all(type(v) is int and v>=0 for v in (
                 unmatched,nontextleft,nontextright))
            and count+unmatched+nontextleft==d["pages_ville"]
            and count+nontextright<=d["pages_mamh"],
            "SOMMES_PAGES_INCOHERENTES")
    anchors=d["ancrages_p53w_textuellement_retrouves"]
    require(type(anchors) is dict and
            set(anchors)=={str(x) for x in p53x.PAGES_CIBLES},
            "ANCRAGES_INCORRECTS")
    for x in p53x.PAGES_CIBLES:
        state=anchors[str(x)]
        require(state is None or type(state) is bool,
                "ANCRAGE_NON_BOOLEEN")
        if x>=d["pages_ville"]:
            require(state is None,"ANCRAGE_HORS_BORNE")
        if x in left:require(state is True,"ANCRAGE_APPARIE_MASQUE")
        if state is True:require(x in left,"ANCRAGE_FAUX")
    if identical:
        require(unmatched==0 and count==d["pages_ville"]-nontextleft
                and nontextleft==nontextright,
                "TEXTE_OCTETS_IDENTIQUES_CONTRADICTOIRES")
    return d

def validate_set(rows,d):
    require(len(rows)<=2,"TROP_DE_FICHES")
    encountered=set();stats=Counter()
    for raw in rows:
        entry=validate_record(raw)
        key=entry["source"]
        require(key not in encountered,"FICHE_DUPLIQUEE")
        encountered.add(key)
        if d is not None:
            require(entry["sha"]==d["sha256_"+key]
                    and entry["size"]==d["taille_octets_"+key]
                    and entry["pages"]==d["pages_"+key],
                    "FICHE_CONTREDIT_DETAIL_P53X")
        stats["SUSPENDUE_DROITS_OU_SERVICES"
              if entry["bloque"] else
              "COPIE_DECLAREE_NON_AUTHENTIFIEE"]+=1
    return {"fiches":len(rows),
            "etats":dict(sorted(stats.items())),
            "detail_charge":d is not None}

def report(cfg,stats):
    return {
      "schema_version":"P53Y-RAPPORT-1",
      "exercice_de_reference":2024,
      "sources_ciblees":2,
      "controles_en_attente":12,
      "fiches_version_declarees":stats["fiches"],
      "statuts_agreges":stats["etats"],
      "detail_p53x_non_signe_importe":stats["detail_charge"],
      "copies_officielles_authentifiees":0,
      "avis_independants_signes":0,
      "comparaisons_certifiees":0,
      "conclusions_comptables_demontrees":0,
      "ecritures_reciproques_certifiees":0,
      "questions_P53W_non_resolues":6,
      "economie_certifiee_cad":None,
      "preuves_fiscales_F01_F20_validees":0,
      "montants_Nova_inconnus":1320,
      "baisse_emplois_services_autorisee":False,
      "fusion_autorisee":False,
      "decision":NO_GO,
    }

def write_new(path,obj):
    p=Path(path)
    require(not p.exists() and not p.is_symlink(),"ECRASEMENT_INTERDIT")
    with p.open("x",encoding="utf-8") as target:
        json.dump(obj,target,indent=2,sort_keys=True,ensure_ascii=False)
        target.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rapport")
    parser.add_argument("--registre")
    parser.add_argument("--fiche",action="append",default=[])
    parser.add_argument("--detail-p53x")
    parser.add_argument("--exiger-authentification",action="store_true")
    a=parser.parse_args(argv)
    try:
        require(len(a.fiche)<=2,"TROP_DE_FICHES")
        dest=[Path(x) for x in (a.rapport,a.registre) if x]
        require(len({p.resolve() for p in dest})==len(dest)
                and all(not p.exists() and not p.is_symlink() for p in dest),
                "SORTIE_INVALIDE")
        cfg=sources()
        detail=(validate_detail(read(private_file(a.detail_p53x)))
                if a.detail_p53x else None)
        entries=[read(private_file(p),12000) for p in a.fiche]
        stats=validate_set(entries,detail)
        bilan=report(cfg,stats)
        if a.rapport:write_new(a.rapport,bilan)
        if a.registre:write_new(a.registre,{
           "schema_version":"P53Y-REGISTRE-1",
           "statut":"DEUX_VERSIONS_OFFICIELLES_NON_AUTHENTIFIEES",
           "sources":register(cfg)})
        print(json.dumps(bilan,ensure_ascii=False,sort_keys=True))
        return 3 if a.exiger_authentification else 0
    except (ValueError,TypeError,OSError,KeyError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P53Y_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
