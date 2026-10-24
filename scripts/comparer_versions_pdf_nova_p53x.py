#!/usr/bin/env python3
"""P53X: comparer deux PDF fournis localement, jamais certifier leur provenance."""
import argparse
from collections import Counter,defaultdict,deque
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import unicodedata

import constituer_dossier_pilote_nova_p53w as prior

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets"/"projet-nova"/"etudes"/"P53X_PROTOCOLE_COMPARAISON_DEUX_PDF_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
URL_VILLE="https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf"
URL_MAMH="https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf"
PAGES_CIBLES=(0,34,196)
SIZE_MAX=67108864
PAGES_MAX=1200
MIN_CHARS=8
OPS=("COMPARAISON_SHA256_OCTETS","COMPARAISON_NOMBRES_PAGES",
     "CORRESPONDANCE_TEXTUELLE_NORMALISEE","REPERAGE_ANCRAGES_P53W")
GUARDS={
 "pdf_mamh_possiblement_assemble_de_plusieurs_documents",
 "comparaison_pas_preuve_d_identite_de_l_emetteur",
 "metadonnees_de_fichiers_pas_attestation_edition",
 "extraction_texte_egale_pas_audit_comptable",
 "absence_texte_extractible_pas_differend_comptable",
 "aucun_pdf_ni_detail_prive_dans_git",
 "suppression_infos_identifiantes_du_bilan_commun",
 "documents_officiels_pas_telecharges_par_ci",
 "version_officielle_pas_attestee_par_le_seul_hash",
 "deux_grands_livres_non_confrontes",
 "eliminations_deja_effectuees_non_recuperees",
 "maintien_emplois_services",
 "deux_regimes_constitutionnels_separes",
 "aucun_gain_certifie_et_aucune_fusion",
}

def require(ok,message):
    if not ok:
        raise ValueError(message)

def load_json(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink()
            and 0<p.stat().st_size<=30000,"FICHIER_SOURCE_INDISPONIBLE")
    result=json.loads(p.read_text("utf-8"))
    require(type(result) is dict,"SOURCE_JSON_NON_OBJET")
    return result

def sources():
    w=prior.load()
    cfg=load_json(CONFIG)
    expected={
      "schema_version":"P53X-1","jalon":"P53X","date_reference":"2026-10-24",
      "statut":"COMPARATEUR_PDF_LOCAL_SANS_ACQUISITION_OFFICIELLE",
      "exercice_reference":2024,
      "ville_code":"23027","rtc_code":"T0088",
      "sources_p53w":{"ville":URL_VILLE,"mamh":URL_MAMH},
      "controle_pages_ville":list(PAGES_CIBLES),
      "operations":list(OPS),
      "plafonds":{"taille_pdf_octets":SIZE_MAX,
                  "pages_pdf":PAGES_MAX,"caracteres_page_min":MIN_CHARS},
      "doctrine":{key:True for key in GUARDS},
      "etat_initial":{
        "organismes_lies":2,"publications_cibles":2,
        "pages_ville_ancres_documentaires":3,
        "originaux_octets_disponibles_dans_git":0,
        "controles_octets_effectues_sur_originaux_officiels":0,
        "preuves_de_versions_identiques":None,
        "provenance_authentifiee":0,
        "differences_comptables_certifiees":0,
        "differences_de_pagination_certifiees":0,
        "economies_certifiees_cad":None,"decision":NO_GO,
      },
    }
    require(cfg==expected and
            w["code_ville"]=="23027" and w["code_rtc"]=="T0088"
            and w["sources"]["ville"]["url"]==URL_VILLE
            and w["sources"]["mamh"]["url"]==URL_MAMH
            and w["sources"]["ville"]["sha256_fichier"] is None
            and w["sources"]["mamh"]["versions_confrontees"] is False
            and w["etat_initial"]["economies_certifiees_cad"] is None,
            "CHAINAGE_P53W_ET_CONFIG_NON_CONFORME")
    return cfg

def relative_pdf(name):
    require(type(name) is str and 1<=len(name)<=128
            and not name.startswith("/") and "\\" not in name
            and ":" not in name and
            re.fullmatch(r"[A-Za-z0-9_.\-/]+",name) is not None,
            "NOM_RELATIF_INTERDIT")
    path=PurePosixPath(name)
    require(1<=len(path.parts)<=5
            and all(p not in (".","..","") and not p.startswith(".")
                    for p in path.parts)
            and path.suffix.lower()==".pdf",
            "CHEMIN_PDF_NON_ADMIS")
    return path

