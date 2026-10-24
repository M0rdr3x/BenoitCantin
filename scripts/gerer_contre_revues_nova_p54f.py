#!/usr/bin/env python3
"""P54F — contrôle contradictoire de déclarations humaines et pièces locales.

Ni une empreinte SHA-256, ni deux avis déclaratifs concordants, ni un statut
DOCUMENTE_NON_ATTESTE ne constituent une expertise comptable certifiée.
Les originaux, extraits, identités, chemins et SHA privés ne sortent pas.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

import preparer_revue_humaine_nova_p54e as p54e

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54F_CONTRE_REVUE_QUATRE_DOSSIERS_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
ROLES=("EXAMINATEUR","CONTRE_REVISEUR")
TYPES=("PUBLICATION_PDF","NOTE_ANALYSE_PRIVEE",
       "PIECE_JUSTIFICATIVE_PRIVEE","AVIS_PROFESSIONNEL_NON_ATTESTE")
ETATS=("EN_ATTENTE","EXAMEN_UNIQUE","DESACCORD","SUSPENDU",
       "CONCORDANCE_DECLARATIVE_INCOMPLETE",
       "CONCORDANCE_DECLARATIVE_DOCUMENTEE_NON_ATTESTEE")
FLAGS={
 "aucune_identite_reelle_publique","pieces_privees_jamais_televersees",
 "empreintes_recalculees_sur_fichiers_locaux",
 "deux_roles_distincts_declaratifs",
 "absence_verification_identite_professionnelle",
 "desaccords_jamais_clos_automatiquement",
 "concordance_n_est_pas_attestation","aucun_montant_brut_dans_bilan",
 "traces_originales_hors_git","aucune_suppression_emplois_services",
 "aucune_nouvelle_economie_operations_deja_eliminees",
 "deux_regimes_constitutionnels_distincts",
 "maintien_no_go","aucune_fusion_main_ou_action_sinjira",
}
LIMITS={"taille_fiche_max_octets":65536,"taille_piece_max_octets":33554432,
        "nombre_pieces_max":12,"taille_toutes_pieces_max_octets":134217728}
CODE=re.compile(r"^[A-Z][A-Z0-9_-]{3,23}$")
DIGEST=re.compile(r"^[a-f0-9]{64}$")
EVIDENCE_ID=re.compile(r"^PIECE-[0-9]{3}$")

def require(ok,why):
    if not ok:raise ValueError(why)

def configuration():
    e=p54e.config()
    data=json.loads(CONFIG.read_text("utf-8"))
    expected={
      "schema_version":"P54F-1","date_reference":"2026-10-24",
      "source_jalon":"P54E","source_run_p54d":40120462237,
      "source_config":"P54E_PLAN_REVUE_HUMAINE_2024.json",
      "exercice":2024,
      "dossiers":[x["id"] for x in e["cases"]],
      "roles":list(ROLES),"statuts":list(p54e.STATUS),
      "contradictions":["NON_EVALUE","QUESTION_OUVERTE",
                        "EXAMEN_CONTRADICTOIRE_REQUIS"],
      "hypotheses":list(p54e.HYP),
      "types_pieces":list(TYPES),"etats_dossier":list(ETATS),
      "limites_techniques":LIMITS,
      "protections":{flag:True for flag in FLAGS},
      "etat_initial":{
        "dossiers":4,"roles_attendus":8,
        "positions_controle_2_roles":80,"preuves_reelles_p54f":0,
        "examens_humains_recus":0,"contre_revues_recues":0,
        "avis_independants_signes":0,
        "conclusions_comptables_certifiees":0,
        "economies_certifiees_cad":None,"decision":NO_GO},
    }
    require(data==expected and len(e["cases"])==4
            and len(e["gates"])==10,"CONFIGURATION_P54F_INCOHERENTE")
    return data

def private_file(path,max_bytes):
    p=Path(path)
    require(p.is_file() and not p.is_symlink()
            and not p.resolve().is_relative_to(ROOT.resolve())
            and 0<p.stat().st_size<=max_bytes
            and stat.S_IMODE(p.stat().st_mode)&0o077==0,
            "PIECE_LOCALE_ABSENTE_NON_PRIVEE_OU_DANS_GIT")
    return p

def verify_proofs(reviews_file,items):
    """Verify actual bytes, never echo their paths, hashes or contents."""
    require(type(items) is list and len(items)<=LIMITS["nombre_pieces_max"],
            "TROP_DE_PIECES")
    root=reviews_file.parent.resolve()
    hashes=set()
    result=set()
    all_size=0
    for item in items:
        require(type(item) is dict and set(item)=={
          "id","type","relative_path","sha256"},
          "CHAMPS_PIECE_INTERDITS")
        ident=item["id"];kind=item["type"];name=item["relative_path"]
        digest=item["sha256"]
        require(type(ident) is str and EVIDENCE_ID.fullmatch(ident)
                and ident not in result and kind in TYPES
                and type(digest) is str and DIGEST.fullmatch(digest),
                "ID_TYPE_OU_EMPREINTE_INVALIDES")
        result.add(ident)
        require(type(name) is str and len(name)<=120
                and "\\" not in name and
                re.fullmatch(r"[A-Za-z0-9_./-]+",name),
                "CHEMIN_PIECE_INVALIDE")
        pure=PurePosixPath(name)
        require(not pure.is_absolute() and
                len(pure.parts)>=2 and pure.parts[0]=="preuves"
                and all(x not in (".","..") for x in name.split("/")),
                "TRAVERSEE_REPERTOIRE_REFUSEE")
        target=reviews_file.parent.joinpath(*pure.parts)
        # Refuse symlinks even when they would resolve inside allowed root.
        require(all(not current.is_symlink() for current in
          [reviews_file.parent.joinpath(*pure.parts[:i])
           for i in range(1,len(pure.parts)+1)]),
          "LIEN_SYMBOLIQUE_REFUSE")
        require(target.resolve().is_relative_to(root),
                "CHEMIN_SORTANT_DU_REPERTOIRE_PRIVE")
        actual=private_file(target,LIMITS["taille_piece_max_octets"])
        all_size+=actual.stat().st_size
        require(all_size<=LIMITS["taille_toutes_pieces_max_octets"],
                "TAILLE_TOTALE_EXCESSIVE")
        h=hashlib.sha256()
        with actual.open("rb") as f:
            for chunk in iter(lambda:f.read(131072),b""):
                h.update(chunk)
        require(h.hexdigest()==digest,"EMPREINTE_DE_PIECE_NON_CONFORME")
        hashes.add(digest)
    # Identical bytes may be referenced by distinct IDs; not necessarily fraud.
    return result

def classify_reviews(rows,proof_ids,cfg):
    require(type(rows) is list and len(rows)<=8,
            "TROP_DE_DECLARATIONS")
    by_case={name:{} for name in cfg["dossiers"]}
    for row in rows:
        require(type(row) is dict and set(row)=={
          "dossier_id","role","code_relecteur",
          "hypothese","statut","contradiction",
          "controles_declares","pieces_referencees",
          "avis_independant_signe_valide",
          "certification_financiere_autorisee"},
          "CHAMPS_DE_DECLARATION_INTERDITS")
        case=row["dossier_id"];role=row["role"]
        who=row["code_relecteur"]
        require(type(case) is str and case in by_case
                and type(role) is str and role in ROLES
                and role not in by_case[case]
                and type(who) is str and CODE.fullmatch(who),
                "IDENTIFIANT_ROLE_INVALIDE_OU_DUPLIQUE")
        require(type(row["hypothese"]) is str
                and row["hypothese"] in p54e.HYP
                and type(row["statut"]) is str
                and row["statut"] in p54e.STATUS
                and row["contradiction"] in (
                   "NON_EVALUE","QUESTION_OUVERTE",
                   "EXAMEN_CONTRADICTOIRE_REQUIS"),
                "HYPOTHESE_OU_STATUT_NON_ADMIS")
        controls=row["controles_declares"]
        refs=row["pieces_referencees"]
        require(type(controls) is list
                and all(type(s) is str and s in p54e.GATES
                        for s in controls)
                and len(controls)==len(set(controls))
                and type(refs) is list
                and all(type(x) is str and x in proof_ids for x in refs)
                and len(refs)==len(set(refs)),
                "CONTROLES_OU_PIECES_DECLARES_NON_RECEVABLES")
        require(row["avis_independant_signe_valide"] is False
                and row["certification_financiere_autorisee"] is False,
                "ATTESTATION_PROFESSIONNELLE_FICTIVE")
        if row["statut"]=="DOCUMENTE_NON_ATTESTE":
            require(len(controls)>0 and len(refs)>0,
                    "DOCUMENTE_SANS_PREUVE_OU_CONTROLE")
        by_case[case][role]=row
    results=[];counts=Counter();disagreements=0
    checked=sum(len(row["controles_declares"]) for row in rows)
    for cid,rec in by_case.items():
        if not rec:state="EN_ATTENTE"
        elif len(rec)==1:state="EXAMEN_UNIQUE"
        else:
            a,b=rec[ROLES[0]],rec[ROLES[1]]
            if a["code_relecteur"]==b["code_relecteur"]:
                raise ValueError("UNE_PERSONNE_DECLARATIVE_DEUX_ROLES")
            if "SUSPENDU" in (a["statut"],b["statut"]):
                state="SUSPENDU"
            elif (a["hypothese"]!=b["hypothese"]
                  or a["statut"]!=b["statut"]
                  or a["contradiction"]!=b["contradiction"]
                  or a["contradiction"]!="NON_EVALUE"):
                state="DESACCORD"
                disagreements+=1
            elif (a["statut"]=="DOCUMENTE_NON_ATTESTE"
                  and set(a["controles_declares"])==set(p54e.GATES)
                  and set(b["controles_declares"])==set(p54e.GATES)
                  and set(a["pieces_referencees"]) &
                      set(b["pieces_referencees"])):
                state="CONCORDANCE_DECLARATIVE_DOCUMENTEE_NON_ATTESTEE"
            else:
                state="CONCORDANCE_DECLARATIVE_INCOMPLETE"
        counts[state]+=1
        results.append({"dossier_id":cid,"etat_procedural":state,
                        "roles_declares_recus":len(rec),
                        "avis_independant_signe":False,
                        "dossier_certifie":False})
    return {
      "fiches_roles_recues":len(rows),
      "preuves_locales_verifiees_par_sha":len(proof_ids),
      "points_declares_examines":checked,
      "desaccords_documentaires":disagreements,
      "statuts":dict(sorted(counts.items())),
      "dossiers":results,
    }

def validate_local(doc,location,cfg):
    require(type(doc) is dict and set(doc)=={
        "schema_version","p54d_run","sources_sha256",
        "pieces","revues"},
        "FORMAT_REVUE_HORS_GIT_INVALIDE")
    anchors={k:p54e.p54d.p54d.p54b.p54a.COPIES[k][2]
             for k in ("ville","mamh")}
    require(doc["schema_version"]=="P54F-REVUES-1"
            and type(doc["p54d_run"]) is int
            and doc["p54d_run"]==40120462237
            and doc["sources_sha256"]==anchors,
            "ANCRAGE_EDITION_OU_EXERCICE_PERDU")
    ids=verify_proofs(location,doc["pieces"])
    return classify_reviews(doc["revues"],ids,cfg)

def status_initial(cfg):
    rows=[{"dossier_id":cid,"etat_procedural":"EN_ATTENTE",
           "roles_declares_recus":0,"avis_independant_signe":False,
           "dossier_certifie":False} for cid in cfg["dossiers"]]
    return {"fiches_roles_recues":0,"preuves_locales_verifiees_par_sha":0,
            "points_declares_examines":0,"desaccords_documentaires":0,
            "statuts":{"EN_ATTENTE":4},"dossiers":rows}

def summary(cfg,observed=None):
    s=observed if observed is not None else status_initial(cfg)
    require(len(s["dossiers"])==4
            and s["fiches_roles_recues"]<=8,
            "BILAN_REVUE_INCOHERENT")
    return {
      "schema_version":"P54F-BILAN-1",
      "source_p54d_run":40120462237,
      "dossiers_attendus":4,
      "positions_role":8,
      "positions_controle_qualitatif_2_roles":80,
      "declarations_recues":s["fiches_roles_recues"],
      "pieces_locales_integrite_sha_verifiee":
           s["preuves_locales_verifiees_par_sha"],
      "controles_declares_examines_non_attestes":
           s["points_declares_examines"],
      "statuts_de_revues":s["statuts"],
      "dossiers_proceduraux":s["dossiers"],
      "desaccords":s["desaccords_documentaires"],
      "dossiers_clos_et_certifies":0,
      "identites_independantes_authentifiees":0,
      "avis_independants_signes":0,
      "controles_p54e_attestes":0,
      "controles_p54b_restants":96,
      "controles_p54c_restants":8,
      "economies_certifiees_cad":None,
      "emplois_services_reduits_autorises":False,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def private_template(cfg):
    hashes={k:p54e.p54d.p54d.p54b.p54a.COPIES[k][2]
            for k in ("ville","mamh")}
    return {"schema_version":"P54F-REVUES-1",
            "p54d_run":40120462237,
            "sources_sha256":hashes,
            "pieces":[],"revues":[]}

def write_new(path,payload,private=False):
    p=Path(path)
    require(not p.exists() and not p.is_symlink(),"ECRASEMENT_INTERDIT")
    if private:
        require(p.parent.exists() and
                not p.resolve().is_relative_to(ROOT.resolve()),
                "FICHIER_PRIVE_DANS_GIT")
        fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as out:
            json.dump(payload,out,ensure_ascii=False,indent=2,sort_keys=True)
            out.write("\n")
    else:
        with p.open("x",encoding="utf-8") as out:
            json.dump(payload,out,ensure_ascii=False,indent=2,sort_keys=True)
            out.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revues-locales")
    parser.add_argument("--modele-prive")
    parser.add_argument("--bilan")
    parser.add_argument("--exiger-certification",action="store_true")
    opts=parser.parse_args(argv)
    try:
        paths=[Path(v) for v in (opts.modele_prive,opts.bilan) if v]
        require(len({x.resolve() for x in paths})==len(paths)
                and all(not x.exists() and not x.is_symlink() for x in paths),
                "DESTINATIONS_DUPLIQUEES_OU_EXISTANTES")
        cfg=configuration()
        observed=None
        if opts.revues_locales:
            f=private_file(opts.revues_locales,LIMITS["taille_fiche_max_octets"])
            require(all(f.resolve()!=out.resolve() for out in paths),
                    "ENTREE_ET_SORTIE_MEME_CHEMIN")
            doc=json.loads(f.read_text("utf-8"))
            observed=validate_local(doc,f,cfg)
        result=summary(cfg,observed)
        if opts.modele_prive:
            write_new(opts.modele_prive,private_template(cfg),private=True)
        if opts.bilan:write_new(opts.bilan,result)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if opts.exiger_certification else 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,
            json.JSONDecodeError) as e:
        print("P54F_REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
