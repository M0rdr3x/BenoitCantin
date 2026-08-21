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
        'remoteAiEnabled: false',
        'commercePublishingEnabled: false',
        'tokenPurchasesEnabled: false',
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

    # Les workflows de production ne doivent plus importer ni synchroniser de secret OpenAI
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
    for root in browser_roots:
        if not root.exists():
            continue
        for path in root.rglob('*'):
            if path.suffix.lower() not in {'.js','.html'}:
                continue
            content=path.read_text('utf-8',errors='ignore')
            for label,pattern in forbidden_patterns.items():
                if re.search(pattern,content,re.I):
                    offenders.append(f'{path.relative_to(ROOT)}: {label}')
    if offenders:
        raise AssertionError('Mode gratuit: intégrations payantes actives détectées:\n- '+'\n- '.join(offenders))

    print('OK mode gratuit V24.4.91: paiements, IA distante, commerce publié et achats de jetons verrouillés; aucun secret OpenAI n’est synchronisé en production.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
