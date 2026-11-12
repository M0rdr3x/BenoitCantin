#!/usr/bin/env python3
"""P54G — décisions de suivi procédurales, non clôturantes et non certifiantes.

Les déclarations humaines et les pièces originales restent dans un répertoire
privé. Un état P54F ou un suivi P54G n'autorise aucun GO ni montant financier.
"""
import argparse
import json
from pathlib import Path
import sys

import gerer_contre_revues_nova_p54f as p54f

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54G_REGISTRE_DECISIONS_PROCEDURALES_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
ACTIONS=("AJOURNER","DEMANDER_PIECES","DEMANDER_CONTRE_REVUE",
         "SAISIR_EXPERT_INDEPENDANT","MAINTENIR_SUSPENSION")
REASONS=("PIECES_INCOMPLETES","REVUE_UNILATERALE","DESACCORD_OUVERT",
         "EXPERTISE_MANQUANTE","CONFIDENTIALITE_OU_ACCES",
         "PERIMETRE_OU_UNITE_INDETERMINE","PREUVE_NON_CORROBOREE")
NEEDED=("PDF_PUBLIC_ORIGINAL","PAGE_ET_FOLIO","PERIMETRE_ET_PERIODE",
        "ECRITURES_RECIPROQUES","JUSTIFICATIF_ET_UNITE",
        "EVALUATION_EMPLOIS_SERVICES",
        "AVIS_JURIDIQUE_OU_COMPTABLE_INDEPENDANT")
ALLOWED={
 "EN_ATTENTE":("AJOURNER","DEMANDER_PIECES"),
 "EXAMEN_UNIQUE":("AJOURNER","DEMANDER_CONTRE_REVUE"),
 "DESACCORD":("AJOURNER","DEMANDER_PIECES","SAISIR_EXPERT_INDEPENDANT"),
 "SUSPENDU":("AJOURNER","MAINTENIR_SUSPENSION"),
 "CONCORDANCE_DECLARATIVE_INCOMPLETE":
   ("AJOURNER","DEMANDER_PIECES","DEMANDER_CONTRE_REVUE"),
 "CONCORDANCE_DECLARATIVE_DOCUMENTEE_NON_ATTESTEE":
   ("AJOURNER","SAISIR_EXPERT_INDEPENDANT"),
}
GUARDS={
 "aucune_decision_certifiante_auto","aucune_fermeture_de_dossier",
 "aucune_identite_ou_signature_authentifiee",
 "decision_humaine_declarative_uniquement","desaccord_conserve",
 "suspension_conservee","pieces_et_identites_reelles_hors_git",
 "aucun_montant_source_publique_extrait",
 "aucune_economie_certifiee","aucun_go_politique_ou_fiscal",
 "protections_emplois_services","pas_de_double_compte_ville_rtc",
 "regimes_constitutionnels_separes","sinjira_separe","aucune_fusion_main",
}

def need(ok,reason):
    if not ok:raise ValueError(reason)

def config():
    upstream=p54f.configuration()
    cfg=json.loads(CONFIG.read_text("utf-8"))
    expected={
      "schema_version":"P54G-1","exercice":2024,
      "date_reference":"2026-10-24","jalon_precedent":"P54F",
      "source_run_p54d":40120462237,
      "dossiers":upstream["dossiers"],
      "actions_de_suivi":list(ACTIONS),"motifs":list(REASONS),
      "pieces_a_demander":list(NEEDED),
      "transitions_procedurales_autorisees":
           {k:list(v) for k,v in ALLOWED.items()},
      "guardrails":{k:True for k in GUARDS},
      "etat_initial":{
        "dossiers_ouverts":4,"declarations_revue_recues":0,
        "decisions_suivi_recues":0,"desaccords_attestes":0,
        "avis_independants_signes":0,
        "decisions_definitives_authentifiees":0,
        "economies_certifiees_cad":None,"decision":NO_GO},
    }
    need(cfg==expected and len(cfg["dossiers"])==4,"SCHEMA_P54G_MODIFIE")
    return cfg

