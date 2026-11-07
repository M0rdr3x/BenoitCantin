#!/usr/bin/env python3
"""P54Z — passation locale de 40 contrôles, sans authentifier aucune expertise."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys

import verifier_preparation_revue_nova_p54y as p54y

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "projets/projet-nova/etudes"
CONFIG = BASE / "P54Z_PASSATION_CONTROLEE_2024.json"
NO_GO = "NO_GO_AUTOMATIQUE"
REFS = ("P54E-V-001", "P54E-M-001", "P54O-DATE-001",
        "P54E-M-002", "P54E-M-003")
CONTROLS = (
    "IDENTIFIER_SOURCE_ORIGINALE", "RETROUVER_OCCURRENCE_NFKC",
    "COMPARER_SUR_PAGE_VISUELLE", "QUALIFIER_NATURE_SUR_PIECE",
    "DISTINGUER_DATE_FOLIO_REFERENCE_VALEUR",
    "VALIDER_UNITE_EXERCICE_COLONNE_SI_PERTINENT",
    "CONSERVER_RESERVES_ET_DESACCORDS", "CONTRE_REVUE_INDEPENDANTE",
)
STATES = ("NON_INSTRUIT", "PREPARATION_DECLAREE_NON_VERIFIEE", "SUSPENDU")
ROLE_NAMES = ("GARANT_DOCUMENTAIRE", "LECTEUR", "CONTRE_LECTEUR",
              "REFERENT_JURIDIQUE", "REFERENT_COMPTABLE")


def require(condition, code):
    if not condition:
        raise ValueError(code)


def no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, "CLE_JSON_DUPLIQUEE")
        out[key] = value
    return out


def read_json(path, limit=180000):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "FICHIER_ABSENT_OU_LIEN")
    require(path.stat().st_size <= limit, "TAILLE_NON_AUTORISEE")
    return json.loads(path.read_text(encoding="utf-8"),
                      object_pairs_hook=no_duplicates,
                      parse_constant=lambda _x: require(False, "NOMBRE_NON_FINI"))


def outside_repo(path):
    path = Path(path).expanduser().absolute()
    real = path.resolve(strict=False)
    require(path != ROOT and ROOT not in path.parents
            and real != ROOT and ROOT not in real.parents,
            "CHEMIN_DANS_DEPOT_INTERDIT")
    require(not any(part.is_symlink() for part in (path, *path.parents)),
            "LIEN_SYMBOLIQUE_DANS_CHEMIN_INTERDIT")
    return path


def configuration():
    cfg = read_json(CONFIG)
    require(cfg.get("schema_version") == "P54Z-1"
            and cfg.get("date_reference") == "2026-11-03"
            and cfg.get("exercice") == 2024
            and cfg.get("source_jalons") == ["P54U","P54W","P54X","P54Y"]
            and cfg.get("references") == list(REFS)
            and cfg.get("controles") == list(CONTROLS)
            and cfg.get("roles_non_designes") == list(ROLE_NAMES)
            and cfg.get("etats_declaratifs") == list(STATES)
            and isinstance(cfg.get("protections"),dict)
            and len(cfg["protections"]) == 21
            and all(v is True for v in cfg["protections"].values())
            and cfg.get("etat_initial") == {
                "positions_de_revue":40, "positions_instruite_sur_preuve":0,
                "avis_professionnels_authentifies":0,
                "signatures_verifiees":0,
                "economies_certifiees_cad":None, "decision":NO_GO
            }, "CONFIGURATION_P54Z_NON_CONFORME")
    w = read_json(BASE / "P54W_GRILLE_QUALIFICATION_HUMAINE_2024.json")
    x = read_json(BASE / "P54X_VERROU_ORIGINAUX_AVANT_REVUE_2024.json")
    u = read_json(BASE / "P54U_FICHES_LOCALISATION_CIBLEES_2024.json")
    require(w.get("refs") == x.get("references") == list(REFS)
            and w.get("controles_reference") == list(CONTROLS)
            and u.get("observations_historiques") == 5
            and u.get("dossiers_p54e") == 4
            and x.get("etat_initial",{}).get("signatures_authentifiees") == 0
            and x.get("etat_initial",{}).get("decision") == NO_GO,
            "CHAINAGE_P54U_W_X_INCONFORME")
    y = p54y.report(p54y.configuration())
    require(y["decision"] == NO_GO
            and y["jalons_structurellement_presents"] == 8
            and y["revue_humaine_effectivement_realisee"] is False
            and y["economies_certifiees_cad"] is None,
            "PREPARATION_P54Y_NON_CONFORME")
    return cfg


def blank_model():
    return {
        "schema_version": "P54Z-DECLARATIONS-1",
        "exercice": 2024,
        "dossiers": [
            {"reference": ref,
             "controles": [{"code": control, "etat": "NON_INSTRUIT"}
                           for control in CONTROLS]}
            for ref in REFS
        ]
    }


def validate_declarations(doc):
    require(type(doc) is dict
            and set(doc) == {"schema_version","exercice","dossiers"}
            and doc["schema_version"] == "P54Z-DECLARATIONS-1"
            and type(doc["exercice"]) is int and doc["exercice"] == 2024
            and type(doc["dossiers"]) is list and len(doc["dossiers"]) == 5,
            "DECLARATIONS_SCHEMA_INVALIDE")
    totals = {name: 0 for name in STATES}
    for index, entry in enumerate(doc["dossiers"]):
        require(type(entry) is dict
                and set(entry) == {"reference","controles"}
                and entry["reference"] == REFS[index]
                and type(entry["controles"]) is list
                and len(entry["controles"]) == len(CONTROLS),
                "DOSSIER_INVALIDE")
        for number, row in enumerate(entry["controles"]):
            require(type(row) is dict and set(row) == {"code","etat"}
                    and row["code"] == CONTROLS[number]
                    and type(row["etat"]) is str and row["etat"] in STATES,
                    "CONTROLE_OU_STATUT_INVALIDE")
            totals[row["etat"]] += 1
    require(sum(totals.values()) == 40, "COUVERTURE_INCOMPLETE")
    return totals


def read_private_declarations(path):
    path = outside_repo(path)
    require(not path.is_symlink() and path.is_file()
            and stat.S_IMODE(path.stat().st_mode) == 0o600,
            "DECLARATIONS_NON_PRIVEES")
    return validate_declarations(read_json(path, 100000))


def write_new(path, data, private=False):
    path = Path(path).expanduser().absolute()
    if private:
        outside_repo(path)
    require(path.parent.is_dir() and not path.parent.is_symlink()
            and not path.exists() and not path.is_symlink(),
            "SORTIE_EXISTANTE_OU_CHEMIN_REFUSE")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600 if private else 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def public_report(counts=None):
    counts = counts or {STATES[0]:40, STATES[1]:0, STATES[2]:0}
    require(set(counts) == set(STATES)
            and all(type(value) is int and value >= 0 for value in counts.values())
            and sum(counts.values()) == 40, "COMPTEURS_INVALIDES")
    return {
        "schema_version":"P54Z-BILAN-1", "exercice":2024,
        "occurrences_non_certifiees":5, "controles_prepares":40,
        "declarations_locales_non_authentifiees":dict(counts),
        "suspensions_prioritaires":counts["SUSPENDU"],
        "revues_humaines_authentifiees":0,
        "signatures_professionnelles_verifiees":0,
        "qualifications_definitives":0,
        "dossiers_p54e_ouverts":4, "date_probable_non_confirmee":1,
        "taches_p54n_non_attestees":40, "blocages_p54o_non_leves":10,
        "controles_p54b_non_attestes":96, "controles_p54c_non_attestes":8,
        "economies_certifiees_cad":None,
        "transmission_autorisee":False, "certification_autorisee":False,
        "fusion_main_autorisee":False, "decision":NO_GO
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--creer-modele")
    parser.add_argument("--declarations")
    parser.add_argument("--bilan-public")
    parser.add_argument("--exiger-go", action="store_true")
    args = parser.parse_args(argv)
    try:
        configuration()
        require(not (args.creer_modele and args.declarations),
                "CREATION_ET_LECTURE_SIMULTANEES_INTERDITES")
        if args.creer_modele:
            write_new(args.creer_modele, blank_model(), private=True)
        counts = read_private_declarations(args.declarations) if args.declarations else None
        result = public_report(counts)
        if args.bilan_public:
            require(not args.creer_modele or
                    Path(args.bilan_public).expanduser().absolute() !=
                    Path(args.creer_modele).expanduser().absolute(),
                    "SORTIES_DUPLIQUEES")
            write_new(args.bilan_public, result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 3 if args.exiger_go else 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            json.JSONDecodeError):
        print("P54Z_REFUS: SOURCE_OU_DECLARATION_NON_CONFORME", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
