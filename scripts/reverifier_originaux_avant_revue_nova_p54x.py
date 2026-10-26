#!/usr/bin/env python3
"""P54X — recontrôle privé des originaux avant qualification déclarative.

Aucune conclusion automatique : les PDF locaux, la fiche P54V et les revues
P54W doivent être fournis ensemble hors Git. Même une reproduction exacte
des cinq extraits ne vaut ni signature ni revue humaine authentifiée.
"""
import argparse
import json
from pathlib import Path
import sys

import qualifier_occurrences_privees_nova_p54w as p54w

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54X_VERROU_ORIGINAUX_AVANT_REVUE_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
PROTECTIONS={
 "deux_pdfs_locaux_exiges_pour_revues",
 "copies_pdf_sha256_historiques_imposees",
 "fiche_p54v_reconstruite_des_originaux",
 "fiche_p54v_privée_identique_requise",
 "revues_p54w_liees_par_sha256",
 "aucun_fichier_prive_dans_git",
 "permissions_privees_0600",
 "symlinks_sources_interdits",
 "aucun_texte_jeton_et_extrait_sur_stdout",
 "aucun_texte_jeton_et_extrait_dans_artifacts",
 "aucun_certificat_ou_signature_presume",
 "revue_declarative_non_assimilee_independance",
 "contradictions_et_suspensions_prioritaires",
 "date_probable_non_finalisee",
 "quatre_dossiers_p54e_ouverts",
 "quarante_taches_p54n_non_attestees",
 "dix_blocages_p54o_non_leves",
 "comparabilites_p54b_et_p54c_ouvertes",
 "pas_de_double_compte_ville_rtc_somhac",
 "maintien_emplois_et_services",
 "regimes_constitutionnels_separes",
 "pas_de_contact_externe",
 "pas_de_merge_main",
 "sinjira_non_modifie",
 "no_go_automatique",
}
EXPECTED={
 "schema_version":"P54X-1",
 "date_reference":"2026-10-26",
 "source_jalons":["P54Q","P54T","P54V","P54W"],
 "source_exercice":2024,
 "source_run_p54p":40151185184,
 "references":list(p54w.REFS),
 "roles":list(p54w.ROLES),
 "revue_privée_exige_quatre_fichiers":True,
 "protections":{k:True for k in PROTECTIONS},
 "etat_initial":{
    "originaux_pdf_locaux_revus":0,
    "fiches_p54v_reconstruites":0,
    "declarations_p54w_acceptees":0,
    "revues_professionnelles_authentifiees":0,
    "signatures_authentifiees":0,
    "qualifications_definitives":0,
    "dossiers_p54e_ouverts":4,
    "date_probable_non_certifiee":1,
    "taches_p54n_non_attestees":40,
    "blocages_p54o_non_leves":10,
    "controles_p54b_non_attestes":96,
    "controles_p54c_non_attestes":8,
    "economies_certifiees_cad":None,
    "decision":NO_GO,
 },
}

def need(value,error):
    if not value:raise ValueError(error)

def configuration():
    base=p54w.configuration()
    registered=json.loads(CONFIG.read_text("utf-8"))
    need(registered==EXPECTED
         and base["refs"]==EXPECTED["references"]
         and base["roles"]==EXPECTED["roles"]
         and base["source_p54p_run"]==EXPECTED["source_run_p54p"]
         and base["etat_initial"]["economies_certifiees_cad"] is None
         and base["etat_initial"]["decision"]==NO_GO,
         "CONFIGURATION_OU_CHAINAGE_P54X_INVALIDE")
    return registered

