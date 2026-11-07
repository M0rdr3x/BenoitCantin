#!/usr/bin/env python3
"""P54H : préparer des mandats CPA/juriste sans engagement ni certification.

Les déclarations optionnelles sont privées. Les critères décrivent des contrôles
à EFFECTUER par des personnes; aucun résultat ne prouve l'inscription, l'absence
de conflit, le consentement du client ni la signature d'un avis.
"""
import argparse
import json
from pathlib import Path
import re
import sys

import controler_decisions_procedurales_nova_p54g as upstream
import gerer_contre_revues_nova_p54f as private

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"projets/projet-nova/etudes/P54H_MANDATS_EXPERTS_INDEPENDANTS_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
MANDATS=(
 ("MANDAT-COMPTABLE-2024","COMPTABILITE_MUNICIPALE_2024",
  "REVUE_DOCUMENTAIRE_COMPTABLE_DES_DEPENSES_MIXTES_ET_DE_LA_CONSOLIDATION"),
 ("MANDAT-JURIDIQUE-2024","DROIT_MUNICIPAL_ET_MANDAT_D_AUDIT",
  "PORTEE_JURIDIQUE_RAVQ_1435_ET_LIMITE_AVIS_AUDIT"),
)
REQUIREMENTS=(
 "COMPETENCE_PERTINENTE_DOCUMENTEE",
 "ORDRE_PROFESSIONNEL_ET_PERMIS_EXAMINES",
 "INDEPENDANCE_ET_CONFLITS_DECLARÉS",
 "LIENS_CLIENTS_CABINET_ANTERIEURS_EXAMINES",
 "REMUNERATION_ET_INCITATIONS_VERIFIEES",
 "CONFIDENTIALITE_ET_SECRET_PROFESSIONNEL",
 "MANDAT_ECRIT_PORTEE_LIMITES_LIVRABLES",
 "SOURCES_PRIMAIRES_ET_HACHAGES_DOCUMENTES",
 "DROITS_ACCES_AUX_GRANDS_LIVRES_VERIFIES",
 "REGLES_CONSOLIDATION_ET_PARTIES_LIEES",
 "IMPACT_EMPLOIS_ET_SERVICES_PUBLICS",
 "AVIS_DATE_SIGNE_ET_AUTHENTIFIE_MANUELLEMENT",
)
CONFLITS=("NON_EXAMINE","ABSENCE_DECLAREE_NON_VERIFIEE",
          "POTENTIEL","APPARENT","REEL")
HONORAIRES=("NON_EXAMINE","MODALITES_DECLAREES_SANS_INTERET_AU_RESULTAT",
           "INCITATION_AU_RESULTAT_A_EVALUER")
STEPS=("NON_DECLARÉ","EXAMINÉ_SANS_ATTESTATION")
GUARDS={
 "aucun_expert_recrute_ou_contacte",
 "absence_conflit_declaree_pas_verifiee",
 "inscription_professionnelle_non_authentifiee",
 "aucune_signature_authentifiee","aucun_avis_independant_recu",
 "aucun_frais_ni_honoraire_engage","pas_de_transmission_vers_un_tiers",
 "identites_reelles_et_pieces_confidentielles_hors_git",
 "ne_pas_diffuser_candidats_ou_num_permis",
 "aucune_economie_financiere_certifiee",
 "aucun_chiffre_financier_invente",
 "aucune_fermeture_des_dossiers_p54e",
 "protections_emploi_et_services",
 "aucune_double_elimination_ville_rtc",
 "scenarios_quebec_canada_souverain_distincts",
 "aucune_fusion_main","aucun_changement_sinjira",
}
URLS=[
 "https://cpaquebec.ca/fr/membres-cpa/deontologie/devoirs-generaux/conflit-dinterets/le-conflit-dinterets/",
 "https://cpaquebec.ca/fr/trouver-un-cpa/tableau-de-lordre/",
 "https://www.legisquebec.gouv.qc.ca/fr/document/rc/B-1,%20r.%203.1/",
]
OPAQUE=re.compile(r"^CAND-[A-Z0-9]{4,12}$")
def need(ok,why):
    if not ok:raise ValueError(why)

