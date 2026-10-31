#!/usr/bin/env python3
"""Fail-closed CI: aucun nouvel export individuel dans les fichiers publics.

IMPORTANT: GitHub Pages diffuse encore la racine du dépôt en attendant #450.
Ceci est une défense CI contre de nouvelles fuites, PAS un confinement HTTP.
Ne loguer ni valeur de données ni contenu de fichier suspect.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOVA_DATA_DIR = Path("projets/projet-nova/data")
NOVA_REFERENCE_DIR = Path("projets/projet-nova/official/reference")
SINJIRA_DIR = Path("projets/sinjira")
NOVA_DATA_FILES = frozenset({
    "actualites.json", "boussole-electorale-v1.json",
    "boussole-electorale-v2.json", "boussole-partis-2026.json",
    "boussole-preuves-2026.json", "boussole-sources-partis-2026.json",
    "comptabilite.json", "documents-word-only.json", "documents.json",
    "rencontres.json", "sources.json",
    "modele_comptabilite.csv", "modele_rencontres.csv",
})
NOVA_REFERENCES = frozenset({
    "architecture-numerique-interoperabilite-reversibilite.md",
    "corpus.md", "cybersecurite-resilience-continuite.md",
    "finances.md", "identite-numerique-vie-privee.md",
    "programme.md", "statuts.md",
})
# Existants historiques : ne pas traiter les deux contrats comme des pages
# fonctionnelles. Toute nouvelle donnée JSON de projet est bloquée.
SINJIRA_EXISTING_JSON = frozenset({
    Path("projets/sinjira/codex/livre-i-delivery-contract.json"),
    Path("projets/sinjira/romans/livre-1-release.json"),
})
PRIVATE_KEYS = frozenset({
    "email", "e_mail", "mail", "phone", "telephone", "mobile",
    "user_id", "voter_id", "person_id", "respondent_id", "respondent",
    "votant_id", "participant_id", "ip", "ip_address", "date_of_birth",
    "adresse", "address", "password", "mot_de_passe", "secret",
    "access_token", "refresh_token", "auth_token", "jwt", "session_id",
    "ballot", "vote", "votes", "choice", "choix", "reponses",
    "responses", "raw_responses",
})
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
MAX_JSON_BYTES = 1_500_000
MAX_VISITED_NODES = 50_000
MAX_DEPTH = 32


def payload_issues(payload: object) -> set[str]:
    found: set[str] = set()
    stack = [(payload, 0)]
    n = 0
    while stack:
        node, depth = stack.pop()
        n += 1
        if n > MAX_VISITED_NODES or depth > MAX_DEPTH:
            found.add("structure JSON non bornée")
            break
        if isinstance(node, dict):
            for key, value in node.items():
                if not isinstance(key, str) or key.casefold() in PRIVATE_KEYS:
                    found.add("champ d'identification ou de réponse individuelle")
                stack.append((value, depth + 1))
        elif isinstance(node, list):
            stack.extend((value, depth + 1) for value in node)
        elif isinstance(node, str) and EMAIL.search(node):
            found.add("adresse courriel")
    return found


def check_json(file: Path) -> list[str]:
    rel = file.name  # Ne jamais imprimer une valeur ou un contenu sensible.
    if file.is_symlink():
        return [f"Lien symbolique JSON interdit: {rel}"]
    if file.stat().st_size > MAX_JSON_BYTES:
        return [f"Document JSON public trop volumineux: {rel}"]
    try:
        data = json.loads(file.read_text("utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return [f"Document JSON public invalide ou illisible: {rel}"]
    return [f"Document JSON public non conforme: {rel} ({problem})"
            for problem in sorted(payload_issues(data))]


def check_directory(root: Path, subdir: Path, allowed: frozenset[str]) -> list[str]:
    errors: list[str] = []
    target = root / subdir
    if not target.is_dir() or target.is_symlink():
        return [f"Répertoire public absent ou symbolique: {subdir.as_posix()}"]
    present: set[str] = set()
    for path in sorted(target.rglob("*")):
        rel = path.relative_to(target).as_posix()
        if path.is_dir() and not path.is_symlink():
            continue
        if rel not in allowed:
            errors.append(f"Artefact public non revu interdit: {subdir.as_posix()}/{rel}")
            continue
        present.add(rel)
        if path.is_symlink() or not path.is_file():
            errors.append(f"Artefact symbolique/invalide: {subdir.as_posix()}/{rel}")
        elif path.suffix.lower() == ".json":
            errors.extend(check_json(path))
    missing = allowed - present
    if missing:
        errors.append(f"Fichier(s) publics contractuels absents sous {subdir.as_posix()}: {len(missing)}")
    return errors


def check_repo(root: Path) -> list[str]:
    errors = check_directory(root, NOVA_DATA_DIR, NOVA_DATA_FILES)
    errors.extend(check_directory(root, NOVA_REFERENCE_DIR, NOVA_REFERENCES))
    sinjira = root / SINJIRA_DIR
    if not sinjira.is_dir() or sinjira.is_symlink():
        return errors + ["Répertoire SINJIRA absent ou symbolique."]
    for file in sorted(sinjira.rglob("*.json")):
        rel = file.relative_to(root)
        if rel not in SINJIRA_EXISTING_JSON:
            errors.append(f"Nouvel export JSON SINJIRA non revu: {rel.as_posix()}")
        elif not file.is_file() or file.is_symlink():
            errors.append(f"JSON SINJIRA symbolique/invalide: {rel.as_posix()}")
        else:
            errors.extend(check_json(file))
    for rel in SINJIRA_EXISTING_JSON:
        if not (root / rel).is_file():
            errors.append(f"Contrat JSON SINJIRA existant absent: {rel.as_posix()}")
    return errors


def self_test() -> None:
    assert not payload_issues({"questions": [{"responseScale": ["oui", "non"]}]})
    dangerous = [
        {"entries": [{"email": "fictif@example.org"}]},
        {"entries": [{"user_id": "test"}]},
        {"entries": [{"ballot": "A"}]},
        {"entries": [{"responses": []}]},
        {"text": "contact@example.org"},
        {"nested": {"session_id": "dummy"}},
    ]
    for entry in dangerous:
        assert payload_issues(entry), "Un export individuel synthétique a été autorisé."

    with tempfile.TemporaryDirectory(prefix="sinjira-data-guard-") as tmp:
        root = Path(tmp)
        for name in NOVA_DATA_FILES:
            p = root / NOVA_DATA_DIR / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("{}" if p.suffix == ".json" else "colonne\n", "utf-8")
        for name in NOVA_REFERENCES:
            p = root / NOVA_REFERENCE_DIR / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("# Référence publique\n", "utf-8")
        for rel in SINJIRA_EXISTING_JSON:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("{}", "utf-8")
        assert not check_repo(root), check_repo(root)

        unknown = root / NOVA_DATA_DIR / "resultats-individuels.json"
        unknown.write_text('{"ballot":"test"}', "utf-8")
        assert check_repo(root), "Un nouveau fichier de votes a été autorisé."
        unknown.unlink()

        known = root / NOVA_DATA_DIR / "actualites.json"
        known.write_text('{"results":[{"voter_id":"dummy"}]}', "utf-8")
        assert check_repo(root), "L'injection de données individuelles est acceptée."
        known.write_text("{}", "utf-8")

        unknown_ref = root / NOVA_REFERENCE_DIR / "notes-privees.md"
        unknown_ref.write_text("Interne", "utf-8")
        assert check_repo(root), "Une référence privée a été publiée."
        unknown_ref.unlink()

        unknown_sinjira = root / SINJIRA_DIR / "reponses-joueurs.json"
        unknown_sinjira.write_text("{}", "utf-8")
        assert check_repo(root), "Un export de joueurs est autorisé."
        unknown_sinjira.unlink()

        assert not check_repo(root), check_repo(root)
    print("PASS: confidentialité des données NOVA/SINJIRA et 10 scénarios de garde.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = check_repo(ROOT)
    if errors:
        print(f"ECHEC: {len(errors)} violation(s) du périmètre de données publiques.")
        for error in errors:
            print("- " + error)
        return 1
    print("PASS: 13 fichiers de données NOVA, 7 références et 2 contrats SINJIRA vérifiés.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
