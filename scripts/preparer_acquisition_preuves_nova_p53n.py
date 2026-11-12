#!/usr/bin/env python3
"""P53N — Plan d'acquisition des preuves : aucun accès ou audit réellement effectué."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import construire_registre_couts_evitables_nova_p53m as precedent

ROOT = Path(__file__).resolve().parents[1]
ETUDES = ROOT / "projets" / "projet-nova" / "etudes"
CADRE = ETUDES / "P53N_PLAN_ACQUISITION_PREUVES.json"
REGIMES = precedent.REGIMES
TYPES = precedent.PREUVES
GARANTIES = precedent.precedent.PROTECTIONS
ETATS = (
    "NON_DEMANDE",
    "REPERE_PUBLIC_DECLARATIF",
    "DEMANDE_PREPAREE_NON_ENVOYEE",
    "ENVOI_DECLARE_NON_VERIFIE",
    "REPONSE_DECLAREE_NON_VERIFIEE",
    "REFUS_DECLARE_NON_VERIFIE",
)
NO_GO = "NO_GO_AUTOMATIQUE"
CHAMPS_DECLARATION = {
    "schema_version", "regime", "categorie", "reference_exercice",
    "nature_source", "documents", "garanties", "acces_licite",
}

def require(ok, code):
    if not ok:
        raise ValueError(code)

def lire(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink()
            and 0 < p.stat().st_size <= 40000, "SOURCE_INDISPONIBLE")
    result = json.loads(p.read_text(encoding="utf-8"))
    require(type(result) is dict, "OBJET_JSON_ATTENDU")
    return result

def sources():
    p53l, p53m, nb, nd = precedent.sources()
    cfg = lire(CADRE)
    require(cfg["schema_version"] == "P53N-1"
            and cfg["statut"] == "PLAN_PREPARATOIRE_SANS_DEMANDE_ENVOYEE"
            and cfg["exercice_reference"] == 2024
            and cfg["projection_hypothetique"] == 2027
            and cfg["regimes"] == list(REGIMES)
            and cfg["categories"] == p53m["categories"]
            and cfg["types_pieces"] == list(TYPES)
            and cfg["garanties"] == list(GARANTIES)
            and cfg["etats_declaratifs"] == list(ETATS)
            and cfg["ordre_acquisition"] == list(TYPES)
            and len(set(cfg["ordre_acquisition"])) == 12
            and set(cfg["verrous"]) == {
                "aucun_envoi_sans_action_humaine",
                "aucune_reception_authentifiee",
                "aucun_stockage_documents_originaux_dans_git",
                "aucun_renseignement_personnel_dans_rapport",
                "aucune_economie_financiere_inventee",
                "montants_inconnus_restent_nuls",
                "droits_confidentialite_respectes",
                "emplois_et_services_proteges",
                "regimes_constitutionnels_non_cumules",
                "aucun_delai_legal_demarre_sans_depot_effectif",
                "aucune_fusion_automatique",
                "avis_independant_exige",
            }
            and all(v is True for v in cfg["verrous"].values())
            and cfg["etat_initial"]["demandes_effectivement_envoyees"] == 0
            and cfg["etat_initial"]["originaux_authentifies"] == 0
            and cfg["etat_initial"]["economies_certifiees_cad"] is None,
            "PLAN_D_ACQUISITION_NON_CONFORME")
    require(nb == 1344 and nd == 26
            and p53m["etat_initial"]["economies_certifiees_cad"] is None
            and p53m["etat_initial"]["decision"] == NO_GO,
            "SOURCE_PRECEDENTE_NON_VERIFIEE")
    return p53m, cfg, nb, nd

def construire_registre(cfg):
    fiches = []
    for regime in REGIMES:
        for categorie in cfg["categories"]:
            fiches.append({
                "regime": regime,
                "categorie": categorie,
                "exercice": 2024,
                "etat_pieces": {nom: "NON_DEMANDE" for nom in TYPES},
                "garanties": {nom: "INCONNU" for nom in GARANTIES},
                "provenance_officielle_verifiee": False,
                "envoi_reel_atteste": False,
                "originaux_authentifies": 0,
                "avis_independant_signe_valide": False,
                "economie_certifiee_cad": None,
                "statut": "ACQUISITION_NON_ENTAMEE",
            })
    require(len(fiches) == 12
            and len({(f["regime"], f["categorie"]) for f in fiches}) == 12,
            "REGISTRE_DOIT_CONTENIR_12_FICHES")
    return fiches

def evaluer_declaration(d, cfg):
    """Une déclaration de suivi n'établit jamais la réception ou l'authenticité d'une pièce."""
    require(type(d) is dict and set(d) == CHAMPS_DECLARATION
            and d["schema_version"] == "P53N-DECLARATION-1",
            "FORMAT_DECLARATION_INVALIDE")
    regime, cat = d["regime"], d["categorie"]
    require(regime in REGIMES and cat in cfg["categories"],
            "REGIME_CATEGORIE_INCONNU")
    require(type(d["reference_exercice"]) is int
            and d["reference_exercice"] == 2024,
            "EXERCICE_NON_CONFORME")
    require(d["nature_source"] in ("INCONNUE", "DOCUMENT_PUBLIC_POTENTIEL",
                                   "DEMANDE_ACCES_POTENTIELLE"),
            "NATURE_SOURCE_NON_ACCEPTEE")
    documents = d["documents"]
    require(type(documents) is dict and set(documents) == set(TYPES)
            and all(type(e) is str and e in ETATS for e in documents.values()),
            "ETATS_PIECES_NON_ADMISSIBLES")
    garanties = d["garanties"]
    require(type(garanties) is dict and set(garanties) == set(GARANTIES)
            and all(type(v) is str and v in ("OUI", "NON", "INCONNU")
                    for v in garanties.values()),
            "GARANTIES_NON_ADMISSIBLES")
    require(d["acces_licite"] in ("INCONNU", "OUI_DECLARATIF", "NON"),
            "DECLARATION_ACCES_NON_ADMISSIBLE")
    # Le mot OUI dans des métadonnées saisies par un tiers n'est pas une preuve.
    if d["acces_licite"] == "NON":
        statut = "ACCES_NON_AUTORISE_A_EXCLURE"
    elif any(v == "NON" for v in garanties.values()):
        statut = "GARANTIES_VIOLEES"
    elif d["acces_licite"] == "INCONNU":
        statut = "BASE_JURIDIQUE_ACCES_NON_DEMONTREE"
    elif "INCONNU" in garanties.values():
        statut = "PROTECTIONS_NON_DEMONTREES"
    elif "REFUS_DECLARE_NON_VERIFIE" in documents.values():
        statut = "REFUS_D_ACCES_DECLARE_A_EXAMINER"
    elif "NON_DEMANDE" in documents.values():
        statut = "PIECES_NON_DEMANDEES"
    elif "DEMANDE_PREPAREE_NON_ENVOYEE" in documents.values():
        statut = "DEMANDES_PREPAREES_NON_TRANSMISES"
    elif "ENVOI_DECLARE_NON_VERIFIE" in documents.values():
        statut = "ENVOI_DECLARE_A_VERIFIER"
    elif "REPONSE_DECLAREE_NON_VERIFIEE" in documents.values():
        statut = "REPONSES_DECLAREES_A_AUTHENTIFIER"
    else:
        statut = "REPERAGE_PUBLIC_DECLARATIF_A_VERIFIER"
    return {
        "cle": (regime, cat),
        "statut": statut,
        "pieces_authentifiees": 0,
        "demandes_verifiees_envoyees": 0,
        "avis_independants_valides": 0,
        "economie_certifiee_cad": None,
    }

