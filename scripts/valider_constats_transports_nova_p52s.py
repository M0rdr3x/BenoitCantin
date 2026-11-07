#!/usr/bin/env python3
"""P52S: vérifier un reçu historique réel vs un reçu actuel sans créer d'attestation."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
    "recu":STUDY/"P52S_RECEPISSES_HTTPS_OBSERVES_2026_10_20.json",
    "protocole":STUDY/"P52S_PROTOCOLE_RECUPERATION_PDF_2026_2027.json",
    "p52k":STUDY/"P52K_REGISTRE_PROVENANCE_BUDGET.json",
    "p52a":STUDY/"P52A_REGISTRE_PREUVES_FISCALES.json",
}
BASELINE=(
 ("DISC2026_T3","cf89d3d8d448cfa4155e2370be8226a904d393205f64962d23f45a40749acbfa",2109269,"2026-10-20T20:25:52+00:00"),
 ("PLAN2026_F2","a0efb80f1a75984d7f0933d7dd6630bc3306e91410a8cfbaa9005e72f788e0e0",5341975,"2026-10-20T20:25:53+00:00")
)
SHA=re.compile(r"[a-f0-9]{64}\Z")
REQUIRED_LIMITS=(
 "identification_binaire_reçue_ne_prouve_pas_identite_editeur",
 "aucune_copie_originale_permanente_entreposee",
 "empreintes_de_capture_pas_sha_officiellement_publies",
 "integrite_pdf_interne_non_certifiee",
 "aucune_signature_cryptographique_editeur_verifiee",
 "pas_de_double_relecture_humaine",
 "lecture_budgetaire_2026_2027_previsionnelle",
 "controles_github_ne_remplacent_pas_revision_independante"
)
def must(v,reason):
    if not v:raise ValueError(reason)
def read(path):
    p=Path(path)
    must(p.is_file() and not p.is_symlink() and
         0<p.stat().st_size<=300000,"JSON_INVALIDE_ABSENT")
    x=json.loads(p.read_text(encoding="utf-8"))
    must(type(x) is dict,"JSON_OBJET_ATTENDU")
    return x
def verify(data):
    must(type(data) is dict and set(data)==set(FILES),
         "QUATRE_SOURCES_REQUISES")
    r,p,k,a=(data[x] for x in FILES)
    must(r.get("schema_version")=="P52S-RECU-1" and
         r.get("jalon")=="P52S" and r.get("date_observation")=="2026-10-20" and
         r.get("statut")=="DEUX_RECEPTION_HTTPS_NON_ATTESTEES_NON_ARCHIVEES" and
         r.get("repo")=="M0rdr3x/BenoitCantin" and
         r.get("run_id")==39491881661 and
         r.get("run_url")==
           "https://github.com/M0rdr3x/BenoitCantin/actions/runs/39491881661" and
         r.get("run_sha")=="3e8e713183931d90dbcb4a851430a9c6b6a294d2",
         "SOURCE_RUN_NON_TRACE")
    must(p.get("schema_version")=="P52S-1" and
         p.get("statut")=="PROTOCOLE_ACQUISITION_TRANSITOIRE_SANS_ARCHIVE_PERMANENTE" and
         len(p.get("sources",[]))==2 and
         k.get("schema_version")=="P52K-1" and
         k.get("decision")=="NO_GO_AUTOMATIQUE" and
         len(k.get("fichiers_source",[]))==2 and
         all(kx.get("empreinte_sha256_pdf_original") is None and
             kx.get("attestation_externe_signee") is None for kx in k["fichiers_source"]),
         "PROTOCOLE_ET_ARCHIVE_DIFFERE")
    must(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
         a.get("automatic_go") is False and
         a.get("human_reviews_received") is False and
         [x.get("id") for x in a.get("required_evidence",[])]==
            [f"F{i:02d}" for i in range(1,21)] and
         all(x.get("statut")=="NON_VALIDE" and
             x.get("preuve_independante_obtenue") is False for x in a["required_evidence"]),
         "P52A_NON_ADOPTEE_EXIGEE")
    sources=r.get("sources")
    must(type(sources) is list and len(sources)==2,
         "DEUX_REÇUS_ATTENDUS")
    for i,(item,(ident,hashval,bytecount,date_)) in enumerate(zip(sources,BASELINE)):
        must(type(item) is dict and
             item.get("id")==ident==p["sources"][i].get("id")==
               k["fichiers_source"][i].get("id") and
             item.get("sha256_octets_recus")==hashval and
             SHA.fullmatch(item["sha256_octets_recus"]) and
             type(item.get("taille_octets")) is int and
             item["taille_octets"]==bytecount and
             item.get("date_utc_tentative")==date_ and
             datetime.fromisoformat(date_).tzinfo==timezone.utc and
             item.get("statut")=="OCTETS_PDF_RECUS_HTTPS_NON_AUTHENTIFIES" and
             item.get("type_mime_recu")=="application/pdf" and
             item.get("validation_tls_client_standard") is True and
             all(item.get(x) is False for x in (
                  "authenticite_ministerielle_attestee",
                  "archivage_permanent_obtenu",
                  "preuve_independante_F09_obtenue")),
             "REÇU_ALTERE_OU_CERTIFICATION_FAUSSE")
    limits=r.get("limitations")
    must(type(limits) is dict and set(limits)==set(REQUIRED_LIMITS) and
         all(limits.get(x) is True for x in REQUIRED_LIMITS),
         "RESERVES_DOC_SUPPRIMEES")
    gov=r.get("gouvernance",{})
    must(gov.get("total_sources_lues_au_moment_du_run")==2 and
         gov.get("pdf_originaux_archives_authentifies")==0 and
         gov.get("preuves_F01_F20_independantes_obtenues")==0 and
         all(gov.get(x) is False for x in (
              "publication_autorisee","fusion_autorisee","adoption_autorisee")) and
         gov.get("decision")=="NO_GO_AUTOMATIQUE",
         "FAUSSE_AUTORISATION")
    return sources

def comparison(baseline,now=None):
    must(type(baseline) is list and len(baseline)==2,
         "BASELINE_INCOMPLETE")
    changes=[]
    for source in baseline:
        state="REFERENCE_HISTORIQUE_SEULE"
        if now is not None:
            must(type(now) is dict and
                 now.get("schema_version")=="P52S-1" and
                 now.get("mode")=="sonde" and
                 now.get("sources_attendues")==2 and
                 now.get("archives_officielles_certifiees")==0 and
                 now.get("avis_independants_F09_obtenus")==0 and
                 now.get("adoption_autorisee") is False and
                 now.get("decision")=="NO_GO_AUTOMATIQUE" and
                 type(now.get("reçus_techniques")) is list and
                 len(now["reçus_techniques"])==2,
                 "NOUVELLE_TENTATIVE_NON_FIABLE")
            current=next((x for x in now["reçus_techniques"]
                            if x.get("id")==source["id"]),None)
            must(current is not None,"SOURCE_NON_PRESENTE_DANS_LE_RECU")
            must(current.get("archive_permanente_obtenue") is False and
                 current.get("signature_ministerielle_verifiee") is False,
                 "SOURCES_FICTIVEMENT_AUTHENTIFIEES")
            if current.get("statut")=="OCTETS_PDF_RECUS_HTTPS_NON_AUTHENTIFIES":
                digest=current.get("sha256_octets_recus")
                must(type(digest) is str and SHA.fullmatch(digest) is not None and
                     type(current.get("taille_octets")) is int,
                     "RECU_COURANT_SANS_HASH")
                state=("OCTETS_IDENTIQUES_A_LA_REFERENCE"
                       if digest==source["sha256_octets_recus"] and
                          current["taille_octets"]==source["taille_octets"]
                       else "OCTETS_DIFFERENTS_REQUIERENT_EXAMEN")
            else:
                must(current.get("sha256_octets_recus") is None and
                     current.get("taille_octets") is None and
                     current.get("statut")=="SOURCE_NON_RECUPEREE",
                     "ERREUR_RESEAU_CONSISTANCE")
                state="SOURCE_NON_RECUPEREE_REQUIERT_EXAMEN"
        changes.append({"id":source["id"],
                        "etat_comparaison":state})
    exact=now is not None and all(x["etat_comparaison"]==
                "OCTETS_IDENTIQUES_A_LA_REFERENCE" for x in changes)
    return {
       "jalon":"P52S","schema_version":"P52S-RECU-1",
       "recepisses_historiques_documentes":2,
       "flux_aujourdhui_identiques_a_octets_observes":2 if exact else
          sum(x["etat_comparaison"]=="OCTETS_IDENTIQUES_A_LA_REFERENCE"
              for x in changes),
       "comparaisons":changes,
       "validation_du_ministere_ou_signature_externe":False,
       "copies_permanentes_archives":0,
       "preuve_F09_independante_obtenue":False,
       "publication_autorisee":False,
       "fusion_autorisee":False,
       "adoption_autorisee":False,
       "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for k,p in FILES.items():parser.add_argument("--"+k,type=Path,default=p)
    parser.add_argument("--capture",type=Path)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--exiger-reproductibilite",action="store_true")
    parser.add_argument("--exiger-attestation",action="store_true")
    args=parser.parse_args(argv)
    try:
        baseline=verify({k:read(getattr(args,k)) for k in FILES})
        now=read(args.capture) if args.capture else None
        outcome=comparison(baseline,now)
        exitcode=(3 if args.exiger_attestation or
                  (args.exiger_reproductibilite and
                   outcome["flux_aujourdhui_identiques_a_octets_observes"]!=2)
                  else 0)
    except (OSError,UnicodeError,ValueError,TypeError,KeyError) as exc:
        outcome={"jalon":"P52S","statut":"REÇU_NON_CONFORME",
                 "categorie_erreur":type(exc).__name__,
                 "publication_autorisee":False,
                 "fusion_autorisee":False,
                 "adoption_autorisee":False,
                 "decision":"NO_GO_AUTOMATIQUE"}
        exitcode=2
    out=json.dumps(outcome,ensure_ascii=False,indent=2)+"\n"
    if args.rapport:
        try:
            args.rapport.parent.mkdir(parents=True,exist_ok=True)
            with args.rapport.open("x",encoding="utf-8") as stream:stream.write(out)
        except OSError:return 2
    else:print(out,end="")
    return exitcode
if __name__=="__main__":
    sys.exit(main())
