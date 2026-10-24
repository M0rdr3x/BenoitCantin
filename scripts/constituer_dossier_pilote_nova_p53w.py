#!/usr/bin/env python3
"""Projet Nova P53W: faits de publication et restrictions de portée."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import reconcilier_ecarts_nova_p53v as previous

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets"/"projet-nova"/"etudes"/"P53W_DOSSIER_PUBLIC_QUEBEC_RTC.json"
NO_GO="NO_GO_AUTOMATIQUE"
PAGES={
 "F01_EXERCICE_2024":("ville",0,None,"COUVERTURE"),
 "F02_RTC_SOMHAC":("ville",34,35,"NOTE_COMPTABLE"),
 "F03_CONSOLIDATION_LIGNE":("ville",34,35,"NOTE_COMPTABLE"),
 "F04_RECIPROQUES_ELIMINEES":("ville",34,35,"NOTE_COMPTABLE"),
 "F05_NOTE_NON_AUDITEE":("ville",196,197,"BUDGET_NON_AUDITE"),
 "F06_ELIMINATIONS_BUDGET":("ville",196,197,"BUDGET_NON_AUDITE"),
 "F07_RESOLUTION_CITEE":("ville",196,197,"REFERENCE_NON_AUTHENTIFIEE"),
 "F08_CATALOGUE":("catalogue",None,None,"INDEX_HTML"),
}
PROBLEMS=("ORIGINAL_ET_SHA256","COMPARAISON_VILLE_MAMH",
          "DEUX_GRANDS_LIVRES","ELIMINATIONS",
          "EMPLOIS_SERVICES","EXPERTISE_INDEPENDANTE")
VIEWS=("LECTURE_DECLAREE_NON_AUTHENTIFIEE",
       "CONTRADICTION_DECLAREE_NON_AUTHENTIFIEE",
       "RELECTURE_IMPOSSIBLE")
INPUT={"schema_version","fait_id","source_id","index_pdf",
       "appreciation","avis_expert_verifie"}
SOURCES={
 "ville":"https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf",
 "catalogue":"https://www.ville.quebec.qc.ca/apropos/profil-financier/rapport-financier.aspx",
 "mamh":"https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf",
}
FLAGS={
 "pas_de_document_original_dans_git","absence_sha256_pdf_explicite",
 "hachage_et_audit_non_simules","sources_ville_mamh_non_presumees_identiques",
 "statut_non_audite_197_non_generalise","RTC_SOMHAC_consolides_pas_economies",
 "elimination_reciproque_pas_second_gain","resolution_citee_pas_original_verifie",
 "controles_P53V_restent_non_certifies","aucun_taux_fiscal_adopte",
 "aucune_baisse_emplois_services","pas_de_fusion_automatique",
}

def require(ok,why):
    if not ok: raise ValueError(why)

def read(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink() and
            0<p.stat().st_size<=40000,"FICHIER_NON_RECEVABLE")
    data=json.loads(p.read_text("utf-8"))
    require(type(data) is dict,"FORMAT_SOURCE_INVALIDE")
    return data

def load():
    pcfg,orgs=previous.sources()
    require(len(previous.build(pcfg,orgs))==48 and
            pcfg["etat_initial"]["ecarts_transactionnels_authentifies"]==0,
            "P53V_NON_VERIFIE")
    cfg=read(CONFIG)
    require(cfg["schema_version"]=="P53W-1" and cfg["jalon"]=="P53W"
            and cfg["date_reference"]=="2026-10-24" and cfg["exercice"]==2024
            and cfg["statut"]=="CONSTATS_PUBLICS_PAGE_PAR_PAGE_SANS_AUDIT_TRANSACTIONNEL"
            and cfg["code_ville"]=="23027" and cfg["code_rtc"]=="T0088",
            "IDENTIFICATION_INCORRECTE")
    need_src={
      "ville":{"url":SOURCES["ville"],"nature":"PDF_PUBLIC_MUNICIPAL",
               "pages_pdf_observees":230,"sha256_fichier":None,
               "octets_locaux_verifies":False},
      "catalogue":{"url":SOURCES["catalogue"],"nature":"CATALOGUE_MUNICIPAL"},
      "mamh":{"url":SOURCES["mamh"],"nature":"PDF_MAMH_REPERE_NON_COMPARE",
              "sha256_fichier":None,"versions_confrontees":False},
    }
    require(cfg["sources"]==need_src,"SOURCES_NON_CONFRONTEES_MODIFIEES")
    rows=cfg["constats"]
    require(type(rows) is list and len(rows)==8 and
            [v["id"] for v in rows]==list(PAGES),"ANCRAGES_MANQUANTS")
    for r in rows:
        require(type(r) is dict
                and set(r)=={"id","source","index_pdf","page_imprimee","classe","observation"}
                and (r["source"],r["index_pdf"],r["page_imprimee"],r["classe"])==PAGES[r["id"]]
                and type(r["observation"]) is str
                and 65<=len(r["observation"])<=320,
                "FAIT_NON_CONFORME")
    problems=cfg["questions"]
    require(type(problems) is list and len(problems)==6
            and [x["id"] for x in problems]==list(PROBLEMS)
            and all(set(x)=={"id","objet","statut"}
                    and x["statut"]=="NON_RESOLUE_BLOQUANTE"
                    and type(x["objet"]) is str
                    and len(x["objet"])>=65 for x in problems),
            "QUESTIONS_TROP_FAIBLES")
    require(set(cfg["verrous"])==FLAGS
            and all(v is True for v in cfg["verrous"].values())
            and cfg["etat_initial"]=={
               "preuves_de_publication_reperees":3,"constats_avec_ancrage":8,
               "pages_pdf_distinctes":3,"questions_bloquantes":6,
               "pieces_transactionnelles_authentifiees":0,
               "bilans_comptables_apparies":0,"versions_pdf_confrontees":0,
               "avis_independants_signes":0,
               "economies_certifiees_cad":None,"decision":NO_GO},
            "GARDE_FOUS_ALTERES")
    return cfg

def declaration(d):
    require(type(d) is dict and set(d)==INPUT
            and d.get("schema_version")=="P53W-DECLARATION-1",
            "DECLARATION_NON_CONFORME")
    fid=d["fait_id"]
    require(type(fid) is str and fid in PAGES,
            "FAIT_HORS_PILOTE")
    require(d["source_id"]==PAGES[fid][0]
            and d["index_pdf"]==PAGES[fid][1],
            "PAGE_ET_SOURCE_INCORRECTES")
    require(type(d["appreciation"]) is str and d["appreciation"] in VIEWS
            and d["avis_expert_verifie"] is False,
            "CERTIFICATION_FICTIVE")
    return fid,d["appreciation"]

def reconcile(entries):
    require(len(entries)<=8,"DECLARATIONS_EXCESSIVES")
    seen=set();counts=Counter()
    for record in entries:
        fid,status=declaration(record)
        require(fid not in seen,"FAIT_DUPLIQUE")
        seen.add(fid)
        counts[status]+=1
    return {"declarations":len(seen),"statuts":dict(sorted(counts.items()))}

def report(cfg,stats):
    return {
      "schema_version":"P53W-BILAN-1","dossier":"QUEBEC_23027_RTC_T0088",
      "exercice_financier":2024,
      "publications_institutionnelles_reperees":3,
      "constats_documentaires_paginés":8,
      "pages_pdf_examinees":3,
      "sections_non_auditees_explicitement_identifiees":1,
      "precaution_consolidation_deja_effectuee":True,
      "declarations_locales_non_authentifiees":stats["declarations"],
      "statuts_declarations":stats["statuts"],
      "questions_probatoires_non_resolues":6,
      "pdf_source_octets_authentifies":0,
      "comparaisons_entre_versions_certifiees":0,
      "pieces_transactionnelles_origines_authentifiees":0,
      "appariements_bilateraux_certifies":0,
      "avis_independants_signes":0,
      "economies_certifiees_cad":None,
      "montants_Nova_inconnus":1320,
      "preuves_F01_F20_validees":0,
      "services_emplois_degrades_autorises":False,
      "fusion_autorisee":False,
      "decision":NO_GO,
    }

def create(path,obj):
    p=Path(path)
    require(not p.exists() and not p.is_symlink(),
            "ECRASEMENT_REFUSE")
    with p.open("x",encoding="utf-8") as f:
        f.write(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bilan")
    ap.add_argument("--dossier")
    ap.add_argument("--declaration",action="append",default=[])
    ap.add_argument("--exiger-gain-certifie",action="store_true")
    a=ap.parse_args(argv)
    try:
        require(len(a.declaration)<=8,"MAX_HUIT_DECLARATIONS")
        paths=[Path(x) for x in (a.bilan,a.dossier) if x]
        require(len({p.resolve() for p in paths})==len(paths)
                and all(not p.exists() and not p.is_symlink() for p in paths),
                "SORTIE_INVALIDE")
        cfg=load()
        r=report(cfg,reconcile([read(x) for x in a.declaration]))
        if a.bilan:create(a.bilan,r)
        if a.dossier:create(a.dossier,{
            "schema_version":"P53W-DOSSIER-1",
            "statut":"PREUVES_PUBLIQUES_DOCUMENTAIRES_SANS_TRANSACTION",
            "sources":cfg["sources"],"constats":cfg["constats"],
            "questions_bloquantes":cfg["questions"],
            "economies_certifiees_cad":None,"decision":NO_GO})
        print(json.dumps(r,ensure_ascii=False,sort_keys=True))
        return 3 if a.exiger_gain_certifie else 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P53W_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
