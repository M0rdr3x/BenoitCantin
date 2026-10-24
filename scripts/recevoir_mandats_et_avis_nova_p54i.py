#!/usr/bin/env python3
"""P54I — réception locale de fichiers de mandat/avis, intégrité ≠ authenticité.

Ne jamais copier des pièces privées dans Git ni vers GitHub Actions. Le hachage
atteste seulement la concordance octet par octet du fichier local.
"""
import argparse
import json
from pathlib import Path
import re
import sys

import preparer_mandats_experts_nova_p54h as p54h
import gerer_contre_revues_nova_p54f as private

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54I_REGISTRE_RECEPTION_AVIS_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
MANDATS=("MANDAT-COMPTABLE-2024","MANDAT-JURIDIQUE-2024")
CASES=("P54E-V-001","P54E-M-001","P54E-M-002","P54E-M-003")
KINDS=("DOCUMENT_MANDAT_DECLARATIF",
       "AVIS_PROFESSIONNEL_NON_AUTHENTIFIE","ANNEXE_JUSTIFICATIVE")
RESERVES=("AUCUNE_DECLAREE_NON_VERIFIEE","SIGNATURE_A_VERIFIER",
          "PORTEE_LIMITEE","PIECES_PRIMAIRES_MANQUANTES",
          "CONFLIT_A_EXAMINER","CONTRADICTION_OUVERTE",
          "UNITE_PERIMETRE_AMBIGUS","SUSPENSION_EXPLICITE")
STATES=("FICHIER_LOCAL_NON_RECU","FICHIER_LOCAL_INTEGRE_NON_AUTHENTIFIE",
        "RESERVE_OUVERTE","SUSPENDU")
GATES=("EMPLACEMENT_PRIVE","SHA256_OCTETS","TYPE_PIECE_ET_MANDAT",
       "PORTEE_EXERCICE_2024","CONFLITS_ET_INDEPENDANCE",
       "SIGNATURE_ET_AUTHENTICITE","RESERVES_ET_CONTRADICTIONS",
       "DROITS_D_ACCES_ET_CONFIDENTIALITE",
       "CONTINUITE_EMPLOIS_SERVICES","DOUBLE_COMPTE_CONSOLIDATION")
GUARDS={
 "fichier_local_ne_prouve_pas_provenance_officielle",
 "hachage_octets_obligatoire","avis_professionnel_ne_signifie_pas_audit_certifie",
 "authenticite_signature_non_automatisee",
 "qualification_professionnelle_non_verifiee",
 "conflits_d_interets_non_resolus_automatiquement",
 "reservations_et_desaccords_non_effaces","pièces_privees_hors_git",
 "aucun_fichier_avis_original_sur_actions",
 "aucun_nom_numero_permis_ni_sha_prive_public",
 "aucune_simulation_d_honoraires_engages",
 "aucun_contact_ou_mandat_reel_pretendu",
 "aucun_go_financier_ou_politique","aucun_dossier_p54e_clos",
 "aucun_double_compte_ville_rtc","emploi_et_services_proteges",
 "deux_scenarios_quebec_separes","main_et_sinjira_inchanges",
}
LIMITS={"taille_manifest_octets":32768,"nombre_fichiers_max":8,
        "fichier_max_octets":33554432,"roles_de_reception_non_authentifies":2}
ID=re.compile(r"^REC-[A-Z0-9]{4,12}$")

def need(ok,why):
    if not ok:raise ValueError(why)

def configuration():
    parent=p54h.configuration()
    expected={
      "schema_version":"P54I-1","date_reference":"2026-10-24",
      "exercice_source":2024,"source_jalon":"P54H",
      "source_run_p54d":40120462237,
      "mandats":[m["code"] for m in parent["mandats"]],
      "dossiers_source":parent["mandats"][0]["dossiers"],
      "types_piece":list(KINDS),"reserves":list(RESERVES),
      "situations":list(STATES),"points_reception":list(GATES),
      "limites":LIMITS,"protections":{x:True for x in GUARDS},
      "etat_initial":{
        "mandats":2,"dossiers_non_clos":4,
        "positions_controle_reception_non_attestees":20,
        "documents_reellement_recus_dans_git":0,
        "avis_originaux_authentifies":0,"mandats_signes_authentifies":0,
        "experts_independance_verifiee":0,
        "economies_certifiees_cad":None,"decision":NO_GO},
    }
    need(tuple(expected["mandats"])==MANDATS
         and tuple(expected["dossiers_source"])==CASES
         and json.loads(CONFIG.read_text("utf-8"))==expected,
         "P54I_REFERENCE_CONFIG_INVALIDE")
    return expected

