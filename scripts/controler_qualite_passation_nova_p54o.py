#!/usr/bin/env python3
"""P54O : contrôle pré-remise du paquet P54N et inventaire des vrais blocages.

Ne contacte aucun destinataire, n'examine aucune preuve privée et ne débloque
aucune transmission. La vérification d'égalité est structurelle et non probante.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import preparer_passation_humaine_nova_p54n as p54n

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54O_CONTROLE_QUALITE_PASSATION_2024.json"
P54D=ROOT/"projets/projet-nova/etudes/P54D_OBSERVATIONS_REELLES_2026_10_24.json"
NO_GO="NO_GO_AUTOMATIQUE"
EXPECTED_SHA={
 "ville":"b3ee3e671f7bf98e56c7d42b5e8b6c34de02a96c9dc1c96469819fa4dbfa7399",
 "mamh":"4323c87d2114b58cf7a093c08f3b30327e949db91b9beb46a627eac1ecb4fc00",
}
DATE_REFERENCE={
 "id":"P54O-DATE-001","source":"mamh","pdf_index":162,
 "observation_index":2,"zone":"FIN",
 "classification":"ANNEE_DATE_PROBABLE","dossier_p54e":False,
}
BLOCKS=(
 ("AUTORISATION_HUMAINE_DE_PASSATION","GOUVERNANCE_A_DESIGNER",
  "AVANT_REMISE","AUTORISATION_EXPLICITE_DESTINATAIRE_ET_PORTEE"),
 ("IDENTIFICATION_DESTINATAIRE_HABILITE","GOUVERNANCE_A_DESIGNER",
  "AVANT_REMISE","QUALIFICATION_DESTINATAIRE_ET_GESTION_DES_CONFLITS"),
 ("ACCES_ORIGINAUX_HORS_GIT","RESPONSABLE_DONNEES_A_DESIGNER",
  "AVANT_EXAMEN","CONTROLE_DES_ACCES_ET_PROVENANCE_COPIES_SOURCE"),
 ("LOCALISATION_CINQ_OCCURRENCES","EXAMINATEUR_DOCUMENTAIRE_A_DESIGNER",
  "EXAMEN_INITIAL","REPERE_INDIVIDUEL_SUR_PAGES_ET_DIAGNOSTIC_PRIVE"),
 ("QUALIFICATION_DOCUMENTAIRE_CINQ_OCCURRENCES",
  "EXAMINATEUR_DOCUMENTAIRE_A_DESIGNER","EXAMEN_INITIAL",
  "CATEGORIE_CONFIRME_PAR_PIECE_PAS_PAR_HEURISTIQUE"),
 ("REVUE_CONTRADICTOIRE_DISTINCTE","CONTRE_REVISEUR_A_MANDATER",
  "APRES_EXAMEN","RESERVES_DESACCORDS_ET_SUSPENSIONS_EXPRESSES"),
 ("AVIS_JURIDIQUE_CIBLE_SI_NECESSAIRE","JURISTE_A_MANDATER",
  "SI_PERTINENT","PORTEE_RAVQ_1435_ET_MANDAT_SPECIALISE"),
 ("CONTROLE_COMPTABLE_CIBLE_SI_MONETAIRE","CPA_A_MANDATER",
  "SI_PERTINENT","UNITE_SIGNE_PERIMETRE_ET_ELIMINATIONS_RECIPROQUES"),
 ("AUTHENTIFICATION_DES_AVIS_ET_PERMIS","AUTORITE_HUMAINE_HABILITEE",
  "AVANT_TOUTE_CONCLUSION","ORIGINAUX_SIGNATURES_STATUTS_CONFLITS_VERIFIES"),
 ("DECISION_INSTITUTIONNELLE_DISTINCTE","AUTORITE_COMPETENTE",
  "HORS_LOGICIEL","RESOLUTION_ECRITE_ET_AUTORISATIONS_REELLES"),
)
GUARDS={
 "aucune_transmission_automatique",
 "aucune_solicitation_automatique",
 "aucun_original_prive_dans_ci",
 "aucun_identifiant_personne_dans_bilan",
 "aucun_token_numerique_brut",
 "cinq_occurrences_distinctes",
 "date_probable_non_resolue",
 "quatre_dossiers_p54e_non_clos",
 "quarante_taches_p54n_non_attestees",
 "comparabilite_p54b_p54c_ouverte",
 "preuve_hachage_non_certifiante",
 "authenticite_humaine_exigee",
 "avis_reglementaire_specialise_non_audit_nova",
 "pas_de_double_compte_ville_rtc_somhac",
 "aucune_reduction_emploi_ou_service",
 "scenarios_constitutionnels_separes",
 "interdiction_GO_automatique",
 "main_non_fusionnee",
 "sinjira_inchange",
}
INITIAL={
 "dossiers_p54e_ouverts":4,
 "occurrences_a_qualifier":5,
 "taches_p54n_non_attestees":40,
 "controles_p54b_restants":96,
 "controles_p54c_restants":8,
 "conditions_non_levees":10,
 "autorisations_effectives_reçues":0,
 "mandats_reels_signes":0,
 "avis_originaux_authentifies":0,
 "economies_certifiees_cad":None,
 "decision":NO_GO,
}

def need(condition,why):
    if not condition:raise ValueError(why)

def configuration():
    upstream=p54n.configuration()
    observed=json.loads(P54D.read_text("utf-8"))
    expected={
      "schema_version":"P54O-1","date_reference":"2026-10-24",
      "source_jalon":"P54N","source_p54d_run":40120462237,
      "exercice":2024,
      "comparaison":{
        "ville_pdf_index":102,"mamh_pdf_index":162,
        "occurrences_totales":5,"occurrences_indeterminees":4,
        "date_probable_non_finale":1},
      "observation_date_probable":DATE_REFERENCE,
      "conditions_pre_passation":[
        {"code":code,"responsable_cible":role,
         "phase":phase,"critere_humain":proof}
        for code,role,phase,proof in BLOCKS],
      "protections":{key:True for key in GUARDS},
      "etat_initial":INITIAL,
    }
    need(json.loads(CONFIG.read_text("utf-8"))==expected,
         "REGISTRE_P54O_MODIFIE")
    need(upstream["source_p54d_run"]==observed["run_id"]==40120462237
         and observed["schema_version"]=="P54D-OBSERVATIONS-CI-1"
         and observed["source_documents"]==EXPECTED_SHA
         and observed["pages"]=={"ville":102,"mamh":162}
         and observed["occurrences"]=={"ville":1,"mamh":4,"total":5}
         and observed["classifications"]=={
            "ANNEE_DATE_PROBABLE":1,"INDETERMINE":4}
         and len(observed["observations"])==5,
         "SOURCE_P54D_NON_CONCORDANTE")
    observations=observed["observations"]
    source_cases={c["observation_index"]:c
                  for c in upstream["dossiers"]}
    need(set(source_cases)=={0,1,3,4}
         and all(
           observations[i]["source"]==case["source"]
           and observations[i]["zone_approximative"]==case["zone"]
           and observations[i]["categorie_indicative"]=="INDETERMINE"
           and case["classification"]=="INDETERMINE"
           and observed["pages"][case["source"]]==case["pdf_index"]
           for i,case in source_cases.items()),
         "LES_QUATRE_DOSSIERS_NE_CORRESPONDENT_PAS_A_P54D")
    fifth=observations[2]
    need(fifth["source"]==DATE_REFERENCE["source"]
         and fifth["zone_approximative"]==DATE_REFERENCE["zone"]
         and fifth["categorie_indicative"]==DATE_REFERENCE["classification"]
         and observed["pages"][fifth["source"]]==DATE_REFERENCE["pdf_index"]
         and fifth["qualification"]=="NON_CERTIFIEE"
         and upstream["categorie_adjacente"]["exiger_confirmation_humaine"]
         and upstream["etat_initial"]["positions_a_instruire"]==40,
         "CINQUIEME_OCCURRENCE_DATE_NON_TRACEABLE")
    return expected

def canonical_sources(cfg):
    """Canonical public handoff, never raw private evidence."""
    base=p54n.configuration()
    packet=p54n.workpack(base)
    instructions=p54n.markdown(packet,p54n.report(base))
    need(len(packet["dossiers"])==4 and
         sum(len(row["instructions"]) for row in packet["dossiers"])==40
         and packet["economies_certifiees_cad"] is None
         and packet["decision"]==NO_GO,
         "PAQUET_SOURCE_NON_NEUTRE")
    return packet,instructions

def validate_public_inputs(cfg,packet=None,instructions=None):
    actual,readme=canonical_sources(cfg)
    if packet is not None:
        need(type(packet) is dict and packet==actual,
             "PAQUET_P54N_MODIFIE_OU_AFFIRMATIONS_NON_VERIFIEES")
    if instructions is not None:
        need(type(instructions) is str and instructions==readme,
             "INSTRUCTIONS_P54N_MODIFIEES")
    return actual,readme

def matrix(cfg,pack):
    observed=[]
    for case in pack["dossiers"]:
        observed.append({
          "identifiant":case["dossier_id"],
          "source":case["publication"],
          "index_pdf_base_zero":case["index_page_pdf_zero_based"],
          "zone":case["zone_approximative"],
          "observation_index":case["index_observation_p54d"],
          "classification":"INDETERMINE",
          "localisation_exacte_et_nature_a_revoir":True,
          "pret_a_declarer_financier":False,
          "statut":"NON_INSTRUIT",
          "est_dossier_p54e":True,
        })
    date=cfg["observation_date_probable"]
    observed.append({
       "identifiant":date["id"],"source":date["source"],
       "index_pdf_base_zero":date["pdf_index"],
       "zone":date["zone"],"observation_index":date["observation_index"],
       "classification":date["classification"],
       "localisation_exacte_et_nature_a_revoir":True,
       "pret_a_declarer_financier":False,
       "statut":"NON_INSTRUIT",
       "est_dossier_p54e":False,
    })
    need(len(observed)==5 and
         {x["observation_index"] for x in observed}==set(range(5)),
         "OBSERVATIONS_ABSENTES_OU_DUPLIQUEES")
    blockers=[{
        "reference":item["code"],
        "phase":item["phase"],
        "responsable_a_designer":item["responsable_cible"],
        "verification_humaine_attendue":item["critere_humain"],
        "etat":"NON_LEVE",
        "preuve_reçue_et_authentifiee":False,
    } for item in cfg["conditions_pre_passation"]]
    return {
      "schema_version":"P54O-PLAN-1",
      "exercice":2024,
      "run_reference_p54d":40120462237,
      "copies_pdf_sha256_reference":EXPECTED_SHA,
      "observations":observed,
      "points_bloquants":blockers,
      "instructions_p54n_a_instruire":40,
      "remise_externe_autorisee":False,
      "dossiers_p54e_clos":0,
      "economie_certifiee_cad":None,
      "decision":NO_GO,
    }

def summary(cfg,plan):
    return {
      "schema_version":"P54O-BILAN-1","exercice":2024,
      "integrite_structurelle_du_paquet":"CONFORME_AUX_SOURCES_VERSIONNEES",
      "originaux_prives_et_signatures_examines":False,
      "dossiers_p54e_ouverts":4,
      "occurrences_indeterminees":4,
      "occurrence_date_probable_non_certifiee":1,
      "observations_a_localiser":len(plan["observations"]),
      "taches_p54n_a_instruire":40,
      "conditions_humaines_non_levees":len(plan["points_bloquants"]),
      "controles_p54b_non_attestes":96,
      "controles_p54c_non_attestes":8,
      "autorisations_de_transmission_obtenues":0,
      "mandats_professionnels_reellement_signes":0,
      "avis_originaux_independants_authentifies":0,
      "economies_certifiees_cad":None,
      "pret_a_transmettre":False,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def markdown_report(plan,report):
    lines=[
      "# P54O — Précontrôle du dossier de passation P54N",
      "",
      "**Contrôle structurel conforme. Aucun original, mandat ou avis reçu.**",
      "",
      "La conformité numérique du paquet ne constitue pas une autorisation",
      "de remise ou une certification de preuves. Les originaux restent privés.",
      "",
      "## Cinq observations à retrouver sans conclure",
      "",
      "| Référence | Source | Index PDF (base zéro) | Zone | Indication |",
      "|---|---|---:|---|---|",
    ]
    for x in plan["observations"]:
        lines.append("| "+x["identifiant"]+" | "+x["source"]+
            " | "+str(x["index_pdf_base_zero"])+" | "+x["zone"]+
            " | "+x["classification"]+" |")
    lines.extend([
       "",
       "Quatre lignes correspondent à P54E; la cinquième est uniquement",
       "une date/année probable, non authentifiée et non close.",
       "",
       "## Conditions bloquantes pour la suite",
       "",
       "| Phase | Contrôle | Responsable à désigner |",
       "|---|---|---|",
    ])
    for item in plan["points_bloquants"]:
        lines.append("| "+item["phase"]+" | "+item["reference"]+
          " | "+item["responsable_a_designer"]+" |")
    lines.extend([
      "",
      "**Aucune de ces conditions n'est déclarée levée.**",
      "Aucun contact externe ni appel aux ordres professionnels n'a été effectué.",
      "Le paquet P54N n'est pas transmis et ne doit pas être diffusé",
      "sans autorisation explicite et destinataire habilité.",
      "",
      "Interdiction de convertir des différences lexicales en montants,",
      "de doubler des éliminations Ville–RTC–SOMHAC ou de réduire",
      "emplois et services sur des hypothèses non documentées.",
      "Les scénarios Québec dans le Canada / souveraineté hypothétique",
      "demeurent juridiquement et économiquement séparés.",
      "Les 96 contrôles P54B et 8 contrôles P54C sont encore ouverts.",
      "",
      "**NO_GO_AUTOMATIQUE — 0 économie, 0 acte professionnel authentifié,**",
      "**aucune fusion main ni intervention sur SINJIRA.**",
      "",
    ])
    return "\n".join(lines)

def new_json(path,value):
    out=Path(path)
    need(not out.exists() and not out.is_symlink()
         and out.parent.is_dir() and not out.parent.is_symlink(),
         "SORTIE_EXISTANTE_OU_NON_AUTORISEE")
    with out.open("x",encoding="utf-8") as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,sort_keys=True)
        stream.write("\n")

def new_text(path,value):
    out=Path(path)
    need(not out.exists() and not out.is_symlink()
         and out.parent.is_dir() and not out.parent.is_symlink(),
         "SORTIE_EXISTANTE_OU_NON_AUTORISEE")
    with out.open("x",encoding="utf-8") as stream:
        stream.write(value)

def read_json(path):
    source=Path(path)
    need(source.is_file() and not source.is_symlink()
         and source.stat().st_size<=131072,
         "PAQUET_P54N_INACCESSIBLE_OU_TROP_VOLUMINEUX")
    return json.loads(source.read_text(encoding="utf-8"))

def read_text(path):
    source=Path(path)
    need(source.is_file() and not source.is_symlink()
         and source.stat().st_size<=131072,
         "INSTRUCTIONS_P54N_INACCESSIBLES_OU_TROP_VOLUMINEUSES")
    return source.read_text(encoding="utf-8")

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paquet-p54n")
    ap.add_argument("--instructions-p54n")
    ap.add_argument("--plan")
    ap.add_argument("--rapport")
    ap.add_argument("--bilan")
    ap.add_argument("--exiger-transmission",action="store_true")
    opts=ap.parse_args(argv)
    try:
        destinations=[Path(x) for x in (opts.plan,opts.rapport,opts.bilan) if x]
        inputs=[Path(x) for x in (opts.paquet_p54n,opts.instructions_p54n) if x]
        paths=destinations+inputs
        need(len({p.resolve() for p in paths})==len(paths)
             and all(not p.exists() and not p.is_symlink()
                     for p in destinations),
             "CHEMIN_DE_SORTIE_EXISTANT_OU_DUPLIQUE")
        cfg=configuration()
        source=read_json(opts.paquet_p54n) if opts.paquet_p54n else None
        instructions=read_text(opts.instructions_p54n) if opts.instructions_p54n else None
        pack,_=validate_public_inputs(cfg,source,instructions)
        plan=matrix(cfg,pack)
        bilan=summary(cfg,plan)
        if opts.plan:new_json(opts.plan,plan)
        if opts.rapport:new_text(opts.rapport,markdown_report(plan,bilan))
        if opts.bilan:new_json(opts.bilan,bilan)
        print(json.dumps(bilan,ensure_ascii=False,sort_keys=True))
        return 3 if opts.exiger_transmission else 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P54O_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