def inspect_pair(pdf_paths,private_sheet,private_reviews):
    """Validate actual local PDFs before accepting any P54W declaration."""
    need(type(pdf_paths) is dict
         and set(pdf_paths)==set(p54w.p54v.p54q.NAMES),
         "DEUX_ORIGINAUX_LOCAUX_MANQUANTS")
    original=p54w.p54v.p54q.checked_local_paths(pdf_paths)
    sheet_file=p54w.private_file(private_sheet)
    review_file=p54w.private_file(private_reviews)
    files=[*original.values(),sheet_file,review_file]
    need(len({p.resolve() for p in files})==4,
         "SOURCES_PRIVEES_DUPLIQUEES")
    original_sheet,verified=p54w.p54v.verify_local(
       original,p54w.p54v.configuration())
    need(type(verified) is dict
         and verified.get("bilans_figes_verifies")==2
         and verified.get("positions_historiques_hachees")==5,
         "HACHAGES_OU_POSITIONS_P54T_NON_REVERIFIES")
    raw_sheet=sheet_file.read_bytes()
    private_doc=json.loads(raw_sheet.decode("utf-8"))
    need(private_doc==original_sheet,
         "FICHE_P54V_DIFFERENTE_DES_PDF_RELUS")
    p54w.validate_p54v(private_doc,verified["positions_de_reference"])
    private_claims=json.loads(review_file.read_text("utf-8"))
    declared=p54w.validate_reviews(private_claims,raw_sheet,private_doc)
    return p54w.report(p54w.configuration(),declared)

def public_report(cfg,technical=None):
    data=technical or p54w.report(p54w.configuration())
    need(data["decision"]==NO_GO and data["economies_certifiees_cad"] is None
         and data["qualifications_definitives"]==0
         and data["signatures_authentifiees"]==0
         and data["contextes_bruts_ou_jetons_publies"]==0,
         "BILAN_SOURCE_NON_NEUTRE")
    success=technical is not None
    return {
      "schema_version":"P54X-BILAN-1",
      "exercice":2024,
      "revue_des_sources_originales_ce_run":success,
      "copies_pdf_sha256_reverifiees":2 if success else 0,
      "cinq_contextes_p54v_reconstruits":5 if success else 0,
      "declarations_p54w_non_authentifiees":data[
          "declarations_locales_non_authentifiees"] if success else 0,
      "occurrences":data["occurrences"],
      "statuts_de_qualification":data["statuts"],
      "textes_ou_jetons_prives_publies":0,
      "dossiers_p54e_ouverts":4,
      "occurrence_date_probable_non_certifiee":1,
      "qualifications_humaines_certifiees":0,
      "signatures_professionnelles_authentifiees":0,
      "economies_certifiees_cad":None,
      "taches_p54n_non_attestees":40,
      "blocages_p54o_non_leves":10,
      "controles_p54b_non_attestes":96,
      "controles_p54c_non_attestes":8,
      "pret_a_transmettre":False,
      "cloture_automatique_autorisee":False,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-ville")
    parser.add_argument("--pdf-mamh")
    parser.add_argument("--fiche-privee-p54v")
    parser.add_argument("--revues-privees-p54w")
    parser.add_argument("--bilan-public")
    parser.add_argument("--exiger-cloture",action="store_true")
    opts=parser.parse_args(argv)
    try:
        group=[opts.pdf_ville,opts.pdf_mamh,
               opts.fiche_privee_p54v,opts.revues_privees_p54w]
        need(not any(group) or all(group),
             "QUATRE_ENTREES_PRIVEES_REQUISES")
        cfg=configuration()
        destination=Path(opts.bilan_public).expanduser().absolute() \
           if opts.bilan_public else None
        if destination is not None:
            need(not destination.exists() and not destination.is_symlink()
                 and destination.parent.is_dir()
                 and not destination.parent.is_symlink(),
                 "BILAN_PUBLIC_EXISTANT_OU_CHEMIN_INVALIDE")
        state=None
        if all(group):
            paths={"ville":opts.pdf_ville,"mamh":opts.pdf_mamh}
            if destination is not None:
                need(destination.resolve() not in {
                    Path(p).expanduser().absolute().resolve()
                    for p in group},
                    "ENTREE_ET_SORTIE_IDENTIQUES")
            state=inspect_pair(paths,opts.fiche_privee_p54v,
                               opts.revues_privees_p54w)
        result=public_report(cfg,state)
        if destination is not None:
            p54w.p54v.write_public_new(destination,result)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if opts.exiger_cloture else 0
    except (ValueError,KeyError,OSError,TypeError,UnicodeError,
            json.JSONDecodeError):
        print("P54X_REFUS: ORIGINAUX_OU_REVUES_NON_CONFORMES",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
