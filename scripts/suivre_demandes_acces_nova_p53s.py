#!/usr/bin/env python3
"""P53S — Suivi *déclaratif* des dossiers d'accès; zéro événement authentifié."""
import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
import sys

import preparer_demandes_acces_nova_p53r as p53r

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"projets"/"projet-nova"/"etudes"/"P53S_REGISTRE_SUIVI_ET_RECOURS.json"
NO_GO="NO_GO_AUTOMATIQUE"

TYPES=(
 "PREPARATION_SANS_DEPOT","IDENTIFICATION_RESPONSABLE_DECLAREE",
 "ENVOI_DECLARE_NON_VERIFIE","RECEPTION_DECLAREE_NON_VERIFIEE",
 "PROLONGATION_DECLAREE_NON_VERIFIEE",
 "REPONSE_PARTIELLE_DECLAREE_NON_VERIFIEE",
 "REPONSE_COMPLETE_DECLAREE_NON_VERIFIEE",
 "REFUS_DECLARE_NON_VERIFIE","SILENCE_DECLARE_SANS_DELAI_VERIFIE",
 "RECOURS_DECLARE_NON_VERIFIE","ARCHIVAGE_DECLARE_NON_VERIFIE",
)
CLASSES={
 "PREPARATION_SANS_DEPOT":"AUCUN",
 "IDENTIFICATION_RESPONSABLE_DECLAREE":"PUBLICATION_PROCEDURE",
 "ENVOI_DECLARE_NON_VERIFIE":"TRACE_ENVOI",
 "RECEPTION_DECLAREE_NON_VERIFIEE":"ACCUSE_RECEPTION",
 "PROLONGATION_DECLAREE_NON_VERIFIEE":"AVIS_PROLONGATION",
 "REPONSE_PARTIELLE_DECLAREE_NON_VERIFIEE":"DECISION_COMMUNICATION",
 "REPONSE_COMPLETE_DECLAREE_NON_VERIFIEE":"DECISION_COMMUNICATION",
 "REFUS_DECLARE_NON_VERIFIE":"DECISION_REFUS",
 "SILENCE_DECLARE_SANS_DELAI_VERIFIE":"CONSTAT_MANUEL_NON_VALIDÉ",
 "RECOURS_DECLARE_NON_VERIFIE":"PREUVE_RECOURS",
 "ARCHIVAGE_DECLARE_NON_VERIFIE":"BORDEREAU_ARCHIVAGE",
}
PREALABLES={
 "PREPARATION_SANS_DEPOT":(),
 "IDENTIFICATION_RESPONSABLE_DECLAREE":("PREPARATION_SANS_DEPOT",),
 "ENVOI_DECLARE_NON_VERIFIE":("IDENTIFICATION_RESPONSABLE_DECLAREE",),
 "RECEPTION_DECLAREE_NON_VERIFIEE":("ENVOI_DECLARE_NON_VERIFIE",),
 "PROLONGATION_DECLAREE_NON_VERIFIEE":("RECEPTION_DECLAREE_NON_VERIFIEE",),
 "REPONSE_PARTIELLE_DECLAREE_NON_VERIFIEE":("RECEPTION_DECLAREE_NON_VERIFIEE",),
 "REPONSE_COMPLETE_DECLAREE_NON_VERIFIEE":("RECEPTION_DECLAREE_NON_VERIFIEE",),
 "REFUS_DECLARE_NON_VERIFIE":("RECEPTION_DECLAREE_NON_VERIFIEE",),
 "SILENCE_DECLARE_SANS_DELAI_VERIFIE":("RECEPTION_DECLAREE_NON_VERIFIEE",),
 "RECOURS_DECLARE_NON_VERIFIE":(
    "REPONSE_PARTIELLE_DECLAREE_NON_VERIFIEE",
    "REPONSE_COMPLETE_DECLAREE_NON_VERIFIEE",
    "REFUS_DECLARE_NON_VERIFIE",
    "SILENCE_DECLARE_SANS_DELAI_VERIFIE",
 ),
 "ARCHIVAGE_DECLARE_NON_VERIFIE":(
    "REPONSE_PARTIELLE_DECLAREE_NON_VERIFIEE",
    "REPONSE_COMPLETE_DECLAREE_NON_VERIFIEE",
    "REFUS_DECLARE_NON_VERIFIE",
    "RECOURS_DECLARE_NON_VERIFIE",
 ),
}
GUARDS={
 "aucune_transmission_par_le_programme",
 "preuve_hors_git_obligatoire_pour_actes_declares",
 "empreinte_sha256_n_est_pas_authentification",
 "ordre_et_dates_declares_ne_certifient_pas_evenements",
 "aucune_date_limite_legale_depuis_metadonnees_non_validees",
 "recours_pas_declenche_sans_examen_juridique",
 "aucun_renseignement_personnel_en_sortie",
 "documents_originaux_jamais_dans_git",
 "maintien_emploi_et_services",
 "consolidation_quebec_rtc_protegee",
 "deux_regimes_nons_additifs",
 "aucune_fusion_automatique",
}
INPUT={
 "schema_version","code_organisme","phase","date_declaree",
 "classe_justificatif","reference_conservation_externe_presente",
 "empreinte_sha256_declaree","examen_humain","droit_acces",
 "protections_emplois_services",
}
HASH=re.compile(r"^[0-9a-f]{64}$")
DATE=re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

