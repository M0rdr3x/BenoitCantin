#!/usr/bin/env python3
"""P54E: dossier opérationnel de revue; aucune authentification automatique.

Les fiches locales constituent des DECLARATIONS, jamais des attestations.
Aucun extrait de document ni jeton numérique n'est produit dans le bilan.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import verifier_observations_numeriques_nova_p54d as p54d

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"projets/projet-nova/etudes/P54E_PLAN_REVUE_HUMAINE_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
CASES=(("P54E-V-001","ville",0,102,"FIN"),
       ("P54E-M-001","mamh",1,162,"DEBUT"),
       ("P54E-M-002","mamh",3,162,"FIN"),
       ("P54E-M-003","mamh",4,162,"FIN"))
GATES=("EMPREINTE_PDF","PAGE_ET_FOLIO","CONTEXTE_DOCUMENTAIRE",
       "EXERCICE_ET_COLONNE","PORTEE_RAVQ_1435","UNITE_ET_SIGNE",
       "TABLEAU_ET_ANNEXE","CONFIDENTIALITE",
       "CONTRE_REVUE_DISTINCTE","EMPLOIS_SERVICES_ET_ELIMINATIONS")
HYP=("INDETERMINE","DATE_PROBABLE","FOLIO_PROBABLE",
     "REFERENCE_NORMATIVE_PROBABLE","IDENTIFIANT_PROBABLE",
     "VALEUR_A_EXAMINER")
STATUS=("EN_EXAMEN","DOCUMENTE_NON_ATTESTE","CONTRADICTOIRE","SUSPENDU")
GUARDS=("aucune_piece_originale_git","aucun_token_ni_contexte_brut_git",
        "aucune_attestation_automatique","revues_de_role_declaratives",
        "unite_et_perimetre_requis","aucun_gain_ville_rtc_double",
        "protections_emplois_services","scenarios_constitutionnels_separes",
        "sinjira_separe","main_non_fusionne")

def need(ok,reason):
    if not ok:raise ValueError(reason)

def config():
    obs=p54d.validate(json.loads(p54d.SOURCE.read_text("utf-8")))
    cfg=json.loads(CFG.read_text("utf-8"))
    expected={
      "schema_version":"P54E-1","date":"2026-10-24","exercice":2024,
      "source_run_p54d":40120462237,"source_artifact_p54d":12570359704,
      "cases":[{"id":cid,"source":src,"observation_index":idx,
                "pdf_index":page,"zone":zone,"classification":"INDETERMINE"}
               for cid,src,idx,page,zone in CASES],
      "gates":list(GATES),"hypotheses":list(HYP),"statuses":list(STATUS),
      "guards":{name:True for name in GUARDS},
      "initial":{"cases_unknown":4,"checkpoints_unverified":40,
                 "date_probable_not_final":1,"signed_nova_opinions":0,
                 "financial_amounts_certified":0,
                 "savings_certified_cad":None,"decision":NO_GO},
    }
    need(cfg==expected,"SCHEMA_P54E_MODIFIE")
    for c in cfg["cases"]:
        reference=obs["observations"][c["observation_index"]]
        need(reference["source"]==c["source"]
             and reference["zone_approximative"]==c["zone"]
             and reference["categorie_indicative"]=="INDETERMINE"
             and obs["pages"][c["source"]]==c["pdf_index"],
             "CAS_NON_ANCRE_DANS_P54D")
    return cfg

def baseline(cfg):
    cases=[]
    for c in cfg["cases"]:
        cases.append({
          "id":c["id"],"source":c["source"],"page_pdf_index_zero":c["pdf_index"],
          "zone_approximative":c["zone"],"observation_index_p54d":c["observation_index"],
          "classification_source":"INDETERMINE",
          "statut":"NON_EXAMINE",
          "points":[{"code":code,"preuve_verifiee":False,
                     "contre_revision_validee":False}
                    for code in GATES],
          "conclusion_comptable_certifiee":False,
          "economie_certifiee_cad":None,
        })
    need(len(cases)==4 and sum(len(x["points"]) for x in cases)==40,
         "QUATRE_DOSSIERS_ET_QUARANTE_CONTROLES_REQUIS")
    return {"schema_version":"P54E-DOSSIERS-1",
            "dossiers":cases,"decision":NO_GO}

def local_file(path):
    file=Path(path)
    need(file.is_file() and not file.is_symlink()
         and not file.resolve().is_relative_to(ROOT.resolve())
         and file.stat().st_size<=65536,
         "REVUE_LOCALE_ABSENTE_OU_DANS_DEPOT")
    return file

def review_stats(decl,cfg):
    need(type(decl) is dict and set(decl)=={
        "schema_version","source_run_p54d","sha256_copies","declarations"},
        "FICHE_REVUE_CHAMPS_INVALIDES")
    hashes={src:p54d.p54d.p54b.p54a.COPIES[src][2]
            for src in ("ville","mamh")}
    need(decl["schema_version"]=="P54E-DECLARATIONS-1"
         and type(decl["source_run_p54d"]) is int
         and decl["source_run_p54d"]==40120462237
         and decl["sha256_copies"]==hashes
         and type(decl["declarations"]) is list
         and len(decl["declarations"])<=4,
         "REVUE_SOURCE_INVALIDE")
    valid_ids={c["id"] for c in cfg["cases"]}
    seen=set()
    states=Counter()
    examined=0
    for row in decl["declarations"]:
        need(type(row) is dict and set(row)=={
            "dossier_id","hypothese","statut","controles_declares",
            "pieces_hors_git_declarees","contradiction",
            "role_examen","role_relecture",
            "avis_independant_signe_valide","decision_certifiante_autorisee"},
            "CHAMPS_LIBRES_OU_SENSIBLES_INTERDITS")
        cid=row["dossier_id"]
        need(type(cid) is str and cid in valid_ids and cid not in seen,
             "DOSSIER_INCONNU_OU_DOUBLON")
        seen.add(cid)
        need(type(row["hypothese"]) is str and row["hypothese"] in HYP
             and type(row["statut"]) is str and row["statut"] in STATUS
             and row["contradiction"] in (
               "NON_EVALUE","QUESTION_OUVERTE","EXAMEN_CONTRADICTOIRE_REQUIS"),
             "QUALIFICATION_OU_CONTRADICTION_HORS_VOCABULAIRE")
        checks=row["controles_declares"]
        need(type(checks) is list and len(checks)==len(set(checks))
             and all(type(x) is str and x in GATES for x in checks),
             "CONTROLES_INCONNUS_OU_DOUBLONS")
        n=row["pieces_hors_git_declarees"]
        need(type(n) is int and 0<=n<=20,
             "NOMBRE_PIECES_DECLAREES_INVALIDE")
        need(row["role_examen"]=="EXAMINATEUR_DECLARE"
             and row["role_relecture"]=="RELECTEUR_DISTINCT_DECLARE"
             and row["avis_independant_signe_valide"] is False
             and row["decision_certifiante_autorisee"] is False,
             "AUTO_CERTIFICATION_INTERDITE")
        if row["statut"]=="DOCUMENTE_NON_ATTESTE":
            need(len(checks)>0 and n>0,"DOCUMENTE_SANS_PIECE_DECLAREE")
        states[row["statut"]]+=1
        examined+=len(checks)
    return {"fiches_declarations":len(seen),
            "checks_declares_examines_non_attestes":examined,
            "etats_declares":dict(sorted(states.items()))}

def summary(cfg,stats=None):
    return {
      "schema_version":"P54E-RAPPORT-1","source_p54d_run":40120462237,
      "exercice":2024,
      "dossiers_a_revoir":len(cfg["cases"]),
      "points_de_revue":len(cfg["cases"])*len(GATES),
      "date_probable_p54d_non_cloturee":1,
      "declarations_locales":stats if stats is not None else {
          "fiches_declarations":0,
          "checks_declares_examines_non_attestes":0,
          "etats_declares":{}},
      "controles_effectivement_attestes":0,
      "dossiers_certifies":0,
      "controles_p54b_restant":96,"controles_p54c_restant":8,
      "avis_independants_signes":0,
      "economies_certifiees_cad":None,
      "emplois_services_reduits_autorises":False,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def write_new(path,obj):
    p=Path(path)
    need(not p.exists() and not p.is_symlink(),"SORTIE_EXISTANTE")
    with p.open("x",encoding="utf-8") as out:
        json.dump(obj,out,sort_keys=True,ensure_ascii=False,indent=2)
        out.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dossiers")
    parser.add_argument("--rapport")
    parser.add_argument("--revue-locale")
    parser.add_argument("--exiger-avis-signe",action="store_true")
    args=parser.parse_args(argv)
    try:
        outputs=[Path(x) for x in (args.dossiers,args.rapport) if x]
        need(len({x.resolve() for x in outputs})==len(outputs)
             and all(not x.exists() and not x.is_symlink() for x in outputs),
             "FICHIERS_DESTINATION_NON_DISPONIBLES")
        cfg=config()
        stats=None
        if args.revue_locale:
            source=local_file(args.revue_locale)
            need(all(source.resolve()!=x.resolve() for x in outputs),
                 "ENTREE_ET_SORTIE_IDENTIQUES")
            stats=review_stats(json.loads(source.read_text("utf-8")),cfg)
        if args.dossiers:write_new(args.dossiers,baseline(cfg))
        result=summary(cfg,stats)
        if args.rapport:write_new(args.rapport,result)
        print(json.dumps(result,sort_keys=True,ensure_ascii=False))
        return 3 if args.exiger_avis_signe else 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as err:
        print("P54E_REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
