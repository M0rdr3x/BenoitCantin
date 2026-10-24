#!/usr/bin/env python3
"""Projet Nova P52O: dependances des preuves et devis fictifs, aucun GO."""
import argparse
from datetime import date
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "plan":D/"P52O_PLAN_ACQUISITION_PREUVES.json",
 "sources":D/"P52O_SOURCES_OFFICIELLES_REPEREES.json",
 "devis":D/"P52O_SIMULATIONS_DEVIS_VIDES.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
 "p52m":D/"P52M_MANDATS_COMITES_ET_RISQUES.json",
 "p52n":D/"P52N_CAHIER_MANDATS_ET_CONSULTATION.json",
}
WAVES=[
 ("V1",("F01","F02","F03","F04","F07","F09","F19","F20")),
 ("V2",("F05","F06","F13","F14","F15")),
 ("V3",("F08","F16","F17")),
 ("V4",("F10",)),
 ("V5",("F11","F18")),
 ("V6",("F12",))
]
DEPS={
 "F01":(),"F02":(),"F03":(),"F04":(),"F07":(),"F09":(),"F19":(),"F20":(),
 "F05":("F01","F02","F07"),
 "F06":("F01","F02","F03","F07"),
 "F13":("F07","F09"),"F14":("F04","F09","F20"),
 "F15":("F02","F03","F09"),"F08":("F06","F07","F09"),
 "F16":("F04","F09","F14","F15"),"F17":("F02","F03","F15"),
 "F10":("F05","F08","F09","F13","F14","F16","F17"),
 "F11":("F05","F09","F10","F20"),"F18":("F09","F10","F16"),
 "F12":("F10","F11","F14")
}
PACKS={
 "B-JUR":("F01","F02","F03","F05","F06","F07","F19","F20"),
 "B-BUD":("F04","F09","F10","F18"),
 "B-ANT":("F06","F08"),
 "B-SOC":("F11","F12","F14"),
 "B-TRA":("F15","F16","F17"),
 "B-SUB":("F13",)
}
SRC_IDS=[f"REF{k:02d}" for k in range(1,11)]
REF_TO_PROOFS={
 "REF01":("F01","F02"),"REF02":("F03","F17"),
 "REF03":("F07","F20"),"REF04":("F01","F07"),
 "REF05":("F09","F10","F18"),"REF06":("F04","F07"),
 "REF07":("F05","F11"),"REF08":("F11",),
 "REF09":(),"REF10":()
}
SOURCE_URLS={
 "REF01":"https://laws-lois.justice.gc.ca/fra/const/section-92.html?wbdisable=true",
 "REF02":"https://www.laws-lois.justice.gc.ca/fra/lois/C-54.011/index.html",
 "REF03":"https://www.legisquebec.gouv.qc.ca/fr/document/lc/A-6.002/20260401",
 "REF04":"https://www.legisquebec.gouv.qc.ca/fr/document/lc/t-0.1/20241201",
 "REF05":"https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/index.asp",
 "REF06":"https://www150.statcan.gc.ca/n1/fr/catalogue/1010002001",
 "REF07":"https://www.statcan.gc.ca/fr/microsimulation/bdmsps/bdmsps",
 "REF08":"https://www150.statcan.gc.ca/n1/fr/catalogue/89F0002X2026001",
 "REF09":"https://www.legisquebec.gouv.qc.ca/fr/tdm/lc/c-65.1",
 "REF10":"https://www.quebec.ca/gouvernement/services-organisations-publiques/services-transformation-numerique/systeme-electronique-dappel-doffres-seao"
}
FALSE_PACK_FLAGS=("mandat_signe","financement_approuve","avis_marches_publics_si_applicable_verifie")
NULL_COSTS=(
 "jours_professionnels","taux_journalier_cad",
 "frais_acces_licence_cad","frais_controle_qualite_cad",
 "frais_de_deplacement_cad","autres_frais_et_conformite_cad",
 "provision_risque_cad","taxes_et_traitement_fiscal_cad",
 "coute_estime_total_cad"
)
ID=re.compile(r"Q-[A-Z0-9]{4,12}\Z")
MONEY=re.compile(r"(0|[1-9][0-9]{0,9})(\.[0-9]{2})\Z")
HEX=re.compile(r"[a-f0-9]{64}\Z")
ALLOWED_QUOTES={"id","lot_id","portee_sha256","preuve_devis_sha256",
                "valide_jusquau","devise","jours","tarif_journalier_cad",
                "frais_fixes_cad","provision_cad","taxes_cad","total_cad",
                "simulation_synthetique"}
MAX_INPUT=450000

def need(test,label):
 if not test:raise ValueError(label)

