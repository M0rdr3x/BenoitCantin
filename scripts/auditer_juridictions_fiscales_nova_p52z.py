#!/usr/bin/env python3
"""Projet Nova P52Z: contrôle de 24 hypothèses fiscales, sans certification juridique."""
import argparse
import csv
import io
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "matrice":D/"P52Z_MATRICE_FISCALITE_JURIDICTIONS.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
 "p52x":D/"P52X_PRECONDITIONS_AUTORITE_ET_CONFIDENTIALITE.json",
 "p52y":D/"P52Y_PLAN_ACTIONS_HUMAINES_ET_GITHUB.json",
 "p52v":D/"P52V_REGISTRE_MISSION_F09.json",
}
SOURCES={
 "S01":("https://laws-lois.justice.gc.ca/fra/const/section-91.html","F02","CANADA"),
 "S02":("https://laws-lois.justice.gc.ca/fra/const/section-92.html","F01","CANADA"),
 "S03":("https://laws-lois.justice.gc.ca/fra/const/section-92A.html","F01","CANADA"),
 "S04":("https://www.legisquebec.gouv.qc.ca/fr/document/lc/I-3","F01","QUEBEC"),
 "S05":("https://laws-lois.justice.gc.ca/fra/lois/I-3.3/section-2.html","F02","CANADA"),
 "S06":("https://www.legisquebec.gouv.qc.ca/fr/document/lc/T-0.1","F07","QUEBEC"),
 "S07":("https://laws-lois.justice.gc.ca/fra/lois/E-15/section-165.html","F02","CANADA"),
 "S08":("https://laws-lois.justice.gc.ca/fra/lois/C-54.011/section-20.html","F03","CANADA"),
 "S09":("https://www.legisquebec.gouv.qc.ca/fr/document/lc/F-2.1","F04","QUEBEC"),
 "S10":("https://www.legisquebec.gouv.qc.ca/fr/document/lc/I-13.3","F04","QUEBEC"),
 "S11":("https://laws-lois.justice.gc.ca/fra/lois/C-31.8/section-3.html","F19","CANADA")
}
TOPICS={
 "T01":("F01",["S02","S04"],"PROVINCIAL_REFORM_TO_VALIDATE"),
 "T02":("F02",["S01","S05"],"FEDERAL_OUTSIDE_PROVINCIAL_UNILATERAL"),
 "T03":("F07",["S02","S06"],"PROVINCIAL_REFORM_TO_VALIDATE"),
 "T04":("F02",["S01","S07"],"FEDERAL_OUTSIDE_PROVINCIAL_UNILATERAL"),
 "T05":("F06",["S02","S04","S05"],"LEGAL_QUALIFICATION_OPEN"),
 "T06":("F03",["S01","S08"],"FEDERAL_OUTSIDE_PROVINCIAL_UNILATERAL"),
 "T07":("F04",["S02","S09"],"PROVINCIAL_REFORM_TO_VALIDATE"),
 "T08":("F04",["S09","S10"],"PROVINCIAL_REFORM_TO_VALIDATE"),
 "T09":("F07",["S01","S02","S04","S05","S09","S10"],"LEGAL_QUALIFICATION_OPEN"),
 "T10":("F01",["S02","S03"],"PROVINCIAL_REFORM_TO_VALIDATE"),
 "T11":("F19",["S01","S02","S11"],"FEDERAL_OUTSIDE_PROVINCIAL_UNILATERAL"),
 "T12":("F17",["S08","S11"],"LEGAL_QUALIFICATION_OPEN")
}
CATEGORIES={
 "PROVINCIAL_REFORM_TO_VALIDATE",
 "FEDERAL_OUTSIDE_PROVINCIAL_UNILATERAL",
 "LEGAL_QUALIFICATION_OPEN",
 "TRANSITION_CONDITIONNELLE_NON_ACQUISE"
}
METHODOLOGY={
 "pages_officielles_reperees_et_relues":True,
 "absence_archives_sources_authentifiees":True,
 "citations_pas_conclusions_de_jurisprudence_exhaustives":True,
 "consultation_2026_instantanee_non_garantie_futur":True,
 "aucune_inference_sur_legislation_future":True,
 "aucun_taux_de_reforme_fixe":True,
 "aucune_preuve_F01_F20_approuvee":True
}
CONSEQUENCES={
 "K01":("IMPOT_FEDERAL","QUEBEC_DANS_CANADA"),
 "K02":("COUT_SERVICES","TOUS"),
 "K03":("PARADIS_FISCAUX","TOUS"),
 "K04":("DOUANES","QUEBEC_DANS_CANADA"),
 "K05":("TRANSITION","QUEBEC_SOUVERAIN_HYPOTHETIQUE")
}
RESULT_KEYS={"publication_autorisee","fusion_autorisee","adoption_autorisee"}

def require(condition,reason):
 if not condition:raise ValueError(reason)

