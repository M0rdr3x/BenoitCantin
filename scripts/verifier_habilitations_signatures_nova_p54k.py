#!/usr/bin/env python3
"""P54K — préparation de contrôles humains, jamais authentification par code.

L'intégrité des octets P54I et des déclarations P54J est exigée. Même deux
déclarations de relecteurs ne prouvent pas leur identité ou indépendance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import qualifier_contradictions_avis_nova_p54j as p54j
import recevoir_mandats_et_avis_nova_p54i as p54i
import gerer_contre_revues_nova_p54f as private

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54K_VERIFICATION_HUMAINE_AVIS_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
MANDATS=p54i.MANDATS
DOSSIERS=p54i.CASES
ROLES=("VERIFICATEUR_DECLARE","CONTRE_REVISEUR_DECLARE")
CHECKS=(
 "STATUT_TABLEAU_PROFESSIONNEL_A_VERIFIER",
 "PERMIS_EXERCICE_ET_LIMITES",
 "IDENTITE_SOURCE_ORIGINALE",
 "CONTROLE_SIGNATURE_VIA_ORDRE",
 "CONSENTEMENT_MANDAT_ECRIT",
 "INDEPENDANCE_ET_CONFLITS",
 "PROVENANCE_CHAINE_SHA256",
 "CORRESPONDANCE_AVIS_ET_PORTEE",
 "RESERVES_ET_CONTRADICTIONS",
 "COLONNES_EXERCICE_UNITES",
 "CONTROLE_DOUBLE_COMPTE_RTC",
 "CONTINUITE_EMPLOIS_SERVICES",
)
PROGRESS=("NON_EXAMINE","EXAMINE_NON_ATTESTE","SUSPENDU")
ALERTS=(
 "AUCUNE_DECLAREE_NON_VERIFIEE","INSCRIPTION_A_VERIFIER",
 "SIGNATURE_A_VERIFIER","CONFLIT_POTENTIEL","CONFLIT_APPARENT",
 "CONFLIT_REEL","PIECE_ORIGINALE_MANQUANTE","PORTEE_HORS_MANDAT",
 "DESACCORD_DOCUMENTAIRE","SUSPENSION_DEMANDEE",
)
STATES=(
 "AUCUNE_REVUE_PROFESSIONNELLE",
 "REVUE_PARTIELLE_NON_AUTHENTIFIEE",
 "DEUX_REVUES_DECLAREES_NON_AUTHENTIFIEES",
 "ALERTE_VERIFICATION","RESERVE_OUVERTE",
 "CONTRADICTION_OUVERTE","SUSPENSION_PRIORITAIRE",
)
REFERENCES=[
 {"metier":"DROIT","source":"https://www.barreau.qc.ca/fr/grand-public/faire-affaire-avec-un-avocat/verification-statut-avocat/"},
 {"metier":"COMPTABILITE","source":"https://cpaquebec.ca/fr/trouver-un-cpa/tableau-de-lordre/"},
 {"metier":"DEONTOLOGIE","source":"https://cpaquebec.ca/fr/membres-cpa/deontologie/devoirs-generaux/conflit-dinterets/le-conflit-dinterets/"},
]
GUARDS={
 "aucun_controle_officiel_execute","aucune_identite_authentifiee",
 "aucune_signature_certifiee","codes_pseudonymes_non_preuves_identite",
 "controles_examines_non_attestes","relecture_distincte_declarative",
 "empreintes_privees_hors_bilan","originaux_et_avis_hors_git",
 "aucune_inference_economie","aucune_cloture_dossier",
 "reserves_p54i_j_preservees","suspension_prioritaire",
 "comptabilite_et_droit_distincts","pas_de_double_compte_ville_rtc",
 "emplois_services_maintenus","aucune_transmission_a_un_ordre",
 "aucune_decision_institutionnelle",
 "deux_scenarios_constitutionnels_separes",
 "sinjira_sans_changement","main_non_fusionnee",
}
ID=re.compile(r"^CONTROLE-[A-Z0-9]{4,12}$")
SHA=re.compile(r"^[a-f0-9]{64}$")

def need(test,reason):
    if not test:raise ValueError(reason)

def configuration():
    prior=p54j.configuration()
    expected={
      "schema_version":"P54K-1","date_reference":"2026-10-24",
      "exercice_source":2024,"chaine":["P54I","P54J"],
      "source_run_p54d":40120462237,
      "mandats":list(MANDATS),"dossiers":list(DOSSIERS),
      "roles":list(ROLES),"controles":list(CHECKS),
      "statuts_revue":list(PROGRESS),"anomalies":list(ALERTS),
      "etats_dossier":list(STATES),
      "referents_institutionnels":REFERENCES,
      "protections":{x:True for x in GUARDS},
      "etat_initial":{
        "dossiers":4,"mandats":2,"roles_possibles":16,
        "controles_de_reference":12,
        "avis_authentifies":0,"identites_professionnelles_authentifiees":0,
        "signatures_certifiees":0,"economies_certifiees_cad":None,
        "decision":NO_GO,
      },
    }
    data=json.loads(CONFIG.read_text("utf-8"))
    need(data==expected
         and tuple(prior["mandats"])==MANDATS
         and tuple(prior["dossiers"])==DOSSIERS,
         "P54K_CHAINAGE_OU_CONFIGURATION_INVALIDE")
    return data

def template(shai=None,shaj=None):
    return {
      "schema_version":"P54K-REVUE-LOCALE-1","annee":2024,
      "run_source_p54d":40120462237,
      "sha256_fiche_p54i":shai or "0"*64,
      "sha256_fiche_p54j":shaj or "0"*64,
      "declarations":[],
    }

def validate_reviews(doc,raw_i,raw_j,opinions,manifest):
    need(type(doc) is dict and set(doc)==set(template()),
         "FICHE_P54K_STRUCTURE_INVALIDE")
    need(doc["schema_version"]=="P54K-REVUE-LOCALE-1"
         and type(doc["annee"]) is int and doc["annee"]==2024
         and type(doc["run_source_p54d"]) is int
         and doc["run_source_p54d"]==40120462237
         and isinstance(doc["sha256_fiche_p54i"],str)
         and isinstance(doc["sha256_fiche_p54j"],str)
         and SHA.fullmatch(doc["sha256_fiche_p54i"])
         and SHA.fullmatch(doc["sha256_fiche_p54j"])
         and doc["sha256_fiche_p54i"]==hashlib.sha256(raw_i).hexdigest()
         and doc["sha256_fiche_p54j"]==hashlib.sha256(raw_j).hexdigest()
         and type(doc["declarations"]) is list
         and len(doc["declarations"])<=16,
         "CHAINAGE_SHA256_DES_ORIGINAUX_DECLARATIFS_ROMPU")
    receipt={r["mandat"]:r for r in manifest["receptions"]}
    by_key={}
    codes_by_key={}
    for row in doc["declarations"]:
        need(type(row) is dict and set(row)=={
          "dossier_id","mandat","role","code_opaque",
          "controles_declares","etat_declare","anomalie_declaree",
          "preuve_originale_authentifiee","statut_professionnel_certifie",
          "signature_authentifiee","independance_certifiee",
          "avis_certifie","decision_institutionnelle_autorisee",
        },"CHAMP_IDENTIFIANT_OU_PREUVE_SENSIBLE_INATTENDU")
        case=row["dossier_id"];mandate=row["mandat"];role=row["role"]
        code=row["code_opaque"]
        need(type(case) is str and case in DOSSIERS
             and type(mandate) is str and mandate in MANDATS
             and type(role) is str and role in ROLES
             and type(code) is str and ID.fullmatch(code)
             and (case,mandate,role) not in by_key,
             "ROLE_OU_REFERENT_INVALIDE_DUPLIQUE")
        opinion=opinions.get((case,mandate))
        rec=receipt.get(mandate)
        need(opinion is not None
             and opinion["conclusion_declaree"]!="AUCUNE_CONCLUSION"
             and rec is not None
             and case in rec["portee_dossiers"]
             and rec["documents"]
             and rec["nature_declaree"]=="AVIS_PROFESSIONNEL_NON_AUTHENTIFIE",
             "AVIS_LOCAL_P54I_P54J_MANQUANT_OU_HORS_CHAMP")
        controls=row["controles_declares"]
        need(type(controls) is list and len(controls)==len(set(controls))
             and all(type(x) is str and x in CHECKS for x in controls),
             "GRILLE_DECLARATIVE_INVALIDE")
        need(type(row["etat_declare"]) is str
             and row["etat_declare"] in PROGRESS
             and type(row["anomalie_declaree"]) is str
             and row["anomalie_declaree"] in ALERTS,
             "ETAT_OU_ALERTE_HORS_SCHEMA")
        if row["etat_declare"]=="EXAMINE_NON_ATTESTE":
            need(bool(controls),"EXAMEN_SANS_CONTROLE")
        if row["etat_declare"]=="SUSPENDU":
            need(row["anomalie_declaree"]=="SUSPENSION_DEMANDEE",
                 "SUSPENSION_SANS_MOTIF")
        if row["anomalie_declaree"]=="SUSPENSION_DEMANDEE":
            need(row["etat_declare"]=="SUSPENDU",
                 "MOTIF_SUSPENSION_SANS_STATUT")
        need(all(row[key] is False for key in (
           "preuve_originale_authentifiee",
           "statut_professionnel_certifie","signature_authentifiee",
           "independance_certifiee","avis_certifie",
           "decision_institutionnelle_autorisee")),
           "AUTO_AUTHENTIFICATION_OU_DECISION_INTERDITE")
        pair=(case,mandate)
        codes_by_key.setdefault(pair,set())
        need(code not in codes_by_key[pair],
             "MEME_PSEUDONYME_DOUBLE_REVUE")
        codes_by_key[pair].add(code)
        by_key[(case,mandate,role)]=row
    return by_key

def matrix(opinions,verified,receipts=None):
    reviews=verified or {}
    sources=receipts or {}
    items=[];states={}
    for cid in DOSSIERS:
        initial=sources.get(cid,"AUCUN_AVIS_LOCAL")
        entries=[row for (case,_m,_role),row in reviews.items() if case==cid]
        pair_counts={}
        for (case,mandate,role),row in reviews.items():
            if case==cid:pair_counts[mandate]=pair_counts.get(mandate,0)+1
        if initial=="SUSPENSION_MAINTENUE" or any(
             x["etat_declare"]=="SUSPENDU" for x in entries):
            status="SUSPENSION_PRIORITAIRE"
        elif initial=="CONTRADICTION_DECLAREE" or any(
             x["anomalie_declaree"]=="DESACCORD_DOCUMENTAIRE" for x in entries):
            status="CONTRADICTION_OUVERTE"
        elif initial=="RESERVE_DOCUMENTAIRE_OUVERTE":
            status="RESERVE_OUVERTE"
        elif any(x["anomalie_declaree"]!="AUCUNE_DECLAREE_NON_VERIFIEE"
                 for x in entries):
            status="ALERTE_VERIFICATION"
        elif entries and any(x["etat_declare"]=="NON_EXAMINE" for x in entries):
            status="REVUE_PARTIELLE_NON_AUTHENTIFIEE"
        elif entries and any(
             pair_counts.get(m,0)==2 for m in pair_counts):
            status="DEUX_REVUES_DECLAREES_NON_AUTHENTIFIEES"
        elif entries:status="REVUE_PARTIELLE_NON_AUTHENTIFIEE"
        else:status="AUCUNE_REVUE_PROFESSIONNELLE"
        states[status]=states.get(status,0)+1
        items.append({
          "dossier_id":cid,"etat_revue":status,
          "declarations_recues":len(entries),
          "authentification_professionnelle_obtenue":False,
          "avis_juridique_ou_comptable_certifie":False,
          "dossier_clos":False,
        })
    return items,dict(sorted(states.items()))

def public_report(cfg,opinions=None,reviewed=None,source_statuses=None):
    rows,distribution=matrix(opinions,reviewed,source_statuses)
    return {
      "schema_version":"P54K-BILAN-1","exercice":2024,
      "source_p54d_run":40120462237,
      "dossiers":rows,"etats":distribution,
      "declarations_humaines_non_attestees":len(reviewed or {}),
      "controles_reference_par_mandat":len(CHECKS),
      "postes_de_role_potentiels":16,
      "avis_professionnels_authentifies":0,
      "statuts_professionnels_certifies":0,
      "signatures_verifiees_par_ordre":0,
      "dossiers_clos":0,"avis_externes_officiels_sollicites":0,
      "controles_p54b_restants":96,
      "controles_p54c_restants":8,
      "economies_certifiees_cad":None,
      "emplois_services_reduits_autorises":False,
      "fusion_main_autorisee":False,"decision":NO_GO,
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fiche-p54i")
    parser.add_argument("--fiche-p54j")
    parser.add_argument("--revue-locale")
    parser.add_argument("--modele-prive")
    parser.add_argument("--bilan")
    parser.add_argument("--exiger-authenticite",action="store_true")
    args=parser.parse_args(argv)
    try:
        need(not args.fiche_p54j or args.fiche_p54i,
             "P54J_REQUIERT_P54I")
        need(not args.revue_locale or (args.fiche_p54i and args.fiche_p54j),
             "REVUE_REQUIERT_P54I_ET_P54J")
        outs=[Path(x) for x in (args.modele_prive,args.bilan) if x]
        need(len({x.resolve() for x in outs})==len(outs)
             and all(not x.exists() and not x.is_symlink() for x in outs),
             "SORTIE_EXISTANTE_OU_DUPLIQUEE")
        cfg=configuration()
        raw_i=None;raw_j=None;manifest=None;opinions={};source={}
        if args.fiche_p54i:
            p=private.private_file(args.fiche_p54i,32768)
            need(all(p.resolve()!=out.resolve() for out in outs),
                 "ENTREE_ECRASEE")
            raw_i=p.read_bytes()
            manifest=json.loads(raw_i.decode("utf-8"))
            checks=p54i.validate_private(manifest,p,p54i.configuration())
        else:checks=None
        if args.fiche_p54j:
            p=private.private_file(args.fiche_p54j,32768)
            need(all(p.resolve()!=out.resolve() for out in outs),
                 "ENTREE_ECRASEE")
            raw_j=p.read_bytes()
            doc=json.loads(raw_j.decode("utf-8"))
            opinions=p54j.validate_locals(doc,raw_i,manifest,checks)
        if checks is not None:
            covered={r["mandat"]:set(r["portee_dossiers"])
                     for r in manifest["receptions"]}
            _,source_status=p54j.review_grid(opinions,checks,covered)
            source={r["dossier_id"]:r["situation"]
                    for r in p54j.public_report(
                      p54j.configuration(),opinions,checks,covered)["dossiers"]}
        if args.revue_locale:
            p=private.private_file(args.revue_locale,32768)
            need(all(p.resolve()!=out.resolve() for out in outs),
                 "ENTREE_ECRASEE")
            reviewed=validate_reviews(
                json.loads(p.read_text("utf-8")),
                raw_i,raw_j,opinions,manifest)
        else:reviewed=None
        if args.modele_prive:
            m=template(hashlib.sha256(raw_i).hexdigest() if raw_i else None,
                       hashlib.sha256(raw_j).hexdigest() if raw_j else None)
            private.write_new(args.modele_prive,m,private=True)
        report=public_report(cfg,opinions,reviewed,source)
        if args.bilan:private.write_new(args.bilan,report)
        print(json.dumps(report,sort_keys=True,ensure_ascii=False))
        return 3 if args.exiger_authenticite else 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,
            json.JSONDecodeError) as e:
        print("P54K_REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
