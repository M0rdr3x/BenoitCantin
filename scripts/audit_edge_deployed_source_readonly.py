#!/usr/bin/env python3
"""Vérifier passivement la parité Edge déployée avant de déclarer une release sûre.

Lit uniquement des métadonnées Management API et des sources téléchargées
par Supabase CLI dans un workspace temporaire ; aucun appel HTTP fonctionnel
aux endpoints clients, aucun SQL, aucun POST, aucun déploiement.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

PROJECT_REF = "gpvivleexywljowcqkru"
PUBLIC_NO_JWT = frozenset({
    "get-document-url",
    "send-game-report",
    "life-story-delivery",
    "nova-civic-poll",
})
JWT_REQUIRED = frozenset({
    "revoke-my-contributions",
    "redeem-license-code",
})
MONITORED_FUNCTIONS = PUBLIC_NO_JWT | JWT_REQUIRED
LIMIT = 250_000
METADATA_LIMIT = 500_000


def safe_text(root: Path, rel: Path) -> str:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Répertoire source absent ou lien symbolique")
    current = root
    for part in rel.parts:
        if part in ("", ".", ".."):
            raise ValueError("Composant de chemin interdit")
        current = current / part
        if current.is_symlink():
            raise ValueError("Lien symbolique refusé")
    if not current.is_file() or current.stat().st_size > LIMIT:
        raise ValueError("Source absente ou anormalement volumineuse")
    try:
        return current.read_text("utf-8", errors="strict").replace("\r\n", "\n").rstrip("\n")
    except (OSError, UnicodeError) as exc:
        raise ValueError("Source illisible") from exc


def read_metadata(path: Path) -> object:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > METADATA_LIMIT:
        raise ValueError("Inventaire déployé absent ou invalide")
    try:
        return json.loads(path.read_text("utf-8", errors="strict"))
    except (ValueError, UnicodeError, OSError) as exc:
        raise ValueError("Inventaire déployé illisible") from exc


def validate_metadata(payload: object) -> list[str]:
    errors: list[str] = []
    if isinstance(payload, dict):
        payload = payload.get("functions")
    if not isinstance(payload, list) or not (4 <= len(payload) <= 128):
        return ["Inventaire Edge absent ou anormal"]
    seen: set[str] = set()
    no_jwt: set[str] = set()
    for row in payload:
        if not isinstance(row, dict):
            return ["Ligne de fonction non conforme"]
        slug = row.get("slug")
        if not isinstance(slug, str) or not slug or not slug.replace("-", "").isalnum():
            return ["Slug de fonction malformé"]
        if slug in seen:
            errors.append("Slug Edge dupliqué : " + slug)
        seen.add(slug)
        if row.get("status") != "ACTIVE":
            errors.append("Fonction non active : " + slug)
        if type(row.get("verify_jwt")) is not bool:
            errors.append("Statut de JWT non booléen : " + slug)
        elif row["verify_jwt"] is False:
            no_jwt.add(slug)
        ver = row.get("version")
        if type(ver) is not int or ver < 1:
            errors.append("Version Edge absente ou invalide : " + slug)
    if no_jwt != PUBLIC_NO_JWT:
        errors.append(
            "Exceptions JWT modifiées : attendues " + ",".join(sorted(PUBLIC_NO_JWT))
            + " ; constatées " + ",".join(sorted(no_jwt))
        )
    if not MONITORED_FUNCTIONS <= seen:
        errors.append("Fonction Edge suivie absente de l'inventaire")
    return errors


def audit(local: Path, downloaded: Path, metadata: object) -> list[str]:
    errors = validate_metadata(metadata)
    if errors:
        return errors
    for slug in sorted(MONITORED_FUNCTIONS):
        rel = Path("supabase/functions") / slug / "index.ts"
        try:
            deployed = safe_text(downloaded, rel)
            canonical = safe_text(local, rel)
        except ValueError as exc:
            errors.append(f"{slug} : source inaccessible ({exc})")
            continue
        if deployed != canonical:
            errors.append(f"{slug} : dérive de code déployé (NO_GO)")
    return errors


def self_test() -> None:
    rows = [
        {"slug": slug, "verify_jwt": slug in JWT_REQUIRED, "status": "ACTIVE", "version": 1}
        for slug in sorted(MONITORED_FUNCTIONS)
    ]
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        repo = base / "repo"
        remote = base / "remote"
        for root in (repo, remote):
            for slug in MONITORED_FUNCTIONS:
                dst = root / "supabase/functions" / slug / "index.ts"
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text("const safe = true;\n", "utf-8")
        assert audit(repo, remote, rows) == []
        mutants: dict[str, object] = {
            "missing JWT flag": [{k: v for k, v in row.items() if k != "verify_jwt"}
                                 if i == 0 else row for i, row in enumerate(rows)],
            "unexpected anonymous function": rows + [
                {"slug": "unknown", "verify_jwt": False, "status": "ACTIVE", "version": 1}],
            "inactive function": [{**row, "status": "DELETED"} if i == 0 else row
                                  for i, row in enumerate(rows)],
            "duplicate slug": rows + [rows[0]],
            "missing function": rows[:-1],
            "wrong metadata": {"unexpected": []},
            "authenticated function exposed without JWT": [
                {**row, "verify_jwt": False}
                if row["slug"] == "redeem-license-code" else row for row in rows
            ],
        }
        for name, payload in mutants.items():
            assert audit(repo, remote, payload), "Métadonnées non fiables acceptées : " + name

        first = sorted(MONITORED_FUNCTIONS)[0]
        f = remote / "supabase/functions" / first / "index.ts"
        f.write_text("const safe = false;\n", "utf-8")
        assert audit(repo, remote, rows), "Dérive de source Edge acceptée"
        f.write_text("const safe = true;\n", "utf-8")

        f.unlink()
        f.symlink_to(base / "outside")
        assert audit(repo, remote, rows), "Symlink de source Edge accepté"
        f.unlink()
        f.write_text("const safe = true;\n", "utf-8")
        f.write_text("A" * (LIMIT + 1), "utf-8")
        assert audit(repo, remote, rows), "Source Edge surdimensionnée acceptée"

        assert validate_metadata([{"slug": "x", "verify_jwt": 0, "status": "ACTIVE",
                                   "version": 1}]), "Faux booléen accepté"
    print("OK : snapshots synthétiques, dérive, ACL JWT, liens symboliques et sources volumineuses refusés.")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--local-root", type=Path)
    p.add_argument("--downloaded-root", type=Path)
    p.add_argument("--metadata", type=Path)
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not (args.local_root and args.downloaded_root and args.metadata):
        p.error("--local-root, --downloaded-root et --metadata sont obligatoires")
    try:
        issues = audit(args.local_root, args.downloaded_root, read_metadata(args.metadata))
    except ValueError as exc:
        issues = [str(exc)]
    if issues:
        for issue in issues:
            print("NO_GO Edge : " + issue)
        return 1
    print(
        "PASS : quatre exceptions JWT inchangées, six fonctions surveillées, fonctions actives "
        "et sources déployées correspondant au code approuvé."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
