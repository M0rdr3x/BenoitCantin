#!/usr/bin/env python3
"""P55E — prioriser des preuves manquantes sans inventer leur obtention."""
import argparse
import json
from pathlib import Path
import sys

import preparer_dossier_experts_nova_p55d as p55d

p55c = p55d.p55c
p55b = p55d.p55b
p55a = p55d.p55a
p54z = p55d.p54z
BASE = p55d.BASE
CONFIG = BASE / "P55E_PRIORITES_PREUVES_2024.json"
NO_GO = p55d.NO_GO
REFS = p55d.REFS
ACCESS = (
    "PUBLIC_SOUS_CONTROLE_EDITION",
    "ACCES_LEGAL_A_VERIFIER",
    "EXPERT_INDEPENDANT_A_MANDATER",
    "DECISION_INSTITUTIONNELLE",
)
ACTIONS = (
    ("A01","OBTENIR_PDF_VILLE_2024",ACCESS[0],"RESPONSABLE_DOCUMENTAIRE","COPIE_VILLE_HORS_DEPOT"),
    ("A02","OBTENIR_PDF_MAMH_2024",ACCESS[0],"RESPONSABLE_DOCUMENTAIRE","COPIE_MAMH_HORS_DEPOT"),
    ("A03","INSTRUIRE_CHANGEMENT_EDITION",ACCESS[1],"RESPONSABLE_DOCUMENTAIRE","TRACE_DISTINCTE_DES_EDITIONS"),
    ("A04","REPRODUIRE_CINQ_POSITIONS",ACCESS[1],"EXAMINATEUR_HABILITE","POSITIONS_NFKC_CONCORDANTES"),
    ("A05","VERIFIER_DROITS_ET_PROVENANCE",ACCESS[1],"RESPONSABLE_DOCUMENTAIRE","DROITS_D_ACCES_VERIFIES"),
    ("A06","RELIRE_CINQ_OBSERVATIONS",ACCESS[1],"LECTEUR_DOCUMENTAIRE","QUALIFICATIONS_CONTRADICTOIRES"),
    ("A07","TRAITER_RESERVES_SUSPENSIONS",ACCESS[2],"CONTRE_LECTEUR_INDEPENDANT","CONTRADICTIONS_TRACEES"),
    ("A08","EXAMINER_MANDAT_COMPTABLE",ACCESS[2],"GOUVERNANCE_HUMAINE","MANDAT_COMPTABLE_NON_TRANSMIS"),
    ("A09","EXAMINER_MANDAT_JURIDIQUE",ACCESS[2],"GOUVERNANCE_HUMAINE","MANDAT_JURIDIQUE_NON_TRANSMIS"),
    ("A10","VERIFIER_CONSOLIDATION_ET_IMPACTS",ACCESS[2],"CPA_ET_ANALYSTE_POLITIQUES_PUBLIQUES","AUCUN_DOUBLE_COMPTE_ET_GARANTIES"),
    ("A11","AUTHENTIFIER_AVIS_INDEPENDANTS",ACCESS[3],"AUTORITE_COMPETENTE","ORIGINAUX_AVIS_VERIFIES"),
    ("A12","DECISION_PAR_AUTORITE_COMPETENTE",ACCESS[3],"AUTORITE_COMPETENTE","DECISION_INSTITUTIONNELLE_DISTINCTE"),
)
GUARDS = {
    "aucun_telechargement_automatique",
    "aucune_sollicitation_ou_contact_externe",
    "etapes_prioritaires_conditionnees_par_preuves_reelles",
    "deux_pdfs_historiques_p54q_requis",
    "editions_divergentes_prioritaires_et_non_reecrites",
    "aucune_reproduction_si_un_pdf_non_concordant",
    "suivi_prive_p55d_reverifie_depuis_sources",
    "plans_prives_hors_git_et_0600",
    "aucun_chemin_offset_sha_prive_publie",
    "aucun_nom_adresse_signature_contrat_ou_montant_dans_github",
    "aucun_statut_preparation_assimile_attestation",
    "suspensions_p54z_p55a_p55c_p55d_non_levees",
    "deux_mandats_p54h_non_transmis",
    "expertise_professionnelle_hors_code",
    "zero_montant_certifie",
    "quatre_p54e_ouverts_et_date_non_qualifiee",
    "quarante_p54n_dix_p54o_non_leves",
    "p54b_96_p54c_8_non_attestes",
    "consolidation_ville_rtc_somhac_sans_double_compte",
    "protection_emplois_services_pouvoir_achat",
    "deux_regimes_constitutionnels_distincts",
    "aucune_fusion_main",
    "aucune_action_sinjira",
    "no_go_automatique",
}
INITIAL = {
    "documents_publics_references":2,
    "copies_originales_fournies_p55e":0,
    "editions_p55e_verifiees":0,
    "observations_a_revoir":5,
    "exigences_p55d_a_collecter":40,
    "mandats_professionnels_reels_signes":0,
    "avis_independants_authentifies":0,
    "dossiers_p54e_ouverts":4,
    "date_probable_non_certifiee":1,
    "taches_p54n_non_attestees":40,
    "blocages_p54o_non_leves":10,
    "controles_p54b_non_attestes":96,
    "controles_p54c_non_attestes":8,
    "economies_certifiees_cad":None,
    "decision":NO_GO,
}
MISSING = p55b.NON_FOURNIE
MATCH = p55b.CONCORDANCE
EDITION = p55b.EDITION


