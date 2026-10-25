#!/usr/bin/env python3
"""P54U — fiches ciblées de localisation humaine à partir de bilans P54T.

N'émet aucune valeur de jeton ni extrait. Exige une vérification réelle des
octets des bilans figés avant de produire les fiches à destination de la revue.
Ces octets sont issus du même run P54P, pas d'une contre-expertise externe.
"""
import argparse
import json
from pathlib import Path
import sys

import verifier_archive_publique_figee_nova_p54t as p54t
import controler_qualite_passation_nova_p54o as p54o
import preparer_passation_humaine_nova_p54n as p54n

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P54U_FICHES_LOCALISATION_CIBLEES_2024.json"
NO_GO="NO_GO_AUTOMATIQUE"
CHECKS=(
 "VERIFIER_VERSION_PDF","REPRODUIRE_EXTRACTION_NFKC",
 "REPERER_SUR_PAGE_VISUELLE","QUALIFIER_NATURE_JETON",
 "CONTRE_REVUE_INDEPENDANTE",
)
GUARDS={
 "bilans_p54t_sha256_obligatoires_pour_fiches",
 "aucun_pdf_relu_par_p54u","aucun_zip_relu_par_p54u",
 "offsets_nonsimilaires_aux_coordonnees_visuelles",
 "aucune_valeur_numerique_brute_publiee",
 "aucun_avis_authentifie","aucune_occurrence_classee_comme_economie",
 "date_probable_non_close","quatre_dossiers_p54e_non_clos",
 "p54o_blocages_non_leves","quarante_taches_p54n_non_attestees",
 "controles_p54b_p54c_ouverts","pas_de_double_compte_consolidation",
 "continuite_emplois_services",
 "deux_scenarios_constitutionnels_distincts",
 "aucune_transmission_externe","no_go_automatique",
 "main_non_fusionnee","sinjira_inchange",
}
INITIAL={
 "bilans_figes_relus_dans_ce_jalon":0,"pdf_reacquis":0,
 "positions_reextraites":0,"offsets_historique_exploites":0,
 "verifications_humaines_effectuees":0,
 "controles_p54b_non_attestes":96,"controles_p54c_non_attestes":8,
 "actions_p54n_non_attestees":40,"blocages_p54o_non_leves":10,
 "avis_professionnels_authentifies":0,
 "economies_certifiees_cad":None,"decision":NO_GO,
}
SOURCES=p54n.SOURCES

def need(ok,why):
    if not ok:raise ValueError(why)

def configuration():
    prior=p54t.configuration()
    p54o.configuration()
    pn=p54n.configuration()
    expected={
       "schema_version":"P54U-1","date_reference":"2026-10-24",
       "source_jalons":["P54P","P54T","P54O","P54N"],
       "reference_run_p54p":prior["reference_run_p54p"],
       "reference_artifact_p54p":prior["reference_artifact_p54p"],
       "exercice":2024,"observations_historiques":5,
       "dossiers_p54e":4,"observation_date_probable":1,
       "controles_humains_par_observation":list(CHECKS),
       "protections":{x:True for x in GUARDS},
       "etat_initial":INITIAL,
    }
    data=json.loads(CONFIG.read_text("utf-8"))
    need(data==expected and pn["source_p54d_run"]==40120462237
         and prior["position_ref_count"]==5
         and pn["etat_initial"]["positions_a_instruire"]==40,
         "REGISTRE_P54U_INVALIDE")
    return data

