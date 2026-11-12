#!/usr/bin/env python3
"""P53U — Revue indépendante planifiée, jamais certification par déclaration."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import verifier_integrite_locale_nova_p53t as p53t

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets"/"projet-nova"/"etudes"/"P53U_GRILLE_INDEPENDANCE_REVUE_PROBATOIRE.json"
NO_GO="NO_GO_AUTOMATIQUE"
CODES=tuple(p53t.CODE)
GATES=(
 "ORIGINE_ET_IDENTITE_EMETTEUR",
 "INTEGRITE_ET_CHAINE_CONSERVATION",
 "DROIT_ACCES_CONFIDENTIALITE",
 "CONTREPARTIES_ET_CONSOLIDATION_2024",
 "EMPLOIS_CONDITIONS_ET_CONTINUITE_SERVICES",
 "COUTS_COMPLETS_TRANSFERTS_ET_DOUBLE_COMPTE",
 "EXAMEN_JURIDIQUE_SEPARE",
 "AVIS_COMPTABLE_INDEPENDANT",
)
ROLES={
 "ORIGINE_ET_IDENTITE_EMETTEUR":"COLLECTE_DOCUMENTAIRE",
 "INTEGRITE_ET_CHAINE_CONSERVATION":"CONTROLE_TECHNIQUE",
 "DROIT_ACCES_CONFIDENTIALITE":"EXAMEN_JURIDIQUE",
 "CONTREPARTIES_ET_CONSOLIDATION_2024":"EXAMEN_COMPTABLE",
 "EMPLOIS_CONDITIONS_ET_CONTINUITE_SERVICES":"EXAMEN_COMPTABLE",
 "COUTS_COMPLETS_TRANSFERTS_ET_DOUBLE_COMPTE":"EXAMEN_COMPTABLE",
 "EXAMEN_JURIDIQUE_SEPARE":"EXAMEN_JURIDIQUE",
 "AVIS_COMPTABLE_INDEPENDANT":"EXAMEN_COMPTABLE",
}
REVIEWER="REVUE_QUALITE_INDEPENDANTE"
CHECKLIST={
 "ORIGINE_ET_IDENTITE_EMETTEUR":(
   "organisme_emetteur_confirme","version_originale_et_periodicite_verifiees",
   "preuve_communication_archivée_hors_git"),
 "INTEGRITE_ET_CHAINE_CONSERVATION":(
   "hash_octets_reference_sure","journaux_authentifies_et_controles",
   "acces_dossiers_restraints"),
 "DROIT_ACCES_CONFIDENTIALITE":(
   "base_legale_et_detenteur","caviardage_droits_tiers",
   "finalite_et_autorisation_consultation"),
 "CONTREPARTIES_ET_CONSOLIDATION_2024":(
   "grand_livre_payeur","grand_livre_beneficiaire",
   "ecritures_reciproques_et_perimetre","eliminations_anterieures"),
 "EMPLOIS_CONDITIONS_ET_CONTINUITE_SERVICES":(
   "effectifs_et_conditions_maintenus",
   "continuite_et_accessibilite_service",
   "droit_des_usagers_et_recours"),
 "COUTS_COMPLETS_TRANSFERTS_ET_DOUBLE_COMPTE":(
   "couts_transition_et_recurrents","absence_transferts_aux_tiers",
   "benefices_financiers_a_produire_separement","absence_de_double_compte"),
 "EXAMEN_JURIDIQUE_SEPARE":(
   "independance_effective_evaluee",
   "competence_juridique_et_conflits_interets",
   "avis_original_signe_et_conserve_hors_git"),
 "AVIS_COMPTABLE_INDEPENDANT":(
   "independance_effective_evaluee",
   "methodologie_comptable_appropriee",
   "avis_original_signe_et_conserve_hors_git",
   "soutien_conclusions_par_pieces_primaires"),
}
BREAKS={
 "ABSENCE_PREUVES_PRIMAIRES","CONFLIT_INTERETS","ACCES_INTERDIT",
 "VIOLATION_GARANTIES_EMPLOIS_SERVICES","RISQUE_DOUBLE_COMPTE",
 "ABSENCE_AVIS_ORIGINAUX_SIGNES",
}
GUARDS={
 "roles_distincts_ne_prouvent_pas_personnes_independantes",
 "aucune_attestation_signée_publiée","aucun_document_original_dans_git",
 "aucune_signature_acceptée_en_entree","aucun_avis_independant_auto_certifié",
 "aucun_montant_financier_utilisé","aucune_économie_non_vérifiée",
 "deux_regimes_séparés","double_élimination_quebec_rtc_interdite",
 "emplois_conditions_services_essentiels_protégés",
 "aucune_déclaration_d_adoption","aucune_fusion_automatique",
}
ENTRY={
 "schema_version","code_organisme","controle","statut_declaratif",
 "role_pilote","role_relecture","presence_piece_primaire",
 "independance_declares","droit_acces","garanties_emplois_services",
 "traitement_consolidation","avis_formel",
}
STATES={"NON_EXAMINE","REVUE_PREPAREE_NON_SIGNEE","BLOCAGE_DECLARE"}
PRIMARY={"ABSENTE","CANDIDATE_NON_AUTHENTIFIEE"}
INDEP={"INCONNUE","DECLAREE_NON_VERIFIEE","CONFLIT_DECLARE"}
LEGAL={"A_VERIFIER","ACCES_POTENTIEL_NON_VERIFIE","ACCES_INTERDIT"}
SOCIAL={"A_VERIFIER","PROTECTIONS_DECLAREES_NON_VERIFIEES","RISQUE_DECLARE"}
SCOPE={"A_VERIFIER","RAPPROCHEMENT_DECLARE_NON_VERIFIE","RISQUE_DOUBLE_COMPTE"}
ADVICE={"NON_OBTENU","PREPARE_NON_SIGNE","SIGNE_DECLARE_NON_AUTHENTIFIE"}

def require(ok,message):
    if not ok:raise ValueError(message)

def read(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink()
            and 0<p.stat().st_size<=48000,"FICHIER_INDISPONIBLE")
    value=json.loads(p.read_text(encoding="utf-8"))
    require(type(value) is dict,"OBJET_JSON_ATTENDU")
    return value

def setup():
    tcfg,qcfg,parents=p53t.setup()
    old=p53t.inventory(qcfg,parents)
    cfg=read(CONFIG)
    baseline={
      "schema_version":"P53U-1","jalon":"P53U",
      "date_reference":"2026-10-22",
      "statut":"GRILLE_CONTROLES_INDEPENDANCE_SANS_AVIS_SIGNE",
      "exercice_comptable":2024,
      "codes":list(CODES),
      "controles":list(GATES),
      "pilotage_par_controle":ROLES,
      "role_relecture":REVIEWER,
      "exigences_par_controle":{k:list(v) for k,v in CHECKLIST.items()},
      "criteres_de_blocage":sorted(BREAKS),
      "sources_methodologiques":[
       "https://www.theiia.org/en/standards/2024-standards/global-internal-audit-standards/",
       "https://csrc.nist.gov/glossary/term/chain_of_custody",
       "https://www.legisquebec.gouv.qc.ca/fr/document/lc/A-2.1"],
      "verrous":{key:True for key in sorted(GUARDS)},
      "etat_initial":{
        "organismes":6,
        "pieces_en_suspens":102,
        "positions_de_controle":48,
        "points_a_examiner":sum(len(v) for v in CHECKLIST.values())*6,
        "avis_independants_signes":0,
        "preuves_de_provenance_authentifiees":0,
        "demandes_externes_envoyees":0,
        "economies_certifiees_cad":None,
        "decision":NO_GO,
      },
    }
    require(cfg==baseline and len(old)==102 and
            len(parents)==6 and
            tcfg["etat_initial"]["attestations_provenance_signees"]==0
            and all(x["provenance_authentifiee"] is False for x in old),
            "CHAINE_P53T_OU_CONFIGURATION_INCOHERENTE")
    return cfg,parents

def matrix(cfg,parents):
    records=[]
    for p in parents:
        code=p["code_organisme"]
        for seq,step in enumerate(GATES,1):
            records.append({
              "code_organisme":code,
              "nom_organisme":p["nom_organisme"],
              "exercice_comptable":2024,
              "ordre_prealable":seq,
              "controle":step,
              "role_pilote_prevu":ROLES[step],
              "role_relecture_prevu":REVIEWER,
              "personnes_reelles_distinctes_verifiees":False,
              "absence_conflit_interets_verifiee":False,
              "critere_exigences":list(CHECKLIST[step]),
              "toutes_pieces_obtenues":False,
              "avis_independant_original_signe":False,
              "controle_quebec_rtc_anti_double_elimination":code in ("23027","T0088"),
              "emplois_et_services_preserves_certifies":False,
              "statut":"PREALABLE_A_VERIFIER",
              "economie_certifiee_cad":None,
              "decision":NO_GO,
            })
    require(len(records)==48 and
            len({(x["code_organisme"],x["controle"]) for x in records})==48
            and all(x["role_pilote_prevu"]!=x["role_relecture_prevu"]
                    for x in records),
            "MATRICE_INCOMPLETE")
    return records

def review(input_):
    """Accepte uniquement des énoncés NON certifiés, jamais une signature."""
    require(type(input_) is dict and set(input_)==ENTRY and
            input_.get("schema_version")=="P53U-REVUE-1",
            "DECLARATION_NON_CONFORME")
    code=input_["code_organisme"];step=input_["controle"]
    require(type(code) is str and code in CODES and
            type(step) is str and step in GATES,
            "CODE_OU_CONTROLE_INCONNU")
    require(input_["role_pilote"]==ROLES[step]
            and input_["role_relecture"]==REVIEWER
            and input_["role_pilote"]!=input_["role_relecture"],
            "ROLES_NON_SEPARES")
    require(input_["statut_declaratif"] in STATES
            and input_["presence_piece_primaire"] in PRIMARY
            and input_["independance_declares"] in INDEP
            and input_["droit_acces"] in LEGAL
            and input_["garanties_emplois_services"] in SOCIAL
            and input_["traitement_consolidation"] in SCOPE
            and input_["avis_formel"] in ADVICE,
            "STATUT_CERTIFIE_NON_ADMIS")
    if (input_["statut_declaratif"]=="BLOCAGE_DECLARE"
        or input_["independance_declares"]=="CONFLIT_DECLARE"
        or input_["droit_acces"]=="ACCES_INTERDIT"
        or input_["garanties_emplois_services"]=="RISQUE_DECLARE"
        or input_["traitement_consolidation"]=="RISQUE_DOUBLE_COMPTE"):
        status="ARRET_CONTROLE_DECLARE"
    elif code in ("23027","T0088") and step in (
            "CONTREPARTIES_ET_CONSOLIDATION_2024",
            "COUTS_COMPLETS_TRANSFERTS_ET_DOUBLE_COMPTE") and (
            input_["traitement_consolidation"]=="A_VERIFIER"):
        status="ALERTE_QUEBEC_RTC_CONSOLIDATION_INCOMPLETE"
    elif input_["presence_piece_primaire"]=="ABSENTE":
        status="PIECE_PRIMAIRE_MANQUANTE"
    elif input_["statut_declaratif"]=="NON_EXAMINE":
        status="EXAMEN_EN_ATTENTE"
    elif input_["independance_declares"]=="INCONNUE":
        status="INDEPENDANCE_PERSONNELLE_NON_ETABLIE"
    elif input_["avis_formel"]=="NON_OBTENU":
        status="AVIS_ORIGINAL_MANQUANT"
    else:
        status="EXAMEN_DECLARE_SANS_CERTIFICATION"
    return {"cle":(code,step),"statut":status,
            "signatures_originales_verifiees":0,
            "personnes_reelles_independantes_attestees":False,
            "economie_certifiee_cad":None}

def inspect(entries):
    """Ordre déclaré vérifié, sans validation des faits, des signatures ou des montants."""
    require(len(entries)<=48,"DECLARATIONS_EXCESSIVES")
    present={}
    counts=Counter()
    for raw in entries:
        item=review(raw)
        code,step=item["cle"]
        already=present.setdefault(code,{})
        require(step not in already,"CONTROLE_DUPLIQUE")
        index=GATES.index(step)
        require(all(prior in already and
                    already[prior]=="EXAMEN_DECLARE_SANS_CERTIFICATION"
                    for prior in GATES[:index]),
                "PREALABLES_NON_ATTESTES_PAR_DECLARATIONS")
        already[step]=item["statut"]
        counts[item["statut"]]+=1
    return {"controles_declares":len(entries),
            "organismes_avec_controles_declares":len(present),
            "statuts_agreges":dict(sorted(counts.items()))}

def report(cfg,rows,stats):
    return {
      "schema_version":"P53U-RAPPORT-1",
      "organismes_cibles":6,
      "positions_documentaires_p53q":102,
      "points_controle_independance":len(rows),
      "exigences_concretes_a_verifier":cfg["etat_initial"]["points_a_examiner"],
      "declarations_formellement_examinees":stats["controles_declares"],
      "organismes_avec_declarations":stats["organismes_avec_controles_declares"],
      "statuts_agreges":stats["statuts_agreges"],
      "personnes_reelles_independantes_attestees":0,
      "avis_juridiques_independants_signes":0,
      "avis_comptables_independants_signes":0,
      "documents_provenance_authentifies":0,
      "appariements_transactionnels_certifies":0,
      "demandes_externes_envoyees":0,
      "economie_operationnelle_certifiee_cad":None,
      "taux_fiscaux_adoptes":0,
      "preuves_F01_F20_validees":0,
      "montants_Nova_inconnus":1320,
      "reduction_emplois_autorisee":False,
      "degradation_services_autorisee":False,
      "fusion_autorisee":False,
      "decision":NO_GO,
    }

def save_new(path,value):
    p=Path(path)
    require(not p.exists() and not p.is_symlink(),"SORTIE_EXISTANTE_NON_ECRASEE")
    with p.open("x",encoding="utf-8") as f:
        f.write(json.dumps(value,indent=2,ensure_ascii=False,sort_keys=True)+"\n")

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rapport")
    ap.add_argument("--matrice")
    ap.add_argument("--declaration",action="append",default=[])
    ap.add_argument("--exiger-certification-independante",action="store_true")
    args=ap.parse_args(argv)
    try:
        require(len(args.declaration)<=48,"TROP_DE_DECLARATIONS")
        paths=[Path(z) for z in (args.rapport,args.matrice) if z]
        require(len({x.resolve() for x in paths})==len(paths)
                and all(not x.exists() and not x.is_symlink() for x in paths),
                "SORTIE_EXISTANTE_OU_DUPLIQUEE")
        cfg,parents=setup()
        rows=matrix(cfg,parents)
        entries=[read(path) for path in args.declaration]
        stats=inspect(entries)
        bilan=report(cfg,rows,stats)
        if args.rapport:save_new(args.rapport,bilan)
        if args.matrice:
            save_new(args.matrice,{"schema_version":"P53U-MATRICE-1",
              "statut":"CONTROLES_POTENTIELS_NON_CERTIFIES","positions":rows})
        print(json.dumps(bilan,sort_keys=True,ensure_ascii=False))
        return 3 if args.exiger_certification_independante else 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P53U_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
