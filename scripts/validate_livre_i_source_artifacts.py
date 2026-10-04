#!/usr/bin/env python3
"""Garde Livre I: nouveaux maîtres du 2026-10-04, sans effacer la provenance historique."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "projets/sinjira/codex/livre-i-source-artifacts-2026-10-04.json"
HISTORICAL_MANIFEST = ROOT / "projets/sinjira/codex/livre-i-source-artifacts-2026-09-15.json"
CONTRACT = ROOT / "projets/sinjira/codex/livre-i-delivery-contract.json"
DEMO = ROOT / "projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf"

DEMO_SHA = "d0668a7b07a07321ef1e02cfceb826d3881330bb36417d53e5ff5bd32635628e"
FULL_SHA = "9acc8f561962850158cb073b122ee038c2731ee3b165deae482260c0cc1ad2d8"
DEMO_GIT_BLOB = "74f925631634c00f39e86aabbf67833091f7a8ff"
DEMO_TEXT_SHA = "fbbd50bd140aef24677228207462e822e4a3f3e5e923ac1f533fdf806facd2ae"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(manifest: dict, contract: dict) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema") != "sinjira.livre-i.source-artifacts.v3":
        errors.append("Le manifeste courant Livre I doit être en schéma v3.")
    if manifest.get("state") != "staged_source_files_not_deployed":
        errors.append("Les maîtres doivent rester staged / non déployés par défaut.")
    if manifest.get("production_deployment_authorized") is not False:
        errors.append("Le manifeste ne doit pas autoriser la production par défaut.")
    if manifest.get("historical_manifest_preserved") != HISTORICAL_MANIFEST.name:
        errors.append("La provenance historique du 15 septembre doit rester référencée.")
    if not HISTORICAL_MANIFEST.is_file():
        errors.append("Le manifeste historique du 15 septembre doit rester présent.")

    full = manifest.get("full_edition") or {}
    expected_full = {
        "pages": 1027,
        "size_bytes": 7_325_502,
        "sha256": FULL_SHA,
        "public_repository_allowed": False,
        "storage_target": "private_storage_only",
        "mime_type": "application/pdf",
    }
    for key, value in expected_full.items():
        if full.get(key) != value:
            errors.append(f"Intégrale maître incohérente: {key}.")

    demo = manifest.get("demo_source") or {}
    expected_demo = {
        "pages": 84,
        "size_bytes": 941_065,
        "sha256": DEMO_SHA,
        "text_extract_engine": "pdftotext",
        "text_extract_sha256": DEMO_TEXT_SHA,
        "mime_type": "application/pdf",
    }
    for key, value in expected_demo.items():
        if demo.get(key) != value:
            errors.append(f"Démo maître incohérente: {key}.")

    candidate = manifest.get("demo_web_candidate") or {}
    if candidate.get("pages") != 84 or candidate.get("size_bytes") != 941_065:
        errors.append("Le candidat web doit rester le maître 84 pages / 941065 octets.")
    if candidate.get("sha256") != DEMO_SHA:
        errors.append("Le SHA-256 du candidat web a dérivé.")
    if candidate.get("git_blob_sha1") != DEMO_GIT_BLOB:
        errors.append("Le blob Git exact de la démo a dérivé.")
    if candidate.get("binary_identical_to_source") is not True:
        errors.append("Le candidat web doit être binaire-identique à la source.")
    if candidate.get("text_extract_matches_source") is not True:
        errors.append("Le texte extrait du candidat doit être identique à la source.")
    if candidate.get("text_extract_sha256") != DEMO_TEXT_SHA:
        errors.append("L'empreinte du texte extrait de la démo a dérivé.")
    if candidate.get("deployment_authorized") is not False:
        errors.append("Le manifeste source ne doit pas auto-autoriser le déploiement.")

    if contract.get("publication_state") != "prepared_not_deployed":
        errors.append("Le contrat Livre I doit rester préparé mais non déployé.")
    contract_demo = contract.get("demo") or {}
    contract_full = contract.get("full_edition") or {}
    for key, value in (("pages",84),("size_bytes",941_065),("sha256",DEMO_SHA)):
        if contract_demo.get(key) != value:
            errors.append(f"Contrat démo incohérent: {key}.")
    for key, value in (("pages",1027),("size_bytes",7_325_502),("sha256",FULL_SHA)):
        if contract_full.get(key) != value:
            errors.append(f"Contrat intégrale incohérent: {key}.")
    if contract_full.get("production_deployment_authorized") is not False:
        errors.append("Le contrat ne doit pas autoriser la production.")
    if contract_full.get("public_repository_allowed") is not False:
        errors.append("L'intégrale doit rester interdite dans le dépôt public.")

    if not DEMO.is_file():
        errors.append("La démo publique suivie est absente.")
    else:
        import hashlib
        raw = DEMO.read_bytes()
        if len(raw) != 941_065:
            errors.append("La taille binaire de la démo suivie a dérivé.")
        if hashlib.sha256(raw).hexdigest() != DEMO_SHA:
            errors.append("Les octets de la démo suivie ont dérivé.")

    return errors


def self_test() -> None:
    manifest = load(MANIFEST)
    contract = load(CONTRACT)
    clean = validate(manifest, contract)
    if clean:
        raise SystemExit("Le manifeste sain doit passer: " + " | ".join(clean))

    cases = []
    m = json.loads(json.dumps(manifest)); m["production_deployment_authorized"] = True
    cases.append(("autorisation production", m, contract))
    m = json.loads(json.dumps(manifest)); m["full_edition"]["public_repository_allowed"] = True
    cases.append(("intégrale publique", m, contract))
    m = json.loads(json.dumps(manifest)); m["demo_web_candidate"]["binary_identical_to_source"] = False
    cases.append(("candidat transcodé", m, contract))
    m = json.loads(json.dumps(manifest)); m["demo_web_candidate"]["git_blob_sha1"] = "0" * 40
    cases.append(("blob Git différent", m, contract))
    c = json.loads(json.dumps(contract)); c["full_edition"]["production_deployment_authorized"] = True
    cases.append(("contrat production activé", manifest, c))

    undetected = [name for name, m, c in cases if not validate(m, c)]
    if undetected:
        raise SystemExit("Régressions non détectées: " + ", ".join(undetected))
    print(f"OK: {len(cases)}/{len(cases)} mutations des maîtres Livre I détectées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate(load(MANIFEST), load(CONTRACT))
    if errors:
        print(f"ÉCHEC artéfacts Livre I: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1
    print("OK Livre I: maître démo exact, intégrale privée 1027 pages, historique préservé, production non autorisée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
