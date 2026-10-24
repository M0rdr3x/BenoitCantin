#!/usr/bin/env python3
"""P54J : confrontation de conclusions DECLAREES, sans authentification.

Les avis juridiques et comptables ont des périmètres distincts : une différence
de formulation n'est pas considérée automatiquement comme une contradiction.
Les documents originaux, SHA privés, identités et détails restent hors Git.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import recevoir_mandats_et_avis_nova_p54i as parent
import gerer_contre_revues_nova_p54f as private

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54J_GRILLE_CONTRADICTIONS_AVIS_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
MANDATES=parent.MANDATS
CASES=parent.CASES
CHECKS=(
 "AVIS_LIE_A_FICHE_P54I","PIECE_LOCALE_SHA256_RECALCULE",
 "PORTEE_DU_MANDAT","PERIMETRE_ENTITES_CONSOLIDATION",
 "EXERCICE_2024_ET_FOLIO","UNITES_ET_CONVENTIONS_SIGNES",
 "CONFLITS_ET_INDEPENDANCE_A_AUTHENTIFIER",
 "SIGNATURE_ORIGINALE_A_AUTHENTIFIER",
 "RESERVES_ET_CONTRADICTIONS",
 "EFFETS_EMPLOIS_SERVICES_ET_RECIPROCITES",
)
FINDINGS=(
 "AUCUNE_CONCLUSION","NON_CONCLUANT",
 "DIFFERENCE_DOCUMENTAIRE_POSSIBLE",
 "COMPARABILITE_A_ETABLIR","PAS_D_ECART_DEMONTRE",
 "HORS_PORTEE_MANDAT",
)
CONTRADICTIONS=(
 "NON_SIGNALEE","DIVERGENCE_DE_PORTEE_OUVERTE",
 "QUESTION_PROBATOIRE_OUVERTE",
)
STATUSES=(
 "AUCUN_AVIS_LOCAL","AVIS_UNIQUE_DECLARATIF_NON_AUTHENTIFIE",
 "DEUX_VOLETS_NON_AUTHENTIFIES","RESERVE_DOCUMENTAIRE_OUVERTE",
 "CONTRADICTION_DECLAREE","SUSPENSION_MAINTENUE",
)
GUARDS={
 "aucune_authenticite_automatique",
 "aucune_signature_professionnelle_fictive",
 "aucun_avis_nouvellement_obtenu_par_ci",
 "fiches_privees_hors_git",
 "empreinte_fiche_p54i_sur_octets",
 "aucune_piece_utilisee_sans_validation_p54i",
 "suspension_prioritaire",
 "reserve_maintenue",
 "avis_juridique_et_comptable_non_assimiles",
 "desaccord_declare_non_efface",
 "dossier_humain_non_clos",
 "aucun_montant_public_extrait",
 "aucune_economie_certifiee",
 "maintien_emploi_et_services",
 "aucun_double_compte_ville_rtc",
 "scenarios_constitutionnels_separes",
 "aucun_merge_main",
 "aucune_intervention_sinjira",
}
REVIEW_CODE=re.compile(r"^REV-[A-Z0-9]{4,12}$")
HASH=re.compile(r"^[a-f0-9]{64}$")

def need(condition,why):
    if not condition:raise ValueError(why)

def configuration():
    cfg=json.loads(CONFIG.read_text("utf-8"))
    before=parent.configuration()
    expected={
      "schema_version":"P54J-1","date_reference":"2026-10-24",
      "exercice_source":2024,"source_jalon":"P54I",
      "source_run_p54d":40120462237,
      "mandats":list(MANDATES),"dossiers":list(CASES),
      "etats_conclusion":list(FINDINGS),
      "etats_contradiction":list(CONTRADICTIONS),
      "statuts_dossier":list(STATUSES),
      "controles_portee":list(CHECKS),
      "reserves_reprises_p54i":list(parent.RESERVES),
      "protections":{name:True for name in GUARDS},
      "etat_initial":{
        "avis_techniquement_recus":0,
        "avis_professionnels_authentifies":0,
        "revues_de_conclusion_reelles":0,
        "dossiers_a_revoir":4,
        "mandats_non_authentifies":2,
        "points_de_controle_non_attestes":20,
        "comparabilites_p54b_ouvertes":96,
        "verifications_p54c_ouvertes":8,
        "economies_certifiees_cad":None,
        "decision":NO_GO,
      }
    }
    need(cfg==expected
         and tuple(before["mandats"])==MANDATES
         and tuple(before["dossiers_source"])==CASES,
         "CONFIG_P54J_OU_CHAINAGE_MODIFIE")
    return cfg

def local_template(_cfg,source_sha256=None):
    return {
      "schema_version":"P54J-CONCLUSIONS-LOCALES-1",
      "annee":2024,"p54d_run":40120462237,
      "sha256_manifest_p54i":source_sha256 or "0"*64,
      "conclusions":[],
    }

def validate_locals(doc,manifest_blob,manifest,validated):
    need(type(doc) is dict and set(doc)=={
        "schema_version","annee","p54d_run",
        "sha256_manifest_p54i","conclusions"},
        "CHAMPS_FICHE_P54J_INVALIDES")
    need(doc["schema_version"]=="P54J-CONCLUSIONS-LOCALES-1"
         and type(doc["annee"]) is int and doc["annee"]==2024
         and type(doc["p54d_run"]) is int and doc["p54d_run"]==40120462237
         and type(doc["sha256_manifest_p54i"]) is str
         and HASH.fullmatch(doc["sha256_manifest_p54i"]) is not None
         and doc["sha256_manifest_p54i"]==
             hashlib.sha256(manifest_blob).hexdigest()
         and type(doc["conclusions"]) is list
         and len(doc["conclusions"])<=8,
         "ANCRAGE_FICHE_P54I_NON_PROUVE")
    evidence={x["mandat"]:x for x in manifest["receptions"]}
    states={x["mandat"]:x for x in validated["mandats"]}
    seen=set()
    results={}
    for row in doc["conclusions"]:
        need(type(row) is dict and set(row)=={
           "dossier_id","mandat","code_relecture",
           "conclusion_declaree","contradiction_declaree",
           "controles_declares","reserve_maintenue",
           "authenticite_professionnelle_certifiee",
           "signature_professionnelle_authentifiee",
           "economie_monetaire_certifiee",
           "decision_institutionnelle_autorisee",
        },"CHAMPS_DE_CONCLUSION_NON_AUTORISES")
        cid=row["dossier_id"];mandate=row["mandat"]
        key=(cid,mandate)
        need(type(cid) is str and cid in CASES
             and type(mandate) is str and mandate in MANDATES
             and key not in seen,
             "DOUBLON_OU_PERIMETRE_INVALIDE")
        seen.add(key)
        reviewer=row["code_relecture"]
        need(type(reviewer) is str and REVIEW_CODE.fullmatch(reviewer)
             and type(row["conclusion_declaree"]) is str
             and row["conclusion_declaree"] in FINDINGS
             and type(row["contradiction_declaree"]) is str
             and row["contradiction_declaree"] in CONTRADICTIONS,
             "CONTEXTE_OU_REVISION_INVALIDE")
        controls=row["controles_declares"]
        need(type(controls) is list and len(controls)==len(set(controls))
             and all(type(c) is str and c in CHECKS for c in controls),
             "POINTS_CONTROLE_INATTENDUS")
        need(type(row["reserve_maintenue"]) is str
             and row["reserve_maintenue"] in parent.RESERVES
             and all(row[name] is False for name in (
                "authenticite_professionnelle_certifiee",
                "signature_professionnelle_authentifiee",
                "economie_monetaire_certifiee",
                "decision_institutionnelle_autorisee")),
             "CERTIFICATION_OU_RESERVE_NON_VALIDES")
        entry=evidence.get(mandate)
        state=states.get(mandate)
        has_opinion=(entry is not None
                     and state is not None
                     and state["etat_technique"] in (
                        "FICHIER_LOCAL_INTEGRE_NON_AUTHENTIFIE",
                        "RESERVE_OUVERTE","SUSPENDU")
                     and entry["nature_declaree"]==
                         "AVIS_PROFESSIONNEL_NON_AUTHENTIFIE"
                     and bool(entry["documents"])
                     and cid in entry["portee_dossiers"])
        if row["conclusion_declaree"]!="AUCUNE_CONCLUSION":
            need(has_opinion,"CONCLUSION_SANS_AVIS_LOCAL_DE_PORTEE_CONFORME")
        # A reservation or suspension in P54I may not be silently cleared in P54J.
        if entry is not None:
            reserve=entry["reserve_declaree"]
            if reserve!="AUCUNE_DECLAREE_NON_VERIFIEE":
                need(row["reserve_maintenue"]==reserve,
                     "RESERVE_P54I_NE_PEUT_PAS_ETRE_EFFACEE")
        results[key]=row
    return results

def review_grid(observed,validated):
    indexed=observed or {}
    upstream={x["mandat"]:x for x in validated["mandats"]} if validated else {}
    items=[];distribution={}
    for cid in CASES:
        entries=[indexed[(cid,m)] for m in MANDATES if (cid,m) in indexed]
        file_states=[
           upstream.get(m,{}).get("etat_technique","FICHIER_LOCAL_NON_RECU")
           for m in MANDATES]
        kept=[r["reserve_maintenue"] for r in entries]
        explicit_conflict=any(r["contradiction_declaree"]!="NON_SIGNALEE"
                              for r in entries)
        if "SUSPENDU" in file_states or "SUSPENSION_EXPLICITE" in kept:
            status="SUSPENSION_MAINTENUE"
        elif explicit_conflict:
            status="CONTRADICTION_DECLAREE"
        elif any(s=="RESERVE_OUVERTE" for s in file_states) or any(
             v!="AUCUNE_DECLAREE_NON_VERIFIEE" for v in kept):
            status="RESERVE_DOCUMENTAIRE_OUVERTE"
        elif len(entries)==2:
            status="DEUX_VOLETS_NON_AUTHENTIFIES"
        elif len(entries)==1:
            status="AVIS_UNIQUE_DECLARATIF_NON_AUTHENTIFIE"
        else:status="AUCUN_AVIS_LOCAL"
        distribution[status]=distribution.get(status,0)+1
        items.append({
          "dossier_id":cid,"situation":status,
          "volets_avec_conclusion_declaree":len(entries),
          "authenticite_avis_confirmee":False,
          "dossier_clos":False,
          "decision_financiere_possible":False,
        })
    need(len(items)==4 and
         sum(distribution.values())==4,"BILAN_DOSSIERS_INCOMPLET")
    return items,dict(sorted(distribution.items()))

def public_report(cfg,observed=None,validated=None):
    cases,count=review_grid(observed,validated)
    return {
      "schema_version":"P54J-BILAN-1",
      "exercice":2024,"source_p54d_run":40120462237,
      "dossiers":cases,"situations":count,
      "conclusions_locales_declares":len(observed or {}),
      "avis_professionnels_authentifies":0,
      "signatures_professionnelles_verifiees":0,
      "dossiers_clos":0,
      "economies_certifiees_cad":None,
      "controles_p54b_restants":96,
      "controles_p54c_restants":8,
      "modification_regime_constitutionnel_autorisee":False,
      "emploi_services_reduits_autorises":False,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fiche-reception-p54i")
    parser.add_argument("--conclusions-locales")
    parser.add_argument("--modele-prive")
    parser.add_argument("--bilan")
    parser.add_argument("--exiger-go",action="store_true")
    opts=parser.parse_args(argv)
    try:
        need(not opts.conclusions_locales or opts.fiche_reception_p54i,
             "RECEPTION_P54I_OBLIGATOIRE")
        paths=[Path(v) for v in (opts.modele_prive,opts.bilan) if v]
        need(len({p.resolve() for p in paths})==len(paths)
             and all(not p.exists() and not p.is_symlink() for p in paths),
             "DESTINATIONS_INTERDITES")
        cfg=configuration()
        manifest=None;check=None;raw=None;observed=None
        if opts.fiche_reception_p54i:
            f=private.private_file(opts.fiche_reception_p54i,
                 parent.LIMITS["taille_manifest_octets"])
            need(all(f.resolve()!=p.resolve() for p in paths),
                 "ENTREE_ET_SORTIE_IDENTIQUES")
            raw=f.read_bytes()
            manifest=json.loads(raw.decode("utf-8"))
            check=parent.validate_private(manifest,f,parent.configuration())
        if opts.conclusions_locales:
            f=private.private_file(opts.conclusions_locales,32768)
            need(all(f.resolve()!=p.resolve() for p in paths)
                 and f.resolve()!=Path(opts.fiche_reception_p54i).resolve(),
                 "ENTREE_ET_SORTIE_IDENTIQUES")
            data=json.loads(f.read_text("utf-8"))
            observed=validate_locals(data,raw,manifest,check)
        if opts.modele_prive:
            digest=hashlib.sha256(raw).hexdigest() if raw else None
            private.write_new(opts.modele_prive,local_template(cfg,digest),
                              private=True)
        result=public_report(cfg,observed,check)
        if opts.bilan:private.write_new(opts.bilan,result)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if opts.exiger_go else 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P54J_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
