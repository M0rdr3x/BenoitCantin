#!/usr/bin/env python3
"""P54L : réception technique de pièces externes DECLAREES, non certifiantes.

Le fichier local peut être haché, mais ni l'auteur, ni la signature, ni la
qualité d'un professionnel ne peuvent être authentifiés par ce programme.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import verifier_habilitations_signatures_nova_p54k as p54k
import gerer_contre_revues_nova_p54f as private

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54L_PREUVES_EXTERNES_A_AUTHENTIFIER_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
MANDATS=p54k.MANDATS
DOSSIERS=p54k.DOSSIERS
CATEGORIES=("TABLEAU_PROFESSIONNEL","AUTHENTICITE_SIGNATURE",
            "CONFLITS_D_INTERETS","VALIDITE_MANDAT")
QUALIFS=("A_VERIFIER","PIECE_LOCALE_NON_AUTHENTIFIEE",
         "RESERVE_EXPLICITE","SUSPENSION_EXPLICITE")
STATES=("AUCUNE_PIECE_LOCALE","PIECES_LOCALES_A_AUTHENTIFIER",
        "RESERVE_OUVERTE","CONTRADICTION_OUVERTE",
        "SUSPENSION_PRIORITAIRE")
LIMITS={"taille_fiche_octets":32768,"nombre_pieces":12,
        "nombre_observations":16}
GUARDS={
 "ne_jamais_inferer_une_authentification_des_octets",
 "aucune_consultation_ordre_professionnel_effectuee",
 "aucun_professionnel_contacte_par_ci",
 "aucune_signature_certifiee","aucun_permis_authentifie",
 "aucun_conflit_legalement_resolu",
 "aucune_decision_institutionnelle",
 "aucune_piece_originale_sur_github",
 "sha_prives_et_identites_hors_bilan",
 "chaîne_p54i_p54j_p54k_ancree",
 "relecture_p54k_obligatoire",
 "suspension_prioritaire","contradictions_non_effacees",
 "reserves_non_effacees","comptabilite_droit_distincts",
 "pas_de_double_compte_ville_rtc","emploi_services_proteges",
 "regimes_quebec_separes","sinjira_inchange","main_non_fusionnee",
}
SHA="0123456789abcdef"

def need(ok,why):
    if not ok:raise ValueError(why)

def config():
    prior=p54k.configuration()
    expected={
      "schema_version":"P54L-1","date_reference":"2026-10-24",
      "exercice":2024,"source_jalon":"P54K",
      "ancrage_p54d_run":40120462237,
      "mandats":list(MANDATS),"dossiers":list(DOSSIERS),
      "categories":list(CATEGORIES),
      "qualifications_declaratives":list(QUALIFS),
      "etats_dossier":list(STATES),
      "limites":LIMITS,
      "protections":{k:True for k in GUARDS},
      "etat_initial":{
        "dossiers":4,"mandats":2,"categories_par_mandat":4,
        "verifications_officielles_executees":0,
        "avis_authentifies":0,"signatures_authentifiees":0,
        "experts_contactes":0,"dossiers_clos":0,
        "economies_certifiees_cad":None,"decision":NO_GO,
      },
    }
    data=json.loads(CONFIG.read_text("utf-8"))
    need(data==expected and tuple(prior["mandats"])==MANDATS
         and tuple(prior["dossiers"])==DOSSIERS,
         "P54L_ANCRAGE_OU_REGISTRE_ALTERE")
    return data

def private_template(raw_i=None,raw_j=None,raw_k=None):
    digest=lambda content:hashlib.sha256(content).hexdigest() if content else "0"*64
    return {
      "schema_version":"P54L-PIECES-LOCALES-1",
      "exercice":2024,"ancrage_p54d_run":40120462237,
      "sha256_fiche_p54i":digest(raw_i),
      "sha256_fiche_p54j":digest(raw_j),
      "sha256_fiche_p54k":digest(raw_k),
      "pieces":[],"observations":[],
    }

def validate_evidence(doc,file,raw_i,raw_j,raw_k,reviewed):
    need(type(doc) is dict and set(doc)==set(private_template()),
         "CHAMPS_MANIFESTE_INATTENDUS")
    expected=private_template(raw_i,raw_j,raw_k)
    need(doc["schema_version"]==expected["schema_version"]
         and type(doc["exercice"]) is int and doc["exercice"]==2024
         and type(doc["ancrage_p54d_run"]) is int
         and doc["ancrage_p54d_run"]==40120462237
         and all(doc[k]==expected[k] for k in (
           "sha256_fiche_p54i","sha256_fiche_p54j","sha256_fiche_p54k"))
         and type(doc["pieces"]) is list
         and len(doc["pieces"])<=LIMITS["nombre_pieces"]
         and type(doc["observations"]) is list
         and len(doc["observations"])<=LIMITS["nombre_observations"],
         "LIEN_P54I_J_K_NON_PROUVE")
    verified_ids=private.verify_proofs(file,doc["pieces"])
    pieces={entry["id"]:entry for entry in doc["pieces"]}
    # Only private documentary pieces, never a claimed certified opinion.
    need(all(row["type"]=="PIECE_JUSTIFICATIVE_PRIVEE"
             for row in doc["pieces"]),
         "TYPE_DE_PREUVE_NON_RECEVABLE")
    observed=set();used_pieces=set();by_case={}
    for record in doc["observations"]:
        need(type(record) is dict and set(record)=={
           "dossier_id","mandat","categorie",
           "qualification_declaree","piece_referencee",
           "authenticite_source_verifiee","signature_officielle_authentifiee",
           "statut_ordre_certifie","absence_conflit_certifiee",
           "decision_institutionnelle_autorisee",
        },"CHAMPS_OBSERVATION_SENSIBLES")
        case=record["dossier_id"];mandate=record["mandat"]
        category=record["categorie"];qualif=record["qualification_declaree"]
        key=(case,mandate,category)
        need(type(case) is str and case in DOSSIERS
             and type(mandate) is str and mandate in MANDATS
             and type(category) is str and category in CATEGORIES
             and key not in observed,
             "DOUBLON_OU_PORTEE_PREUVE_INVALIDE")
        observed.add(key)
        need(type(qualif) is str and qualif in QUALIFS,
             "QUALIFICATION_NON_ADMISSIBLE")
        need(any(c==case and m==mandate for c,m,_ in reviewed),
             "DECLARATION_SANS_REVUE_P54K")
        ref=record["piece_referencee"]
        need(ref is None or (type(ref) is str and ref in verified_ids),
             "REFERENCE_PIECE_INVALIDE")
        if qualif=="PIECE_LOCALE_NON_AUTHENTIFIEE":
            need(ref is not None,"PREUVE_DECLAREE_SANS_FICHIER")
        if ref is not None:
            need(ref not in used_pieces,"PIECE_REUTILISEE_COMME_PREUVE_DISTINCTE")
            used_pieces.add(ref)
        need(all(record[flag] is False for flag in (
          "authenticite_source_verifiee","signature_officielle_authentifiee",
          "statut_ordre_certifie","absence_conflit_certifiee",
          "decision_institutionnelle_autorisee")),
          "CERTIFICATION_FICTIVE_INTERDITE")
        by_case.setdefault(case,[]).append({
            "mandat":mandate,"categorie":category,
            "qualification":qualif,"piece_locale":ref is not None,
        })
    need(used_pieces==verified_ids,"PIECE_NON_RATTACHEE_A_UN_DOSSIER")
    return {"par_dossier":by_case,"pieces_verifiees":len(used_pieces),
            "observations_recues":len(observed),
            "pieces_referencees":len(used_pieces)}

def case_matrix(observed=None,upstream=None):
    reviews=(observed or {}).get("par_dossier",{})
    prior=upstream or {}
    rows=[];counts={}
    for case in DOSSIERS:
        parent=prior.get(case,"AUCUNE_REVUE_PROFESSIONNELLE")
        entries=reviews.get(case,[])
        if parent=="SUSPENSION_PRIORITAIRE" or any(
           x["qualification"]=="SUSPENSION_EXPLICITE" for x in entries):
            state="SUSPENSION_PRIORITAIRE"
        elif parent=="CONTRADICTION_OUVERTE":
            state="CONTRADICTION_OUVERTE"
        elif parent in ("RESERVE_OUVERTE","ALERTE_VERIFICATION") or any(
           x["qualification"]=="RESERVE_EXPLICITE" for x in entries):
            state="RESERVE_OUVERTE"
        elif any(x["piece_locale"] for x in entries):
            state="PIECES_LOCALES_A_AUTHENTIFIER"
        else:state="AUCUNE_PIECE_LOCALE"
        counts[state]=counts.get(state,0)+1
        rows.append({
          "dossier_id":case,"etat_p54l":state,
          "observations_declarees":len(entries),
          "pieces_techniquement_liees":sum(x["piece_locale"] for x in entries),
          "authenticite_professionnelle":False,
          "signature_authentifiee":False,
          "cloture_autorisee":False,
        })
    return rows,dict(sorted(counts.items()))

def report(cfg,observed=None,upstream=None):
    rows,states=case_matrix(observed,upstream)
    return {
      "schema_version":"P54L-BILAN-1","exercice":2024,
      "dossiers":rows,"etats":states,
      "observations_declarees_non_authentifiees":
           (observed or {}).get("observations_recues",0),
      "pieces_locales_integrite_seulement":
           (observed or {}).get("pieces_verifiees",0),
      "verifications_officielles_executees":0,
      "identites_et_permis_authentifies":0,
      "signatures_professionnelles_authentifiees":0,
      "avis_professionnels_certifies":0,
      "dossiers_clos":0,
      "controles_p54b_restants":96,
      "controles_p54c_restants":8,
      "economies_certifiees_cad":None,
      "effectifs_services_reduits_autorises":False,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def load_chain(p_i,p_j,p_k):
    source=[]
    for name in (p_i,p_j,p_k):
        file=private.private_file(name,32768)
        source.append((file,file.read_bytes()))
    (fi,ri),(fj,rj),(fk,rk)=source
    # Forbid aliases, including different paths to same file.
    need(len({f.resolve() for f,_ in source})==3,
         "SOURCE_DUPLIQUEE")
    manifest=json.loads(ri.decode("utf-8"))
    verified_i=p54k.p54i.validate_private(manifest,fi,p54k.p54i.configuration())
    conclusions=json.loads(rj.decode("utf-8"))
    opinions=p54k.p54j.validate_locals(conclusions,ri,manifest,verified_i)
    checklist=json.loads(rk.decode("utf-8"))
    reviewed=p54k.validate_reviews(checklist,ri,rj,opinions,manifest)
    scope={r["mandat"]:set(r["portee_dossiers"])
           for r in manifest["receptions"]}
    prior_j=p54k.p54j.public_report(p54k.p54j.configuration(),
             opinions,verified_i,scope)
    state_j={r["dossier_id"]:r["situation"] for r in prior_j["dossiers"]}
    prior_k=p54k.public_report(p54k.configuration(),opinions,
                              reviewed,state_j)
    upstream={r["dossier_id"]:r["etat_revue"] for r in prior_k["dossiers"]}
    return (ri,rj,rk),reviewed,upstream

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p54i")
    parser.add_argument("--p54j")
    parser.add_argument("--p54k")
    parser.add_argument("--pieces-locales")
    parser.add_argument("--modele-prive")
    parser.add_argument("--bilan")
    parser.add_argument("--exiger-authenticite",action="store_true")
    arg=parser.parse_args(argv)
    try:
        sources=[arg.p54i,arg.p54j,arg.p54k]
        need(not any(sources) or all(sources),
             "TROIS_SOURCES_REQUISES")
        need(not arg.pieces_locales or all(sources),
             "PIECES_EXIGENT_CHAINE_COMPLETE")
        paths=[Path(x) for x in (arg.modele_prive,arg.bilan) if x]
        need(len({p.resolve() for p in paths})==len(paths)
             and all(not p.exists() and not p.is_symlink() for p in paths),
             "SORTIES_EXISTANTES_OU_DUPLIQUEES")
        cfg=config()
        raw=None;reviewed={};upstream=None;observed=None
        if all(sources):
            raw,reviewed,upstream=load_chain(*sources)
        if arg.pieces_locales:
            file=private.private_file(arg.pieces_locales,
                                      LIMITS["taille_fiche_octets"])
            need(all(file.resolve()!=p.resolve() for p in paths)
                 and file.resolve() not in {
                   Path(s).resolve() for s in sources},
                 "CHEMINS_ENTREE_SORTIE_NON_DISTINCTS")
            doc=json.loads(file.read_text("utf-8"))
            observed=validate_evidence(doc,file,*raw,reviewed)
        if arg.modele_prive:
            private.write_new(arg.modele_prive,
              private_template(*(raw or (None,None,None))),private=True)
        result=report(cfg,observed,upstream)
        if arg.bilan:private.write_new(arg.bilan,result)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if arg.exiger_authenticite else 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError,
            json.JSONDecodeError) as error:
        print("P54L_REFUS: "+str(error),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