def build_cards(cfg,verified):
    """Requires verified bytes of both public P54T JSON, no raw PDF."""
    need(type(verified) is dict
         and verified.get("bilans_figes_verifies")==2
         and verified.get("positions_historiques_hachees")==5
         and verified.get("tailles_octets_verifiees")==3426,
         "BILANS_FIGES_NON_REVERIFIES")
    original=p54o.configuration()
    pack,_=p54o.canonical_sources(original)
    plan=p54o.matrix(original,pack)
    previous={x["observation_index"]:x for x in plan["observations"]}
    rows=verified["positions_de_reference"]
    need(type(rows) is list and len(rows)==5
         and rows==p54t.p54r.known_rows()
         and set(previous)==set(range(5))
         and len(plan["points_bloquants"])==10,
         "CHAINAGE_P54O_P54T_INCOHERENT")
    result=[]
    for row in rows:
        idx=row["index_observation_p54d"]
        old=previous[idx]
        source=row["source"]
        offset=row["offset_texte_extrait"]
        length=row["longueur_texte_normalise_nfkc"]
        need(source in SOURCES
             and type(idx) is int
             and type(offset) is int
             and type(length) is int and 0<=offset<length
             and row["pdf_index_zero"]==old["index_pdf_base_zero"]
             and row["source"]==old["source"]
             and row["zone_confirmee_par_parseur"]==old["zone"]
             and row["classification_indicative"]==old["classification"]
             and row["dossier"]==(old["identifiant"] if old["est_dossier_p54e"] else None)
             and row["aucune_conclusion_financiere"] is True,
             "OFFSETS_HISTORIQUES_HORS_CHAINE")
        result.append({
          "identifiant":old["identifiant"],
          "dossier_p54e":old["est_dossier_p54e"],
          "publication":source,"url_pdf_public":SOURCES[source],
          "page_pdf_index_zero":row["pdf_index_zero"],
          "offset_caractere_nfkc":offset,
          "longueur_texte_nfkc":length,
          "zone_indicative":old["zone"],
          "qualification_indicative":old["classification"],
          "type_position":"INDEX_CARACTERE_TEXTE_NFKC_NON_COORDONNEE_PDF",
          "preuves_historique_sha256_bilans_p54t":True,
          "original_pdf_relus_dans_ce_jalon":False,
          "avis_expert_authentifie":False,
          "qualification_humaine_confirmee":False,
          "travail_humain_a_effectuer":[{
              "controle":c,"etat":"A_INSTRUIRE",
              "attestation_reelle":False} for c in CHECKS],
        })
    need(len(result)==5 and
         sum(x["dossier_p54e"] for x in result)==4
         and len({x["identifiant"] for x in result})==5
         and sum(len(x["travail_humain_a_effectuer"]) for x in result)==25,
         "FICHES_MANQUANTES")
    return {
      "schema_version":"P54U-FICHES-1","exercice":2024,
      "reference_workflow_p54p":cfg["reference_run_p54p"],
      "reference_artifact_p54p":cfg["reference_artifact_p54p"],
      "source":"DEUX_BILANS_PUBLICS_P54T_REVERIFIES_SHA256",
      "verification_octets_bilans_au_run_courant":True,
      "pdf_relus_au_run_courant":0,
      "fiches":result,
      "blocages_p54o_non_leves":10,
      "taches_p54n_a_instruire":40,
      "autorisation_transmission_obtenue":False,
      "signature_certifiee":False,
      "economies_certifiees_cad":None,
      "decision":NO_GO,
    }

def report(cfg,verified=None):
    good=verified is not None
    return {
      "schema_version":"P54U-BILAN-1",
      "exercice":2024,
      "reference_workflow_p54p":cfg["reference_run_p54p"],
      "deux_bilans_publics_p54t_reverifies_ce_run":2 if good else 0,
      "octets_bilans_publics_reverifies_ce_run":
           verified["tailles_octets_verifiees"] if good else 0,
      "positions_historiques_vers_fiches":5 if good else 0,
      "qualifications_humaines_reelles_effectuees":0,
      "fiches_p54e_ouvertes":4,"date_probable_non_certifiee":1,
      "verifications_humaines_a_instruire":25,
      "blocages_p54o_non_leves":10,
      "taches_p54n_non_attestees":40,
      "controles_p54b_non_attestes":96,
      "controles_p54c_non_attestes":8,
      "pdf_originaux_reacquis_ce_run":0,
      "zip_original_reverifie_ce_run":False,
      "mandats_originaux_authentifies":0,
      "economies_certifiees_cad":None,
      "pret_a_transmettre":False,
      "fusion_main_autorisee":False,
      "decision":NO_GO,
    }

