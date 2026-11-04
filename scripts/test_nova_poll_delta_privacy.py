#!/usr/bin/env python3
"""Contrôler la confidentialité entre deux publications, sans vote ni réseau."""
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase/NOVA_POLL_SCHEMA_PREDEPLOY.sql").read_text(encoding="utf-8")
required = [
    "current_count.total - COALESCE(previous_count.total,0) < 5",
    "current_count.total < COALESCE(previous_count.total,0)",
    "AND NOT EXISTS (",
    "current_count.poll_version=p_version",
    "previous_count.question_id=current_count.question_id",
    "previous_count.option_value=current_count.option_value",
]
for marker in required:
    assert marker in SQL, f"Règle de confidentialité SQL manquante : {marker}"

# Vérifier la sémantique du garde SQL à l'aide de petits tableaux artificiels.
# SQLite utilise ici les mêmes constructions COALESCE, LEFT JOIN et AND NOT EXISTS.
def publishable(previous: list[int], current: list[int]) -> bool:
    assert len(previous) == len(current) == 6
    con = sqlite3.connect(":memory:")
    try:
        con.execute("CREATE TABLE current_count (option_value INTEGER PRIMARY KEY, total INTEGER)")
        con.execute("CREATE TABLE previous_count (option_value INTEGER PRIMARY KEY, total INTEGER)")
        con.executemany("INSERT INTO current_count VALUES (?,?)", enumerate(current))
        con.executemany(
            "INSERT INTO previous_count VALUES (?,?)",
            [(i,n) for i,n in enumerate(previous) if n>0],
        )
        unsafe = con.execute("""
            SELECT EXISTS (
              SELECT 1 FROM current_count
              LEFT JOIN previous_count USING(option_value)
              WHERE current_count.total < COALESCE(previous_count.total,0)
                 OR (current_count.total > COALESCE(previous_count.total,0)
                     AND current_count.total - COALESCE(previous_count.total,0) < 5)
            )""").fetchone()[0]
        return not bool(unsafe)
    finally:
        con.close()

assert publishable([0]*6,[10,0,0,0,0,0])
assert publishable([0]*6,[5,5,0,0,0,0])
assert not publishable([0]*6,[9,1,0,0,0,0])
assert not publishable([0]*6,[6,4,0,0,0,0])
assert publishable([10,10,0,0,0,0],[15,15,0,0,0,0])
assert not publishable([10,10,0,0,0,0],[11,19,0,0,0,0])
assert not publishable([10,10,0,0,0,0],[9,21,0,0,0,0])
assert publishable([10,10,0,0,0,0],[10,20,0,0,0,0])
assert not publishable([0]*6,[0,0,0,0,4,6])

print("OK NOVA : écarts publics 9/1, 6/4 et 1/9 rejetés; 5/5 et 0/10 tolérés, pas de votes.")
