#!/usr/bin/env python3
"""Qualifier les conflits native Git entre main et la release candidate.

Les conflits portant SEULEMENT sur script.js?v=... sont des divergences
techniques mais restent de VRAIS conflits Git. Ne jamais forcer le merge.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "refs/remotes/origin/main"
RELEASE = "refs/remotes/origin/a1/web-release-transparency"
NOVA_PAGE = re.compile(r"^projets/projet-nova/[^/]+\.html$")
SCRIPT_SRC = re.compile(rb'(src=["\']script\.js\?v=)([0-9A-Za-z.\-_]+)(["\'])')
EXPECTED_RELEASE_CACHE = b"26.2.0"


def git(*args: str, allowed: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, check=False
    )
    if result.returncode not in allowed:
        raise RuntimeError(
            f"git {' '.join(args)} ({result.returncode}): "
            + result.stderr.decode("utf-8", "replace")[:380]
        )
    return result


def cache_only_nova_conflict(path: str, main: bytes, candidate: bytes) -> bool:
    """Strictement identiques après neutralisation du seul cache JS Nova.

    Ne couvre ni le contenu politique, ni le code de compte, ni les PDF.
    """
    if not NOVA_PAGE.fullmatch(path):
        return False
    a, b = SCRIPT_SRC.findall(main), SCRIPT_SRC.findall(candidate)
    if len(a) != 1 or len(b) != 1:
        return False
    if a[0][1] == b[0][1] or b[0][1] != EXPECTED_RELEASE_CACHE:
        return False
    ma = SCRIPT_SRC.sub(rb"\g<1>RELEASE_VERSION\g<3>", main)
    mb = SCRIPT_SRC.sub(rb"\g<1>RELEASE_VERSION\g<3>", candidate)
    return ma == mb


def classify(paths: list[str], main_ref: str, release_ref: str) -> tuple[list[str], list[str]]:
    cache: list[str] = []
    substantive: list[str] = []
    for path in sorted(set(paths)):
        if not NOVA_PAGE.fullmatch(path):
            substantive.append(path)
            continue
        main = git("show", f"{main_ref}:{path}", allowed=(0, 128))
        release = git("show", f"{release_ref}:{path}", allowed=(0, 128))
        if main.returncode or release.returncode:
            substantive.append(path)
        elif cache_only_nova_conflict(path, main.stdout, release.stdout):
            cache.append(path)
        else:
            substantive.append(path)
    return cache, substantive


def audit() -> list[str]:
    # L'audit natif échoue également ailleurs dans la CI; ce rapport n'est
    # qu'une catégorisation en lecture seule et ne peut autoriser la fusion.
    main = git("rev-parse", MAIN).stdout.decode().strip()
    release = git("rev-parse", RELEASE).stdout.decode().strip()
    merge = git("merge-tree", "--write-tree", "--name-only", main, release,
                allowed=(0, 1))
    output = merge.stdout.decode("utf-8", "replace")
    paths = [
        line.split("Merge conflict in ", 1)[1]
        for line in output.splitlines()
        if "Merge conflict in " in line
    ]
    cache, substantive = classify(paths, main, release)
    if len(cache) + len(substantive) != len(set(paths)):
        raise RuntimeError("Incohérence du classement des chemins conflictuels")
    report = [
        "## Qualification des conflits Git #449 (lecture seule)",
        f"- Conflits natifs du moteur Git : **{len(paths)}**",
        f"- Conflits HTML Projet Nova uniquement sur la version du script : **{len(cache)}**",
        f"- Autres conflits exigeant revue : **{len(substantive)}**",
        "",
        "**Important : les deux catégories restent bloquantes.** "
        "La qualification ne résout pas la fusion et ne valide aucun déploiement.",
        "",
        "### Versions de cache uniquement (contenu HTML autrement identique)",
        *[f"- `{name}`" for name in cache],
        "",
        "### Revue du contenu, de la sécurité ou des données nécessaire",
        *[f"- `{name}`" for name in substantive],
    ]
    result = "\n".join(report) + "\n"
    print(result)
    dest = os.environ.get("GITHUB_STEP_SUMMARY")
    if dest:
        with open(dest, "a", encoding="utf-8") as f:
            f.write(result)
    return paths


def self_test() -> list[str]:
    path = "projets/projet-nova/faq.html"
    main = b'<html><script src="script.js?v=26.1.0"></script><p>FAQ</p></html>'
    release = main.replace(b"26.1.0", EXPECTED_RELEASE_CACHE)
    errors: list[str] = []
    if not cache_only_nova_conflict(path, main, release):
        errors.append("Cas positif : simple version Nova non reconnue")
    malicious = release.replace(b"<p>FAQ</p>", b"<p>Questions differentes</p>")
    if cache_only_nova_conflict(path, main, malicious):
        errors.append("Changement de contenu masqué comme une simple version")
    if cache_only_nova_conflict("projets/projet-nova/data/evidence.json", main, release):
        errors.append("JSON politique assimilé abusivement à une version de script")
    if cache_only_nova_conflict(path, main, main):
        errors.append("Versions identiques classées à tort comme conflit")
    if cache_only_nova_conflict(path, main, main.replace(b"26.1.0", b"24.4.23")):
        errors.append("Version candidate obsolète classée à tort comme correcte")
    if cache_only_nova_conflict(path, main, release.replace(b"</html>", b"</body></html>")):
        errors.append("Page modifiée considérée à tort comme cache identique")
    page = (ROOT / "projets/projet-nova/404.html").read_text(encoding="utf-8")
    for marker in (
        'noindex, nofollow, noarchive',
        'aria-controls="navigation-principale"',
        'id="navigation-principale"',
        'script.js?v=26.2.0',
    ):
        if marker not in page:
            errors.append("404 Nova : reprise main/accessibilité absente : " + marker)
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        faults = self_test()
        for fault in faults:
            print("ECHEC:", fault)
        if faults:
            raise SystemExit(1)
        print("OK : classification conservative des conflits et 404 Nova protégée.")
    elif args.audit:
        audit()
    else:
        parser.error("Choisir --self-test ou --audit")
