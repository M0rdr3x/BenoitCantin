#!/usr/bin/env python3
"""P54N — paquet public de passation humaine pour les quatre dossiers P54E.

Ne lit pas les jetons bruts ni les fichiers privés. Aucune transmission,
sollicitation, authentification, décision financière ou clôture automatique.
"""
import argparse
import json
from pathlib import Path
import sys

import evaluer_recevabilite_authentifications_nova_p54m as p54m

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54N_PASSATION_HUMAINE_DOSSIERS_2024.json"
P54E=ROOT/"projets/projet-nova/etudes/P54E_PLAN_REVUE_HUMAINE_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
REQUESTS=(
 ("ORIGINAUX_ET_IDENTIFICATION","EXAMINATEUR_DOCUMENTAIRE",
  "COPIES_SOURCES_DATEES_ET_EMPREINTES",
  "VALIDER_LES_DEUX_PDF_SOURCES_ET_RETROUVER_L_OCCURRENCE_EXACTE"),
 ("CONCORDANCE_FOLIO_PAGE","EXAMINATEUR_DOCUMENTAIRE",
  "TABLE_CORRESPONDANCE_PAGES_FOLIOS",
  "IDENTIFIER_PAGINATION_ET_ZONE_SANS_PREJUGER_DE_LA_NATURE_DU_JETON"),
 ("CONTEXTE_ET_CATEGORIE","EXAMINATEUR_DOCUMENTAIRE",
  "QUALIFICATION_INDIVIDUELLE_DOCUMENTEE",
  "DISTINGUER_DATE_FOLIO_REFERENCE_IDENTIFIANT_OU_VALEUR_A_EXAMINER"),
 ("EXERCICE_UNITE_ET_COLONNE","EXPERT_COMPTABLE_A_MANDATER",
  "NOTE_UNITES_COLONNES_SIGNES",
  "VERIFIER_EXERCICE_2024_ET_NATURE_MONETAIRE_AVANT_TOUTE_QUANTIFICATION"),
 ("PERIMETRE_REGLEMENTAIRE","EXPERT_JURIDIQUE_A_MANDATER",
  "AVIS_PORTEE_RAVQ_1435",
  "DISTINGUER_AUDIT_DEPENSES_MIXTES_ET_AUDIT_HYPOTHETIQUE_NOVA"),
 ("OPERATIONS_RECIPROQUES","EXPERT_COMPTABLE_A_MANDATER",
  "TABLE_RAPPROCHEMENT_CONSOLIDATION",
  "VERIFIER_VILLE_RTC_SOMHAC_ET_ELIMINATIONS_AVANT_TOUT_GAIN"),
 ("REGLES_CONFIDENTIALITE","RESPONSABLE_DONNEES_HABILITE",
  "AUTORISATIONS_ET_CONSERVATION_HORS_GIT",
  "NE_PAS_PUBLIER_ORIGINAUX_PROTEGES_IDENTITES_JETONS"),
 ("CONTRE_EXAMEN","CONTRE_REVISEUR_INDEPENDANT_A_MANDATER",
  "EXAMEN_CONTRADICTOIRE_TRACE",
  "MAINTENIR_DESACCORD_ET_SUSPENSION_NON_RESOLUS"),
 ("GARANTIES_SOCIALES","RESPONSABLE_POLITIQUES_PUBLIQUES_A_MANDATER",
  "EVALUATION_CONTINUITE_SERVICES_EMPLOIS",
  "AUCUNE_REDUCTION_SUR_HYPOTHESE_NON_ETAYEE"),
 ("AUTHENTIFICATION_ET_DECISION","AUTORITE_HUMAINE_COMPETENTE",
  "AVIS_ORIGINAL_DATE_SIGNE_ET_AUTHENTIFIE_MANUELLEMENT",
  "DECISION_INSTITUTIONNELLE_HORS_LOGICIEL_APRES_EXPERTISE"),
)
GUARDS={
 "aucune_anomalie_financiere_demontree","aucune_economie_certifiee",
 "quatre_dossiers_non_clos","une_date_probable_non_resolue",
 "deux_audits_specialises_ne_certifient_pas_nova",
 "aucune_pression_sur_emploi_ou_services",
 "aucun_double_compte_consolidation_ville_rtc_somhac",
 "aucun_contact_avec_un_tiers_par_le_logiciel",
 "aucune_signature_ou_qualification_authentifiee",
 "originaux_proteges_hors_git","aucun_merge_main",
 "aucun_changement_sinjira",
 "quebec_dans_canada_et_souverain_hypothetique_distincts",
 "no_go_automatique",
}
MANDATES=(
 "EXPERT_COMPTABLE_A_MANDATER","EXPERT_JURIDIQUE_A_MANDATER",
 "CONTRE_REVISEUR_INDEPENDANT_A_MANDATER",
)
DELIVERABLES=(
 "ORIGINAUX_DOCUMENTES","OBSERVATIONS_QUALIFIEES",
 "CONTRE_REVUE_RESOLUE","AVIS_COMPTABLE_INDEPENDANT_SI_PERTINENT",
 "AVIS_JURIDIQUE_INDEPENDANT_SI_PERTINENT",
 "SIGNATURES_AUTHENTIFIEES_PAR_PROCEDURE_HUMAINE",
 "PERIMETRE_UNITES_CONSOLIDATION_VERIFIES",
 "GARANTIES_EMPLOIS_SERVICES",
 "DECISION_AUTORITE_COMPETENTE_EXTERNE_AU_CODE",
)
INITIAL={
 "dossiers_ouverts":4,"taches_par_dossier":10,
 "positions_a_instruire":40,
 "verifications_p54b_non_attestees":96,
 "verifications_p54c_non_attestees":8,
 "expertises_reelles_obtenues":0,
 "decisions_financieres_certifiees":0,
 "economies_certifiees_cad":None,"decision":"NO_GO_AUTOMATIQUE",
}
SOURCES={
 "ville":"https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf",
 "mamh":"https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf",
}

