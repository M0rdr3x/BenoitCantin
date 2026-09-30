#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import hashlib
import os
import shutil
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "_site"
DEPLOY_PREVIEW_CONTEXT = "deploy-preview"
PREVIEW_HEADERS = """/*
  X-Robots-Tag: noindex, nofollow, noarchive
"""
NETLIFY_CONFIG = ROOT / "netlify.toml"
REQUIRED_TECHNICAL_404S = {
    "/supabase/*",
    "/scripts/*",
    "/docs/*",
    "/.github/*",
    "/tests/*",
    "/mobile-native/*",
}

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

RESTRICTED_RUNTIME_DIRS = {
    "Admin",
    "admin",
    "app",
    "compte",
    "histoire-de-vie",
}

RUNTIME_WEB_SUFFIXES = {
    ".html",
    ".htm",
    ".css",
    ".js",
    ".mjs",
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
    ".woff",
    ".woff2",
    ".ttf",
}

PUBLIC_ROOT_EXACT = {
    ".nojekyll",
    "CNAME",
    "documents.json",
    "documents-word-only.json",
    "robots.txt",
    "sitemap.xml",
}

PROJECT_NOVA_STRUCTURED_SUFFIXES = {
    ".md",
    ".csv",
    ".markdown",
    ".txt",
    ".toml",
    ".json",
    ".yaml",
    ".yml",
    ".sql",
    ".py",
    ".sh",
    ".ts",
    ".tsx",
    ".env",
    ".ini",
    ".cfg",
    ".lock",
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".odt",
    ".ods",
    ".odp",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".log",
    ".bak",
    ".backup",
    ".tmp",
    ".psd",
    ".ai",
    ".sketch",
    ".fig",
    ".pem",
    ".key",
    ".crt",
    ".p12",
    ".pfx",
}

PROJECT_NOVA_PUBLIC_STRUCTURED_EXACT = {
    Path("projets/projet-nova/PROPOSITIONS_PUBLIQUES.md"),
    Path("projets/projet-nova/documents.json"),
    Path("projets/projet-nova/documents-word-only.json"),
}

PROJECT_NOVA_PUBLIC_STRUCTURED_PREFIXES = (
    Path("projets/projet-nova/data"),
    Path("projets/projet-nova/official/reference"),
)

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
    ".well-known/security.txt",
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


def re_full_sha256(value: str) -> bool:
    value = value.strip().lower()
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def project_nova_structured_allowed(rel: Path) -> bool:
    if rel in PROJECT_NOVA_PUBLIC_STRUCTURED_EXACT:
        return True
    for prefix in PROJECT_NOVA_PUBLIC_STRUCTURED_PREFIXES:
        try:
            nested = rel.relative_to(prefix)
        except ValueError:
            continue
        if not nested.parts:
            return False
        if prefix.name == "data":
            return rel.suffix.lower() == ".json"
        if prefix.name == "reference":
            return rel.suffix.lower() == ".md"
    return False


def relative_path_allowed(rel: Path) -> bool:
    parts = rel.parts
    if not parts:
        return False
    if len(parts) == 1:
        return root_file_allowed(ROOT / rel)
    if parts[0] not in PUBLIC_DIRS:
        return False

    # Les surfaces privées/runtime doivent rester publiables sans jamais
    # accepter par défaut un futur artefact de maintenance, de configuration
    # ou de données techniques.
    if parts[0] in RESTRICTED_RUNTIME_DIRS:
        return rel.suffix.lower() in RUNTIME_WEB_SUFFIXES

    # Les assets runtime ne doivent pas embarquer leurs README de maintenance.
    if parts[0] == "assets" and rel.suffix.lower() in {".md", ".txt", ".toml"}:
        return False

    # Projet Nova publie uniquement les données runtime explicitement publiques
    # et les références documentaires déclarées. Les README, rapports,
    # receipts, états de build et historiques official/versions restent dans Git.
    if (
        len(parts) >= 3
        and parts[0] == "projets"
        and parts[1] == "projet-nova"
        and rel.suffix.lower() in PROJECT_NOVA_STRUCTURED_SUFFIXES
    ):
        return project_nova_structured_allowed(rel)

    # Le Codex peut contenir des contrats de livraison et inventaires de sources
    # qui documentent précisément des artefacts privés/non déployés. Ils restent
    # dans le dépôt de travail mais ne doivent jamais être copiés dans _site.
    if (
        len(parts) >= 4
        and parts[0] == "projets"
        and parts[1] == "sinjira"
        and parts[2] == "codex"
        and rel.suffix.lower() == ".json"
        and (
            rel.name.endswith("-delivery-contract.json")
            or "-source-artifacts-" in rel.name
        )
    ):
        return False

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


