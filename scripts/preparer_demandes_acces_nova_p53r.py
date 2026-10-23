#!/usr/bin/env python3
"""P53R: six projets de demandes d'accès à réviser, aucun envoi et aucune certification."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import inventorier_pieces_primaires_nova_p53q as p53q

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"projets"/"projet-nova"/"etudes"/"P53R_PROJETS_DEMANDES_ACCES_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
CODES=p53q.precedent.CODES
ACCESS={
 "66023":("VILLE_DE_MONTREAL","https://montreal.ca/services/acces-linformation"),
 "T1025":("ARTM","https://www.artm.quebec/a-propos-de-l-artm/acces-aux-documents-et-protection-des-renseignements-personnels/"),
 "23027":("VILLE_DE_QUEBEC","https://www.ville.quebec.qc.ca/apropos/acces-information/demande.aspx"),
 "T0081":("STM","https://www.stm.info/fr/a-propos/gouvernance-d-entreprise/acces-linformation"),
 "T0088":("RTC","https://www.rtcquebec.ca/propos/gouvernance/acces-linformation"),
 "39135":("SAINT_VALERE","https://www.msvalere.qc.ca/acces-linformation"),
}
FIRST=p53q.FIRST
PERMITTED_REVIEW={
 "NON_EXAMINE","VERIFICATION_DECLARATIVE_NON_AUTHENTIFIEE"
}
DECISION_KEYS={
 "schema_version","code_organisme","procedure_responsable",
 "reperage_public_preexistant","precision_documents",
 "confidentialite_tiers","perimetre_juridique","services_et_emplois",
 "autorisation_envoi"
}

def require(ok,msg):
    if not ok:
        raise ValueError(msg)

def read(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink()
            and 0<p.stat().st_size<=45000,"FICHIER_SOURCE_INVALIDE")
    raw=json.loads(p.read_text(encoding="utf-8"))
    require(type(raw) is dict,"OBJET_JSON_ATTENDU")
    return raw

def sources():
    _,parents=p53q.sources()
    cfg=read(SOURCE)
    require(cfg["schema_version"]=="P53R-1"
            and cfg["statut"]=="SIX_PROJETS_DE_DEMANDES_NON_TRANSMISES"
            and cfg["date_reference"]=="2026-10-22"
            and cfg["exercice"]==2024
            and cfg["cadre_juridique"]=="QUEBEC_ACTUEL_LOI_A_2_1"
            and cfg["reference_legale"]=="https://www.legisquebec.gouv.qc.ca/fr/document/lc/A-2.1"
            and cfg["reference_cai"]=="https://www.cai.gouv.qc.ca/acces-documents-organismes-publics/citoyens-acces-documents-publics/comment-acceder-documents-organismes-publics"
            and cfg["codes"]==list(CODES)
            and set(cfg["destinations"])==set(CODES)
            and set(cfg["demandes_par_code"])==set(CODES),
            "SOURCE_ET_REGLES_INCOHERENTES")
    for code in CODES:
        dest=cfg["destinations"][code]
        label,url=ACCESS[code]
        require(type(dest) is dict and dest=={
            "identifiant":label,
            "page_procedure":url,
            "identite_responsable_personnellement_verifiee":False,
        },"DESTINATAIRE_NON_VERIFIE")
        requests=cfg["demandes_par_code"][code]
        require(type(requests) is list and len(requests)==3
                and all(type(v) is dict and set(v)=={"type_piece","description"}
                        for v in requests)
                and {v["type_piece"] for v in requests}.issubset(set(p53q.DOCUMENTS))
                and requests[0]["type_piece"]==FIRST[code]
                and len({v["type_piece"] for v in requests})==3
                and all(type(v["description"]) is str
                        and 45<=len(v["description"])<=420
                        and "2024" in v["description"]
                        for v in requests),
                "DEMANDE_NON_CIBLEE")
    require(set(cfg["verrous"])=={
        "absence_envoi_reseau","absence_avis_d_envoi",
        "aucune_coordonnees_personnelles_publiquees",
        "demander_documents_existants_non_analyse_nouvelle",
        "droit_acces_et_tiers_a_examiner",
        "caviardage_et_frais_eventuels",
        "delai_court_apres_reception_effective",
        "separation_competences_organismes",
        "aucun_gain_financier_certifie",
        "consolidation_quebec_rtc_protegee",
        "travailleurs_et_services_proteges",
        "aucune_fusion_automatique"}
        and all(v is True for v in cfg["verrous"].values())
        and cfg["etat_initial"]=={
            "projets_de_demandes":6,
            "documents_decrits":18,
            "organismes_procedures_identifiees":6,
            "demandes_envoyees":0,
            "reponses_reçues_et_verifiees":0,
            "originals_transactionnels_authentifies":0,
            "economies_certifiees_cad":None,
            "decision":NO_GO,
        },"GARDE_FOUS_P53R_INVALIDES")
    require(len(parents)==6
            and len(p53q.registre(None,parents))==102
            and all(d["economie_budgetaire_certifiee_cad"] is None
                    for d in parents),
            "CHAINAGE_P53Q_NON_VERIFIE")
    return cfg,parents

def generate(cfg,parents):
    by={x["code_organisme"]:x for x in parents}
    results=[]
    for code in CODES:
        p=by[code]
        dest=cfg["destinations"][code]
        req=cfg["demandes_par_code"][code]
        # These are *drafts*: no requester details, signature, dates or address.
        lines=[
            "PROJET DE DEMANDE — NE PAS TRANSMETTRE SANS REVUE HUMAINE",
            "Destinataire pressenti : responsable de l'accès aux documents — "+p["nom_organisme"],
            "Objet : demande écrite d'accès à des documents existants — exercice 2024",
            "",
            "Madame, Monsieur,",
            "",
            "Je souhaite obtenir, dans la mesure où votre organisme les détient et où la loi permet leur communication, les documents existants ci-dessous pour l'exercice du 1er janvier au 31 décembre 2024 :",
        ]
        for i,item in enumerate(req,1):
            lines.append(str(i)+". "+item["description"])
        lines.extend([
            "",
            "Merci de préciser, lorsque possible, les versions ou annexes concernées. Si un document est déjà diffusé, une référence à sa publication suffira.",
            "Dans la mesure où un document contient des renseignements protégés, je sollicite la communication de la partie accessible après les retraits légalement requis.",
            "Si le document n'est pas détenu par votre organisme, merci de le préciser et, selon les obligations applicables, d'indiquer l'organisme compétent.",
            "Cette demande vise des documents existants; elle ne requiert aucun nouveau calcul, rapprochement ou rapport à produire.",
            "Merci de me signaler au préalable les frais de reproduction ou de transmission applicables.",
            "",
            "[Nom et coordonnées du demandeur à ajouter hors dépôt public avant tout envoi]",
            "[Signature et date à ajouter après validation]",
            "",
            "FIN DU PROJET — NON ENVOYE",
        ])
        results.append({
            "code_organisme":code,
            "organisme":p["nom_organisme"],
            "statut":"PROJET_NON_TRANSMIS",
            "page_officielle_procedure":dest["page_procedure"],
            "destinataire_nominatif":None,
            "adresse_personnelle_demandeur":None,
            "signature":None,
            "date_depot_reel":None,
            "debut_delai_reponse":None,
            "type_pieces_recherchees":[r["type_piece"] for r in req],
            "courrier_modele":"\n".join(lines)+"\n",
            "condition_envoi":"VERIFICATION_MANUELLE_RESPONSABLE_ACCES_PUBLICATION_TIERS_IDENTITE",
            "preuves_recues_authentifiees":0,
            "economies_certifiees_cad":None,
            "decision":NO_GO,
        })
    require(len(results)==6 and
            len({x["code_organisme"] for x in results})==6
            and all(x["date_depot_reel"] is None and
                    x["debut_delai_reponse"] is None and
                    x["destinataire_nominatif"] is None
                    for x in results),
            "SORTIES_NON_CONFORMES")
    return results

def review(d):
    """No action of this function can authorize transmission."""
    require(type(d) is dict and set(d)==DECISION_KEYS
            and d.get("schema_version")=="P53R-REVUE-1",
            "FORMAT_REVUE_INVALIDE")
    code=d["code_organisme"]
    require(type(code) is str and code in CODES,"ORGANISME_NON_RETENU")
    for k in ("procedure_responsable","reperage_public_preexistant",
              "precision_documents","confidentialite_tiers",
              "perimetre_juridique","services_et_emplois"):
        require(type(d[k]) is str and d[k] in PERMITTED_REVIEW|{"BLOCAGE_SIGNALE"},
                "VALIDATION_NON_PROUVEE_INTERDITE")
    # Hard block: this programme never receives an authorisation to send.
    require(d["autorisation_envoi"] is False,"AUTORISATION_ENVOI_INTERDITE")
    if any(d[k]=="BLOCAGE_SIGNALE" for k in (
        "procedure_responsable","reperage_public_preexistant",
        "precision_documents","confidentialite_tiers",
        "perimetre_juridique","services_et_emplois")):
        status="ARRET_REVUE_POUR_RISQUE_DECLARE"
    elif any(d[k]=="NON_EXAMINE" for k in (
        "procedure_responsable","reperage_public_preexistant",
        "precision_documents","confidentialite_tiers",
        "perimetre_juridique","services_et_emplois")):
        status="REVUE_HUMAINE_INCOMPLETE"
    else:
        status="RELECTURE_DECLAREE_NON_AUTHENTIFIEE_SANS_DROIT_ENVOI"
    return {"code":code,"statut":status,"depot_effectue":False,
            "avis_juridique_valide":False,"economies_certifiees_cad":None}

def summary(cfg,drafts,reviews):
    return {
        "schema_version":"P53R-RAPPORT-1",
        "exercice_documentaire":2024,
        "organismes_identifies":len(drafts),
        "projets_courriers_prepares":len(drafts),
        "descriptions_precises_documents":sum(len(x["type_pieces_recherchees"]) for x in drafts),
        "emplacements_p53q_encore_a_documenter":102,
        "pages_procedures_institutionnelles":len(cfg["destinations"]),
        "revues_declaratives_locales":len(reviews),
        "statuts_agreges":dict(sorted(Counter(x["statut"] for x in reviews).items())),
        "demandes_effectivement_envoyees":0,
        "accuses_de_reception_verifies":0,
        "delais_legaux_effectivement_declenches":0,
        "originaux_transactionnels_authentifies":0,
        "economies_certifiees_cad":None,
        "preuves_fiscales_F01_F20_validees":0,
        "montants_Nova_inconnus":1320,
        "taux_fiscaux_adoptes":0,
        "services_essentiels_reduits_autorises":False,
        "emplois_supprimes_autorises":0,
        "fusion_autorisee":False,
        "decision":NO_GO,
    }

def save_new(path,obj):
    p=Path(path)
    require(not p.exists() and not p.is_symlink(),"ECRASEMENT_REFUSE")
    with p.open("x",encoding="utf-8") as f:
        f.write(json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+"\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bilan")
    parser.add_argument("--courriers")
    parser.add_argument("--revue",action="append",default=[])
    parser.add_argument("--exiger-depot-confirme",action="store_true")
    args=parser.parse_args(argv)
    try:
        require(len(args.revue)<=6,"TROP_DE_REVUES")
        outputs=[Path(s) for s in (args.bilan,args.courriers) if s]
        require(len({p.resolve() for p in outputs})==len(outputs),
                "DEUX_SORTIES_IDENTIQUES")
        require(all(not p.exists() and not p.is_symlink() for p in outputs),
                "SORTIE_DEJA_EXISTANTE")
        cfg,parents=sources()
        drafts=generate(cfg,parents)
        data=[]
        seen=set()
        for path in args.revue:
            r=review(read(path))
            require(r["code"] not in seen,"REVUE_DOUBLE")
            seen.add(r["code"]);data.append(r)
        result=summary(cfg,drafts,data)
        if args.bilan:
            save_new(args.bilan,result)
        if args.courriers:
            save_new(args.courriers,{"schema_version":"P53R-COURRIERS-1",
                       "statut":"SIX_PROJETS_NON_ENVOYES","courriers":drafts})
        print(json.dumps(result,sort_keys=True,ensure_ascii=False))
        return 3 if args.exiger_depot_confirme else 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,
            json.JSONDecodeError) as e:
        print("P53R_REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
