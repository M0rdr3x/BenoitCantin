#!/usr/bin/env python3
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / 'scripts' / 'build_supabase_production_workspace.py'


def git_blob_sha1(data: bytes) -> str:
    header = f'blob {len(data)}\0'.encode('ascii')
    return hashlib.sha1(header + data).hexdigest()


class ReviewedProductionMigrationBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sinjira-reviewed-batch-test-')
        self.root = Path(self.tmp.name)
        self.scripts = self.root / 'scripts'
        self.supabase = self.root / 'supabase'
        self.migrations = self.supabase / 'migrations'
        self.scripts.mkdir(parents=True)
        self.migrations.mkdir(parents=True)
        shutil.copy2(BUILDER, self.scripts / BUILDER.name)
        (self.supabase / 'production-migration-ledger.txt').write_text(
            '20260101000000 baseline\n',
            encoding='utf-8',
        )
        (self.supabase / 'config.toml').write_text('project_id = "test"\n', encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def write_migration(self, version, name, text='select 1;\n'):
        path = self.migrations / f'{version}_{name}.sql'
        path.write_text(text, encoding='utf-8')
        return path

    def write_batch(self, rows):
        lines = ['# lot de test']
        for version, name, blob_sha in rows:
            lines.append(f'{version} {name} {blob_sha}')
        (self.supabase / 'production-reviewed-migration-batch.txt').write_text(
            '\n'.join(lines) + '\n',
            encoding='utf-8',
        )

    def run_builder(self):
        out = self.root / '.prod-workspace' / 'supabase'
        proc = subprocess.run(
            [sys.executable, str(self.scripts / BUILDER.name), '--output', str(out)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        return proc, out

    @staticmethod
    def output(proc):
        return (proc.stdout or '') + (proc.stderr or '')

    def test_valid_reviewed_batch_is_accepted(self):
        version = '20260102000000'
        name = 'future_reviewed'
        content = b'select 1;\n'
        self.write_migration(version, name, content.decode())
        self.write_batch([(version, name, git_blob_sha1(content))])

        proc, out = self.run_builder()

        self.assertEqual(proc.returncode, 0, self.output(proc))
        self.assertTrue((out / 'migrations' / f'{version}_{name}.sql').is_file())
        marker = (out / 'migrations' / '20260101000000_baseline.sql').read_text('utf-8')
        self.assertIn('Marqueur de déploiement lié uniquement', marker)

    def test_unreviewed_future_migration_is_rejected(self):
        first_version = '20260102000000'
        first_name = 'future_reviewed'
        first_content = b'select 1;\n'
        self.write_migration(first_version, first_name, first_content.decode())
        self.write_batch([(first_version, first_name, git_blob_sha1(first_content))])
        self.write_migration('20260103000000', 'future_not_reviewed', 'select 2;\n')

        proc, _ = self.run_builder()

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('non revue(s): 20260103000000_future_not_reviewed.sql', self.output(proc))

    def test_modified_reviewed_migration_is_rejected(self):
        version = '20260102000000'
        name = 'future_reviewed'
        original = b'select 1;\n'
        path = self.write_migration(version, name, original.decode())
        self.write_batch([(version, name, git_blob_sha1(original))])
        path.write_text('select 999;\n', encoding='utf-8')

        proc, _ = self.run_builder()

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('Contenu de migration modifié depuis la revue', self.output(proc))

    def test_missing_reviewed_migration_is_rejected(self):
        version = '20260102000000'
        name = 'future_missing'
        self.write_batch([(version, name, '0' * 40)])

        proc, _ = self.run_builder()

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('attendue(s) absente(s): 20260102000000_future_missing.sql', self.output(proc))

    def test_reviewed_version_at_or_before_ledger_cutoff_is_rejected(self):
        self.write_batch([('20260101000000', 'already_applied', '0' * 40)])

        proc, _ = self.run_builder()

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('déjà couverte par le ledger production', self.output(proc))


if __name__ == '__main__':
    unittest.main(verbosity=2)
