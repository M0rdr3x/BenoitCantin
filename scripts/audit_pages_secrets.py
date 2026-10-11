#!/usr/bin/env python3
"""Audit des secrets du site STATIQUE produit par Jekyll, avant tout upload.

Réutilise les motifs Git éprouvés sans imprimer une valeur de secret.
Refuse les fichiers textes trop volumineux ou non lisibles au lieu de les
ignorer silencieusement. Aucune requête réseau, aucune publication.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from validate_no_committed_secrets import SECRET_PATTERNS

MAX_TEXT_BYTES = 8 * 1024 * 1024
TEXT_SUFFIXES = frozenset({
    '.html', '.htm', '.js', '.mjs', '.css', '.json', '.csv', '.txt', '.xml',
    '.md', '.svg', '.webmanifest', '.map', '.yaml', '.yml', '.toml',
})
EXTRA_TEXT_NAMES = frozenset({'CNAME', 'robots.txt', 'humans.txt', 'ads.txt'})


def audit(built: Path) -> list[str]:
    if not built.is_dir():
        return ["Artefact Jekyll absent"]
    errors: list[str] = []
    for file in built.rglob('*'):
        if file.is_symlink():
            errors.append(f"Lien symbolique interdit dans l'artefact: {file.relative_to(built)}")
            continue
        if not file.is_file():
            continue
        if file.suffix.lower() not in TEXT_SUFFIXES and file.name not in EXTRA_TEXT_NAMES:
            continue
        rel = file.relative_to(built).as_posix()
        try:
            if file.stat().st_size > MAX_TEXT_BYTES:
                errors.append(f"Fichier texte non auditable (taille excessive): {rel}")
                continue
            content = file.read_text('utf-8-sig')
        except (OSError, UnicodeError):
            errors.append(f"Fichier texte non auditable: {rel}")
            continue
        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(content)
            if match is not None:
                # Jamais de substring ni de token dans les logs GitHub Actions.
                line = content.count('\n', 0, match.start()) + 1
                errors.append(f"Secret potentiellement publié: {rel}:{line} ({label})")
    return errors


def self_test() -> None:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        public = root / 'index.html'
        public.write_text('<!doctype html><title>SINJIRA</title>', 'utf-8')
        (root / 'public.json').write_text('{"status":"public"}', 'utf-8')
        image = root / 'visual.webp'
        image.write_bytes(b'\x00\x01\x02')
        assert not audit(root), audit(root)

        # Les clés de test sont fabriquées localement pour éviter d'insérer
        # une chaîne ressemblant à une véritable clé dans le dépôt source.
        for secret in ('ghp_' + 'A' * 40, 'sb_secret_' + 'B' * 28,
                       'sk_live_' + 'C' * 30,
                       '-----BEGIN PRIVATE KEY-----'):
            public.write_text('<!-- ' + secret + ' -->', 'utf-8')
            issues = audit(root)
            assert any('index.html' in issue and 'Secret' in issue
                       for issue in issues), "Secret statique non détecté"
            assert all(secret not in issue for issue in issues), (
                "Valeur confidentielle affichée dans les erreurs"
            )
        public.write_text('<!doctype html><title>SINJIRA</title>', 'utf-8')
        public.write_bytes(b'\xff\xfe')
        assert any('non auditable' in issue for issue in audit(root)), (
            "Contenu texte UTF-8 invalide accepté"
        )
        public.write_text('ok', 'utf-8')
        assert not audit(root), audit(root)
    print("OK secrets artefact Pages : motifs Git, fichiers générés, "
          "échec fermé et logs sans valeurs sensibles")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--built')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.built:
        parser.error('--built requis sans --self-test')
    errors = audit(Path(args.built).resolve())
    if errors:
        print(f'ERREUR : {len(errors)} problème(s) dans l\'artefact public', file=sys.stderr)
        for issue in errors:
            print('- ' + issue, file=sys.stderr)
        return 1
    print("OK : aucun motif de secret critique détecté dans les fichiers publics Jekyll")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
