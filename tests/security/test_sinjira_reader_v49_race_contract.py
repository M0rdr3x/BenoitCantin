"""SINJIRA V49 — preuve locale d'un conflit d'écritures du MÊME compte.

Aucun appel réseau, secret, vrai lecteur, PDF ou base de production.
La preuve d'un risque n'est pas un certificat d'aptitude à lancer le service.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "tests/security/sql"
FIXTURE = ROOT / "tests/security/sql/setup_sinjira_reader_v48.sql"
CLIENT = ROOT / "assets/js/sinjira-liseuse-v26.js"
STAGES = [
    DIR / "test_sinjira_reader_v49_device_a_start.sql",
    DIR / "test_sinjira_reader_v49_device_b_fresh.sql",
    DIR / "test_sinjira_reader_v49_device_a_stale_arrives.sql",
]
FAKE_OWNER = "00000000-0000-0000-0000-000000000001"
FAKE_BOOK = "10000000-0000-0000-0000-000000000001"
B_TIME = "2026-11-09T13:05:00Z"
A_TIME = "2026-11-09T13:00:00Z"


class SameAccountOutOfOrderWriteProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = FIXTURE.read_text(encoding="utf-8")
        cls.steps = [p.read_text(encoding="utf-8") for p in STAGES]
        cls.client = CLIENT.read_text(encoding="utf-8")

    def test_original_v32_migration_runs_only_in_disposable_fixture(self):
        self.assertIn(
            r"\i supabase/migrations/20261107185500_sinjira_reader_progress_spot_v32.sql",
            self.fixture,
        )
        self.assertIn("CREATE TABLE public.sinjira_reader_library", self.fixture)
        self.assertIn("ENABLE ROW LEVEL SECURITY", self.fixture)
        self.assertIn("JAMAIS PRODUCTION", self.fixture)

    def test_a_and_b_are_TWO_devices_of_SAME_fake_owner_not_two_different_owners(self):
        for source in self.steps:
            self.assertIn("SET ROLE authenticated;", source)
            self.assertIn(FAKE_OWNER, source)
            self.assertIn(r"\set ON_ERROR_STOP on", source)
        self.assertNotIn("00000000-0000-0000-0000-000000000002", "\n".join(self.steps))

    def test_newer_b_arrives_before_delayed_a(self):
        self.assertIn(B_TIME, self.steps[1])
        self.assertIn(A_TIME, self.steps[2])
        self.assertLess(A_TIME, B_TIME)
        self.assertIn("last_page=31", self.steps[1])
        self.assertIn("last_page=12", self.steps[2])
        self.assertIn("scroll_ratio=0.8123", self.steps[1])
        self.assertIn("scroll_ratio=0.2100", self.steps[2])

    def test_scenario_reuses_actual_unconditional_upsert_shape(self):
        for sql in self.steps[1:]:
            self.assertIn("ON CONFLICT (user_id,novel_id) DO UPDATE SET", sql)
            self.assertIn("updated_at=excluded.updated_at", sql)
            self.assertNotRegex(sql, r"(?i)WHERE\s+excluded\.updated_at\s*>")
        self.assertIn(".upsert(payload,{onConflict:'user_id,novel_id'})", self.client)
        self.assertIn("updated_at:updatedAt", self.client)

    def test_production_client_sync_does_not_currently_have_atomic_version_check(self):
        # Snapshot/code tether; when the implementation changes, reassess the risk.
        send_start = self.client.index("const send=async()=>{")
        send_end = self.client.index("return state.progressQueue;", send_start)
        send = self.client[send_start:send_end]
        self.assertIn(".upsert(payload,{onConflict:'user_id,novel_id'})", send)
        self.assertNotIn("shouldReplayReadingProgress", send)
        self.assertNotIn("rpc(", send)
        self.assertIn("shouldReplayReadingProgress(pendingAt,remote?.updated_at)", self.client)
        self.assertIn("async function retryCloudProgress()", self.client)

    def test_explicit_NO_GO_and_no_claim_that_risk_is_fixed(self):
        s = self.steps[2]
        self.assertIn("V49-RACE-RISK-REPRODUCED-NO_GO", s)
        self.assertIn("IF n<>1 THEN", s)
        self.assertIn("last_page=12", s)
        self.assertIn("scroll_ratio=0.2100", s)

    def test_no_real_network_or_privileged_connection(self):
        combined = "\n".join([self.fixture,*self.steps])
        for forbidden in (
            "gpvivleexywljowcqkru", "supabase.co", "SUPABASE_DB_PASSWORD",
            "service_role_key", "postgresql://", "db push", "apply_migration",
            "COPY PROGRAM", "pg_read_file", "lo_import",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.lower(),combined.lower())
        for sql in self.steps:
            self.assertNotRegex(sql, r"(?im)^\s*\\(?:connect|copy|gexec|shell|!)\b")
            self.assertNotIn("ALTER TABLE",sql.upper())
            self.assertNotIn("DROP TABLE",sql.upper())

    def test_iso_timestamps_are_intentionally_stale(self):
        self.assertEqual(self.steps[1].count(B_TIME),2)
        self.assertEqual(self.steps[2].count(A_TIME),2)
        self.assertRegex(self.steps[2],r"ON CONFLICT \(user_id,novel_id\) DO UPDATE SET")

if __name__ == "__main__":
    unittest.main()
