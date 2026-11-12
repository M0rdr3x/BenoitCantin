#!/usr/bin/env python3
"""P54V — contexte privé de cinq occurrences des PDF 2024, sans conclusion.

L'opérateur fournit deux originaux locaux HORS dépôt. Aucun PDF n'est
récupéré par réseau. Les extraits/token bruts ne sont JAMAIS imprimés
ni copiés dans les bilans publics ou artefacts CI.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import unicodedata

import reproduire_pdf_locaux_nova_p54q as p54q
import verifier_archive_publique_figee_nova_p54t as p54t
import preparer_feuilles_localisation_nova_p54u as p54u

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54V_REVUE_PRIVEE_CONTEXTES_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
CHECKS=(
 "IDENTIFIER_SOURCE_ORIGINALE","RETROUVER_OCCURRENCE_NFKC",
 "COMPARER_SUR_PAGE_VISUELLE","QUALIFIER_NATURE_SUR_PIECE",
 "DISTINGUER_DATE_FOLIO_REFERENCE_VALEUR",
 "VALIDER_UNITE_EXERCICE_COLONNE_SI_PERTINENT",
 "CONSERVER_RESERVES_ET_DESACCORDS","CONTRE_REVUE_INDEPENDANTE",
)
GUARDS={
 "double_pdf_hors_git_obligatoire","empreintes_historiques_exactes",
 "relecture_bilans_figes_sha256","cinq_offsets_p54p_identiques",
 "analyse_complete_ou_refus","aucune_requete_reseau",
 "original_pdfs_non_archives","extraits_prives_mode_0600",
 "liens_symboliques_et_sorties_repo_interdits",
 "aucun_jeton_dans_bilan_public","aucune_sortie_privee_console",
 "anomalie_monetaire_non_inferable","date_probable_non_certifiee",
 "quatre_dossiers_p54e_ouverts",
 "qualification_et_contre_revues_humaines",
 "emplois_services_proteges","pas_double_compte_ville_rtc_somhac",
 "scenarios_constitutionnels_separes","aucun_contact_externe",
 "aucun_merge_main","sinjira_inchange",
}
INITIAL={
 "documents_locaux_examines":0,"offsets_reproduits":0,
 "extraits_prives_ecrits":0,
 "occurrences_qualifiees_humainement":0,
 "avis_independants_authentifies":0,"dossiers_p54e_ouverts":4,
 "observation_date_probable_non_certifiee":1,
 "taches_p54n_non_attestees":40,"blocages_p54o_non_leves":10,
 "controles_p54b_restants":96,"controles_p54c_restants":8,
 "economies_certifiees_cad":None,"decision":NO_GO,
}

def need(ok,why):
    if not ok:raise ValueError(why)

def configuration():
    q=p54q.configuration()
    t=p54t.configuration()
    u=p54u.configuration()
    expected={
       "schema_version":"P54V-1","date_reference":"2026-10-24",
       "exercice":2024,
       "source_jalons":["P54Q","P54T","P54U"],
       "reference_p54p_run":t["reference_run_p54p"],
       "reference_p54p_artifact":t["reference_artifact_p54p"],
       "mode":"LOCAL_PRIVE_HORS_GIT_SANS_RESEAU",
       "observations":5,
       "indices_pdf_zero_based":{
          k:q["copies"][k]["pdf_index_zero"] for k in p54q.NAMES},
       "controle_humain":list(CHECKS),
       "protections":{k:True for k in GUARDS},
       "etat_initial":INITIAL,
    }
    data=json.loads(CONFIG.read_text("utf-8"))
    need(data==expected and t["position_ref_count"]==5
         and u["observations_historiques"]==5
         and u["reference_run_p54p"]==t["reference_run_p54p"]
         and q["copies"]==p54q.p54p.configuration()["sources"],
         "CONFIGURATION_P54V_OU_CHAINE_ALTEREE")
    return data

def nfkc(text):
    need(type(text) is str and 0<len(text)<=1000000,
         "TEXTE_SOURCE_NON_CONFORME")
    return unicodedata.normalize("NFKC",text).replace("\u202f"," ")

def private_sheet(texts,positions,controls=CHECKS):
    """Exact historic offsets required; raw snippets remain private only."""
    need(type(texts) is dict and set(texts)==set(p54q.NAMES)
         and type(positions) is list and len(positions)==5
         and positions==p54t.p54r.known_rows(),
         "OFFSETS_HISTORIQUES_NONSEMBLABLES")
    normal={name:nfkc(txt) for name,txt in texts.items()}
    extras=p54q.p54p.p54d.unmatched(texts["ville"],texts["mamh"])
    indexed={(source,item["pos"]):item
             for source in p54q.NAMES for item in extras[source]}
    need(len(indexed)==5,"CINQ_JETONS_NON_RETROUVES")
    cards=[]
    for row in positions:
        source=row["source"];position=row["offset_texte_extrait"]
        text=normal[source]
        item=indexed.get((source,position))
        need(item is not None and item["zone"]==row["zone_confirmee_par_parseur"]
             and p54q.p54p.p54d.classify(item)==row["classification_indicative"]
             and len(text)==row["longueur_texte_normalise_nfkc"]
             and 0<=position<len(text),
             "SOURCE_NFKC_OU_JETON_NON_REPRODUIT")
        start=max(0,position-70)
        end=min(len(text),position+len(item["token"])+70)
        snippet=text[start:end]
        need(type(snippet) is str and snippet,
             "EXTRAIT_PRIVE_VIDE")
        cards.append({
          "reference":row["dossier"] or "P54O-DATE-001",
          "source":source,"page_pdf_index_zero":row["pdf_index_zero"],
          "offset_caractere_nfkc":position,
          "zone_indicative":row["zone_confirmee_par_parseur"],
          "classification_automatique_non_attestee":
              row["classification_indicative"],
          "jeton_brut_STRICTEMENT_PRIVE":item["token"],
          "extrait_contextuel_STRICTEMENT_PRIVE":snippet,
          "debut_extrait_nfkc":start,
          "etat":"A_EXAMINER_PAR_PERSONNE_HABILITEE",
          "controles_a_instruire":[{
             "code":c,"etat":"NON_ATTESTE"} for c in controls],
          "revue_contradictoire_effectuee":False,
          "qualification_humaine_confirmee":False,
        })
    need(len(cards)==5 and
         len({(x["source"],x["offset_caractere_nfkc"]) for x in cards})==5,
         "CINQ_FICHES_PRIVEES_INCOMPLETES")
    return {
      "schema_version":"P54V-FICHE-PRIVEE-1",
      "confidentialite":"NE_PAS_DEPLOYER_OU_PUBLIER",
      "source":"PDF_2024_SHA256_CONFORMES_LOCALEMENT_PLUS_P54T",
      "occurrences":cards,
      "signatures_professionnelles_authentifiees":0,
      "economies_certifiees_cad":None,"decision":NO_GO,
    }

def verify_local(paths,config,extractor=None):
    """Exact local PDFs + hashed P54T + reproduced normalized offsets."""
    original=p54q.checked_local_paths(paths)
    ref=p54q.configuration()["copies"]
    checked=p54t.verify_frozen(p54t.configuration())
    need(checked["bilans_figes_verifies"]==2
         and checked["positions_historiques_hachees"]==5,
         "BILANS_P54T_NON_REVERIFIES")
    texts={}
    for source in p54q.NAMES:
        raw,meta=p54q.read_copy(source,original[source],ref)
        need(type(raw) is bytes and len(raw)==ref[source]["taille_octets"]
             and hashlib.sha256(raw).hexdigest()==ref[source]["sha256"]
             and meta["sha256_fichier_copie_publique"]==ref[source]["sha256"],
             "PDF_EDITION_NON_IDENTIQUE")
        read=extractor or p54q.p54p.context.page
        texts[source]=read(raw,ref[source]["pdf_index_zero"])
    observed=p54q.p54p.localize(texts)
    need(observed==checked["positions_de_reference"],
         "OFFSETS_REPRODUITS_DIFFERENTS_DES_BILANS_FIGES")
    return private_sheet(texts,observed),checked

def public_summary(created=False):
    return {
      "schema_version":"P54V-BILAN-1","exercice":2024,
      "copies_pdf_verifiees_ce_run":2 if created else 0,
      "positions_nfkc_reproduites_ce_run":5 if created else 0,
      "fiches_contextuelles_privees_creees":5 if created else 0,
      "qualifications_humaines_effectuees":0,
      "contenus_jetons_extraits_publies":0,
      "originals_pdfs_publies":0,
      "avis_independants_authentifies":0,
      "dossiers_p54e_ouverts":4,"date_probable_non_certifiee":True,
      "taches_p54n_non_attestees":40,
      "blocages_p54o_non_leves":10,
      "controles_p54b_non_attestes":96,
      "controles_p54c_non_attestes":8,
      "economies_certifiees_cad":None,
      "pret_a_transmettre":False,
      "fusion_main_autorisee":False,"decision":NO_GO,
    }

def safe_private_target(path):
    need(isinstance(path,(str,Path)) and str(path),
         "DESTINATION_PRIVEE_ABSENTE")
    p=Path(path).expanduser().absolute()
    need(not any(node.is_symlink() for node in (p,*p.parents)),
         "SYMLINK_INTERDIT")
    resolved=p.resolve()
    need(ROOT.resolve() not in (resolved,*resolved.parents)
         and p.parent.is_dir() and not p.exists(),
         "SORTIE_PRIVEE_DANS_DEPOT_OU_EXISTANTE")
    return p

def private_write_new(path,data):
    dest=safe_private_target(path)
    content=(json.dumps(data,ensure_ascii=False,sort_keys=True,
                        indent=2)+"\n").encode("utf-8")
    fd=os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL|
               getattr(os,"O_NOFOLLOW",0),0o600)
    try:
        with os.fdopen(fd,"wb") as stream:
            stream.write(content)
        need(stat.S_IMODE(dest.stat().st_mode)==0o600,
             "DROITS_PRIVES_NON_CONFORMES")
    except BaseException:
        dest.unlink(missing_ok=True)
        raise

def write_public_new(path,summary):
    p=Path(path)
    need(not p.exists() and not p.is_symlink() and p.parent.is_dir()
         and not p.parent.is_symlink(),"SORTIE_PUBLIQUE_EXISTANTE")
    with p.open("x",encoding="utf-8") as stream:
        json.dump(summary,stream,ensure_ascii=False,sort_keys=True,indent=2)
        stream.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ville-pdf")
    parser.add_argument("--mamh-pdf")
    parser.add_argument("--fiche-privee")
    parser.add_argument("--bilan-public")
    parser.add_argument("--exiger-certification",action="store_true")
    arg=parser.parse_args(argv)
    try:
        need(bool(arg.ville_pdf)==bool(arg.mamh_pdf),
             "DEUX_PDF_LOCAUX_EXIGES")
        need(not arg.fiche_privee or (arg.ville_pdf and arg.mamh_pdf),
             "FICHE_PRIVEE_EXIGE_LES_DEUX_PDF")
        need(not arg.ville_pdf or arg.fiche_privee,
             "RELECTURE_LOCALE_EXIGE_SORTIE_PRIVEE")
        cfg=configuration()
        target=safe_private_target(arg.fiche_privee) if arg.fiche_privee else None
        if arg.bilan_public:
            output=Path(arg.bilan_public).absolute()
            need(not output.exists() and not output.is_symlink(),
                 "BILAN_PUBLIC_NON_ECRASABLE")
            if target is not None:
                need(target.resolve()!=output.resolve(),
                     "SORTIES_PRIVEE_PUBLIQUE_IDENTIQUES")
        created=False
        if arg.ville_pdf:
            pair={"ville":arg.ville_pdf,"mamh":arg.mamh_pdf}
            inputs=p54q.checked_local_paths(pair)
            need(target.resolve() not in inputs.values(),
                 "FICHE_IDENTIQUE_A_SOURCE_PDF")
            if arg.bilan_public:
                need(output.resolve() not in inputs.values(),
                     "BILAN_IDENTIQUE_A_SOURCE_PDF")
            sheet,verified=verify_local(pair,cfg)
            private_write_new(target,sheet)
            created=True
        result=public_summary(created)
        if arg.bilan_public:write_public_new(arg.bilan_public,result)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if arg.exiger_certification else 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,
            json.JSONDecodeError):
        # Deliberately exclude private paths and raw PDF fragments from stderr.
        print("P54V_REFUS: ENTREE_OU_PREUVE_NON_CONFORME",file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