def evidence_root(path):
    root=Path(path)
    require(root.is_dir() and not root.is_symlink(),
            "RACINE_ABSENTE_OU_LIEN_SYMBOLIQUE")
    resolved=root.resolve()
    require(not resolved.is_relative_to(ROOT.resolve()),
            "ORIGINAUX_INTERDITS_DANS_DEPOT_GIT")
    return root

def read_local_pdf(root,name):
    base=evidence_root(root)
    rel=relative_pdf(name)
    p=base
    for part in rel.parts:
        p=p/part
        require(not p.is_symlink(),"LIEN_SYMBOLIQUE_INTERDIT")
    require(p.resolve().is_relative_to(base.resolve()),
            "SORTIE_DE_RACINE_INTERDITE")
    mode=p.stat().st_mode
    size=p.stat().st_size
    require(stat.S_ISREG(mode) and 0<size<=SIZE_MAX,
            "TAILLE_OU_TYPE_PDF_INTERDIT")
    # The file is read only. Its bytes are not printed, uploaded or committed.
    data=p.read_bytes()
    require(len(data)==size and data.startswith(b"%PDF-"),
            "FICHIER_NON_PDF_OU_MODIFIE")
    return data

def normalized(content):
    if not content:
        return ""
    return re.sub(r"\s+"," ",
                  unicodedata.normalize("NFKC",content).casefold()).strip()

def pdf_pages(blob):
    from pypdf import PdfReader
    reader=PdfReader(BytesIO(blob),strict=True)
    require(not reader.is_encrypted,"PDF_CHIFFRE_A_NE_PAS_FORCER")
    total=len(reader.pages)
    require(1<=total<=PAGES_MAX,"NB_PAGES_INVALIDE")
    fingerprints=[]
    valid=[]
    for page in reader.pages:
        text=normalized(page.extract_text() or "")
        if len(text)<MIN_CHARS:
            fingerprints.append(None)
            valid.append(False)
        else:
            fingerprints.append(hashlib.sha256(text.encode("utf-8")).hexdigest())
            valid.append(True)
    return {"nombre_pages":total,"fingerprints":fingerprints,
            "pages_avec_texte":sum(valid),
            "pages_sans_texte_exploitable":total-sum(valid)}

def correlate(left,right):
    # The MAMH report may contain annexes, introductions, or other pages.
    # Match unique occurrences one-to-one; page numbers may differ.
    indices=defaultdict(deque)
    for index,digest in enumerate(right["fingerprints"]):
        if digest is not None:
            indices[digest].append(index)
    matches=[]
    for page_num,digest in enumerate(left["fingerprints"]):
        if digest is not None and indices[digest]:
            matches.append([page_num,indices[digest].popleft()])
    found={a:b for a,b in matches}
    anchors={str(index):(None if index>=left["nombre_pages"]
                          or left["fingerprints"][index] is None
                          else index in found)
             for index in PAGES_CIBLES}
    return {"pages_textuellement_appariees":len(matches),
            "correspondances_indices":matches,
            "ancrages_p53w_textuellement_retrouves":anchors,
            "textes_ville_non_apparies":left["pages_avec_texte"]-len(matches),
            "pages_ville_sans_texte_exploitable":left["pages_sans_texte_exploitable"],
            "pages_mamh_sans_texte_exploitable":right["pages_sans_texte_exploitable"]}

def compare(ville,mamh):
    # Caller must supply bytes they are legally allowed to inspect.
    require(type(ville) is bytes and type(mamh) is bytes and
            0<len(ville)<=SIZE_MAX and 0<len(mamh)<=SIZE_MAX,
            "OCTETS_NON_RECEVABLES")
    left=pdf_pages(ville)
    right=pdf_pages(mamh)
    comp=correlate(left,right)
    digest_v=hashlib.sha256(ville).hexdigest()
    digest_m=hashlib.sha256(mamh).hexdigest()
    result={
        "taille_octets_ville":len(ville),"taille_octets_mamh":len(mamh),
        "sha256_ville":digest_v,"sha256_mamh":digest_m,
        "octets_strictement_identiques":digest_v==digest_m,
        "pages_ville":left["nombre_pages"],
        "pages_mamh":right["nombre_pages"],
        "meme_nombre_pages":left["nombre_pages"]==right["nombre_pages"],
        **comp,
        "audit_comptable_effectue":False,
        "provenance_institutionnelle_authentifiee":False,
        "comparaison_version_source_certifiee":False,
        "economie_certifiee_cad":None,
    }
    return result