def validate_netlify_config() -> list[str]:
    errors: list[str] = []
    if not NETLIFY_CONFIG.is_file():
        return ["netlify.toml absent"]

    try:
        data = tomllib.loads(NETLIFY_CONFIG.read_text(encoding="utf-8", errors="strict"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"netlify.toml illisible: {exc}"]

    build = data.get("build") or {}
    if build.get("command") != "python3 scripts/build_netlify_public.py":
        errors.append("Commande Netlify inattendue: python3 scripts/build_netlify_public.py requis.")
    if build.get("publish") != "_site":
        errors.append("Publish Netlify inattendu: _site requis.")

    headers = data.get("headers") or []
    global_values = None
    for rule in headers:
        if rule.get("for") == "/*":
            global_values = rule.get("values") or {}
            break
    if global_values is None:
        errors.append("En-têtes globaux Netlify absents.")
    else:
        csp = str(global_values.get("Content-Security-Policy") or "")
        if "script-src" not in csp or "connect-src" not in csp:
            errors.append("CSP Netlify: script-src et connect-src sont obligatoires.")
        if "https://www.bubblav.com" in csp:
            errors.append(
                "CSP Netlify: BubblaV doit rester bloqué tant que le fournisseur public n’est pas réactivé."
            )
        for directive in ("frame-ancestors 'self'", "object-src 'self'", "base-uri 'self'"):
            if directive not in csp:
                errors.append(f"CSP Netlify: directive requise absente: {directive}.")
        if global_values.get("X-Content-Type-Options") != "nosniff":
            errors.append("En-tête X-Content-Type-Options=nosniff requis.")

    redirects = data.get("redirects") or []
    observed = {
        rule.get("from")
        for rule in redirects
        if rule.get("to") == "/404.html"
        and rule.get("status") == 404
        and rule.get("force") is True
    }
    missing = sorted(REQUIRED_TECHNICAL_404S - observed)
    if missing:
        errors.append("Redirections 404 techniques absentes: " + ", ".join(missing))

    return errors


def validate_plan() -> list[str]:
    errors: list[str] = []
    errors.extend(validate_netlify_config())

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

    for runtime_dir in sorted(RESTRICTED_RUNTIME_DIRS):
        for probe in ("README.md", "config.json", "secret.env", "schema.sql"):
            if relative_path_allowed(Path(runtime_dir) / probe):
                errors.append(
                    f"Artefact non web autorisé par erreur dans {runtime_dir}/: {probe}"
                )

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
        Path("projets/projet-nova/official/versions/V320/V320_GITHUB_PUBLICATION_RECEIPT.json"),
        Path("projets/projet-nova/data/modele_comptabilite.csv"),
        Path("projets/projet-nova/data/modele_rencontres.csv"),
        Path("projets/projet-nova/official/versions/V320/V320_REGISTRE_ANTI_CONTOURNEMENT_MODELE.csv"),
        Path("projets/projet-nova/official/versions/V320/V320_VALIDATION_REPORT.md"),
        Path("projets/projet-nova/README.md"),
        Path("projets/projet-nova/SHA256SUMS.txt"),
        Path("projets/projet-nova/README.md"),
        Path("projets/projet-nova/VERIFICATION_AVANT_PUBLICATION.md"),
        Path("projets/projet-nova/netlify.toml"),
        Path("projets/sinjira/codex/livre-i-delivery-contract.json"),
        Path("projets/sinjira/codex/livre-i-source-artifacts-2026-09-15.json"),
    ):
        if relative_path_allowed(rel):
            errors.append(f"Artefact technique sous-arbre autorisé par erreur: {rel.as_posix()}")

    for rel in (
        Path("projets/projet-nova/PROPOSITIONS_PUBLIQUES.md"),
        Path("projets/projet-nova/documents.json"),
        Path("projets/projet-nova/data/actualites.json"),
        Path("projets/projet-nova/data/sources.json"),
        Path("projets/projet-nova/official/reference/corpus.md"),
        Path("projets/projet-nova/official/reference/statuts.md"),
        Path("projets/projet-nova/official/reference/programme.md"),
        Path("projets/projet-nova/official/reference/finances.md"),
    ):
        if (ROOT / rel).is_file() and not relative_path_allowed(rel):
            errors.append(f"Référence publique Projet Nova exclue par erreur: {rel.as_posix()}")

    sources_manifest = ROOT / "projets/projet-nova/data/sources.json"
    if sources_manifest.is_file():
        try:
            manifest = json.loads(sources_manifest.read_text(encoding="utf-8", errors="strict"))
            documents = manifest.get("documents") or {}
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"Manifeste sources Projet Nova illisible: {exc}")
            documents = {}

        for key, document in documents.items():
            parts_manifest = document.get("parts") if isinstance(document, dict) else None
            if not isinstance(parts_manifest, list) or not parts_manifest:
                errors.append(f"Source Projet Nova sans parts: {key}")
                continue
            for part in parts_manifest:
                source_path = part.get("path") if isinstance(part, dict) else None
                if not isinstance(source_path, str) or not source_path.strip():
                    errors.append(f"Source Projet Nova invalide: {key}")
                    continue
                rel = Path("projets/projet-nova") / source_path
                source_file = ROOT / rel
                if not source_file.is_file():
                    errors.append(f"Source Projet Nova absente: {rel.as_posix()}")
                    continue
                if not relative_path_allowed(rel):
                    errors.append(f"Source Projet Nova hors allowlist: {rel.as_posix()}")
                    continue

                expected_sha = part.get("sha256") if isinstance(part, dict) else None
                if not isinstance(expected_sha, str) or not re_full_sha256(expected_sha):
                    errors.append(f"SHA-256 Projet Nova absent ou invalide: {rel.as_posix()}")
                    continue
                actual_sha = hashlib.sha256(source_file.read_bytes()).hexdigest()
                if actual_sha != expected_sha.lower():
                    errors.append(
                        f"SHA-256 Projet Nova incohérent: {rel.as_posix()} "
                        f"(manifest={expected_sha.lower()}, actuel={actual_sha})"
                    )

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


