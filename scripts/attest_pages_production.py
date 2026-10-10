#!/usr/bin/env python3
"""Attestation read-only et fail-closed AVANT tout déploiement GitHub Pages SINJIRA.

Contrôle à deux reprises (préparation puis juste avant deploy-pages) le HEAD
courant, la source de publication Pages, le CNAME et HTTPS. Aucun write API.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Callable
from urllib.request import Request, urlopen

REPOSITORY = "M0rdr3x/BenoitCantin"
PAGES_URL = "https://api.github.com/repos/M0rdr3x/BenoitCantin/pages"
MAIN_REF_URL = "https://api.github.com/repos/M0rdr3x/BenoitCantin/git/ref/heads/main"
SHA_RE = re.compile(r"[0-9a-f]{40}\Z")


def attest(repo: str, ref: str, dispatched: str, expected: str,
           get_json: Callable[[str], object]) -> list[str]:
    """Comparer les états approuvés, sans prétendre qu'un dry-run est un publish."""
    errors: list[str] = []
    if repo != REPOSITORY:
        return ["Dépôt inattendu — refus du déploiement"]
    if ref != "refs/heads/main":
        return ["Déploiement uniquement depuis refs/heads/main"]
    if not SHA_RE.fullmatch(expected):
        return ["SHA approuvé invalide ou incomplet"]
    if not SHA_RE.fullmatch(dispatched):
        return ["SHA GitHub Actions invalide ou incomplet"]
    if dispatched != expected:
        return ["Commit du workflow différent du commit approuvé"]
    # Ces endpoints sont des constantes de code, pas des URL contrôlées par l'utilisateur.
    try:
        pages = get_json(PAGES_URL)
        current = get_json(MAIN_REF_URL)
    except Exception as exc:
        return [f"Attestation API GitHub inaccessible ({type(exc).__name__})"]
    if not isinstance(pages, dict) or not isinstance(current, dict):
        return ["Réponses API GitHub malformées"]
    if pages.get("build_type") != "workflow":
        errors.append("Source Pages différente de GitHub Actions")
    if pages.get("cname") != "www.benoitcantin.com":
        errors.append("Domaine personnalisé Pages inattendu")
    if pages.get("https_enforced") is not True:
        errors.append("HTTPS non imposé dans la configuration Pages")
    obj = current.get("object")
    if not isinstance(obj, dict) or obj.get("type") != "commit":
        errors.append("Référence main GitHub invalide")
    elif obj.get("sha") != expected:
        errors.append("main a changé depuis l'approbation du SHA — abandon du déploiement")
    if current.get("ref") != "refs/heads/main":
        errors.append("Réponse GitHub ne correspond pas à refs/heads/main")
    return errors


def github_get_json(url: str, token: str) -> object:
    if url not in {PAGES_URL, MAIN_REF_URL}:
        raise ValueError("Requête hors de l'API GitHub autorisée")
    if not token:
        raise ValueError("GitHub token absent")
    req = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "Authorization": "Bearer " + token,
        "User-Agent": "SINJIRA-Pages-ReadOnly-Attestation/1.0",
    })
    # urlopen ne suit aucune redirection en situation normale pour ces endpoints.
    # La connexion impose HTTPS et un host constant.
    import json
    with urlopen(req, timeout=12) as response:
        if response.status != 200:
            raise ValueError("GitHub API HTTP non 200")
        return json.load(response)


def self_test() -> None:
    sha = "a" * 40
    def good(url: str) -> object:
        if url == PAGES_URL:
            return {"build_type": "workflow", "cname": "www.benoitcantin.com",
                    "https_enforced": True}
        if url == MAIN_REF_URL:
            return {"ref": "refs/heads/main", "object": {"type": "commit", "sha": sha}}
        raise ValueError("Unknown URL")
    assert attest(REPOSITORY, "refs/heads/main", sha, sha, good) == []
    assert attest("another/repo", "refs/heads/main", sha, sha, good)
    assert attest(REPOSITORY, "refs/heads/draft", sha, sha, good)
    assert attest(REPOSITORY, "refs/heads/main", "x" * 40, sha, good)
    assert attest(REPOSITORY, "refs/heads/main", sha, "bad", good)
    def mutated_url(url: str, altered_url: str, alter: object) -> object:
        return alter if url == altered_url else good(url)
    bad_pages = (
        {"build_type": "legacy", "cname": "www.benoitcantin.com", "https_enforced": True},
        {"build_type": "workflow", "cname": "wrong.example", "https_enforced": True},
        {"build_type": "workflow", "cname": "www.benoitcantin.com", "https_enforced": False},
        {},
        "unexpected",
    )
    for payload in bad_pages:
        assert attest(REPOSITORY, "refs/heads/main", sha, sha,
                      lambda url, p=payload: mutated_url(url, PAGES_URL, p)), payload
    bad_refs = (
        {"ref": "refs/heads/main", "object": {"type": "commit", "sha": "b" * 40}},
        {"ref": "refs/heads/main", "object": {"type": "tag", "sha": sha}},
        {"ref": "refs/heads/other", "object": {"type": "commit", "sha": sha}},
        {},
    )
    for payload in bad_refs:
        assert attest(REPOSITORY, "refs/heads/main", sha, sha,
                      lambda url, p=payload: mutated_url(url, MAIN_REF_URL, p)), payload
    def broken(_url: str) -> object:
        raise TimeoutError("Simulated failure")
    assert attest(REPOSITORY, "refs/heads/main", sha, sha, broken)
    print("OK Pages attestation: branche, SHA immuable, API, CNAME, HTTPS et race main refusés")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    token = os.environ.get("GH_PAGES_READ_TOKEN", "")
    def get(url: str) -> object:
        return github_get_json(url, token)
    errors = attest(
        os.environ.get("GITHUB_REPOSITORY", ""),
        os.environ.get("GITHUB_REF", ""),
        os.environ.get("GITHUB_SHA", ""),
        os.environ.get("EXPECTED_SHA", ""),
        get,
    )
    if errors:
        for error in errors:
            print("ERREUR : " + error, file=sys.stderr)
        return 1
    print("OK Pages : mode workflow, domaine HTTPS et main au SHA approuvé exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
