#!/usr/bin/env python3
"""A1 guard: Livre I source artifacts stay faithful and non-deployed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "projets/sinjira/codex/livre-i-source-artifacts-2026-09-15.json"
CONTRACT = ROOT / "projets/sinjira/codex/livre-i-delivery-contract.json"

EXPECTED = {
    "full_sha": "cd5eb783ff16311d819c7e0153b3c5fcecacce10d47b999b5c427e20065c781a",
    "demo_sha": "43f2fa19ebc8299fb23c0aa09c010518ddc705d53985964fe1c5fe9331c05eab",
    "demo_text_sha": "74bd791170e6697c15edac9d1df4c5418e439d6c5abeac8824575648922921a3",
    "candidate_sha": "b42353031681fa206e7cf85ca39d342a8b59a6e092755fd5c61def4d899666c2",
    "rejected_sha": "21bea0722660f085d947d02d6b868eb2a6033f8b921d83d6786a512d829588a3",
    "front_sha": "1861ad785685b21518e65c3469739727a3546ddf2bdecfa2e2b5834d1d565ff1",
    "back_sha": "fb44a442bead4a9af6f46cd3e5109ce2d9245fac7ce775fb2e1c3459a6f314c7",
}


def validate(manifest: dict, contract: dict) -> list[str]:
    errors: list[str] = []

    if manifest.get("schema") != "sinjira.livre-i.source-artifacts.v2":
        errors.append("Le manifeste source Livre I doit rester en schéma v2.")
    if manifest.get("state") != "staged_source_files_not_deployed":
        errors.append("Les artéfacts source doivent rester staged / non déployés.")
    if manifest.get("production_deployment_authorized") is not False:
        errors.append("Le manifeste ne doit jamais autoriser un déploiement production par défaut.")

    full = manifest.get("full_edition") or {}
    if full.get("pages") != 1066 or full.get("sha256") != EXPECTED["full_sha"]:
        errors.append("L’empreinte ou le nombre de pages de l’intégrale source a dérivé.")
    if full.get("public_repository_allowed") is not False:
        errors.append("L’intégrale ne doit jamais devenir un actif public du dépôt.")
    if full.get("storage_target") != "private_storage_only":
        errors.append("L’intégrale doit rester destinée au stockage privé seulement.")

    demo = manifest.get("demo_source") or {}
    if demo.get("pages") != 83 or demo.get("sha256") != EXPECTED["demo_sha"]:
        errors.append("La source démo vérifiée a dérivé.")
    if demo.get("text_extract_sha256") != EXPECTED["demo_text_sha"]:
        errors.append("L’empreinte du texte extrait de la démo source a dérivé.")

    candidate = manifest.get("demo_web_candidate") or {}
    if candidate.get("pages") != 83 or candidate.get("sha256") != EXPECTED["candidate_sha"]:
        errors.append("Le candidat web fidèle attendu n’est plus celui qui a été vérifié.")
    if candidate.get("text_extract_matches_source") is not True:
        errors.append("Le candidat web doit explicitement conserver le texte extractible de la source.")
    if candidate.get("text_extract_sha256") != demo.get("text_extract_sha256"):
        errors.append("Le candidat web et la source doivent avoir la même empreinte de texte extrait.")
    if candidate.get("deployment_authorized") is not False:
        errors.append("Le candidat web ne doit pas être publié sans décision humaine explicite.")
    render = candidate.get("render_compare") or {}
    if render.get("pages_compared") != 83 or render.get("engine") != "pdftoppm":
        errors.append("La preuve de comparaison visuelle intégrale du candidat web est incomplète.")

    rejected = manifest.get("rejected_demo_candidates") or []
    rejected_by_sha = {row.get("sha256"): row for row in rejected if isinstance(row, dict)}
    bad = rejected_by_sha.get(EXPECTED["rejected_sha"])
    if not bad or bad.get("reason") != "text_extraction_not_faithful":
        errors.append("Le candidat démo dont le texte n’est pas fidèle doit rester explicitement rejeté.")

    front = manifest.get("cover_front_source") or {}
    back = manifest.get("cover_back_source") or {}
    if front.get("sha256") != EXPECTED["front_sha"] or front.get("dimensions") != "1024x1536":
        errors.append("La couverture avant source officielle a dérivé.")
    if back.get("sha256") != EXPECTED["back_sha"] or back.get("dimensions") != "1024x1536":
        errors.append("La quatrième de couverture source officielle a dérivé.")
    if front.get("deployment_authorized") is not False or back.get("deployment_authorized") is not False:
        errors.append("Les couvertures préparées ne doivent pas s’auto-autoriser en production.")

    if contract.get("publication_state") != "prepared_not_deployed":
        errors.append("Le contrat Livre I doit rester préparé mais non déployé.")
    full_contract = contract.get("full_edition") or {}
    if full_contract.get("production_deployment_authorized") is not False:
        errors.append("Le contrat de diffusion ne doit pas autoriser la production.")
    if full_contract.get("public_repository_allowed") is not False:
        errors.append("Le contrat ne doit jamais autoriser l’intégrale dans le dépôt public.")

    return errors


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def self_test() -> None:
    manifest = load(MANIFEST)
    contract = load(CONTRACT)
    if validate(manifest, contract):
        raise SystemExit("Le manifeste sain doit passer le garde A1.")

    mutations = []
    mutated = json.loads(json.dumps(manifest))
    mutated["production_deployment_authorized"] = True
    mutations.append(("autorisation production", mutated, contract))

    mutated = json.loads(json.dumps(manifest))
    mutated["full_edition"]["public_repository_allowed"] = True
    mutations.append(("intégrale publique", mutated, contract))

    mutated = json.loads(json.dumps(manifest))
    mutated["demo_web_candidate"]["text_extract_matches_source"] = False
    mutations.append(("texte candidat non fidèle", mutated, contract))

    mutated = json.loads(json.dumps(manifest))
    mutated["demo_web_candidate"]["text_extract_sha256"] = "0" * 64
    mutations.append(("empreinte texte différente", mutated, contract))

    mutated = json.loads(json.dumps(manifest))
    mutated["rejected_demo_candidates"] = []
    mutations.append(("candidat dégradé réhabilité", mutated, contract))

    mutated_contract = json.loads(json.dumps(contract))
    mutated_contract["full_edition"]["production_deployment_authorized"] = True
    mutations.append(("contrat production activé", manifest, mutated_contract))

    undetected = [name for name, m, c in mutations if not validate(m, c)]
    if undetected:
        raise SystemExit("Régressions non détectées: " + ", ".join(undetected))
    print(f"OK: {len(mutations)}/{len(mutations)} mutations d’artéfacts Livre I détectées.")


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
    print("OK Livre I: sources figées, candidat démo fidèle, candidat dégradé rejeté, production non autorisée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
