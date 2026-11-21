#!/usr/bin/env python3
"""Contrat SINJIRA : commentaires modérés, interface tactile et absence de fuite."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
reader = (root / "assets/js/sinjira-reader.js").read_text(encoding="utf-8")
html = (root / "projets/sinjira/romans/index.html").read_text(encoding="utf-8")
css = (root / "assets/css/sinjira-comments-responsive-v2.css").read_text(encoding="utf-8")
errors = []

def check(ok, message):
    if not ok:
        errors.append(message)

for marker in [
    "from('sinjira_novels')",
    "rpc('list_sinjira_novel_comments'",
    "from('sinjira_novel_comments').insert(",
    "p_novel_slug:slug",
    "spoiler:fd.get('contains_spoilers')==='yes'",
    "friendlyBackendMessage(",
    "submit.disabled=true",
    "submit.disabled=false",
    "aria-expanded",
    "form.hidden=false",
]:
    check(marker in reader, "Contrat commentaires absent : " + marker)
for forbidden in ["from('novel_comments')", "contains_spoilers:", "display_name_snapshot:", "setStatus(error.message", "insert({novel_id:novel.id,user_id:user.id,display_name_snapshot"]:
    check(forbidden not in reader, "Ancienne API ou risque sécurité : " + forbidden)
for marker in [
    'data-reader-page="novel"',
    'sinjira-comments-responsive-v2.css?v=2.0.0',
    'sinjira-reader.js?v=25.1.2',
    'id="sinjira-commentaire-texte"',
    'for="sinjira-commentaire-texte"',
    'minlength="3"',
    'maxlength="3000"',
    'rows="6"',
    'aria-live="polite"',
]:
    check(marker in html, "HTML commentaires manquant : " + marker)
for marker in [
    '.reader-comment-form[hidden]', 'display:none!important',
    'grid-template-columns:minmax(0,1fr)',
    'max-width:100%', 'min-height:180px',
    'font-size:max(16px,1rem)', 'button[type="submit"]',
    '@media(max-width:600px)', 'prefers-reduced-motion:reduce',
    'textarea:focus-visible',
]:
    check(marker in css, "CSS ergonomique manquant : " + marker)
if errors:
    print("ECHEC ergonomie/commentaires SINJIRA :")
    for problem in errors:
        print(" - " + problem)
    raise SystemExit(1)
print("OK : contrat SQL/RPC historique protégé, formulaire centré et ergonomie responsive.")
