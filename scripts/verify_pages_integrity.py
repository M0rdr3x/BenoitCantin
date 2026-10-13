#!/usr/bin/env python3
"""Prouver que les octets CRITIQUES servis par le domaine correspondent au SHA publié.

Exécution après le reçu SHA/run (verify_pages_live.py). Le reçu peut être à
jour alors qu'un CDN conserve des fichiers statiques périmés. Ce contrôle
compare 8 ressources réelles au checkout exact du commit approuvé.
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


def audit(root: Path, expected_sha: str, actual_sha: str,
          getter: Callable[[str], Reply], attempts: int = MAX_ATTEMPTS,
          pause: Callable[[int], None] = time.sleep) -> list[str]:
    if not SHA_PATTERN.fullmatch(expected_sha) or actual_sha != expected_sha:
        return ["Checkout Git différent du SHA approuvé ou SHA malformé"]
    if not 1 <= attempts <= MAX_ATTEMPTS:
        return ["Nombre de tentatives non approuvé"]
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

    for relative, expected_digest in expected.items():
        url = BASE + "/" + relative
        last = "aucune réponse"
        for n in range(attempts):
            try:
                reply = getter(url)
            except (URLError, OSError, TimeoutError, ValueError) as exc:
                last = "erreur réseau " + type(exc).__name__
            else:
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
                pause(PAUSE_SECONDS)
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
    print(f"OK intégrité HTTP : {len(CRITICAL_RESOURCES)} ressources, SHA Git, "
          "MIME, encodage, octets et propagation bornée")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--check", action="store_true",
                      help="8 GET HTTPS read-only, après la preuve de reçu SHA/run")
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
    issues = audit(Path(__file__).resolve().parents[1],
                   args.expected_sha, actual, get)
    if issues:
        for issue in issues:
            print("ECHEC HTTP intégrité : " + issue, file=sys.stderr)
        return 1
    print(f"OK : {len(CRITICAL_RESOURCES)} fichiers du CDN identiques "
          "octet par octet au SHA Git approuvé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
