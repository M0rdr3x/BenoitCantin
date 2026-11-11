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
        'name="formspree_receipt_opt_in"', 'v24-signup.js?v=24.5.6', '<noscript>',
    ])
    supabase_client=check('assets/js/sinjira-supabase.js',[
        "import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.0/+esm';",
        'persistSession:true', 'autoRefreshToken:true', 'detectSessionInUrl:true',
    ])
    # Toute mise à jour du SDK est un changement de code contrôlé, jamais
    # une montée silencieuse de version mineure depuis le CDN.
    if '@supabase/supabase-js@2/+esm' in supabase_client or '@supabase/supabase-js@latest/+esm' in supabase_client:
        errors.append('SDK Supabase : URL CDN flottante interdite.')
    # Les tests Playwright d'édition privée doivent intercepter le même
    # SDK figé que celui du vrai navigateur : sinon la simulation Auth ne
    # fonctionne plus et peut bloquer la vérification de déconnexion.
    literature_browser_tests=check('tests/e2e/test_literature_site.py',[
        '**/npm/@supabase/supabase-js@2.119.0/+esm*',
        'assert_private_signout_during_load(browser)',
        'assert_private_cross_device_resume_mock(browser)',
    ])
    if literature_browser_tests.count('**/npm/@supabase/supabase-js@2.119.0/+esm*') != 3:
        errors.append('Mise à jour Supabase : trois interceptions E2E attendues.')
    if '**/npm/@supabase/supabase-js@2/+esm*' in literature_browser_tests:
        errors.append('Tests navigateur : anciennes interceptions CDN flottantes.')
    signup=check('assets/js/v24-signup.js',[
        'getSupabase().auth.signUp(', 'emailRedirectTo:', '/compte/confirmer.html',
        "formspree_receipt_opt_in:d.get('formspree_receipt_opt_in')==='yes'",
        'vous devrez ensuite activer et valider la double authentification (AAL2) dans Ma sécurité.',
    ])
    confirmation=check('assets/js/sinjira-confirm-email.js',[
        "getSupabase().auth.verifyOtp(", "confirmButton?.addEventListener('click'",
        "getSupabase().auth.resend(", "options:{emailRedirectTo:", "'notify-account-confirmation'",
        "signal:AbortSignal.timeout(8500)", "resendButton.disabled=!isSinjiraBackendConfigured()",
    ])
    confirmation_page=check('compte/confirmer.html',[
        'data-confirm-button hidden', 'data-confirm-resend-form',
        'noindex,nofollow', 'sinjira-confirm-email.js?v=3',
        'data-confirm-resend-form method="post" action="/compte/confirmer.html"',
        'type="submit" disabled>Renvoyer un lien', '<noscript>',
    ])
    registry_page=check('projets/sinjira/registre/index.html',[
        'data-character-form=', 'type="submit" disabled>Transmettre ma participation',
        'name="formspree_receipt_opt_in"', 'sinjira-character-registry.js?v=24.5.8',
        'La double authentification (AAL2) est obligatoire pour tous les participants au Registre',
    ])
    security_page=check('compte/securite.html',[
        'name="sensitive_step_up"', 'Le Registre exige toujours AAL2, même si cette option est désactivée.',
        'Le Registre des Consciences exige toujours le niveau AAL2.',
    ])
    registry_js=check('assets/js/sinjira-character-registry.js',[
        "form?.addEventListener('submit',async e=>{",
        'e.preventDefault();', 'if(!registryReady||isSending||!currentUser)',
        "functions.invoke('submit-character-questionnaire'",
        "let invocationStarted=false;",
        "invocationStarted=true;",
        "result.admin_notification_created===true",
        "auth.mfa.getAuthenticatorAssuranceLevel()",
        "aal.nextLevel!=='aal2'",
        "aal.currentLevel!=='aal2'",
        "uncertainError.submissionOutcomeUnknown=true;",
        "const unknown=err?.submissionOutcomeUnknown===true;",
        "if(unknown){",
        "registryReady=false;",
        "link.href='/compte/mon-personnage.html';",
        "link.target='_blank';",
        "try{localStorage.removeItem('registre-consciences-draft-v1')}catch{",
    ])
    registry_edge=check('supabase/functions/submit-character-questionnaire/index.ts',[
        "requiredVaultUser(req)", "answers.formspree_receipt_opt_in==='yes'",
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

    # Le Registre doit annoncer honnêtement que AAL2 est obligatoire et jamais facultatif.
    if 'Si la protection renforcée est activée' in registry_page:
        errors.append('Registre : la MFA obligatoire est annoncée comme facultative.')
    if 'Le Registre, l’IA privée et la récupération peuvent demander' in security_page:
        errors.append('Ma sécurité : une préférence semble pouvoir supprimer la MFA du Registre.')

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
    # La préférence sensitive_step_up ne doit jamais permettre un POST Registre en AAL1.
    if 'const {user}=await requiredVaultUser(req);' not in registry_edge:
        errors.append('Registre : AAL2 non obligatoire sur l’Edge Function.')
    if re.search(r'const\s+user\s*=\s*await\s+requiredUser\(req\)',registry_edge):
        errors.append('Registre : frontière utilisateur standard utilisée à la place de la garde AAL2.')
    if not registry_js.index('auth.mfa.getAuthenticatorAssuranceLevel()') < registry_js.index("rpc('security_sensitive_access_status'"):
        errors.append('Registre : niveau MFA non contrôlé avant la vérification des permissions.')
    # Aucun second POST possible après une invocation réseau au résultat incertain.
    if not re.search(r'if\s*\(unknown\)\s*\{\s*registryReady=false;',registry_js):
        errors.append('Registre : second envoi encore autorisé après une réponse réseau incertaine')
    if not re.search(r'if\s*\(!invocationStarted\)\s*\{\s*await\s+cleanupUploadedPhoto\(photo_path\)',registry_js):
        errors.append('Registre : nettoyage temporaire pré-envoi non protégé')
    if re.search(r"(?m)^\s*localStorage\.removeItem\('registre-consciences-draft-v1'\);?\s*$",registry_js):
        errors.append('Registre : panne du stockage local interprétée comme échec de sauvegarde')
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