def build(output: Path, deploy_context: str | None = None) -> None:
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

    context = (deploy_context if deploy_context is not None else os.environ.get("CONTEXT", "")).strip()
    if context == DEPLOY_PREVIEW_CONTEXT:
        (output / "_headers").write_text(PREVIEW_HEADERS, encoding="utf-8")


def validate_output(output: Path, deploy_context: str | None = None) -> list[str]:
    errors: list[str] = []
    output = output.resolve()
    context = (deploy_context if deploy_context is not None else os.environ.get("CONTEXT", "")).strip()
    preview_headers = output / "_headers"
    if context == DEPLOY_PREVIEW_CONTEXT:
        if not preview_headers.is_file():
            errors.append("Fichier _headers absent du deploy preview.")
        elif preview_headers.read_text(encoding="utf-8", errors="strict") != PREVIEW_HEADERS:
            errors.append("Fichier _headers du deploy preview inattendu.")
    elif preview_headers.exists():
        errors.append("Fichier _headers présent hors deploy preview.")


    for forbidden in FORBIDDEN_DIRS:
        if (output / forbidden).exists():
            errors.append(f"Répertoire technique présent dans le publish: {forbidden}/")

    for rel in REQUIRED_PUBLIC_PATHS:
        if not (output / rel).is_file():
            errors.append(f"Fichier public requis absent du publish: {rel}")

    for published in output.rglob("*"):
        if not published.is_file():
            continue
        rel = published.relative_to(output)
        if rel == Path("_headers") and context == DEPLOY_PREVIEW_CONTEXT:
            continue
        if not relative_path_allowed(rel):
            errors.append(f"Fichier hors allowlist présent dans le publish: {rel.as_posix()}")

    sitemap_path = output / "sitemap.xml"
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
            errors.append(f"Sitemap du publish illisible: {exc}")
            locs = []

        for url in locs:
            try:
                rel = sitemap_source_path(url)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if not (output / rel).is_file():
                errors.append(f"URL sitemap absente du publish: {url} -> {rel.as_posix()}")

    return errors


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
        with tempfile.TemporaryDirectory(prefix="sinjira-netlify-public-") as tmp:
            root = Path(tmp)

            production_output = root / "production" / "_site"
            build(production_output, deploy_context="production")
            production_errors = validate_output(production_output, deploy_context="production")
            if production_errors:
                print(f"ECHEC: {len(production_errors)} problème(s) dans le publish Netlify production temporaire.")
                for error in production_errors:
                    print("- " + error)
                return 1

            preview_output = root / "deploy-preview" / "_site"
            build(preview_output, deploy_context=DEPLOY_PREVIEW_CONTEXT)
            preview_errors = validate_output(preview_output, deploy_context=DEPLOY_PREVIEW_CONTEXT)
            if preview_errors:
                print(f"ECHEC: {len(preview_errors)} problème(s) dans le deploy preview Netlify temporaire.")
                for error in preview_errors:
                    print("- " + error)
                return 1

            file_count = sum(1 for path in production_output.rglob("*") if path.is_file())
        print(
            "OK publication Netlify: builds production + deploy-preview vérifiés; "
            f"{file_count} fichiers publics en production; preview noindex; "
            "répertoires techniques exclus; sitemap couvert."
        )
        return 0

    build(args.output)
    output_errors = validate_output(args.output)
    if output_errors:
        print(f"ECHEC: {len(output_errors)} problème(s) dans le publish Netlify.")
        for error in output_errors:
            print("- " + error)
        return 1
    print(f"OK publication Netlify construite et vérifiée dans {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