def summary(comp):
    if comp is None:
        fields={
          "comparaison_pdf_effectuee_localement":False,
          "octets_strictement_identiques":None,
          "nombre_pages_ville_mesure":None,
          "nombre_pages_mamh_mesure":None,
          "meme_nombre_pages":None,
          "pages_textuellement_appariees":None,
          "textes_ville_non_apparies":None,
          "pages_non_extractibles_ville":None,
          "pages_non_extractibles_mamh":None,
          "ancrages_p53w_textuellement_retrouves":{str(i):None for i in PAGES_CIBLES},
        }
    else:
        fields={
          "comparaison_pdf_effectuee_localement":True,
          "octets_strictement_identiques":comp["octets_strictement_identiques"],
          "nombre_pages_ville_mesure":comp["pages_ville"],
          "nombre_pages_mamh_mesure":comp["pages_mamh"],
          "meme_nombre_pages":comp["meme_nombre_pages"],
          "pages_textuellement_appariees":comp["pages_textuellement_appariees"],
          "textes_ville_non_apparies":comp["textes_ville_non_apparies"],
          "pages_non_extractibles_ville":comp["pages_ville_sans_texte_exploitable"],
          "pages_non_extractibles_mamh":comp["pages_mamh_sans_texte_exploitable"],
          "ancrages_p53w_textuellement_retrouves":
             comp["ancrages_p53w_textuellement_retrouves"],
        }
    return {
      "schema_version":"P53X-BILAN-1",
      "organismes_concernes":2,
      "exercice_comptable":2024,
      "sources_pdf_cibles":2,
      "constats_p53w_non_modifies":8,
      "questions_p53w_initialement_bloquantes":6,
      **fields,
      "identite_emetteur_confirmee_par_la_comparaison":False,
      "differends_comptables_demontres":0,
      "comparaisons_certifiees_par_expert":0,
      "grands_livres_apparies":0,
      "avis_comptables_independants_signes":0,
      "economie_certifiee_cad":None,
      "emplois_ou_services_degrades_autorises":False,
      "fusion_autorisee":False,
      "decision":NO_GO,
    }

def output(path,data,private=False):
    p=Path(path)
    require(not p.exists() and not p.is_symlink(),"ECRASEMENT_REFUSE")
    if private:
        # Internal details include document fingerprints. Never emit to CI artifacts.
        require(not p.resolve().is_relative_to(ROOT.resolve()),
                "RAPPORT_DETAIL_PRIVE_INTERDIT_DANS_GIT")
        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(data,f,indent=2,sort_keys=True,ensure_ascii=False)
            f.write("\n")
    else:
        with p.open("x",encoding="utf-8") as f:
            json.dump(data,f,indent=2,sort_keys=True,ensure_ascii=False)
            f.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bilan")
    parser.add_argument("--detail-prive")
    parser.add_argument("--racine")
    parser.add_argument("--ville")
    parser.add_argument("--mamh")
    parser.add_argument("--confirmer-acces-legal",action="store_true")
    parser.add_argument("--exiger-certification",action="store_true")
    args=parser.parse_args(argv)
    try:
        supplied=[bool(args.racine),bool(args.ville),bool(args.mamh)]
        require(all(supplied) or not any(supplied),
                "DEUX_FICHIERS_ET_RACINE_OBLIGATOIRES_ENSEMBLE")
        require(not any(supplied) or args.confirmer_acces_legal,
                "AUTORISATION_CONSULTATION_NON_DECLAREE")
        require(not args.detail_prive or all(supplied),
                "DETAIL_PRIVE_SANS_COMPARAISON")
        paths=[Path(p) for p in (args.bilan,args.detail_prive) if p]
        require(len({p.resolve() for p in paths})==len(paths) and
                all(not p.exists() and not p.is_symlink() for p in paths),
                "DESTINATIONS_EXISTANTES_OU_IDENTIQUES")
        sources()
        data=None
        if all(supplied):
            root=evidence_root(args.racine)
            v=read_local_pdf(root,args.ville)
            m=read_local_pdf(root,args.mamh)
            data=compare(v,m)
        results=summary(data)
        if args.bilan: output(args.bilan,results)
        if args.detail_prive: output(args.detail_prive,{
            "schema_version":"P53X-DETAIL-LOCAL-1",
            "statut":"EMPREINTES_DE_FICHIERS_FOURNIS_SANS_PREUVE_DE_SOURCE",
            "comparaison":data,
            "decision":NO_GO},True)
        print(json.dumps(results,sort_keys=True,ensure_ascii=False))
        return 3 if args.exiger_certification else 0
    except (ValueError,TypeError,OSError,KeyError,UnicodeError,
            json.JSONDecodeError) as e:
        print("P53X_REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