def require(ok,raison):
    if not ok:
        raise ValueError(raison)

def load_json(path,limit=45000):
    p=Path(path)
    require(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=limit,
            "FICHIER_INDISPONIBLE")
    obj=json.loads(p.read_text(encoding="utf-8"))
    require(type(obj) is dict,"OBJET_JSON_ATTENDU")
    return obj

def sources():
    prior,parents=p53r.sources()
    previous=p53r.generate(prior,parents)
    cfg=load_json(CFG)
    require(cfg["schema_version"]=="P53S-1"
            and cfg["statut"]=="REGISTRE_DECLARATIF_SANS_EVENEMENT_AUTHENTIFIE"
            and cfg["date_reference"]=="2026-10-22"
            and cfg["exercice_documentaire"]==2024
            and cfg["codes"]==list(p53r.CODES)
            and cfg["phases"]==list(TYPES)
            and cfg["justificatif_attendu_par_phase"]==CLASSES
            and cfg["prerequis_par_phase"]=={k:list(v) for k,v in PREALABLES.items()}
            and cfg["base_legale"]=={
                "loi":"https://www.legisquebec.gouv.qc.ca/fr/document/lc/A-2.1",
                "info":"https://www.cai.gouv.qc.ca/acces-documents-organismes-publics/citoyens-acces-documents-publics/comment-acceder-documents-organismes-publics",
                "delai_initial_jours_civils":20,
                "prolongation_max_jours":10,
                "recours_indicatif_jours":30,
                "debut_compte_a_la_reception_reelle":True,
            }
            and set(cfg["verrous"])==GUARDS
            and all(v is True for v in cfg["verrous"].values())
            and cfg["etat_initial"]=={
                "dossiers":6,"projets_lettres_p53r":6,
                "descriptions_ciblees_p53r":18,"positions_suivi":66,
                "evenements_declares":0,"evenements_authentifies":0,
                "envois_verifies":0,"receptions_verifiees":0,
                "recours_verifies":0,"avis_independants_signes":0,
                "economie_certifiee_cad":None,"decision":NO_GO,
            }
            and len(previous)==6
            and sum(len(x["type_pieces_recherchees"]) for x in previous)==18
            and all(x["date_depot_reel"] is None and
                    x["preuves_recues_authentifiees"]==0 for x in previous),
            "CHAINAGE_JURIDIQUE_P53R_INCOHERENT")
    return cfg,previous