def local_template(cfg):
    return {"schema_version":"P54I-FICHE-LOCALE-1",
            "ancrage_P54D_run":40120462237,
            "annee_comptable":2024,
            "pieces":[],
            "receptions":[]}

def validate_private(doc,location,cfg):
    need(type(doc) is dict and set(doc)=={
      "schema_version","ancrage_P54D_run",
      "annee_comptable","pieces","receptions"},
      "RECEPTION_CHAMPS_INATTENDUS")
    need(doc["schema_version"]=="P54I-FICHE-LOCALE-1"
         and type(doc["ancrage_P54D_run"]) is int
         and doc["ancrage_P54D_run"]==40120462237
         and type(doc["annee_comptable"]) is int
         and doc["annee_comptable"]==2024
         and type(doc["pieces"]) is list
         and len(doc["pieces"])<=LIMITS["nombre_fichiers_max"]
         and type(doc["receptions"]) is list
         and len(doc["receptions"])<=2,
         "FICHE_RECEPTION_INVALIDE")
    # p54f checks byte hashes, secure paths, permissions, traversal and symlinks.
    ids=private.verify_proofs(location,doc["pieces"])
    types={p["id"]:p["type"] for p in doc["pieces"]}
    seen=set();all_refs=set();counts={"FICHIER_LOCAL_NON_RECU":0,
         "FICHIER_LOCAL_INTEGRE_NON_AUTHENTIFIE":0,
         "RESERVE_OUVERTE":0,"SUSPENDU":0}
    results=[]
    for rec in doc["receptions"]:
        need(type(rec) is dict and set(rec)=={
           "mandat","code_reception","documents",
           "nature_declaree","reserve_declaree","portee_dossiers",
           "controles_declaratifs","contact_effectif_verifie",
           "contrat_signe_authentifie","signature_avis_authentifiee",
           "independance_verifiee","montant_financier_certifie"},
           "RECEPTION_CONTIENT_CHAMPS_SENSIBLES")
        mandate=rec["mandat"];code=rec["code_reception"]
        need(type(mandate) is str and mandate in MANDATS
             and mandate not in seen
             and type(code) is str and bool(ID.fullmatch(code)),
             "RECEPTION_MANDAT_OU_ID_INVALIDE")
        seen.add(mandate)
        docs=rec["documents"]
        need(type(docs) is list and len(docs)==len(set(docs))
             and all(type(x) is str and x in ids for x in docs)
             and not (set(docs)&all_refs),
             "PIECES_REUTILISEES_OU_INCONNUES")
        all_refs.update(docs)
        need(type(rec["nature_declaree"]) is str
             and rec["nature_declaree"] in KINDS
             and type(rec["reserve_declaree"]) is str
             and rec["reserve_declaree"] in RESERVES,
             "NATURE_OU_RESERVE_NON_ADMISSIBLE")
        if docs:
            required={
              "DOCUMENT_MANDAT_DECLARATIF":"PIECE_JUSTIFICATIVE_PRIVEE",
              "AVIS_PROFESSIONNEL_NON_AUTHENTIFIE":
                       "AVIS_PROFESSIONNEL_NON_ATTESTE",
              "ANNEXE_JUSTIFICATIVE":"PIECE_JUSTIFICATIVE_PRIVEE"
            }[rec["nature_declaree"]]
            need(any(types[x]==required for x in docs),
                 "PIECE_DE_TYPE_INCOHERENT")
        cases=rec["portee_dossiers"];checks=rec["controles_declaratifs"]
        need(type(cases) is list and cases
             and len(set(cases))==len(cases)
             and all(type(x) is str and x in CASES for x in cases),
             "PORTÉE_DES_DOSSIERS_HORS_CHAMP")
        need(type(checks) is list and len(checks)==len(set(checks))
             and all(type(x) is str and x in GATES for x in checks),
             "POINTS_DE_CONTROLE_INVALIDES")
        need(all(rec[x] is False for x in (
          "contact_effectif_verifie","contrat_signe_authentifie",
          "signature_avis_authentifiee","independance_verifiee",
          "montant_financier_certifie")),
          "AUTHENTICITE_OU_CERTIFICATION_FICTIVE")
        if not docs:state="FICHIER_LOCAL_NON_RECU"
        elif rec["reserve_declaree"]=="SUSPENSION_EXPLICITE":state="SUSPENDU"
        elif rec["reserve_declaree"]!="AUCUNE_DECLAREE_NON_VERIFIEE":
            state="RESERVE_OUVERTE"
        else:state="FICHIER_LOCAL_INTEGRE_NON_AUTHENTIFIE"
        counts[state]+=1
        results.append({
          "mandat":mandate,"etat_technique":state,
          "nb_pieces_locales_verifiees_par_hachage":len(docs),
          "nb_controles_declares_non_attestes":len(checks),
          "nb_dossiers_concernes":len(cases),
          "expert_independant_authentifie":False,
          "avis_professionnel_authentifie":False,
          "montant_certifie":False})
    for mandate in MANDATS:
        if mandate not in seen:
            counts["FICHIER_LOCAL_NON_RECU"]+=1
            results.append({
              "mandat":mandate,"etat_technique":"FICHIER_LOCAL_NON_RECU",
              "nb_pieces_locales_verifiees_par_hachage":0,
              "nb_controles_declares_non_attestes":0,
              "nb_dossiers_concernes":4,
              "expert_independant_authentifie":False,
              "avis_professionnel_authentifie":False,
              "montant_certifie":False})
    return {"mandats":results,"etats":{k:v for k,v in counts.items() if v},
            "pieces_locales_integrite_verifiee":len(ids),
            "declarations_de_reception":len(doc["receptions"])}

