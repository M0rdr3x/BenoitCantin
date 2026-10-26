#!/usr/bin/env python3
"""P52K - Audit fail closed; empreinte locale PDF sans validation de provenance."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
    "registre":STUDY/"P52K_REGISTRE_PROVENANCE_BUDGET.json",
    "relecture":STUDY/"P52J_RELECTURE_PRIMAIRE_BUDGET_2026_2027.json",
    "preuves":STUDY/"P52A_REGISTRE_PREUVES_FISCALES.json",
    "pistes":STUDY/"P52I_SOURCES_ET_ATTESTATIONS.json"
}
MAX_PDF_BYTES=80*1024*1024
MAX_JSON_BYTES=350_000
EXPECTED=(
    ("DISC2026_T3","https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_Discours.pdf","Tableau 3","27",29),
    ("PLAN2026_F2","https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf","Tableau F.2","F.9",277),
)
REQUIRED_CHAIN={
    "PDF_originaux_recuperes_et_empreintes_comparees",
    "versions_officielles_archivees_avec_droits",
    "horodatage_externe_verifiable",
    "revision_humaine_independante",
    "verification_conflit_interets_des_reviseurs",
    "confrontation_budget_actualise_et_comptes_reels",
    "analyse_independante_impact_menages_et_entreprises",
    "competence_et_autorisation_democratique"
}

def require(cond,code):
    if not cond: raise ValueError(code)

def json_read(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size<=MAX_JSON_BYTES,
            "SOURCE_JSON_ABSENTE_OU_INADMISSIBLE")
    obj=json.loads(p.read_text(encoding="utf-8"))
    require(type(obj) is dict,"SOURCE_JSON_NON_OBJET")
    return obj

def verifier_registre(src):
    require(type(src) is dict and set(src)==set(FILES),"QUATRE_SOURCES_REQUISES")
    r,j,a,i=(src[k] for k in FILES)
    require(r.get("schema_version")=="P52K-1" and
            r.get("jalon")=="P52K" and r.get("statut")=="CHAINE_PREUVE_EN_ATTENTE" and
            r.get("date_reference")=="2026-10-19","SCHEMA_REGISTRE_INCORRECT")
    require(r.get("ref_p52j")==str(FILES["relecture"].relative_to(ROOT)) and
            r.get("ref_p52a")==str(FILES["preuves"].relative_to(ROOT)) and
            r.get("ref_p52i")==str(FILES["pistes"].relative_to(ROOT)),
            "REFERENCES_NON_CONCORDANTES")
    require(all(r.get(k) is False for k in
                ("publication_autorisee","fusion_autorisee","adoption_autorisee")) and
            r.get("decision")=="NO_GO_AUTOMATIQUE",
            "GO_INTERDIT")
    require(j.get("schema_version")=="P52J-1" and
            j.get("validation_de_nature",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
            j["validation_de_nature"].get("preuve_F09_independamment_attestee") is False and
            j["validation_de_nature"].get("verification_hash_pdf_original") is False,
            "RELECTURE_P52J_CERTIFICATION_INVENTEE")
    require(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
            a.get("automatic_go") is False and a.get("rates_selected") is False,
            "P52A_GARDES_ABANDONNEES")
    items=a.get("required_evidence")
    require(type(items) is list and len(items)==20 and
            [x.get("id") for x in items]==[f"F{k:02d}" for k in range(1,21)] and
            all(x.get("statut")=="NON_VALIDE" and
                x.get("preuve_independante_obtenue") is False and
                x.get("decision_autorisee") is False for x in items),
            "P52A_PREUVES_DECLAREES_ACQUISES")
    require(i.get("schema_version")=="P52I-1" and
            i.get("publication_autorisee") is False and
            i.get("fusion_autorisee") is False and
            i.get("source_revue_independante") is False and
            i.get("donnees_extraites_certifiees") is False and
            len(i.get("plan_preuves",[]))==20 and
            all(p.get("statut")=="NON_ATTESTEE" and
                p.get("piece_expertise_independante") is None for p in
                i["plan_preuves"]),
            "P52I_RENSEIGNEMENTS_FAUX")
    documents=r.get("fichiers_source")
    references=j.get("source_primaires")
    require(type(documents) is list and type(references) is list and
            len(documents)==len(references)==len(EXPECTED)==2,
            "DEUX_PDF_SOURCE_REQUIS")
    for d,ref,expected in zip(documents,references,EXPECTED):
        sid,url,tableau,page,idx=expected
        require([d.get("id"),d.get("url"),d.get("tableau"),
                 d.get("page_imprimee"),d.get("page_pdf_index_zero")] ==
                list(expected) and
                [ref.get("id"),ref.get("url"),ref.get("tableau"),
                 ref.get("page_imprimee"),ref.get("page_pdf_index_zero")]==
                list(expected), "PDF_REFERENCE_MODIFIE")
        require(d.get("source_nature")=="PDF_PUBLIC_OFFICIEL_DE_PREVISION" and
                d.get("acquisition_document_origine")=="NON_EFFECTUEE" and
                d.get("empreinte_sha256_pdf_original") is None and
                d.get("taille_octets_original") is None and
                d.get("archive_integrite_verifiee") is False and
                d.get("double_saisie_independante") is False and
                d.get("certificat_horodatage_independant") is None and
                d.get("attestation_externe_signee") is None and
                d.get("journal_chaine_conservation_externe") is None,
                "PREUVE_DOCUMENTAIRE_FICTIVE")
    jur=r.get("preuves_juridiques")
    require(type(jur) is list and len(jur)==2 and
            [x.get("id") for x in jur]==["F09","F20"],"BLOCAGES_JURIDIQUES_INCORRECTS")
    for item in jur:
        require(item.get("reference")=="P52A" and item.get("statut")=="NON_VALIDEE" and
                item.get("avis_date_signe") is None,"FAUX_AVIS_JURIDIQUE")
        require(all(value is False for key,value in item.items()
                    if key in ("expert_independant_mandate","conflit_interets_verifie",
                               "analyse_vie_privee_externe","droits_acces_et_recours_verifies")),
                "AVIS_NON_OBTENU")
    for jidx in (8,19):
        require(items[jidx].get("statut")=="NON_VALIDE","PREUVE_BLOQUANTE_INCORRECTE")
    flags=r.get("chaine_certification")
    require(type(flags) is dict and set(flags)==REQUIRED_CHAIN and
            all(v is False for v in flags.values()),
            "CERTIFICATION_FICTIVE")
    return {
        "jalon":"P52K", "schema_version":"P52K-1",
        "sources_pdf_officielles_referencees":2,
        "pdf_originaux_dont_integrite_externe_attestee":0,
        "empreintes_d_originaux_enregistrees_dans_le_registre":0,
        "preuves_P52A_independantes_manquantes":20,
        "avis_F09_et_F20_manquants":2,
        "horodatages_externes_verifies":0,
        "lecture_officielle_P52J_conservee":True,
        "attestation_budget_independante":False,
        "absence_appauvrissement_demontree":False,
        "publication_autorisee":False,
        "fusion_autorisee":False,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def empreinte_pdf(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink(),"PDF_NON_ADMISSIBLE")
    size=p.stat().st_size
    require(16<=size<=MAX_PDF_BYTES,"TAILLE_PDF_INVALIDE")
    digest=hashlib.sha256()
    with p.open("rb") as handle:
        start=handle.read(8)
        require(start.startswith(b"%PDF-"),"EN_TETE_PDF_INVALIDE")
        handle.seek(0)
        while True:
            chunk=handle.read(1024*1024)
            if not chunk:break
            digest.update(chunk)
        handle.seek(max(0,size-2048))
        tail=handle.read()
    require(b"%%EOF" in tail,"FIN_PDF_ABSENTE")
    # Detect modifications during reading to the extent a size comparison allows.
    require(p.stat().st_size==size,"FICHIER_MODIFIE_EN_COURS_DE_LECTURE")
    return size,digest.hexdigest()

def recu_local(registre,document_id,pdf_path,clock=None):
    require(type(document_id) is str and document_id in
            [p[0] for p in EXPECTED],"IDENTIFIANT_PDF_NON_PREVU")
    require(registre.get("schema_version")=="P52K-1","SCHEMA_REGISTRE_INVALIDE")
    sources=registre.get("fichiers_source",[])
    require(type(sources) is list and len(sources)==2 and
            [s.get("id") for s in sources]==[p[0] for p in EXPECTED],
            "SOURCES_NON_ATTENDUES")
    item=next(x for x in sources if x["id"]==document_id)
    expected=next(e for e in EXPECTED if e[0]==document_id)
    require(item.get("url")==expected[1] and item.get("tableau")==expected[2] and
            item.get("acquisition_document_origine")=="NON_EFFECTUEE",
            "REGISTRE_DE_PROVENANCE_NON_APPROUVE")
    size,digest=empreinte_pdf(pdf_path)
    now=clock if clock is not None else datetime.now(timezone.utc)
    require(isinstance(now,datetime) and now.tzinfo is not None,
            "HEURE_SANS_FUSEAU")
    return {
        "schema_version":"P52K-RECU-LOCAL-1",
        "id":document_id, "url_reference":expected[1],
        "taille_octets":size,"sha256_octets":digest,
        "horodatage_poste_utc_non_certifie":now.astimezone(timezone.utc).isoformat(),
        "nature_controle":"INTEGRITE_LOCALE_PAS_AUTHENTICITE_OFFICIELLE",
        "preuve_origine_officielle_etablie":False,
        "relecture_humaine_independante":False,
        "signature_externe_verifiee":False,
        "adoption_autorisee":False,
        "publication_autorisee":False,
        "fusion_autorisee":False,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def verifier_recu(recu, registre, document_id, pdf_path):
    require(type(recu) is dict and
            recu.get("schema_version")=="P52K-RECU-LOCAL-1" and
            recu.get("id")==document_id and
            recu.get("nature_controle")=="INTEGRITE_LOCALE_PAS_AUTHENTICITE_OFFICIELLE" and
            recu.get("decision")=="NO_GO_AUTOMATIQUE",
            "RECU_NON_VALIDE")
    for flag in ("preuve_origine_officielle_etablie","relecture_humaine_independante",
                 "signature_externe_verifiee","adoption_autorisee",
                 "publication_autorisee","fusion_autorisee"):
        require(recu.get(flag) is False,"FAUSSE_ATTESTATION_DANS_RECU")
    require(type(recu.get("horodatage_poste_utc_non_certifie")) is str and
            recu["horodatage_poste_utc_non_certifie"].endswith("+00:00"),
            "HORODATAGE_LOCAL_INVALIDE")
    actual=recu_local(registre,document_id,pdf_path)
    require(recu.get("url_reference")==actual["url_reference"] and
            type(recu.get("taille_octets")) is int and
            recu["taille_octets"]==actual["taille_octets"] and
            type(recu.get("sha256_octets")) is str and
            recu["sha256_octets"]==actual["sha256_octets"],
            "PDF_ET_RECU_NON_CONCORDANTS")
    return {
        "jalon":"P52K","id":document_id,
        "integrite_octets_locale":"CONCORDANTE",
        "authenticite_officielle_certifiee":False,
        "attestation_externe_obtenue":False,
        "publication_autorisee":False,
        "fusion_autorisee":False,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def ecrire_json_non_ecrasant(path,result):
    target=Path(path)
    # Never overwrite a receipt or report: independent trace of versions.
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
        f.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="action",required=True)
    audit=sub.add_parser("audit")
    for key,path in FILES.items():
        audit.add_argument("--"+key,type=Path,default=path)
    audit.add_argument("--rapport",type=Path)
    audit.add_argument("--exiger-attestation",action="store_true")
    for name in ("empreinte","verifier"):
        p=sub.add_parser(name)
        p.add_argument("--registre",type=Path,default=FILES["registre"])
        p.add_argument("--source-id",required=True)
        p.add_argument("--pdf",required=True,type=Path)
        if name=="empreinte":p.add_argument("--sortie",required=True,type=Path)
        else:p.add_argument("--recu",required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        if args.action=="audit":
            result=verifier_registre({k:json_read(getattr(args,k)) for k in FILES})
            rc=3 if args.exiger_attestation else 0
            output=args.rapport
        elif args.action=="empreinte":
            result=recu_local(json_read(args.registre),args.source_id,args.pdf)
            rc=0
            output=args.sortie
        else:
            result=verifier_recu(json_read(args.recu),json_read(args.registre),
                                 args.source_id,args.pdf)
            rc=0
            output=None
    except (OSError,ValueError,UnicodeError,TypeError,KeyError) as error:
        # Return a fail-closed report, never expose file paths or personal info.
        result={"jalon":"P52K","statut":"ERREUR_VALIDATION",
                "type_erreur":type(error).__name__,
                "publication_autorisee":False,"fusion_autorisee":False,
                "decision":"NO_GO_AUTOMATIQUE"}
        rc=2
        output=None
    if output is not None and rc!=2:
        try:
            ecrire_json_non_ecrasant(output,result)
        except (OSError,ValueError):
            return 2
    else:
        print(json.dumps(result,ensure_ascii=False,indent=2))
    return rc

if __name__=="__main__":
    sys.exit(main())