def bilan(cfg, nb, nd, declarations):
    repartition = Counter(x["statut"] for x in declarations)
    return {
        "schema_version": "P53N-RAPPORT-1",
        "organismes_source_mamh_2024": nb,
        "dossiers_p53k_non_certifies": nd,
        "regimes": len(REGIMES),
        "categories": len(cfg["categories"]),
        "fiches_d_acquisition_preparees": 12,
        "emplacements_de_pieces_non_obtenues": 12 * len(TYPES),
        "declarations_examinees_formellement": len(declarations),
        "statuts_declarations_agreges": dict(sorted(repartition.items())),
        "pieces_primaires_authentifiees": 0,
        "demandes_effectivement_envoyees_verifiees": 0,
        "revues_independantes_validees": 0,
        "economies_certifiees_cad": None,
        "economies_certifiees_par_regime_cad": {x: None for x in REGIMES},
        "couts_deplaces_aux_citoyens_certifies_cad": None,
        "reductions_effectifs_autorisees": 0,
        "services_essentiels_degrades_autorises": False,
        "preuves_F01_F20_validees": 0,
        "montants_fiscaux_Nova_inconnus": 1320,
        "decision": NO_GO,
        "pret_a_certification": False,
    }

def ecrire_sortie(path, value):
    p = Path(path)
    require(not p.exists() and not p.is_symlink(), "ECRASEMENT_REFUSE")
    with p.open("x", encoding="utf-8") as out:
        out.write(json.dumps(value, sort_keys=True, indent=2,
                             ensure_ascii=False) + "\n")

def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--rapport")
    a.add_argument("--registre")
    a.add_argument("--declaration", action="append", default=[])
    a.add_argument("--exiger-preuves-certifiees", action="store_true")
    args = a.parse_args(argv)
    try:
        require(len(args.declaration) <= 12, "TROP_DE_DECLARATIONS")
        require(not (args.rapport and args.registre
                    and Path(args.rapport).resolve() == Path(args.registre).resolve()),
                "SORTIES_IDENTIQUES_REFUSEES")
        for path in (args.rapport, args.registre):
            if path:
                p = Path(path)
                require(not p.exists() and not p.is_symlink(), "ECRASEMENT_REFUSE")
        _, cfg, nb, nd = sources()
        etats = []
        seen = set()
        for path in args.declaration:
            d = evaluer_declaration(lire(path), cfg)
            require(d["cle"] not in seen, "DECLARATION_DOUBLON")
            seen.add(d["cle"])
            etats.append(d)
        result = bilan(cfg, nb, nd, etats)
        if args.rapport:
            ecrire_sortie(args.rapport, result)
        if args.registre:
            ecrire_sortie(args.registre, {
                "schema_version": "P53N-REGISTRE-1",
                "fiches": construire_registre(cfg),
                "etat": "PLAN_PREPARATOIRE_SANS_ENVOI",
            })
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return 3 if args.exiger_preuves_certifiees else 0
    except (ValueError, TypeError, OSError, KeyError,
            UnicodeError, json.JSONDecodeError) as exc:
        print("P53N_REFUS: " + str(exc), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
