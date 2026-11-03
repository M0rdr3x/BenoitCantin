#!/usr/bin/env python3
"""P54Y : readiness documentaire, sans authentification ni accès privé."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54Y_CONTROLE_PREPARATION_REVUE_2024.json"
BASE=ROOT/"projets/projet-nova/etudes"
NO_GO="NO_GO_AUTOMATIQUE"
STAGES=("P54Q","P54R","P54S","P54T","P54U","P54V","P54W","P54X")
GATES=(
 ("P54Q","REPRODUCTION_LOCALE_DEUX_PDF","PDF_2024_VERIFIES_HORS_GIT"),
 ("P54R","PROVENANCE_POSITIONS","BILAN_ORIGINAL_P54P_CONFORME"),
 ("P54S","INTEGRITE_ARTEFACT","ARCHIVE_CONFRONTEE_AU_RUN"),
 ("P54T","PREUVE_PUBLIQUE_FIGEE","DEUX_BILANS_PUBLICS_VERIFIES"),
 ("P54U","FICHES_CIBLEES","CINQ_FICHES_DOCUMENTAIRES"),
 ("P54V","EXTRAITS_PRIVES","CINQ_EXTRAITS_HORS_GIT"),
 ("P54W","REVUES_DECLAREES","DEUX_ROLES_SANS_AUTHENTIFICATION"),
 ("P54X","RECONTROLE_ORIGINAUX","QUATRE_ENTREES_PRIVEES_CONCORDANTES"),
)
GUARDS={
 "aucune_certification_automatique","aucune_transmission_reelle",
 "aucune_revue_humaine_reelle_deduite","aucun_pdf_origine_archive_ci",
 "aucun_extrait_jeton_publie","aucun_montant_deduit_des_offsets",
 "deux_pdf_historiques_requis","statuts_validation_distincts",
 "preuve_ci_ne_vaut_pas_avis_professionnel",
 "cinq_occurrences_toujours_a_qualifier","quatre_dossiers_p54e_ouverts",
 "date_probable_non_confirmee","quarante_taches_p54n_non_attestees",
 "dix_blocages_p54o_non_leves","p54b_96_et_p54c_8_ouverts",
 "consolidations_sans_double_compte","maintien_emplois_services",
 "deux_scenarios_constitutionnels_separes",
 "main_non_fusionnee","sinjira_non_modifie",
}
SOURCES={
 "ville":{"index_pdf_zero":102,"sha256":"b3ee3e671f7bf98e56c7d42b5e8b6c34de02a96c9dc1c96469819fa4dbfa7399"},
 "mamh":{"index_pdf_zero":162,"sha256":"4323c87d2114b58cf7a093c08f3b30327e949db91b9beb46a627eac1ecb4fc00"},
}
INITIAL={
 "gates_humains_non_attestes":8,"dossiers_p54e_ouverts":4,
 "occurrences_a_qualifier":5,"taches_p54n_non_attestees":40,
 "blocages_p54o_non_leves":10,"controles_p54b_non_attestes":96,
 "controles_p54c_non_attestes":8,"signatures_authentifiees":0,
 "economies_certifiees_cad":None,"decision":NO_GO,
}

def must(ok,msg):
    if not ok:raise ValueError(msg)

def configuration():
    raw=json.loads(CONFIG.read_text("utf-8"))
    expected={
      "schema_version":"P54Y-1","date_reference":"2026-11-02",
      "exercice":2024,"chaine_reference":list(STAGES),
      "sources_reference":SOURCES,
      "gates":[{"jalon":a,"controle":b,"preuve_requise":c} for a,b,c in GATES],
      "protections":{k:True for k in GUARDS},"etat_initial":INITIAL,
    }
    must(raw==expected,"CONFIGURATION_P54Y_NON_CONFORME")
    archive=BASE/"p54t_archive_durable_p54p"
    must((archive/"p54p_avant_acquisition.json").is_file()
         and (archive/"p54p_reproduction_conditionnelle.json").is_file(),
         "ARCHIVE_P54T_ABSENTE")
    evidence=json.loads((archive/"p54p_reproduction_conditionnelle.json").read_text("utf-8"))
    must(evidence.get("decision")==NO_GO
         and evidence.get("occurrences_localisees_automatiquement")==5
         and evidence.get("copies_exactes_verifiees")==2
         and evidence.get("economies_certifiees_cad") is None
         and isinstance(evidence.get("positions_caracteres_sur_texte_extrait"),list)
         and len(evidence["positions_caracteres_sur_texte_extrait"])==5,
         "BILAN_FIGE_P54T_NON_CONFORME")
    return raw

def check_structure(cfg,root=ROOT):
    rows=[]
    for stage,control,proof in GATES:
        workflow=root/(".github/workflows/validate-nova-"+stage.lower()+".yml")
        register=list((root/"projets/projet-nova/etudes").glob(stage+"_*.json"))
        protocol=list((root/"projets/projet-nova/etudes").glob(stage+"_*.md"))
        present=workflow.is_file() and len(register)>=1 and len(protocol)>=1
        rows.append({
          "jalon":stage,"controle":control,
          "preuve_requise":proof,
          "fichiers_de_structure_presents":present,
          "execution_humaine_verifiee":False,
          "attestation_professionnelle_obtenue":False,
        })
    return rows

def report(cfg,root=ROOT):
    rows=check_structure(cfg,root)
    return {
      "schema_version":"P54Y-BILAN-1","exercice":2024,
      "jalons_documentaires":rows,
      "jalons_structurellement_presents":sum(r["fichiers_de_structure_presents"] for r in rows),
      "jalons_non_presents":sum(not r["fichiers_de_structure_presents"] for r in rows),
      "workflow_git_hub_actions_estime_reussi":False,
      "revue_humaine_effectivement_realisee":False,
      "authenticite_professionnelle_confirmee":False,
      "dossiers_p54e_ouverts":4,"occurrences_a_qualifier":5,
      "taches_p54n_non_attestees":40,"blocages_p54o_non_leves":10,
      "controles_p54b_non_attestes":96,"controles_p54c_non_attestes":8,
      "economies_certifiees_cad":None,
      "pret_a_certifier":False,"pret_a_fusionner":False,
      "decision":NO_GO,
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bilan")
    ap.add_argument("--exiger-go",action="store_true")
    arg=ap.parse_args(argv)
    try:
        result=report(configuration())
        if arg.bilan:
            path=Path(arg.bilan)
            must(not path.exists() and not path.is_symlink()
                 and path.parent.is_dir() and not path.parent.is_symlink(),
                 "SORTIE_NON_AUTORISEE")
            with path.open("x",encoding="utf-8") as f:
                json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2)
                f.write("\n")
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if arg.exiger_go else 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P54Y_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
