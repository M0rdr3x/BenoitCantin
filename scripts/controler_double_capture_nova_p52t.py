#!/usr/bin/env python3
"""Projet Nova P52T: deux jobs, deux captures et référence P52S; jamais de GO."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "plan":D/"P52T_PROCEDURE_DOUBLE_CAPTURE.json",
 "baseline":D/"P52S_RECEPISSES_HTTPS_OBSERVES_2026_10_20.json",
 "protocole":D/"P52S_PROTOCOLE_RECUPERATION_PDF_2026_2027.json",
 "p52k":D/"P52K_REGISTRE_PROVENANCE_BUDGET.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json"
}
IDS=("DISC2026_T3","PLAN2026_F2")
EXPECTED={
 "DISC2026_T3":("cf89d3d8d448cfa4155e2370be8226a904d393205f64962d23f45a40749acbfa",2109269),
 "PLAN2026_F2":("a0efb80f1a75984d7f0933d7dd6630bc3306e91410a8cfbaa9005e72f788e0e0",5341975)
}
SHA=re.compile(r"[a-f0-9]{64}\Z")
COMMIT=re.compile(r"[a-f0-9]{40}\Z")
RUN_FIELDS={"schema_version","role","github_run_id","github_run_attempt","github_sha",
            "github_job","runner_os","capture","publisher_signature_verified",
            "archive_permanent","reviewer_human"}
CAPTURE_FIELDS={"jalon","schema_version","mode","sources_attendues","tentatives_reseau_effectuees",
                "flux_pdf_recus_non_authentifies","sources_non_recuperees","reçus_techniques",
                "archives_officielles_certifiees","avis_independants_F09_obtenus",
                "preuves_F01_F20_validees","publication_autorisee","fusion_autorisee",
                "adoption_autorisee","decision"}
BASIC={"id","statut","sha256_octets_recus","taille_octets","date_utc_tentative",
       "categorie_echec","archive_permanente_obtenue","signature_ministerielle_verifiee"}
SUCCESS={"type_mime_recu","validation_tls_client_standard","controle_structurel_pdf_complet"}
FAIL_TYPES={"HTTPError","URLError","TimeoutError","OSError","ValueError","TypeError"}
RULES={"deux_jobs_distincts_sans_garantie_machines_distinctes","github_run_id_communs",
       "github_sha_commun","refuser_les_deux_sources_incompletes",
       "comparer_chaque_empreinte_et_taille_entre_jobs",
       "comparer_chaque_empreinte_et_taille_avec_p52s","divergence_bloque_workflow",
       "aucun_pdf_conserve_dans_git_ou_artifact",
       "deux_processus_ne_sont_pas_deux_experts_humains",
       "absence_attestation_et_signature_officielles",
       "aucune_transformation_automatique_de_F09","aucun_GO_automatique"}
def need(ok,reason):
 if not ok:raise ValueError(reason)
def read(path):
 p=Path(path)
 need(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=450000,
      "SOURCE_ABSENTE_OU_TROP_GRANDE")
 j=json.loads(p.read_text(encoding="utf-8"))
 need(type(j) is dict,"JSON_OBJET_ATTENDU")
 return j
def baseline_check(data):
 need(type(data) is dict and set(data)==set(FILES),"CINQ_FICHIERS_ATTENDUS")
 m,b,s,k,a=(data[x] for x in FILES)
 need(m.get("schema_version")=="P52T-1" and m.get("jalon")=="P52T" and
      m.get("date_reference")=="2026-10-20" and
      m.get("statut")=="DOUBLE_CAPTURE_TECHNIQUE_SANS_EXPERTISE_HUMAINE",
      "PLAN_P52T_INVALIDE")
 need(m.get("relations")=={
      "recu_p52s":str(FILES["baseline"].relative_to(ROOT)),
      "protocole_p52s":str(FILES["protocole"].relative_to(ROOT)),
      "registre_p52k":str(FILES["p52k"].relative_to(ROOT)),
      "registre_p52a":str(FILES["p52a"].relative_to(ROOT))},
      "CHEMINS_PROVENANCE_MODIFIES")
 roles=m.get("procedures",[])
 need(type(roles) is list and len(roles)==2 and
      [x.get("role") for x in roles]==["A","B"] and
      [x.get("github_job") for x in roles]==["capture-a","capture-b"] and
      all(x.get("sources")==list(IDS) and x.get("humain_independant") is False
          for x in roles),"FAUSSE_SEPARATION_DES_PERSONNES")
 controls=m.get("controles",{})
 need(type(controls) is dict and set(controls)==RULES and
      all(controls[x] is True for x in RULES),"GARDE_P52T_SUPPRIMEE")
 gov=m.get("etat",{})
 need(all(type(gov.get(z)) is int and gov[z]==0 for z in
          ("personnes_expertes_mandatees","avis_signes",
           "originaux_pdf_archives","preuves_F01_F20_certifiees")) and
      gov.get("donnees_financieres_inconnues")==1320 and
      all(gov.get(z) is False for z in
          ("fusion_autorisee","publication_autorisee","adoption_autorisee")) and
      gov.get("decision")=="NO_GO_AUTOMATIQUE","AUTORISATION_NON_PROUVEE")
 need(b.get("schema_version")=="P52S-RECU-1" and
      b.get("run_id")==39491881661 and
      b.get("run_sha")=="3e8e713183931d90dbcb4a851430a9c6b6a294d2" and
      b.get("gouvernance",{}).get("decision")=="NO_GO_AUTOMATIQUE",
      "BASELINE_P52S_NON_TRACABLE")
 src=b.get("sources")
 need(type(src) is list and len(src)==2 and
      [x.get("id") for x in src]==list(IDS),"RECU_P52S_MANQUANT")
 for obj in src:
  digest,size=EXPECTED[obj["id"]]
  need(obj.get("sha256_octets_recus")==digest and obj.get("taille_octets")==size and
       all(obj.get(f) is False for f in
           ("archivage_permanent_obtenu","preuve_independante_F09_obtenue",
            "authenticite_ministerielle_attestee")),"BASELINE_FALSIFIEE")
 need(s.get("schema_version")=="P52S-1" and
      [x.get("id") for x in s.get("sources",[])]==list(IDS) and
      all(x.get("sha256_pdf_officiel_atteste") is None for x in s["sources"]),
      "PROTOCOLE_CERTIFICATION_INVENTEE")
 need(k.get("schema_version")=="P52K-1" and
      k.get("decision")=="NO_GO_AUTOMATIQUE" and
      len(k.get("fichiers_source",[]))==2 and
      all(x.get("empreinte_sha256_pdf_original") is None and
          x.get("attestation_externe_signee") is None
          for x in k["fichiers_source"]),"ARCHIVES_NON_ATTESTEES")
 need(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
      a.get("automatic_go") is False and a.get("financial_model_certified") is False and
      [x.get("id") for x in a.get("required_evidence",[])]==
          [f"F{i:02d}" for i in range(1,21)] and
      all(x.get("statut")=="NON_VALIDE" and
          x.get("preuve_independante_obtenue") is False
          for x in a["required_evidence"]),"PREUVES_NON_VALIDEES")
 return src
def check_capture(c):
 need(type(c) is dict and set(c)==CAPTURE_FIELDS and
      c.get("schema_version")=="P52S-1" and c.get("jalon")=="P52S" and
      c.get("mode")=="sonde" and c.get("sources_attendues")==2 and
      c.get("tentatives_reseau_effectuees")==2 and
      c.get("archives_officielles_certifiees")==0 and
      c.get("avis_independants_F09_obtenus")==0 and
      c.get("preuves_F01_F20_validees")==0 and
      all(c.get(x) is False for x in
          ("publication_autorisee","fusion_autorisee","adoption_autorisee")) and
      c.get("decision")=="NO_GO_AUTOMATIQUE","CAPTURE_NON_COMPARABLE")
 rows=c.get("reçus_techniques")
 need(type(rows) is list and len(rows)==2 and
      [x.get("id") for x in rows]==list(IDS),"ORDRE_SOURCES_ERRONE")
 ok=failed=0
 for x in rows:
  need(type(x) is dict and
       x.get("archive_permanente_obtenue") is False and
       x.get("signature_ministerielle_verifiee") is False,
       "AUTHENTIFICATION_FAUSSE")
  ts=x.get("date_utc_tentative")
  need(type(ts) is str and len(ts)<=35,"HORODATAGE_ABSENT")
  try:dt=datetime.fromisoformat(ts)
  except ValueError as e:raise ValueError("HORODATAGE_INVALIDE") from e
  need(dt.tzinfo is not None and dt.utcoffset()==timezone.utc.utcoffset(dt),
       "HORODATAGE_NON_UTC")
  if x.get("statut")=="OCTETS_PDF_RECUS_HTTPS_NON_AUTHENTIFIES":
   need(set(x)==BASIC|SUCCESS and
        type(x.get("sha256_octets_recus")) is str and SHA.fullmatch(x["sha256_octets_recus"]) and
        type(x.get("taille_octets")) is int and 32<=x["taille_octets"]<=50_000_000 and
        x.get("categorie_echec") is None and
        x.get("type_mime_recu") in ("application/pdf","application/octet-stream") and
        x.get("validation_tls_client_standard") is True and
        x.get("controle_structurel_pdf_complet") is False,
        "RECU_HTTPS_MALFORME")
   ok+=1
  else:
   need(x.get("statut")=="SOURCE_NON_RECUPEREE" and
        set(x)==BASIC and x.get("sha256_octets_recus") is None and
        x.get("taille_octets") is None and x.get("categorie_echec") in FAIL_TYPES,
        "ECHEC_HTTPS_MALFORME")
   failed+=1
 need(c.get("flux_pdf_recus_non_authentifies")==ok and
      c.get("sources_non_recuperees")==failed and ok+failed==2,
      "COMPTEURS_INCOHERENTS")
 return rows
def wrap(role,capture,env):
 need(role in ("A","B"),"ROLE_INVALIDE")
 check_capture(capture)
 fields=("NOVA_RUN_ID","NOVA_RUN_ATTEMPT","NOVA_SHA","NOVA_JOB","NOVA_RUNNER_OS")
 need(type(env) is dict and all(type(env.get(k)) is str for k in fields),
      "VARIABLES_GITHUB_ABSENTES")
 try:runid=int(env["NOVA_RUN_ID"]);attempt=int(env["NOVA_RUN_ATTEMPT"])
 except ValueError as e:raise ValueError("RUN_ID_INVALIDE") from e
 sha=env["NOVA_SHA"]
 need(runid>0 and attempt>0 and COMMIT.fullmatch(sha) and
      env["NOVA_JOB"]=={"A":"capture-a","B":"capture-b"}[role] and
      env["NOVA_RUNNER_OS"]=="Linux","CONTEXTE_GITHUB_INCONNU")
 return {"schema_version":"P52T-RUN-1","role":role,
  "github_run_id":runid,"github_run_attempt":attempt,
  "github_sha":sha,"github_job":env["NOVA_JOB"],
  "runner_os":"Linux","capture":capture,
  "publisher_signature_verified":False,"archive_permanent":False,
  "reviewer_human":False}
def check_wrapper(w,role):
 need(type(w) is dict and set(w)==RUN_FIELDS and
      w.get("schema_version")=="P52T-RUN-1" and w.get("role")==role and
      w.get("github_job")=={"A":"capture-a","B":"capture-b"}[role] and
      type(w.get("github_run_id")) is int and w["github_run_id"]>0 and
      type(w.get("github_run_attempt")) is int and w["github_run_attempt"]>0 and
      type(w.get("github_sha")) is str and COMMIT.fullmatch(w["github_sha"]) and
      w.get("runner_os")=="Linux" and
      all(w.get(k) is False for k in
          ("publisher_signature_verified","archive_permanent","reviewer_human")),
      "FAUSSE_ENVELOPPE")
 return check_capture(w.get("capture"))
def compare(baseline,A,B):
 a=check_wrapper(A,"A");b=check_wrapper(B,"B")
 need(A["github_run_id"]==B["github_run_id"] and
      A["github_run_attempt"]==B["github_run_attempt"] and
      A["github_sha"]==B["github_sha"] and A["github_job"]!=B["github_job"],
      "JOBS_NON_COMPARABLES")
 need([x.get("id") for x in baseline]==list(IDS),"REFERENCE_ERRONEE")
 outcomes=[]
 for old,l,r in zip(baseline,a,b):
  need(old["id"]==l["id"]==r["id"],"SOURCES_NON_ALIGNÉES")
  if any(x["statut"]!="OCTETS_PDF_RECUS_HTTPS_NON_AUTHENTIFIES" for x in (l,r)):
   state="CAPTURE_MANQUANTE"
  elif (l["sha256_octets_recus"],l["taille_octets"])!=(
         r["sha256_octets_recus"],r["taille_octets"]):
   state="DIVERGENCE_ENTRE_TACHES"
  elif (l["sha256_octets_recus"],l["taille_octets"])!=(
         old["sha256_octets_recus"],old["taille_octets"]):
   state="DERIVE_DEPUIS_P52S"
  else:state="IDENTIQUE_3_REFERENCES"
  outcomes.append({"id":old["id"],"etat":state})
 good=all(x["etat"]=="IDENTIQUE_3_REFERENCES" for x in outcomes)
 return {"jalon":"P52T","schema_version":"P52T-1","deux_taches_distinctes":True,
         "nombre_references_comparees":2,
         "concordances_trois_references":sum(x["etat"]=="IDENTIQUE_3_REFERENCES" for x in outcomes),
         "incoherences_techniques":sum(x["etat"]!="IDENTIQUE_3_REFERENCES" for x in outcomes),
         "resultats":outcomes,"integrite_binaire_triple_confirmee":good,
         "verification_independante_humaine_obtenue":False,
         "copies_pdf_archivees_et_authentifiees":0,
         "preuves_F01_F20_attestees":0,
         "publication_autorisee":False,"fusion_autorisee":False,
         "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"}
def save_new(path,content):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8") as f:
  f.write(json.dumps(content,ensure_ascii=False,indent=2)+"\n")
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("operation",choices=("audit","envelopper","comparer"))
 for k,path in FILES.items():p.add_argument("--"+k,type=Path,default=path)
 p.add_argument("--role",choices=("A","B"));p.add_argument("--capture",type=Path)
 p.add_argument("--a",type=Path);p.add_argument("--b",type=Path)
 p.add_argument("--sortie",type=Path);p.add_argument("--rapport",type=Path)
 p.add_argument("--exiger-coherence",action="store_true")
 p.add_argument("--exiger-expertise",action="store_true")
 args=p.parse_args(argv)
 try:
  baseline=baseline_check({k:read(getattr(args,k)) for k in FILES})
  if args.operation=="audit":
   result={"jalon":"P52T","reçus_historiques":2,
           "deux_taches_distinctes":False,
           "integrite_binaire_triple_confirmee":False,
           "publication_autorisee":False,"adoption_autorisee":False,
           "decision":"NO_GO_AUTOMATIQUE"}
  elif args.operation=="envelopper":
   need(args.role and args.capture and args.sortie,"ENVELOPPE_INCOMPLETE")
   result=wrap(args.role,read(args.capture),os.environ)
  else:
   need(args.a and args.b,"REÇUS_A_ET_B_MANQUANTS")
   result=compare(baseline,read(args.a),read(args.b))
  code=3 if args.exiger_expertise else (
       4 if args.exiger_coherence and not (
        args.operation=="comparer" and result["integrite_binaire_triple_confirmee"])
       else 0)
 except (OSError,ValueError,TypeError,UnicodeError,KeyError) as e:
  diagnostic=str(e) if type(e) is ValueError and re.fullmatch(
      r"[A-Z0-9_]{4,90}",str(e)) else type(e).__name__
  result={"jalon":"P52T","statut":"CONTROLE_REJETE",
          "categorie_erreur":type(e).__name__,
          "diagnostic_controle":diagnostic,
          "publication_autorisee":False,"fusion_autorisee":False,
          "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"}
  code=2
 try:
  if args.operation=="envelopper" and args.sortie:save_new(args.sortie,result)
  elif args.rapport:save_new(args.rapport,result)
  else:print(json.dumps(result,ensure_ascii=False,indent=2))
 except OSError:return 2
 return code
if __name__=="__main__":
 sys.exit(main())
