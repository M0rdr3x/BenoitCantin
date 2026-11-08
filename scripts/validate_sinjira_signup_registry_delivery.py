#!/usr/bin/env python3
"""Contrats non destructifs des deux formulaires SINJIRA et des avis Formspree."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]

def read(path:str)->str:
    return (ROOT/path).read_text(encoding='utf-8',errors='strict')

def main()->int:
    errors=[]
    def require(path, snippets):
        source=read(path)
        for marker in snippets:
            if marker not in source:
                errors.append(f"{path}: garde absent: {marker[:75]}")
        return source

    account=require('compte/inscription.html',[
        'data-signup-form method="post"', 'type="submit" disabled>Créer mon compte',
        'v24-signup.js?v=24.5.3','<noscript>',
    ])
    signup=require('assets/js/v24-signup.js',[
        'getSupabase().auth.signUp(', 'emailRedirectTo:`${SINJIRA_CONFIG.siteUrl}/compte/confirmer.html`',
        'setBusy(!isSinjiraBackendConfigured());',
    ])
    confirmation=require('assets/js/sinjira-confirm-email.js',[
        "getSupabase().auth.verifyOtp(", "confirmButton?.addEventListener('click'",
        "getSupabase().auth.resend(", "'notify-account-confirmation'",
    ])
    confirm_page=require('compte/confirmer.html',[
        'data-confirm-button hidden', 'data-confirm-resend-form', 'noindex,nofollow',
        'sinjira-confirm-email.js?v=2'
    ])
    registry_page=require('projets/sinjira/registre/index.html',[
        'data-character-form=', 'type="submit" disabled>Transmettre ma participation',
        'sinjira-character-registry.js?v=24.5.3'
    ])
    registry=require('assets/js/sinjira-character-registry.js',[
        "form?.addEventListener('submit',async e=>{", 'e.preventDefault();',
        'if(!registryReady||isSending||!currentUser)', 'if(profileError||submissionError||characterError)',
        "functions.invoke('submit-character-questionnaire'",
    ])
    edge=require('supabase/functions/submit-character-questionnaire/index.ts',[
        "requiredUser(req)", "sendFormspreeNotice(service,'registre_enregistre',sub.id)",
        "if(error)throw new Error('CHARACTER_SUBMISSION_WRITE_FAILED')",
    ])
    notify=require('supabase/functions/notify-account-confirmation/index.ts',[
        'requiredUser(req)', 'if(!user.email_confirmed_at)',
        "sendFormspreeNotice(serviceClient(),'compte_confirme',user.id)",
    ])
    helper=require('supabase/functions/_shared/sinjira-formspree.ts',[
        "'https://formspree.io/f/xzeeqynp'", "'https://formspree.io/f/mrppvrwa'",
        ".from('sinjira_formspree_events')", 'body:JSON.stringify(fields)',
        'reference:String(receipt.id)',
    ])
    migration=require('supabase/migrations/20261108041500_sinjira_formspree_notification_ledger.sql',[
        'unique(event_type,source_id)',
        'enable row level security',
        'revoke all on public.sinjira_formspree_events from public, anon, authenticated',
        'to service_role',
    ])
    config=require('supabase/config.toml',[
        '[functions.notify-account-confirmation]', 'verify_jwt = true',
    ])
    inventory=require('scripts/validate_edge_function_inventory.py',[
        '"notify-account-confirmation"',
    ])
    # Le navigateur n'envoie jamais de contenu sensible à Formspree.
    for path,src in [
        ('compte/inscription.html',account),
        ('assets/js/v24-signup.js',signup),
        ('assets/js/sinjira-confirm-email.js',confirmation),
        ('compte/confirmer.html',confirm_page),
        ('projets/sinjira/registre/index.html',registry_page),
        ('assets/js/sinjira-character-registry.js',registry)
    ]:
        if 'formspree.io' in src:
            errors.append(f'{path}: endpoint Formspree interdit côté navigateur')
    # Pas de courriels, profils, mots de passe ou questionnaire dans l'avis.
    if 'body:JSON.stringify(fields)' not in helper or 'email:' in helper or 'password:' in helper or 'answers:' in helper:
        errors.append('Formspree: charge utile privée interdite.')
    if "req.method!=='POST'" not in notify:
        errors.append('Notification compte: POST obligatoire.')
    if 'user.id' not in notify:
        errors.append('Notification compte: source vérifiée manquante.')
    if 'source_id' not in migration:
        errors.append('Ledger: identité unique manquante.')
    if errors:
        for err in errors:
            print('ECHEC',err)
        return 1
    print('OK inscription, confirmation, registre, Formspree, RLS, JWT et idempotence.')
    return 0

if __name__=='__main__':
    sys.exit(main())
