#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260917223000_sinjira_v25_junior_community.sql'
TEST=ROOT/'supabase/tests/child_community_v25.test.sql'
PAGE=ROOT/'compte/communaute-junior.html'
RULES_PAGE=ROOT/'compte/regles-communaute-junior.html'
CLIENT=ROOT/'assets/js/sinjira-community-junior-v25.js'
RULES_CLIENT=ROOT/'assets/js/sinjira-community-junior-rules-v25.js'
ACCOUNT=ROOT/'assets/js/sinjira-account.js'
COMMUNITY=ROOT/'assets/js/sinjira-community-real.js'
RELATIONS=ROOT/'assets/js/v24-relations.js'
RELATIONS_HTML=ROOT/'compte/relations.html'
WORKFLOW=ROOT/'.github/workflows/sinjira-child-community-v25.yml'

errors=[]

def read(path):
    if not path.exists():
        errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
        return ''
    return path.read_text('utf-8')

def compact(text):
    return ''.join(text.lower().split())

def req(condition,message):
    if not condition:
        errors.append(message)

mig=read(MIG)
test=read(TEST)
page=read(PAGE)
rules_page=read(RULES_PAGE)
client=read(CLIENT)
rules_client=read(RULES_CLIENT)
account=read(ACCOUNT)
community=read(COMMUNITY)
relations=read(RELATIONS)
relations_html=read(RELATIONS_HTML)
workflow=read(WORKFLOW) if WORKFLOW.exists() else ''

m=compact(mig)
t=compact(test)
p=page.lower()
rp=rules_page.lower()
c=compact(client)
rc=compact(rules_client)
a=compact(account)
co=compact(community)
r=compact(relations)
rh=relations_html.lower()
w=workflow.lower()

# Serveur : surface distincte, tables non accessibles directement et garde parentale.
for table in ('junior_community_guardian_consents','junior_community_posts','junior_community_comments'):
    req(f'createtableifnotexistspublic.{table}' in m,f'Table Junior absente: {table}')
    req(f'revokeallontablepublic.{table}frompublic,anon,authenticated' in m,f'Accès direct navigateur non révoqué: {table}')
req("public.sinjira_age_band(p_user_id)='child'" in m,'La Communauté Junior n est pas bornée à la bande child 11–12.')
req('public.sinjira_parent_can_supervise(uid,p_child_user_id)' in m,'Le parent ne doit pas pouvoir activer Junior sans lien de supervision vérifié.')
req('junior_community_guardian_consents' in m and 'revoked_atisnull' in m,'Le consentement parent Junior révocable est absent.')
req("'sinjira-junior-rules-v1-2026-09-17'" in m,'Version de règles Junior absente.')

# Minimisation identité et séparation sociale.
req("'explorateur-'||upper(substr(md5(" in m,'Le pseudonyme Junior généré côté serveur est absent.')
feed_section=m[m.find('createorreplacefunctionpublic.junior_community_feed'):m.find('createorreplacefunctionpublic.junior_community_create_post')]
req('profiles' not in feed_section and 'social_profiles' not in feed_section,'Le fil Junior ne doit pas lire les profils réels.')
req("'author_alias',private.sinjira_junior_alias" in m,'Le fil ne renvoie pas le pseudonyme Junior.')
req('p.author_user_id=uidmine' in m and "'mine',c.author_user_id=uid" in m,'Le client doit recevoir seulement un indicateur own/mine, pas l identité auteur.')
req('social_real_messages' not in m and 'social_character_messages' not in m,'La migration Junior ne doit créer aucune messagerie privée.')
req('public.sinjira_can_social_interact' not in feed_section,'Le fil Junior ne doit pas réutiliser la frontière sociale youth/adulte.')

# Garde de contenu Junior.
for marker,msg in (
    ('external_contact_forbidden','Les coordonnées/liens externes ne sont pas bloqués.'),
    ('sexual_content_forbidden','Le contenu sexuel Junior n est pas bloqué.'),
    ('meetup_or_secrecy_forbidden','Les rencontres/secrets dangereux ne sont pas bloqués.'),
    ('money_or_commerce_forbidden','Le commerce Junior n est pas bloqué.'),
):
    req(marker in m,msg)
req("interval'1hour')>=5" in m,'Le débit de publications Junior n est pas borné.')
req("interval'1hour')>=30" in m,'Le débit de commentaires Junior n est pas borné.')

# Signalement + blocage vers la modération existante.
req("insertintopublic.social_reports" in m and "'source','junior_community'" in m,'Les signalements Junior ne rejoignent pas la modération existante.')
req('insertintopublic.social_blocks' in m,'Le masquage immédiat après signalement est absent.')

# Supervision sans surveillance.
req("'content_visible_to_guardian',false" in m,'Le parent pourrait recevoir le contenu Junior.')
req("'private_messages_available',false" in m,'Le contrat ne prouve pas l absence de messages privés Junior.')