def instructions(cards):
    need(cards["schema_version"]=="P54U-FICHES-1"
         and len(cards["fiches"])==5
         and cards["decision"]==NO_GO,
         "FICHES_NON_VALIDES")
    lines=[
      "# P54U — Feuilles ciblées de localisation des cinq occurrences",
      "",
      "**Préparation documentaire uniquement. Aucune transmission autorisée.**",
      "",
      "Ces positions proviennent du même résultat P54P (deux bilans publics",
      "figés, contrôlés par SHA-256 dans P54T). Aucun PDF n'a été relu ici.",
      "Les nombres sont des indices de caractères après normalisation NFKC,",
      "PAS des coordonnées sur les pages, ni des montants monétaires.",
      "",
    ]
    for x in cards["fiches"]:
        lines.extend([
          "## "+x["identifiant"],"",
          "Source publique : "+x["url_pdf_public"],"",
          "Index PDF (base zéro) : "+str(x["page_pdf_index_zero"]),
          "",
          "Offset dans le texte NFKC : "+str(x["offset_caractere_nfkc"])
          +" / "+str(x["longueur_texte_nfkc"]),
          "",
          "Qualification indicative non certifiée : "+x["qualification_indicative"],
          "",
          "| Vérification humaine | État |",
          "|---|---|",
        ])
        for c in x["travail_humain_a_effectuer"]:
            lines.append("| "+c["controle"]+" | A_INSTRUIRE |")
        lines.append("")
    lines.extend([
      "## Conditions de décision","",
      "Localiser visuellement chaque occurrence dans un original autorisé,",
      "qualifier sa nature et conserver la trace privée des pièces primaires.",
      "Une contre-revue indépendante doit examiner les désaccords.",
      "Une année/date probable ne devient pas une preuve sans confirmation.",
      "Aucune authentification de signature ou statut professionnel ne",
      "résulte des offsets ou des empreintes SHA-256 des bilans.",
      "Les dix blocages P54O et quarante tâches P54N restent ouverts.",
      "Ne pas convertir en économie les opérations réciproques déjà",
      "éliminées Ville–RTC–SOMHAC. Maintenir emplois et services.",
      "Étudier séparément Québec dans le Canada et souveraineté hypothétique.",
      "",
      "**NO_GO_AUTOMATIQUE — aucune transmission, aucun dossier clos,",
      "aucune fusion main, aucune modification SINJIRA.**","",
    ])
    return "\n".join(lines)

def write_new(path,document):
    p=Path(path)
    need(not p.exists() and not p.is_symlink()
         and p.parent.is_dir() and not p.parent.is_symlink(),
         "SORTIE_EXISTANTE_OU_INVALIDE")
    with p.open("x",encoding="utf-8") as f:
        if type(document) is str:
            f.write(document)
        else:
            json.dump(document,f,ensure_ascii=False,sort_keys=True,indent=2)
            f.write("\n")

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verifier-bilans-figes",action="store_true")
    ap.add_argument("--fiches")
    ap.add_argument("--instructions")
    ap.add_argument("--bilan")
    ap.add_argument("--exiger-remise",action="store_true")
    a=ap.parse_args(argv)
    try:
        outputs=[Path(n) for n in (a.fiches,a.instructions,a.bilan) if n]
        need(len({p.resolve() for p in outputs})==len(outputs)
             and all(not p.exists() and not p.is_symlink() for p in outputs),
             "SORTIES_NON_DISTINCTES")
        need(a.verifier_bilans_figes or not (a.fiches or a.instructions),
             "FICHES_EXIGENT_VERIFICATION_EFFECTIVE_DES_BILANS_FIGES")
        cfg=configuration()
        checked=p54t.verify_frozen(p54t.configuration()) \
            if a.verifier_bilans_figes else None
        cards=build_cards(cfg,checked) if checked is not None else None
        bilan=report(cfg,checked)
        if a.fiches:write_new(a.fiches,cards)
        if a.instructions:write_new(a.instructions,instructions(cards))
        if a.bilan:write_new(a.bilan,bilan)
        print(json.dumps(bilan,sort_keys=True,ensure_ascii=False))
        return 3 if a.exiger_remise else 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P54U_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