def plan(cfg,previous):
    ret=[]
    for draft in previous:
        code=draft["code_organisme"]
        ret.append({
            "code_organisme":code,
            "organisme":draft["organisme"],
            "statut_reel":"AUCUNE_DEMANDE_EFFECTIVEMENT_ENVOYEE",
            "lien_procedure":draft["page_officielle_procedure"],
            "documents_recherches":[x for x in draft["type_pieces_recherchees"]],
            "evenements_a_tracer":[
                {"phase":event,"justificatif":CLASSES[event],
                 "statut":"AUCUNE_PREUVE_OBTENUE",
                 "date_certifiee":None,"document_original_authentifie":False}
                for event in TYPES
            ],
            "date_reception_reelle":None,
            "echeance_reponse_reelle":None,
            "date_ouverture_recours_reelle":None,
            "etat_pieces_2024":"NON_OBTENUES",
            "gestion_confidentielle":"DOCUMENTS_ET_JUSTIFICATIFS_HORS_GIT",
            "preuve_consolidation_quebec_rtc":(
                "A_RAPPROCHER_SANS_DOUBLE_ELIMINATION"
                if code in ("23027","T0088") else "NON_ETABLIE"),
            "sauvegarde_emplois_et_services":"OBLIGATOIRE",
            "economie_certifiee_cad":None,
            "decision":NO_GO,
        })
    require(len(ret)==6 and
            sum(len(x["evenements_a_tracer"]) for x in ret)==66,
            "PLAN_DE_SUIVI_INCOMPLET")
    return ret

def validate_event(raw):
    """Validation de métadonnées déclarées, sans audit de la preuve externe."""
    require(type(raw) is dict and set(raw)==INPUT
            and raw.get("schema_version")=="P53S-EVENEMENT-1",
            "ENTREE_NON_CONFORME")
    code=raw["code_organisme"];typ=raw["phase"]
    require(type(code) is str and code in p53r.CODES
            and type(typ) is str and typ in TYPES,
            "ORGANISME_OU_PHASE_INCONNU")
    require(raw["classe_justificatif"]==CLASSES[typ],
            "CLASSE_PREUVE_INCOHERENTE")
    declared=raw["date_declaree"]
    if declared is not None:
        require(type(declared) is str and DATE.fullmatch(declared) is not None,
                "DATE_DECLARATIVE_INVALIDE")
        datevalue=date.fromisoformat(declared)
        require(date(2024,1,1)<=datevalue,
                "DATE_AVANT_EXERCICE_D_ETUDE")
    else:
        datevalue=None
    require(type(raw["reference_conservation_externe_presente"]) is bool,
            "PRESENCE_PREUVE_BOOL_ATTENDU")
    digest=raw["empreinte_sha256_declaree"]
    require(digest is None or
            (type(digest) is str and HASH.fullmatch(digest) is not None),
            "EMPREINTE_NON_SHA256")
    require(raw["examen_humain"] in ("NON_EFFECTUE","DECLARE_NON_AUTHENTIFIE"),
            "EXAMEN_CERTIFIE_NON_AUTORISE")
    require(raw["droit_acces"] in ("INCONNU","POTENTIEL_NON_VERIFIE","NON_AUTORISE"),
            "BASE_JURIDIQUE_NON_DOCUMENTEE")
    require(raw["protections_emplois_services"] in (
        "INCONNU","DECLAREES_NON_AUTHENTIFIEES","RISQUE_SIGNALE"),
        "PROTECTIONS_CERTIFIEES_INTERDITES")
    if typ=="PREPARATION_SANS_DEPOT":
        require(datevalue is None and digest is None and
                raw["reference_conservation_externe_presente"] is False,
                "FAUSSE_PREUVE_DE_DEPOT")
    elif typ=="IDENTIFICATION_RESPONSABLE_DECLAREE":
        require(digest is None,"PREUVE_IDENTITE_NON_AUTHENTIFIEE")
    else:
        require(datevalue is not None and digest is not None
                and raw["reference_conservation_externe_presente"] is True,
                "PREUVE_EXTERNE_DECLARATIVE_MANQUANTE")
    return {"code":code,"phase":typ,"date":datevalue,
            "arret":raw["droit_acces"]=="NON_AUTORISE" or
                     raw["protections_emplois_services"]=="RISQUE_SIGNALE"}

