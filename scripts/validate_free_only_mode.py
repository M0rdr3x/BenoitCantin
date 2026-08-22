#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def text(path:str)->str:
    p=ROOT/path
    if not p.exists():raise AssertionError(f'Fichier absent: {path}')
    return p.read_text('utf-8',errors='ignore')


def require(value:str,markers:list[str],label:str)->None:
    missing=[m for m in markers if m not in value]
    if missing:raise AssertionError(f'{label}: marqueurs absents: {missing}')


def scan_files(roots:list[Path],suffixes:set[str]):
    for root in roots:
        if not root.exists():continue
        for path in root.rglob('*'):
            if path.is_file() and path.suffix.lower() in suffixes:yield path


def main()->int:
    config=text('assets/js/sinjira-supabase-config.js')
    licenses=text('assets/js/v24-licenses.js')
    license_html=text('compte/licences.html')
    market=text('assets/js/v24-market-account.js')
    tokens=text('assets/js/v24-tokens.js')
    purchases=text('compte/mes-achats.html')
    workflows='\n'.join(p.read_text('utf-8',errors='ignore') for p in scan_files([ROOT/'.github'/'workflows'],{'.yml','.yaml'}))

    require(config,[
        'freeOnlyMode: true','paidFeaturesEnabled: false','paidExternalServicesEnabled: false',
        'remoteAiEnabled: false','externalEmailDeliveryEnabled: false',
        'commercePublishingEnabled: false','tokenPurchasesEnabled: false',
        'nativeStorePublishingEnabled: false','export function isSinjiraFreeOnlyMode()'
    ],'configuration gratuite')

    require(licenses,["rpc('is_sinjira_owner'",'Mode gratuit verrouillé','SINJIRA_CONFIG.freeOnlyMode',"functions.invoke('redeem-license-code'"],'Licences')
    if 'isSinjiraOwner' in licenses:raise AssertionError('Licences: rôle propriétaire dépend encore du helper local par courriel.')
    require(license_html,['Aucun achat ni abonnement n’est proposé sur cette page.','Aucun système de paiement en ligne n’est activé actuellement.'],'page Licences')

    require(market,["status:'draft'",'Aucun paiement ni débit de jeton n’est actif'],'Marché')
    for marker in ("status:'published'","status:'active'",'checkout','payment_intent','stripe'):
        if marker.lower() in market.lower():raise AssertionError(f'Marché: activation commerciale interdite: {marker}')

    require(tokens,["from('token_ledger').select"],'Jetons')
    for marker in ("from('token_ledger').insert","from('token_ledger').update",'checkout','stripe'):
        if marker.lower() in tokens.lower():raise AssertionError(f'Jetons: écriture/achat interdit: {marker}')
    require(purchases,['La boutique n’est pas encore ouverte.'],'Mes achats')

    # Le navigateur ne doit contenir aucun SDK/end-point payant actif.
    browser_patterns={
        'Stripe':r'https?://js\.stripe\.com|Stripe\s*\(|checkout\.sessions|payment_intents?',
        'PayPal':r'paypal\.com/sdk/js','Lemon Squeezy':r'lemonsqueezy','Paddle':r'cdn\.paddle\.com|Paddle\.Checkout',
        'OpenAI':r'api\.openai\.com','Anthropic':r'api\.anthropic\.com','Gemini':r'generativelanguage\.googleapis\.com'
    }
    offenders=[]
    for path in scan_files([ROOT/'assets'/'js',ROOT/'compte',ROOT/'projets'/'sinjira'],{'.js','.html'}):
        content=path.read_text('utf-8',errors='ignore')
        for label,pattern in browser_patterns.items():
            if re.search(pattern,content,re.I):offenders.append(f'{path.relative_to(ROOT)}: {label}')
    if offenders:raise AssertionError('Mode gratuit: intégrations navigateur payantes détectées:\n- '+'\n- '.join(offenders))

    # Le serveur peut garder une intégration préparée. Elle est valide uniquement si
    # le fichier qui contient le fournisseur porte un verrou de compilation à false.
    paid_provider_pattern=re.compile(r'api\.resend\.com|RESEND_API_KEY|api\.sendgrid\.com|SENDGRID_API_KEY|api\.mailgun\.net|MAILGUN_API_KEY|api\.postmarkapp\.com|POSTMARK_SERVER_TOKEN|api\.stripe\.com|STRIPE_SECRET_KEY|api\.twilio\.com|TWILIO_',re.I)
    remote_ai_pattern=re.compile(r'api\.openai\.com|OPENAI_API_KEY|api\.anthropic\.com|ANTHROPIC_API_KEY|generativelanguage\.googleapis\.com',re.I)
    dormant_errors=[]
    for path in scan_files([ROOT/'supabase'/'functions'],{'.ts','.js'}):
        content=path.read_text('utf-8',errors='ignore')
        if paid_provider_pattern.search(content):
            if not re.search(r'const\s+PAID_EXTERNAL_SERVICES_ENABLED\s*=\s*false\s*;',content):
                dormant_errors.append(f'{path.relative_to(ROOT)}: fournisseur payant sans PAID_EXTERNAL_SERVICES_ENABLED=false')
            if 'PAID_EXTERNAL_SERVICES_ENABLED' not in content:
                dormant_errors.append(f'{path.relative_to(ROOT)}: fournisseur payant non conditionné')
        if remote_ai_pattern.search(content):
            if not re.search(r'const\s+REMOTE_AI_ENABLED\s*=\s*false\s*;',content):
                dormant_errors.append(f'{path.relative_to(ROOT)}: IA distante sans REMOTE_AI_ENABLED=false')
    if dormant_errors:raise AssertionError('Intégrations externes préparées mais non verrouillées:\n- '+'\n- '.join(dormant_errors))

    # Contrat renforcé sur les quatre chemins historiques connus.
    for path,markers in {
        'supabase/functions/send-game-report/index.ts':['const PAID_EXTERNAL_SERVICES_ENABLED=false','PAID_EXTERNAL_SERVICE_DISABLED'],
        'supabase/functions/send-player-sheet/index.ts':['const PAID_EXTERNAL_SERVICES_ENABLED=false','PAID_EXTERNAL_SERVICE_DISABLED'],
        'supabase/functions/submit-fracture-endgame/index.ts':['const PAID_EXTERNAL_SERVICES_ENABLED=false','if(PAID_EXTERNAL_SERVICES_ENABLED&&resend&&from)'],
        'supabase/functions/submit-character-questionnaire/index.ts':['const PAID_EXTERNAL_SERVICES_ENABLED=false','const REMOTE_AI_ENABLED=false','if(!REMOTE_AI_ENABLED)return null','if(!PAID_EXTERNAL_SERVICES_ENABLED)return']
    }.items():require(text(path),markers,path)

    # Aucun workflow ne doit synchroniser de secret d'IA distante. La présence éventuelle
    # d'un ancien secret courriel ne peut pas activer les fonctions car les verrous serveur
    # ci-dessus sont compilés à false; les workflows ne valent jamais autorisation d'achat.
    for marker in ('OPENAI_API_KEY','OPTIONAL_OPENAI_API_KEY','OPENAI_CHARACTER_MODEL','OPTIONAL_OPENAI_CHARACTER_MODEL','ANTHROPIC_API_KEY'):
        if marker in workflows:raise AssertionError(f'Workflow production: secret IA distante interdit: {marker}')

    # Construire le mobile est permis; soumettre aux stores ne l'est pas.
    for label,pattern in {
        'EAS submit':r'\beas\s+submit\b','Expo submit':r'\bexpo\s+submit\b',
        'Fastlane store upload':r'\bfastlane\s+(?:pilot|supply|deliver)\b',
        'Google Play deploy':r'play-console|upload.*\.aab','App Store deploy':r'app-store-connect|altool|notarytool'
    }.items():
        if re.search(pattern,workflows,re.I):raise AssertionError(f'Publication mobile interdite sans accord explicite: {label}')

    heritage='\n'.join([text('HERITAGE_NUMERIQUE_V24_5_2.md'),text('supabase/functions/life-story-export/index.ts'),text('supabase/functions/life-story-delivery/index.ts')])
    require(heritage,['Aucun fournisseur externe de courriel',"transport: 'manual_or_future_sender'"],'Héritage numérique')
    require(text('SERVICES_EXTERNES_PAYANTS.md'),['Préparer une intégration ne constitue jamais une autorisation de l’activer','décision explicite'],'Politique services payants')

    print('OK mode gratuit V24.5.2: intégrations payantes préparables mais dormantes; paiements, IA distante, courriel/SMS externe, achats de jetons et publication App Store/Play Store restent désactivés.')
    return 0


if __name__=='__main__':raise SystemExit(main())
