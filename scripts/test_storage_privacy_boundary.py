#!/usr/bin/env python3
"""Tests de mutations négatives; aucune donnée ni connexion de production."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_storage_privacy_boundary import (  # noqa: E402
    PRIVATE, PUBLIC, ALL_EXPECTED, EXPECTED_FLAGS, PRODUCTION_ONLY_BUCKETS,
    QUERY, migration_errors, repository_errors, validate_snapshot,
)


def fixture_migrations() -> dict[str, str]:
    return {
        "001.sql": "\n".join(
            ("INSERT INTO storage.buckets(id,name,public) VALUES "
             f"('{name}','{name}',false) ON CONFLICT(id) DO UPDATE SET public=false;")
            for name in sorted(PRIVATE)
        ),
        "002.sql": (
            "INSERT INTO storage.buckets(id,name,public) VALUES "
            "('sinjira-avatars','sinjira-avatars',true) "
            "ON CONFLICT(id) DO UPDATE SET public=true;"
        ),
    }


class StoragePrivacyBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good = fixture_migrations()

    def test_repository_current_state_passes(self):
        self.assertEqual(repository_errors(), [])

    def test_known_5_buckets_4_private_1_public(self):
        self.assertEqual(len(ALL_EXPECTED), 5)
        self.assertEqual(len(PRIVATE), 4)
        self.assertEqual(PUBLIC, {"sinjira-avatars"})
        self.assertEqual(migration_errors(self.good), [])

    def test_externally_provisioned_bucket_not_implicitly_public(self):
        self.assertEqual(PRODUCTION_ONLY_BUCKETS, {"sinjira-character-submissions"})
        self.assertTrue(PRODUCTION_ONLY_BUCKETS <= PRIVATE)
        changed = {**self.good, "003.sql":
            "UPDATE storage.buckets SET public=true WHERE id='sinjira-character-submissions';"}
        self.assertTrue(migration_errors(changed))

    def test_reject_private_bucket_became_public(self):
        for name in PRIVATE:
            with self.subTest(bucket=name):
                source = self.good["001.sql"]
                mutated = source.replace(f"('{name}','{name}',false)",
                                         f"('{name}','{name}',true)")
                self.assertTrue(migration_errors({**self.good, "001.sql": mutated}))

    def test_reject_private_bucket_changed_by_update(self):
        mutated = dict(self.good)
        mutated["003.sql"] = (
            "UPDATE storage.buckets SET public=true "
            "WHERE id='sinjira-private-documents';"
        )
        self.assertTrue(migration_errors(mutated))

    def test_reject_new_public_bucket(self):
        mutated = dict(self.good)
        mutated["003.sql"] = (
            "INSERT INTO storage.buckets(id,name,public) VALUES "
            "('sinjira-secret-export','sinjira-secret-export',true);"
        )
        self.assertTrue(migration_errors(mutated))

    def test_reject_new_private_bucket_without_explicit_review(self):
        mutated = dict(self.good)
        mutated["003.sql"] = (
            "INSERT INTO storage.buckets(id,name,public) VALUES "
            "('sinjira-unreviewed','sinjira-unreviewed',false);"
        )
        self.assertTrue(migration_errors(mutated))

    def test_reject_missing_baseline_bucket(self):
        mutated = dict(self.good)
        mutated["001.sql"] = mutated["001.sql"].replace("sinjira-life-story-exports", "deleted-private-bucket")
        self.assertTrue(migration_errors(mutated))

    def test_reject_empty_or_missing_repository(self):
        self.assertTrue(migration_errors({}))
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(repository_errors(Path(tmp)))

    def test_valid_snapshot_requires_all_true(self):
        good = [{key: True for key in EXPECTED_FLAGS}]
        self.assertEqual(validate_snapshot(good), [])

    def test_denies_bad_snapshots(self):
        cases = (
            [],
            {},
            None,
            [{key: "true" for key in EXPECTED_FLAGS}],
            [{key: 1 for key in EXPECTED_FLAGS}],
            [{key: None for key in EXPECTED_FLAGS}],
            [{key: True for key in EXPECTED_FLAGS}, {"extra": True}],
            [{**{key: True for key in EXPECTED_FLAGS}, "extra": True}],
        )
        for bad in cases:
            with self.subTest(snapshot=repr(bad)[:90]):
                self.assertTrue(validate_snapshot(bad))

    def test_denies_each_failed_boundary(self):
        for field in EXPECTED_FLAGS:
            with self.subTest(field=field):
                payload = {key: True for key in EXPECTED_FLAGS}
                payload[field] = False
                self.assertIn(field, " ".join(validate_snapshot([payload])))

    def test_query_only_reads_metadata_and_has_expected_flags(self):
        self.assertTrue(QUERY.upper().startswith("SELECT"))
        for field in EXPECTED_FLAGS:
            self.assertIn(field, QUERY)
        for marker in ("storage.buckets", "storage' AND c.relname = 'objects'", "NOT public"):
            self.assertIn(marker, QUERY)
        for disallowed in ("storage.objects o", "o.name", "auth.users", "SELECT *", "INSERT ", "UPDATE ", "DELETE ", "COPY "):
            self.assertNotIn(disallowed, QUERY)
        self.assertNotIn(";", QUERY)

    def test_private_migration_does_not_expose_user_values(self):
        fail = migration_errors({**self.good, "003.sql":
            "UPDATE storage.buckets SET public=true WHERE id='sinjira-life-story-exports';"})
        self.assertTrue(fail)
        self.assertNotIn("private-user-name", "\n".join(fail))


if __name__ == "__main__":
    unittest.main(verbosity=2)