def configuration():
    prev=upstream.config()
    data=json.loads(CFG.read_text("utf-8"))
    expected={
      "schema_version":"P54H-1","date_reference":"2026-10-24",
      "exercice_source":2024,
      "source":"P54G_REGISTRE_DECISIONS_PROCEDURALES_2024.json",
      "source_p54d_run":40120462237,
      "mandats":[{
        "code":code,"specialite":specialty,"objet":purpose,
        "dossiers":prev["dossiers"],
      } for code,specialty,purpose in MANDATS],
      "controles_qualification":list(REQUIREMENTS),
      "risques_conflit":list(CONFLITS),
      "etat_remuneration":list(HONORAIRES),
      "etapes":list(STEPS),
      "sources_deontologiques":URLS,
      "garde_fous":{k:True for k in GUARDS},
      "etat_initial":{
        "mandats_a_preparer":2,
        "controles_de_qualification_non_attestes":24,
        "experts_engages":0,"ordres_professionnels_verifies":0,
        "avis_originaux_signes_recus":0,"dossiers_p54e_restants":4,
        "controles_p54b_restants":96,"controles_p54c_restants":8,
        "economies_certifiees_cad":None,"decision":NO_GO,
      },
    }
    need(data==expected,"P54H_CHAINE_ET_SCHEMA_ALTERES")
    return data

def template(cfg):
    return {
      "schema_version":"P54H-CANDIDATURES-LOCALES-1",
      "exercice_source":2024,
      "ancrage_P54D_run":40120462237,
      "declarations":[],
    }

def analyze_declarations(doc,cfg):
    expected=template(cfg)
    need(type(doc) is dict and set(doc)==set(expected)
         and doc["schema_version"]==expected["schema_version"]
         and type(doc["exercice_source"]) is int
         and doc["exercice_source"]==2024
         and type(doc["ancrage_P54D_run"]) is int
         and doc["ancrage_P54D_run"]==40120462237
         and type(doc["declarations"]) is list
         and len(doc["declarations"])<=2,
         "FICHE_CANDIDATURES_INVALIDE")
    valid_mandats={x[0] for x in MANDATS}
    encountered=set();risk_counts={x:0 for x in CONFLITS}
    completed=0;attention=0
    for row in doc["declarations"]:
        need(type(row) is dict and set(row)=={
            "mandat","code_opaque","verification_appartenance_declaree",
            "conflit","honoraires","controles_declares",
            "dossier_de_pieces_privées_declare",
            "contact_reel_effectue","mandat_accepte_verifie",
            "avis_signe_authentifie","qualification_verifiee_par_systeme",
            "autorisation_financiere"},
            "CHAMPS_CANDIDAT_INATTENDUS")
        code=row["mandat"]
        who=row["code_opaque"]
        need(type(code) is str and code in valid_mandats
             and code not in encountered
             and type(who) is str and bool(OPAQUE.fullmatch(who)),
             "CANDIDATURE_INCONNUE_OU_DUPLIQUEE")
        encountered.add(code)
        need(row["verification_appartenance_declaree"] in
             ("NON_VERIFIEE","CONTROLE_HUMAIN_DECLARE_NON_AUTHENTIFIE")
             and row["conflit"] in CONFLITS
             and row["honoraires"] in HONORAIRES,
             "QUALIFICATION_CONFLIT_OU_REMUNERATION_HORS_SCHEMA")
        checklist=row["controles_declares"]
        need(type(checklist) is list
             and len(checklist)==len(set(checklist))
             and all(type(c) is str and c in REQUIREMENTS for c in checklist),
             "CONTROLES_NON_RECONNUS_OU_DUPLIQUES")
        need(row["dossier_de_pieces_privées_declare"] in
             ("AUCUNE_PIECE","PIECES_HORS_GIT_DECLAREES")
             and all(row[k] is False for k in (
               "contact_reel_effectue","mandat_accepte_verifie",
               "avis_signe_authentifie","qualification_verifiee_par_systeme",
               "autorisation_financiere")),
             "ACTE_HUMAIN_OU_CERTIFICATION_FICTIVE")
        completed+=len(checklist)
        risk_counts[row["conflit"]]+=1
        if row["conflit"] in ("POTENTIEL","APPARENT","REEL") or row[
           "honoraires"]=="INCITATION_AU_RESULTAT_A_EVALUER":
            attention+=1
    return {
      "declarations_non_authentifiees":len(encountered),
      "controles_declares_examines_non_attestes":completed,
      "dossiers_risque_ou_incitation_a_expertiser":attention,
      "risques_conflit_declares":{k:v for k,v in risk_counts.items() if v},
    }

