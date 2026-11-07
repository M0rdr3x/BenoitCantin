#!/usr/bin/env python3
"""P54C : valider les résultats CI observés sans conclure à un audit comptable."""
import argparse
import json
from pathlib import Path
import sys
import analyser_contexte_audit_depenses_nova_p54c as prior

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"projets/projet-nova/etudes/P54C_OBSERVATIONS_AUDIT_2026_10_24.json"
NO_GO="NO_GO_AUTOMATIQUE"
RUN=40119313052
HASH="f466f35a8432056c0dcf73bdc4ed9e95a944c60e57d0c8e39b6f5e935964a958"
RESERVES={
 "mise_en_page_notes_coordonnees_pourraient_expliquer_les_variations",
 "cause_des_differences_numeriques_non_demontrée",
 "aucun_montant_extrait_ni_publie",
 "rapport_au_perimetre_specifique_non_expertise_Nova",
 "pas_d_anomalie_financiere_demontree",
 "deux_pdfs_copies_https_pas_signatures_editeurs",
 "questions_p54b_96_restent_a_instruire",
 "protection_emplois_services",
 "eliminations_anterieures_non_economies",
 "pas_de_fusion_automatique",
}

def need(ok,msg):
    if not ok:raise ValueError(msg)

def validate(v):
    prior.cfg()
    need(type(v) is dict and set(v)=={
      "schema_version","date_reference","source_run","source_job_id",
      "artefact_id","artefact_archive_sha256","source_pdf_p53z_hash_stables",
      "pages","marqueurs_documentaires","conclusion_contextuelle",
      "comparaison_lexicale","reserves","etat"},
      "CHAMPS_RESULTAT_INVALIDES")
    need(v["schema_version"]=="P54C-OBSERVATIONS-1"
         and v["date_reference"]=="2026-10-24"
         and v["source_run"]==RUN
         and v["source_job_id"]==120947176733
         and v["artefact_id"]==12570109480
         and v["artefact_archive_sha256"]==HASH
         and v["source_pdf_p53z_hash_stables"] is True
         and v["pages"]==prior.PAGES,
         "PROVENANCE_RESULTATS_NON_CONFORME")
    flags=v["marqueurs_documentaires"]
    need(type(flags) is dict and set(flags)==set(prior.MARKERS)
         and all(f=={"ville":True,"mamh":True} for f in flags.values())
         and v["conclusion_contextuelle"]==
             "MEME_TYPE_DE_RAPPORT_AUDIT_SPECIALISE_PROBABLE_NON_CERTIFIE",
         "CONTEXTE_AUDIT_NON_CORROBORE")
    need(v["comparaison_lexicale"]=={
       "jetons_ville":10,"jetons_mamh":13,"communs":9,
       "non_apparies_ville":1,"non_apparies_mamh":4,
       "score_dice":0.7826,"statut":"NON_QUALIFIE_COMME_MONTANT"},
       "RECROISEMENT_NUMERIQUE_INVALIDE")
    need(v["reserves"]=={x:True for x in RESERVES},
         "PRECAUTIONS_NON_RESPECTEES")
    need(v["etat"]=={
       "examens_techniques_pages":2,"marqueurs_correspondants":7,
       "differences_numeric_lexical_non_classees":5,
       "controles_professionnels_a_instruire":8,
       "expertises_independantes_signees_pour_nova":0,
       "montants_comptables_certifies":0,
       "economies_certifiees_cad":None,"decision":NO_GO},
       "AUCUNE_EXPERTISE_NOVA_AUTORISEE")
    return v

def result(v):
    d=validate(v)
    return {
      "schema_version":"P54C-VALIDATION-1",
      "source_run":RUN,"pages_examinees":2,
      "marqueurs_communs":7,
      "jetons_non_apparies_toutes_sources":5,
      "cause_justifiee_des_jetons_differents":False,
      "examens_comptables_independants_signes":0,
      "montants_authentifies":0,
      "economies_certifiees_cad":None,
      "decision":NO_GO,
    }

def main(argv=None):
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--bilan")
    arg.add_argument("--exiger-avis-independant",action="store_true")
    a=arg.parse_args(argv)
    try:
        v=json.loads(SOURCE.read_text("utf-8"))
        out=result(v)
        if a.bilan:
            dest=Path(a.bilan)
            need(not dest.exists() and not dest.is_symlink(),
                 "REFUS_ECRASEMENT")
            with dest.open("x",encoding="utf-8") as f:
                json.dump(out,f,sort_keys=True,ensure_ascii=False,indent=2)
                f.write("\n")
        print(json.dumps(out,ensure_ascii=False,sort_keys=True))
        return 3 if a.exiger_avis_independant else 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as err:
        print("P54C_OBSERVATIONS_REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
