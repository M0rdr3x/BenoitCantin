#!/usr/bin/env python3
"""P54B : vérifier les mesures de jetons numériques observées en CI, sans audit."""
import argparse
import json
from pathlib import Path
import sys
import comparer_postes_financiers_nova_p54b as p54b

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"projets"/"projet-nova"/"etudes"/"P54B_OBSERVATIONS_NUMERIQUES_2026_10_24.json"
NO_GO="NO_GO_AUTOMATIQUE"
FLAGS={
 "recouvrement_de_jetons_pas_concordance_comptable",
 "numeros_pages_et_annees_peuvent_influencer",
 "montants_extraits_non_publies",
 "source_edition_perimetre_audit_non_certifies",
 "indice_pdf_commence_zero",
 "protection_emplois_services",
 "double_elimination_interdite",
 "scenarios_constitutionnels_non_additifs",
 "pas_de_fusion_automatique",
}
KNOWN_REPORT={"workflow_run_id":40118178035,
    "workflow_job_id":120943789111,"artifact_id":12569352928,
    "artifact_archive_sha256":"79e3f3fb2031ce5a81db8709f487785f490e275fff3a966e91be18600b8f76fc"}

def need(ok,msg):
    if not ok:raise ValueError(msg)

def check(data):
    cfg,p54a=p54b.config()
    need(type(data) is dict and set(data)=={
      "schema_version","jalon","exercice_financier","date_capture_utc",
      "workflow_run_id","workflow_job_id","artifact_id",
      "artifact_archive_sha256","phase_source_p54a_run","documents_heureux",
      "methode","lignes","resume","limites"},"FORMAT_P54B_OBSERVATION")
    need(data["schema_version"]=="P54B-OBSERVE-1"
         and data["jalon"]=="P54B"
         and data["exercice_financier"]==2024
         and data["date_capture_utc"]=="2026-10-24"
         and all(data[k]==v for k,v in KNOWN_REPORT.items())
         and data["phase_source_p54a_run"]==40116065853
         and data["methode"]=="RECROISEMENT_DE_JETONS_NUMERIQUES_NON_QUALIFIES_DICE"
         and data["limites"]=={k:True for k in FLAGS},
         "PROVENANCE_OU_LIMITES_INCOHERENTES")
    need(type(data["documents_heureux"]) is list and
         data["documents_heureux"]==[
           {"source_id":source,"sha256_copie":p54b.p54a.COPIES[source][2],
            "copie_reverifiee":True}
           for source in ("ville","mamh")],
         "HASH_ORIGINAL_NON_CONFORME")
    expected={
      (x["index_pdf_ville"],x["index_pdf_mamh"]) for x in p54b.matrix(p54a)}
    records=data["lignes"]
    need(type(records) is list and len(records)==12,"PAS_DOUZE_PAIRES")
    refs=set();high=0;weak=None;smallest=2
    for r in records:
        need(type(r) is dict and set(r)=={
         "index_pdf_ville","index_pdf_mamh","jetons_ville","jetons_mamh",
         "occurrences_communes","non_appariees_ville","non_appariees_mamh",
         "score_dice","statut"},
         "LIGNE_NON_ADMISSIBLE")
        pair=(r["index_pdf_ville"],r["index_pdf_mamh"])
        need(all(type(i) is int for i in pair) and
             pair in expected and pair not in refs,
             "APPARIEMENT_INVALID")
        refs.add(pair)
        nums=[r[key] for key in ("jetons_ville","jetons_mamh",
          "occurrences_communes","non_appariees_ville","non_appariees_mamh")]
        need(all(type(x) is int and x>=0 for x in nums)
             and nums[2]<=min(nums[0],nums[1])
             and nums[3]==nums[0]-nums[2]
             and nums[4]==nums[1]-nums[2],
             "OCCURRENCES_NON_RECONCILIEES")
        score=(round(2*nums[2]/(nums[0]+nums[1]),4)
               if nums[0]+nums[1] else None)
        need(type(r["score_dice"]) is float
             and r["score_dice"]==score
             and r["statut"]=="MESURE_NUMERIQUE_LEXICALE_NON_CERTIFIEE",
             "SCORE_OU_STATUT_NON_CONFORME")
        if score>=0.97:high+=1
        if score<smallest:
            smallest=score;weak=str(pair[0])+":"+str(pair[1])
    need(refs==expected and data["resume"]=={
      "paires_observees":12,
      "controles_qualificatifs_restants":96,
      "paires_dice_au_moins_0_97":high,
      "paire_moins_similaire":weak,
      "extraction_jetons_effectuee":True,
      "preuves_comptables_certifiees":0,
      "anomalies_financieres_demontrees":0,
      "economies_certifiees_cad":None,
      "decision":NO_GO},
      "RESULTAT_AGREGE_OU_RESERVES_ERRONEES")
    return data

def report(data):
    result=check(data)
    return {
     "schema_version":"P54B-CONTROLE-RESULTAT-1",
     "source_run":result["workflow_run_id"],
     "paires_numériques_observees":12,
     "paires_recouvrement_au_moins_97_pourcent":
       result["resume"]["paires_dice_au_moins_0_97"],
     "paires_a_revoir_en_priorite":1,
     "controles_comptables_toujours_requis":96,
     "montants_certifies":0,
     "economies_certifiees_cad":None,
     "decision":NO_GO,
    }

def main(args=None):
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--bilan")
    a.add_argument("--exiger-certification",action="store_true")
    opts=a.parse_args(args)
    try:
        obj=json.loads(SOURCE.read_text("utf-8"))
        result=report(obj)
        if opts.bilan:
            p=Path(opts.bilan)
            need(not p.exists() and not p.is_symlink(),"SORTIE_EXISTANTE")
            with p.open("x",encoding="utf-8") as f:
                json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2)
                f.write("\n")
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if opts.exiger_certification else 0
    except (OSError,ValueError,TypeError,KeyError,
            UnicodeError,json.JSONDecodeError) as e:
        print("P54B_REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
