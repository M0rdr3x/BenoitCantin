#!/usr/bin/env python3
"""P55A — matrice de passation à une expertise indépendante, jamais une expertise."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import preparer_passation_controlee_nova_p54z as p54z

ROOT = p54z.ROOT
BASE = p54z.BASE
CONFIG = BASE / "P55A_CADRE_REVUE_INDEPENDANTE_2024.json"
NO_GO = p54z.NO_GO
REFS = p54z.REFS
GATES = (
    "ORIGINE_ET_INTEGRITE_ORIGINAUX",
    "CHAINE_CONSERVATION_HORS_GIT",
    "BASE_LEGALE_ET_DROITS_ACCES",
    "MANDAT_ECRIT_ET_PERIMETRE_EXPERTISE",
    "QUALIFICATION_ET_INDEPENDANCE_EXPERTS",
    "CONFLITS_INTERETS",
    "CONTRE_LECTURE_VISUELLE_ET_NFKC",
    "CONTRADICTIONS_ET_RESERVES",
    "CONSOLIDATION_VILLE_RTC_SOMHAC",
    "IMPACT_EMPLOIS_SERVICES_ET_POUVOIR_ACHAT",
)
STATES = ("NON_INSTRUIT", "PREPARE_NON_ATTESTE", "RESERVE", "SUSPENDU")
GUARDS = {
    "aucun_expert_reel_designe", "aucune_authentification_professionnelle",
    "aucune_signature_ou_identite_dans_git", "declarations_privees_hors_depot",
    "fichiers_prives_0600_sans_liens_symboliques", "ancrage_sha256_p54z_requis",
    "chaine_p54z_complete_pour_preparation", "suspensions_p54z_prioritaires",
    "reserves_p55a_non_closes_automatiquement", "aucun_contact_ni_demande_externe",
    "aucun_fichier_original_publication_ci", "aucun_montant_ou_texte_brut_public",
    "aucun_avis_certifie_par_presence_fichier", "cinq_occurrences_non_qualifiees",
    "quatre_dossiers_p54e_ouverts", "date_probable_a_examiner",
    "quarante_taches_p54n_non_attestees", "dix_blocages_p54o_non_leves",
    "p54b_96_p54c_8_non_attestes", "pas_double_compte_ville_rtc_somhac",
    "maintien_emplois_et_services", "pouvoir_achat_non_degrade",
    "deux_regimes_constitutionnels_separes", "aucune_certification_fiscale",
    "aucune_fusion_main", "aucun_changement_sinjira", "no_go_automatique",
}
INITIAL = {
    "observations":5, "controles_revue":50, "positions_p54z":40,
    "dossiers_p54e_ouverts":4, "occurrence_date_probable_non_certifiee":1,
    "taches_p54n_non_attestees":40, "blocages_p54o_non_leves":10,
    "controles_p54b_non_attestes":96, "controles_p54c_non_attestes":8,
    "experts_mandates_attestes":0, "avis_independants_authentifies":0,
    "signatures_authentifiees":0, "economies_certifiees_cad":None,
    "decision":NO_GO,
}


def need(test, msg):
    if not test:
        raise ValueError(msg)


def configuration():
    cfg = p54z.read_json(CONFIG)
    expected = {
        "schema_version":"P55A-1", "date_reference":"2026-11-03",
        "exercice_source":2024,
        "chaine_reference":["P54U","P54W","P54X","P54Y","P54Z"],
        "dossier_references":list(REFS),
        "controles":list(GATES), "etats":list(STATES),
        "protections":{name:True for name in GUARDS},
        "etat_initial":INITIAL,
    }
    need(cfg == expected, "CONFIGURATION_P55A_MODIFIEE")
    parent = p54z.configuration()
    need(parent["references"] == list(REFS)
         and len(parent["controles"]) == 8
         and parent["etat_initial"]["decision"] == NO_GO
         and parent["etat_initial"]["economies_certifiees_cad"] is None,
         "CHAINE_P54Z_NON_CONFORME")
    return cfg


def private_source(path):
    path = p54z.outside_repo(path)
    need(path.is_file() and not path.is_symlink()
         and (path.stat().st_mode & 0o777) == 0o600,
         "SOURCE_PRIVEE_INVALIDE")
    return path


def upstream(path):
    f = private_source(path)
    declared = p54z.read_json(f, 100000)
    p54z.validate_declarations(declared)
    raw = f.read_bytes()
    return declared, hashlib.sha256(raw).hexdigest()


def model(sha_p54z):
    need(type(sha_p54z) is str and len(sha_p54z) == 64
         and all(c in "0123456789abcdef" for c in sha_p54z),
         "ANCRAGE_SHA_INVALIDE")
    return {
        "schema_version":"P55A-DECLARATIONS-1", "exercice":2024,
        "sha256_declarations_p54z":sha_p54z,
        "dossiers":[
            {"reference":ref, "verifications":[
                {"code":gate, "etat":"NON_INSTRUIT"} for gate in GATES
            ]}
            for ref in REFS
        ],
    }


def validate_local(doc, p54z_doc, p54z_sha):
    need(type(doc) is dict
         and set(doc) == {"schema_version","exercice",
                          "sha256_declarations_p54z","dossiers"}
         and doc["schema_version"] == "P55A-DECLARATIONS-1"
         and type(doc["exercice"]) is int and doc["exercice"] == 2024
         and type(doc["sha256_declarations_p54z"]) is str
         and doc["sha256_declarations_p54z"] == p54z_sha
         and type(doc["dossiers"]) is list and len(doc["dossiers"]) == 5,
         "FICHE_P55A_OU_ANCRAGE_INVALIDE")
    p54z.validate_declarations(p54z_doc)
    counts = {name:0 for name in STATES}
    inherited = 0
    for idx, row in enumerate(doc["dossiers"]):
        need(type(row) is dict
             and set(row) == {"reference","verifications"}
             and row["reference"] == REFS[idx]
             and type(row["verifications"]) is list
             and len(row["verifications"]) == len(GATES),
             "DOSSIER_P55A_INCONNU")
        statuses = [r["etat"] for r in p54z_doc["dossiers"][idx]["controles"]]
        prepared = all(s == "PREPARATION_DECLAREE_NON_VERIFIEE"
                       for s in statuses)
        inherited += statuses.count("SUSPENDU")
        for j, control in enumerate(row["verifications"]):
            need(type(control) is dict and set(control) == {"code","etat"}
                 and control["code"] == GATES[j]
                 and type(control["etat"]) is str
                 and control["etat"] in STATES,
                 "CONTROLE_P55A_HORS_VOCABULAIRE")
            if control["etat"] == "PREPARE_NON_ATTESTE":
                need(prepared, "PREPARATION_P55A_SANS_40_POSITIONS_P54Z")
            counts[control["etat"]] += 1
    need(sum(counts.values()) == 50, "COUVERTURE_P55A_INCOMPLETE")
    return counts, inherited


def report(counts=None, inherited=0):
    if counts is None:
        counts = {name:(50 if name == "NON_INSTRUIT" else 0)
                  for name in STATES}
    need(type(counts) is dict and set(counts) == set(STATES)
         and all(type(v) is int and v >= 0 for v in counts.values())
         and sum(counts.values()) == 50
         and type(inherited) is int and 0 <= inherited <= 40,
         "BILAN_P55A_INVALIDE")
    return {
        "schema_version":"P55A-BILAN-1", "exercice":2024,
        "observations_non_certifiees":5,
        "verifications_preparees":50,
        "distribution_declarations_non_authentifiees":dict(counts),
        "suspensions_p54z_heritees":inherited,
        "suspensions_p55a_declarees":counts["SUSPENDU"],
        "reserves_p55a_ouvertes":counts["RESERVE"],
        "experts_mandates_attestes":0,
        "independance_experts_authentifiee":False,
        "avis_independants_authentifies":0,
        "signatures_officielles_verifiees":0,
        "qualifications_definitives":0,
        "dossiers_p54e_ouverts":4,
        "occurrence_date_probable_non_certifiee":1,
        "taches_p54n_non_attestees":40,
        "blocages_p54o_non_leves":10,
        "controles_p54b_non_attestes":96,
        "controles_p54c_non_attestes":8,
        "economies_certifiees_cad":None,
        "autorisation_envoi_externe":False,
        "autorisation_fermeture_dossier":False,
        "autorisation_fusion_main":False,
        "decision":NO_GO,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--declarations-p54z")
    parser.add_argument("--creer-modele-prive")
    parser.add_argument("--relecture-locale")
    parser.add_argument("--bilan-public")
    parser.add_argument("--exiger-go", action="store_true")
    a = parser.parse_args(argv)
    try:
        configuration()
        need(not a.relecture_locale or a.declarations_p54z,
             "RELECTURE_P55A_REQUIERT_P54Z")
        need(not a.creer_modele_prive or a.declarations_p54z,
             "MODELE_P55A_REQUIERT_P54Z")
        need(not (a.creer_modele_prive and a.relecture_locale),
             "MODELE_ET_LECTURE_SIMULTANES_INTERDITS")
        sources = [p for p in (a.declarations_p54z,a.relecture_locale) if p]
        targets = [p for p in (a.creer_modele_prive,a.bilan_public) if p]
        src_paths = [private_source(p) for p in sources]
        out_paths = [Path(p).expanduser().absolute() for p in targets]
        need(len(set(p.resolve() for p in src_paths + out_paths))
             == len(src_paths + out_paths), "CHEMINS_DUPLIQUES")
        for out in out_paths:
            need(not out.exists() and not out.is_symlink()
                 and out.parent.is_dir() and not out.parent.is_symlink(),
                 "SORTIE_EXISTANTE_OU_NON_AUTORISEE")
        if a.creer_modele_prive:
            p54z.outside_repo(a.creer_modele_prive)
        doc = None
        sha = None
        if a.declarations_p54z:
            doc, sha = upstream(a.declarations_p54z)
        if a.creer_modele_prive:
            p54z.write_new(a.creer_modele_prive, model(sha), private=True)
        totals = None
        inherited = 0
        if a.relecture_locale:
            local = p54z.read_json(private_source(a.relecture_locale),100000)
            totals, inherited = validate_local(local,doc,sha)
        result = report(totals,inherited)
        if a.bilan_public:
            p54z.write_new(a.bilan_public,result)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if a.exiger_go else 0
    except (ValueError, TypeError, KeyError, OSError, UnicodeError,
            json.JSONDecodeError):
        print("P55A_REFUS: DOSSIER_OU_ANCRAGE_NON_CONFORME",file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
