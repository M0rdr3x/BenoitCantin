#!/usr/bin/env python3
"""Vérifier passivement la parité Edge déployée avant de déclarer une release sûre.

Lit uniquement des métadonnées Management API et des sources téléchargées
par Supabase CLI dans un workspace temporaire ; aucun appel HTTP fonctionnel
aux endpoints clients, aucun SQL, aucun POST, aucun déploiement.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import tempfile
import tomllib

PROJECT_REF = "gpvivleexywljowcqkru"
PUBLIC_NO_JWT = frozenset({
    "get-document-url",
    "send-game-report",
    "life-story-delivery",
    "nova-civic-poll",
})
JWT_REQUIRED = frozenset({
    "admin-analytics",
    "admin-console",
    "admin-license-codes",
    "admin-reports",
    "admin-sinjira-v18",
    "admin-social-v20",
    "admin-users",
    "conscience-vault",
    "delete-player-account",
    "fracture-engine-gateway",
    "get-novel-file-url",
    "life-story-export",
    "notify-account-confirmation",
    "personal-ai",
    "redeem-license-code",
    "revoke-my-contributions",
    "security-context",
    "send-player-sheet",
    "submit-character-questionnaire",
    "submit-fracture-endgame",
    "submit-game-contribution",
})
RETIRED_TOMBSTONES = frozenset({
    "admin-reader",
    "generate-sinjira-character",
    "admin-literary",
    "validate-phone-v22",
    "guardian-create-youth-v22",
    "create-youth-account",
    "sinjira-maintenance-upload-20261007",
})
MONITORED_FUNCTIONS = PUBLIC_NO_JWT | JWT_REQUIRED
EXPECTED_FUNCTIONS = MONITORED_FUNCTIONS | RETIRED_TOMBSTONES
TOMBSTONES_PATH = Path("supabase/retired-edge-tombstones.json")
REPO_ONLY_NOT_DEPLOYED = frozenset({"get-private-book-url"})
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
    if seen != EXPECTED_FUNCTIONS:
        unexpected = sorted(seen - EXPECTED_FUNCTIONS)
        missing = sorted(EXPECTED_FUNCTIONS - seen)
        errors.append(
            "Inventaire Edge changé sans revue : absentes=" + ",".join(missing)
            + " ; nouvelles=" + ",".join(unexpected)
        )
    return errors


def retired_snapshots(local: Path) -> dict[str, str]:
    """Lire le contrat de sources 410 approuvé, jamais le traiter comme code exécutable."""
    try:
        payload = json.loads(safe_text(local, TOMBSTONES_PATH))
    except (ValueError, TypeError) as exc:
        raise ValueError("Contrat des fonctions retirées absent ou illisible") from exc
    if not isinstance(payload, dict) or payload.get("contract_version") != 1:
        raise ValueError("Version du contrat des fonctions retirées non approuvée")
    expected = payload.get("functions")
    if not isinstance(expected, dict) or set(expected) != RETIRED_TOMBSTONES:
        raise ValueError("Liste des fonctions retirées non conforme au contrat")
    normalized: dict[str, str] = {}
    for slug, src in expected.items():
        if not isinstance(src, str) or len(src.encode("utf-8")) > 2048:
            raise ValueError("Source de retrait absente ou anormale : " + slug)
        source = src.replace("\r\n", "\n").rstrip("\n")
        if (
            source.count("Deno.serve(") != 1
            or not re.search(r"\bstatus\s*:\s*410\b", source)
            or "no-store" not in source
            or "fetch(" in source
            or "Deno.env" in source
        ):
            raise ValueError("Fonction retirée non fail-closed : " + slug)
        normalized[slug] = source
    return normalized


def verify_repository_contract(local: Path) -> list[str]:
    """Garantir que chaque source attendue existe et que les JWT source sont conformes."""
    errors: list[str] = []
    try:
        settings = tomllib.loads(safe_text(local, Path("supabase/config.toml")))
        funcs = settings.get("functions", {})
        if not isinstance(funcs, dict):
            return ["Configuration Edge absente"]
        expected = MONITORED_FUNCTIONS | REPO_ONLY_NOT_DEPLOYED
        if set(funcs) != expected:
            errors.append("Liste des fonctions du dépôt changée sans revue")
        for slug in sorted(expected):
            cfg = funcs.get(slug, {})
            should_verify = slug not in PUBLIC_NO_JWT
            if not isinstance(cfg, dict) or cfg.get("verify_jwt") is not should_verify:
                errors.append(slug + " : verify_jwt du dépôt affaibli ou absent")
        for slug in sorted(MONITORED_FUNCTIONS):
            safe_text(local, Path("supabase/functions") / slug / "index.ts")
        retired_snapshots(local)
    except (ValueError, TypeError, OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        errors.append("Contrat du dépôt incomplet ou illisible : " + str(exc))
    return errors


def audit(local: Path, downloaded: Path, metadata: object) -> list[str]:
    errors = validate_metadata(metadata)
    if errors:
        return errors
    try:
        tombstones = retired_snapshots(local)
    except ValueError as exc:
        return [str(exc)]
    for slug in sorted(EXPECTED_FUNCTIONS):
        rel = Path("supabase/functions") / slug / "index.ts"
        try:
            deployed = safe_text(downloaded, rel)
            canonical = tombstones[slug] if slug in RETIRED_TOMBSTONES else safe_text(local, rel)
        except ValueError as exc:
            errors.append(f"{slug} : source inaccessible ({exc})")
            continue
        if deployed != canonical:
            errors.append(f"{slug} : dérive de source Edge ou réactivation d'une fonction retirée (NO_GO)")
    return errors


def self_test() -> None:
    rows = [
        {"slug": slug, "verify_jwt": slug in (JWT_REQUIRED | RETIRED_TOMBSTONES), "status": "ACTIVE", "version": 1}
        for slug in sorted(EXPECTED_FUNCTIONS)
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
        retired_source = (
            'Deno.serve(()=>new Response("retired",'
            '{status:410,headers:{"Cache-Control":"no-store"}}));\n'
        )
        retired_contract = repo / TOMBSTONES_PATH
        retired_contract.parent.mkdir(parents=True, exist_ok=True)
        retired_contract.write_text(
            json.dumps({
                "contract_version": 1,
                "functions": {slug: retired_source for slug in RETIRED_TOMBSTONES},
            }),
            "utf-8",
        )
        for slug in RETIRED_TOMBSTONES:
            dst = remote / "supabase/functions" / slug / "index.ts"
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(retired_source, "utf-8")
        config = repo / "supabase/config.toml"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text("".join(
            "[functions." + slug + "]\nverify_jwt = "
            + ("false" if slug in PUBLIC_NO_JWT else "true") + "\n"
            for slug in sorted(MONITORED_FUNCTIONS | REPO_ONLY_NOT_DEPLOYED)
        ), "utf-8")
        assert verify_repository_contract(repo) == []
        config.write_text(config.read_text("utf-8").replace(
            "[functions.redeem-license-code]\nverify_jwt = true",
            "[functions.redeem-license-code]\nverify_jwt = false"), "utf-8")
        assert verify_repository_contract(repo), "Configuration locale JWT affaiblie acceptée"
        config.write_text(config.read_text("utf-8").replace(
            "[functions.redeem-license-code]\nverify_jwt = false",
            "[functions.redeem-license-code]\nverify_jwt = true"), "utf-8")
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
            "unexpected authenticated function": rows + [
                {"slug": "unreviewed-auth-function", "verify_jwt": True,
                 "status": "ACTIVE", "version": 1}
            ],
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
        f.write_text("const safe = true;\n", "utf-8")

        retired = sorted(RETIRED_TOMBSTONES)[0]
        stopped = remote / "supabase/functions" / retired / "index.ts"
        stopped.write_text(retired_source.replace("status:410", "status:200"), "utf-8")
        assert audit(repo, remote, rows), "Réactivation d'une fonction retirée acceptée"
        stopped.write_text(retired_source, "utf-8")
        retired_contract.write_text(
            json.dumps({"contract_version": 1, "functions": {}}), "utf-8"
        )
        assert audit(repo, remote, rows), "Inventaire des fonctions retirées altéré"
        retired_contract.unlink()
        assert audit(repo, remote, rows), "Contrat de retrait manquant accepté"

        assert validate_metadata([{"slug": "x", "verify_jwt": 0, "status": "ACTIVE",
                                   "version": 1}]), "Faux booléen accepté"
    print("OK : snapshots synthétiques, dérive, ACL JWT, liens symboliques et sources volumineuses refusés.")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--verify-repo", action="store_true")
    p.add_argument("--local-root", type=Path)
    p.add_argument("--downloaded-root", type=Path)
    p.add_argument("--metadata", type=Path)
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.verify_repo:
        problems = verify_repository_contract(Path(__file__).resolve().parents[1])
        for problem in problems:
            print("NO_GO Edge source : " + problem)
        return 1 if problems else 0
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
        "PASS : inventaire exact 32/32, JWT et sources des 25 fonctions actives, "
        "sept fonctions retirées bloquées, parité déployée confirmée."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
