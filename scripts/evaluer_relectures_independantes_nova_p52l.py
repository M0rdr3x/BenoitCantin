#!/usr/bin/env python3
"""P52L: instruction declarative des avis contradictoires, sans octroi de GO."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
    "matrice":STUDY/"P52L_MATRICE_REVUES_INDEPENDANTES.json",
    "journal":STUDY/"P52L_JOURNAL_DECLARATIF_VIDE.json",
    "preuves":STUDY/"P52A_REGISTRE_PREUVES_FISCALES.json",
    "pistes":STUDY/"P52I_SOURCES_ET_ATTESTATIONS.json",
    "provenance":STUDY/"P52K_REGISTRE_PROVENANCE_BUDGET.json",
}
PHASES=[
    "NON_RECUE","RECUE_A_CONTROLER","CONTROLE_DOCUMENTAIRE_DECLARATIF",
    "AVIS_INDEPENDANT_DECLARE","EN_CONTESTATION","REEXAMEN_REQUIS",
    "PROPOSITION_DE_DECISION_NON_AUTHENTIFIEE",
]
OPERATIONS={
    "DEPOSER":"DEPOSANT",
    "CONTROLER":"VERIFICATEUR",
    "AVIS":"EXPERT_INDEPENDANT",
    "CONTESTER":"CONTRADICTEUR",
    "RESOUDRE":"CONTROLEUR_CONTESTATION",
    "PROPOSER_DECISION":"AUTORITE_PROPOSEE",
}
EVENT_FIELDS={
    "index","preuve_id","operation","acteur_ref","role","date_utc",
    "document_sha256","piece_action_sha256","regime","conflit_signale"
}
FALSE_POLICY=[
    "acceptation_juridique_independante_non_constatee",
    "adoption_democratique_non_constatee",
    "taux_fiscaux_non_adoptes",
    "garanties_pouvoir_achat_non_demontrees",
    "modeles_p52b_p52d_encore_incomplets",
    "budget_souverain_certifie",
    "publication_autorisee",
    "fusion_autorisee",
    "adoption_autorisee",
]
# Les cinq premieres sont des avertissements vrais, pas des portes ouvertes.
WARNING_FLAGS=FALSE_POLICY[:5]
ACTOR=re.compile(r"A-[A-Z0-9]{3,12}\Z")
SHA=re.compile(r"[a-f0-9]{64}\Z")
MAX_JSON_BYTES=450_000
MAX_EVENTS=200

def require(ok,reason):
    if not ok:
        raise ValueError(reason)

def load_json(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size<=MAX_JSON_BYTES,
            "FICHIER_JSON_ABSENT_OU_NON_ADMISSIBLE")
    value=json.loads(p.read_text(encoding="utf-8"))
    require(type(value) is dict,"OBJET_JSON_ATTENDU")
    return value

def controler_referentiel(inputs):
    require(type(inputs) is dict and set(inputs)==set(FILES),"CINQ_SOURCES_REQUISES")
    r,j,a,i,k=(inputs[n] for n in FILES)
    require(r.get("schema_version")=="P52L-1" and r.get("jalon")=="P52L" and
            r.get("statut")=="PROCEDURE_CONTROLE_INDEPENDANT_NON_APPLIQUEE" and
            r.get("date_reference")=="2026-10-19","SCHEMA_MATRICE_INVALIDE")
    refs=r.get("objets_references",{})
    require(type(refs) is dict and refs == {
        "p52a":str(FILES["preuves"].relative_to(ROOT)),
        "p52i":str(FILES["pistes"].relative_to(ROOT)),
        "p52k":str(FILES["provenance"].relative_to(ROOT)),
    },"DEPENDANCES_NON_TRACABLES")
    require(r.get("phases_autorisees")==PHASES,"ETAPES_MODIFIEES")
    require(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
            a.get("automatic_go") is False and a.get("rates_selected") is False and
            a.get("financial_model_certified") is False and
            a.get("human_reviews_received") is False,"GARDES_P52A_LEVEES")
    p=a.get("required_evidence")
    require(type(p) is list and len(p)==20 and
            [x.get("id") for x in p]==[f"F{n:02d}" for n in range(1,21)] and
            all(x.get("statut")=="NON_VALIDE" and
                x.get("preuve_independante_obtenue") is False and
                x.get("decision_autorisee") is False and
                x.get("priorite")=="BLOQUANT" for x in p),
            "STATUT_P52A_INCOHERENT")
    m=r.get("exigences")
    require(type(m) is list and len(m)==20,"MATRICE_20_PREUVES_INCOMPLETE")
    exact={"id","regime","theme","responsable_fonctionnel","priorite",
           "preuve_a_obtenir","etape_canonique",
           "piece_documentaire_deposee","identite_expert_authentifiee",
           "mandat_expert_verifie","conflit_interets_verifie",
           "avis_independant_signe_obtenu","contre_expertise_recue",
           "contestation_resolue_par_autorite","decision_humaine_signee",
           "reference_externe_attestation"}
    for left,right in zip(m,p):
        require(set(left)==exact,"SCHEMA_EXIGENCE_MODIFIE")
        for key in ("id","regime","theme","responsable_fonctionnel","priorite","preuve_a_obtenir"):
            require(left.get(key)==right.get(key),"MATRICE_ET_P52A_DIVERGENT_"+key)
        require(left.get("etape_canonique")=="NON_RECUE" and
                left.get("reference_externe_attestation") is None and
                all(left.get(flag) is False for flag in
                    ("piece_documentaire_deposee","identite_expert_authentifiee",
                     "mandat_expert_verifie","conflit_interets_verifie",
                     "avis_independant_signe_obtenu","contre_expertise_recue",
                     "contestation_resolue_par_autorite","decision_humaine_signee")),
                "PREUVE_OU_VALIDATION_FICTIVE")
    require(i.get("schema_version")=="P52I-1" and
            i.get("source_revue_independante") is False and
            i.get("donnees_extraites_certifiees") is False and
            i.get("publication_autorisee") is False and
            [x.get("id") for x in i.get("plan_preuves",[])]==
            [x.get("id") for x in p] and
            all(x.get("statut")=="NON_ATTESTEE" for x in i["plan_preuves"]),
            "P52I_INCOHERENT")
    require(k.get("schema_version")=="P52K-1" and
            k.get("decision")=="NO_GO_AUTOMATIQUE" and
            all(x.get("empreinte_sha256_pdf_original") is None and
                x.get("attestation_externe_signee") is None for x in k.get("fichiers_source",[])) and
            len(k.get("fichiers_source",[]))==2,
            "P52K_CERTIFICATION_FICTIVE")
    policy=r.get("politique_decision")
    require(type(policy) is dict and
            policy.get("attribution_validation_automatique_interdite") is True and
            all(policy.get(key) is True for key in WARNING_FLAGS) and
            all(policy.get(key) is False for key in FALSE_POLICY[5:]) and
            policy.get("attestations_P52A_obtenues")==0 and
            policy.get("decision")=="NO_GO_AUTOMATIQUE","GARDE_DECISION_MANQUANTE")
    protocole=r.get("protocole_journal")
    require(type(protocole) is dict and
            protocole.get("journal_commite_de_reference")==
            str(FILES["journal"].relative_to(ROOT)) and
            all(protocole.get(k) is True for k in
                ("pieces_reelles_hors_git","aucun_nom_ou_signature_personnelle_dans_repo",
                 "authentification_identites_et_signatures_par_tiers_exigee",
                 "separation_des_roles_exigee","contre_expertise_et_droit_de_contestation_exiges")) and
            protocole.get("declaration_conflit_interets_independamment_verifiee") is False and
            protocole.get("registre_revue_externe_en_place") is False,
            "INDEPENDANCE_FICTIVE")
    deploy=r.get("controle_de_deploiement")
    require(type(deploy) is dict and deploy and all(x is False for x in deploy.values()) and
            set(deploy)=={
                "main_change_autorise","publication_operationnelle_autorisee",
                "affectation_reviseur_reel_autorisee",
                "collecte_donnees_personnelles_autorisee"},
            "AUTORISATION_DEPLOIEMENT_INVENTEE")
    require(j.get("schema_version")=="P52L-JOURNAL-1" and j.get("jalon")=="P52L" and
            j.get("statut")=="EXEMPLE_SANS_PREUVE_REELLE" and
            j.get("date_reference")=="2026-10-19" and
            j.get("authentification_externe_obtenue") is False and
            j.get("autorisation_humaine_obtenue") is False and
            j.get("publication_autorisee") is False and
            j.get("decision")=="NO_GO_AUTOMATIQUE",
            "JOURNAL_NON_AUTORISE")
    return m

def evaluer_journal(exigences,journal):
    require(type(journal) is dict and
            journal.get("schema_version")=="P52L-JOURNAL-1" and
            journal.get("jalon")=="P52L" and
            journal.get("statut")=="EXEMPLE_SANS_PREUVE_REELLE" and
            journal.get("authentification_externe_obtenue") is False and
            journal.get("autorisation_humaine_obtenue") is False and
            journal.get("publication_autorisee") is False and
            journal.get("decision")=="NO_GO_AUTOMATIQUE",
            "FAUSSE_AUTORISATION_JOURNAL")
    events=journal.get("evenements")
    require(type(events) is list and len(events)<=MAX_EVENTS,
            "EVENEMENTS_INCORRECTS_OU_TROP_NOMBREUX")
    status={x["id"]:{"etape":"NON_RECUE","regime":x["regime"],
                      "empreinte":None,"deposant":None,"verificateur":None,
                      "expert":None,"contestataire":None,
                      "autorite":None,"date":None} for x in exigences}
    prev_date=None
    for position,event in enumerate(events,1):
        require(type(event) is dict and set(event)==EVENT_FIELDS,
                "EVENEMENT_CHAMPS_INCORRECTS")
        require(type(event["index"]) is int and event["index"]==position,
                "INDEX_DISCONTINU")
        pid=event["preuve_id"]
        require(type(pid) is str and pid in status,"PREUVE_INCONNUE")
        state=status[pid]
        op=event["operation"]
        require(op in OPERATIONS and event["role"]==OPERATIONS[op],
                "ROLE_OU_OPERATION_INADMISSIBLE")
        actor=event["acteur_ref"]
        require(type(actor) is str and ACTOR.fullmatch(actor) is not None,
                "ACTEUR_REF_INADMISSIBLE")
        require(event["regime"]==state["regime"],"REGIME_INCOMPATIBLE")
        require(type(event["conflit_signale"]) is bool,"CONFLIT_MAL_DEFINI")
        require(all(type(event[k]) is str and SHA.fullmatch(event[k])
                    for k in ("document_sha256","piece_action_sha256")),
                "EMPREINTE_NON_CONFORME")
        # Meta donnees uniquement: aucune preuve de possession/identite/signature.
        stamp=event["date_utc"]
        require(type(stamp) is str and re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",stamp),
            "HEURE_NON_UTC")
        try:
            moment=datetime.strptime(stamp,"%Y-%m-%dT%H:%M:%SZ")
        except ValueError as exc:
            raise ValueError("DATE_INVALIDE") from exc
        require(prev_date is None or moment>prev_date,"JOURNAL_NON_CHRONOLOGIQUE")
        prev_date=moment
        stage=state["etape"]
        if op=="DEPOSER":
            require(stage=="NON_RECUE","DEPOT_DEJA_RECU")
            require(event["conflit_signale"] is False,"CONFLIT_AU_DEPOT")
            state.update(etape="RECUE_A_CONTROLER",empreinte=event["document_sha256"],
                         deposant=actor)
        else:
            require(event["document_sha256"]==state["empreinte"] and
                    state["empreinte"] is not None,"DOCUMENT_NON_IDENTIQUE")
            if op=="CONTROLER":
                require(stage in ("RECUE_A_CONTROLER","REEXAMEN_REQUIS") and
                        actor!=state["deposant"] and
                        event["conflit_signale"] is False,
                        "CONTROLE_NON_INDEPENDANT")
                state.update(etape="CONTROLE_DOCUMENTAIRE_DECLARATIF",
                             verificateur=actor,expert=None,autorite=None)
            elif op=="AVIS":
                require(stage=="CONTROLE_DOCUMENTAIRE_DECLARATIF" and
                        actor not in (state["deposant"],state["verificateur"]) and
                        event["conflit_signale"] is False,
                        "AVIS_NON_INDEPENDANT_OU_NON_RECEVABLE")
                state.update(etape="AVIS_INDEPENDANT_DECLARE",expert=actor)
            elif op=="CONTESTER":
                require(stage in (
                    "CONTROLE_DOCUMENTAIRE_DECLARATIF","AVIS_INDEPENDANT_DECLARE",
                    "PROPOSITION_DE_DECISION_NON_AUTHENTIFIEE") and
                    actor!=state["deposant"],
                    "CONTESTATION_IRRECEVABLE")
                state.update(etape="EN_CONTESTATION",contestataire=actor,
                             autorite=None)
            elif op=="RESOUDRE":
                require(stage=="EN_CONTESTATION" and
                        actor not in (state["deposant"],state["expert"],
                                      state["contestataire"]) and
                        event["conflit_signale"] is False,
                        "RESOLUTION_NON_INDEPENDANTE")
                # Il faut refaire contrôle et avis, pas rétablir un avis annulé.
                state.update(etape="REEXAMEN_REQUIS",verificateur=None,
                             expert=None,autorite=None,contestataire=None)
            elif op=="PROPOSER_DECISION":
                require(stage=="AVIS_INDEPENDANT_DECLARE" and
                        actor not in (state["deposant"],state["verificateur"],
                                      state["expert"]) and
                        event["conflit_signale"] is False,
                        "PROPOSITION_NON_RECEVABLE")
                state.update(etape="PROPOSITION_DE_DECISION_NON_AUTHENTIFIEE",
                             autorite=actor)
        state["date"]=stamp
    count={p:sum(s["etape"]==p for s in status.values()) for p in PHASES}
    require(sum(count.values())==20,"GRILLE_INCOMPLETE")
    # Liste blanche d'agrégats: jamais noms, pseudonymes, URL, hashes ni cas.
    return {
        "jalon":"P52L","schema_version":"P52L-1",
        "preuves_encadrees":20,
        "evenements_declares":len(events),
        "stades_declaratifs":count,
        "attestations_humaines_authentifiees":0,
        "decisions_formelles_authentifiees":0,
        "validation_juridique_et_budgetaire_demontrée":False,
        "autorisation_publique_et_adoption":False,
        "publication_autorisee":False,"fusion_autorisee":False,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for key,path in FILES.items():
        parser.add_argument("--"+key,type=Path,default=path)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--exiger-validation",action="store_true")
    args=parser.parse_args(argv)
    try:
        loaded={key:load_json(getattr(args,key)) for key in FILES}
        model=controler_referentiel(loaded)
        result=evaluer_journal(model,loaded["journal"])
        rc=3 if args.exiger_validation else 0
    except (OSError,UnicodeError,ValueError,TypeError,KeyError) as error:
        result={"jalon":"P52L","statut":"ERREUR_VALIDATION",
                "type_erreur":type(error).__name__,
                "publication_autorisee":False,"fusion_autorisee":False,
                "decision":"NO_GO_AUTOMATIQUE"}
        rc=2
    payload=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.rapport:
        try:
            path=args.rapport
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open("x",encoding="utf-8") as handle:handle.write(payload)
        except OSError:return 2
    else:
        print(payload,end="")
    return rc

if __name__=="__main__":
    sys.exit(main())
