#!/usr/bin/env python3
"""Contrat fail-closed de provenance du lockfile Netlify CLI staging.

Le lockfile réel est issu d'un npm --package-lock-only dans GitHub Actions,
sans secrets. Aucune installation ni aucun réseau n'est utilisé ici.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools/netlify-cli/package.json"
LOCKFILE = ROOT / "tools/netlify-cli/package-lock.json"

VERSION = "27.19.0"
NAME = "sinjira-netlify-cli-toolchain"
EXPECTED_SHA256 = "6a21a830c8f3adc799db04bfca9a8c09ea6d864b6903e4f333c7abfdd9535bd4"
EXPECTED_PACKAGE_COUNT = 1015
CLI_SRI = "sha512-tsJuEmTWH1rbg7JSKYUwCfO4jQtd++VDVdH5HdOiZTteMPFWqWU2y/SHD3hFjxlHhdMWILST6eymwTY3HUCTOg=="
SRI = re.compile(r"sha512-[A-Za-z0-9+/]+={0,2}\Z")


def inspect(manifest_bytes: bytes, lock_bytes: bytes, *, check_snapshot: bool = True) -> list[str]:
    issues: list[str] = []
    if check_snapshot and hashlib.sha256(lock_bytes).hexdigest() != EXPECTED_SHA256:
        issues.append("SHA-256 du lockfile différent de la version revue")
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        lock = json.loads(lock_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        return issues + [f"JSON manifest/lockfile invalide: {exc}"]
    if not isinstance(manifest, dict) or not isinstance(lock, dict):
        return issues + ["manifest/lockfile doit être un objet JSON"]
    expected = {"name": NAME, "version": "1.0.0", "private": True, "dependencies": {"netlify-cli": VERSION}}
    if manifest != expected:
        issues.append("manifest npm non conforme: dépendance directe et champs exacts requis")
    if lock.get("name") != NAME or lock.get("version") != "1.0.0" or lock.get("lockfileVersion") != 3:
        issues.append("identité ou version du lockfile inattendue")
    packages = lock.get("packages")
    if not isinstance(packages, dict):
        return issues + ["packages manquants ou invalides"]
    if len(packages) - 1 != EXPECTED_PACKAGE_COUNT:
        issues.append(f"nombre de dépendances anormal: {len(packages)-1} au lieu de {EXPECTED_PACKAGE_COUNT}")
    root = packages.get("")
    if not isinstance(root, dict) or root != {
        "name": NAME, "version": "1.0.0", "dependencies": {"netlify-cli": VERSION}
    }:
        issues.append("résolution des dépendances racines différente du manifest approuvé")
    cli = packages.get("node_modules/netlify-cli")
    if not isinstance(cli, dict) or cli.get("version") != VERSION or cli.get("integrity") != CLI_SRI:
        issues.append("paquet Netlify CLI non conforme à l'identité/l'empreinte approuvées")
    for path, entry in packages.items():
        if not path:
            continue
        if not isinstance(entry, dict) or entry.get("link"):
            issues.append(f"{path}: paquet invalide ou lien local interdit")
            continue
        if not path.startswith("node_modules/") or ".." in path.split("/"):
            issues.append(f"{path}: chemin npm inattendu")
        if not isinstance(entry.get("version"), str) or not entry["version"]:
            issues.append(f"{path}: version exacte absente")
        if not isinstance(entry.get("integrity"), str) or not SRI.fullmatch(entry["integrity"]):
            issues.append(f"{path}: empreinte sha512 SRI absente ou invalide")
        resolved = entry.get("resolved")
        if not isinstance(resolved, str):
            issues.append(f"{path}: URL tarball résolue manquante")
            continue
        try:
            u = urlsplit(resolved)
            allowed = (
                u.scheme == "https" and u.netloc == "registry.npmjs.org"
                and u.path.endswith(".tgz") and u.path.startswith("/")
                and not u.query and not u.fragment
            )
        except ValueError:
            allowed = False
        if not allowed:
            issues.append(f"{path}: hôte, schéma ou ressource tarball non approuvés")
    return issues


def self_test(manifest: bytes, lock: bytes) -> None:
    if problems := inspect(manifest, lock):
        raise AssertionError("référence invalide: " + "; ".join(problems[:5]))
    original = json.loads(lock)
    mutants: dict[str, tuple[bytes, bytes]] = {}
    def changed(label: str, update) -> None:
        data = json.loads(lock)
        update(data)
        mutants[label] = (manifest, json.dumps(data).encode())

    changed("version CLI", lambda d: d["packages"]["node_modules/netlify-cli"].__setitem__("version", "27.19.1"))
    changed("SRI CLI", lambda d: d["packages"]["node_modules/netlify-cli"].__setitem__("integrity", "sha512-fausse"))
    changed("URL exfiltration", lambda d: d["packages"]["node_modules/netlify-cli"].__setitem__("resolved", "https://evil.example/a.tgz"))
    changed("HTTP", lambda d: d["packages"]["node_modules/netlify-cli"].__setitem__("resolved", "http://registry.npmjs.org/a.tgz"))
    changed("SRI supprimée", lambda d: d["packages"]["node_modules/netlify-cli"].pop("integrity"))
    changed("paquet supprimé", lambda d: d["packages"].pop("node_modules/netlify-cli"))
    changed("symlink local", lambda d: d["packages"]["node_modules/netlify-cli"].__setitem__("link", True))
    changed("root modifiée", lambda d: d["packages"][""].__setitem__("version", "2.0.0"))
    changed("lockfile v2", lambda d: d.__setitem__("lockfileVersion", 2))
    changed("dépendance directe mobile", lambda d: d["packages"][""]["dependencies"].__setitem__("netlify-cli", "*"))
    mutants["manifest mobile"] = (
        manifest.replace(b'"27.19.0"', b'"*"'), lock
    )
    mutants["manifest autre paquet"] = (
        manifest.replace(b'"netlify-cli"', b'"other-cli"'), lock
    )
    for label, (m, l) in mutants.items():
        if (m, l) == (manifest, lock) or not inspect(m, l, check_snapshot=False):
            raise AssertionError("mutation non détectée: " + label)
    print(f"OK: lockfile immuable, {EXPECTED_PACKAGE_COUNT} paquets SRI et {len(mutants)} mutants refusés.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    manifest = MANIFEST.read_bytes()
    lock = LOCKFILE.read_bytes()
    if args.self_test:
        self_test(manifest, lock)
        return 0
    findings = inspect(manifest, lock)
    for finding in findings:
        print("ERREUR:", finding)
    if findings:
        return 1
    print(f"OK: Netlify CLI {VERSION}, {EXPECTED_PACKAGE_COUNT} dépendances verrouillées et SHA-256 validé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