def need(test,reason):
    if not test:
        raise ValueError(reason)


def action_catalog():
    return [
        {"code":code,"action":action,"categorie":cat,
         "role_a_designer":role,"livrable_attendu":deliverable}
        for code,action,cat,role,deliverable in ACTIONS
    ]


def configuration():
    cfg=p54z.read_json(CONFIG)
    expected={
        "schema_version":"P55E-1","date_reference":"2026-11-03",
        "exercice":2024,
        "source_jalons":["P54H","P54Q","P54Z","P55A","P55B","P55C","P55D"],
        "references":list(REFS),
        "categories_acces":list(ACCESS),
        "plan_actions":action_catalog(),
        "protections":{x:True for x in GUARDS},
        "etat_initial":INITIAL,
    }
    need(cfg==expected,"P55E_CONFIG_MODIFIEE")
    p=p55d.configuration()
    need(p["schema_version"]=="P55D-1"
         and p["etat_initial"]["positions_a_instruire"]==40
         and p["etat_initial"]["decision"]==NO_GO
         and p["mandats_sans_engagement"]==list(p55b.MANDATES)
         and p55b.configuration()["schema_version"]=="P55B-1",
         "P55E_CHAINAGE_NON_CONFORME")
    return cfg


def valid_status(states,reproduced):
    need(type(states) is dict and set(states)==set(p55b.PDF_CODES)
         and all(s in (MISSING,MATCH,EDITION) for s in states.values())
         and type(reproduced) is bool
         and (not reproduced or all(s==MATCH for s in states.values())),
         "P55E_SOURCES_NON_CONFORMES")
    return states


def priority(states,reproduced,blockers=0):
    """Only current next actions; downstream expert stages never marked done."""
    valid_status(states,reproduced)
    need(type(blockers) is int and blockers>=0 and blockers<=200,
         "P55E_OBSTACLES_NON_CONFORMES")
    waiting=[]
    if states["VILLE_2024"]==MISSING:
        waiting.append("A01")
    if states["MAMH_23027_2024"]==MISSING:
        waiting.append("A02")
    if EDITION in states.values():
        waiting.append("A03")
    if waiting:
        stage=("EDITIONS_A_INSTRUIRE" if EDITION in states.values()
               else "COPIES_MANQUANTES")
        return stage,waiting
    if not reproduced:
        return "REPRODUCTION_NON_OBTENUE",["A04"]
    if blockers:
        return "RESERVES_ET_ACCES_A_EXAMINER",["A05","A07"]
    return "REVUE_HUMAINE_A_ORGANISER",["A05","A06"]


def validate_inputs(paths,outputs):
    src=[p55a.private_source(x) for x in paths if x]
    dest=[Path(x).expanduser().absolute() for x in outputs if x]
    need(len({p.resolve() for p in src+dest})==len(src+dest),
         "P55E_CHEMINS_CONFONDUS")
    for out in dest:
        need(out.parent.is_dir() and not out.parent.is_symlink()
             and not out.exists() and not out.is_symlink(),
             "P55E_SORTIE_EXISTANTE_OU_INVALIDE")
    return src,dest


def private_followup(path_z,path_a,path_c,path_d,positions):
    need(positions is not None,"P55E_CINQ_POSITIONS_ABSENTES")
    z,a,c,raw,counts,inherited,review=p55d.upstream(
        path_z,path_a,path_c,positions)
    need(raw is not None,"P55E_FICHE_P55C_OBLIGATOIRE")
    local=p54z.read_json(p55a.private_source(path_d),100000)
    totals=p55d.validate_followup(local,raw,z,a,c)
    return local,totals,counts,inherited,review