# Interface enfant.
for marker,msg in (
    ('communauté junior sinjira','Titre Communauté Junior absent.'),
    ('aucun message privé','L interface n explique pas l absence de messages privés.'),
    ('adultes et 13–17 ans séparés','L interface n explique pas la séparation des cohortes.'),
    ('signaler et masquer','L action de sécurité Junior est absente.'),
    ('pseudonyme junior automatique','La pseudonymisation Junior n est pas expliquée.'),
):
    req(marker in p,msg)
req("s.rpc('junior_community_feed'" in c,'Le client Junior n utilise pas le RPC de fil.')
req("s.rpc('junior_community_create_post'" in c,'Le client Junior ne publie pas via RPC.')
req("s.rpc('junior_community_report_content'" in c,'Le client Junior ne signale pas via RPC.')
req(".from('junior_community_" not in client.lower(),'Le client Junior contourne les RPC avec un accès table direct.')
req("if(band!=='child')" in c,'Le client Junior ne vérifie pas la bande child.')
req("location.replace('/compte/communaute.html')" in c,'Le client Junior ne renvoie pas les autres âges vers leur communauté.')

# Règles Junior et activation parent.
req('pas de messages privés' in rp and 'pas de rencontre privée' in rp and 'pas d’argent ni de commerce' in rp,'Les règles Junior sont incomplètes.')
req("s.rpc('junior_community_accept_rules')" in rc,'L acceptation des règles Junior ne passe pas par RPC.')
req('data-junior-community-children' in rh,'Relations ne contient pas le panneau d activation Junior.')
req("s.rpc('guardian_set_junior_community'" in r,'Relations ne peut pas activer/révoquer la Communauté Junior.')
req("s.rpc('junior_guardian_summary'" in r,'Relations ne peut pas lire le résumé de sécurité sans contenu.')

# Navigation fail-closed minimale pour 11–12.
req("ageband!=='child'" in a and "link.href='communaute-junior.html'" in a,'La navigation du compte ne route pas child vers Junior.')
for route in ('messages.html','rencontres.html','reseau-personnage.html','marche.html','jetons.html','mes-achats.html','contributions.html'):
    req(f"'{route}'" in a,f'Route sensible non masquée pour child: {route}')
req("ageband==='child'" in co and "communaute-junior.html" in co,'La Communauté générale ne redirige pas un compte child.')

# Tests comportementaux.
req('selectplan(33);' in t,'Plan pgTAP Junior inattendu.')
for marker,msg in (
    ('aucunselectdirectsurpublicationsjunior','Le test ne prouve pas l absence de SELECT direct.'),
    ('leparentactiveexplicitementlacommunautéjunior','Le test ne prouve pas l opt-in parent.'),
    ('levraipseudo/profildupremierenfantnestpasexposé','Le test ne prouve pas la pseudonymisation.'),
    ('luuidauteurnestpasexposé','Le test ne prouve pas la minimisation UUID.'),
    ('unlienexterneestrefusécôtéserveur','Le test ne prouve pas le blocage de liens.'),
    ('unadultenepeutpaslirelefiljunior','Le test ne prouve pas l isolation adulte.'),
    ('lamessagerieetlesréseauxsociauxhistoriquesrestentfermés','Le test ne prouve pas l absence de messagerie.'),
    ('lerésuméparentnedonnepasaccèsaucontenu','Le test ne prouve pas la supervision sans surveillance.'),
    ('à13anslecomptequitteautomatiquementlabandejunior','Le test ne prouve pas la sortie Junior à 13 ans.'),
):
    req(marker in t,msg)

# CI locale uniquement, lecture seule et sans capacité de production.
if workflow:
    req('permissions:\n  contents: read' in workflow,'Le workflow Junior doit rester contents:read.')
    req('persist-credentials: false' in workflow,'Le checkout Junior doit désactiver les credentials persistés.')
    req('secrets.' not in w,'Le workflow Junior ne doit référencer aucun secret.')
    req('pull_request_target' not in w,'pull_request_target interdit.')
    for forbidden in ('supabase db push','supabase link','supabase functions deploy','supabase secrets set'):
        req(forbidden not in w,f'Commande production interdite dans le workflow Junior: {forbidden}')
    req('supabase db reset' in w and 'supabase test db supabase/tests/child_community_v25.test.sql' in w,'Le workflow Junior ne rejoue pas la base et le pgTAP local.')

if errors:
    print(f'ECHEC Communauté Junior V25: {len(errors)} problème(s).')
    for error in errors:
        print('- '+error)
    raise SystemExit(1)

print('OK V25: Communauté Junior 11–12 isolée, parent-opt-in, pseudonymisée, sans DM/coordonnées/commerce et testée localement.')