def decision_template(cfg):
    return {
      "schema_version":"P54G-DECLARATIONS-1",
      "p54d_run":40120462237,
      "sources_sha256":p54f.private_template(
          p54f.configuration())["sources_sha256"],
      "suivis":[],
    }

def empty_states(cfg):
    return [{
      "dossier_id":cid,
      "etat_procedural_source":"EN_ATTENTE",
      "roles_recus":0,"action_declaree":None,"motif_declare":None,
      "pieces_demandees_count":0,
      "exige_resolution_humaine":True,
      "dossier_clos":False,"attestation_independante":False,
    } for cid in cfg["dossiers"]]

def validate_decisions(doc,cfg,upstream):
    """The review status is derived by P54F, never accepted from input."""
    need(type(doc) is dict and set(doc)=={
      "schema_version","p54d_run","sources_sha256","suivis"},
      "FICHE_DECISION_CHAMPS_INATTENDUS")
    expected=decision_template(cfg)
    need(doc["schema_version"]==expected["schema_version"]
         and type(doc["p54d_run"]) is int
         and doc["p54d_run"]==expected["p54d_run"]
         and doc["sources_sha256"]==expected["sources_sha256"]
         and type(doc["suivis"]) is list and len(doc["suivis"])<=4,
         "SOURCE_DECISION_INVALIDE")
    by_case={r["dossier_id"]:r for r in upstream["dossiers"]}
    need(set(by_case)==set(cfg["dossiers"]),"RELECTURE_P54F_INCOMPLETE")
    seen=set();accepted={}
    for follow in doc["suivis"]:
        need(type(follow) is dict and set(follow)=={
          "dossier_id","action_suivi","motif","pieces_a_demander",
          "identite_verifiee","avis_independant_signe_verifie",
          "cloture_financiere_autorisee","transmission_externe_effectuee"},
          "SUIVI_HORS_SCHEMA")
        cid=follow["dossier_id"]
        need(type(cid) is str and cid in by_case and cid not in seen,
             "ID_SUIVI_DUPLIQUE_OU_INCONNU")
        seen.add(cid)
        state=by_case[cid]["etat_procedural"]
        action=follow["action_suivi"]
        need(type(action) is str and action in ALLOWED[state],
             "TRANSITION_SUIVI_INTERDITE")
        need(type(follow["motif"]) is str
             and follow["motif"] in REASONS,
             "MOTIF_NON_RECEVABLE")
        desired=follow["pieces_a_demander"]
        need(type(desired) is list and len(desired)<=len(NEEDED)
             and all(type(x) is str and x in NEEDED for x in desired)
             and len(set(desired))==len(desired),
             "PIECES_A_DEMANDER_HORS_VOCABULAIRE")
        if action=="DEMANDER_PIECES":
            need(bool(desired),"DEMANDE_SANS_PIECES")
        if action=="DEMANDER_CONTRE_REVUE":
            need(state in ("EXAMEN_UNIQUE",
                          "CONCORDANCE_DECLARATIVE_INCOMPLETE"),
                 "CONTRE_REVUE_SANS_BESOIN_IDENTIFIE")
        if action=="MAINTENIR_SUSPENSION":
            need(state=="SUSPENDU","SUSPENSION_NON_ATTESTEE_COMME_DECLAREE")
        need(follow["identite_verifiee"] is False
             and follow["avis_independant_signe_verifie"] is False
             and follow["cloture_financiere_autorisee"] is False
             and follow["transmission_externe_effectuee"] is False,
             "CERTIFICATION_FUSION_OU_TRANSMISSION_FICTIVE")
        accepted[cid]=follow
    rows=[];actions_count={};need_manual=0
    for source in upstream["dossiers"]:
        cid=source["dossier_id"]
        follow=accepted.get(cid)
        action=follow["action_suivi"] if follow else None
        if action:actions_count[action]=actions_count.get(action,0)+1
        state=source["etat_procedural"]
        if state in ("DESACCORD","SUSPENDU"):need_manual+=1
        rows.append({
          "dossier_id":cid,
          "etat_procedural_source":state,
          "roles_recus":source["roles_declares_recus"],
          "action_declaree":action,
          "motif_declare":follow["motif"] if follow else None,
          "pieces_demandees_count":len(follow["pieces_a_demander"])
                                  if follow else 0,
          "exige_resolution_humaine":True,
          "dossier_clos":False,
          "attestation_independante":False,
        })
    return {
      "lignes":rows,
      "suivis_declares":len(accepted),
      "actions_par_categorie":dict(sorted(actions_count.items())),
      "dossiers_en_desaccord_ou_suspendus":need_manual,
    }