def private_worklist(doc):
    """No raw data, no paths, no NFKC offsets, no hashes; always local 0600."""
    need(type(doc) is dict and
         doc.get("schema_version")=="P55D-SUIVI-LOCAL-1"
         and type(doc.get("observations")) is list
         and len(doc["observations"])==5,
         "P55E_SUIVI_PRIVÉ_INVALIDE")
    rows=[]
    for ref,record in zip(REFS,doc["observations"]):
        need(type(record) is dict
             and set(record)=={"reference","exigences"}
             and record["reference"]==ref
             and type(record["exigences"]) is list
             and len(record["exigences"])==len(p55d.GATES),
             "P55E_GRILLE_OU_REFERENCE_MODIFIEE")
        pending=[]
        for (gate,_deliverable,role),cell in zip(
                p55d.GATES,record["exigences"]):
            need(type(cell) is dict and set(cell)=={"code","etat"}
                 and cell["code"]==gate
                 and type(cell["etat"]) is str
                 and cell["etat"] in p55d.STATES,
                 "P55E_GATE_INVALIDE")
            if cell["etat"]!="PREPARATION_DECLAREE_NON_ATTESTEE":
                pending.append({"controle":gate,"etat":cell["etat"],
                                "role_a_designer":role})
        rows.append({"reference":ref,"exigences_a_traiter":pending})
    return {
        "schema_version":"P55E-TRIAGE-PRIVE-1","exercice":2024,
        "dossiers":rows,"pieces_originales_reproduites_techniquement":True,
        "aucune_certification_par_plan":True,
        "transmission_autorisee":False,"decision":NO_GO,
    }


def report(states=None,reproduced=False,totals=None,
           p55a_counts=None,inherited_z=0,p55c_review=None):
    if states is None:
        states={code:MISSING for code in p55b.PDF_CODES}
    valid_status(states,reproduced)
    if totals is None:
        totals=p55d.empty_counts()
    need(type(totals) is dict and set(totals)==set(p55d.STATES)
         and all(type(v) is int and v>=0 for v in totals.values())
         and sum(totals.values())==40
         and (reproduced or totals==p55d.empty_counts()),
         "P55E_COMPTEUR_P55D_NON_CONFORME")
    if p55a_counts is None:
        p55a_counts={s:(50 if s=="NON_INSTRUIT" else 0)
                     for s in p55a.STATES}
    need(type(p55a_counts) is dict and set(p55a_counts)==set(p55a.STATES)
         and all(type(v) is int and v>=0 for v in p55a_counts.values())
         and sum(p55a_counts.values())==50
         and type(inherited_z) is int and 0<=inherited_z<=40,
         "P55E_AMONT_P55A_INCOHERENT")
    if p55c_review is None:
        p55c_review=(5,0,0)
    need(type(p55c_review) is tuple and len(p55c_review)==3
         and all(type(v) is int and v>=0 for v in p55c_review)
         and p55c_review[0]+p55c_review[1]<=5,
         "P55E_AMONT_P55C_INCOHERENT")
    # These are counts of declarative flags, not unique underlying cases.
    blockers=(inherited_z+p55a_counts["RESERVE"]+
              p55a_counts["SUSPENDU"]+p55c_review[1]+p55c_review[2]+
              totals["RESERVE"]+totals["SUSPENDU"]+totals["INACCESSIBLE"])
    stage,actions=priority(states,reproduced,blockers)
    return {
        "schema_version":"P55E-BILAN-PUBLIC-1","exercice":2024,
        "phase_prioritaire":stage,"prochaines_actions_codes":actions,
        "copies_publiques_absentes":
            sum(s==MISSING for s in states.values()),
        "editions_divergentes_a_instruire":
            sum(s==EDITION for s in states.values()),
        "copies_concordantes_p54q_non_authentifiees":
            sum(s==MATCH for s in states.values()),
        "positions_nfkc_reproduites_techniquement":5 if reproduced else 0,
        "suivi_p55d_declaratif_non_atteste":dict(totals),
        "suspensions_p54z_heritees":inherited_z,
        "suspensions_p55a_heritees":p55a_counts["SUSPENDU"],
        "reserves_p55a_heritees":p55a_counts["RESERVE"],
        "suspensions_p55c_heritees":p55c_review[1],
        "reserves_desaccords_p55c_herites":p55c_review[2],
        "obstacles_declaratifs_agreges_non_uniques":blockers,
        "dossiers_p54e_ouverts":4,"date_probable_non_certifiee":1,
        "mandats_comptable_juridique_non_transmis":2,
        "experts_engages_authentifies":0,
        "avis_independants_authentifies":0,
        "taches_p54n_non_attestees":40,"blocages_p54o_non_leves":10,
        "controles_p54b_non_attestes":96,"controles_p54c_non_attestes":8,
        "economies_certifiees_cad":None,
        "transmission_externe_autorisee":False,
        "engagement_depense_autorise":False,
        "cloture_dossier_autorisee":False,"fusion_main_autorisee":False,
        "decision":NO_GO,
    }


