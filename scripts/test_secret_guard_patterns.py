#!/usr/bin/env python3
"""Tests de mutation sans vrais secrets ni réseau pour le garde Git."""
from __future__ import annotations

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


    def test_sensitive_credential_files_are_never_committed(self):
        # Filenames can identify private credentials without reading bytes.
        # No actual secrets, tokens or credentials are included in tests.
        for filename in (
            "tls/key.pem", "tls/secret.key", "tls/store.p12",
            "tls/store.pfx", "tls/store.jks", "tls/store.keystore",
            "passwords.kdbx", ".npmrc", ".pypirc", ".netrc",
            ".git-credentials", ".ssh/id_rsa", ".ssh/id_dsa",
            ".ssh/id_ecdsa", ".ssh/id_ed25519",
            "sub/.aws/credentials", "sub/.docker/config.json",
            "sub/.kube/config",
        ):
            with self.subTest(path=filename):
                self.assertTrue(guard.is_forbidden_credential_file(Path(filename)))
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / filename
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(b"\x00\xffsynthetic")
                    self.assertTrue(guard.inspect_file(p, Path(filename)))

    def test_approved_public_and_sample_files_remain_allowed(self):
        for filename in (
            ".env.example", ".env.sample", ".env.template",
            "assets/certificate.svg", "assets/js/site.js",
            "docs/how-to-secure-keys.md", "assets/favicon.png",
        ):
            with self.subTest(path=filename):
                self.assertFalse(guard.is_forbidden_credential_file(Path(filename)))
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / filename
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text("only synthetic benign content", encoding="utf-8")
                    self.assertEqual(guard.inspect_file(p, Path(filename)), [])

    def test_additional_private_key_headers_and_access_tokens(self):
        for payload, expected in (
            ("-----BEGIN " + "ENCRYPTED PRIVATE KEY-----", "Private key block"),
            ("-----BEGIN " + "DSA PRIVATE KEY-----", "Private key block"),
            ("-----BEGIN PGP " + "PRIVATE KEY BLOCK-----", "PGP private key block"),
            ("npm_" + ("a" * 36), "npm access token"),
            ("xoxb-" + ("a" * 45), "Slack access token"),
        ):
            with self.subTest(kind=expected):
                self.assertIn(expected, detected_names(payload))

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