def report(cfg,review=None,decisions=None):
    rows=(decisions["lignes"] if decisions is not None
          else empty_states(cfg) if review is None
          else [{
            "dossier_id":r["dossier_id"],
            "etat_procedural_source":r["etat_procedural"],
            "roles_recus":r["roles_declares_recus"],
            "action_declaree":None,"motif_declare":None,
            "pieces_demandees_count":0,
            "exige_resolution_humaine":True,
            "dossier_clos":False,"attestation_independante":False,
          } for r in review["dossiers"]])
    need(len(rows)==4 and
         {r["dossier_id"] for r in rows}==set(cfg["dossiers"]),
         "RAPPORT_DOSSIERS_INCOMPLET")
    return {
      "schema_version":"P54G-RAPPORT-1",
      "source_exercice":2024,"source_p54d_run":40120462237,
      "dossiers":rows,
      "dossiers_a_resoudre_manuellement":4,
      "declarations_P54F_recues":review["fiches_roles_recues"]
          if review else 0,
      "actions_suivi_declarees":decisions["suivis_declares"]
          if decisions else 0,
      "statuts_source_P54F":review["statuts"] if review
          else {"EN_ATTENTE":4},
      "actions_par_categorie":decisions["actions_par_categorie"]
          if decisions else {},
      "dossiers_certifies":0,
      "avis_independants_signes_authentifies":0,
      "montants_financiers_certifies":0,
      "economies_certifiees_cad":None,
      "emplois_services_reduits_autorises":False,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revues-locales")
    parser.add_argument("--decisions-locales")
    parser.add_argument("--modele-prive")
    parser.add_argument("--bilan")
    parser.add_argument("--exiger-go",action="store_true")
    args=parser.parse_args(argv)
    try:
        need(not args.decisions_locales or args.revues_locales,
             "DECISIONS_EXIGENT_REVUES_P54F")
        paths=[Path(x) for x in (args.modele_prive,args.bilan) if x]
        need(len({p.resolve() for p in paths})==len(paths)
             and all(not p.exists() and not p.is_symlink() for p in paths),
             "DESTINATION_EXISTANTE_OU_DUPLIQUEE")
        cfg=config()
        review=None;decisions=None
        if args.revues_locales:
            f=p54f.private_file(
              args.revues_locales,
              p54f.LIMITS["taille_fiche_max_octets"])
            need(all(f.resolve()!=p.resolve() for p in paths),
                 "DESTINATION_IDENTIQUE_A_REVUE")
            data=json.loads(f.read_text("utf-8"))
            review=p54f.validate_local(data,f,p54f.configuration())
        if args.decisions_locales:
            f=p54f.private_file(args.decisions_locales,32768)
            need(all(f.resolve()!=p.resolve() for p in paths),
                 "DESTINATION_IDENTIQUE_A_DECISION")
            data=json.loads(f.read_text("utf-8"))
            decisions=validate_decisions(data,cfg,review)
        result=report(cfg,review,decisions)
        if args.modele_prive:
            p54f.write_new(args.modele_prive,decision_template(cfg),private=True)
        if args.bilan:p54f.write_new(args.bilan,result)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if args.exiger_go else 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,
            json.JSONDecodeError) as e:
        print("P54G_REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
