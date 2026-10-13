#!/usr/bin/env python3
"""Prouver que les octets CRITIQUES servis par le domaine correspondent au SHA publié.

Exécution après le reçu SHA/run (verify_pages_live.py). Le reçu peut être à
jour alors qu'un CDN conserve des fichiers statiques périmés. Ce contrôle
compare 18 ressources réelles au checkout exact du commit approuvé.
Aucun PUT/POST, aucune donnée privée, aucun fichier de session.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE = "https://www.benoitcantin.com"
SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
MAX_BYTES = 4 * 1024 * 1024
MAX_ATTEMPTS = 4
PAUSE_SECONDS = 8
MAX_AUDIT_SECONDS = 420  # 7 minutes pour les 18 ressources, fail-closed.
# Source repository-relative path -> MIME acceptable on the real domain.
CRITICAL_RESOURCES = {
    "sw.js": ("application/javascript", "text/javascript", "application/x-javascript"),
    "manifest.webmanifest": ("application/manifest+json", "application/json"),
    "assets/css/site.css": ("text/css",),
    "assets/js/site.js": ("application/javascript", "text/javascript",
                          "application/x-javascript", "application/ecmascript",
                          "text/ecmascript"),
    "projets/projet-nova/data/boussole-partis-2026.json": ("application/json",),
    "projets/projet-nova/data/boussole-preuves-2026.json": ("application/json",),
    "projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf":
        ("application/pdf",),
    "assets/media/nova-logo.webp": ("image/webp",),
    "assets/media/sinjira-romans-banniere-2026.webp": ("image/webp",),
    "assets/media/sinjira-jeux-banniere-2026.webp": ("image/webp",),
    "assets/media/sinjira-logiciels-banniere-2026.webp": ("image/webp",),
    "projets/sinjira/logiciels/index.html": ("text/html",),
    "projets/sinjira/index.html": ("text/html",),
    "projets/sinjira/romans/index.html": ("text/html",),
    "projets/sinjira/jeux/index.html": ("text/html",),
    "projets/sinjira/sinjira.css": ("text/css",),
    "compte/bibliotheque.html": ("text/html",),
    "sitemap.xml": ("application/xml", "text/xml"),
}


@dataclass(frozen=True)
class Reply:
    status: int
    content_type: str = ""
    content_encoding: str = ""
    location: str = ""
    body: bytes = b""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def get(url: str) -> Reply:
    if not url.startswith(BASE + "/") or url[len(BASE) + 1:] not in CRITICAL_RESOURCES:
        raise ValueError("Chemin HTTP non approuvé")
    opener = build_opener(NoRedirect)
    request = Request(url, headers={
        "User-Agent": "SINJIRA-Pages-Static-Integrity/1.0",
        "Cache-Control": "no-cache, no-store",
        "Pragma": "no-cache",
        "Accept-Encoding": "identity",
        "Accept": "*/*",
    })
    try:
        resp = opener.open(request, timeout=12)
    except HTTPError as exc:
        return Reply(exc.code, exc.headers.get("Content-Type", ""),
                     exc.headers.get("Content-Encoding", ""),
                     exc.headers.get("Location", ""))
    with resp:
        if resp.geturl() != url:
            raise ValueError("Redirection interdite")
        return Reply(resp.status, resp.headers.get("Content-Type", ""),
                     resp.headers.get("Content-Encoding", ""),
                     resp.headers.get("Location", ""),
                     resp.read(MAX_BYTES + 1))


def attest_committed_bytes(root: Path, sha: str) -> list[str]:
    """Empêcher qu'un fichier modifié après checkout usurpe le SHA approuvé.

    La référence HEAD seule ne garantit pas que le worktree est intact.
    Git cat-file lit les blobs directement depuis l'objet du commit.
    """
    if not SHA_PATTERN.fullmatch(sha):
        return ["SHA Git approuvé malformé"]
    errors: list[str] = []
    for relative in CRITICAL_RESOURCES:
        file = root / relative
        if not file.is_file() or file.is_symlink():
            errors.append(f"Source Git critique absente ou symbolique: {relative}")
            continue
        try:
            result = subprocess.run(
                ["git", "-C", str(root), "show", f"{sha}:{relative}"],
                capture_output=True, timeout=12, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            errors.append(f"Objet Git critique non vérifiable: {relative}")
            continue
        if result.returncode != 0:
            errors.append(f"Fichier critique absent du commit approuvé: {relative}")
            continue
        if len(result.stdout) > MAX_BYTES:
            errors.append(f"Fichier critique Git trop volumineux: {relative}")
            continue
        try:
            actual = file.read_bytes()
        except OSError:
            errors.append(f"Source critique Git illisible: {relative}")
            continue
        if hashlib.sha256(actual).digest() != hashlib.sha256(result.stdout).digest():
            errors.append(f"Worktree différent du blob Git approuvé: {relative}")
    return errors


def audit(root: Path, expected_sha: str, actual_sha: str,
          getter: Callable[[str], Reply], attempts: int = MAX_ATTEMPTS,
          pause: Callable[[float], None] = time.sleep,
          clock: Callable[[], float] = time.monotonic,
          budget_seconds: float = MAX_AUDIT_SECONDS) -> list[str]:
    if not SHA_PATTERN.fullmatch(expected_sha) or actual_sha != expected_sha:
        return ["Checkout Git différent du SHA approuvé ou SHA malformé"]
    if not 1 <= attempts <= MAX_ATTEMPTS:
        return ["Nombre de tentatives non approuvé"]
    if not 0 < budget_seconds <= MAX_AUDIT_SECONDS:
        return ["Budget global CDN invalide"]
    deadline = clock() + budget_seconds
    if not root.is_dir() or root.is_symlink():
        return ["Checkout des sources invalide"]
    errors: list[str] = []
    expected: dict[str, bytes] = {}
    for relative in CRITICAL_RESOURCES:
        local = root / relative
        if (not local.is_file() or local.is_symlink()
                or any(part.is_symlink() for part in local.parents if part != root)):
            errors.append(f"Source critique absente ou symbolique: {relative}")
            continue
        try:
            size = local.stat().st_size
            if size > MAX_BYTES:
                errors.append(f"Source critique trop volumineuse pour contrôle: {relative}")
                continue
            expected[relative] = hashlib.sha256(local.read_bytes()).digest()
        except OSError:
            errors.append(f"Source critique illisible: {relative}")
    if errors:
        return errors

    def expired(relative: str) -> list[str]:
        # Ne jamais prétendre que les chemins restants ont été contrôlés.
        return errors + [
            f"Budget global CDN épuisé: {relative} non prouvé "
            f"({budget_seconds:g} secondes maximales)"
        ]

    for relative, expected_digest in expected.items():
        if clock() >= deadline:
            return expired(relative)
        url = BASE + "/" + relative
        last = "aucune réponse"
        for n in range(attempts):
            if clock() >= deadline:
                return expired(relative)
            try:
                reply = getter(url)
            except (URLError, OSError, TimeoutError, ValueError) as exc:
                last = "erreur réseau " + type(exc).__name__
            else:
                if clock() >= deadline:
                    return expired(relative)
                if reply.location or reply.status in {301, 302, 303, 307, 308}:
                    errors.append(f"Ressource critique redirigée: {relative}")
                    break
                if reply.status == 200:
                    mime = reply.content_type.split(";", 1)[0].lower().strip()
                    if mime not in CRITICAL_RESOURCES[relative]:
                        errors.append(f"MIME critique incorrect: {relative}")
                        break
                    if reply.content_encoding.lower().strip() not in {"", "identity"}:
                        errors.append(f"Encodage critique inattendu: {relative}")
                        break
                    if len(reply.body) > MAX_BYTES:
                        errors.append(f"Réponse critique trop volumineuse: {relative}")
                        break
                    if hashlib.sha256(reply.body).digest() == expected_digest:
                        break
                    last = "octets différents de la révision approuvée"
                else:
                    last = "HTTP " + str(reply.status)
            if n + 1 == attempts:
                errors.append(
                    f"Ressource critique non conforme après {attempts} tentatives: "
                    f"{relative} ({last})"
                )
            else:
                remaining = deadline - clock()
                if remaining <= 0:
                    return expired(relative)
                pause(min(PAUSE_SECONDS, remaining))
    if clock() >= deadline:
        return expired("fin des vérifications CDN")
    return errors


def self_test() -> None:
    sha = "a" * 40
    with __import__("tempfile").TemporaryDirectory() as directory:
        root = Path(directory)
        content: dict[str, bytes] = {}
        for rel in CRITICAL_RESOURCES:
            f = root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            data = ("version:" + rel).encode("utf-8")
            f.write_bytes(data)
            content[rel] = data

        def good(url: str) -> Reply:
            rel = url[len(BASE) + 1:]
            return Reply(200, CRITICAL_RESOURCES[rel][0], body=content[rel])

        assert not audit(root, sha, sha, good), "Artefact sain incorrectement refusé"
        assert audit(root, "b" * 40, sha, good), "SHA inadéquat accepté"
        assert audit(root, "bad", sha, good), "SHA tronqué accepté"

        def stale(url: str) -> Reply:
            if url.endswith("sw.js"):
                return Reply(200, CRITICAL_RESOURCES["sw.js"][0],
                             body=b"ancien service worker")
            return good(url)

        assert any("sw.js" in e for e in audit(root, sha, sha, stale,
                    attempts=2, pause=lambda _: None)), "Ancien SW accepté"
        def altered_json(url: str) -> Reply:
            if "boussole-preuves-2026.json" in url:
                return Reply(200, "application/json", body=b'{"obsolete":true}')
            return good(url)
        assert any("boussole-preuves-2026.json" in e for e in audit(
            root, sha, sha, altered_json, attempts=2, pause=lambda _: None)), (
                "Données politiques obsolètes acceptées"
        )

        # Même avec un reçu SHA/run actuel, une page, un style ou un sitemap
        # issu d'un ancien commit ne doit jamais être certifié conforme.
        for protected in (
            "projets/sinjira/index.html",
            "projets/sinjira/romans/index.html",
            "projets/sinjira/jeux/index.html",
            "projets/sinjira/logiciels/index.html",
            "projets/sinjira/sinjira.css",
            "compte/bibliotheque.html",
            "sitemap.xml",
        ):
            def outdated(url: str, protected_path: str = protected) -> Reply:
                if url == BASE + "/" + protected_path:
                    return Reply(200, CRITICAL_RESOURCES[protected_path][0],
                                 body=b"ancienne version CDN")
                return good(url)
            assert any(protected in error for error in audit(
                root, sha, sha, outdated, attempts=2, pause=lambda _: None
            )), f"Fichier SINJIRA obsolète accepté: {protected}"

        calls: dict[str, int] = {}
        delays: list[int] = []
        def eventually(url: str) -> Reply:
            calls[url] = calls.get(url, 0) + 1
            if url.endswith("sw.js") and calls[url] < 3:
                return stale(url)
            return good(url)
        assert not audit(root, sha, sha, eventually, attempts=3,
                         pause=delays.append), "Fichier actualisé tardivement refusé"
        assert delays == [PAUSE_SECONDS] * 2, "Attente bornée non respectée"

        # Le budget est global, non 18 budgets indépendants. Refuser aussi
        # une réponse valide reçue APRÈS la date limite.
        tick = [0.0]
        def too_late(url: str) -> Reply:
            tick[0] += 3.0
            return good(url)
        assert any("Budget global CDN" in e for e in audit(
            root, sha, sha, too_late, clock=lambda: tick[0],
            budget_seconds=2.0)), "Réponse tardive après deadline acceptée"

        tick = [0.0]
        def stuck(_url: str) -> Reply:
            return Reply(503, "text/html")
        def advance(seconds: float) -> None:
            tick[0] += seconds
        assert any("Budget global CDN" in e for e in audit(
            root, sha, sha, stuck, attempts=4, pause=advance,
            clock=lambda: tick[0], budget_seconds=9.0)), (
                "Propagation bloquée au-delà du budget acceptée"
            )
        assert audit(root, sha, sha, good, budget_seconds=-1.0), (
            "Budget négatif accepté"
        )
        assert audit(root, sha, sha, good,
                     budget_seconds=MAX_AUDIT_SECONDS + 1), (
            "Budget sans limite accepté"
        )

        for name, bad in (
            ("MIME", Reply(200, "text/html", body=content["sw.js"])),
            ("redirection", Reply(302, location="https://other.example/")),
            ("encodage", Reply(200, CRITICAL_RESOURCES["sw.js"][0],
                             content_encoding="gzip", body=content["sw.js"])),
            ("volume", Reply(200, CRITICAL_RESOURCES["sw.js"][0],
                            body=b"x" * (MAX_BYTES + 1))),
        ):
            def broken(url: str) -> Reply:
                return bad if url.endswith("sw.js") else good(url)
            assert any("sw.js" in e for e in audit(
                root, sha, sha, broken, attempts=1)), f"{name} incorrect accepté"

        path = root / "assets/css/site.css"
        path.unlink()
        assert any("site.css" in e for e in audit(root, sha, sha, good)), (
            "Fichier local absent accepté"
        )
        path.symlink_to(root / "sw.js")
        assert any("site.css" in e for e in audit(root, sha, sha, good)), (
            "Fichier source symbolique accepté"
        )

    # Comparaison explicite des blobs COMMIT versus worktree : SHA HEAD seul
    # ne détecterait pas une modification locale introduite après checkout.
    with __import__("tempfile").TemporaryDirectory() as directory:
        root = Path(directory)
        for rel in CRITICAL_RESOURCES:
            file = root / rel
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(("tracked:" + rel).encode("utf-8"))
        def git(*args: str) -> str:
            run = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True, text=True, timeout=12, check=True
            )
            return run.stdout.strip()
        git("init", "-q")
        git("add", ".")
        git("-c", "user.name=SINJIRA Test",
            "-c", "user.email=ci@example.invalid",
            "commit", "-qm", "fixture snapshot")
        committed = git("rev-parse", "HEAD")
        assert not attest_committed_bytes(root, committed), (
            attest_committed_bytes(root, committed)
        )
        tampered = root / "sw.js"
        tampered.write_text("worktree changed after commit", "utf-8")
        assert any("sw.js" in error and "Worktree" in error
                   for error in attest_committed_bytes(root, committed)), (
            "Modification du worktree après checkout non détectée"
        )
        tampered.write_bytes(b"tracked:sw.js")
        missing = root / "assets/js/site.js"
        missing.unlink()
        assert any("site.js" in error for error in attest_committed_bytes(
            root, committed)), "Source Git supprimée après checkout acceptée"
    print(f"OK intégrité HTTP : {len(CRITICAL_RESOURCES)} ressources, SHA Git, "
          "MIME, encodage, octets et propagation bornée")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--check", action="store_true",
                      help="18 ressources HTTPS avec budget global de 7 minutes, après reçu SHA/run")
    parser.add_argument("--expected-sha")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.expected_sha:
        parser.error("--expected-sha est obligatoire")
    try:
        actual = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=8
        ).strip()
    except (OSError, subprocess.SubprocessError):
        print("ERREUR : commit local non vérifiable", file=sys.stderr)
        return 1
    repository = Path(__file__).resolve().parents[1]
    # Compare les octets de chaque source au blob de l'objet Git approuvé,
    # avant tout accès réseau au CDN : le SHA HEAD seul est insuffisant.
    errors = attest_committed_bytes(repository, args.expected_sha)
    if errors:
        for error in errors:
            print("ECHEC checkout Git : " + error, file=sys.stderr)
        return 1
    issues = audit(repository, args.expected_sha, actual, get)
    if issues:
        for issue in issues:
            print("ECHEC HTTP intégrité : " + issue, file=sys.stderr)
        return 1
    print(f"OK : {len(CRITICAL_RESOURCES)} fichiers du CDN identiques "
          "octet par octet au SHA Git approuvé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
