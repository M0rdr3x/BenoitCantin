#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MAX_TEXT_BYTES = 2 * 1024 * 1024
ALLOWED_ENV_FILES = {'.env.example', '.env.sample', '.env.template'}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ('Supabase secret key', re.compile(r'\bsb_secret_[A-Za-z0-9._-]{20,}\b')),
    ('GitHub classic token', re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b')),
    ('GitHub fine-grained token', re.compile(r'\bgithub_pat_[A-Za-z0-9_]{30,}\b')),
    ('Stripe live secret key', re.compile(r'\bsk_live_[A-Za-z0-9]{20,}\b')),
    ('Private key block', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
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


def main() -> int:
    findings: list[str] = []

    for path in tracked_files():
        rel = path.relative_to(ROOT)
        if is_forbidden_env_file(path):
            findings.append(f'{rel}: fichier d’environnement réel versionné')
            continue

        text = read_text(path)
        if text is None:
            continue

        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if match:
                line = text.count('\n', 0, match.start()) + 1
                findings.append(f'{rel}:{line}: {label}')

    if findings:
        print('ECHEC: secret potentiel détecté dans les fichiers suivis par Git.')
        for finding in findings:
            print(f'- {finding}')
        print('Retirez le secret du dépôt, révoquez/renouvelez la valeur exposée, puis relancez la validation.')
        return 1

    print('OK: aucun fichier .env réel ni motif de secret critique détecté dans les fichiers suivis.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