def read(path):
 p=Path(path)
 require(p.is_file() and not p.is_symlink() and
         0<p.stat().st_size<=500000,"REGISTRE_ABSENT_OU_TROP_GRAND")
 data=json.loads(p.read_text(encoding="utf-8"))
 require(type(data) is dict,"JSON_OBJET_REQUIS")
 return data

def check(doc):
 require(type(doc) is dict and set(doc)==set(FILES),
         "CINQ_SOURCES_REQUISES")
 m,a,x,y,v=(doc[key] for key in FILES)
 require(m.get("schema_version")=="P52Z-1" and
         m.get("jalon")=="P52Z" and
         m.get("date_reference")=="2026-10-20" and
         m.get("statut")=="INSTRUCTION_PRIMAIRE_PROVISOIRE_NON_CERTIFIEE",
         "SCHEMA_PROVISOIRE_REQUIS")
 require(m.get("references")=={
    key:str(FILES[key].relative_to(ROOT)) for key in FILES if key!="matrice"
 }, "REFERENCES_AMONT_MODIFIEES")
 require(m.get("notes_methode")==METHODOLOGY,
         "RESERVES_SOURCES_MANQUANTES")
 require(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
         a.get("automatic_go") is False and
         a.get("financial_model_certified") is False and
         a.get("human_reviews_received") is False and
         a.get("rates_selected") is False and
         [row.get("id") for row in a.get("required_evidence",[])]==
            ["F%02d"%k for k in range(1,21)] and
         all(row.get("statut")=="NON_VALIDE" and
             row.get("preuve_independante_obtenue") is False
             for row in a["required_evidence"]),
         "P52A_INVALIDE_OU_CERTIFIE")
 require(x.get("schema_version")=="P52X-1" and
         x.get("decision_precontractuelle",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
         x["decision_precontractuelle"].get("mandant_legal_identifie") is False,
         "P52X_AUTORITE_NON_REELLE")
 require(y.get("schema_version")=="P52Y-1" and
         y.get("bilan",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
         y.get("points_non_delegables",{}).get("f09_avis_professionnel_independant_signe") is False and
         y["points_non_delegables"].get("main_protegee_via_github") is False,
         "P52Y_GOUVERNANCE_INVALIDE")
 require(v.get("schema_version")=="P52V-1" and
         v.get("audit_et_protection",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
         v.get("bilan",{}).get("expertises_independantes_signees")==0,
         "P52V_AVIS_INVENTE")
 source=m.get("sources_primaires")
 require(type(source) is list and len(source)==11 and
         [s.get("id") for s in source]==list(SOURCES),
         "ONZE_SOURCES_REQUISES")
 for s in source:
  url,prio,juridiction=SOURCES[s["id"]]
  parts=urlsplit(url)
  require(type(s) is dict and
          s.get("url")==url and
          parts.scheme=="https" and
          parts.hostname in ("laws-lois.justice.gc.ca",
                             "www.legisquebec.gouv.qc.ca") and
          s.get("f_prioritaire")==prio and
          s.get("juridiction")==juridiction and
          type(s.get("fondement")) is str and len(s["fondement"])>16 and
          type(s.get("constat_primaire")) is str and len(s["constat_primaire"])>40 and
          s.get("consultation_page_officielle")=="REPEREE_EN_LIGNE_LE_2026_10_20" and
          s.get("copie_integrale_archivee_et_hash_certifie") is False and
          s.get("avis_juridique_externe_independant_obtenu") is False and
          s.get("date_version_authentifiee_par_expert") is None,
          "SOURCE_NON_FIDÈLE_OU_CERTIFICATION_INVENTEE")
 topics=m.get("questions")
 require(type(topics) is list and len(topics)==12 and
         [x.get("id") for x in topics]==list(TOPICS),
         "DOUZE_QUESTIONS_REQUISES")
 for t in topics:
  prio,src,cls=TOPICS[t["id"]]
  require(t.get("f_prioritaire")==prio and
          t.get("sources")==src and
          type(t.get("theme")) is str and len(t["theme"])>14,
          "CORRESPONDANCE_SUJETS_SOURCES_BRISÉE")
 evaluations=m.get("evaluations")
 require(type(evaluations) is list and len(evaluations)==24,
         "VINGT_QUATRE_EVALUATIONS_REQUISES")
 for i,row in enumerate(evaluations):
  topic=list(TOPICS)[i//2]
  prio,source_ids,ccls=TOPICS[topic]
  souv=i%2==1
  expected_id=topic+("-QC-SOUV" if souv else "-QC-CA")
  expected_sources=(list(dict.fromkeys(source_ids+["S11"])) if souv
                    else source_ids)
  require(type(row) is dict and
          row.get("id")==expected_id and
          row.get("theme")==topics[i//2]["theme"] and
          row.get("scenario")==("QUEBEC_SOUVERAIN_HYPOTHETIQUE" if souv
            else "QUEBEC_DANS_CANADA") and
          row.get("f_prioritaire")==prio and
          row.get("sources")==expected_sources and
          row.get("categorie_initiale") in CATEGORIES and
          row["categorie_initiale"]==(
            "TRANSITION_CONDITIONNELLE_NON_ACQUISE" if souv else ccls) and
          type(row.get("conclusion_preliminaire")) is str and
          len(row["conclusion_preliminaire"])>=60 and
          type(row.get("travail_juridique_requis")) is str and
          len(row["travail_juridique_requis"])>=40 and
          type(row.get("risque_d_interpretation")) is str and
          len(row["risque_d_interpretation"])>=35 and
          row.get("avis_juridique_independant") is None and
          row.get("revue_humaine_signee") is False and
          row.get("acquis_sans_reserve") is False and
          row.get("conclusion_fiscale_approuvee") is False and
          row.get("statut")=="ANALYSE_PRELIMINAIRE_A_REVOIR",
          "QUALIFICATION_JURIDIQUE_EXAGEREE")
 consequences=m.get("consequences_directes")
 require(type(consequences) is list and len(consequences)==5 and
         [r.get("id") for r in consequences]==list(CONSEQUENCES),
         "CINQ_CONSEQUENCES_MANQUANTES")
 for c in consequences:
  classification,regime=CONSEQUENCES[c["id"]]
  require(c.get("nature")==classification and
          c.get("regime")==regime and
          type(c.get("constat")) is str and len(c["constat"])>50 and
          c.get("avis_externe_obtenu") is False,
          "AVIS_EXTERNE_NON_AUTHENTIFIE")
 stats=m.get("bilan",{})
 require(type(stats) is dict and
         stats.get("sources_officielles_reperes")==11 and
         stats.get("questions_de_faisabilite")==12 and
         stats.get("evaluations_comparatives")==24 and
         stats.get("conclusions_humaines_independantes")==0 and
         stats.get("preuves_F01_F20_validees")==0 and
         stats.get("montants_financiers_nova_inconnus")==1320 and
         stats.get("taux_fiscaux_fixes")==0 and
         all(stats.get(k) is False for k in RESULT_KEYS) and
         stats.get("decision")=="NO_GO_AUTOMATIQUE",
         "BILAN_FAUSSE_CERTIFICATION")
 return {
  "jalon":"P52Z","schema_version":"P52Z-1",
  "sources_primaires_reperes":len(source),
  "questions_comparees":len(topics),
  "scenarios_examens":len(evaluations),
  "pouvoirs_federaux_ineliminables_unilateralement":sum(
    1 for t in TOPICS.values()
    if t[2]=="FEDERAL_OUTSIDE_PROVINCIAL_UNILATERAL"),
  "analyses_fiscales_legalement_certifiees":0,
  "droits_souverains_reellement_acquis":0,
  "preuves_F01_F20_non_validees":20,
  "valeurs_financieres_inconnues":1320,
  "taux_fiscaux_adoptes":0,
  "publication_autorisee":False,
  "fusion_autorisee":False,
  "adoption_autorisee":False,
  "decision":"NO_GO_AUTOMATIQUE"
 }

def export_csv(m):
 buff=io.StringIO(newline="")
 writer=csv.writer(buff,lineterminator="\n")
 writer.writerow(["evaluation","scenario","f_prioritaire","sources_officielles",
                  "qualification_initiale_non_certifiee",
                  "question_au_constitutionnaliste","avis_juridique_authentique",
                  "reservation_ou_refus","date_verifiee","controleur_distinct"])
 for row in m["evaluations"]:
  writer.writerow([row["id"],row["scenario"],row["f_prioritaire"],
                   " ".join(row["sources"]),row["categorie_initiale"],
                   row["travail_juridique_requis"],"","","",""])
 return buff.getvalue()

def write_new(path,value):
 p=Path(path)
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="") as f:f.write(value)

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 for key,path in FILES.items():p.add_argument("--"+key,type=Path,default=path)
 p.add_argument("--rapport",type=Path)
 p.add_argument("--export-csv",type=Path)
 p.add_argument("--exiger-avis-juridique",action="store_true")
 args=p.parse_args(argv)
 try:
  docs={key:read(getattr(args,key)) for key in FILES}
  result=check(docs)
  if args.rapport and args.export_csv:
   require(args.rapport.resolve()!=args.export_csv.resolve(),
           "SORTIES_MEME_CHEMIN")
  if args.rapport:write_new(args.rapport,json.dumps(result,ensure_ascii=False,indent=2)+"\n")
  if args.export_csv:write_new(args.export_csv,export_csv(docs["matrice"]))
  if not args.rapport and not args.export_csv:
   print(json.dumps(result,ensure_ascii=False,indent=2))
  return 3 if args.exiger_avis_juridique else 0
 except (ValueError,OSError,TypeError,UnicodeError,KeyError) as err:
  print(json.dumps({"jalon":"P52Z","statut":"REJET_CONTROLE",
   "categorie_erreur":type(err).__name__,"publication_autorisee":False,
   "fusion_autorisee":False,"adoption_autorisee":False,
   "decision":"NO_GO_AUTOMATIQUE"},ensure_ascii=False))
  return 2

if __name__=="__main__":
 sys.exit(main())
