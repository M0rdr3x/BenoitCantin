#!/usr/bin/env python3
"""Projet Nova P52I : auditer un registre de PISTES, jamais certifier une reforme."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "projets" / "projet-nova" / "etudes"
DEFAULT_CATALOG = STUDY / "P52I_SOURCES_ET_ATTESTATIONS.json"
DEFAULT_PROOFS = STUDY / "P52A_REGISTRE_PREUVES_FISCALES.json"
HOSTS = frozenset({
    "www.finances.gouv.qc.ca", "statistique.quebec.ca", "www.statcan.gc.ca",
    "www150.statcan.gc.ca", "www.canada.ca"
})
LEVELS = ("QUEBEC_PROVINCIAL", "CANADA_FEDERAL", "MUNICIPAL_LOCAL")

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def read_json(path):
    p = Path(path)
    require(p.is_file() and p.stat().st_size < 300_000, "FICHIER_ABSENT_OU_TROP_GRAND")
    data = json.loads(p.read_text(encoding="utf-8"))
    require(type(data) is dict, "OBJET_JSON_REQUIS")
    return data

def analyser(catalog, proofs):
    require(catalog.get("schema_version") == "P52I-1" and catalog.get("jalon") == "P52I",
            "SCHEMA_P52I_INVALIDE")
    require(catalog.get("statut") == "DOSSIER_DE_RECHERCHE_NON_ADOPTE",
            "STATUT_PROPOSITION_INVALIDE")
    for key in ("publication_autorisee", "fusion_autorisee", "source_revue_independante",
                "donnees_extraites_certifiees"):
        require(catalog.get(key) is False, "GO_OU_CERTIFICATION_NON_FONDEE_" + key)
    require(proofs.get("status") == "PROPOSITION_NON_ADOPTEE" and
            proofs.get("rates_selected") is False and
            proofs.get("automatic_go") is False and
            proofs.get("financial_model_certified") is False,
            "P52A_ABANDON_DE_GARDE_FOU")
    expected = proofs.get("required_evidence")
    plan = catalog.get("plan_preuves")
    require(type(expected) is list and type(plan) is list and
            len(expected) == len(plan) == 20, "20_PREUVES_REQUISES")
    ids = [f"F{i:02d}" for i in range(1,21)]
    require([e.get("id") for e in expected] == ids and
            [e.get("id") for e in plan] == ids, "ID_PREUVES_NON_CONCORDANTS")
    for e, p in zip(expected, plan):
        require(e.get("statut") == "NON_VALIDE" and
                e.get("preuve_independante_obtenue") is False and
                e.get("decision_autorisee") is False,
                "PREUVE_P52A_NON_AUTORISEE")
        for key in ("regime", "theme"):
            require(p.get(key) == e.get(key), "MAPPAGE_PREUVE_INCORRECT")
        require(p.get("objet_preuve") == e.get("preuve_a_obtenir") and
                p.get("responsable_fonctionnel") == e.get("responsable_fonctionnel"),
                "BESOIN_DE_PREUVE_ALTERE")
        require(p.get("statut") == "NON_ATTESTEE" and
                p.get("adoption_autorisee") is False, "FAUSSE_ATTESTATION")
        for field in ("piece_expertise_independante", "reviseur_independant",
                      "validation_juridique", "montant_certifie"):
            require(p.get(field, "ABSENT") is None, "ATTESTATION_NON_OBTENUE_" + field)
    ss = catalog.get("sources")
    require(type(ss) is list and len(ss) == 8, "HUIT_PISTES_OFFICIELLES_ATTENDUES")
    names = [s.get("id") for s in ss]
    require(names == [f"S{i:02d}" for i in range(1,9)], "SOURCES_MANQUANTES_OU_DOUBLONS")
    for source in ss:
        u = urlsplit(source.get("url", ""))
        require(u.scheme == "https" and u.hostname in HOSTS and
                u.username is None and u.password is None and
                not u.query and not u.fragment and bool(u.path),
                "SOURCE_NON_AUTORISEE")
        require(source.get("type") == "PISTE_OFFICIELLE_A_EXAMINER" and
                source.get("preuve_validee") is False and
                source.get("extraction_chiffree", "ABSENT") is None and
                source.get("expert_independant", "ABSENT") is None,
                "PISTE_PRESENTEE_COMME_PREUVE")
    linked = 0
    for p in plan:
        candidates = p.get("source_ids_candidats")
        require(type(candidates) is list and len(candidates) == len(set(candidates)) and
                all(type(s) is str and s in names for s in candidates),
                "LIAISON_SOURCE_INVALIDE")
        linked += bool(candidates)
    levels = catalog.get("perimetres_budgetaires")
    require(type(levels) is list and
            [l.get("niveau") for l in levels] == list(LEVELS),
            "TROIS_PERIMETRES_BUDGETAIRES_REQUIS")
    require(all(l.get("conciliation") == "NON_EFFECTUEE" and
                l.get("montants_certifies", "ABSENT") is None for l in levels),
            "CONSOLIDATION_NON_PROUVEE")
    r = catalog.get("representativite")
    require(type(r) is dict and r.get("outil_candidat") == "STATCAN_BD_MSPS",
            "MODELE_REPRESENTATIF_NON_DOCUMENTE")
    for key in ("licence_signee", "microdonnees_utilisees", "echantillon_quebec_calibre",
                "poids_population_valides", "revision_independante",
                "effets_comportementaux_modelises", "pertes_population_demonstrees_absentes"):
        require(r.get(key) is False, "REPRESENTATIVITE_INVENTEE_" + key)
    # Ne retourner AUCUN contenu source, cas, URL ou personne.
    return {
        "jalon": "P52I", "schema_version": "P52I-1",
        "sources_officielles_candidatures": len(ss),
        "sources_avec_extraction_certifiee": 0,
        "preuves_P52A_requises": len(ids),
        "preuves_independantes_attestees": 0,
        "preuves_avec_piste_source": linked,
        "preuves_sans_piste_source": len(ids) - linked,
        "perimetres_budgetaires_separes": len(levels),
        "perimetres_budgetaires_concilies": 0,
        "licence_microsimulation_obtenue": False,
        "representativite_quebec_demontree": False,
        "inconnues_financieres_P52H_encore_a_documenter": 1320,
        "adoption_autorisee": False, "publication_autorisee": False,
        "fusion_autorisee": False, "decision": "NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--preuves", type=Path, default=DEFAULT_PROOFS)
    parser.add_argument("--rapport", type=Path)
    parser.add_argument("--exiger-preuves", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = analyser(read_json(args.catalogue), read_json(args.preuves))
        status = 3 if args.exiger_preuves else 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        result = {"jalon": "P52I", "statut": "ERREUR_VALIDATION",
                  "erreur_type": type(error).__name__,
                  "publication_autorisee": False, "fusion_autorisee": False,
                  "decision": "NO_GO_AUTOMATIQUE"}
        status = 2
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True, exist_ok=True)
        args.rapport.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return status

if __name__ == "__main__":
    raise SystemExit(main())
