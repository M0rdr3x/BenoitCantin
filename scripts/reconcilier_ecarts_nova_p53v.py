#!/usr/bin/env python3
"""P53V: organiser des écarts *possibles* et des correctifs non certifiés."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import sys

import verifier_separation_controles_nova_p53u as p53u

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"projets"/"projet-nova"/"etudes"/"P53V_REGISTRE_ECARTS_ET_CORRECTIFS.json"
NO_GO="NO_GO_AUTOMATIQUE"
CODES=tuple(p53u.CODES)
CATEGORIES=(
 "EMETTEUR_OU_VERSION_NON_CONFIRME",
 "REFERENCE_INTEGRITE_NON_FIABLE",
 "DROIT_ACCES_ET_CONFIDENTIALITE_INCERTAINS",
 "CONTREPARTIE_BILATERALE_NON_ETABLIE",
 "ELIMINATIONS_ANTERIEURES_A_RECONCILIER",
 "EMPLOIS_ET_SERVICES_NON_DEMONTRES",
 "COUT_COMPLET_ET_TRANSFERTS_NON_ETABLIS",
 "INDEPENDANCE_ET_AVIS_ORIGINAUX_ABSENTS",
)
LINK={
 "EMETTEUR_OU_VERSION_NON_CONFIRME":"ORIGINE_ET_IDENTITE_EMETTEUR",
 "REFERENCE_INTEGRITE_NON_FIABLE":"INTEGRITE_ET_CHAINE_CONSERVATION",
 "DROIT_ACCES_ET_CONFIDENTIALITE_INCERTAINS":"DROIT_ACCES_CONFIDENTIALITE",
 "CONTREPARTIE_BILATERALE_NON_ETABLIE":"CONTREPARTIES_ET_CONSOLIDATION_2024",
 "ELIMINATIONS_ANTERIEURES_A_RECONCILIER":"COUTS_COMPLETS_TRANSFERTS_ET_DOUBLE_COMPTE",
 "EMPLOIS_ET_SERVICES_NON_DEMONTRES":"EMPLOIS_CONDITIONS_ET_CONTINUITE_SERVICES",
 "COUT_COMPLET_ET_TRANSFERTS_NON_ETABLIS":"COUTS_COMPLETS_TRANSFERTS_ET_DOUBLE_COMPTE",
 "INDEPENDANCE_ET_AVIS_ORIGINAUX_ABSENTS":"AVIS_COMPTABLE_INDEPENDANT",
}
FIX={
 "EMETTEUR_OU_VERSION_NON_CONFIRME":"CONFIRMER_EMETTEUR_ET_VERSION",
 "REFERENCE_INTEGRITE_NON_FIABLE":"CONFIRMER_HASH_REFERENCE_ET_JOURNAL",
 "DROIT_ACCES_ET_CONFIDENTIALITE_INCERTAINS":"EXAMINER_ACCES_ET_DROITS_TIERS",
 "CONTREPARTIE_BILATERALE_NON_ETABLIE":"RAPPROCHER_GRANDS_LIVRES_ET_PAIEMENT",
 "ELIMINATIONS_ANTERIEURES_A_RECONCILIER":"IDENTIFIER_ECRITURES_DEJA_ELIMINEES",
 "EMPLOIS_ET_SERVICES_NON_DEMONTRES":"DOCUMENTER_GARANTIES_ET_QUALITE_SERVICE",
 "COUT_COMPLET_ET_TRANSFERTS_NON_ETABLIS":"RECONSTITUER_COUTS_COMPLETS_ET_TIERS",
 "INDEPENDANCE_ET_AVIS_ORIGINAUX_ABSENTS":"QUALIFIER_EXPERTS_ET_OBTENIR_AVIS_ORIGINAUX",
}
STATES=(
 "NON_INSTRUIT","ECART_POTENTIEL_DECLARE",
 "CORRECTIF_PROPOSE_NON_VERIFIE","CORRECTIF_EXAMINE_NON_CERTIFIE",
 "BLOCAGE_DECLARE",
)
ROLES=("COLLECTE_DOCUMENTAIRE","REVUE_QUALITE_INDEPENDANTE")
FLAGS={
 "aucune_anomalie_affirmee_sans_preuve",
 "aucun_correctif_clos_automatiquement",
 "un_hash_ne_valide_pas_la_provenance",
 "contradictions_conservees_et_non_masquees",
 "avis_roles_ne_prouvent_pas_independance_personnes",
 "aucune_donnee_personnelle_ou_piece_primaire_dans_git",
 "ne_pas_repondre_ni_contacter_tiers",
 "double_elimination_quebec_rtc_bloquee",
 "aucune_economie_calculee_a_partir_de_recettes",
 "maintien_emplois_et_services_essentiels",
 "regimes_constitutionnels_non_additifs",
 "aucune_publication_ou_fusion_automatique",
}
ITEM_KEYS={
 "schema_version","code_organisme","categorie","role_source",
 "statut_declaratif","niveau_piece","code_correctif",
 "perimetre_comptable","droit_acces","emplois_services",
 "independance_personnelle",
}
EVIDENCE={"ABSENTE","PUBLICATION_CANDIDATE_NON_PRIMAIRE",
          "PIECE_DECLAREE_NON_AUTHENTIFIEE","ELEMENTS_CONTRADICTOIRES_DECLARES"}
SCOPE={"NON_ETABLI","PERIMETRE_DECLARE_NON_VERIFIE",
       "INCOHERENCE_DECLAREE"}
LEGAL={"A_VERIFIER","POTENTIEL_NON_VERIFIE","ACCES_INTERDIT"}
SOCIAL={"A_VERIFIER","MAINTIEN_DECLARE_NON_VERIFIE","RISQUE_DECLARE"}
INDEP={"A_VERIFIER","ABSENCE_CONFLIT_DECLAREE_NON_VERIFIEE","CONFLIT_DECLARE"}
CORR={"CORRECTIF_PROPOSE_NON_VERIFIE","CORRECTIF_EXAMINE_NON_CERTIFIE"}
GUARD_CATEGORIES={"DROIT_ACCES_ET_CONFIDENTIALITE_INCERTAINS",
                  "EMPLOIS_ET_SERVICES_NON_DEMONTRES"}
SPECIAL={"23027","T0088"}

def require(cond,why):
    if not cond:raise ValueError(why)

def read(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink() and
            0<p.stat().st_size<=45000,"ENTREE_MANQUANTE_OU_TROP_GRANDE")
    value=json.loads(p.read_text(encoding="utf-8"))
    require(type(value) is dict,"JSON_OBJET_ATTENDU")
    return value

def sources():
    previous,parents=p53u.setup()
    old=p53u.matrix(previous,parents)
    cfg=read(SOURCE)
    expected={
      "schema_version":"P53V-1","jalon":"P53V",
      "date_reference":"2026-10-23",
      "statut":"PLAN_RAPPROCHEMENT_NON_INSTRUIT",
      "exercice_source":2024,
      "codes":list(CODES),
      "categories":list(CATEGORIES),
      "correspondance_p53u":LINK,
      "correctif_attendu":FIX,
      "statuts_declaratifs":list(STATES),
      "roles_sources":list(ROLES),
      "methodologie":[
        "https://www.theiia.org/en/content/standards/complete-global-internal-audit-standards/",
        "https://csrc.nist.gov/glossary/term/chain_of_custody",
      ],
      "verrous":{key:True for key in FLAGS},
      "etat_initial":{
        "organismes":6,"types_alertes":8,
        "positions_a_examiner":48,
        "references_p53q_manquantes":102,
        "exigences_p53u_non_verifiees":162,
        "cas_quebec_rtc_signales_pour_consolidation":2,
        "ecarts_transactionnels_authentifies":0,
        "avis_professionnels_independants_signes":0,
        "correctifs_clos_par_une_personne_habilitee":0,
        "economies_certifiees_cad":None,
        "decision":NO_GO,
      },
    }
    require(cfg==expected and len(parents)==6 and
            len(old)==48 and
            previous["etat_initial"]["avis_independants_signes"]==0 and
            all(r["economie_certifiee_cad"] is None for r in old),
            "CHAINE_P53U_ET_CONFIG_INCOHERENTES")
    return cfg,parents

def priority(code,category):
    if category in GUARD_CATEGORIES:
        return "PROTECTION_DROITS_ET_SERVICES_A_VERIFIER"
    if code in SPECIAL and category=="ELIMINATIONS_ANTERIEURES_A_RECONCILIER":
        return "PRIORITE_RAPPROCHEMENT_CONSOLIDATION_QUEBEC_RTC"
    return "RECHERCHE_PROBATOIRE_SANS_CONCLUSION"

def build(cfg,parents):
    lines=[]
    for person in parents:
        code=person["code_organisme"]
        for category in CATEGORIES:
            special=code in SPECIAL and category=="ELIMINATIONS_ANTERIEURES_A_RECONCILIER"
            lines.append({
                "code_organisme":code,
                "nom_organisme":person["nom_organisme"],
                "exercice":2024,
                "categorie_a_examiner":category,
                "controle_p53u_associe":LINK[category],
                "ordre_priorisation":priority(code,category),
                "correctif_potentiel":FIX[category],
                "signalement_documentaire_preexistant":(
                    "PRECAUTION_METHODOLOGIQUE_CONSOLIDATION_P53P"
                    if special else "AUCUN_FAIT_INSTITUTIONNEL_IMPUTE"),
                "ecart_reel_etabli":False,
                "statut":"NON_INSTRUIT",
                "preuves_origines_certifiees":0,
                "avis_independants_signes":0,
                "correctif_effectivement_realise_verifie":False,
                "cloture_par_personne_habilitee":False,
                "economie_certifiee_cad":None,
                "decision":NO_GO,
            })
    require(len(lines)==48
            and len({(r["code_organisme"],r["categorie_a_examiner"]) for r in lines})==48
            and sum(r["signalement_documentaire_preexistant"]==
                    "PRECAUTION_METHODOLOGIQUE_CONSOLIDATION_P53P"
                    for r in lines)==2,
            "REGISTRE_48_NON_CONFORME")
    return lines

def evaluate(entry):
    require(type(entry) is dict and set(entry)==ITEM_KEYS
            and entry.get("schema_version")=="P53V-DECLARATION-1",
            "DECLARATION_INVALIDE")
    code=entry["code_organisme"];category=entry["categorie"]
    require(type(code) is str and code in CODES
            and type(category) is str and category in CATEGORIES,
            "CIBLE_INCONNUE")
    role=entry["role_source"]
    require(type(role) is str and role in ROLES,"ROLE_INCONNU")
    state=entry["statut_declaratif"]
    require(type(state) is str and state in STATES,"STATUT_CERTIFIE_INTERDIT")
    require(type(entry["niveau_piece"]) is str and
            entry["niveau_piece"] in EVIDENCE,
            "PREUVE_CERTIFIEE_INTERDITE")
    action=entry["code_correctif"]
    require(type(action) is str and
            action==(FIX[category] if state in CORR else "AUCUN"),
            "CORRECTIF_INCOMPATIBLE_AVEC_STATUT")
    require(entry["perimetre_comptable"] in SCOPE
            and entry["droit_acces"] in LEGAL
            and entry["emplois_services"] in SOCIAL
            and entry["independance_personnelle"] in INDEP,
            "VERROU_JURIDIQUE_SOCIAL_INVALIDE")
    stop=(
        state=="BLOCAGE_DECLARE"
        or entry["droit_acces"]=="ACCES_INTERDIT"
        or entry["emplois_services"]=="RISQUE_DECLARE"
        or entry["independance_personnelle"]=="CONFLIT_DECLARE"
        or entry["perimetre_comptable"]=="INCOHERENCE_DECLAREE"
    )
    return {
        "cle":(code,category),
        "role":role,
        "statut_declare":state,
        "bloquant_declare":stop,
        "preuve_authentifiee":False,
        "avis_independant_valide":False,
        "correction_validee":False,
    }

def reconcile(entries):
    """Deux sources déclaratives indépendantes *sur papier*, aucun arbitrage automatique."""
    require(len(entries)<=96,"DECLARATIONS_EXCESSIVES")
    collected=defaultdict(dict)
    for raw in entries:
        e=evaluate(raw)
        key=e["cle"];role=e["role"]
        require(role not in collected[key],"DOUBLON_MEME_ROLE")
        collected[key][role]=e
    status=Counter()
    contradictions=0
    blocked=0
    for opinions in collected.values():
        views=list(opinions.values())
        risk=any(v["bloquant_declare"] for v in views)
        different=(len(views)==2 and
                   views[0]["statut_declare"]!=views[1]["statut_declare"])
        if different:
            if risk:
                label="CONTRADICTION_AVEC_BLOCAGE_NON_RESOLUE"
                blocked+=1
            else:
                label="CONTRADICTION_DECLAREE_NON_RESOLUE"
            contradictions+=1
        elif risk:
            label="BLOCAGE_DECLARE_NON_RESOLU"
            blocked+=1
        elif len(views)==1:
            label="AVIS_UNIQUE_DECLARE_SANS_PREUVE"
        elif views[0]["statut_declare"]=="NON_INSTRUIT":
            label="NON_INSTRUIT"
        else:
            label="AVIS_CONCORDANTS_DECLARATIFS_NON_CERTIFIES"
        status[label]+=1
    return {
        "declarations_exam":len(entries),
        "positions_avec_declarations":len(collected),
        "positions_avec_contradictions":contradictions,
        "positions_avec_blocages":blocked,
        "statuts_agreges":dict(sorted(status.items())),
        "correctifs_certifies":0,
        "ecarts_transactionnels_authentifies":0,
    }

def report(cfg,plan,stats):
    return {
        "schema_version":"P53V-RAPPORT-1",
        "exercice_des_sources":2024,
        "organismes":6,
        "positions_d_examen":len(plan),
        "alertes_methodologiques_quebec_rtc":2,
        "documents_p53q_non_obtenus":102,
        "points_p53u_non_certifies":48,
        "exigences_p53u_en_suspens":162,
        "declarations_examinees":stats["declarations_exam"],
        "positions_avec_declarations":stats["positions_avec_declarations"],
        "positions_avec_contradictions_declarees":stats["positions_avec_contradictions"],
        "positions_avec_blocages_declares":stats["positions_avec_blocages"],
        "statuts_agreges":stats["statuts_agreges"],
        "ecarts_financiers_reels_authentifies":0,
        "correctifs_independamment_valides":0,
        "clotures_par_autorite_habilitee":0,
        "avis_juridiques_comptables_signes":0,
        "demandes_d_acces_envoyees":0,
        "economies_certifiees_cad":None,
        "preuves_F01_F20_validees":0,
        "montants_Nova_inconnus":1320,
        "emplois_services_degrades_autorises":False,
        "fusion_autorisee":False,
        "decision":NO_GO,
    }

def write_new(path,value):
    p=Path(path)
    require(not p.exists() and not p.is_symlink(),"ECRASEMENT_REFUSE")
    with p.open("x",encoding="utf-8") as out:
        out.write(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

def main(args=None):
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--bilan")
    cli.add_argument("--registre")
    cli.add_argument("--declaration",action="append",default=[])
    cli.add_argument("--exiger-correctifs-clos",action="store_true")
    options=cli.parse_args(args)
    try:
        require(len(options.declaration)<=96,"TROP_DE_DECLARATIONS")
        targets=[Path(x) for x in (options.bilan,options.registre) if x]
        require(len({p.resolve() for p in targets})==len(targets)
                and all(not p.exists() and not p.is_symlink() for p in targets),
                "SORTIES_EXISTANTES_OU_IDENTIQUES")
        cfg,parents=sources()
        plan=build(cfg,parents)
        submitted=[read(p) for p in options.declaration]
        grouped=reconcile(submitted)
        summary=report(cfg,plan,grouped)
        if options.bilan:write_new(options.bilan,summary)
        if options.registre:
            write_new(options.registre,{
                "schema_version":"P53V-REGISTRE-1",
                "statut":"GRILLE_NON_INSTRUITE_SANS_ANOMALIES_DEMONTREES",
                "lignes":plan,
            })
        print(json.dumps(summary,sort_keys=True,ensure_ascii=False))
        return 3 if options.exiger_correctifs_clos else 0
    except (ValueError,OSError,KeyError,TypeError,UnicodeError,
            json.JSONDecodeError) as err:
        print("P53V_REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
