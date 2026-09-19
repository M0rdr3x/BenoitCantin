#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
COMPTE=ROOT/'compte'
ACCOUNT=ROOT/'assets/js/sinjira-account.js'
DOC=ROOT/'docs/SINJIRA_CHILD_ACCESS_MATRIX_V25.md'

ALLOWED={
    'index.html','bibliotheque.html','documents.html','projet.html','blocages.html','communaute-junior.html','confidentialite-joueur.html',
    'histoire-de-vie.html','moderation.html','mon-personnage.html','mes-personnages.html',
    'notifications.html','parametres.html','profil.html','registre-personnel.html',
    'regles-communaute-junior.html','relations.html','securite.html','vie-privee.html',
}
AUTH={
    'connexion.html','inscription.html','mot-de-passe-oublie.html',
    'reinitialiser-mot-de-passe.html','mfa.html',
}
REDIRECTS={
    'communaute.html':'communaute-junior.html',
    'regles-communaute.html':'regles-communaute-junior.html',
}
RESTRICTED={
    'contributions.html','emploi.html','jetons.html',
    'licences.html','marche.html','mes-achats.html','mes-commentaires.html','mes-lectures.html',
    'mes-parties.html','messages-personnage.html','messages-reels.html','messages.html',
    'mon-ia.html','monde-parallele.html','playtests.html','rencontres.html',
    'reseau-personnage.html','signaler-deces.html',
}

errors=[]
def req(cond,msg):
    if not cond: errors.append(msg)

actual={p.name for p in COMPTE.glob('*.html')}
categories=[ALLOWED,AUTH,set(REDIRECTS),RESTRICTED]
union=set().union(*categories)

req(len(actual)==44,f'Nombre de routes compte inattendu: {len(actual)} au lieu de 44.')
req(union==actual,'La matrice 11–12 ne couvre pas exactement les routes compte: manquantes=%s; en trop=%s' % (sorted(actual-union),sorted(union-actual)))
for i,left in enumerate(categories):
    for right in categories[i+1:]:
        req(not (left & right),f'Catégories enfant non disjointes: {sorted(left & right)}')

account=ACCOUNT.read_text('utf-8')
doc=DOC.read_text('utf-8')

allowed_match=re.search(r"const CHILD_11_12_ALLOWED_ROUTES=new Set\(\[(.*?)\]\);",account,re.S)
req(allowed_match is not None,'Ensemble CHILD_11_12_ALLOWED_ROUTES absent.')
if allowed_match:
    js_allowed=set(re.findall(r"'([^']+\.html)'",allowed_match.group(1)))
    req(js_allowed==ALLOWED|AUTH,'Routes autorisées JS divergentes: attendu=%s obtenu=%s' % (sorted(ALLOWED|AUTH),sorted(js_allowed)))

redirect_match=re.search(r"const CHILD_11_12_ROUTE_REDIRECTS=new Map\(\[(.*?)\]\);",account,re.S)
req(redirect_match is not None,'Map CHILD_11_12_ROUTE_REDIRECTS absente.')
if redirect_match:
    pairs=dict(re.findall(r"\['([^']+\.html)','/compte/([^']+\.html)'\]",redirect_match.group(1)))
    req(pairs==REDIRECTS,'Redirections Junior divergentes: attendu=%s obtenu=%s' % (REDIRECTS,pairs))

compact=''.join(account.split())
req("location.pathname.startsWith('/compte/')&&!CHILD_11_12_ALLOWED_ROUTES.has(currentLeaf)" in account,'La garde directe fail-closed des routes compte est absente.')
req("next.searchParams.set('from','restricted')" in account,'La redirection restreinte n indique pas son origine.')
req("next.searchParams.set('module',currentLeaf)" in account,'La redirection restreinte ne conserve pas le module demandé.')
req("if(!CHILD_11_12_ALLOWED_ROUTES.has(leaf))link.hidden=true" in compact,'Les liens non autorisés ne sont pas masqués par défaut.')

for name in sorted(RESTRICTED|set(REDIRECTS)):
    text=(COMPTE/name).read_text('utf-8')
    req('sinjira-account.js' in text,f'{name}: la garde de compte n est pas chargée.')

for name in sorted(actual):
    req(f'`{name}`' in doc,f'Document matrice: route absente {name}.')
req('**44**' in doc,'Le document ne fixe pas la couverture à 44 routes.')
req('fail-closed' in doc.lower(),'Le principe fail-closed n est pas documenté.')
req('ne remplace pas les contrôles serveur' in doc.lower(),'La matrice doit rappeler que la navigation ne remplace pas la sécurité serveur.')
req('guardian_links' in doc and 'revoked_at' in doc,'La matrice doit documenter le fail-closed de révocation multi-tuteur Junior.')
req('ne peut ni maintenir l’activation Junior ni conserver l’enfant dans la liste Junior' in doc,'La matrice doit expliciter les deux effets de la révocation tuteur Junior.')

junior=(COMPTE/'communaute-junior.html').read_text('utf-8')
junior_js=(ROOT/'assets/js/sinjira-community-junior-v25.js').read_text('utf-8')
req('data-junior-access-note' in junior,'Le message de repli Junior est absent.')
req("accessParams.get('from')==='restricted'" in junior_js,'Le client Junior n affiche pas le message après redirection restreinte.')

if errors:
    print(f'ECHEC matrice accès enfant V25: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)

print('OK V25: 44 routes compte classées explicitement; comptes 11–12 fail-closed avec redirections Junior et garde CI.')
