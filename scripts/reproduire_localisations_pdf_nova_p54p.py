#!/usr/bin/env python3
"""P54P — tentative de localisation documentaire exacte sur PDF publics.

Aucune valeur ni contexte de jeton n'est émis. Les offsets sont des indices
dans le texte extrait par pypdf 5.9.0, et non des coordonnées sur la page.
Sans les deux PDF de hachage P54D identique, aucune position n'est retenue.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import controler_qualite_passation_nova_p54o as p54o
import classer_ecarts_numeriques_nova_p54d as p54d
import acquerir_publications_nova_p53z as acquire
import analyser_contexte_audit_depenses_nova_p54c as context

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54P_REPRODUCTION_POSITIONS_PDF_2024.json"
OBS=ROOT/"projets/projet-nova/etudes/P54D_OBSERVATIONS_REELLES_2026_10_24.json"
NO_GO="NO_GO_AUTOMATIQUE"
STATE=("NON_TENTE","SOURCE_NON_ACQUISE","EDITION_DIFFERENTE",
       "CONTEXTE_OU_EXTRACTION_INCOHERENTE",
       "REPRODUCTION_TECHNIQUE_SANS_ATTESTATION")
GUARDS={
 "aucune_lecture_jeton_brut_en_sortie","aucune_inference_montant",
 "sources_https_publiques_uniquement","versions_pdf_exactes_ou_echec",
 "metadonnees_p54d_imposees","positions_seulement_si_reproduction_complete",
 "pas_de_melange_versions","diagnostic_prive_non_publie",
 "aucune_authentification_emetteur","aucune_expertise_nova",
 "pages_index_zero","dates_probables_non_certifiees",
 "aucune_reduction_emplois_services",
 "pas_de_double_compte_ville_rtc_somhac",
 "regimes_constitutionnels_distincts","aucune_transmission_externe",
 "aucun_merge_main","sinjira_inchange",
}
NAMES=("ville","mamh")
EXPECTED_ROWS=[
 {"source":"ville","index_p54d":0,"classe":"INDETERMINE",
  "zone":"FIN","dossier":"P54E-V-001"},
 {"source":"mamh","index_p54d":1,"classe":"INDETERMINE",
  "zone":"DEBUT","dossier":"P54E-M-001"},
 {"source":"mamh","index_p54d":2,"classe":"ANNEE_DATE_PROBABLE",
  "zone":"FIN","dossier":None},
 {"source":"mamh","index_p54d":3,"classe":"INDETERMINE",
  "zone":"FIN","dossier":"P54E-M-002"},
 {"source":"mamh","index_p54d":4,"classe":"INDETERMINE",
  "zone":"FIN","dossier":"P54E-M-003"},
]
INITIAL={
 "sources_reacquises_dans_ce_jalon":0,
 "positions_caracteres_reproduites":0,
 "occurrences_indeterminees":4,
 "annee_date_probable_non_certifiee":1,
 "dossiers_p54e_ouverts":4,
 "controles_p54b_ouverts":96,
 "controles_p54c_ouverts":8,
 "economies_certifiees_cad":None,
 "decision":NO_GO,
}

def need(condition,error):
    if not condition:raise ValueError(error)

def configuration():
    p54o.configuration()
    observed=json.loads(OBS.read_text("utf-8"))
    source={
      k:{
        "pdf_index_zero":p54d.PAGES[k],
        "taille_octets":p54d.p54b.p54a.COPIES[k][1],
        "sha256":p54d.p54b.p54a.COPIES[k][2],
      } for k in NAMES
    }
    expected={
      "schema_version":"P54P-1",
      "date_reference":"2026-10-24","exercice":2024,
      "source_jalons":["P53Z","P54D","P54O"],
      "source_run_p54d":40120462237,
      "sources":source,
      "observations_attendues":EXPECTED_ROWS,
      "etats":list(STATE),
      "protections":{x:True for x in GUARDS},
      "etat_initial":INITIAL,
    }
    data=json.loads(CONFIG.read_text("utf-8"))
    need(data==expected and observed["source_documents"]==
         {k:source[k]["sha256"] for k in NAMES}
         and observed["pages"]=={k:source[k]["pdf_index_zero"] for k in NAMES}
         and observed["run_id"]==40120462237
         and len(observed["observations"])==5,
         "CHAINAGE_P54P_SOURCE_NON_CONFORME")
    for expected_row in EXPECTED_ROWS:
        src=observed["observations"][expected_row["index_p54d"]]
        need(src["source"]==expected_row["source"]
             and src["categorie_indicative"]==expected_row["classe"]
             and src["zone_approximative"]==expected_row["zone"]
             and src["qualification"]=="NON_CERTIFIEE",
             "METADONNEE_P54D_CONTREDITE")
    return data

def localize(texts,audit_checker=None):
    """Pure extraction testable; never returns the actual raw tokens."""
    need(type(texts) is dict and set(texts)==set(NAMES)
         and all(type(x) is str and 0<len(x)<=1000000
                 for x in texts.values()),
         "TEXTE_PDF_INVALIDE")
    audit_checker=audit_checker or (
      lambda a,b:context.analyze_text(a,b)[
        "sections_se_rapportent_probablement_au_meme_audit"])
    need(audit_checker(texts["ville"],texts["mamh"]) is True,
         "PORTEE_AUDIT_NON_IDENTIQUE")
    extras=p54d.unmatched(texts["ville"],texts["mamh"])
    found=[]
    idx=0
    for source in NAMES:
        for item in extras[source]:
            expected=EXPECTED_ROWS[idx]
            # Each unmatched token remains internal to memory only.
            need(source==expected["source"]
                 and item["zone"]==expected["zone"]
                 and p54d.classify(item)==expected["classe"]
                 and type(item["pos"]) is int
                 and 0<=item["pos"]<len(texts[source]),
                 "OCCURRENCE_INCOMPATIBLE_AVEC_P54D")
            found.append({
              "index_observation_p54d":idx,
              "source":source,
              "dossier":expected["dossier"],
              "pdf_index_zero":p54d.PAGES[source],
              "offset_texte_extrait":item["pos"],
              "longueur_texte_extrait":len(texts[source]),
              "zone_confirmee_par_parseur":item["zone"],
              "classification_indicative":expected["classe"],
              "aucune_conclusion_financiere":True,
            })
            idx+=1
    need(idx==5 and len({
       (x["source"],x["offset_texte_extrait"]) for x in found})==5,
       "CINQ_POSITIONS_NON_REPRODUITES")
    return found

def verify_captures(fetcher,extractor,expected):
    """Return a public status, never original bytes, tokens, or raw context."""
    acquired={};texts={};states={}
    for source in NAMES:
        try:
            raw,meta=fetcher(source)
        except (OSError,TimeoutError,ConnectionError,
                ValueError,KeyError,TypeError):
            states[source]="SOURCE_NON_ACQUISE"
            continue
        try:
            ref=expected[source]
            ok=(type(raw) is bytes
                and len(raw)==ref["taille_octets"]
                and hashlib.sha256(raw).hexdigest()==ref["sha256"]
                and type(meta) is dict and meta.get("source_id")==source
                and meta.get("taille_octets")==len(raw)
                and meta.get("sha256_fichier_copie_publique")==ref["sha256"])
            if not ok:
                states[source]="EDITION_DIFFERENTE"
                continue
            acquired[source]=True
            txt=extractor(raw,ref["pdf_index_zero"])
            need(type(txt) is str and 0<len(txt)<=1000000,
                 "EXTRACTION_INEXPLOITABLE")
            texts[source]=txt
            states[source]="REPRODUCTION_TECHNIQUE_SANS_ATTESTATION"
        except (ValueError,TypeError,KeyError,IndexError,OSError):
            states[source]="CONTEXTE_OU_EXTRACTION_INCOHERENTE"
    positions=None
    if len(texts)==2:
        try:
            positions=localize(texts)
        except (ValueError,KeyError,IndexError,TypeError):
            positions=None
            states={k:"CONTEXTE_OU_EXTRACTION_INCOHERENTE" for k in NAMES}
    else:
        # A successful PDF hash alone cannot produce a located observation.
        for k in NAMES:
            if states.get(k)=="REPRODUCTION_TECHNIQUE_SANS_ATTESTATION":
                states[k]="CONTEXTE_OU_EXTRACTION_INCOHERENTE"
    need(set(states)==set(NAMES),"ETAT_CAPTURE_INCOMPLET")
    return {
       "statut":"REPRODUCTION_TECHNIQUE_SANS_ATTESTATION"
           if positions is not None else "NON_REPRODUIT",
       "sources":states,
       "copies_verifiees_par_hachage":len(acquired),
       "cinq_positions_reproduites":positions is not None,
       "positions":positions,
    }

def baseline():
    return {
       "statut":"NON_TENTE",
       "sources":{k:"NON_TENTE" for k in NAMES},
       "copies_verifiees_par_hachage":0,
       "cinq_positions_reproduites":False,
       "positions":None,
    }

def report(cfg,attempt=None):
    obs=attempt or baseline()
    is_confirmed=obs["cinq_positions_reproduites"] is True
    locations=obs["positions"] if is_confirmed else None
    return {
      "schema_version":"P54P-BILAN-1",
      "exercice":2024,
      "statut_capture":obs["statut"],
      "sources":obs["sources"],
      "copies_exactes_verifiees":obs["copies_verifiees_par_hachage"],
      "occurrences_localisees_automatiquement":5 if is_confirmed else 0,
      "positions_caracteres_sur_texte_extrait":locations,
      "limite_offsets":"CHARACTERES_DU_TEXTE_PYPDF_NON_COORDONNEES_VISUELLES",
      "pdf_sources_deja_attestes_par_emetteur":False,
      "dossiers_p54e_ouverts":4,
      "occurrence_date_probable_non_certifiee":1,
      "controles_p54b_non_attestes":96,
      "controles_p54c_non_attestes":8,
      "originaux_confidentiels_publies":0,
      "tokens_bruts_publies":0,
      "economies_certifiees_cad":None,
      "expertises_independantes_signees":0,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def save(path,result):
    out=Path(path)
    need(not out.exists() and not out.is_symlink()
         and out.parent.is_dir() and not out.parent.is_symlink(),
         "SORTIE_EXISTANTE_OU_REPERTOIRE_INTERDIT")
    with out.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,ensure_ascii=False,sort_keys=True,indent=2)
        stream.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquerir",action="store_true")
    parser.add_argument("--bilan")
    parser.add_argument("--exiger-certification",action="store_true")
    args=parser.parse_args(argv)
    try:
        cfg=configuration()
        result=verify_captures(acquire.capture,context.page,cfg["sources"]) \
            if args.acquerir else baseline()
        public=report(cfg,result)
        if args.bilan:save(args.bilan,public)
        print(json.dumps(public,ensure_ascii=False,sort_keys=True))
        if args.exiger_certification:return 3
        return 4 if args.acquerir and not result["cinq_positions_reproduites"] else 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError,
            json.JSONDecodeError) as err:
        print("P54P_REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