def public_plan(summary):
    need(type(summary) is dict and
         summary.get("schema_version")=="P55E-BILAN-PUBLIC-1"
         and summary.get("decision")==NO_GO
         and type(summary.get("prochaines_actions_codes")) is list,
         "P55E_BILAN_SOURCE_PLAN_INVALIDE")
    current=set(summary["prochaines_actions_codes"])
    need(current.issubset({x[0] for x in ACTIONS}),"P55E_ACTION_INCONNUE")
    return {
        "schema_version":"P55E-PLAN-PUBLIC-1","exercice":2024,
        "phase_prioritaire":summary["phase_prioritaire"],
        "actions":[
            dict(item,statut=(
                "ACTION_PRIORITAIRE_A_REALISER"
                if item["code"] in current else
                "ETAPE_HUMAINE_NON_REALISEE_ET_NON_AUTORISEE"))
            for item in action_catalog()
        ],
        "sources_officielles_a_consulter":[
            {"code":s["code"],"url_officielle":s["url_officielle"]}
            for s in p55b.expected_sources()
        ],
        "aucune_requete_externe_effectuee":True,
        "aucune_decision_automatique":True,"decision":NO_GO,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ville-pdf")
    parser.add_argument("--mamh-pdf")
    parser.add_argument("--declarations-p54z")
    parser.add_argument("--relecture-p55a")
    parser.add_argument("--fiche-p55c")
    parser.add_argument("--suivi-p55d")
    parser.add_argument("--plan-public")
    parser.add_argument("--bilan-public")
    parser.add_argument("--plan-prive")
    parser.add_argument("--exiger-go",action="store_true")
    a=parser.parse_args(argv)
    try:
        configuration()
        need(bool(a.ville_pdf)==bool(a.mamh_pdf),
             "P55E_DEUX_PDF_INSEPARABLES")
        group=(a.declarations_p54z,a.relecture_p55a,
               a.fiche_p55c,a.suivi_p55d)
        need(not any(group) or all(group),"P55E_QUATRE_FICHES_OBLIGATOIRES")
        need(not any(group) or bool(a.ville_pdf),
             "P55E_FICHES_REQUIERENT_DEUX_PDF")
        need(not a.plan_prive or all(group),
             "P55E_PLAN_PRIVE_REQUIERT_SUIVI_COMPLET")
        sources=(a.ville_pdf,a.mamh_pdf,*group)
        targets=(a.plan_public,a.bilan_public,a.plan_prive)
        validate_inputs(sources,targets)
        if a.plan_prive:
            p54z.outside_repo(a.plan_prive)
        states,attempt=p55c.local_sources(a.ville_pdf,a.mamh_pdf)
        reproduced=(attempt is not None and
                    attempt["cinq_positions_reproduites"] is True)
        local=None
        totals=counts=review=None
        inherited=0
        # Never use a follow-up declaration if PDF versions do not reproduce.
        if all(group) and not reproduced:
            return 4
        if all(group):
            local,totals,counts,inherited,review=private_followup(
                *group,attempt["positions"])
        summary=report(states,reproduced,totals,counts,inherited,review)
        plan=public_plan(summary)
        if a.bilan_public:
            p54z.write_new(a.bilan_public,summary)
        if a.plan_public:
            p54z.write_new(a.plan_public,plan)
        if a.plan_prive:
            p54z.write_new(a.plan_prive,private_worklist(local),private=True)
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        if a.exiger_go:
            return 3
        return 4 if a.ville_pdf and not reproduced else 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError,
            json.JSONDecodeError,ImportError):
        print("P55E_REFUS: PREUVES_OU_CHAINAGE_NON_CONFORMES",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
