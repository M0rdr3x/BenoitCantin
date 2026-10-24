#!/usr/bin/env python3
"""P54M — recevabilité documentaire PREPARATOIRE, jamais authentification.

Exige la chaîne P54I/J/K/L à partir de vrais octets privés et refuse toute
conversion d'une pièce hachée ou revue déclarée en preuve officielle certifiée.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import recevoir_preuves_externes_nova_p54l as upstream
import gerer_contre_revues_nova_p54f as private

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54M_MATRICE_RECEVABILITE_AUTHENTIFICATIONS_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
MANDATES=upstream.MANDATS
CASES=upstream.DOSSIERS
CATEGORIES=upstream.CATEGORIES
GATES=(
 "PORTEE_DOSSIER_MANDAT",
 "ANCRAGE_SHA_P54I_P54L",
 "ORIGINE_AUTORITE_COMPETENTE_A_CONTROLER",
 "STATUT_PERMIS_A_CONTROLER",
 "SIGNATURE_ORIGINALE_A_CONTROLER",
 "CONFLITS_INDEPENDANCE_A_EXAMINER",
 "QUATRE_CATEGORIES_DE_PREUVES",
 "CONSOLIDATION_EMPLOIS_SERVICES",
)
DECISIONS=(
 "DEMANDER_COMPLEMENT","EXAMEN_FORMEL_NON_ATTESTE",
 "IRRECEVABILITE_PROVISOIRE","SUSPENSION_DEMANDEE",
)
RESERVES=(
 "AUCUNE_DECLAREE_NON_VERIFIEE","PIECES_INCOMPLETES",
 "SIGNATURE_A_CONTROLER","STATUT_PERMIS_A_CONTROLER",
 "CONFLIT_INTERETS_A_EXAMINER","CONTRADICTION_A_INSTRUIRE",
)
STATES=(
 "NON_INSTRUIT","COMPLEMENT_DOCUMENTAIRE_REQUIS",
 "EXAMEN_FORMEL_DECLARATIF_NON_ATTESTE",
 "IRRECEVABILITE_PROVISOIRE_DECLAREE",
 "RESERVE_OUVERTE","CONTRADICTION_OUVERTE","SUSPENSION_PRIORITAIRE",
)
GUARDS={
 "aucune_attestation_automatisee","origine_officielle_non_presumee",
 "statut_professionnel_non_certifie","signature_non_authentifiee",
 "aucun_contact_autorite","aucun_engagement_professionnel",
 "aucun_document_personnel_dans_ci","identites_et_sha_prives_non_publies",
 "quatre_categories_exigees_pour_examen_formel",
 "examen_formel_non_certifiant","pas_de_dossier_clos",
 "suspensions_conservees","contradictions_conservees",
 "reserves_conservees","pas_de_double_compte_ville_rtc",
 "emplois_services_proteges","regimes_constitutionnels_separes",
 "aucun_go_automatique","main_non_fusionnee","sinjira_inchange",
}
AUTH_FLAGS=(
 "autorite_professionnelle_contactee",
 "statut_permis_officiellement_authentifie",
 "signature_officiellement_authentifiee",
 "mandat_juridiquement_valide_certifie",
 "absence_conflit_interets_certifiee",
 "avis_financier_certifie",
 "decision_institutionnelle_autorisee",
)

def need(test,message):
    if not test:raise ValueError(message)

def config():
    parent=upstream.config()
    expected={
      "schema_version":"P54M-1","date_reference":"2026-10-24",
      "exercice_source":2024,"source_jalon":"P54L",
      "ancrage_p54d_run":40120462237,
      "mandats":list(MANDATES),"dossiers":list(CASES),
      "categories_source":list(CATEGORIES),"controles":list(GATES),
      "decisions_preparatoires":list(DECISIONS),
      "reserves":list(RESERVES),"etats":list(STATES),
      "protections":{x:True for x in GUARDS},
      "etat_initial":{
        "dossiers_a_instruire":4,"positions_mandat_dossier":8,
        "controles_de_portee_par_mandat":8,
        "authentifications_officielles_realisees":0,
        "signatures_certifiees":0,"decisions_institutionnelles":0,
        "avis_originaux_authentifies":0,
        "economies_certifiees_cad":None,"decision":NO_GO,
      },
    }
    need(json.loads(CONFIG.read_text("utf-8"))==expected
         and tuple(parent["mandats"])==MANDATES
         and tuple(parent["dossiers"])==CASES,
         "P54M_CONFIGURATION_OU_REFERENCE_MODIFIEE")
    return expected

def local_template(raw_l=None):
    return {
      "schema_version":"P54M-EXAMEN-LOCAL-1",
      "exercice":2024,
      "ancrage_p54d_run":40120462237,
      "sha256_fiche_p54l":hashlib.sha256(raw_l).hexdigest()
          if raw_l is not None else "0"*64,
      "evaluations":[],
    }

def available_categories(manifest):
    """Distinct types and distinct byte digests for each required category."""
    digests={p["id"]:p["sha256"] for p in manifest["pieces"]}
    found={}
    for item in manifest["observations"]:
        if (item["piece_referencee"] is not None and
            item["qualification_declaree"]=="PIECE_LOCALE_NON_AUTHENTIFIEE"):
            key=(item["dossier_id"],item["mandat"])
            found.setdefault(key,{})[item["categorie"]]=digests[item["piece_referencee"]]
    return found

def validate_local(doc,raw_l,source_manifest,verified_l,upstream_status):
    need(type(doc) is dict and set(doc)==set(local_template()),
         "FICHE_EXAMEN_INATTENDUE")
    expected=local_template(raw_l)
    need(doc["schema_version"]==expected["schema_version"]
         and type(doc["exercice"]) is int and doc["exercice"]==2024
         and type(doc["ancrage_p54d_run"]) is int
         and doc["ancrage_p54d_run"]==40120462237
         and type(doc["sha256_fiche_p54l"]) is str
         and doc["sha256_fiche_p54l"]==expected["sha256_fiche_p54l"]
         and type(doc["evaluations"]) is list
         and len(doc["evaluations"])<=8,
         "ANCRAGE_OU_SCHEMA_P54L_INVALIDE")
    covered=available_categories(source_manifest)
    need(verified_l["observations_recues"]==len(source_manifest["observations"]),
         "SOURCE_P54L_NON_VALIDE")
    seen=set();records={}
    for row in doc["evaluations"]:
        need(type(row) is dict and set(row)=={
          "dossier_id","mandat","decision_preparatoire",
          "reserve_declaree","controles_declares",
          *AUTH_FLAGS,
        },"CHAMPS_LIBRES_OU_ACTES_REELS_NON_AUTORISES")
        case=row["dossier_id"];mandate=row["mandat"]
        key=(case,mandate)
        need(type(case) is str and case in CASES and type(mandate) is str
             and mandate in MANDATES and key not in seen,
             "DOUBLON_OU_DOSSIER_NON_RECONNU")
        seen.add(key)
        outcome=row["decision_preparatoire"]
        reason=row["reserve_declaree"]
        need(type(outcome) is str and outcome in DECISIONS
             and type(reason) is str and reason in RESERVES,
             "DECISION_OU_RESERVE_INVALIDE")
        checklist=row["controles_declares"]
        need(type(checklist) is list
             and all(type(c) is str and c in GATES for c in checklist)
             and len(set(checklist))==len(checklist),
             "CONTROLES_DUPLIQUES_OU_INCONNUS")
        need(all(row[f] is False for f in AUTH_FLAGS),
             "AUTHENTIFICATION_INSTITUTIONNELLE_FICTIVE")
        supported=covered.get(key,{})
        prior=upstream_status.get(case,"AUCUNE_PIECE_LOCALE")
        if outcome=="EXAMEN_FORMEL_NON_ATTESTE":
            need(set(checklist)==set(GATES)
                 and set(supported)==set(CATEGORIES)
                 and len(set(supported.values()))==len(CATEGORIES)
                 and reason=="AUCUNE_DECLAREE_NON_VERIFIEE"
                 and prior not in (
                    "SUSPENSION_PRIORITAIRE","CONTRADICTION_OUVERTE",
                    "RESERVE_OUVERTE"),
                 "EXAMEN_FORMEL_SANS_DOSSIER_COMPLET_OU_RESERVES")
        if outcome=="DEMANDER_COMPLEMENT":
            need(reason!="AUCUNE_DECLAREE_NON_VERIFIEE",
                 "COMPLEMENT_SANS_MOTIF")
        if outcome=="SUSPENSION_DEMANDEE":
            need(reason!="AUCUNE_DECLAREE_NON_VERIFIEE",
                 "SUSPENSION_SANS_MOTIF")
        records[key]={
          "decision_preparatoire":outcome,
          "reserve_declaree":reason,
          "categories_documentees":len(supported),
          "controles_declares":len(checklist),
        }
    return records

def matrix(data=None,upstream_status=None):
    observed=data or {}
    prior=upstream_status or {}
    rows=[];distribution={}
    for cid in CASES:
        relevant=[rec for (case,_),rec in observed.items() if case==cid]
        previous=prior.get(cid,"AUCUNE_PIECE_LOCALE")
        if previous=="SUSPENSION_PRIORITAIRE" or any(
            r["decision_preparatoire"]=="SUSPENSION_DEMANDEE" for r in relevant):
            status="SUSPENSION_PRIORITAIRE"
        elif previous=="CONTRADICTION_OUVERTE" or any(
            r["reserve_declaree"]=="CONTRADICTION_A_INSTRUIRE" for r in relevant):
            status="CONTRADICTION_OUVERTE"
        elif previous=="RESERVE_OUVERTE" or any(
            r["reserve_declaree"] in (
              "SIGNATURE_A_CONTROLER","STATUT_PERMIS_A_CONTROLER",
              "CONFLIT_INTERETS_A_EXAMINER") for r in relevant):
            status="RESERVE_OUVERTE"
        elif any(r["decision_preparatoire"]=="IRRECEVABILITE_PROVISOIRE"
                 for r in relevant):
            status="IRRECEVABILITE_PROVISOIRE_DECLAREE"
        elif any(r["decision_preparatoire"]=="DEMANDER_COMPLEMENT"
                 for r in relevant):
            status="COMPLEMENT_DOCUMENTAIRE_REQUIS"
        elif relevant and all(
              r["decision_preparatoire"]=="EXAMEN_FORMEL_NON_ATTESTE"
              for r in relevant):
            status="EXAMEN_FORMEL_DECLARATIF_NON_ATTESTE"
        else:status="NON_INSTRUIT"
        distribution[status]=distribution.get(status,0)+1
        rows.append({
          "dossier_id":cid,"recevabilite":status,
          "evaluations_preparatoires_declarees":len(relevant),
          "avis_autorite_authentifies":0,"decision_reelle_obtenue":False,
          "dossier_clos":False,
        })
    need(len(rows)==4 and sum(distribution.values())==4,
         "MATRICE_INCOMPLETE")
    return rows,dict(sorted(distribution.items()))

def report(cfg,data=None,upstream_status=None):
    rows,status=matrix(data,upstream_status)
    return {
      "schema_version":"P54M-BILAN-1",
      "exercice":2024,
      "dossiers":rows,"statuts_recevabilite":status,
      "evaluations_preparatoires_non_certifiantes":len(data or {}),
      "authentifications_officielles_executees":0,
      "verifications_permis_certifiees":0,
      "signatures_authentifiees":0,
      "avis_independants_certifies":0,
      "dossiers_clos":0,
      "controles_p54b_restants":96,
      "controles_p54c_restants":8,
      "economies_certifiees_cad":None,
      "effectifs_services_reduits_autorises":False,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def load_chain(p_i,p_j,p_k,p_l):
    sources=[private.private_file(p,32768) for p in (p_i,p_j,p_k,p_l)]
    need(len({p.resolve() for p in sources})==4,
         "SOURCES_CONFONDUES")
    (raw_i,raw_j,raw_k),reviewed,old=upstream.load_chain(
        str(sources[0]),str(sources[1]),str(sources[2]))
    raw_l=sources[3].read_bytes()
    manifest=json.loads(raw_l.decode("utf-8"))
    verified=upstream.validate_evidence(
        manifest,sources[3],raw_i,raw_j,raw_k,reviewed)
    _,states=upstream.case_matrix(verified,old)
    upstream_map={
      entry["dossier_id"]:entry["etat_p54l"]
      for entry in upstream.case_matrix(verified,old)[0]
    }
    return raw_l,manifest,verified,upstream_map

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p54i")
    parser.add_argument("--p54j")
    parser.add_argument("--p54k")
    parser.add_argument("--p54l")
    parser.add_argument("--evaluations-locales")
    parser.add_argument("--modele-prive")
    parser.add_argument("--bilan")
    parser.add_argument("--exiger-decision",action="store_true")
    args=parser.parse_args(argv)
    try:
        sources=[args.p54i,args.p54j,args.p54k,args.p54l]
        need(not any(sources) or all(sources),
             "CHAINE_COMPLETE_P54I_A_L_OBLIGATOIRE")
        need(not args.evaluations_locales or all(sources),
             "EVALUATION_REQUIERT_ORIGINAUX")
        destinations=[Path(p) for p in (args.modele_prive,args.bilan) if p]
        need(len({p.resolve() for p in destinations})==len(destinations)
             and all(not p.exists() and not p.is_symlink() for p in destinations),
             "SORTIE_NON_AUTORISEE")
        cfg=config()
        loaded=None;assessments=None;old=None
        if all(sources):
            raw_l,manifest,verified,old=load_chain(*sources)
            loaded=raw_l
            need(not any(Path(s).resolve() in {p.resolve() for p in destinations}
                         for s in sources),
                 "SOURCE_ET_SORTIE_IDENTIQUE")
        if args.evaluations_locales:
            f=private.private_file(args.evaluations_locales,32768)
            need(f.resolve() not in {Path(p).resolve() for p in sources}
                 and f.resolve() not in {p.resolve() for p in destinations},
                 "DOUBLON_ENTREES_SORTIES")
            assessments=validate_local(
                json.loads(f.read_text("utf-8")),loaded,manifest,verified,old)
        if args.modele_prive:
            private.write_new(args.modele_prive,local_template(loaded),private=True)
        results=report(cfg,assessments,old)
        if args.bilan:private.write_new(args.bilan,results)
        print(json.dumps(results,ensure_ascii=False,sort_keys=True))
        return 3 if args.exiger_decision else 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,
            json.JSONDecodeError) as err:
        print("P54M_REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
