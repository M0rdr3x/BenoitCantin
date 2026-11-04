#!/usr/bin/env python3
"""Tests de confinement en mémoire locale; aucune connexion à la production."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import build_supabase_production_workspace as builder

ROOT = Path(__file__).resolve().parents[1]
SUPABASE = ROOT / 'supabase'
QUARANTINED = ('security-context', 'nova-civic-poll')


def make_workspace(root: Path) -> Path:
    out = root / 'supabase'
    (out / 'functions').mkdir(parents=True)
    shutil.copy2(SUPABASE / 'config.toml', out / 'config.toml')
    shutil.copy2(SUPABASE / 'NOVA_POLL_SCHEMA_PREDEPLOY.sql',
                 out / 'NOVA_POLL_SCHEMA_PREDEPLOY.sql')
    for slug in QUARANTINED:
        shutil.copytree(SUPABASE / 'functions' / slug, out / 'functions' / slug)
    keep = out / 'functions' / 'other-private-function'
    keep.mkdir()
    (keep / 'index.ts').write_text('// Function test preserved', encoding='utf-8')
    return out


class DeploymentQuarantineTests(unittest.TestCase):
    def test_two_sensitive_functions_are_excluded_without_touching_sources(self):
        with tempfile.TemporaryDirectory(prefix='edge-release-test-') as tmp:
            workspace = make_workspace(Path(tmp))
            original_source = (SUPABASE / 'functions/security-context/index.ts').read_bytes()
            quarantined = builder.quarantine_unreviewed_edge_deploys(workspace)
            self.assertEqual(quarantined, QUARANTINED)
            for slug in QUARANTINED:
                self.assertFalse((workspace / 'functions' / slug).exists())
                self.assertNotIn(f'[functions.{slug}]', (workspace / 'config.toml').read_text('utf-8'))
            self.assertFalse((workspace / 'NOVA_POLL_SCHEMA_PREDEPLOY.sql').exists())
            self.assertTrue((workspace / 'functions/other-private-function/index.ts').is_file())
            self.assertEqual(original_source, (SUPABASE / 'functions/security-context/index.ts').read_bytes())

    def test_missing_or_incomplete_source_is_rejected(self):
        for slug in QUARANTINED:
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as tmp:
                workspace = make_workspace(Path(tmp))
                (workspace / 'functions' / slug / 'index.ts').unlink()
                with self.assertRaises(SystemExit):
                    builder.quarantine_unreviewed_edge_deploys(workspace)

    def test_changed_jwt_settings_are_rejected(self):
        for slug, old, new in (
            ('security-context', '[functions.security-context]\nverify_jwt = true',
             '[functions.security-context]\nverify_jwt = false'),
            ('nova-civic-poll', '[functions.nova-civic-poll]\nverify_jwt = false',
             '[functions.nova-civic-poll]\nverify_jwt = true'),
        ):
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as tmp:
                workspace = make_workspace(Path(tmp))
                config = workspace / 'config.toml'
                source = config.read_text('utf-8')
                self.assertIn(old, source)
                config.write_text(source.replace(old, new, 1), encoding='utf-8')
                with self.assertRaises(SystemExit):
                    builder.quarantine_unreviewed_edge_deploys(workspace)

    def test_mismatched_auth_rpc_and_public_captcha_are_rejected(self):
        for slug, marker in (
            ('security-context', 'service_security_evaluate_context_session'),
            ('nova-civic-poll', 'if(!await confirmCaptcha(payload.captchaToken))'),
        ):
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as tmp:
                workspace = make_workspace(Path(tmp))
                entry = workspace / 'functions' / slug / 'index.ts'
                source = entry.read_text('utf-8')
                self.assertIn(marker, source)
                entry.write_text(source.replace(marker, 'REMOVED_BY_TEST', 1), encoding='utf-8')
                with self.assertRaises(SystemExit):
                    builder.quarantine_unreviewed_edge_deploys(workspace)

    def test_missing_nova_sql_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = make_workspace(Path(tmp))
            (workspace / 'NOVA_POLL_SCHEMA_PREDEPLOY.sql').unlink()
            with self.assertRaises(SystemExit):
                builder.quarantine_unreviewed_edge_deploys(workspace)

    def test_source_tree_symlink_is_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'supabase-source'
            source.mkdir()
            target = Path(tmp) / 'fixture.txt'
            target.write_text('synthetic private marker', encoding='utf-8')
            (source / 'unexpected.txt').symlink_to(target)
            with self.assertRaises(SystemExit):
                builder.reject_source_symlinks(source)

    def test_normal_source_tree_is_accepted(self):
        builder.reject_source_symlinks(SUPABASE)

    def test_symlinked_function_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = make_workspace(Path(tmp))
            folder = workspace / 'functions' / 'security-context'
            shutil.rmtree(folder)
            folder.symlink_to(SUPABASE / 'functions' / 'security-context', target_is_directory=True)
            with self.assertRaises(SystemExit):
                builder.quarantine_unreviewed_edge_deploys(workspace)
            self.assertTrue((SUPABASE / 'functions/security-context/index.ts').is_file())


if __name__ == '__main__':
    unittest.main(verbosity=2)
