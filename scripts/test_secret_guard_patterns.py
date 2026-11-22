#!/usr/bin/env python3
"""Tests de mutation sans vrais secrets ni réseau pour le garde Git."""
from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path

from scripts import validate_no_committed_secrets as guard


def detected_names(source: str) -> set[str]:
    return {name for name, pattern in guard.SECRET_PATTERNS if pattern.search(source)}


class SecretGuardTests(unittest.TestCase):
    def test_cloud_and_deployment_credentials_are_caught(self):
        for name in (
            'NETLIFY_AUTH_TOKEN', 'CLOUDFLARE_API_TOKEN',
            'TURNSTILE_SECRET_KEY', 'SUPABASE_ACCESS_TOKEN',
        ):
            with self.subTest(name=name):
                sample = name + ' = "' + ('a' * 40) + '"'
                self.assertIn('Deployment or anti-bot secret assignment', detected_names(sample))

    def test_real_token_prefixes_are_caught(self):
        for token in (
            'sk-proj-' + ('a' * 32),
            'AKIA' + ('A' * 16),
            'glpat-' + ('a' * 32),
        ):
            with self.subTest(prefix=token[:4]):
                self.assertTrue(detected_names(token))

    def test_environment_references_are_not_secrets(self):
        for sample in (
            'NETLIFY_AUTH_TOKEN = process.env.NETLIFY_AUTH_TOKEN',
            'SUPABASE_ACCESS_TOKEN: ' + '$' + '{{ secrets.SUPABASE_ACCESS_TOKEN }}',
            'TURNSTILE_SECRET_KEY = Deno.env.get("TURNSTILE_SECRET_KEY")',
            'CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")',
        ):
            with self.subTest(sample=sample):
                self.assertNotIn('Deployment or anti-bot secret assignment', detected_names(sample))

    @staticmethod
    def synthetic_jwt(role: str, algorithm: str = 'HS256') -> str:
        """Dummy segments: recognizable JWT structure, NEVER a signed credential."""
        def encode(data: object) -> str:
            payload = json.dumps(data, separators=(',', ':')).encode('utf-8')
            return base64.urlsafe_b64encode(payload).rstrip(b'=').decode('ascii')

        header = encode({'alg': algorithm, 'typ': 'JWT'})
        claims = encode({'iss': 'synthetic-test', 'role': role, 'sub': 'fake-user'})
        signature = 'A' * 43
        return '.'.join((header, claims, signature))

    def test_unlabelled_privileged_jwts_are_caught_without_leaking_them(self):
        for role in ('service_role', 'supabase_admin', 'postgres'):
            with self.subTest(role=role):
                dummy = self.synthetic_jwt(role)
                self.assertEqual(len(guard.leaked_privileged_jwt_positions(
                    'const header = "Bearer ' + dummy + '";'
                )), 1)
                with tempfile.TemporaryDirectory() as d:
                    path = Path(d) / 'client.ts'
                    path.write_text('let value = "' + dummy + '";\n', encoding='utf-8')
                    findings = guard.inspect_file(path, Path('client.ts'))
                    self.assertEqual(len(findings), 1)
                    self.assertIn('Supabase privileged JWT credential', findings[0])
                    self.assertNotIn(dummy, findings[0])
                    self.assertNotIn(role, findings[0])

    def test_public_jwt_and_dummy_or_invalid_tokens_do_not_flag(self):
        for role in ('anon', 'authenticated', 'user', ''):
            with self.subTest(role=role):
                self.assertEqual(guard.leaked_privileged_jwt_positions(
                    self.synthetic_jwt(role)
                ), [])
        for sample in (
            'eyJbm90Ijoiand0In0.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.invalid',
            self.synthetic_jwt('service_role', algorithm='none'),
            '.'.join((
                base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b'=').decode(),
                base64.urlsafe_b64encode(b'{"role":[],"iss":"synthetic-test"}').rstrip(b'=').decode(),
                'A' * 43,
            )),
            self.synthetic_jwt('service_role').replace('.', '-', 1),
            self.synthetic_jwt('service_role').split('.', 1)[0] + '.not_json.' + 'A' * 43,
        ):
            with self.subTest(sample=sample[:16]):
                self.assertEqual(guard.leaked_privileged_jwt_positions(sample), [])

    def test_privileged_jwt_on_subsequent_line_reports_only_location(self):
        dummy = self.synthetic_jwt('service_role')
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / 'notes.md'
            file.write_text('Public docs\n' + dummy + '\n', encoding='utf-8')
            issues = guard.inspect_file(file, Path('notes.md'))
            self.assertEqual(len(issues), 1)
            self.assertTrue(issues[0].startswith('notes.md:2:'))
            self.assertNotIn(dummy, issues[0])

    def test_large_text_is_rejected_instead_of_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'large.sql'
            path.write_bytes(b'x' * (guard.MAX_TEXT_BYTES + 1))
            result = guard.inspect_file(path, Path('large.sql'))
            self.assertTrue(any('trop volumineux' in warning for warning in result))

    def test_unreadable_text_and_real_env_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / 'unreadable.json'
            bad.write_bytes(b'\xff\xfe')
            self.assertTrue(guard.inspect_file(bad, Path('unreadable.json')))
            env = Path(d) / '.env.production'
            env.write_text('DUMMY=1', encoding='utf-8')
            self.assertTrue(guard.inspect_file(env, Path('.env.production')))

    def test_symlink_is_rejected_before_reading_its_target(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / 'fake-private.txt'
            target.write_text('synthetic content', encoding='utf-8')
            tracked = root / 'tracked.js'
            tracked.symlink_to(target)
            findings = guard.inspect_file(tracked, Path('tracked.js'))
            self.assertTrue(any('lien symbolique' in item for item in findings))
            self.assertEqual(target.read_text(encoding='utf-8'), 'synthetic content')

    def test_big_binary_file_is_not_treated_as_text(self):
        with tempfile.TemporaryDirectory() as d:
            image = Path(d) / 'image.png'
            image.write_bytes(b'\x00' * (guard.MAX_TEXT_BYTES + 1))
            self.assertEqual(guard.inspect_file(image, Path('image.png')), [])


if __name__ == '__main__':
    unittest.main()
