#!/usr/bin/env python3
"""Concurrency tests ONLY against the disposable loopback CI Supabase database."""
import concurrent.futures
import os
from pathlib import Path
import select
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "security/candidates/registry_photo_budget.sql"
CMD = ["psql", "-X", "-qAt", "-w", "-v", "ON_ERROR_STOP=1", "-h", "127.0.0.1", "-p", "54322", "-U", "postgres", "-d", "postgres"]
ENV = {"PATH": os.environ["PATH"], "PGPASSWORD": "postgres", "PGCONNECT_TIMEOUT": "5",
       "PGOPTIONS": "-c statement_timeout=5000 -c idle_in_transaction_session_timeout=15000"}
def query(sql):
    return subprocess.run(CMD, input=sql, text=True, capture_output=True, env=ENV, timeout=10, check=True).stdout.strip()
def uid(i):
    return f"10000000-0000-4000-8000-{i:012d}"
def consume(i):
    result = query(f"SET ROLE service_role; SELECT public.consume_registry_photo_budget('{uid(i)}'::uuid);")
    assert result in ("t", "f"), result
    return result == "t"
def reset():
    query("UPDATE private.registry_photo_budget SET window_start=clock_timestamp(), used=0, accounts='{}'::jsonb;")
def state():
    result = query("""SELECT used, COALESCE((SELECT sum(value::int) FROM jsonb_each_text(accounts)),0),
      COALESCE((SELECT max(value::int) FROM jsonb_each_text(accounts)),0),
      clock_timestamp()<window_start+interval '60 seconds'
      FROM private.registry_photo_budget;""")
    used,total,maximum,fresh = result.split("|")
    assert int(used)==int(total) and int(maximum)<=3 and fresh=="t", result
    return int(used)
def held_transaction(finish):
    p = subprocess.Popen(CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, env=ENV)
    try:
        p.stdin.write(f"BEGIN; SET LOCAL ROLE service_role; SELECT public.consume_registry_photo_budget('{uid(1)}'::uuid);\n")
        p.stdin.flush()
        assert select.select([p.stdout], [], [], 8)[0], "first connection did not acquire lock"
        assert p.stdout.readline().strip()=="t", "first admission failed"
        start=time.monotonic()
        assert not consume(2), "contending connection admitted"
        assert time.monotonic()-start<4, "contention did not fail promptly"
        p.stdin.write(finish+";\n")
        p.stdin.flush()
        p.stdin.close()
        assert p.wait(timeout=8)==0, p.stderr.read()
    finally:
        if p.poll() is None:
            p.kill()
            p.wait(timeout=5)
        for stream in (p.stdin,p.stdout,p.stderr):
            if stream and not stream.closed: stream.close()

assert os.environ.get("GITHUB_ACTIONS")=="true", "disposable CI only"
assert query("SELECT to_regclass('private.registry_photo_budget') IS NULL AND to_regprocedure('public.consume_registry_photo_budget(uuid)') IS NULL;")=="t"
source=SQL.read_text(encoding="utf-8").rstrip()
assert source.endswith("ROLLBACK;")
# Only the ephemeral CI database needs committed objects for cross-session testing.
query(source.removesuffix("ROLLBACK;")+"COMMIT;")
try:
    reset()
    held_transaction("ROLLBACK")
    assert state()==0
    assert consume(2) and state()==1
    reset()
    held_transaction("COMMIT")
    assert state()==1
    assert consume(2) and state()==2
    reset()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        admitted=sum(pool.map(consume,[1]*12))
    assert 1<=admitted<=3 and state()==admitted
    for _ in range(3-admitted): assert consume(1)
    assert not consume(1) and state()==3
    reset()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        admitted=sum(pool.map(consume,range(1,41)))
    assert 1<=admitted<=30 and state()==admitted
    for i in range(100,100+30-admitted): assert consume(i)
    assert not consume(999) and state()==30
    print("PASS: contention, rollback, commit, 12 same-account calls and 40 distinct-account calls.")
finally:
    query("DROP FUNCTION public.consume_registry_photo_budget(uuid); DROP TABLE private.registry_photo_budget;")
