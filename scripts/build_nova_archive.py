#!/usr/bin/env python3
"""Export reproductible des fichiers Git suivis associés à Projet Nova.

Conçu pour une exécution GitHub Actions sans accès réseau et sans clé d'écriture.
L'archive conserve les chemins originaux et ne traite jamais .git ou les secrets locaux.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
RELEVANT = re.compile(r"nova|boussole|sondage|electoral|électoral|scrutin", re.I)
EXTRA_SHARED = {
    "assets/css/site.css",
    "assets/js/site.js",
    "assets/js/site-personality-v25.js",
    "tests/e2e/test_public_site.py",
    "scripts/validate_public_root_shell.py",
}
FORBIDDEN_NAMES = {".env", ".env.local", ".env.production", "credentials.json"}
FORBIDDEN_SUFFIXES = {".pem", ".p12", ".pfx", ".key", ".sqlite3"}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], stderr=subprocess.PIPE)


def tracked_paths() -> list[str]:
    files = git("ls-files", "-z", "--cached").decode("utf-8", "strict").split("\0")
    return sorted(p for p in files if p)


def is_relevant(p: str) -> bool:
    return (
        p.startswith("projets/projet-nova/")
        or bool(RELEVANT.search(PurePosixPath(p).name))
        or p.startswith("docs/nova-sondages/")
        or p.startswith("docs/AVANCEMENT_QUATRE_PROGRAMMES_")
        or p in EXTRA_SHARED
    )


def selected_paths() -> list[str]:
    found = []
    for relative in tracked_paths():
        if not is_relevant(relative):
            continue
        candidate = PurePosixPath(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("Chemin Git non sûr")
        path = ROOT.joinpath(*candidate.parts)
        if not path.is_file() or path.is_symlink():
            raise ValueError("Entrée Git manquante ou lien symbolique: " + relative)
        if candidate.name.lower() in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise ValueError("Fichier sensible potentiel : revue nécessaire avant export: " + relative)
        found.append(relative)
    return found


def make_archive(destination: Path) -> dict:
    paths = selected_paths()
    if not any(p.startswith("projets/projet-nova/") for p in paths):
        raise RuntimeError("Sous-arborescence du projet Nova absente")
    revision = git("rev-parse", "HEAD").decode().strip()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "repository": "M0rdr3x/BenoitCantin",
        "git_checkout_sha": revision,
        "created_at_utc": timestamp,
        "scope": "Fichiers Git suivis dans le projet Nova, éléments annexes nommés Nova/sondage/boussole, rapports et dépendances partagées listées.",
        "not_included": [
            "git history object database (.git)",
            "issues/PR non matérialisées dans les fichiers",
            "conversations privées ou mémoire intégrale de ChatGPT",
            "données de production ou secrets externes",
        ],
        "files": [],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=7, allowZip64=True) as archive:
        for relative in paths:
            data = (ROOT / relative).read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            archive.writestr("SOURCE_GITHUB/" + relative, data)
            manifest["files"].append({"path": relative, "bytes": len(data), "sha256": digest})
        # Un résumé interprété de nos échanges, distinct des fichiers du projet.
        note = ROOT / "docs/archives/PROJET_NOVA_CONTEXTE_2026-11-20.md"
        if note.is_file():
            archive.writestr("CONTEXTE_DES_CONVERSATIONS/NOTE_DE_CONTEXTE.md", note.read_bytes())
        history = git(
            "log", "--all", "--date=iso-strict", "--pretty=format:%h %aI %s",
            "--", "projets/projet-nova", "docs/nova-sondages",
        ).decode("utf-8", "replace")
        archive.writestr("HISTORIQUE_COMMITS_NOVA.txt", history + "\n")
        manifest["file_count"] = len(manifest["files"])
        manifest["source_bytes_total"] = sum(f["bytes"] for f in manifest["files"])
        archive.writestr("MANIFESTE_SHA256.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        intro = (
            "# Archive complète des éléments identifiés Projet Nova\n\n"
            f"Source : M0rdr3x/BenoitCantin — checkout Git \`{revision}\`\n\n"
            f"Fichiers Git préservés : {len(paths)} (total source {manifest['source_bytes_total']} octets).\n\n"
            "Les chemins sont sous SOURCE_GITHUB/; l'inventaire et les empreintes SHA-256 "
            "sont dans MANIFESTE_SHA256.json. Les notes de contexte résument seulement les "
            "éléments des conversations accessibles ici et ne sont pas une sauvegarde "
            "de la mémoire ChatGPT. L'historique des commits est un index textuel; "
            "les objets Git, les issues et les services externes ne sont pas exportés.\n\n"
            "La mise en retrait de Nova ne supprime aucune page ni service externe "
            "et n'homologue pas une remise en production.\n"
        ).replace("\\`", "`")
        archive.writestr("LISEZ_MOI_AVANT_REPRISE.md", intro)
    return {"path": str(destination), "file_count": len(paths), "checkout_sha": revision,
            "source_bytes": manifest["source_bytes_total"],
            "zip_bytes": destination.stat().st_size}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Chemin final du fichier .zip")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    candidates = selected_paths()
    expected = [
        "projets/projet-nova/index.html",
        "projets/projet-nova/data/registre-donnees-services-nova-sinjira.json",
        "docs/nova-sondages/reception-sondage-boussole-2026-11-08.json",
        "docs/archives/PROJET_NOVA_CONTEXTE_2026-11-20.md",
    ]
    absent = [p for p in expected if p not in candidates]
    if absent:
        print("Fichiers Nova obligatoires absents: " + ", ".join(absent), file=sys.stderr)
        return 2
    if len(candidates) < 300:
        print(f"Inventaire suspect : seulement {len(candidates)} fichiers", file=sys.stderr)
        return 2
    if args.self_test:
        print(json.dumps({"self_test": "OK", "file_count": len(candidates),
                          "examples": expected}, ensure_ascii=False))
        return 0
    if not args.output:
        parser.error("--output est requis sans --self-test")
    result = make_archive(args.output)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