def need(ok,why):
    if not ok:raise ValueError(why)

def configuration():
    upstream=p54m.config()
    original=json.loads(P54E.read_text("utf-8"))
    data=json.loads(CONFIG.read_text("utf-8"))
    expected={
      "schema_version":"P54N-1","date_reference":"2026-10-24",
      "source_jalons":["P54D","P54E","P54M"],
      "source_exercice":2024,"source_p54d_run":40120462237,
      "dossiers":original["cases"],
      "taches":[{
          "code":code,"responsable":role,"livrable":out,"condition":condition,
        } for code,role,out,condition in REQUESTS],
      "categorie_adjacente":{
          "type":"DATE_PROBABLE_NON_RESOLUE","nombre":1,
          "exiger_confirmation_humaine":True},
      "roles_mandat":list(MANDATES),
      "exigences_sortie":list(DELIVERABLES),
      "protections":{g:True for g in GUARDS},
      "etat_initial":INITIAL,
    }
    need(data==expected and original["schema_version"]=="P54E-1"
         and original["source_run_p54d"]==40120462237
         and original["initial"]["date_probable_not_final"]==1
         and len(original["cases"])==4
         and all(x["classification"]=="INDETERMINE"
                 for x in original["cases"])
         and [x["id"] for x in original["cases"]]==upstream["dossiers"]
         and len(original["gates"])==10,
         "CHAINAGE_P54E_M_NON_CONFORME")
    return data

def workpack(cfg):
    work=[]
    for row in cfg["dossiers"]:
        work.append({
          "dossier_id":row["id"],
          "publication":row["source"],
          "url_source_publique":SOURCES[row["source"]],
          "index_page_pdf_zero_based":row["pdf_index"],
          "zone_approximative":row["zone"],
          "index_observation_p54d":row["observation_index"],
          "classification_initiale":"INDETERMINE",
          "localisation_exacte_a_confirmer":True,
          "instructions":[{
             "code":task["code"],"role_cible":task["responsable"],
             "livrable_attendu":task["livrable"],
             "critere_de_reception":task["condition"],
             "etat":"A_INSTRUIRE",
             "piece_originale_recue":False,
             "verification_professionnelle_obtenue":False,
           } for task in cfg["taches"]],
          "revue_contradictoire_effectuee":False,
          "cloture_autorisee":False,
        })
    need(len(work)==4 and sum(len(r["instructions"]) for r in work)==40,
         "PAQUET_INCOMPLET")
    return {
      "schema_version":"P54N-PAQUET-1",
      "exercice":2024,
      "source_p54d_run":40120462237,
      "objet":"VERIFICATION_DES_OCCURRENCES_LEXICALES_NON_APPARIEES",
      "dossiers":work,
      "observation_distincte_date_probable":{
          "nombre":1,"qualif_definitive":False,
          "reste_a_verifier_hors_git":True},
      "livrables_preparatoires":list(DELIVERABLES),
      "mandats_reels_non_encore_attribues":list(MANDATES),
      "economies_certifiees_cad":None,
      "decision":NO_GO,
    }