def report(cfg,observed=None):
    if observed is None:
        observed={"mandats":[{
          "mandat":code,"etat_technique":"FICHIER_LOCAL_NON_RECU",
          "nb_pieces_locales_verifiees_par_hachage":0,
          "nb_controles_declares_non_attestes":0,
          "nb_dossiers_concernes":4,
          "expert_independant_authentifie":False,
          "avis_professionnel_authentifie":False,
          "montant_certifie":False} for code in MANDATS],
          "etats":{"FICHIER_LOCAL_NON_RECU":2},
          "pieces_locales_integrite_verifiee":0,
          "declarations_de_reception":0}
    return {
      "schema_version":"P54I-BILAN-1",
      "annee_source":2024,
      "mandats":observed["mandats"],
      "statuts_locaux":observed["etats"],
      "pieces_locales_integrite_seulement":
           observed["pieces_locales_integrite_verifiee"],
      "declarations_de_reception":observed["declarations_de_reception"],
      "mandats_reellement_authentifies":0,
      "experts_independants_authentifies":0,
      "avis_independants_signes_authentifies":0,
      "dossiers_clos":0,
      "controles_p54b_en_attente":96,
      "controles_p54c_en_attente":8,
      "economies_certifiees_cad":None,
      "emplois_services_proteges":True,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bilan")
    p.add_argument("--modele-prive")
    p.add_argument("--fiche-locale")
    p.add_argument("--exiger-authenticite-certifiee",action="store_true")
    args=p.parse_args(argv)
    try:
        outputs=[Path(x) for x in (args.bilan,args.modele_prive) if x]
        need(len({x.resolve() for x in outputs})==len(outputs)
             and all(not x.exists() and not x.is_symlink() for x in outputs),
             "SORTIE_EXISTANTE_OU_DUPLIQUEE")
        cfg=configuration()
        observed=None
        if args.fiche_locale:
            f=private.private_file(args.fiche_locale,
                                   LIMITS["taille_manifest_octets"])
            need(all(f.resolve()!=x.resolve() for x in outputs),
                 "ENTREE_SORTIE_IDENTIQUE")
            observed=validate_private(json.loads(f.read_text("utf-8")),f,cfg)
        summary=report(cfg,observed)
        if args.modele_prive:
            private.write_new(args.modele_prive,local_template(cfg),private=True)
        if args.bilan:private.write_new(args.bilan,summary)
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        return 3 if args.exiger_authenticite_certifiee else 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P54I_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
