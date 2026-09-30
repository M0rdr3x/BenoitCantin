#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "_site"

PUBLIC_DIRS = (
    ".well-known",
    "Admin",
    "admin",
    "app",
    "assets",
    "compte",
    "histoire-de-vie",
    "projets",
)

FORBIDDEN_DIRS = (
    ".github",
    "docs",
    "mobile-native",
    "scripts",
    "supabase",
    "tests",
)

PUBLIC_ROOT_EXACT = {
    ".nojekyll",
    "CNAME",
    "documents.json",
    "documents-word-only.json",
    "robots.txt",
    "sitemap.xml",
}

PUBLIC_ROOT_SUFFIXES = {
    ".html",
    ".css",
    ".js",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".avif",
    ".gif",
    ".svg",
    ".ico",
    ".webmanifest",
    ".xml",
    ".pdf",
    ".mp4",
    ".webm",
    ".mp3",
    ".ogg",
    ".wav",
}

REQUIRED_PUBLIC_PATHS = (
    "index.html",
    "404.html",
    "robots.txt",
    "sitemap.xml",
    "sw.js",
    "manifest.webmanifest",
    "assets/js/site.js",
    "assets/js/ai-transparency.js",
    "assets/css/ai-transparency.css",
    "assistant.html",
    "transparence-ia.html",
    "projets/projet-nova/index.html",
    "projets/projet-nova/script.js",
    "compte/index.html",
    "admin/index.html",
    "app/index.html",
)


def root_file_allowed(path: Path) -> bool:
    if path.parent != ROOT:
        return False
    if path.name in PUBLIC_ROOT_EXACT:
        return True
    return path.suffix.lower() in PUBLIC_ROOT_SUFFIXES


def relative_path_allowed(rel: Path) -> bool:
    parts = rel.parts
    if not parts:
        return False
    if len(parts) == 1:
        return root_file_allowed(ROOT / rel)
    if parts[0] not in PUBLIC_DIRS:
        return False

    # Les assets runtime ne doivent pas embarquer leurs README de maintenance.
    if parts[0] == "assets" and rel.suffix.lower() in {".md", ".txt", ".toml"}:
        return False

    # Projet Nova conserve ses références publiques structurées sous official/.
    # Les guides/audits/configs directement à la racine du sous-site ne font
    # pas partie du site déployé, sauf la proposition publique explicitement
    # conservée.
    if (
        len(parts) == 3
        and parts[0] == "projets"
        and parts[1] == "projet-nova"
        and rel.suffix.lower() in {".md", ".txt", ".toml"}
    ):
        return rel.name == "PROPOSITIONS_PUBLIQUES.md"

    return True


def sitemap_source_path(url: str) -> Path:
    parsed = urlparse(url)
    if parsed.netloc not in {"www.benoitcantin.com", "benoitcantin.com"}:
        raise ValueError(f"Domaine sitemap inattendu: {url}")
    path = parsed.path
    if path == "/":
        return Path("index.html")
    rel = Path(path.lstrip("/"))
    if path.endswith("/"):
        rel = rel / "index.html"
    return rel


def validate_plan() -> list[str]:
    errors: list[str] = []

    overlap = sorted(set(PUBLIC_DIRS) & set(FORBIDDEN_DIRS))
    if overlap:
        errors.append("Répertoires à la fois publics et interdits: " + ", ".join(overlap))

    for rel in REQUIRED_PUBLIC_PATHS:
        source = ROOT / rel
        if not source.is_file():
            errors.append(f"Fichier public requis absent: {rel}")
        elif not relative_path_allowed(Path(rel)):
            errors.append(f"Fichier public requis hors allowlist: {rel}")

    for forbidden in FORBIDDEN_DIRS:
        if relative_path_allowed(Path(forbidden) / "probe.txt"):
            errors.append(f"Répertoire technique autorisé par erreur: {forbidden}/")

    for name in (
        "README.md",
        "AI_TRANSPARENCY.md",
        "ASSISTANT_GOVERNANCE.md",
        "SUPABASE_V24_1_A_APPLIQUER.md",
        "VERIFICATION_AVANT_PUBLICATION.md",
    ):
        if root_file_allowed(ROOT / name):
            errors.append(f"Document technique racine autorisé par erreur: {name}")

    for rel in (
        Path("assets/icons/README.md"),
        Path("projets/projet-nova/README.md"),
        Path("projets/projet-nova/VERIFICATION_AVANT_PUBLICATION.md"),
        Path("projets/projet-nova/netlify.toml"),
    ):
        if relative_path_allowed(rel):
            errors.append(f"Artefact technique sous-arbre autorisé par erreur: {rel.as_posix()}")

    for rel in (
        Path("projets/projet-nova/PROPOSITIONS_PUBLIQUES.md"),
        Path("projets/projet-nova/official/reference/programme.md"),
    ):
        if (ROOT / rel).is_file() and not relative_path_allowed(rel):
            errors.append(f"Référence publique Projet Nova exclue par erreur: {rel.as_posix()}")

    sitemap_path = ROOT / "sitemap.xml"
    if sitemap_path.is_file():
        try:
            root = ET.parse(sitemap_path).getroot()
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            locs = [
                (node.text or "").strip()
                for node in root.findall(".//sm:loc", ns)
                if (node.text or "").strip()
            ]
        except (ET.ParseError, OSError) as exc:
            errors.append(f"Sitemap illisible: {exc}")
            locs = []

        if not locs:
            errors.append("Sitemap public vide ou illisible.")

        for url in locs:
            try:
                rel = sitemap_source_path(url)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if not relative_path_allowed(rel):
                errors.append(f"URL sitemap hors allowlist Netlify: {url} -> {rel.as_posix()}")
                continue
            if not (ROOT / rel).is_file():
                errors.append(f"URL sitemap sans fichier source: {url} -> {rel.as_posix()}")

    return errors


def build(output: Path) -> None:
    errors = validate_plan()
    if errors:
        raise SystemExit("\n".join(errors))

    output = output.resolve()
    if output == ROOT or ROOT in output.parents and output.name in FORBIDDEN_DIRS:
        raise SystemExit(f"Répertoire de sortie invalide: {output}")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    for name in PUBLIC_DIRS:
        source_root = ROOT / name
        if not source_root.is_dir():
            continue
        for source in source_root.rglob("*"):
            if not source.is_file():
                continue
            rel = source.relative_to(ROOT)
            if not relative_path_allowed(rel):
                continue
            destination = output / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    for source in ROOT.iterdir():
        if not source.is_file():
            continue
        if root_file_allowed(source):
            shutil.copy2(source, output / source.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Construire le publish directory public Netlify.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Valider l'allowlist sans copier de fichiers.")
    args = parser.parse_args()

    errors = validate_plan()
    if errors:
        print(f"ECHEC: {len(errors)} problème(s) dans le plan de publication Netlify.")
        for error in errors:
            print("- " + error)
        return 1

    if args.check:
        print(
            "OK publication Netlify: allowlist racine validée; "
            "répertoires techniques exclus; sitemap couvert."
        )
        return 0

    build(args.output)
    print(f"OK publication Netlify construite dans {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
