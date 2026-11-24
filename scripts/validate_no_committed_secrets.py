#!/usr/bin/env python3
from __future__ import annotations

import base64
import binascii
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MAX_TEXT_BYTES = 2 * 1024 * 1024
# Les gros fichiers sources ne doivent pas échapper silencieusement au contrôle.
MANDATORY_TEXT_EXTENSIONS = frozenset({
    '.cjs', '.conf', '.css', '.csv', '.html', '.htm', '.ini', '.js',
    '.json', '.md', '.mjs', '.py', '.sh', '.sql', '.svg', '.toml',
    '.ts', '.tsx', '.txt', '.webmanifest', '.xml', '.yaml', '.yml',
})
MANDATORY_TEXT_NAMES = frozenset({'Dockerfile', 'Makefile', 'CNAME'})

ALLOWED_ENV_FILES = {'.env.example', '.env.sample', '.env.template'}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ('Supabase secret key', re.compile(r'\bsb_secret_[A-Za-z0-9._-]{20,}\b')),
    ('GitHub classic token', re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b')),
    ('GitHub fine-grained token', re.compile(r'\bgithub_pat_[A-Za-z0-9_]{30,}\b')),
    ('Stripe live secret key', re.compile(r'\bsk_live_[A-Za-z0-9]{20,}\b')),
    ('OpenAI project secret', re.compile(r'\bsk-proj-[A-Za-z0-9_-]{20,}\b')),
    ('AWS access key ID', re.compile(r'\bAKIA[0-9A-Z]{16}\b')),
    ('GitLab access token', re.compile(r'\bglpat-[A-Za-z0-9_-]{20,}\b')),
    ('Private key block', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
    (
        'Deployment or anti-bot secret assignment',
        re.compile(
            r'\b(?:NETLIFY_AUTH_TOKEN|CLOUDFLARE_API_TOKEN|TURNSTILE_SECRET_KEY|SUPABASE_ACCESS_TOKEN)\b'
            r'\s*[:=]\s*["\x27]?'
            r'(?!\$\{|\$[A-Z_]|Deno\.env|process\.env|os\.environ|os\.getenv|secrets\.|'
            r'<|your[-_]|example|placeholder|changeme|redacted)'
            r'[A-Za-z0-9._-]{24,}',
            re.IGNORECASE,
        ),
    ),
    (
        'Supabase service-role assignment',
        re.compile(
            r'\bSUPABASE_SERVICE_ROLE_KEY\b\s*[:=]\s*["\']?'
            r'(?!\$\{|\$[A-Z_]|Deno\.env|process\.env|os\.environ|secrets\.|<|your[-_]|example|placeholder|changeme)'
            r'[^\s"\']{20,}',
            re.IGNORECASE,
        ),
    ),
    (
        'Database password assignment',
        re.compile(
            r'\b(?:SUPABASE_DB_PASSWORD|POSTGRES_PASSWORD|DATABASE_PASSWORD)\b\s*[:=]\s*["\']?'
            r'(?!\$\{|\$[A-Z_]|Deno\.env|process\.env|os\.environ|secrets\.|<|your[-_]|example|placeholder|changeme)'
            r'[^\s"\']{12,}',
            re.IGNORECASE,
        ),
    ),
    (
        'Resend API key assignment',
        re.compile(
            r'\bRESEND_API_KEY\b\s*[:=]\s*["\']?'
            r'(?!\$\{|\$[A-Z_]|Deno\.env|process\.env|os\.environ|secrets\.|<|your[-_]|example|placeholder|changeme)'
            r'[^\s"\']{20,}',
            re.IGNORECASE,
        ),
    ),
)


# A JWT can be pasted directly into a source file without an assignment such as
# SUPABASE_SERVICE_ROLE_KEY=..., evading prefix/assignment-only detection.
# Require recognizable JSON JWT headers/claims; never print a matched token.
# The signature need not verify: the guard flags plausible leaked credentials,
# not whether the credential is currently accepted by Supabase.
JWT_CANDIDATE = re.compile(
    r"(?<![A-Za-z0-9_-])"
    r"(eyJ[A-Za-z0-9_-]{16,1024})\."
    r"(eyJ[A-Za-z0-9_-]{16,8192})\."
    r"([A-Za-z0-9_-]{16,2048})"
    r"(?![A-Za-z0-9_-])"
)
PRIVILEGED_JWT_ROLES = frozenset({"service_role", "supabase_admin", "postgres"})


def _jwt_json_segment(segment: str) -> dict[str, object] | None:
    try:
        raw = base64.b64decode(
            segment + "=" * (-len(segment) % 4),
            altchars=b"-_",
            validate=True,
        )
        parsed = json.loads(raw)
    except (binascii.Error, ValueError, UnicodeDecodeError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def leaked_privileged_jwt_positions(source: str) -> list[int]:
    """Byte-safe positions for high-privilege JWTs; excludes public anon JWTs."""
    found: list[int] = []
    for match in JWT_CANDIDATE.finditer(source):
        header = _jwt_json_segment(match.group(1))
        claims = _jwt_json_segment(match.group(2))
        if not header or not claims:
            continue
        alg = header.get("alg")
        if not isinstance(alg, str) or alg not in {
            "HS256", "HS384", "HS512", "RS256", "RS384", "RS512",
            "ES256", "ES384", "ES512", "EdDSA",
        }:
            continue
        role = claims.get("role")
        if isinstance(role, str) and role in PRIVILEGED_JWT_ROLES:
            found.append(match.start())
    return found


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ['git', 'ls-files', '-z'],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [ROOT / item.decode('utf-8') for item in result.stdout.split(b'\0') if item]


def is_forbidden_env_file(path: Path) -> bool:
    name = path.name.lower()
    return name.startswith('.env') and name not in ALLOWED_ENV_FILES


def read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return None
        raw = path.read_bytes()
    except (OSError, PermissionError):
        return None
    if b'\0' in raw:
        return None
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return None


def inspect_file(path: Path, rel: Path) -> list[str]:
    """Refuser tout fichier texte suivi qui n'a pas pu être inspecté."""
    if is_forbidden_env_file(path):
        return [f'{rel}: fichier d’environnement réel versionné']
    # Un lien suivi par Git peut pointer hors du dépôt ou vers une source
    # non contrôlée par la PR. Refuser ce type d'entrée AVANT stat()/read().
    if path.is_symlink():
        return [f'{rel}: lien symbolique suivi interdit dans le garde secrets']

    must_scan = path.suffix.lower() in MANDATORY_TEXT_EXTENSIONS or path.name in MANDATORY_TEXT_NAMES
    try:
        size = path.stat().st_size
    except (OSError, PermissionError):
        return [f'{rel}: fichier suivi illisible'] if must_scan else []

    if must_scan and size > MAX_TEXT_BYTES:
        return [f'{rel}: fichier texte trop volumineux pour inspection complète ({size} octets)']

    content = read_text(path)
    if content is None:
        return [f'{rel}: fichier texte impossible à inspecter (binaire, encodage ou erreur)'] if must_scan else []

    findings: list[str] = []
    for label, pattern in SECRET_PATTERNS:
        match = pattern.search(content)
        if match:
            line = content.count('\n', 0, match.start()) + 1
            findings.append(f'{rel}:{line}: {label}')
    # Validate encoded JWT claims rather than relying on a key's variable name.
    # Only privileged roles are flagged: public Supabase anon/publishable
    # credentials can appear intentionally in client-side configuration.
    for position in leaked_privileged_jwt_positions(content):
        line = content.count('\n', 0, position) + 1
        findings.append(f'{rel}:{line}: Supabase privileged JWT credential')

    return findings


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        findings.extend(inspect_file(path, path.relative_to(ROOT)))

    if findings:
        print('ECHEC: secret potentiel ou fichier non inspecté dans les fichiers suivis par Git.')
        for finding in findings:
            print(f'- {finding}')
        print('Retirez/révoquez tout secret exposé et rendez les fichiers source inspectables avant fusion.')
        return 1

    print('OK: fichiers sources inspectés; aucun fichier .env réel ni motif de secret critique détecté.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