def build_mandates(cfg):
    return {"schema_version":"P54H-TERMS-DE-REFERENCE-1",
            "mandats":[{
               "code":m["code"],
               "specialite":m["specialite"],
               "objet":m["objet"],
               "dossiers":m["dossiers"],
               "controles":[{"code":x,"deja_atteste":False}
                            for x in REQUIREMENTS],
               "statut":"PROJET_NON_TRANSMIS",
               "livrables_reçus":0,
               "expert_mandate":False,
               "conclusion_certifiee":False
            } for m in cfg["mandats"]],
            "decision":NO_GO}

def report(cfg,stats=None):
    return {
      "schema_version":"P54H-BILAN-1",
      "mandats_prepares":len(cfg["mandats"]),
      "controles_qualification":len(REQUIREMENTS)*len(cfg["mandats"]),
      "declarations_locales":stats or {
         "declarations_non_authentifiees":0,
         "controles_declares_examines_non_attestes":0,
         "dossiers_risque_ou_incitation_a_expertiser":0,
         "risques_conflit_declares":{},
      },
      "mandats_transmis_et_acceptes_authentifies":0,
      "appartenances_ordre_verifiees_par_procedure_independante":0,
      "absences_conflit_certifiees":0,
      "avis_independants_originaux_signes_reçus":0,
      "dossiers_financiers_clos":0,
      "controles_p54b_en_attente":96,
      "controles_p54c_en_attente":8,
      "economies_certifiees_cad":None,
      "reductions_effectifs_services_autorisees":False,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mandats")
    parser.add_argument("--bilan")
    parser.add_argument("--declarations-locales")
    parser.add_argument("--modele-prive")
    parser.add_argument("--exiger-avis-certifie",action="store_true")
    arg=parser.parse_args(argv)
    try:
        destinations=[Path(p) for p in (arg.mandats,arg.bilan,arg.modele_prive) if p]
        need(len({p.resolve() for p in destinations})==len(destinations)
             and all(not p.exists() and not p.is_symlink() for p in destinations),
             "DESTINATIONS_EXISTANTES_OU_DUPLIQUEES")
        cfg=configuration()
        stats=None
        if arg.declarations_locales:
            source=private.private_file(arg.declarations_locales,32768)
            need(all(source.resolve()!=x.resolve() for x in destinations),
                 "DESTINATION_ET_ENTREE_IDENTIQUES")
            stats=analyze_declarations(json.loads(source.read_text("utf-8")),cfg)
        if arg.modele_prive:
            private.write_new(arg.modele_prive,template(cfg),private=True)
        if arg.mandats:
            private.write_new(arg.mandats,build_mandates(cfg))
        summary=report(cfg,stats)
        if arg.bilan:private.write_new(arg.bilan,summary)
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        return 3 if arg.exiger_avis_certifie else 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P54H_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
