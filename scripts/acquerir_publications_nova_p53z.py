#!/usr/bin/env python3
"""P53Z — acquisition HTTPS de deux publications publiques et vérification d'octets.

La comparaison ne certifie ni la provenance de l'émetteur, ni le contenu financier.
Aucun document source n'est conservé dans GitHub ou publié comme artefact.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import comparer_versions_pdf_nova_p53x as p53x

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets"/"projet-nova"/"etudes"/"P53Z_ACQUISITION_PUBLICATIONS_OFFICIELLES.json"
SOURCE={"ville":p53x.URL_VILLE,"mamh":p53x.URL_MAMH}
HOSTS={
 "ville":{"www.ville.quebec.qc.ca","ville.quebec.qc.ca"},
 "mamh":{"www.mamh.gouv.qc.ca","mamh.gouv.qc.ca"},
}
MAX=p53x.SIZE_MAX
TIMEOUT=25
NO_GO="NO_GO_AUTOMATIQUE"
LIMITS=("TELECHARGEMENT_TLS_DOMAINES_OFFICIELS",
 "REJET_REDIRECTIONS_HORS_HOTES_ADMIS","CONTROLE_OCTETS_PDF",
 "SHA256_DES_OCTETS_REELLEMENT_ACQUIS","COMPARAISON_P53X_SANS_PREUVE_JURIDIQUE",
 "CITATION_ET_DATE_ACQUISITION","BILAN_SANS_ORIGINAL_PDF",
 "ERREUR_RESEAU_SANS_FAUSSE_PREUVE")
GUARDS={
 "aucune_piece_originale_dans_git",
 "aucune_image_ocr_extraction_texte_en_sortie",
 "aucun_telechargement_confidentiel",
 "aucun_url_personnalise_accepte",
 "domaines_de_redirection_restreints",
 "original_fichier_non_conserve_par_ci",
 "hachage_fichier_public_pas_preuve_identite_emetteur",
 "divergences_pdf_pas_anomalies_financieres",
 "date_observation_pas_date_creation_officielle",
 "rapprochement_grands_livres_non_realise",
 "elimination_reciproque_rtc_deja_effectuee",
 "emplois_et_services_maintenus",
 "regimes_constitutionnels_separes",
 "pas_de_fusion_automatique",
}

def need(ok,why):
    if not ok:raise ValueError(why)

def config():
    cfg=json.loads(CONFIG.read_text("utf-8"))
    base={
      "schema_version":"P53Z-1","jalon":"P53Z","date_reference":"2026-10-24",
      "statut":"ACQUISITION_PUBLICATIONS_OFFICIELLES_CONDITIONNELLE_SANS_CERTIFICATION",
      "exercice":2024,"organismes":["23027","T0088"],
      "sources":SOURCE,
      "plafonds":{"octets_par_pdf":MAX,"secondes_par_source":TIMEOUT,
                  "extraction_pages_max":p53x.PAGES_MAX},
      "controles":list(LIMITS),
      "gardes":{k:True for k in GUARDS},
      "etat_initial":{
        "publications_a_acquerir":2,
        "octets_officiels_acquis_dans_ce_jalon":0,
        "empreintes_publiees_par_organisme_emetteur_connues":0,
        "equivalences_pdf_constatees":None,
        "rapprochements_comptables_certifies":0,
        "avis_independants_signes":0,
        "economies_certifiees_cad":None,"decision":NO_GO},
    }
    prior=p53x.sources()
    need(cfg==base and prior["sources_p53w"]==SOURCE
         and prior["etat_initial"]["originaux_octets_disponibles_dans_git"]==0,
         "CONFIG_OU_CHAINAGE_P53X_INVALIDES")
    return cfg

def safe_url(url,source):
    need(source in SOURCE and type(url) is str,"SOURCE_INCONNUE")
    p=urlparse(url)
    need(p.scheme=="https" and p.hostname in HOSTS[source]
         and p.username is None and p.password is None
         and p.port in (None,443) and p.query=="" and p.fragment==""
         and p.path.startswith("/"),"URL_OU_REDIRECTION_INTERDITE")
    return url

class SafeRedirect(HTTPRedirectHandler):
    def __init__(self,source):
        self.source=source
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        safe_url(newurl,self.source)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def open_remote(url,source):
    safe_url(url,source)
    # urllib verifies CA certificates and HTTPS hostnames by default.
    opener=build_opener(SafeRedirect(source))
    request=Request(url,headers={
       "User-Agent":"ProjetNova-DocumentaryPublicVerification/1.0",
       "Accept":"application/pdf,application/octet-stream",
    })
    return opener.open(request,timeout=TIMEOUT)

def capture(source,opener=open_remote):
    """Télécharge en mémoire, vérifie le PDF et retourne octets+observations.

    The PDF bytes are intentionally kept out of stdout, disk and GitHub artifacts.
    """
    need(source in SOURCE,"SOURCE_INCONNUE")
    url=SOURCE[source]
    received=opener(url,source)
    with received as response:
        destination=response.geturl()
        safe_url(destination,source)
        headers=response.info()
        claimed=headers.get("Content-Length")
        mime=headers.get_content_type().lower()
        need(mime in ("application/pdf","application/octet-stream","binary/octet-stream"),
             "TYPE_HTTP_NON_PDF")
        if claimed is not None:
            need(claimed.isdigit() and 0<int(claimed)<=MAX,
                 "TAILLE_HTTP_NON_ADMISE")
        data=bytearray()
        while True:
            chunk=response.read(min(131072,MAX+1-len(data)))
            if not chunk:break
            data.extend(chunk)
            need(len(data)<=MAX,"DOCUMENT_TROP_VOLUMINEUX")
        need(len(data)>=8 and data.startswith(b"%PDF-")
             and b"%%EOF" in data[-1024:],
             "CONTENU_PDF_INCOMPLET_OU_INVALIDE")
        digest=hashlib.sha256(data).hexdigest()
        observation={
          "source_id":source,
          "url_source":url,
          "url_finale":destination,
          "date_capture_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
          "type_http":mime,
          "taille_octets":len(data),
          "sha256_fichier_copie_publique":digest,
          "empreinte_officielle_signee_verifiee":False,
          "identite_emetteur_certifiee":False,
        }
    return bytes(data),observation

def aggregate(samples):
    """Ne transforme pas une absence de capture en conformité."""
    rows={}
    raw={}
    for src in SOURCE:
        item=samples.get(src)
        if item is None:
            rows[src]={"statut":"NON_TENTE","source":SOURCE[src],
                       "sha256_fichier_copie_publique":None,
                       "pages_extraites":None}
        elif item.get("ok") is False:
            rows[src]={"statut":"ECHEC_ACQUISITION","source":SOURCE[src],
                       "erreur":item["erreur"],
                       "sha256_fichier_copie_publique":None,
                       "pages_extraites":None}
        else:
            obs=item["observation"]
            raw[src]=item["octets"]
            rows[src]={
               "statut":"COPIE_HTTPS_PUBLIQUE_OBSERVEE_NON_AUTHENTIFIEE",
               "source":SOURCE[src],
               "url_finale":obs["url_finale"],
               "capturé_utc":obs["date_capture_utc"],
               "taille_octets":obs["taille_octets"],
               "sha256_fichier_copie_publique":obs["sha256_fichier_copie_publique"],
               "pages_extraites":None,
               "identite_emetteur_certifiee":False,
            }
    comparison=None
    if len(raw)==2:
        try:
            comp=p53x.compare(raw["ville"],raw["mamh"])
            comparison=p53x.summary(comp)
            rows["ville"]["pages_extraites"]=comp["pages_ville"]
            rows["mamh"]["pages_extraites"]=comp["pages_mamh"]
        except (ValueError,IndexError,KeyError,TypeError) as exc:
            comparison={"comparaison_pdf_effectuee_localement":False,
                        "erreur":"ECHEC_EXTRACTION_OU_COMPARAISON"}
    return {
        "schema_version":"P53Z-BILAN-1",
        "exercice_sources":2024,
        "publications_cibles":2,
        "copies_https_observees":len(raw),
        "observations":rows,
        "comparaison":comparison,
        "comparaison_octets_officiels_effectuee":bool(comparison and
            comparison.get("comparaison_pdf_effectuee_localement")),
        "preuve_authenticite_emetteur":False,
        "empreintes_officielles_signées_verifiees":0,
        "appariements_comptables_certifies":0,
        "avis_comptables_independants_signes":0,
        "economies_certifiees_cad":None,
        "emplois_services_degrades_autorises":False,
        "fusion_autorisee":False,
        "decision":NO_GO,
    }

def failure_class(exc):
    if isinstance(exc,(HTTPError,URLError,TimeoutError,ConnectionError)):
        return "RESEAU_OU_HTTP_INDISPONIBLE"
    if isinstance(exc,(ValueError,KeyError)):
        return "REPONSE_NON_RECEVABLE"
    return "ERREUR_CAPTURE_TECHNIQUE"

def fetch_all(opener=open_remote):
    sampled={}
    for src in SOURCE:
        try:
            data,obs=capture(src,opener)
            sampled[src]={"ok":True,"octets":data,"observation":obs}
        except (ValueError,OSError,HTTPError,URLError,TimeoutError,
                ConnectionError,KeyError,TypeError) as exc:
            sampled[src]={"ok":False,"erreur":failure_class(exc)}
    return aggregate(sampled)

def write(path,summary):
    p=Path(path)
    need(not p.exists() and not p.is_symlink(),"SORTIE_EXISTANTE")
    with p.open("x",encoding="utf-8") as out:
        json.dump(summary,out,indent=2,sort_keys=True,ensure_ascii=False)
        out.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquerir",action="store_true")
    parser.add_argument("--bilan")
    parser.add_argument("--exiger-authenticite",action="store_true")
    args=parser.parse_args(argv)
    try:
        config()
        summary=fetch_all() if args.acquerir else aggregate({})
        if args.bilan:write(args.bilan,summary)
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        if args.exiger_authenticite:return 3
        if args.acquerir and not summary["comparaison_octets_officiels_effectuee"]:
            return 4
        return 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as e:
        print("P53Z_REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
