#!/usr/bin/env python3
"""Contrats non destructifs : inscription, registre, consentement et envois Formspree."""
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]

def read(path:str)->str:
    return (ROOT/path).read_text(encoding='utf-8',errors='strict')

def main()->int:
    errors=[]
    def check(path, markers):
        body=read(path)
        for marker in markers:
            if marker not in body:
                errors.append(f"{path}: garde manquante : {marker[:80]}")
        return body

    signup_page=check('compte/inscription.html',[
        'data-signup-form method="post"', 'type="submit" disabled>Créer mon compte',
        'name="formspree_receipt_opt_in"', 'v24-signup.js?v=24.5.3', '<noscript>',
    ])
    signup=check('assets/js/v24-signup.js',[
        'getSupabase().auth.signUp(', 'emailRedirectTo:', '/compte/confirmer.html',
        "formspree_receipt_opt_in:d.get('formspree_receipt_opt_in')==='yes'",
    ])
    confirmation=check('assets/js/sinjira-confirm-email.js',[
        "getSupabase().auth.verifyOtp(", "confirmButton?.addEventListener('click'",
        "getSupabase().auth.resend(", "options:{emailRedirectTo:", "'notify-account-confirmation'",
        "signal:AbortSignal.timeout(8500)", "resendButton.disabled=!isSinjiraBackendConfigured()",
    ])
    confirmation_page=check('compte/confirmer.html',[
        'data-confirm-button hidden', 'data-confirm-resend-form',
        'noindex,nofollow', 'sinjira-confirm-email.js?v=2',
        'data-confirm-resend-form method="post" action="/compte/confirmer.html"',
        'type="submit" disabled>Renvoyer un lien', '<noscript>',
    ])
    registry_page=check('projets/sinjira/registre/index.html',[
        'data-character-form=', 'type="submit" disabled>Transmettre ma participation',
        'name="formspree_receipt_opt_in"', 'sinjira-character-registry.js?v=24.5.6',
    ])
    registry_js=check('assets/js/sinjira-character-registry.js',[
        "form?.addEventListener('submit',async e=>{",
        'e.preventDefault();', 'if(!registryReady||isSending||!currentUser)',
        "functions.invoke('submit-character-questionnaire'",
        "let invocationStarted=false;",
        "invocationStarted=true;",
        "if(!invocationStarted)await cleanupUploadedPhoto(photo_path);",
        "result.admin_notification_created===true",
        "uncertainError.submissionOutcomeUnknown=true;",
        "const unknown=err?.submissionOutcomeUnknown===true;",
        "if(unknown){",
        "registryReady=false;",
        "link.href='/compte/mon-personnage.html';",
        "link.target='_blank';",
    ])
    registry_edge=check('supabase/functions/submit-character-questionnaire/index.ts',[
        "requiredUser(req)", "answers.formspree_receipt_opt_in==='yes'",
        "sendFormspreeNotice(service,'registre_enregistre',sub.id,",
        "answers:answers as Record<string,unknown>",
        "CHARACTER_SUBMISSION_WRITE_FAILED",
    ])
    account_edge=check('supabase/functions/notify-account-confirmation/index.ts',[
        "requiredUser(req)", "if(!user.email_confirmed_at)",
        "user.user_metadata?.formspree_receipt_opt_in!==true",
        "sendFormspreeNotice(serviceClient(),'compte_confirme',user.id,{email:user.email||''})",
    ])
    helper=check('supabase/functions/_shared/sinjira-formspree.ts',[
        "'https://formspree.io/f/xzeeqynp'",
        "'https://formspree.io/f/mrppvrwa'",
        "QUESTIONNAIRE_FIELDS",
        "const email=safeEmail(options?.email)",
        "if(questionnaire)fields.questionnaire=questionnaire;",
        "email, // Champ officiel Formspree",
        ".from('sinjira_formspree_events')",
        'body:JSON.stringify(fields)',
        'reference:String(receipt.id)',
        "if(reserveError.code==='23505')",
        ".select('delivery_status')",
        "accepted:!priorError&&prior?.delivery_status==='sent'",
        "already:true",
        "async function sendFormspreeNoticeCore(",
        "export async function sendFormspreeNotice(",
        "return await sendFormspreeNoticeCore(service,kind,sourceId,options);",
        "reason:'SECONDARY_CHANNEL_UNAVAILABLE'",
    ])
    migration=check('supabase/migrations/20261108054703_sinjira_formspree_notification_ledger.sql',[
        'unique(event_type,source_id)', 'enable row level security',
        'revoke all on public.sinjira_formspree_events from public, anon, authenticated',
        'to service_role',
    ])
    check('supabase/config.toml',[
        '[functions.notify-account-confirmation]', 'verify_jwt = true',
    ])
    check('scripts/validate_edge_function_inventory.py',[
        '"notify-account-confirmation"',
    ])

    # Jamais de soumission Formspree directe depuis des pages contenant les secrets.
    for path,src in [
        ('compte/inscription.html',signup_page),
        ('assets/js/v24-signup.js',signup),
        ('assets/js/sinjira-confirm-email.js',confirmation),
        ('compte/confirmer.html',confirmation_page),
        ('projets/sinjira/registre/index.html',registry_page),
        ('assets/js/sinjira-character-registry.js',registry_js),
    ]:
        if 'formspree.io' in src:
            errors.append(f'{path}: endpoint tiers interdit côté navigateur')

    # La liste blanche ne doit inclure ni secrets, ni champs d'identification.
    allow=helper.partition('const QUESTIONNAIRE_FIELDS = [')[2].partition('] as const;')[0]
    for forbidden in ('password','date_naissance','prenom_legal','nom_legal','parent_','compte_','email','photo'):
        if forbidden in allow:
            errors.append(f'Liste blanche Formspree contient un champ interdit : {forbidden}')


    # Vérifier automatiquement toutes les questions du formulaire contre la copie
    # Formspree et leurs libellés français. Pas de liste manuelle divergente.
    form_html=registry_page.partition('<form ')[2].partition('</form>')[0]
    displayed_fields=set(re.findall(r'\bname="([a-z][a-z0-9_]*)"',form_html))
    private_fields={
        'compte_pseudo','compte_courriel','photo',
        'confirm_original','formspree_receipt_opt_in',
    }
    exported=set(re.findall(r"'([a-z][a-z0-9_]*)'",allow))
    expected=displayed_fields-private_fields
    if not displayed_fields or not exported:
        errors.append('Questionnaire : impossible de lire la liste des champs.')
    if missing:=sorted(expected-exported):
        errors.append('Formspree : questions manquantes de la copie : '+', '.join(missing))
    if extra:=sorted(exported-expected):
        errors.append('Formspree : champs non autorisés dans la copie : '+', '.join(extra))
    if len(re.findall(r"'([a-z][a-z0-9_]*)'",allow))!=len(exported):
        errors.append('Formspree : champs exportés en double.')
    labels=helper.partition('const QUESTION_LABELS:Record<string,string>={')[2].partition('};')[0]
    label_names=set(re.findall(r'^\s*([a-z][a-z0-9_]*):',labels,re.M))
    if exported!=label_names:
        errors.append('Formspree : libellés français en décalage avec les questions.')
    if len(re.findall(r'^\s*([a-z][a-z0-9_]*):',labels,re.M))!=len(label_names):
        errors.append('Formspree : libellés en double.')
    if 'formspree_receipt_opt_in' not in form_html:
        errors.append('Registre : consentement Formspree absent du formulaire.')

    # Si la réponse HTTP se perd après un enregistrement réussi, ne pas
    # effacer la photo que le serveur peut déjà référencer dans le dossier.
    if re.search(r'catch\s*\(e\)\s*\{\s*await\s+cleanupUploadedPhoto\(photo_path\)',registry_js):
        errors.append('Registre : effacement photo aveugle après un échec réseau')
    # Aucun second POST possible après une invocation réseau au résultat incertain.
    if not re.search(r'if\s*\(unknown\)\s*\{\s*registryReady=false;',registry_js):
        errors.append('Registre : second envoi encore autorisé après une réponse réseau incertaine')
    if not re.search(r'if\s*\(!invocationStarted\)\s*\{\s*await\s+cleanupUploadedPhoto\(photo_path\)',registry_js):
        errors.append('Registre : nettoyage temporaire pré-envoi non protégé')
    if 'Avis interne créé. Aucune copie' in registry_js:
        errors.append('Registre : avis interne annoncé sans vérifier le statut serveur')

    if "req.method!=='POST'" not in account_edge:
        errors.append('Notification de compte : POST requis.')
    if 'source_id' not in migration:
        errors.append('Journal : source idempotente manquante.')

    if errors:
        for error in errors:
            print('ECHEC',error)
        return 1
    print('OK inscription et Registre, copie créative, accord explicite, JWT, RLS et anti-doublons.')
    return 0

if __name__=='__main__':
    sys.exit(main())
