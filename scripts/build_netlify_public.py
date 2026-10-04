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
PREVIEW_ROBOTS_TAG = "noindex, nofollow, noarchive"
PREVIEW_HEADERS = f"""/*
  X-Robots-Tag: {PREVIEW_ROBOTS_TAG}
"""
GENERATED_NETLIFY_FILES = {"_headers", "_redirects"}
RELEASE_METADATA_PATH = Path(".well-known/release.json")
RELEASE_SHA_ENV = "SINJIRA_RELEASE_SHA"
NETLIFY_CONFIG = ROOT / "netlify.toml"
VERCEL_CONFIG = ROOT / "vercel.json"
NETLIFY_STAGING_WORKFLOW = ROOT / ".github/workflows/deploy-netlify-staging.yml"
VERCEL_BUILD_COMMAND = "CONTEXT=deploy-preview SINJIRA_RELEASE_SHA=$VERCEL_GIT_COMMIT_SHA python3 scripts/build_netlify_public.py"
REQUIRED_TECHNICAL_404S = {
    "/supabase/*",
    "/scripts/*",
    "/docs/*",
    "/.github/*",
    "/tests/*",
    "/mobile-native/*",
}
PRIVATE_RUNTIME_HEADER_PATHS = {
    "/compte/*",
    "/admin/*",
    "/Admin/*",
    "/app/*",
    "/histoire-de-vie/*",
}
REQUIRED_ROBOTS_DISALLOWS = {
    "/app/",
    "/compte/",
    "/histoire-de-vie/",
    "/Admin/",
    "/admin/",
    "/supabase/",
    "/.github/",
    "/mobile-native/",
    "/tests/",
    "/docs/",
    "/scripts/",
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

# Frontière fail-closed des PDF SINJIRA publics. Le dossier documents ne doit
# jamais devenir une allowlist implicite par extension : l'édition intégrale
# du Livre I reste privée/non publiée tant qu'une décision humaine explicite
# et un mécanisme de diffusion autorisé ne sont pas en place.
SINJIRA_PUBLIC_DOCUMENTS = {
    Path("projets/sinjira/documents/Questionnaire_Registre_des_Consciences_Fans.pdf"),
    Path("projets/sinjira/documents/Questionnaire_SINJIRA_Registre_des_Consciences.pdf"),
    Path("projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf"),
}
SINJIRA_DOCUMENTS_DIR = Path("projets/sinjira/documents")
LIVRE1_DEMO_PUBLIC_PATH = Path(
    "projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf"
)
LIVRE1_DEMO_MASTER_SIZE_BYTES = 941_065
LIVRE1_DEMO_MASTER_SHA256 = (
    "d0668a7b07a07321ef1e02cfceb826d3881330bb36417d53e5ff5bd32635628e"
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

PUBLIC_ROOT_DENY = {
    "script.js",  # legacy racine inutilisé; contenait encore un routage Formspree Nova.
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
    if path.name in PUBLIC_ROOT_DENY:
        return False
    if path.name in PUBLIC_ROOT_EXACT:
        return True
    return path.suffix.lower() in PUBLIC_ROOT_SUFFIXES


def re_full_sha256(value: str) -> bool:
    value = value.strip().lower()
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def re_full_git_sha(value: str) -> bool:
    value = value.strip().lower()
    return len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def configured_release_sha() -> str:
    return os.environ.get(RELEASE_SHA_ENV, "").strip().lower()


def release_metadata(deploy_context: str | None) -> dict[str, object] | None:
    source_sha = configured_release_sha()
    if not source_sha:
        return None
    context = (deploy_context or "").strip()
    return {
        "schema_version": 1,
        "source_sha": source_sha,
        "context": "preview" if context == DEPLOY_PREVIEW_CONTEXT else "production",
    }


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

    # Les documents SINJIRA sont publiés par allowlist exacte. Une future
    # intégrale, un nouveau master ou une pièce de travail ajoutée dans ce
    # dossier reste donc hors _site jusqu'à décision explicite.
    if (
        len(parts) >= 3
        and parts[0] == "projets"
        and parts[1] == "sinjira"
        and parts[2] == "documents"
    ):
        return rel in SINJIRA_PUBLIC_DOCUMENTS

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



def load_netlify_config() -> dict:
    return tomllib.loads(NETLIFY_CONFIG.read_text(encoding="utf-8", errors="strict"))


def normalize_header_value(value: object) -> str:
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())


def render_standalone_headers(deploy_context: str | None = None) -> str:
    data = load_netlify_config()
    context = (
        deploy_context if deploy_context is not None else os.environ.get("CONTEXT", "")
    ).strip()
    lines: list[str] = []
    for rule in data.get("headers") or []:
        path = str(rule.get("for") or "").strip()
        values = dict(rule.get("values") or {})
        if not path:
            continue
        if context == DEPLOY_PREVIEW_CONTEXT and path == "/*":
            values["X-Robots-Tag"] = PREVIEW_ROBOTS_TAG
        lines.append(path)
        for key, value in values.items():
            header_value = normalize_header_value(value)
            if header_value:
                lines.append(f"  {key}: {header_value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_standalone_redirects() -> str:
    data = load_netlify_config()
    lines: list[str] = []
    for rule in data.get("redirects") or []:
        source = str(rule.get("from") or "").strip()
        target = str(rule.get("to") or "").strip()
        status = int(rule.get("status") or 301)
        force = bool(rule.get("force"))
        if not source or not target:
            continue
        status_token = f"{status}{'!' if force else ''}"
        lines.append(f"{source} {target} {status_token}")
    return "\n".join(lines).rstrip() + "\n"

def validate_vercel_config() -> list[str]:
    errors: list[str] = []
    if not VERCEL_CONFIG.is_file():
        return ["vercel.json absent"]

    try:
        data = json.loads(VERCEL_CONFIG.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"vercel.json illisible: {exc}"]

    if data.get("buildCommand") != VERCEL_BUILD_COMMAND:
        errors.append("Commande Vercel inattendue: builder public fail-closed requis.")
    if data.get("outputDirectory") != "_site":
        errors.append("Output Vercel inattendu: _site requis.")
    if data.get("cleanUrls") is not False:
        errors.append("Vercel cleanUrls doit rester false pour conserver les routes canoniques explicites.")

    header_rules = {
        rule.get("source"): {
            str(item.get("key") or ""): str(item.get("value") or "")
            for item in (rule.get("headers") or [])
            if isinstance(item, dict)
        }
        for rule in (data.get("headers") or [])
        if isinstance(rule, dict) and isinstance(rule.get("source"), str)
    }

    global_values = header_rules.get("/(.*)")
    if global_values is None:
        errors.append("En-têtes globaux Vercel absents.")
    else:
        robots = global_values.get("X-Robots-Tag", "").lower()
        for token in ("noindex", "nofollow", "noarchive"):
            if token not in robots:
                errors.append(f"Preview Vercel: X-Robots-Tag sans {token}.")
        if global_values.get("X-Content-Type-Options", "").lower() != "nosniff":
            errors.append("Preview Vercel: X-Content-Type-Options=nosniff requis.")
        csp = global_values.get("Content-Security-Policy", "")
        for directive in (
            "default-src 'self'",
            "script-src 'self'",
            "connect-src 'self'",
            "frame-src 'self' https://gpvivleexywljowcqkru.supabase.co",
            "frame-ancestors 'self'",
            "object-src 'self'",
            "base-uri 'self'",
        ):
            if directive not in csp:
                errors.append(f"Preview Vercel: directive CSP requise absente: {directive}.")
        if "https://www.bubblav.com" in csp:
            errors.append("Preview Vercel: BubblaV doit rester bloqué dans la CSP.")

    for source in (
        "/.well-known/release.json",
        "/compte/(.*)",
        "/admin/(.*)",
        "/Admin/(.*)",
        "/app/(.*)",
        "/histoire-de-vie/(.*)",
    ):
        values = header_rules.get(source)
        if values is None:
            errors.append(f"Preview Vercel: en-têtes privés absents: {source}")
            continue
        if values.get("Cache-Control", "").lower() != "no-store":
            errors.append(f"Preview Vercel: Cache-Control no-store requis: {source}")

    redirects = {
        (str(rule.get("source") or ""), str(rule.get("destination") or ""), bool(rule.get("permanent")))
        for rule in (data.get("redirects") or [])
        if isinstance(rule, dict)
    }
    expected_redirects = {
        ("/nova", "/projets/projet-nova/index.html", True),
        ("/roman", "/projets/sinjira/index.html", True),
        ("/registre", "/projets/sinjira/registre/index.html", True),
        ("/sinjira", "/projets/sinjira/index.html", True),
        ("/projets/ere-des-consciences/:path*", "/projets/sinjira/:path*", True),
    }
    missing_redirects = sorted(expected_redirects - redirects)
    if missing_redirects:
        errors.append(
            "Preview Vercel: redirections publiques requises absentes: "
            + ", ".join(source for source, _, _ in missing_redirects)
        )

    return errors


def validate_netlify_staging_workflow() -> list[str]:
    errors: list[str] = []
    if not NETLIFY_STAGING_WORKFLOW.is_file():
        return ["Workflow staging Netlify authentifié absent."]

    try:
        text = NETLIFY_STAGING_WORKFLOW.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        return [f"Workflow staging Netlify illisible: {exc}"]

    required_markers = (
        "workflow_dispatch:",
        "expected_sha:",
        "expected_site_name:",
        "confirmation:",
        "STAGING_ONLY",
        "permissions:\n  contents: read",
        "startsWith(github.ref, 'refs/heads/a1/web-release-')",
        "secrets.NETLIFY_AUTH_TOKEN",
        "secrets.NETLIFY_SITE_ID",
        "netlify-cli@27.10.2 deploy",
        "--auth \"$NETLIFY_AUTH_TOKEN\"",
        "--site \"$NETLIFY_SITE_ID\"",
        "--dir _preview_site",
        "--dir _site",
        "--no-build",
        "CONTEXT: deploy-preview",
        "CONTEXT: production",
        "--context preview --expected-sha \"$GITHUB_SHA\"",
        "--context production-candidate --same-netlify-site-as \"$PREVIEW_PERMALINK\" --expected-sha \"$GITHUB_SHA\"",
        "production_promoted",
        '"dns_changed": False',
    )
    for marker in required_markers:
        if marker not in text:
            errors.append(f"Workflow staging Netlify: marqueur requis absent: {marker}")

    forbidden_markers = (
        "\npush:",
        "\npull_request:",
        "--prod ",
        "--prod\n",
        "--prod-if-unlocked",
        "netlify deploy --prod",
        "github.ref == 'refs/heads/main'",
    )
    for marker in forbidden_markers:
        if marker in text:
            errors.append(f"Workflow staging Netlify: comportement interdit détecté: {marker.strip()}")

    deploy_count = text.count("netlify-cli@27.10.2 deploy")
    if deploy_count != 2:
        errors.append(
            f"Workflow staging Netlify: exactement 2 deploys brouillon requis, observé={deploy_count}."
        )

    if text.count("--no-build") != 2:
        errors.append("Workflow staging Netlify: --no-build requis sur les deux deploys.")

    return errors


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
        for directive in (
            "frame-src 'self' https://gpvivleexywljowcqkru.supabase.co",
            "frame-ancestors 'self'",
            "object-src 'self'",
            "base-uri 'self'",
        ):
            if directive not in csp:
                errors.append(f"CSP Netlify: directive requise absente: {directive}.")
        if global_values.get("X-Content-Type-Options") != "nosniff":
            errors.append("En-tête X-Content-Type-Options=nosniff requis.")

    header_rules = {
        rule.get("for"): (rule.get("values") or {})
        for rule in headers
        if isinstance(rule, dict) and isinstance(rule.get("for"), str)
    }
    release_values = header_rules.get("/.well-known/release.json")
    if release_values is None:
        errors.append("En-têtes Netlify du marqueur release.json absents.")
    else:
        if str(release_values.get("Cache-Control") or "").lower() != "no-store":
            errors.append("Cache-Control no-store requis: /.well-known/release.json")
        release_robots = str(release_values.get("X-Robots-Tag") or "").lower()
        for token in ("noindex", "nofollow", "noarchive"):
            if token not in release_robots:
                errors.append(f"X-Robots-Tag {token} requis: /.well-known/release.json")

    for private_path in sorted(PRIVATE_RUNTIME_HEADER_PATHS):
        values = header_rules.get(private_path)
        if values is None:
            errors.append(f"En-têtes privés Netlify absents: {private_path}")
            continue
        if str(values.get("Cache-Control") or "").lower() != "no-store":
            errors.append(f"Cache-Control no-store requis: {private_path}")
        robots = str(values.get("X-Robots-Tag") or "").lower()
        for token in ("noindex", "nofollow", "noarchive"):
            if token not in robots:
                errors.append(f"X-Robots-Tag {token} requis: {private_path}")

    redirects = data.get("redirects") or []
    for rule in redirects:
        unsupported = sorted(set(rule) & {"query", "conditions", "headers", "signed"})
        if unsupported:
            errors.append(
                "Redirection Netlify non sérialisable dans l’artefact autonome: "
                + str(rule.get("from") or "<sans from>")
                + " (" + ", ".join(unsupported) + ")"
            )
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


def validate_plan(*, allow_known_stale_demo_for_containment: bool = False) -> list[str]:
    errors: list[str] = []
    release_sha = configured_release_sha()
    if release_sha and not re_full_git_sha(release_sha):
        errors.append(f"{RELEASE_SHA_ENV} doit être un SHA Git complet de 40 caractères hexadécimaux.")
    errors.extend(validate_netlify_config())
    errors.extend(validate_vercel_config())
    errors.extend(validate_netlify_staging_workflow())

    robots_path = ROOT / "robots.txt"
    if not robots_path.is_file():
        errors.append("robots.txt absent")
    else:
        robots_text = robots_path.read_text(encoding="utf-8", errors="strict")
        for route in sorted(REQUIRED_ROBOTS_DISALLOWS):
            if f"Disallow: {route}" not in robots_text:
                errors.append(f"robots.txt: exclusion requise absente: {route}")

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

    for rel in sorted(SINJIRA_PUBLIC_DOCUMENTS):
        source = ROOT / rel
        if not source.is_file():
            errors.append(f"Document SINJIRA public allowlisté absent: {rel.as_posix()}")
        elif not relative_path_allowed(rel):
            errors.append(f"Document SINJIRA public allowlisté refusé: {rel.as_posix()}")

    sinjira_documents_root = ROOT / SINJIRA_DOCUMENTS_DIR
    if sinjira_documents_root.is_dir():
        for source in sorted(sinjira_documents_root.rglob("*")):
            if not source.is_file():
                continue
            rel = source.relative_to(ROOT)
            if rel not in SINJIRA_PUBLIC_DOCUMENTS and relative_path_allowed(rel):
                errors.append(
                    f"Document SINJIRA non allowlisté publiable par erreur: {rel.as_posix()}"
                )

    demo_master = ROOT / LIVRE1_DEMO_PUBLIC_PATH
    if demo_master.is_file():
        try:
            demo_size = demo_master.stat().st_size
            demo_sha = hashlib.sha256(demo_master.read_bytes()).hexdigest()
        except OSError as exc:
            errors.append(f"Démo Livre I illisible: {exc}")
        else:
            if not allow_known_stale_demo_for_containment:
                if demo_size != LIVRE1_DEMO_MASTER_SIZE_BYTES:
                    errors.append(
                        "Démo Livre I non conforme au master #363: "
                        f"taille={demo_size}, attendu={LIVRE1_DEMO_MASTER_SIZE_BYTES}."
                    )
                if demo_sha != LIVRE1_DEMO_MASTER_SHA256:
                    errors.append(
                        "Démo Livre I non conforme au master #363: "
                        f"sha256={demo_sha}, attendu={LIVRE1_DEMO_MASTER_SHA256}."
                    )
    else:
        errors.append(
            f"Démo Livre I publique absente: {LIVRE1_DEMO_PUBLIC_PATH.as_posix()}"
        )

    for private_probe in (
        Path("projets/sinjira/documents/SINJIRA_LIVRE_I_LA_CENDRE_DU_JUGEMENT.pdf"),
        Path("projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement.pdf"),
        Path("projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_MAITRE_OFFICIEL.pdf"),
        Path("projets/sinjira/documents/Livre_01_La_Cendre_du_Jugement.pdf"),
    ):
        if relative_path_allowed(private_probe):
            errors.append(
                f"Master/intégrale Livre I autorisé par erreur: {private_probe.as_posix()}"
            )

    if root_file_allowed(ROOT / "script.js"):
        errors.append("Script racine legacy script.js autorisé par erreur.")

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



def build(
    output: Path,
    deploy_context: str | None = None,
    standalone_netlify: bool = False,
    allow_known_stale_demo_for_containment: bool = False,
) -> None:
    errors = validate_plan(
        allow_known_stale_demo_for_containment=allow_known_stale_demo_for_containment
    )
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

    context = (
        deploy_context if deploy_context is not None else os.environ.get("CONTEXT", "")
    ).strip()
    metadata = release_metadata(context)
    if metadata is not None:
        release_path = output / RELEASE_METADATA_PATH
        release_path.parent.mkdir(parents=True, exist_ok=True)
        release_path.write_text(
            json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    if standalone_netlify:
        (output / "_headers").write_text(
            render_standalone_headers(context),
            encoding="utf-8",
        )
        (output / "_redirects").write_text(
            render_standalone_redirects(),
            encoding="utf-8",
        )
    elif context == DEPLOY_PREVIEW_CONTEXT:
        (output / "_headers").write_text(PREVIEW_HEADERS, encoding="utf-8")


def validate_output(
    output: Path,
    deploy_context: str | None = None,
    standalone_netlify: bool = False,
) -> list[str]:
    errors: list[str] = []
    output = output.resolve()
    context = (
        deploy_context if deploy_context is not None else os.environ.get("CONTEXT", "")
    ).strip()
    headers_path = output / "_headers"
    redirects_path = output / "_redirects"
    release_path = output / RELEASE_METADATA_PATH
    expected_release_metadata = release_metadata(context)

    if expected_release_metadata is None:
        if release_path.exists():
            errors.append("Marqueur release.json inattendu sans SHA source configuré.")
    elif not release_path.is_file():
        errors.append("Marqueur .well-known/release.json requis absent du publish.")
    else:
        try:
            observed_release_metadata = json.loads(
                release_path.read_text(encoding="utf-8", errors="strict")
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"Marqueur release.json illisible: {exc}")
        else:
            if observed_release_metadata != expected_release_metadata:
                errors.append("Marqueur release.json incohérent avec le SHA/contexte de build.")

    expected_headers: str | None = None
    if standalone_netlify:
        expected_headers = render_standalone_headers(context)
    elif context == DEPLOY_PREVIEW_CONTEXT:
        expected_headers = PREVIEW_HEADERS

    if expected_headers is None:
        if headers_path.exists():
            errors.append("Fichier _headers inattendu dans ce contexte.")
    elif not headers_path.is_file():
        errors.append("Fichier _headers requis absent du publish.")
    elif headers_path.read_text(encoding="utf-8", errors="strict") != expected_headers:
        errors.append("Fichier _headers du publish inattendu.")

    if standalone_netlify:
        expected_redirects = render_standalone_redirects()
        if not redirects_path.is_file():
            errors.append("Fichier _redirects requis absent de l’artefact Netlify autonome.")
        elif redirects_path.read_text(encoding="utf-8", errors="strict") != expected_redirects:
            errors.append("Fichier _redirects de l’artefact Netlify autonome inattendu.")
    elif redirects_path.exists():
        errors.append("Fichier _redirects inattendu hors artefact Netlify autonome.")

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
        if rel.as_posix() in GENERATED_NETLIFY_FILES:
            if rel == Path("_headers") and expected_headers is not None:
                continue
            if rel == Path("_redirects") and standalone_netlify:
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
    parser.add_argument("--check", action="store_true", help="Valider l'allowlist sans conserver de fichiers.")
    parser.add_argument(
        "--standalone-netlify",
        action="store_true",
        help="Embarquer _headers et _redirects dans _site pour un déploiement Netlify autonome.",
    )
    parser.add_argument(
        "--security-containment",
        action="store_true",
        help=(
            "Confinement GitHub Pages uniquement: conserve temporairement la démo Livre I "
            "actuelle même si son hash diffère du master #363, sans relâcher l'allowlist."
        ),
    )
    args = parser.parse_args()

    if args.security_containment and args.standalone_netlify:
        print("ECHEC: --security-containment est interdit avec --standalone-netlify.")
        return 1

    errors = validate_plan(
        allow_known_stale_demo_for_containment=args.security_containment
    )
    if errors:
        print(f"ECHEC: {len(errors)} problème(s) dans le plan de publication Netlify.")
        for error in errors:
            print("- " + error)
        return 1

    if args.check and args.security_containment:
        with tempfile.TemporaryDirectory(prefix="sinjira-pages-containment-") as tmp:
            containment_output = Path(tmp) / "_site"
            build(
                containment_output,
                deploy_context="production",
                allow_known_stale_demo_for_containment=True,
            )
            containment_errors = validate_output(
                containment_output,
                deploy_context="production",
            )
            if containment_errors:
                print(
                    f"ECHEC: {len(containment_errors)} problème(s) "
                    "dans l’artefact de confinement GitHub Pages."
                )
                for error in containment_errors:
                    print("- " + error)
                return 1
            if (containment_output / "_headers").exists() or (containment_output / "_redirects").exists():
                print("ECHEC: le confinement GitHub Pages ne doit pas embarquer _headers/_redirects.")
                return 1
            file_count = sum(
                1 for path in containment_output.rglob("*") if path.is_file()
            )
        print(
            "OK confinement GitHub Pages: artefact public isolé vérifié; "
            f"{file_count} fichiers; démo #363 actuelle tolérée uniquement pour confinement."
        )
        return 0

    if args.check:
        with tempfile.TemporaryDirectory(prefix="sinjira-netlify-public-") as tmp:
            root = Path(tmp)

            production_output = root / "production" / "_site"
            build(production_output, deploy_context="production")
            production_errors = validate_output(
                production_output,
                deploy_context="production",
            )
            if production_errors:
                print(f"ECHEC: {len(production_errors)} problème(s) dans le publish Netlify production temporaire.")
                for error in production_errors:
                    print("- " + error)
                return 1

            preview_output = root / "deploy-preview" / "_site"
            build(preview_output, deploy_context=DEPLOY_PREVIEW_CONTEXT)
            preview_errors = validate_output(
                preview_output,
                deploy_context=DEPLOY_PREVIEW_CONTEXT,
            )
            if preview_errors:
                print(f"ECHEC: {len(preview_errors)} problème(s) dans le deploy preview Netlify temporaire.")
                for error in preview_errors:
                    print("- " + error)
                return 1

            standalone_output = root / "standalone-production" / "_site"
            build(
                standalone_output,
                deploy_context="production",
                standalone_netlify=True,
            )
            standalone_errors = validate_output(
                standalone_output,
                deploy_context="production",
                standalone_netlify=True,
            )
            if standalone_errors:
                print(f"ECHEC: {len(standalone_errors)} problème(s) dans l’artefact Netlify autonome.")
                for error in standalone_errors:
                    print("- " + error)
                return 1

            standalone_preview_output = root / "standalone-preview" / "_site"
            build(
                standalone_preview_output,
                deploy_context=DEPLOY_PREVIEW_CONTEXT,
                standalone_netlify=True,
            )
            standalone_preview_errors = validate_output(
                standalone_preview_output,
                deploy_context=DEPLOY_PREVIEW_CONTEXT,
                standalone_netlify=True,
            )
            if standalone_preview_errors:
                print(
                    f"ECHEC: {len(standalone_preview_errors)} problème(s) "
                    "dans l’artefact Netlify autonome preview."
                )
                for error in standalone_preview_errors:
                    print("- " + error)
                return 1

            file_count = sum(1 for path in production_output.rglob("*") if path.is_file())
            standalone_file_count = sum(
                1 for path in standalone_output.rglob("*") if path.is_file()
            )
        print(
            "OK publication Netlify: builds dépôt + artefacts autonomes production/preview vérifiés; "
            f"{file_count} fichiers publics via build dépôt; "
            f"{standalone_file_count} fichiers dans l’artefact autonome; "
            "_headers/_redirects embarqués; preview noindex; "
            "répertoires techniques exclus; sitemap couvert."
        )
        return 0

    build(
        args.output,
        standalone_netlify=args.standalone_netlify,
        allow_known_stale_demo_for_containment=args.security_containment,
    )
    output_errors = validate_output(
        args.output,
        standalone_netlify=args.standalone_netlify,
    )
    if output_errors:
        print(f"ECHEC: {len(output_errors)} problème(s) dans le publish Netlify.")
        for error in output_errors:
            print("- " + error)
        return 1
    mode = "autonome" if args.standalone_netlify else "lié au dépôt"
    if args.security_containment:
        mode = "confinement sécurité GitHub Pages (démo #363 temporairement tolérée)"
    print(
        f"OK publication Netlify {mode} construite et vérifiée dans {args.output.resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
