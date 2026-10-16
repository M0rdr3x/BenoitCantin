#!/usr/bin/env python3
"""P50R — Inspecte une integration Git uniquement locale, et retourne toujours NO_GO.

Aucune commande de fusion, de push, de réseau ou de publication ici.
Les merges se font uniquement dans un environnement ephemere GitHub Actions.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

MAIN = "9ed5f70cbe7022f25a679346a1288701f3b09067"
PR640 = "332afe7d9d73390feb41b0deb588692f3c73d48d"
EXPECT = frozenset((
    ".github/workflows/validate-nova-participation.yml",
    "projets/projet-nova/avis-legal.html",
    "projets/projet-nova/participer.html",
    "scripts/tests/test_validate_nova_publication_p50b.py",
    "scripts/validate_nova_publication_p50b.py",
    ".github/workflows/nova-identite.yml",
    "projets/projet-nova/IDENTITE_UNIQUE_PROJET_NOVA.md",
    "projets/projet-nova/README.md",
    "projets/projet-nova/README_SITE.txt",
    "projets/projet-nova/code-conduite.html",
    "projets/projet-nova/data/sources.json",
    "projets/projet-nova/official/reference/statuts.md",
    "scripts/tests/test_validate_nova_identity.py",
    "scripts/validate_nova_identity.py",
))
PAGE_SHA = {
    "projets/projet-nova/participer.html": "ef037f1ef6257c676573a80afae060b4e965bb25",
    "projets/projet-nova/avis-legal.html": "602dc790de1416a3bc3806f6a0d328a489925752",
    "projets/projet-nova/code-conduite.html": "34a00ecae9592846d6578b74e03796a768b2450f",
}
SCANNER_FILE = "scripts/validate_nova_publication_p50b.py"


def git(repo: Path, *args: str):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True, capture_output=True, check=False,
    )


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") +
                        b"\x00" + data).hexdigest()


def examine_paths(paths: object) -> list[str]:
    if not isinstance(paths, (set, list, tuple)):
        return ["CHEMINS_INVALIDES"]
    if set(paths) != EXPECT:
        return [
            "DELTA_CHEMINS_NON_CONFORME",
            "CHEMINS_EN_TROP:" + ",".join(sorted(set(paths) - EXPECT)),
            "CHEMINS_MANQUANTS:" + ",".join(sorted(EXPECT - set(paths))),
        ]
    return []


def check_statuts(root: Path) -> list[str]:
    site = root / "projets/projet-nova"
    try:
        manifest = json.loads((site / "data/sources.json").read_text("utf-8"))
        item = manifest["documents"]["statuts"]["parts"][0]
        if item.get("path") != "official/reference/statuts.md":
            return ["CHEMIN_STATUTS_INVALIDE"]
        content = (site / "official/reference/statuts.md").read_bytes()
        computed = hashlib.sha256(content).hexdigest()
        if item.get("sha256") != computed:
            return ["EMPREINTE_STATUTS_INVALIDE"]
    except (OSError, KeyError, ValueError, TypeError, IndexError):
        return ["MANIFESTE_STATUTS_ILLISIBLE"]
    return []


def inspect(root: Path, base: str=MAIN) -> dict:
    problems=[]
    if re.fullmatch(r"[a-f0-9]{40}",base) is None:
        problems.append("SHA_BASE_INVALIDE")
    if not (root / ".git").exists():
        problems.append("ARBRE_GIT_ABSENT")
    if problems:
        return make_report(problems, None, [])
    current = git(root, "rev-parse", "HEAD")
    if current.returncode:
        problems.append("HEAD_ILLISIBLE")
    changed = git(root, "diff", "--name-only", base, "HEAD")
    if changed.returncode:
        problems.append("DIFF_GIT_INACCESSIBLE")
        paths=[]
    else:
        paths=[v for v in changed.stdout.splitlines() if v]
        problems+=examine_paths(paths)
    ancestor = git(root, "merge-base", "--is-ancestor", PR640, "HEAD")
    if ancestor.returncode == 0:
        problems.append("PR640_INTEGREE_INTERDITE")
    elif ancestor.returncode != 1:
        problems.append("CONTROLE_PR640_INCONCLUSIF")
    status = git(root, "status", "--porcelain")
    if status.returncode or status.stdout.strip():
        problems.append("ARBRE_NON_PROPRE")
    for path, expected in PAGE_SHA.items():
        try:
            got=blob_sha((root/path).read_bytes())
            if got!=expected:
                problems.append("BLOB_PAGE_NON_CONFORME:"+path)
        except OSError:
            problems.append("PAGE_MANQUANTE:"+path)
    # Scanner digest is read from the exact PR657 blob, not a hard-coded vendor list.
    try:
        scanner=(root/SCANNER_FILE).read_text("utf-8")
        if ("suspicious_destination" not in scanner or
            "class SiteHTML" not in scanner or
            "urlsplit" not in scanner):
            problems.append("VALIDATEUR_ATTENDU_ABSENT")
    except (OSError, UnicodeError):
        problems.append("VALIDATEUR_ILLISIBLE")
    problems+=check_statuts(root)
    return make_report(problems, current.stdout.strip() if not current.returncode else None, paths)


def make_report(issues: list[str], head: str|None, changed: list[str]) -> dict:
    return {
        "jalon":"P50R",
        "controle":"INTEGRATION_LOCALE_SANS_PUSH",
        "statut_technique":"COHERENCE_SIMULEE" if not issues else "ECHEC_OU_PREUVE_INCOMPLETE",
        "problemes":sorted(set(issues)),
        "base_figee":MAIN,
        "head_ephemere":head,
        "nb_fichiers_modifies":len(changed),
        "fichiers_modifies":sorted(changed),
        "nb_fichiers_attendus":len(EXPECT),
        "pr640_autorisee":False,
        "revue_humaine_obtenue":False,
        "autorisation_publication":False,
        "deploiement_effectue":False,
        "decision":"NO_GO_AUTOMATIQUE",
        "limite":"La simulation et les tests ne prouvent ni publication ni habilitations reelles.",
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree",type=Path,required=True)
    parser.add_argument("--report",type=Path)
    args=parser.parse_args(argv)
    result=inspect(args.tree)
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(text,encoding="utf-8")
    else:
        print(text,end="")
    return 0 if result["statut_technique"]=="COHERENCE_SIMULEE" else 2

if __name__=="__main__":
    sys.exit(main())
