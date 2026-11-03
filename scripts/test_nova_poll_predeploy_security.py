#!/usr/bin/env python3
"""Tests fail-closed : le sondage NOVA reste hors du déploiement Supabase.

Aucun appel à la production ni données personnelles : construction locale
de l'artefact déployable et mutations d'un code Edge non activé.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / "supabase/functions/nova-civic-poll/index.ts"
SQL = ROOT / "supabase/NOVA_POLL_SCHEMA_PREDEPLOY.sql"
CONFIG = ROOT / "supabase/config.toml"
BUILDER = ROOT / "scripts/build_supabase_production_workspace.py"
INVENTORY = ROOT / "scripts/validate_edge_function_inventory.py"
TABLES = (
    "nova_poll_questions", "nova_poll_counts", "nova_poll_receipts",
    "nova_poll_public_counts", "nova_poll_publication_state",
)


def check_poll_edge(code: str) -> list[str]:
    errors: list[str] = []
    needed = (
        'Deno.env.get("NOVA_POLL_ENABLED") === "true"',
        '!!CAPTCHA_SECRET && !!CAPTCHA_SITE_KEY && HMAC_KEY.length >= 32',
        'MAX_BODY_BYTES = 8192', 'size>MAX_BODY_BYTES',
        'new TextDecoder("utf-8",{fatal:true})',
        'ORIGINS.has(origin)', 'req.method==="OPTIONS"',
        'if(!isOpen()) return respond(503',
        'result.hostname==="www.benoitcantin.com"',
        'result.action==="nova_poll_vote"',
        'result.success===true',
        'crypto.subtle.sign("HMAC"', 'token_hash',
        'MIN_PUBLIC_BALLOTS = 10',
        'nova_poll_public_counts', 'nova_poll_publication_state',
        'reader.releaseLock()', '"Cache-Control":"no-store, private"',
        '"Referrer-Policy":"no-referrer"',
        'return respond(403,{error:"verification_anti_robot_echouee"},origin)',
    )
    for marker in needed:
        if marker not in code:
            errors.append("Garde sondage absent: " + marker)
    # Eviter les tests par préfixe : 81920000 contient littéralement "8192".
    if not re.search(r"\bconst MAX_BODY_BYTES\s*=\s*8192\s*;", code):
        errors.append("Plafond du corps HTTP différent de 8192 octets.")
    # Le contrôle CORS de la réponse et le refus initial du handler sont
    # indépendants : une régression de l'un ne doit pas être cachée par l'autre.
    if code.count("ORIGINS.has(origin)") != 2:
        errors.append("Contrôle des origines incomplet pour CORS ou pour le handler.")
    for raw in (
        'console.log(', 'console.error(', 'console.warn(',
        'await req.json()', 'await req.text()',
        'db("nova_poll_counts?', 'db("nova_poll_receipts?',
        'Deno.env.get("NOVA_POLL_ENABLED") !== "false"',
    ):
        if raw in code:
            errors.append("Accès ou journalisation interdit: " + raw)
    try:
        handler = code.index('Deno.serve(')
        start = code.index('if(!isOpen())', handler)
        verified = code.index('if(!await confirmCaptcha(payload.captchaToken))', start)
        lookup = code.index('const questions=await db("nova_poll_questions?', start)
        submit = code.index('const result=await db("rpc/nova_poll_submit"', start)
        if not start < verified < lookup < submit:
            errors.append("CAPTCHA doit précéder chaque requête privilégiée de vote.")
        if 'await db(' in code[start:verified]:
            errors.append("Appel à la base avant CAPTCHA dans le chemin POST.")
    except ValueError:
        errors.append("Séquence d'authentification du POST introuvable.")
    return errors


def check_poll_sql(sql: str) -> list[str]:
    errors = []
    for table in TABLES:
        if f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;" not in sql:
            errors.append("RLS absent: " + table)
    for marker in (
        'BEGIN;', 'COMMIT;', 'SECURITY DEFINER', "SET search_path = ''",
        "REVOKE ALL ON FUNCTION public.nova_poll_submit(text,text,jsonb) FROM PUBLIC,anon,authenticated;",
        "GRANT EXECUTE ON FUNCTION public.nova_poll_submit(text,text,jsonb) TO service_role;",
        "v_total_ballots - v_published_ballots >= 10", "interval '6 hours'",
        "IF v_inserted=0 THEN RETURN 'duplicate'; END IF;",
        "ON CONFLICT(poll_version,question_id,option_value)",
    ):
        if marker not in sql:
            errors.append("Confinement SQL absent: " + marker)
    if not re.search(r"REVOKE ALL ON public\.nova_poll_questions.*FROM PUBLIC,anon,authenticated;", sql):
        errors.append("ACL tables publique non révoquée.")
    if re.search(r"GRANT\s+EXECUTE\s+ON\s+FUNCTION\s+public\.nova_poll_submit.*\bTO\s+(?:anon|authenticated|PUBLIC)\b", sql, re.I):
        errors.append("RPC PRIVILEGIEE rendue publique.")
    return errors


class NovaPollSecurityTests(unittest.TestCase):
    def test_source_guards(self):
        code = EDGE.read_text("utf-8")
        self.assertEqual(check_poll_edge(code), [])
        self.assertEqual(check_poll_sql(SQL.read_text("utf-8")), [])
        config = tomllib.loads(CONFIG.read_text("utf-8"))
        self.assertIs(config["functions"]["nova-civic-poll"]["verify_jwt"], False)

    def test_mutations_of_public_api_denied(self):
        code = EDGE.read_text("utf-8")
        mutations = {
            "enable guard": (
                'Deno.env.get("NOVA_POLL_ENABLED") === "true"',
                'Deno.env.get("NOVA_POLL_ENABLED") !== "false"'),
            "captcha ordering": (
                'if(!await confirmCaptcha(payload.captchaToken)) return respond(403,{error:"verification_anti_robot_echouee"},origin);',
                'if(true) { /* CAPTCHA validation disabled */ }'),
            "body ceiling": ("MAX_BODY_BYTES = 8192", "MAX_BODY_BYTES = 81920000"),
            "hmac": ('crypto.subtle.sign("HMAC"', 'crypto.subtle.sign("SHA-256"'),
            "privacy": ('db("nova_poll_public_counts?', 'db("nova_poll_counts?'),
            "origin": ('ORIGINS.has(origin)', 'origin !== null'),
            "pre-captcha database": (
                'const questions=await db("nova_poll_questions?',
                'const questions=await db("nova_poll_questions?'), # changed below
        }
        for name, (old, replacement) in mutations.items():
            self.assertIn(old, code, name)
            if name == "pre-captcha database":
                original = 'if(!await confirmCaptcha(payload.captchaToken))'
                begin = code.index(original, code.index('Deno.serve('))
                search = code.index(old, begin)
                injected = 'await db("nova_poll_questions?poll_version=eq."+VERSION+"&select=question_id");'
                altered = code[:begin] + injected + '\n    ' + code[begin:]
            else:
                altered = code.replace(old, replacement, 1)
            with self.subTest(name=name):
                self.assertNotEqual(altered, code)
                self.assertTrue(check_poll_edge(altered), "Fail-closed mutation not detected.")

    def test_sql_permission_mutations_denied(self):
        source = SQL.read_text("utf-8")
        for name, old, replacement in [
            ("RLS", "ALTER TABLE public.nova_poll_receipts ENABLE ROW LEVEL SECURITY;", "-- RLS removed"),
            ("RPC revocation", "REVOKE ALL ON FUNCTION public.nova_poll_submit(text,text,jsonb) FROM PUBLIC,anon,authenticated;", "-- revocation removed"),
            ("batch size", "v_total_ballots - v_published_ballots >= 10", "v_total_ballots - v_published_ballots >= 1"),
        ]:
            self.assertIn(old, source)
            with self.subTest(name=name):
                self.assertTrue(check_poll_sql(source.replace(old, replacement, 1)))

    def test_production_workspace_omits_staged_function_and_schema(self):
        spec = importlib.util.spec_from_file_location("edge_inventory", INVENTORY)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.STAGED_PUBLIC, {"nova-civic-poll"})
        with tempfile.TemporaryDirectory(prefix="nova-poll-prod-isolation-") as tmp:
            out = Path(tmp) / "supabase"
            result = subprocess.run(
                [sys.executable, str(BUILDER), "--output", str(out)],
                cwd=str(ROOT), capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("fonction, configuration JWT et schéma SQL candidat exclus", result.stdout)
            self.assertFalse((out / "functions/nova-civic-poll").exists())
            self.assertFalse((out / "NOVA_POLL_SCHEMA_PREDEPLOY.sql").exists())
            self.assertNotIn("nova-civic-poll", tomllib.loads(
                (out / "config.toml").read_text("utf-8")
            ).get("functions", {}))
            sources = {p.name for p in (out / "functions").iterdir()
                       if p.is_dir() and p.name != "_shared"}
            self.assertEqual(sources, module.CANONICAL)
            self.assertTrue((out / "functions/send-game-report/index.ts").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