def read(path):
 p=Path(path)
 need(p.is_file() and not p.is_symlink() and p.stat().st_size<=MAX_INPUT,
      "SOURCE_JSON_ABSENTE_OU_INVALIDE")
 x=json.loads(p.read_text(encoding="utf-8"))
 need(type(x) is dict,"JSON_OBJET_REQUIS")
 return x

def money(v):
 need(type(v) is str and MONEY.fullmatch(v),"MONTANT_CAD_FORMAT_INVALIDE")
 try: return Decimal(v)
 except InvalidOperation as err: raise ValueError("NOMBRE_CAD_INVALIDE") from err

def reference(d):
 need(type(d) is dict and set(d)==set(FILES),"SIX_SOURCES_REQUISES")
 plan,sources,devis,a,m,n=(d[k] for k in FILES)
 need(plan.get("schema_version")=="P52O-1" and plan.get("jalon")=="P52O" and
      plan.get("statut")=="PLAN_D_ACQUISITION_NON_ENGAGE" and
      plan.get("date_reference")=="2026-10-19","PLAN_P52O_INVALIDE")
 need(plan.get("refs")=={
  "p52a":str(FILES["p52a"].relative_to(ROOT)),
  "p52m":str(FILES["p52m"].relative_to(ROOT)),
  "p52n":str(FILES["p52n"].relative_to(ROOT)),
  "sources":str(FILES["sources"].relative_to(ROOT)),
  "quotes":str(FILES["devis"].relative_to(ROOT))},"REFERENCES_INCOMPLETES")
 need(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
      a.get("automatic_go") is False and a.get("financial_model_certified") is False and
      a.get("rates_selected") is False and a.get("human_reviews_received") is False,
      "P52A_FAUSSE_DECISION")
 evid=a.get("required_evidence",[])
 need(type(evid) is list and len(evid)==20 and
      [e.get("id") for e in evid]==[f"F{i:02d}" for i in range(1,21)] and
      all(e.get("statut")=="NON_VALIDE" and
          e.get("preuve_independante_obtenue") is False and
          e.get("decision_autorisee") is False for e in evid),
      "PREUVES_P52A_FAUSSEMENT_ATTESTEES")
 need(m.get("schema_version")=="P52M-1" and
      m.get("etat_reel",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
      m["etat_reel"].get("membres_nommes")==0 and
      len(m.get("cartographie",[]))==20,"COMITES_REELLEMENT_INEXISTANTS")
 need(n.get("schema_version")=="P52N-1" and
      n.get("controles_transversaux",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
      len(n.get("mandats",[]))==20 and
      all(x.get("expert_mandate") is False for x in n["mandats"]),
      "MANDATS_FICTIFS")
 need(sources.get("schema_version")=="P52O-SOURCES-1" and
      sources.get("nature")==
         "REPERAGE_WEB_PAGES_OFFICIELLES_NON_CERTIFICATION_DES_PREUVES" and
      sources.get("source_officielle_document_archivé_certifié") is False and
      sources.get("preuve_F01_F20_obtenue") is False and
      sources.get("publication_autorisee") is False and
      sources.get("decision")=="NO_GO_AUTOMATIQUE",
      "SOURCES_FAUSSEMENT_CERTIFIEES")
 refs=sources.get("references",[])
 need(type(refs) is list and len(refs)==10 and
      [x.get("id") for x in refs]==SRC_IDS,
      "DIX_REFERENCES_REQUISES")
 for r in refs:
  ref=r["id"]
  need(r.get("url")==SOURCE_URLS[ref] and
       r.get("preuves_candidats")==list(REF_TO_PROOFS[ref]) and
       type(r.get("titre")) is str and len(r["titre"])>10 and
       type(r.get("limite")) is str and len(r["limite"])>10 and
       r.get("page_publique_reperée") is True and
       r.get("contenu_premier_niveau_consulte") is True and
       all(r.get(flag) is False for flag in
           ("piece_archivee_avec_hash","attestation_expert_independant",
            "conformite_juridique_attestee")),
       "SOURCE_PRIMAIRE_NON_VERIFIEE_INDEPENDAMMENT")
 waves=plan.get("vagues")
 need(type(waves) is list and len(waves)==6 and
      [w.get("id") for w in waves]==[v[0] for v in WAVES],
      "SIX_VAGUES_REQUISES")
 order={}
 for i,(w,official) in enumerate(zip(waves,WAVES),1):
  need(w.get("preuves")==list(official[1]) and
       type(w.get("objectif")) is str and len(w["objectif"])>=25,
       "ORDRE_PREUVES_NON_CONFORME")
  for ref in w["preuves"]:
   need(ref not in order,"PREUVE_EN_DOUBLE")
   order[ref]=i
 need(set(order)=={e["id"] for e in evid},"PREUVE_ABSENTE_DU_PLAN")
 for key,ds in DEPS.items():
  need(key in order and all(v in order and order[v]<order[key] for v in ds),
       "DEPENDANCE_NON_ANTERIEURE")
 mapped=m.get("cartographie",[])
 mandats=n.get("mandats",[])
 proofs=plan.get("preuves",[])
 need(type(proofs) is list and len(proofs)==20,
      "VINGT_PREUVES_CANDIDATES_REQUISES")
 for item,p,mm,mand in zip(proofs,evid,mapped,mandats):
  pid=p["id"]
  need(item.get("id")==pid==mm.get("id")==mand.get("id") and
       item.get("regime")==p["regime"] and
       item.get("theme")==p["theme"] and
       item.get("comite_pilote")==mm.get("comite_pilote") and
       item.get("criticite_provisoire")==mm.get("niveau_risque") and
       item.get("vague")=="V"+str(order[pid]) and
       item.get("dependances_techniques")==list(DEPS[pid]) and
       item.get("sources_preliminaires")==[
           sid for sid in SRC_IDS if pid in REF_TO_PROOFS[sid]] and
       item.get("livrable_attendu")==mand.get("livrable_minimum_candidat") and
       item.get("preuve_independante_obtenue") is False and
       item.get("cout_total_prevu_cad") is None and
       item.get("avis_professionnel_signee") is False and
       item.get("devis_reels_conformes")==0 and
       item.get("mandat_attribue") is False and
       item.get("decision")=="NO_GO",
       "CHAINE_DEPENDANCE_OU_PREUVE_TRONQUEE")
 packs=plan.get("lot_expertises")
 need(type(packs) is list and len(packs)==len(PACKS)==6 and
      [x.get("id") for x in packs]==list(PACKS),
      "LOT_MANQUANT")
 for lot in packs:
  need(lot.get("preuve_ids")==list(PACKS[lot["id"]]) and
       type(lot.get("objectif")) is str and len(lot["objectif"])>=20 and
       all(lot.get(x) is None for x in NULL_COSTS) and
       lot.get("devis_verifiables_recus")==0 and
       lot.get("devis_minimum_comparaison_candidats")==2 and
       all(lot.get(x) is False for x in FALSE_PACK_FLAGS),
       "COUT_INVENTE_OU_MANDAT_FICTIF")
 rules=plan.get("regles_acquisition",{})
 need(type(rules) is dict and
      all(rules.get(x) is False for x in (
          "budgets_monetaires_reels_obtenus","prix_du_marche_observes_dans_ce_jalon",
          "prix_a_zero_assumes","microdonnees_ou_donnees_identifiantes_dans_git")) and
      all(rules.get(x) is True for x in (
          "consultation_legale_regime_de_contrat_a_verifier",
          "obligations_SEAO_uniquement_si_organisme_assujetti",
          "prix_de_microsimulation_BDMSPS_produit_gratuit_sous_licence_signee",
          "couts_execution_et_expertise_BDMSPS_non_chiffres",
          "double_devis_prevu_non_obtenu",
          "aucune_depense_sans_financement_et_competence_legale")) and
      rules.get("devis_reels_recus")==0 and rules.get("contrats_reels_signes")==0,
      "RECRUTEMENT_OU_COUT_FAUSSEMENT_ETABLI")
 gov=plan.get("gouvernance",{})
 need(gov.get("main_techniquement_protegee") is False and
      gov.get("experts_independants_mandates")==0 and
      gov.get("preuves_certifiees")==0 and
      gov.get("variables_financieres_inconnues")==1320 and
      all(gov.get(x) is False for x in (
          "licences_de_microsimulation_obtenues","couverture_municipale_consolidee",
          "revenu_supplementaire_anti_evasion_certifie",
          "adoption_democratique_realisee","publication_autorisee",
          "fusion_autorisee","sollicitation_reelle_autorisee")) and
      gov.get("decision")=="NO_GO_AUTOMATIQUE",
      "GARANTIES_GO_DESACTIVEES")
 need(devis.get("schema_version")=="P52O-DEVIS-1" and
      devis.get("statut")=="SIMULATIONS_SYNTHETIQUES_NON_REELLES" and
      devis.get("aucun_devis_reel_obtenu") is True and
      devis.get("aucun_mandat_signe") is True and
      devis.get("financement_autorise") is False and
      devis.get("publication_autorisee") is False and
      devis.get("decision")=="NO_GO_AUTOMATIQUE",
      "DEVIS_FICTIVEMENT_AUTORISES")
 return {e["id"]:order[e["id"]] for e in evid}

def evaluer_devis(waves,quotes):
 need(type(quotes) is dict and quotes.get("schema_version")=="P52O-DEVIS-1" and
      quotes.get("statut")=="SIMULATIONS_SYNTHETIQUES_NON_REELLES" and
      quotes.get("aucun_devis_reel_obtenu") is True and
      quotes.get("aucun_mandat_signe") is True and
      quotes.get("financement_autorise") is False and
      quotes.get("publication_autorisee") is False and
      quotes.get("decision")=="NO_GO_AUTOMATIQUE",
      "DEVIS_JAMAIS_AUTORISES")
 arr=quotes.get("simulations")
 need(type(arr) is list and len(arr)<=24,"TROP_DE_DEVIS_SYNTHETIQUES")
 ids=set()
 group={}
 for q in arr:
  need(type(q) is dict and set(q)==ALLOWED_QUOTES,
       "DEVIS_CHAMPS_NON_ADMIS")
  key=q["id"]
  need(type(key) is str and ID.fullmatch(key) and key not in ids,
       "DEVIS_ID_INVALIDE")
  ids.add(key)
  pack=q["lot_id"]
  need(pack in PACKS and q["simulation_synthetique"] is True and
       q["devise"]=="CAD","DEVIS_OU_DEVISE_NON_VALIDE")
  for field in ("portee_sha256","preuve_devis_sha256"):
   need(type(q[field]) is str and HEX.fullmatch(q[field]),
        "REFERENTIEL_DEVIS_ABSENT")
  valid=q["valide_jusquau"]
  need(type(valid) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}",valid),
       "DATE_DEVIS_INVALIDE")
  try: expiry=date.fromisoformat(valid)
  except ValueError as exc: raise ValueError("DATE_DEVIS_NON_CALENDAIRE") from exc
  need(expiry>=date(2026,10,19),"DEVIS_PERIME")
  days=q["jours"]
  need(type(days) is int and 1<=days<=365,"JOURS_INCORRECTS")
  amount=money(q["tarif_journalier_cad"])
  need(amount>0,"TARIF_NUL_NON_VALABLE")
  total=amount*days
  for fee in ("frais_fixes_cad","provision_cad","taxes_cad"):
   total+=money(q[fee])
  need(total==money(q["total_cad"]),"DEVIS_SOMME_ERRONEE")
  group.setdefault(pack,[]).append(q)
 # If included, packets can only be compared with >=2 quote candidates
 for lot,records in group.items():
  need(len(records)>=2,"AU_MOINS_DEUX_DEVIS_COMPARABLES")
  need(len({r["portee_sha256"] for r in records})==1,
       "PERIMETRES_NON_COMPARABLES")
 return {
  "jalon":"P52O","schema_version":"P52O-1",
  "preuves_candidat_a_prioriser":20,"vagues_ordonnees":6,
  "lots_de_competences":6,"references_officielles_reperées_non_certifiées":10,
  "devis_synthetiques_evalues":len(arr),
  "lots_avec_comparaison_fictive":len(group),
  "offres_reelles_reçues":0,"montants_devis_reels_certifies":0,
  "experts_independants_recrutes":0,
  "preuves_independantes_certifiees":0,
  "valeurs_financieres_encore_inconnues":1320,
  "publication_autorisee":False,"fusion_autorisee":False,
  "sollicitation_autorisee":False,
  "decision":"NO_GO_AUTOMATIQUE"
 }

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 for key,path in FILES.items():parser.add_argument("--"+key,type=Path,default=path)
 parser.add_argument("--rapport",type=Path)
 parser.add_argument("--exiger-preuves",action="store_true")
 args=parser.parse_args(argv)
 try:
  src={k:read(getattr(args,k)) for k in FILES}
  ordering=reference(src)
  result=evaluer_devis(ordering,src["devis"])
  code=3 if args.exiger_preuves else 0
 except (ValueError,TypeError,UnicodeError,KeyError,OSError) as exc:
  result={"jalon":"P52O","statut":"ANOMALIE",
          "type_erreur":type(exc).__name__,
          "publication_autorisee":False,"fusion_autorisee":False,
          "sollicitation_autorisee":False,
          "decision":"NO_GO_AUTOMATIQUE"}
  code=2
 out=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
 if args.rapport:
  try:
   args.rapport.parent.mkdir(parents=True,exist_ok=True)
   with args.rapport.open("x",encoding="utf-8") as fh:fh.write(out)
  except OSError:return 2
 else:print(out,end="")
 return code

if __name__=="__main__":
 sys.exit(main())
