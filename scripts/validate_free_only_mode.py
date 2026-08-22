#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def text(path:str)->str:
    p=ROOT/path
    if not p.exists():
        raise AssertionError(f'Fichier absent: {path}')
    return p.read_text('utf-8',errors='ignore')


def require(value:str,markers:list[str],label:str)->None:
    missing=[m for m in markers if m not in value]
    if missing:
        raise AssertionError(f'{label}: marqueurs absents: {missing}')


def scan_files(roots:list[Path],suffixes:set[str]):
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob('*'):
            if path.is_file() and path.suffix.lower() in suffixes:
                yield path


def main()->int:
    config=text('assets/js/sinjira-supabase-config.js')
    licenses=text('assets/js/v24-licenses.js')
    license_html=text('compte/licences.html')
    market=text('assets/js/v24-market-account.js')
    tokens=text('assets/js/v24-tokens.js')
    purchases=text('compte/mes-achats.html')
    production_workflows='\n'.join([
        text('.github/workflows/supabase-production-safe.yml'),
        text('.github/workflows/supabase-production-preflight.yml'),
    ])

    require(config,[
        'freeOnlyMode: true',
        'paidFeaturesEnabled: false',
        'paidExternalServicesEnabled: false',
        'remoteAiEnabled: false',
        'externalEmailDeliveryEnabled: false',
        'commercePublishingEnabled: false',
        'tokenPurchasesEnabled: false',
        'nativeStorePublishingEnabled: false',
        'export function isSinjiraFreeOnlyMode()'
    ],'configuration gratuite')

    require(licenses,[
        "rpc('is_sinjira_owner'",
        'Mode gratuit verrouillé',
        'SINJIRA_CONFIG.freeOnlyMode',
        "functions.invoke('redeem-license-code'"
    ],'Licences')
    if 'isSinjiraOwner' in licenses:
        raise AssertionError('Licences: le rôle propriétaire ne doit plus dépendre du helper local par courriel.')

    require(license_html,[
        'Aucun achat ni abonnement n’est proposé sur cette page.',
        'Aucun système de paiement en ligne n’est activé actuellement.',
        'v24-licenses.js?v=24.4.62'
    ],'page Licences')

    # Marché: la phase actuelle doit rester limitée aux brouillons.
    require(market,["status:'draft'",'Aucun paiement ni débit de jeton n’est actif'],'Marché')
    forbidden_market=["status:'published'","status:'active'",'checkout','payment_intent','stripe']
    for marker in forbidden_market:
        if marker.lower() in market.lower():
            raise AssertionError(f'Marché: activation commerciale interdite en mode gratuit: {marker}')

    # Jetons: lecture du grand livre uniquement, aucun achat/crédit client.
    require(tokens,["from('token_ledger').select"],'Jetons')
    for marker in ("from('token_ledger').insert","from('token_ledger').update",'functions.invoke','checkout','stripe'):
        if marker.lower() in tokens.lower():
            raise AssertionError(f'Jetons: opération payante ou écriture client interdite: {marker}')

    require(purchases,['La boutique n’est pas encore ouverte.'],'Mes achats')

    # Les workflows de production ne doivent pas importer ni synchroniser de secret OpenAI
    # tant que freeOnlyMode/remoteAiEnabled gardent l'IA distante payante désactivée.
    for marker in ('OPENAI_API_KEY','OPTIONAL_OPENAI_API_KEY','OPENAI_CHARACTER_MODEL','OPTIONAL_OPENAI_CHARACTER_MODEL'):
        if marker in production_workflows:
            raise AssertionError(f'Production: pont IA distante interdit en mode gratuit: {marker}')

    # Aucun SDK/end-point de paiement ou IA payante ne doit être actif dans le runtime navigateur.
    browser_roots=[ROOT/'assets'/'js',ROOT/'compte',ROOT/'projets'/'sinjira']
    forbidden_patterns={
        'Stripe JS':r'https?://js\.stripe\.com|Stripe\s*\(',
        'Stripe checkout':r'checkout\.sessions|payment_intents?|stripe\.redirectToCheckout',
        'PayPal SDK':r'paypal\.com/sdk/js',
        'Lemon Squeezy':r'lemonsqueezy',
        'Paddle':r'cdn\.paddle\.com|Paddle\.Checkout',
        'OpenAI API':r'api\.openai\.com',
        'Anthropic API':r'api\.anthropic\.com',
        'Gemini API':r'generativelanguage\.googleapis\.com',
    }
    offenders=[]
    for path in scan_files(browser_roots,{'.js','.html'}):
        content=path.read_text('utf-8',errors='ignore')
        for label,pattern in forbidden_patterns.items():
            if re.search(pattern,content,re.I):
                offenders.append(f'{path.relative_to(ROOT)}: {label}')
    if offenders:
        raise AssertionError('Mode gratuit: intégrations payantes actives détectées:\n- '+'\n- '.join(offenders))

    # Les Edge Functions peuvent être préparées pour de futurs fournisseurs, mais aucun
    # transport payant (courriel/SMS/IA/paiement) ne doit être activé dans le runtime serveur.
    server_patterns={
        'SendGrid':r'api\.sendgrid\.com|SENDGRID_API_KEY',
        'Mailgun':r'api\.mailgun\.net|MAILGUN_API_KEY',
        'Postmark':r'api\.postmarkapp\.com|POSTMARK_SERVER_TOKEN',
        'Resend':r'api\.resend\.com|RESEND_API_KEY',
        'Amazon SES':r'email\.[a-z0-9-]+\.amazonaws\.com|AWS_SES',
        'Twilio':r'api\.twilio\.com|TWILIO_(?:ACCOUNT|AUTH|SID)',
        'Vonage':r'api\.vonage\.com|VONAGE_API',
        'Telnyx':r'api\.telnyx\.com|TELNYX_API',
        'OpenAI API':r'api\.openai\.com|OPENAI_API_KEY',
        'Anthropic API':r'api\.anthropic\.com|ANTHROPIC_API_KEY',
        'Stripe serveur':r'api\.stripe\.com|STRIPE_SECRET_KEY',
    }
    server_offenders=[]
    for path in scan_files([ROOT/'supabase'/'functions'],{'.ts','.js'}):
        content=path.read_text('utf-8',errors='ignore')
        for label,pattern in server_patterns.items():
            if re.search(pattern,content,re.I):
                server_offenders.append(f'{path.relative_to(ROOT)}: {label}')
    if server_offenders:
        raise AssertionError('Services externes payants: activation serveur détectée:\n- '+'\n- '.join(server_offenders))

    # On peut construire l'application mobile et ses métadonnées, mais aucune action CI
    # ne doit publier vers Apple/Google tant que nativeStorePublishingEnabled=false.
    workflow_text='\n'.join(
        p.read_text('utf-8',errors='ignore')
        for p in scan_files([ROOT/'.github'/'workflows'],{'.yml','.yaml'})
    )
    store_publish_patterns={
        'EAS submit':r'\beas\s+submit\b',
        'Expo submit':r'\bexpo\s+submit\b',
        'Fastlane upload':r'\bfastlane\s+(?:pilot|supply|deliver)\b',
        'Google Play deploy':r'google-play|play-console|upload.*aab',
        'App Store deploy':r'app-store-connect|altool|notarytool',
    }
    for label,pattern in store_publish_patterns.items():
        if re.search(pattern,workflow_text,re.I):
            raise AssertionError(f'Publication mobile payante/interne interdite sans accord explicite: {label}')

    # Héritage numérique V24.5.2 : la remise reste manuelle; aucun fournisseur externe
    # de courriel ne doit être requis pour générer ou remettre les PDF.
    heritage='\n'.join([
        text('HERITAGE_NUMERIQUE_V24_5_2.md'),
        text('supabase/functions/life-story-export/index.ts'),
        text('supabase/functions/life-story-delivery/index.ts'),
    ])
    require(heritage,[
        'Aucun fournisseur externe de courriel',
        "transport: 'manual_or_future_sender'"
    ],'Héritage numérique sans transport payant')

    print('OK mode gratuit V24.5.2: paiements, IA distante, transport courriel/SMS payant, commerce publié, achats de jetons et publication App Store/Play Store restent désactivés; le code peut être préparé sans activation externe.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