def inspect_events(raw_events):
    """Impose la cohérence d'ordre, sans jamais valider un envoi ou une réception."""
    past={}
    last={}
    stops=set()
    count=Counter()
    for item in raw_events:
        e=validate_event(item)
        code=e["code"];stage=e["phase"]
        already=past.setdefault(code,set())
        require(stage not in already,"ETAPE_DECLARATIVE_DUPLIQUEE")
        requirements=PREALABLES[stage]
        if requirements:
            if stage in ("RECOURS_DECLARE_NON_VERIFIE",
                         "ARCHIVAGE_DECLARE_NON_VERIFIE"):
                require(any(r in already for r in requirements),
                        "PREALABLE_RECOURS_OU_ARCHIVAGE_ABSENT")
            else:
                require(all(r in already for r in requirements),
                        "ETAPE_PRECEDENTE_NON_DECLARÉE")
        require(code not in stops or e["arret"],
                "AVANCEMENT_APRES_ARRET")
        if e["date"] is not None and last.get(code) is not None:
            require(e["date"]>=last[code],"CHRONOLOGIE_INVERSE")
        if e["date"] is not None:
            last[code]=e["date"]
        if e["arret"]:
            stops.add(code)
        already.add(stage)
        count["ARRET_DECLARE_NON_VERIFIE" if e["arret"]
              else "ETAPE_DECLAREE_NON_AUTHENTIFIEE"]+=1
    return {"evenements_examines":len(raw_events),
            "organismes_avec_declarations":len(past),
            "statuts_agreges":dict(sorted(count.items()))}

def bilan(cfg,plan_data,stats):
    return {
        "schema_version":"P53S-RAPPORT-1",
        "exercice_source":2024,
        "dossiers":len(plan_data),
        "positions_de_suivi":sum(len(x["evenements_a_tracer"]) for x in plan_data),
        "projets_de_demandes_non_envoyes":6,
        "descriptions_de_pieces_p53r":18,
        "emplacements_p53q_non_obtenus":102,
        "evenements_declares_non_authentifies":stats["evenements_examines"],
        "organismes_avec_declarations":stats["organismes_avec_declarations"],
        "statuts_agreges":stats["statuts_agreges"],
        "demandes_reellement_envoyees_verifiees":0,
        "accuses_reception_authentifies":0,
        "reponses_authentifiees":0,
        "refus_authentifies":0,
        "recours_reellement_deposes_verifies":0,
        "documents_originaux_authentifies":0,
        "empreinte_sha256_constitue_preuve_authenticite":False,
        "delais_legaux_declenches":0,
        "echeances_reponse_calculables":0,
        "echeances_recours_calculables":0,
        "avis_independants_valides":0,
        "economies_certifiees_cad":None,
        "preuves_F01_F20_validees":0,
        "montants_Nova_inconnus":1320,
        "diminution_emplois_autorisee":False,
        "degradation_services_autorisee":False,
        "fusion_autorisee":False,
        "decision":NO_GO,
    }

def write_new(path,obj):
    p=Path(path)
    require(not p.exists() and not p.is_symlink(),
            "SORTIE_EXISTANTE_NON_ECRASEE")
    with p.open("x",encoding="utf-8") as stream:
        stream.write(json.dumps(obj,sort_keys=True,ensure_ascii=False,indent=2)+"\n")

def main(args=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bilan")
    ap.add_argument("--registre")
    ap.add_argument("--evenement",action="append",default=[])
    ap.add_argument("--exiger-envoi-ou-reception-verifie",action="store_true")
    x=ap.parse_args(args)
    try:
        require(len(x.evenement)<=66,"TROP_D_EVENEMENTS")
        outputs=[Path(p) for p in (x.bilan,x.registre) if p]
        require(len({p.resolve() for p in outputs})==len(outputs),
                "DESTINATIONS_IDENTIQUES")
        require(all(not p.exists() and not p.is_symlink() for p in outputs),
                "SORTIE_DEJA_PRESENTE")
        cfg,previous=sources()
        planned=plan(cfg,previous)
        statements=[load_json(p) for p in x.evenement]
        inspected=inspect_events(statements)
        report=bilan(cfg,planned,inspected)
        if x.bilan:
            write_new(x.bilan,report)
        if x.registre:
            write_new(x.registre,{"schema_version":"P53S-REGISTRE-1",
                   "statut":"SANS_DEMANDE_REELLEMENT_DEPOSEE",
                   "dossiers":planned})
        print(json.dumps(report,sort_keys=True,ensure_ascii=False))
        return 3 if x.exiger_envoi_ou_reception_verifie else 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P53S_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
