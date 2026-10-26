#!/usr/bin/env python3
"""P54W — déclarations privées de qualification, SANS attestation professionnelle.

Exploite un fichier privé P54V fourni par un opérateur; son empreinte et ses
références P54T sont vérifiées, mais la provenance des extraits n'est pas
réauthentifiée ici. Ne publie jamais jetons, contextes, notes ou identités.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import sys

import preparer_contextes_prives_nova_p54v as p54v

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54W_GRILLE_QUALIFICATION_HUMAINE_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
REFS=("P54E-V-001","P54E-M-001","P54O-DATE-001",
      "P54E-M-002","P54E-M-003")
ROLES=("LECTEUR_DECLARE","CONTRE_LECTEUR_DECLARE")
NATURE=(
 "INDETERMINE","ANNEE_DATE_POSSIBLE","FOLIO_PAGINATION_POSSIBLE",
 "REFERENCE_NORMATIVE_POSSIBLE","IDENTIFIANT_POSSIBLE",
 "VALEUR_NON_MONETAIRE_POSSIBLE","MONTANT_POTENTIEL_NON_ATTESTE",
)
PROGRESS=("NON_EXAMINE","EXAMINE_SUR_PIECE_NON_ATTESTE","SUSPENDU")
RESERVES=(
 "AUCUNE_DECLAREE_NON_VERIFIEE","CONTEXTE_INSUFFISANT",
 "ORIGINAL_ABSENT","UNITE_COLONNE_A_VERIFIER",
 "CONTRADICTION_OUVERTE","SUSPENSION_DEMANDEE",
)
STATES=(
 "NON_EXAMINE","REVUE_PARTIELLE_NON_ATTESTEE",
 "DEUX_REVUES_DECLARATIVES_NON_ATTESTEES",
 "RESERVE_OUVERTE","CONTRADICTION_DECLAREE_NON_RESOLUE",
 "SUSPENSION_MAINTENUE",
)
CHECKS=p54v.CHECKS
GUARDS={
 "contextes_et_jetons_prives_hors_git",
 "aucun_texte_brut_dans_bilan_public",
 "empreinte_de_fiche_p54v_recalculee",
 "positions_publiques_p54t_verifiees",
 "identites_pseudonymes_non_authentifiees",
 "double_revue_declarative_seulement",
 "desaccords_non_resolus_automatiquement",
 "suspensions_prioritaires","date_probable_non_finalisee",
 "qualification_monetaires_non_certifiante",
 "aucune_economie_fiscale_certifiee",
 "consolidation_ville_rtc_somhac_sans_double_compte",
 "emploi_et_services_proteges",
 "quebec_canada_et_souverain_hypothetique_separes",
 "aucun_contact_avec_autorites","aucun_deploiement_ni_transmission",
 "aucune_fusion_main","sinjira_inchange",
 "dossiers_p54e_non_clos","no_go_automatique",
}
ID=re.compile(r"^REV-[A-Z0-9]{4,12}$")
SHA=re.compile(r"^[a-f0-9]{64}$")
FLAGS=(
 "identite_professionnelle_authentifiee",
 "signature_professionnelle_authentifiee",
 "independance_verifiee",
 "qualification_finale_certifiee",
 "valeur_financiere_certifiee",
 "dossier_clos",
)

def need(ok,why):
    if not ok:raise ValueError(why)

def configuration():
    prior=p54v.configuration()
    expected={
      "schema_version":"P54W-1","date_reference":"2026-10-25",
      "exercice":2024,"source_jalons":["P54T","P54U","P54V"],
      "source_p54p_run":40151185184,
      "source_p54p_artifact":12583661231,
      "refs":list(REFS),"roles":list(ROLES),
      "nature_possible":list(NATURE),"etats_revue":list(PROGRESS),
      "reserves":list(RESERVES),"statuts_suivi":list(STATES),
      "controles_reference":list(CHECKS),
      "protections":{name:True for name in GUARDS},
      "etat_initial":{
        "occurrences":5,"dossiers_p54e_ouverts":4,
        "occurrence_date_probable_non_certifiee":1,
        "positions_role_potentielles":10,
        "revues_humaines_authentifiees":0,
        "signatures_professionnelles_authentifiees":0,
        "conclusions_financieres_certifiees":0,
        "controles_p54b_non_attestes":96,
        "controles_p54c_non_attestes":8,
        "taches_p54n_non_attestees":40,
        "blocages_p54o_non_leves":10,
        "economies_certifiees_cad":None,"decision":NO_GO,
      },
    }
    cfg=json.loads(CONFIG.read_text("utf-8"))
    need(cfg==expected and prior["observations"]==5
         and prior["controle_humain"]==list(CHECKS)
         and prior["reference_p54p_run"]==cfg["source_p54p_run"]
         and prior["reference_p54p_artifact"]==
             cfg["source_p54p_artifact"],
         "CONFIGURATION_P54W_NON_CONFORME")
    return cfg

def private_file(path,max_bytes=131072):
    need(isinstance(path,(str,Path)) and str(path),"FICHIER_PRIVÉ_ABSENT")
    p=Path(path).expanduser().absolute()
    need(not any(part.is_symlink() for part in (p,*p.parents)),
         "LIEN_SYMBOLIQUE_INTERDIT")
    need(p.is_file() and p.stat().st_size<=max_bytes
         and stat.S_IMODE(p.stat().st_mode)==0o600,
         "FICHIER_PRIVE_INACCESSIBLE_OU_PERMISSIONS_NON_SURES")
    resolved=p.resolve();root=ROOT.resolve()
    need(root not in (resolved,*resolved.parents),
         "ENTREE_PRIVEE_DANS_GIT")
    return p

def validate_p54v(doc,reference):
    """Strict metadata checks. Does not authenticate the PDF origin."""
    need(type(doc) is dict and set(doc)=={
      "schema_version","confidentialite","source","occurrences",
      "signatures_professionnelles_authentifiees",
      "economies_certifiees_cad","decision",
    },"STRUCTURE_FICHE_P54V_INVALIDE")
    need(doc["schema_version"]=="P54V-FICHE-PRIVEE-1"
         and doc["confidentialite"]=="NE_PAS_DEPLOYER_OU_PUBLIER"
         and doc["source"]==
          "PDF_2024_SHA256_CONFORMES_LOCALEMENT_PLUS_P54T"
         and doc["signatures_professionnelles_authentifiees"]==0
         and doc["economies_certifiees_cad"] is None
         and doc["decision"]==NO_GO
         and type(doc["occurrences"]) is list
         and len(doc["occurrences"])==5,
         "FICHE_P54V_NEUTRALITE_OU_NOMBRE_INVALIDE")
    need(type(reference) is list and len(reference)==5,
         "REFERENCES_P54T_MANQUANTES")
    for i,card in enumerate(doc["occurrences"]):
        expected=reference[i]
        need(type(card) is dict and set(card)=={
          "reference","source","page_pdf_index_zero",
          "offset_caractere_nfkc","zone_indicative",
          "classification_automatique_non_attestee",
          "jeton_brut_STRICTEMENT_PRIVE",
          "extrait_contextuel_STRICTEMENT_PRIVE",
          "debut_extrait_nfkc","etat","controles_a_instruire",
          "revue_contradictoire_effectuee",
          "qualification_humaine_confirmee",
        },"CHAMPS_OCCURRENCE_P54V_INATTENDUS")
        token=card["jeton_brut_STRICTEMENT_PRIVE"]
        excerpt=card["extrait_contextuel_STRICTEMENT_PRIVE"]
        start=card["debut_extrait_nfkc"]
        offset=expected["offset_texte_extrait"]
        inner=offset-start if type(start) is int else -1
        need(card["reference"]==REFS[i]
             and card["reference"]==(
                 expected["dossier"] or "P54O-DATE-001")
             and card["source"]==expected["source"]
             and type(card["page_pdf_index_zero"]) is int
             and card["page_pdf_index_zero"]==expected["pdf_index_zero"]
             and type(card["offset_caractere_nfkc"]) is int
             and card["offset_caractere_nfkc"]==offset
             and card["zone_indicative"]==
                expected["zone_confirmee_par_parseur"]
             and card["classification_automatique_non_attestee"]==
                expected["classification_indicative"]
             and type(start) is int and 0<=start<=offset
             and type(token) is str and 0<len(token)<=64
             and type(excerpt) is str and 0<len(excerpt)<=512
             and 0<=inner<len(excerpt)
             and excerpt[inner:inner+len(token)]==token
             and card["etat"]=="A_EXAMINER_PAR_PERSONNE_HABILITEE"
             and card["revue_contradictoire_effectuee"] is False
             and card["qualification_humaine_confirmee"] is False
             and type(card["controles_a_instruire"]) is list
             and card["controles_a_instruire"]==[
                {"code":c,"etat":"NON_ATTESTE"} for c in CHECKS],
             "SOURCE_P54V_OU_JETON_NON_CONFORME")
    return True

def private_template(raw=None):
    return {
      "schema_version":"P54W-DECLARATIONS-PRIVEES-1",
      "exercice":2024,
      "sha256_fiche_p54v":hashlib.sha256(raw).hexdigest()
           if raw is not None else "0"*64,
      "declarations":[],
    }

def validate_reviews(doc,raw,source):
    need(type(doc) is dict and set(doc)==set(private_template()),
         "FICHE_P54W_CHAMPS_INATTENDUS")
    expected=private_template(raw)
    need(doc["schema_version"]==expected["schema_version"]
         and type(doc["exercice"]) is int and doc["exercice"]==2024
         and type(doc["sha256_fiche_p54v"]) is str
         and SHA.fullmatch(doc["sha256_fiche_p54v"]) is not None
         and doc["sha256_fiche_p54v"]==expected["sha256_fiche_p54v"]
         and type(doc["declarations"]) is list
         and len(doc["declarations"])<=10,
         "SHA_P54V_OU_FORMULAIRE_NON_CONFORME")
    recorded={};codes={}
    for row in doc["declarations"]:
        need(type(row) is dict and set(row)=={
          "reference","role","code_lecteur","nature_declaree",
          "etat_declare","reserve_declaree","controles_declares",*FLAGS
        },"CHAMPS_LIBRES_OU_CERTIFIANTS_INTERDITS")
        ref=row["reference"];role=row["role"];code=row["code_lecteur"]
        key=(ref,role)
        need(type(ref) is str and ref in REFS
             and type(role) is str and role in ROLES
             and type(code) is str and ID.fullmatch(code) is not None
             and key not in recorded,
             "ROLE_OU_REFERENCE_NON_CONFORME")
        nature=row["nature_declaree"];progress=row["etat_declare"]
        reserve=row["reserve_declaree"];controls=row["controles_declares"]
        need(type(nature) is str and nature in NATURE
             and type(progress) is str and progress in PROGRESS
             and type(reserve) is str and reserve in RESERVES
             and type(controls) is list
             and all(type(c) is str and c in CHECKS for c in controls)
             and len(set(controls))==len(controls),
             "QUALIFICATION_OU_GRILLE_INVALIDE")
        if progress=="NON_EXAMINE":
            need(nature=="INDETERMINE" and not controls
                 and reserve=="AUCUNE_DECLAREE_NON_VERIFIEE",
                 "AUCUN_EXAMEN_NE_PEUT_AVOIR_DE_CONCLUSION")
        if progress=="EXAMINE_SUR_PIECE_NON_ATTESTE":
            need("QUALIFIER_NATURE_SUR_PIECE" in controls
                 and reserve!="SUSPENSION_DEMANDEE",
                 "QUALIFICATION_SANS_EXAMEN_CIBLE")
        need((progress=="SUSPENDU")==
             (reserve=="SUSPENSION_DEMANDEE"),
             "SUSPENSION_ET_MOTIF_INCOHERENTS")
        need(all(row[flag] is False for flag in FLAGS),
             "SIGNATURE_OU_CERTIFICATION_FICTIVE")
        codes.setdefault(ref,set())
        need(code not in codes[ref],
             "MEME_PSEUDONYME_DEUX_ROLES")
        codes[ref].add(code)
        recorded[key]=row
    return recorded

def matrix(reviewed=None):
    parsed=reviewed or {}
    items=[];count={}
    for ref in REFS:
        entries=[parsed[(ref,r)] for r in ROLES if (ref,r) in parsed]
        examined=[x for x in entries if x["etat_declare"]==
                   "EXAMINE_SUR_PIECE_NON_ATTESTE"]
        substantive={x["nature_declaree"] for x in examined}
        if any(x["etat_declare"]=="SUSPENDU" for x in entries):
            state="SUSPENSION_MAINTENUE"
        elif len(substantive)>1 or any(
            x["reserve_declaree"]=="CONTRADICTION_OUVERTE"
            for x in entries):
            state="CONTRADICTION_DECLAREE_NON_RESOLUE"
        elif any(x["reserve_declaree"] not in (
            "AUCUNE_DECLAREE_NON_VERIFIEE",) for x in entries):
            state="RESERVE_OUVERTE"
        elif len(examined)==2:
            state="DEUX_REVUES_DECLARATIVES_NON_ATTESTEES"
        elif examined:
            state="REVUE_PARTIELLE_NON_ATTESTEE"
        else:state="NON_EXAMINE"
        count[state]=count.get(state,0)+1
        items.append({
          "reference":ref,"etat":state,
          "declarations_recues":len(entries),
          "revues_sur_piece_declarees_non_authentifiees":len(examined),
          "qualification_definitive":False,
          "signature_verifiee":False,
          "montant_certifie":False,
          "dossier_clos":False,
        })
    return items,dict(sorted(count.items()))

def report(cfg,reviewed=None):
    rows,distribution=matrix(reviewed)
    return {
      "schema_version":"P54W-BILAN-1","exercice":2024,
      "occurrences":rows,"statuts":distribution,
      "declarations_locales_non_authentifiees":len(reviewed or {}),
      "contextes_bruts_ou_jetons_publies":0,
      "identites_professionnelles_authentifiees":0,
      "signatures_authentifiees":0,
      "qualifications_definitives":0,
      "valeurs_monetaires_certifiees":0,
      "dossiers_p54e_ouverts":4,
      "occurrence_date_probable_non_certifiee":1,
      "taches_p54n_non_attestees":40,
      "blocages_p54o_non_leves":10,
      "controles_p54b_non_attestes":96,
      "controles_p54c_non_attestes":8,
      "economies_certifiees_cad":None,
      "fusion_main_autorisee":False,"transmission_autorisee":False,
      "decision":NO_GO,
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fiche-privee-p54v")
    parser.add_argument("--revues-privees")
    parser.add_argument("--modele-prive")
    parser.add_argument("--bilan-public")
    parser.add_argument("--exiger-cloture",action="store_true")
    args=parser.parse_args(argv)
    try:
        need(not args.revues_privees or args.fiche_privee_p54v,
             "REVUES_EXIGENT_FICHE_P54V")
        cfg=configuration()
        sources=[private_file(v) for v in (
           args.fiche_privee_p54v,args.revues_privees) if v]
        outputs=[Path(v).expanduser().absolute() for v in (
           args.modele_prive,args.bilan_public) if v]
        need(len({p.resolve() for p in sources+outputs})==
             len(sources)+len(outputs)
             and all(not f.exists() and not f.is_symlink() for f in outputs),
             "CHEMINS_IDENTIQUES_OU_SORTIES_EXISTANTES")
        raw=None;source=None;reviewed=None
        if args.fiche_privee_p54v:
            f=private_file(args.fiche_privee_p54v)
            raw=f.read_bytes()
            source=json.loads(raw.decode("utf-8"))
            ref=p54v.p54t.verify_frozen(p54v.p54t.configuration())
            validate_p54v(source,ref["positions_de_reference"])
        if args.revues_privees:
            file=private_file(args.revues_privees)
            reviewed=validate_reviews(
               json.loads(file.read_text("utf-8")),raw,source)
        if args.modele_prive:
            p54v.private_write_new(args.modele_prive,
                                   private_template(raw))
        public=report(cfg,reviewed)
        if args.bilan_public:
            p54v.write_public_new(args.bilan_public,public)
        print(json.dumps(public,ensure_ascii=False,sort_keys=True))
        return 3 if args.exiger_cloture else 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,
            json.JSONDecodeError):
        print("P54W_REFUS: SOURCE_OU_REVUE_NON_CONFORME",file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
