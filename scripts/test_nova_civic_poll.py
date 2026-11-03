#!/usr/bin/env python3
"""Contrôles statiques Projet NOVA : boussole + consultation citoyenne."""
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOVA = ROOT / "projets" / "projet-nova"
poll = json.loads((NOVA / "data" / "sondage-citoyen-v1.json").read_text(encoding="utf-8"))
compass = json.loads((NOVA / "data" / "boussole-electorale-v2.json").read_text(encoding="utf-8"))
evidence = json.loads((NOVA / "data" / "boussole-preuves-2026.json").read_text(encoding="utf-8"))
html = (NOVA / "index.html").read_text(encoding="utf-8")
poll_html = (NOVA / "sondage-citoyen.html").read_text(encoding="utf-8")
compass_html = (NOVA / "boussole-electorale.html").read_text(encoding="utf-8")
compass_js = (NOVA / "assets" / "boussole-electorale.js").read_text(encoding="utf-8")
poll_js = (NOVA / "assets" / "sondage-citoyen.js").read_text(encoding="utf-8")
edge = (ROOT / "supabase" / "functions" / "nova-civic-poll" / "index.ts").read_text(encoding="utf-8")
sql = (ROOT / "supabase" / "NOVA_POLL_SCHEMA_PREDEPLOY.sql").read_text(encoding="utf-8")
config = (ROOT / "supabase" / "config.toml").read_text(encoding="utf-8")

assert len(compass["axes"]) == 16
assert len(compass["questions"]) == 64
assert len({a["id"] for a in compass["axes"]}) == 16
assert len({q["id"] for q in compass["questions"]}) == 64
assert isinstance(poll["published"], bool), "La publication est un booléen explicite"
assert poll["version"] == "nova-consultation-v1"
assert len(poll["questions"]) == 8
assert len({q["id"] for q in poll["questions"]}) == 8
by_id = {q["id"]: q for q in compass["questions"]}
for n, q in enumerate(poll["questions"], 1):
    assert q["id"] in by_id and q["ordinal"] == n
    assert q["text"] == by_id[q["id"]]["text"], q["id"]
    assert q["text"].replace("'", "''") in sql
assert [o["value"] for o in poll["options"]] == [-2, -1, 0, 1, 2, 9]
assert "sondage-citoyen.html" in html
assert "boussole-electorale.html" in html
assert "sondage-citoyen.html" in compass_html
assert 'id="poll-adult"' in poll_html and 'id="poll-agree"' in poll_html
assert 'id="poll-results"' in poll_html and 'id="poll-form"' in poll_html
assert "MIN_PUBLIC_BALLOTS = 10" in edge
assert "NOVA_POLL_ENABLED" in edge and '=== "true"' in edge
assert "local.published===true" in poll_js, "Ouverture du scrutin interdite sans publication explicite"
assert "NOVA_POLL_TURNSTILE_SECRET" in edge and "NOVA_POLL_HMAC_KEY" in edge
assert "confirmCaptcha(payload.captchaToken)" in edge
assert "crypto.subtle.sign" in edge
assert "jsonb_each_text(p_answers)" in sql
assert "ENABLE ROW LEVEL SECURITY" in sql
assert "REVOKE ALL ON FUNCTION public.nova_poll_submit" in sql
assert "GRANT EXECUTE ON FUNCTION public.nova_poll_submit" in sql
assert "[functions.nova-civic-poll]" in config
for path in ("netlify.toml", "vercel.json", "projets/projet-nova/netlify.toml"):
    deployment = (ROOT / path).read_text(encoding="utf-8")
    assert "https://challenges.cloudflare.com" in deployment, path
assert "resultsVisible" in edge and "showCounts?Object.fromEntries" in edge
assert "localStorage.setItem" not in compass_js
assert "results.filter(r => r.score !== null)" not in compass_js[
    compass_js.index("function renderRadar"):compass_js.index("function coveragePercent")
], "Le radar ne doit jamais réindexer les axes partiels"
assert "const complete = points.every" in compass_js
assert "compass-radar-marker" in compass_js
assert "renderRadar(results)" in compass_js
assert "partyComparison" in compass
assert "questionnaireBinding" in evidence
for p in ("assets/sondage-citoyen.css", "assets/sondage-citoyen.js", "data/sondage-citoyen-v1.json"):
    assert (NOVA / p).is_file()
assert "width:100%" in (NOVA / "assets" / "sondage-citoyen.css").read_text(encoding="utf-8")
if shutil.which("node"):
    for js in (NOVA / "assets" / "sondage-citoyen.js", NOVA / "assets" / "boussole-electorale.js"):
        subprocess.run(["node", "--check", str(js)], check=True)
print("OK: questionnaire versionné, liens, protections serveur, anonymisation et radar stable.")
