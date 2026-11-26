#!/usr/bin/env python3
"""Contrat statique du candidat, sans connexion ni exécution SQL."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
SQL=ROOT/'security/candidates/registry_source_insert_mfa.sql'
EDGE=ROOT/'supabase/functions/submit-character-questionnaire/index.ts'
def valid(s):
    required=[
        "BEGIN;", "ROLLBACK;", "SET LOCAL lock_timeout = '3s';",
        "AND c.relrowsecurity", "AND public IS FALSE AND file_size_limit=10485760",
        "policyname='char_source_insert_own'", "AS RESTRICTIVE FOR INSERT TO authenticated",
        "bucket_id <> 'sinjira-character-sources' OR (",
        "(SELECT auth.uid()) IS NOT NULL", "(SELECT auth.jwt()->>'aal') = 'aal2'",
        "COALESCE((SELECT auth.jwt()->>'is_anonymous'), 'false') = 'false'",
        "split_part(name, '/', 1) = (SELECT auth.uid())::text",
        "length(name) - length((SELECT auth.uid())::text) IN (41,42)",
        "name = (SELECT auth.uid())::text || '/' || split_part(name, '/', 2)",
        """split_part(name, '/', 2) COLLATE "C" ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}[.](jpg|png|webp|avif|gif)$'""",
        "permissive='RESTRICTIVE' AND cmd='INSERT'"
    ]
    return (all(s.count(x)==1 for x in required)
        and s.strip().endswith('ROLLBACK;')
        and not re.search(r'\b(COMMIT|GRANT|DROP|ALTER|UPDATE|DELETE|TRUNCATE)\b',s,re.I)
        and len(re.findall(r'\bCREATE\s+POLICY\b',s,re.I))==1)
s=SQL.read_text(encoding='utf-8')
assert valid(s)
for old,new in [
    ('ROLLBACK;', 'COMMIT;'),
    ('AS RESTRICTIVE','AS PERMISSIVE'),
    ("= 'aal2'","= 'aal1'"),
    ("bucket_id <>","bucket_id ="),
    ("IN (41,42)","IN (41,43)"),
    ("AND name =","AND name <>"),
    ("[89ab]","[0-9a-f]"),
    ("AND c.relrowsecurity","AND true"),
    ("AND public IS FALSE","AND public IS TRUE"),
    ("(SELECT auth.uid()) IS NOT NULL","true"),
    ("FOR INSERT TO authenticated","FOR INSERT TO public"),
]:
    assert old in s and not valid(s.replace(old,new,1)), old
edge=EDGE.read_text(encoding='utf-8')
assert r'\.(?:jpg|png|webp|avif|gif)$' in edge
print('PASS registry source policy: 11 static mutations rejected; SQL staging required.')
