#!/usr/bin/env python3
"""P53T — Concordance locale des octets; jamais preuve d'authenticité ni économie."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys

import suivre_demandes_acces_nova_p53s as p53s
import inventorier_pieces_primaires_nova_p53q as p53q

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets"/"projet-nova"/"etudes"/"P53T_PROTOCOLE_INTEGRITE_PROVENANCE.json"
NO_GO="NO_GO_AUTOMATIQUE"
CODE=tuple(p53s.p53r.CODES)
ROLE=("COLLECTE_DOCUMENTAIRE","CONTROLE_TECHNIQUE","EXAMEN_JURIDIQUE","REVUE_INDEPENDANTE")
ACT=("RECEPTION","COPIE_CONTROLEE","CONSULTATION","TRANSFERT")
TYPES=("PIECE_FINANCIERE","TRACE_TRANSMISSION","ETAT_FINANCIER","PIECE_SERVICES_EMPLOIS")
STATUTS=("NON_PRESENTE","CONCORDANCE_OCTETS_LOCAUX_NON_AUTHENTIFICATION",
         "ECHEC_CONTROLE_OCTETS","ACCES_RESTREINT_NON_TRAITE")
SHA=re.compile(r"^[0-9a-f]{64}$")
CLOCK=re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
ENTREE={"code_organisme","type_piece","categorie_justificatif",
        "fichier_relatif","sha256_reference",
        "date_capture_declaree_utc","role_collecte","role_relecture",
        "droits_acces","origine_declaree","journal_declare"}
EVENT={"action","role","date_utc","but"}
BUT=("RECEPTION","COPIE","CONTROLE","TRANSMISSION")
MAX_FILE=4*1024*1024

def require(cond,why):
    if not cond:raise ValueError(why)

def read_json(path,limit=95000):
    p=Path(path)
    require(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=limit,
            "SOURCE_INDISPONIBLE")
    doc=json.loads(p.read_text("utf-8"))
    require(type(doc) is dict,"OBJET_JSON_ATTENDU")
    return doc

def setup():
    p53s_cfg,p53s_dossiers=p53s.sources()
    q_cfg,q_dossiers=p53q.sources()
    cfg=read_json(CONFIG)
    check={
      "schema_version":"P53T-1","jalon":"P53T",
      "date_reference":"2026-10-22",
      "statut":"PROTOCOLE_INTEGRITE_LOCALE_SANS_AUTHENTIFICATION",
      "exercice_reference":2024,
      "codes":list(CODE),
      "positions_par_dossier":17,
      "types_justificatifs":list(TYPES),
      "roles":list(ROLE),
      "operations":list(ACT),
      "statuts":list(STATUTS),
      "standards":[
        "https://csrc.nist.gov/glossary/term/chain_of_custody",
        "https://nvlpubs.nist.gov/nistpubs/ir/2022/NIST.IR.8387.pdf",
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-175Br1.pdf"],
      "verrous":{
        "aucun_original_ni_montant_en_sortie":True,
        "controles_sur_fichiers_locaux_explicitement_fournis":True,
        "aucune_connexion_reseau":True,
        "chemins_de_traversee_et_symlinks_refuses":True,
        "documents_restraints_non_lus":True,
        "hash_seul_ne_prouve_pas_provenance":True,
        "declaration_roles_journal_non_signes":True,
        "horodatage_declare_n_est_pas_preuve":True,
        "pieces_de_six_organismes_non_equivalentes_economies":True,
        "controle_double_elimination_quebec_rtc":True,
        "garanties_emplois_et_services":True,
        "pas_d_economie_certifiee":True,
        "aucune_fusion_automatique":True,
      },
      "etat_initial":{
        "dossiers":6,"slots":102,
        "originaux_obtenus_par_le_projet":0,
        "attestations_provenance_signees":0,
        "controles_humains_independants_valides":0,
        "economies_certifiees_cad":None,
        "decision":NO_GO,
      },
    }
    require(cfg==check,"CADRE_P53T_MODIFIE")
    require(len(q_dossiers)==6 and len(q_cfg["types_pieces"])==17
            and len(p53s_dossiers)==6
            and p53s_cfg["etat_initial"]["evenements_authentifies"]==0
            and len(p53q.registre(q_cfg,q_dossiers))==102,
            "CHAINAGE_P53Q_P53S_NON_RECONCILIE")
    return cfg,q_cfg,q_dossiers

def inventory(q_cfg,q_dossiers):
    rows=p53q.registre(q_cfg,q_dossiers)
    result=[]
    for r in rows:
        result.append({
          "code_organisme":r["code_organisme"],
          "type_piece":r["type_piece"],
          "exercice":2024,
          "priorite":r["priorite_locale"],
          "statut":"NON_PRESENTE",
          "empreinte_locale_verifiee":False,
          "provenance_authentifiee":False,
          "independance_revue_validee":False,
          "piece_confidentielle_dans_git":False,
          "economie_certifiee_cad":None,
          "controles_requis":[
              "DETECTION_OCTETS","AUTORITE_EMETTRICE",
              "PREUVE_DE_COMMUNICATION","TRACABILITE_TRANSFERTS",
              "CONTROLE_INDEPENDANT","CONTROLE_DOUBLE_COMPTE",
              "MAINTIEN_EMPLOIS_ET_SERVICES",
          ],
        })
    require(len(result)==102
            and len({(r["code_organisme"],r["type_piece"]) for r in result})==102
            and all(r["statut"]=="NON_PRESENTE" for r in result),
            "INVENTAIRE_INCOMPLET")
    return result

def instant(value):
    require(type(value) is str and CLOCK.fullmatch(value) is not None,
            "HORODATAGE_UTC_INVALIDE")
    dt=datetime.strptime(value,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    require(datetime(2024,1,1,tzinfo=timezone.utc)<=dt,
            "HORODATAGE_ANTERIEUR_EXERCICE")
    return dt

def relative_file(rel):
    require(type(rel) is str and rel and len(rel)<=128 and
            "\\" not in rel and ":" not in rel and
            not rel.startswith("/") and
            re.fullmatch(r"[a-zA-Z0-9_\-./]+",rel) is not None,
            "CHEMIN_INTERDIT")
    path=PurePosixPath(rel)
    require(all(part not in ("..",".","") and not part.startswith(".")
                for part in path.parts) and 1<=len(path.parts)<=4
            and path.suffix.lower() in (".txt",".csv",".json",".pdf",".xml"),
            "CHEMIN_INVALIDE")
    return path

def metadata(item):
    """Format et ordre déclaratifs uniquement; aucune signature cryptographique vérifiée."""
    require(type(item) is dict and set(item)==ENTREE,"MANIFESTE_NON_CONFORME")
    require(type(item["code_organisme"]) is str and item["code_organisme"] in CODE
            and type(item["type_piece"]) is str and item["type_piece"] in p53q.DOCUMENTS
            and item["categorie_justificatif"] in TYPES,
            "PIECE_INCONNUE")
    relative_file(item["fichier_relatif"])
    require(type(item["sha256_reference"]) is str
            and SHA.fullmatch(item["sha256_reference"]) is not None,
            "EMPREINTE_SHA256_INVALIDE")
    dt=instant(item["date_capture_declaree_utc"])
    require(item["origine_declaree"] in ("OFFICIELLE_DECLAREE_NON_AUTHENTIFIEE",
                                        "COMMUNIQUEE_DECLAREE_NON_AUTHENTIFIEE",
                                        "INCONNUE"),
            "ORIGINE_AUTOMATIQUEMENT_CERTIFIEE_INTERDITE")
    require(item["droits_acces"] in ("PUBLIC","RESTREINT","A_VERIFIER"),
            "ACCES_INCONNU")
    a,b=item["role_collecte"],item["role_relecture"]
    require(a in ROLE and b in ROLE and a!=b,"INDEPENDANCE_ROLES_DECLARATIFS_NON_CONFORME")
    log=item["journal_declare"]
    require(type(log) is list and 1<=len(log)<=6,"JOURNAL_ABSENT")
    prev=None
    for i,event in enumerate(log):
        require(type(event) is dict and set(event)==EVENT
                and event["action"] in ACT and
                event["role"] in ROLE and
                event["but"] in BUT,
                "ENTREE_JOURNAL_NON_CONFORME")
        timestamp=instant(event["date_utc"])
        require(prev is None or timestamp>=prev,
                "TRANSFERTS_DECLARÉS_HORS_ORDRE")
        prev=timestamp
        if i==0:
            require(event["action"]=="RECEPTION" and
                    event["role"]==a and timestamp==dt
                    and event["but"]=="RECEPTION",
                    "RECEPTION_INITIALE_MANQUANTE")
    require(any(t["role"]==b and t["action"]=="CONSULTATION"
                and t["but"]=="CONTROLE" for t in log),
            "REVUE_DECLAREE_SEPAREE_MANQUANTE")
    return (item["code_organisme"],item["type_piece"])

def resolve_local(root,relative):
    base=Path(root)
    require(base.is_dir() and not base.is_symlink(),
            "DOSSIER_PREUVE_ABSENT_OU_LIEN")
    rel=relative_file(relative)
    candidate=base
    for part in rel.parts:
        candidate=candidate / part
        require(not candidate.is_symlink(),"SYMLINK_DOCUMENT_INTERDIT")
    require(candidate.resolve().is_relative_to(base.resolve()),
            "HORS_RACINE_INTERDIT")
    mode=candidate.stat().st_mode
    require(stat.S_ISREG(mode) and 0<candidate.stat().st_size<=MAX_FILE,
            "DOCUMENT_NON_REGULIER_OU_TROP_GRAND")
    return candidate

def check_local(root,records):
    seen=set();statuses=Counter()
    for item in records:
        key=metadata(item)
        require(key not in seen,"DOUBLON_PIECE_ET_ORGANISME")
        seen.add(key)
        # A restricted file is never opened, even when explicitly named.
        if item["droits_acces"]=="RESTREINT":
            statuses["ACCES_RESTREINT_NON_TRAITE"]+=1
            continue
        file=resolve_local(root,item["fichier_relatif"])
        hash_=hashlib.sha256()
        with file.open("rb") as source:
            for chunk in iter(lambda: source.read(65536),b""):
                hash_.update(chunk)
        status=("CONCORDANCE_OCTETS_LOCAUX_NON_AUTHENTIFICATION"
                if hash_.hexdigest()==item["sha256_reference"]
                else "ECHEC_CONTROLE_OCTETS")
        statuses[status]+=1
    return {"enregistrements_exam":len(records),
            "pieces_uniques_declares":len(seen),
            "statuts_techniques":dict(sorted(statuses.items())),
            "authentifications_provenance":0,"attestations_humaines_validees":0}

def result(cfg,rows,control):
    return {
      "schema_version":"P53T-RAPPORT-1",
      "dossiers":6,"positions_p53q":len(rows),
      "enregistrements_locaux_examines":control["enregistrements_exam"],
      "statuts_techniques_agreges":control["statuts_techniques"],
      "preuves_origine_certifiees":0,
      "signatures_emetteurs_verifiees":0,
      "revues_independantes_certifiees":0,
      "authentifications_factures_grands_livres":0,
      "documents_financiers_2024_certifies":0,
      "demandes_externes_envoyees":0,
      "echeances_legales_validees":0,
      "economie_operationnelle_certifiee_cad":None,
      "evaluations_F01_F20_validees":0,
      "variables_financieres_Nova_inconnues":1320,
      "degradations_emplois_services_autorisees":False,
      "fusion_autorisee":False,
      "decision":NO_GO,
    }

def save(path,data):
    p=Path(path)
    require(not p.exists() and not p.is_symlink(),"ECRASEMENT_REFUSE")
    with p.open("x",encoding="utf-8") as stream:
        stream.write(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)+"\n")

def main(argv=None):
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--bilan")
    cli.add_argument("--inventaire")
    cli.add_argument("--manifeste")
    cli.add_argument("--racine-preuves")
    cli.add_argument("--exiger-authentification-ou-economie",action="store_true")
    args=cli.parse_args(argv)
    try:
        require(bool(args.manifeste)==bool(args.racine_preuves),
                "MANIFESTE_ET_RACINE_INSEPARABLES")
        outputs=[Path(x) for x in (args.bilan,args.inventaire) if x]
        require(len({p.resolve() for p in outputs})==len(outputs)
                and all(not p.exists() and not p.is_symlink() for p in outputs),
                "SORTIE_EXISTANTE_OU_DUPLIQUEE")
        cfg,q_cfg,dossiers=setup()
        rows=inventory(q_cfg,dossiers)
        inspected={"enregistrements_exam":0,"statuts_techniques":{}}
        if args.manifeste:
            local=read_json(args.manifeste)
            require(set(local)=={"schema_version","pieces"} and
                    local["schema_version"]=="P53T-MANIFESTE-1"
                    and type(local["pieces"]) is list and
                    len(local["pieces"])<=102,
                    "FORMAT_MANIFESTE_INVALIDE")
            inspected=check_local(args.racine_preuves,local["pieces"])
        report=result(cfg,rows,inspected)
        if args.bilan:save(args.bilan,report)
        if args.inventaire:save(args.inventaire,{
            "schema_version":"P53T-INVENTAIRE-1",
            "statut":"PREPARATOIRE_DOCUMENTS_NON_OBTENUS",
            "positions":rows})
        print(json.dumps(report,sort_keys=True,ensure_ascii=False))
        return 3 if args.exiger_authentification_ou_economie else 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError,
            json.JSONDecodeError) as err:
        print("P53T_REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
