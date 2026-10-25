#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CHUNK_BYTES = 64 * 1024
OVERLAP_BYTES = 8 * 1024
# L'ancien contrôle ignorait silencieusement tous les fichiers > 2 Mio.
# Scanner en flux, même les binaires : un secret ASCII peut y être intégré.
ALLOWED_ENV_FILES = {'.env.example', '.env.sample', '.env.template'}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ('Supabase secret key', re.compile(r'\bsb_secret_[A-Za-z0-9._-]{20,}\b')),
    ('GitHub classic token', re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b')),
    ('GitHub fine-grained token', re.compile(r'\bgithub_pat_[A-Za-z0-9_]{30,}\b')),
    ('Stripe live secret key', re.compile(r'\bsk_live_[A-Za-z0-9]{20,}\b')),
    ('Stripe restricted key', re.compile(r'\brk_live_[A-Za-z0-9]{20,}\b')),
    ('AWS access key identifier', re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b')),
    ('Google API key', re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b')),
    ('GitLab access token', re.compile(r'\bglpat-[A-Za-z0-9_-]{20,}\b')),
    ('OpenAI project/service token', re.compile(r'\bsk-(?:proj|svcacct)-[A-Za-z0-9_-]{24,}\b')),
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


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Lire tout fichier suivi par Git, même > 2 Mio, sans charger son corps.

    Un décodage ASCII à remplacement garde un caractère par octet; les
    octets binaires ne masquent donc pas les frontières des identifiants.
    Le chevauchement détecte les clés coupées entre deux blocs. Rien de
    secret (ni fragment du match) n'est imprimé dans les logs Actions.
    """
    findings: list[tuple[int, str]] = []
    seen: set[str] = set()
    tail = b''
    lines_before_tail = 0
    with path.open('rb') as file:
        while chunk := file.read(CHUNK_BYTES):
            window = tail + chunk
            # Latin-1 seul interprète \xff comme une lettre (\b Unicode),
            # masquant une clé ASCII contiguë à des octets binaires.
            text = window.decode('ascii', errors='replace')
            for label, expression in SECRET_PATTERNS:
                if label in seen:
                    continue
                for match in expression.finditer(text):
                    # Ne pas signaler deux fois une clé dans le chevauchement.
                    if match.end() <= len(tail):
                        continue
                    findings.append((
                        lines_before_tail + window.count(b'\n', 0, match.start()) + 1,
                        label,
                    ))
                    seen.add(label)
                    break
            tail_length = min(OVERLAP_BYTES, len(window))
            lines_before_tail += window[:-tail_length].count(b'\n')
            tail = window[-tail_length:]
    return findings


def self_test() -> None:
    assert CHUNK_BYTES > OVERLAP_BYTES >= 4096
    with tempfile.TemporaryDirectory() as temp:
        sample = Path(temp) / 'large.test'
        # Clé synthétique découpée entre deux lectures et située APRÈS 2 Mio.
        fake_gh = 'gh' + 'p_' + 'Q' * 36
        fake_stripe = 'rk_' + 'live_' + 'X' * 25
        fake_aws = 'AK' + 'IA' + 'K' * 16
        fake_google = 'AI' + 'za' + 'A' * 35
        sample.write_bytes(
            b'noise\n' + b'a' * (2 * 1024 * 1024 + CHUNK_BYTES - 20)
            + b'\n' + fake_gh.encode('ascii') + b'\n'
            + fake_stripe.encode('ascii') + b'\n'
            + fake_aws.encode('ascii') + b'\n'
            + fake_google.encode('ascii') + b'\n'
        )
        labels = {label for _line, label in scan_file(sample)}
        assert {'GitHub classic token', 'Stripe restricted key',
                'AWS access key identifier', 'Google API key'} <= labels, labels
        # Un octet NUL ou un caractère UTF-8 invalide ne masque pas le secret.
        sample.write_bytes(b'\x00\xff' + fake_gh.encode('ascii'))
        assert scan_file(sample) == [(1, 'GitHub classic token')]
        sample.write_bytes(b'placeholder with no credentials\n')
        assert not scan_file(sample)
        assert is_forbidden_env_file(Path('secrets/.env.production'))
        assert not is_forbidden_env_file(Path('.env.example'))
    print('OK garde secrets : gros fichiers, frontières de blocs, binaire,'
          ' NUL, formats cloud et absence de faux positifs.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    findings: list[str] = []
    scanned = 0
    for path in tracked_files():
        # Échapper le nom : pas d'injection de séquences de contrôle dans Actions.
        rel = path.relative_to(ROOT).as_posix().encode('unicode_escape').decode('ascii')
        if is_forbidden_env_file(path):
            findings.append(f'{rel}: fichier d’environnement réel versionné')
            continue
        if path.is_symlink():
            findings.append(f'{rel}: lien symbolique suivi par Git interdit')
            continue
        try:
            hits = scan_file(path)
            scanned += 1
        except (OSError, PermissionError):
            # Ne pas assimiler un fichier illisible ou disparu à un fichier sûr.
            findings.append(f'{rel}: fichier suivi non analysable')
            continue
        for line, label in hits:
            findings.append(f'{rel}:{line}: {label}')
    if findings:
        print('ECHEC : secrets potentiels ou fichiers non vérifiables détectés.')
        for finding in findings:
            print('- ' + finding)
        print('Retirer et révoquer les identifiants exposés; refaire l’audit.')
        return 1
    print(f'OK : {scanned} fichiers suivis inspectés intégralement,'
          ' aucun secret critique ni fichier .env réel détecté.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