def report(cfg):
    return {
      "schema_version":"P54N-BILAN-1","exercice":2024,
      "dossiers_a_instruire":4,
      "taches_documentaires_a_instruire":40,
      "observation_date_probable_non_resolue":1,
      "controles_p54b_non_attestes":96,
      "controles_p54c_non_attestes":8,
      "mandats_effectifs_attribues":0,
      "sources_privees_reçues":0,
      "avis_authentifies":0,
      "conclusions_financieres_certifiees":0,
      "economies_certifiees_cad":None,
      "dossiers_clos":0,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def markdown(pack,summary):
    lines=[
      "# P54N — Dossier de passation aux vérificateurs habilités",
      "",
      "**Travail préparatoire non transmis — aucun mandat signé.**",
      "",
      "Objet : quatre occurrences indéterminées des rapports financiers 2024",
      "de la Ville de Québec et du MAMH. Les positions PDF sont des index",
      "commençant à zéro; les zones sont approximatives.",
      "",
      "Aucune de ces occurrences n'est une anomalie monétaire établie.",
      "Une cinquième occurrence (année ou date probable) reste non résolue.",
      "",
    ]
    for entry in pack["dossiers"]:
        lines.extend([
          "## "+entry["dossier_id"],
          "",
          "Publication : "+entry["publication"]+
          " ; index PDF : "+str(entry["index_page_pdf_zero_based"])+
          " ; zone : "+entry["zone_approximative"]+".",
          "",
          "Source publique : "+entry["url_source_publique"],
          "",
          "| Point de travail | Responsable à désigner | Livrable attendu |",
          "|---|---|---|",
        ])
        for x in entry["instructions"]:
            lines.append("| "+x["code"]+" | "+x["role_cible"]+" | "+
                         x["livrable_attendu"]+" |")
        lines.append("")
    lines.extend([
      "## Seuils de non-transmission et conditions de progression",
      "",
      "Les pièces privées, jetons exacts, signatures, données personnelles,",
      "grands livres et correspondances doivent rester hors GitHub.",
      "Le dossier ne doit être envoyé qu'après autorisation humaine explicite.",
      "Tout destinataire doit être habilité; permis, mandat, conflits d'intérêts",
      "et signatures sont à vérifier par les voies professionnelles appropriées.",
      "",
      "Le travail progresse seulement après identification précise et",
      "qualification de chaque occurrence, contre-examen distinct et examen",
      "des unités, périmètres et écritures consolidées lorsque pertinents.",
      "Une différence de texte n'est pas une économie.",
      "",
      "Aucun gain issu des écritures Ville–RTC–SOMHAC déjà éliminées",
      "ne peut être compté une seconde fois. Emplois et services protégés.",
      "Québec au Canada et souveraineté hypothétique restent distincts.",
      "",
      "La CI et les fiches P54D–P54M ne certifient aucun avis Nova.",
      "Les 96 contrôles P54B et huit contrôles P54C restent ouverts.",
      "",
      "**NO_GO_AUTOMATIQUE — aucune décision, économie, sollicitation",
      "professionnelle, fusion main ou modification SINJIRA.**",
      "",
    ])
    return "\n".join(lines)

def write_new(path,content):
    target=Path(path)
    need(not target.exists() and not target.is_symlink(),
         "REFUS_ECRASEMENT")
    need(target.parent.is_dir() and not target.parent.is_symlink(),
         "REPERTOIRE_SORTIE_INVALIDE")
    if type(content) is str:
        target.write_text(content,encoding="utf-8")
    else:
        target.write_text(json.dumps(content,ensure_ascii=False,
                                    indent=2,sort_keys=True)+"\n",
                          encoding="utf-8")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dossier")
    parser.add_argument("--instructions")
    parser.add_argument("--bilan")
    parser.add_argument("--exiger-transmission",action="store_true")
    args=parser.parse_args(argv)
    try:
        destinations=[Path(v) for v in (
          args.dossier,args.instructions,args.bilan) if v]
        need(len({x.resolve() for x in destinations})==len(destinations)
             and all(not x.exists() and not x.is_symlink()
                     for x in destinations),
             "SORTIE_EXISTANTE_OU_DUPLIQUEE")
        cfg=configuration()
        packet=workpack(cfg)
        summary=report(cfg)
        if args.dossier:write_new(args.dossier,packet)
        if args.instructions:
            write_new(args.instructions,markdown(packet,summary))
        if args.bilan:write_new(args.bilan,summary)
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        return 3 if args.exiger_transmission else 0
    except (OSError,ValueError,KeyError,TypeError,
            UnicodeError,json.JSONDecodeError) as exc:
        print("P54N_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
