#!/usr/bin/env python3
"""Projet Nova P52M: comites, recusations et reserves, NO_GO inconditionnel."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "politique":D/"P52M_MANDATS_COMITES_ET_RISQUES.json",
 "seances":D/"P52M_SEANCES_FICTIVES_VIDES.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
 "p52l":D/"P52L_MATRICE_REVUES_INDEPENDANTES.json",
 "p52k":D/"P52K_REGISTRE_PROVENANCE_BUDGET.json"
}
COMITES={
 "CJF":("F01","F02","F03","F05","F06","F07"),
 "CFP":("F04","F08","F09","F10","F13","F18"),
 "CSD":("F11","F12","F14","F20"),
 "CTE":("F15","F16","F17"),
 "CDE":("F19",)
}
CROISES={
 "F01":("CDE",),"F02":("CTE",),"F03":("CTE",),"F04":("CSD",),
 "F05":("CSD",),"F06":("CTE",),"F07":("CFP",),"F08":("CJF",),
 "F09":("CDE",),"F10":("CSD",),"F11":("CFP",),"F12":("CFP",),
 "F13":("CSD",),"F14":("CTE",),"F15":("CFP",),"F16":("CFP","CSD"),
 "F17":("CJF",),"F18":("CSD",),"F19":("CJF",),"F20":("CJF","CDE")
}
ELEVES={"F03","F07","F13"}
SIEGES=["PRESIDENCE","RAPPORTEUR","EXPERT_METHODE","EXPERT_DROITS","MEMBRE_INDEPENDANT"]
REF=re.compile(r"A-[A-Z0-9]{3,12}\Z")
SHA=re.compile(r"[a-f0-9]{64}\Z")
SIM=re.compile(r"SIM-[0-9]{4}\Z")
RES=re.compile(r"R-[0-9]{4}\Z")
PARTICIPANT_FIELDS={"siege","acteur_ref","independance_declaree","conflit_signale","recuse","vote"}
SIM_FIELDS={"id","preuve_id","comite_id","regime","date_utc","document_sha256","deposant_ref","participants","reserves","avis_croises","orientation_declaree"}
RES_FIELDS={"id","gravite","etat","empreinte_piece","empreinte_resolution"}
AVIS_FIELDS={"comite_id","orientation","empreinte_avis"}

def require(test,why):
 if not test:raise ValueError(why)

def load(path):
 p=Path(path)
 require(p.is_file() and not p.is_symlink() and p.stat().st_size<=450000,"FICHIER_ABSENT_INVALIDE")
 obj=json.loads(p.read_text("utf-8"))
 require(type(obj) is dict,"JSON_OBJET_ATTENDU")
 return obj

def auditer_regles(data):
 require(type(data) is dict and set(data)==set(FILES),"CINQ_SOURCES_ATTENDUES")
 m,s,a,l,k=(data[key] for key in FILES)
 require(m.get("schema_version")=="P52M-1" and m.get("jalon")=="P52M" and
         m.get("statut")=="MANDATS_ET_RISQUES_PROPOSES_NON_ADOPTES" and
         m.get("date_reference")=="2026-10-19","MATRICE_INVALIDE")
 require(m.get("sources")=={
  "p52a":str(FILES["p52a"].relative_to(ROOT)),
  "p52l":str(FILES["p52l"].relative_to(ROOT)),
  "p52k":str(FILES["p52k"].relative_to(ROOT)),
  "seances":str(FILES["seances"].relative_to(ROOT))
 },"REFERENCES_NON_TRACABLES")
 require(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
         a.get("automatic_go") is False and a.get("rates_selected") is False and
         a.get("financial_model_certified") is False and
         a.get("human_reviews_received") is False,"P52A_GO_INTERDIT")
 proofs=a.get("required_evidence",[])
 require(type(proofs) is list and len(proofs)==20 and
         [x.get("id") for x in proofs]==[f"F{i:02d}" for i in range(1,21)] and
         all(x.get("priorite")=="BLOQUANT" and x.get("statut")=="NON_VALIDE" and
             x.get("preuve_independante_obtenue") is False and
             x.get("decision_autorisee") is False for x in proofs),
         "P52A_PREUVES_NON_INTACTES")
 require(l.get("schema_version")=="P52L-1" and
         l.get("politique_decision",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
         l["politique_decision"].get("attestations_P52A_obtenues")==0 and
         [x.get("id") for x in l.get("exigences",[])]==
         [x["id"] for x in proofs] and
         all(x.get("etape_canonique")=="NON_RECUE" for x in l["exigences"]),
         "P52L_VALIDATION_INVENTEE")
 require(k.get("schema_version")=="P52K-1" and k.get("decision")=="NO_GO_AUTOMATIQUE" and
         len(k.get("fichiers_source",[]))==2 and
         all(x.get("empreinte_sha256_pdf_original") is None and
             x.get("attestation_externe_signee") is None for x in k["fichiers_source"]),
         "P52K_PREUVE_INVENTEE")
 comites=m.get("comites",[])
 require(type(comites) is list and len(comites)==5 and
         [x.get("id") for x in comites]==list(COMITES),"CINQ_COMITES_REQUIS")
 for c in comites:
  require(c.get("titre") and type(c["titre"]) is str and
          c.get("preuves_pilotees")==list(COMITES[c["id"]]) and
          c.get("sieges")==SIEGES and
          c.get("quorum_simule")==3 and c.get("voix_minimum_critique")==4 and
          c.get("voix_minimum_eleve")==3 and
          c.get("majorite_qualifiee")=="DEUX_TIERS_DES_SUFFRAGES_EXPRIMES" and
          c.get("membres_reels_nommes")==0 and c.get("mandat_adopte") is False,
          "MANDAT_COMITE_MODIFIE")
 grille=m.get("grille_de_risques",{})
 require(grille.get("nature")=="TRI_QUALITATIF_PRELIMINAIRE_NON_EMPIRIQUE" and
         grille.get("dimensions")==["impact","incertitude","irreversibilite"] and
         grille.get("echelle")==[1,4] and
         grille.get("seuil_eleve")==7 and grille.get("seuil_critique")==10 and
         grille.get("tous_blocages_p52a_maintenus") is True and
         grille.get("classification_officiellement_adoptee") is False,
         "RISQUE_SANS_RESERVES")
 rows=m.get("cartographie",[])
 require(type(rows) is list and len(rows)==20,"CARTOGRAPHIE_INCOMPLETE")
 indexes={}
 for x,proof in zip(rows,proofs):
  pid=proof["id"]
  pilot=next(cid for cid,ids in COMITES.items() if pid in ids)
  impact,uncertain,irreversible=(3,3,2) if pid in ELEVES else (4,4,3)
  score=impact+uncertain+irreversible
  require(x.get("id")==pid and x.get("regime")==proof["regime"] and
          x.get("theme")==proof["theme"] and x.get("priorite_p52a")=="BLOQUANT" and
          x.get("comite_pilote")==pilot and
          x.get("comites_consultes")==list(CROISES[pid]) and
          type(x.get("impact")) is int and x["impact"]==impact and
          type(x.get("incertitude")) is int and x["incertitude"]==uncertain and
          type(x.get("irreversibilite")) is int and x["irreversibilite"]==irreversible and
          x.get("score_indicatif")==score and
          x.get("niveau_risque")==("ELEVE" if pid in ELEVES else "CRITIQUE") and
          x.get("statut_preuve")=="NON_VALIDE" and
          x.get("relecture_humaine_authentifiee") is False and
          x.get("autorisation_adoption") is False,
          "RATTACHEMENT_OU_SCORE_FALSIFIE")
  indexes[pid]=x
 flags=m.get("regles",{})
 need={"separation_deposant_et_votants","recusation_en_cas_de_conflit",
       "quorum_avec_presidence_et_rapporteur","majorite_deux_tiers",
       "avis_croises_exiges","absence_reserve_majeure_ouverte",
       "proces_verbaux_et_dissidences_exiges_hors_depot",
       "recours_humain_independant_exige","simulations_jamais_autorisation"}
 require(type(flags) is dict and set(flags)==need and all(v is True for v in flags.values()),
         "PROTECTIONS_DESACTIVEES")
 real=m.get("etat_reel",{})
 require(real.get("decision")=="NO_GO_AUTOMATIQUE" and
         all(type(real.get(k)) is int and real[k]==0 for k in
             ("comites_constitues","membres_nommes","avis_authentifies",
              "proces_verbaux_authentifies")) and
         all(real.get(k) is False for k in
             ("conflits_verifies_par_tiers","mandats_signes",
              "consultation_democratique_terminee","adoption_autorisee",
              "publication_autorisee","fusion_autorisee")),
         "FAUSSE_CONSTITUTION_DU_COMITE")
 require(s.get("schema_version")=="P52M-SIM-1" and
         s.get("jalon")=="P52M" and
         s.get("statut")=="SIMULATIONS_SANS_AUTORITE_REELLE" and
         s.get("date_reference")=="2026-10-19" and
         all(s.get(k) is False for k in
             ("avis_externes_authentifies","membres_reels_identifies",
              "publication_autorisee","adoption_autorisee")) and
         s.get("decision")=="NO_GO_AUTOMATIQUE",
         "SIMULATION_COMME_AUTORISATION")
 return indexes

def verifier_seances(indexes,journal):
 require(type(journal) is dict and journal.get("schema_version")=="P52M-SIM-1" and
         journal.get("statut")=="SIMULATIONS_SANS_AUTORITE_REELLE" and
         all(journal.get(k) is False for k in
             ("avis_externes_authentifies","membres_reels_identifies",
              "publication_autorisee","adoption_autorisee")) and
         journal.get("decision")=="NO_GO_AUTOMATIQUE",
         "JOURNAL_NON_FICTIF")
 sims=journal.get("simulations")
 require(type(sims) is list and len(sims)<=30,"SEANCES_TROP_NOMBREUSES")
 ids=set()
 last=None
 votes={"FAVORABLE":0,"DEFAVORABLE":0,"AJOURNER":0}
 recusations=0
 reserve_ouvertes=0
 for s in sims:
  require(type(s) is dict and set(s)==SIM_FIELDS,"SEANCE_CHAMPS_INATTENDUS")
  sid=s["id"]
  require(type(sid) is str and SIM.fullmatch(sid) and sid not in ids,
          "ID_SEANCE_REPETE")
  ids.add(sid)
  pid=s["preuve_id"]
  require(type(pid) is str and pid in indexes,"PREUVE_INCONNUE")
  p=indexes[pid]
  require(s["comite_id"]==p["comite_pilote"] and s["regime"]==p["regime"],
          "COMITE_OU_REGIME_ERRONE")
  when=s["date_utc"]
  require(type(when) is str and
          re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",when),
          "DATE_FORMAT_INVALIDE")
  try:dt=datetime.strptime(when,"%Y-%m-%dT%H:%M:%SZ")
  except ValueError as exc:raise ValueError("DATE_INVALIDE") from exc
  require(last is None or dt>last,"CHRONOLOGIE_INVALIDEE")
  last=dt
  require(type(s["document_sha256"]) is str and SHA.fullmatch(s["document_sha256"]),
          "DOCUMENT_SANS_EMPREINTE")
  deposant=s["deposant_ref"]
  require(type(deposant) is str and REF.fullmatch(deposant),"REF_DEPOSANT_INVALIDE")
  members=s["participants"]
  require(type(members) is list and 3<=len(members)<=5,"PARTICIPANTS_INSUFFISANTS")
  refs=set()
  seats=set()
  eligible=[]
  for item in members:
   require(type(item) is dict and set(item)==PARTICIPANT_FIELDS,
           "DONNEES_PERSONNELLES_OU_CHAMPS_NON_RECONNUS")
   seat=item["siege"]
   ref=item["acteur_ref"]
   require(seat in SIEGES and seat not in seats and
           type(ref) is str and REF.fullmatch(ref) and
           ref not in refs and ref!=deposant,"DOUBLE_VOTE_OU_DEPOSANT_VOTANT")
   refs.add(ref)
   seats.add(seat)
   require(all(type(item[k]) is bool for k in
               ("independance_declaree","conflit_signale","recuse")) and
           item["vote"] in ("POUR","CONTRE","ABSTENTION","NON_PARTICIPANT"),
           "RECUSATION_OU_VOTE_INVALIDE")
   if not item["independance_declaree"] or item["conflit_signale"]:
    require(item["recuse"] is True,"CONFLIT_SANS_RECUSATION")
   if item["recuse"]:
    require(item["vote"]=="NON_PARTICIPANT","RECUSATION_AVEC_VOTE")
    recusations+=1
   else:
    require(item["vote"]!="NON_PARTICIPANT","VOTE_SANS_DECISION")
    eligible.append(item)
  reserves=s["reserves"]
  require(type(reserves) is list and len(reserves)<=25,"TROP_DE_RESERVES")
  seen_reserves=set()
  bloquantes=0
  for r in reserves:
   require(type(r) is dict and set(r)==RES_FIELDS,"RESERVE_CHAMPS_INVALIDES")
   rid=r["id"]
   require(type(rid) is str and RES.fullmatch(rid) and rid not in seen_reserves,
           "RESERVE_DUPLIQUEE")
   seen_reserves.add(rid)
   require(r["gravite"] in ("BLOQUANTE","MAJEURE","MINEURE") and
           r["etat"] in ("OUVERTE","RESOLUTION_DECLAREE") and
           type(r["empreinte_piece"]) is str and SHA.fullmatch(r["empreinte_piece"]),
           "RESERVE_NON_DOCUMENTEE")
   if r["etat"]=="OUVERTE":
    require(r["empreinte_resolution"] is None,"RESERVE_OUVERTE_AVEC_FAUSSE_RESOLUTION")
    reserve_ouvertes+=1
    if r["gravite"] in ("BLOQUANTE","MAJEURE"):bloquantes+=1
   else:
    res=r["empreinte_resolution"]
    require(type(res) is str and SHA.fullmatch(res),"RESOLUTION_SANS_PIECE")
  notes=s["avis_croises"]
  require(type(notes) is list and len(notes)<=len(p["comites_consultes"]),
          "AVIS_CROISES_INATTENDUS")
  consulted=set()
  for n in notes:
   require(type(n) is dict and set(n)==AVIS_FIELDS,"AVIS_CROISE_INVALIDE")
   cid=n["comite_id"]
   require(cid in p["comites_consultes"] and cid not in consulted and
           n["orientation"] in ("FAVORABLE","DEFAVORABLE","RESERVES") and
           type(n["empreinte_avis"]) is str and SHA.fullmatch(n["empreinte_avis"]),
           "AVIS_INDEPENDANCE_INVALIDE")
   consulted.add(cid)
  direction=s["orientation_declaree"]
  require(direction in votes,"ORIENTATION_NON_AUTORISEE")
  yes=sum(x["vote"]=="POUR" for x in eligible)
  no=sum(x["vote"]=="CONTRE" for x in eligible)
  expressed=yes+no
  quorum=len(eligible)>=3 and {"PRESIDENCE","RAPPORTEUR"}.issubset(
      {x["siege"] for x in eligible})
  if direction=="FAVORABLE":
   minimum=4 if p["niveau_risque"]=="CRITIQUE" else 3
   require(quorum and yes>=minimum and expressed>0 and
           yes*3>=expressed*2 and bloquantes==0 and
           consulted==set(p["comites_consultes"]) and
           all(x["orientation"]=="FAVORABLE" for x in notes),
           "FAVORABLE_NON_RECEVABLE")
  elif direction=="DEFAVORABLE":
   require(quorum and no>=3 and expressed>0 and no*3>=expressed*2,
           "DEFAVORABLE_NON_RECEVABLE")
  votes[direction]+=1
 return {"jalon":"P52M","schema_version":"P52M-1",
         "comites_proposes_non_constitues":5,"preuves_bloquantes":20,
         "simulations_examinees":len(sims),
         "orientations_non_authentifiees":votes,
         "recusations_fictives":recusations,"reserves_ouvertes_fictives":reserve_ouvertes,
         "membres_reellement_nommes":0,"avis_externes_authentifies":0,
         "proces_verbaux_reels":0,"adoption_autorisee":False,
         "publication_autorisee":False,"fusion_autorisee":False,
         "decision":"NO_GO_AUTOMATIQUE"}

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 for key,path in FILES.items():parser.add_argument("--"+key,type=Path,default=path)
 parser.add_argument("--rapport",type=Path)
 parser.add_argument("--exiger-adoption",action="store_true")
 args=parser.parse_args(argv)
 try:
  data={key:load(getattr(args,key)) for key in FILES}
  idx=auditer_regles(data)
  result=verifier_seances(idx,data["seances"])
  code=3 if args.exiger_adoption else 0
 except (OSError,ValueError,TypeError,KeyError,UnicodeError) as exc:
  result={"jalon":"P52M","statut":"ERREUR_VALIDATION",
          "type_erreur":type(exc).__name__,
          "adoption_autorisee":False,"publication_autorisee":False,
          "fusion_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"}
  code=2
 blob=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
 if args.rapport:
  try:
   args.rapport.parent.mkdir(parents=True,exist_ok=True)
   with args.rapport.open("x",encoding="utf-8") as f:f.write(blob)
  except OSError:return 2
 else:print(blob,end="")
 return code

if __name__=="__main__":
 sys.exit(main())
