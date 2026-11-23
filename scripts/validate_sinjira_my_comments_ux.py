#!/usr/bin/env python3
"""Contrat UX du compte SINJIRA : Mes commentaires sur PC et cellulaire.

Validation statique, sans connexion à un compte ni écriture en base.
Les autorisations sont exclusivement appliquées côté serveur et via RLS.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    failures = []
    page = (ROOT / 'compte/mes-commentaires.html').read_text('utf-8')
    js = (ROOT / 'assets/js/sinjira-account-v18.js').read_text('utf-8')
    css = (ROOT / 'assets/css/sinjira-comments-responsive-v2.css').read_text('utf-8')

    required_js = [
        'data-comment-id="${escapeHtml(c.id)}"',
        "escapeHtml(entry.id)",
        "const counter=form.querySelector('.reader-comment-counter')",
        "textarea.addEventListener('input',updateCounter)",
        "counter.classList.toggle('near-limit',size>=2700)",
        "const body=textarea.value.trim()",
        "textarea.focus()",
        "if(saving)return",
        "saving=true",
        "submit.disabled=true",
        "cancel.disabled=true",
        "button.disabled=true",
        "if(button.disabled)return",
        "button.textContent='Suppression…'",
        ".eq('user_id',user.id).eq('status','pending')",
        "if(button.isConnected)",
        "if(status){status.tabIndex=-1;status.focus({preventScroll:true});}",
        "Commentaire enregistré, mais la liste ne peut pas être actualisée.",
        "Commentaire supprimé, mais la liste ne peut pas être actualisée.",
        "if(deleteButton)deleteButton.disabled=true",
        "if(deleteButton)deleteButton.disabled=false",
        "if(event.key!=='Escape'||event.isComposing||saving)return",
        "event.stopPropagation()",
        "if(textarea.value!==entry.body&&",
        "window.confirm('Abandonner les modifications non enregistrées de ce commentaire?')",
        "textarea.focus();",
        "if(saving)return",
        "box.setAttribute('aria-busy','false')",
        'aria-label="Modifier mon commentaire du',
        'aria-label="Supprimer mon commentaire du',
    ]
    for marker in required_js:
        if marker not in js:
            failures.append(f"JS sans garde UX : {marker}")

    for marker in (
        "sinjira-comments-responsive-v2.css?v=2.0.3",
        "sinjira-account-v18.js?v=24.1.5",
        # Les flèches du compte sont apportées par la PR UX #1160.
        "site-ux-sinjira-v1.css?v=1.0.1",
        "site.js?v=24.4.102",
        'data-v18-page="comments"',
        'data-my-comments',
        'aria-busy="true"',
        'reader-comments-loading',
        'role="status"',

    ):
        if marker not in page:
            failures.append(f"Page du compte incomplète : {marker}")

    for marker in (
        '.reader-comment-inline-edit .reader-comment-counter',
        '.reader-comment-inline-edit .reader-comment-counter.near-limit',
        '.reader-comment:focus',
        'min-height:48px!important',
        '@media(max-width:520px)',
        'grid-template-columns:repeat(2,minmax(0,1fr))',
    ):
        if marker not in css:
            failures.append(f"CSS adapté absent : {marker}")

    if "await load()}" in js:
        failures.append("Ancien handler de suppression sans gestion d'erreur présent.")
    return failures


def main() -> int:
    problems = validate()
    if problems:
        print(f"ÉCHEC Mes commentaires UX : {len(problems)} erreur(s)")
        for problem in problems:
            print(" - " + problem)
        return 1
    print("OK Mes commentaires : brouillon protégé, compteur, suppression contrôlée, retour focus et CSS mobile.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
