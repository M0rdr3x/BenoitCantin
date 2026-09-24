#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260917223000_sinjira_v25_junior_community.sql'
COMMENT_VISIBILITY=ROOT/'supabase/migrations/20260924173000_sinjira_v25_junior_comment_author_visibility.sql'
HIDDEN_POST_COMMENT_GUARD=ROOT/'supabase/migrations/20260924191000_sinjira_v25_junior_hidden_post_comment_guard.sql'
BOUNDARY=ROOT/'supabase/migrations/20260919123000_sinjira_v25_public_rpc_boundary.sql'
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
BROWSER_TEST=ROOT/'tests/e2e/test_child_community.py'
ADMIN_EDGE=ROOT/'supabase/functions/admin-social-v20/index.ts'
ADMIN_CLIENT=ROOT/'assets/js/sinjira-admin-social-v20.js'

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
comment_visibility=read(COMMENT_VISIBILITY)
hidden_post_comment_guard=read(HIDDEN_POST_COMMENT_GUARD)
boundary=read(BOUNDARY)
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
browser_test=read(BROWSER_TEST)
admin_edge=read(ADMIN_EDGE)
admin_client=read(ADMIN_CLIENT)

m=compact(mig)
cv=compact(comment_visibility)
hpc=compact(hidden_post_comment_guard)
b=compact(boundary)
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
bt=browser_test.lower()
ae=compact(admin_edge)
ac=compact(admin_client)

# Serveur : surface distincte, tables non accessibles directement et garde parentale.
for table in ('junior_community_guardian_consents','junior_community_posts','junior_community_comments'):
    req(f'createtableifnotexistspublic.{table}' in m,f'Table Junior absente: {table}')
    req(f'revokeallontablepublic.{table}frompublic,anon,authenticated' in m,f'Accès direct navigateur non révoqué: {table}')
req("public.sinjira_age_band(p_user_id)='child'" in m,'La Communauté Junior n est pas bornée à la bande child 11–12.')
req('public.sinjira_parent_can_supervise(uid,p_child_user_id)' in m,'Le parent ne doit pas pouvoir activer Junior sans lien de supervision vérifié.')
req('junior_community_guardian_consents' in m and 'revoked_atisnull' in m,'Le consentement parent Junior révocable est absent.')
req("'sinjira-junior-rules-v1-2026-09-17'" in m,'Version de règles Junior absente.')
req('createorreplacefunctionprivate.sinjira_is_junior(p_user_iduuid)' in m,'Le helper arbitraire de bande Junior n est pas privé.')
req('createorreplacefunctionprivate.sinjira_junior_community_enabled(p_user_iduuid)' in m,'Le helper arbitraire d activation Junior n est pas privé.')
req('createorreplacefunctionprivate.has_accepted_junior_community_rules(p_user_iduuid)' in m,'Le helper arbitraire de règles Junior n est pas privé.')
req('createorreplacefunctionpublic.sinjira_junior_community_enabled()' in m,'Le RPC self-only d activation Junior est absent.')
req('createorreplacefunctionpublic.has_accepted_junior_community_rules()' in m,'Le RPC self-only des règles Junior est absent.')
req('createorreplacefunctionpublic.sinjira_junior_community_enabled(p_user_iduuid' not in m,'Un RPC public permet encore de sonder l activation Junior par UUID.')
req('createorreplacefunctionpublic.has_accepted_junior_community_rules(p_user_iduuid' not in m,'Un RPC public permet encore de sonder les règles Junior par UUID.')
req('createorreplacefunctionpublic.sinjira_is_junior(p_user_iduuid' not in m,'Un RPC public permet encore de sonder la bande Junior par UUID.')
req('createorreplacefunctionpublic.sinjira_my_age_band()' in m and 'securitydefiner' in m[m.find('createorreplacefunctionpublic.sinjira_my_age_band()'):m.find('--helpersarbitraires')],'Le wrapper sinjira_my_age_band n est pas SECURITY DEFINER dans la dernière migration Junior.')
req('revokeallonfunctionpublic.sinjira_my_age_band()frompublic,anon,authenticated' in m and 'grantexecuteonfunctionpublic.sinjira_my_age_band()toanon,authenticated,service_role' in m,'ACL finale du wrapper self-only incompatible avec les RLS publiques.')
req('as$self_age$selectpublic.sinjira_age_band(auth.uid());$self_age$;' in m,'Le wrapper sinjira_my_age_band historique doit utiliser un délimiteur SQL nommé valide.')
req('createorreplacefunctionpublic.sinjira_my_age_band()returnstextlanguagesqlstablesecuritydefinersetsearch_path=pg_catalog,public,authas$self_age$selectpublic.sinjira_age_band(auth.uid());$self_age$;' in m,'Le wrapper sinjira_my_age_band initial doit rester self-only, SECURITY DEFINER et borné par search_path.')
for marker in (
    'createschemaifnotexistssinjira_v25_internal',
    "'sinjira_my_age_band'",
    'securityinvoker',
    'v_count<>23',
    'v_anon_count<>3',
):
    req(marker in b,f'Frontière RPC V25 finale incomplète: {marker}')
req('20260919123000_sinjira_v25_public_rpc_boundary.sql' in w,'La CI Junior ne surveille pas la frontière RPC V25 finale.')

# Minimisation identité et séparation sociale.
req("'explorateur-'||upper(substr(md5(" in m,'Le pseudonyme Junior généré côté serveur est absent.')
feed_section=m[m.find('createorreplacefunctionpublic.junior_community_feed'):m.find('createorreplacefunctionpublic.junior_community_create_post')]
req('profiles' not in feed_section and 'social_profiles' not in feed_section,'Le fil Junior ne doit pas lire les profils réels.')
req("'author_alias',private.sinjira_junior_alias" in m,'Le fil ne renvoie pas le pseudonyme Junior.')
req('p.author_user_id=uidmine' in m and "'mine',c.author_user_id=uid" in m,'Le client doit recevoir seulement un indicateur own/mine, pas l identité auteur.')
req('social_real_messages' not in m and 'social_character_messages' not in m,'La migration Junior ne doit créer aucune messagerie privée.')
req('public.sinjira_can_social_interact' not in feed_section,'Le fil Junior ne doit pas réutiliser la frontière sociale youth/adulte.')

# Révocation cohérente des auteurs de commentaires : le correctif forward-only
# modifie l implémentation interne après la frontière RPC sans réouvrir un DEFINER public.
req('createorreplacefunctionsinjira_v25_internal.junior_community_feed(p_limitintegerdefault30)' in cv,
    'Le correctif de visibilité des commentaires Junior ne redéfinit pas le fil interne final.')
req('private.sinjira_is_junior(c.author_user_id)' in cv
    and 'private.sinjira_junior_community_enabled(c.author_user_id)' in cv,
    'Le fil Junior laisse encore visible un commentaire dont l auteur a quitté la bande Junior ou perdu son consentement.')
req('createorreplacefunctionpublic.junior_community_feed' not in cv,
    'Le correctif commentaires ne doit pas recréer un SECURITY DEFINER dans le schéma public.')
req('revokeallonfunctionsinjira_v25_internal.junior_community_feed(integer)frompublic,anon,authenticated' in cv
    and 'grantexecuteonfunctionsinjira_v25_internal.junior_community_feed(integer)toauthenticated,service_role' in cv,
    'Les ACL finales du fil Junior interne ne sont pas bornées.')

# Une publication masquée par une décision humaine ne doit plus accepter de nouveaux commentaires.
req('createorreplacefunctionsinjira_v25_internal.junior_community_create_comment(p_post_iduuid,p_bodytext)' in hpc,
    'Le correctif de modération ne redéfinit pas la création de commentaire Junior interne finale.')
req("public.moderation_content_visible('real','post',p.id)" in hpc,
    'La création de commentaire Junior ne respecte pas encore la visibilité de modération du post.')
req('createorreplacefunctionpublic.junior_community_create_comment' not in hpc,
    'Le correctif de commentaire masqué ne doit pas recréer un SECURITY DEFINER public.')
req('revokeallonfunctionsinjira_v25_internal.junior_community_create_comment(uuid,text)frompublic,anon,authenticated' in hpc
    and 'grantexecuteonfunctionsinjira_v25_internal.junior_community_create_comment(uuid,text)toauthenticated,service_role' in hpc,
    'Les ACL finales de création de commentaire Junior interne ne sont pas bornées.')

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

# La migration d'introduction doit déjà porter les protections finales afin d'éviter
# toute fenêtre transitoire moins sûre pendant un db push séquentiel.
req("ifv_enabledandcoalesce(auth.jwt()->>'aal','aal1')<>'aal2'then" in m and "mfa_aal2_required" in m,
    "La migration Junior initiale permet encore une activation AAL1 avant le durcissement ultérieur.")
req("andg.revoked_atisnull" in m,
    "La migration Junior initiale ne ferme pas immédiatement les liens tuteur révoqués.")
req("createtriggersinjira_revoke_junior_consent_on_guardian_link" in m
    and "setrevoked_at=coalesce(revoked_at,now())" in m,
    "La migration Junior initiale ne révoque pas durablement le consentement avec le lien tuteur.")

guardian_children_start=m.find("createorreplacefunctionpublic.guardian_junior_community_children()")
guardian_children_end=m.find("createorreplacefunctionpublic.junior_community_accept_rules()",guardian_children_start)
guardian_children_initial=m[guardian_children_start:guardian_children_end] if guardian_children_start>=0 and guardian_children_end>guardian_children_start else ""
req(guardian_children_initial and "'junior_alias'" not in guardian_children_initial,
    "La migration Junior initiale expose encore junior_alias au tuteur.")

summary_start=m.find("createorreplacefunctionpublic.junior_guardian_summary(p_child_user_iduuid)")
summary_end=m.find("commentonfunctionpublic.sinjira_junior_community_enabled()",summary_start)
summary_initial=m[summary_start:summary_end] if summary_start>=0 and summary_end>summary_start else ""
req(summary_initial and "mfa_aal2_required" in summary_initial,
    "Le résumé parental Junior initial n'exige pas AAL2.")
req("'last_activity_date'" in summary_initial and "'last_activity_at'" not in summary_initial,
    "Le résumé parental Junior initial n'est pas minimisé à la date UTC.")

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
req("s.rpc('sinjira_my_account_capabilities')" in c,'Le client Junior n utilise pas les capacités self-only centralisées.')
req("capabilities.junior_community_enabled!==true" in c and "capabilities.junior_rules_accepted!==true" in c,'Le client Junior ne borne pas activation/règles via les capacités serveur.')
req("s.rpc('sinjira_my_account_capabilities')" in rc,'Le client des règles Junior n utilise pas les capacités self-only centralisées.')
req("capabilities.junior_community_enabled!==true" in rc and "capabilities.junior_rules_accepted===true" in rc,'Le client des règles ne borne pas activation/acceptation via les capacités serveur.')
req("if(button)button.disabled=true;" in rules_client,'Le bouton des règles Junior n est pas verrouillé avant validation.')
req("if(button)button.disabled=false;" in rules_client,'Le bouton des règles Junior n est pas réactivé après validation.')
req("règlesjuniordéjàacceptées" in rc and "return;" in rules_client,'Le bouton des règles déjà acceptées ne reste pas borné.')
req('sinjira-community-junior-rules-v25.js?v=25.0.3' in rules_page,'Le cache des règles Junior V25.0.3 n est pas forcé.')
req("p_user_id:user.id" not in c and "p_user_id:user.id" not in rc,'Les clients Junior transmettent encore leur UUID aux RPC d état self-only.')
req(".from('junior_community_" not in client.lower(),'Le client Junior contourne les RPC avec un accès table direct.')
req("capabilities.child_11_12!==true" in c,'Le client Junior ne vérifie pas la capacité child_11_12.')
req("location.replace('/compte/communaute.html')" in c,'Le client Junior ne renvoie pas les autres âges vers leur communauté.')
req('setcomposerenabled(false)' in c,'Le formulaire Junior n est pas verrouillé avant validation des capacités.')
req('setcomposerenabled(true)' in c,'Le formulaire Junior n est pas réactivé après validation.')
req('asyncfunctionrefreshfeedafteraction(successmessage,stalemessage)' in c,'Les mutations Junior ne séparent pas succès serveur et rafraîchissement du fil.')
for marker,msg in (
    ('publicationajoutée,maislefilnepeutpasêtrerafraîchi','La création de publication peut encore devenir un faux échec après rafraîchissement.'),
    ('commentaireajouté,maislefilnepeutpasêtrerafraîchi','La création de commentaire peut encore devenir un faux échec après rafraîchissement.'),
    ('signalementenregistréetpersonnemasquée.lefilesttemporairementferméjusqu’àsonprochainrafraîchissement','Le signalement Junior ne ferme pas le fil stale après succès sans rafraîchissement.'),
    ('filtemporairementmasqué','Le fil Junior ne masque pas le contenu stale après signalement confirmé.'),
    ('publicationsupprimée,maislefilnepeutpasêtrerafraîchi','La suppression de publication peut encore devenir un faux échec.'),
    ('commentairesupprimé,maislefilnepeutpasêtrerafraîchi','La suppression de commentaire peut encore devenir un faux échec.'),
):
    req(marker in c,msg)
req('sinjira-community-junior-v25.js?v=25.0.5&rev=child-access-matrix' in page,'Le cache Communauté Junior V25.0.5 n est pas forcé.')
req('<textarea disabled maxlength="500" name="body"' in page,'Le compositeur Junior HTML n est pas fail-closed sans JavaScript.')
req('<button class="btn btn-primary" disabled type="submit">Publier</button>' in page,'Le bouton Publier Junior HTML n est pas désactivé par défaut.')
req('data-junior-rules-accept disabled' in rules_page,'Le bouton des règles Junior HTML n est pas désactivé par défaut.')

# Règles Junior et activation parent.
req('pas de messages privés' in rp and 'pas de rencontre privée' in rp and 'pas d’argent ni de commerce' in rp,'Les règles Junior sont incomplètes.')
req("s.rpc('junior_community_accept_rules')" in rc,'L acceptation des règles Junior ne passe pas par RPC.')
req('data-junior-community-children' in rh,'Relations ne contient pas le panneau d activation Junior.')
req("s.rpc('sinjira_my_account_capabilities')" in r,'Relations ne lit pas la bande via les capacités self-only.')
req("s.rpc('guardian_set_junior_community'" in r,'Relations ne peut pas activer/révoquer la Communauté Junior.')
req("s.rpc('junior_guardian_summary'" in r,'Relations ne peut pas lire le résumé de sécurité sans contenu.')
req("return false;" in relations and "const refreshed=await renderJuniorCommunityChildren();" in relations,'Le panneau tuteur ne distingue pas un échec de rafraîchissement après décision Junior.')
req("Le panneau de contrôle ne peut pas être rafraîchi pour le moment." in relations,'Le parent ne reçoit pas un état explicite après décision Junior réussie mais rafraîchissement impossible.')
req("let ready=false;" in relations and "function setFormReady(value){ready=value;for(const el of form.elements)el.disabled=!value}" in relations,'Le formulaire Relations privées n est pas fail-closed pendant le chargement.')
req("setFormReady(false);" in relations,'Chaque relecture Relations privées ne reverrouille pas le formulaire.')
req("ageBand='unverified';" in relations and "return false;" in relations,'La bande d âge Relations ne repasse pas fail-closed si les capacités deviennent indisponibles.')
req("const ageRefreshed=await refreshAgeBand();" in relations,'Les mutations de supervision ne revérifient pas la bande d âge.')
req("L’état du compte ne peut pas être entièrement rafraîchi pour le moment." in relations,'Les mutations de supervision ne signalent pas un rafraîchissement incomplet.')
req("Le panneau de supervision ne peut pas être rafraîchi pour le moment." in relations,'Les permissions/codes parentaux ne distinguent pas mutation et rafraîchissement.')
req("return false;" in relations and "Relation ajoutée, mais la liste ne peut pas être rafraîchie" in relations and "Relation retirée, mais la liste ne peut pas être rafraîchie" in relations,'Les mutations Relations privées ne distinguent pas succès et rafraîchissement.')
for marker,msg in (
    ('<select disabled name="relationship_type" required>','Le type de relation HTML n est pas désactivé par défaut.'),
    ('<input disabled maxlength="120" name="relative_name" required>','Le nom/pseudo de relation HTML n est pas désactivé par défaut.'),
    ('<textarea disabled maxlength="1000" name="private_note"></textarea>','La note privée HTML n est pas désactivée par défaut.'),
    ('<button class="btn btn-primary" disabled type="submit">Ajouter la relation</button>','Le submit Relations HTML n est pas désactivé par défaut.'),
):
    req(marker in relations_html,msg)
req('v24-relations.js?v=25.0.14&amp;rev=junior-alias-private' in relations_html,'Le cache Relations Junior V25.0.14 n est pas forcé.')

# Navigation fail-closed pour 11–12 : liste blanche explicite, redirections Junior et refus par défaut.
req("constaccountmode=string(capabilities.account_mode||'restricted')" in a and "capabilities.child_11_12===true" in a and "if(!childaccount)return" in a and "constchild_11_12_allowed_routes=newset([" in a,'La navigation du compte ne borne pas explicitement les routes child via les capacités serveur.')
req("['communaute.html','/compte/communaute-junior.html']" in a,'La communauté générale n est pas redirigée vers Junior.')
req("['regles-communaute.html','/compte/regles-communaute-junior.html']" in a,'Les règles générales ne sont pas redirigées vers les règles Junior.')
allowed_section=a[a.find('constchild_11_12_allowed_routes=newset(['):a.find('constchild_11_12_route_redirects=newmap([')]
for route in ('messages.html','rencontres.html','reseau-personnage.html','marche.html','jetons.html','mes-achats.html','contributions.html','playtests.html','emploi.html','mon-ia.html','monde-parallele.html','mes-lectures.html','mes-parties.html'):
    req(f"'{route}'" not in allowed_section,f'Route sensible autorisée par erreur pour child: {route}')
for route in ('bibliotheque.html','documents.html','projet.html'):
    req(f"'{route}'" in allowed_section,f'Route de contenu classé absente de la liste blanche child: {route}')
req("location.pathname.startswith('/compte/')&&!child_11_12_allowed_routes.has(currentleaf)" in a,'Un compte child peut encore ouvrir directement une route compte non autorisée.')
req("next.searchparams.set('from','restricted')" in a and "next.searchparams.set('module',currentleaf)" in a,'Le repli Junior des routes restreintes n est pas traçable dans l URL locale.')
req("if(!child_11_12_allowed_routes.has(leaf))link.hidden=true" in a,'La navigation ne masque pas par défaut les routes non autorisées aux comptes child.')
req("capabilities.child_11_12===true" in co and "communaute-junior.html" in co and "capabilities.general_community!==true" in co,'La Communauté générale n est pas bornée par les capacités serveur.')

# Tests comportementaux.
req('selectplan(60);' in t,'Plan pgTAP Junior inattendu.')
req('leparentpeutrévoquerimmédiatementlacommunautéjunior' in t,'La preuve de révocation parentale immédiate est absente.')
req('wrapperpublicdebandeself-onlyrestesecurityinvokeretsonimplémentationinternesecuritydefiner' in t,'Le pgTAP ne prouve pas la séparation INVOKER public / DEFINER interne du wrapper self-only final.')
req('authenticatedconservelewrapperdebandeself-only' in t,'Le pgTAP ne prouve pas l accès authenticated au wrapper self-only final.')
req('anonconservelewrapperself-onlyrequisparlesrlspubliques' in t,'Le pgTAP ne prouve pas l accès anon self-only requis par les RLS publiques.')
req('junior_guardian_consent_required' in t and 'aprèsrévocationlefiljuniorestimmédiatementrefusécôtéserveur' in t,'Le fil Junior n est pas prouvé fermé après révocation.')
req('leparentpeutréactiverlacommunautéjunior' in t,'La réactivation parentale n est pas couverte.')
req('unepublicationmasquéeparmodérationnepeutplusrecevoirdecommentairejunior' in t,
    'Le pgTAP ne prouve pas qu un post Junior masqué refuse immédiatement les nouveaux commentaires.')
req('leparentretirelaccèsjuniordelauteurducommentaire' in t
    and 'lecommentairedisparaîtdufildèsquesonauteurperdlaccèsjunior' in t
    and 'lapublicationdisparaîtdufildèsquesonauteurperdlaccèsjunior' in t
    and 'leparentréactiveexplicitementlaccèsjuniordelauteurducommentaire' in t
    and 'lecommentaireredevientvisibleaprèsréactivationexplicitedumêmeenfant' in t
    and 'lapublicationredevientvisibleaprèsréactivationexplicitedumêmeenfant' in t,
    'Le pgTAP ne prouve pas que la visibilité des publications et commentaires suit immédiatement le consentement Junior de leur auteur.')
for marker,msg in (
    ('aucunselectdirectsurpublicationsjunior','Le test ne prouve pas l absence de SELECT direct.'),
    ('leparentactiveexplicitementlacommunautéjunior','Le test ne prouve pas l opt-in parent.'),
    ('aucunrpcpublicnepermetdesonderlactivationjuniorparuuid','Le test ne prouve pas la frontière self-only de l activation Junior.'),
    ('aucunrpcpublicnepermetdesonderlesrèglesjuniorparuuid','Le test ne prouve pas la frontière self-only des règles Junior.'),
    ('aucunrpcpublicnepermetdesonderlabandejuniorparuuid','Le test ne prouve pas la frontière self-only de la bande Junior.'),
    ('levraipseudo/profildupremierenfantnestpasexposé','Le test ne prouve pas la pseudonymisation.'),
    ('luuidauteurnestpasexposé','Le test ne prouve pas la minimisation UUID.'),
    ('unlienexterneestrefusécôtéserveur','Le test ne prouve pas le blocage de liens.'),
    ('unadultenepeutpaslirelefiljunior','Le test ne prouve pas l isolation adulte.'),
    ('unedécisionhumainehide_contentmasquelapublicationjunior','Le test ne prouve pas le masquage humain réversible.'),
    ('unedécisionrenverséerendlapublicationjuniorvisibleànouveau','Le test ne prouve pas la restauration après appel/révision.'),
    ('lamessagerieetlesréseauxsociauxhistoriquesrestentfermés','Le test ne prouve pas l absence de messagerie.'),
    ('lerésuméparentnedonnepasaccèsaucontenu','Le test ne prouve pas la supervision sans surveillance.'),
    ('à13anslecomptequitteautomatiquementlabandejunior','Le test ne prouve pas la sortie Junior à 13 ans.'),
):
    req(marker in t,msg)

# Modération humaine : les signalements Junior doivent être résolus sur les tables Junior
# et les décisions hide_content doivent rester réversibles via moderation_content_visible.
req("public.moderation_content_visible('real','post',p.id)" in m and "public.moderation_content_visible('real','comment',c.id)" in m,'Le fil Junior ne respecte pas les décisions de modération réversibles.')
req("snap.source==='junior_community'" in ae,'La fonction admin ne reconnaît pas les signalements Junior.')
req("canonicaluser(s,'junior_community_posts','id','author_user_id'" in ae,'La modération ne résout pas l auteur d une publication Junior.')
req("canonicaluser(s,'junior_community_comments','id','author_user_id'" in ae,'La modération ne résout pas l auteur d un commentaire Junior.')
req("r.snapshot?.source==='junior_community'" in ae and "junior_community_posts" in ae and "junior_community_comments" in ae,'La preuve de modération Junior ne charge pas le contenu cible borné.')
req("isjunior=x.snapshot?.source==='junior_community'" in ac and "communautéjunior" in ac,'L interface admin n identifie pas clairement la Communauté Junior.')

# Preuve navigateur isolée : aucun appel production, identité pseudonymisée et RPC seulement.
req(('page.route(' in browser_test or 'context.route(' in browser_test) and '@supabase/supabase-js@2/+esm' in browser_test,'La preuve navigateur Junior n intercepte pas le client Supabase.')
req('private-child@example.test' in browser_test and 'child-test-11' in browser_test,'La preuve navigateur ne contient pas les sentinelles de données privées.')
req('private-child@example.test" not in text' in browser_test and 'child-test-11" not in text' in browser_test,'La preuve navigateur ne vérifie pas l absence de données privées dans le DOM.')
req('getauthenticatorassurancelevel' in bt,'La preuve navigateur Junior ne simule pas le niveau MFA attendu par requireUser().')
req('not production_requests' in bt,'La preuve navigateur ne bloque pas les appels vers Supabase production.')
req('junior_community_create_post' in browser_test and 'junior_community_create_comment' in browser_test,'La preuve navigateur ne couvre pas publication + commentaire.')
req('sinjira_junior_external_contact_forbidden' in bt,'La preuve navigateur ne couvre pas le blocage des liens externes.')
req('compte/bibliotheque.html' in browser_test and 'aucun contenu n’a encore été approuvé pour les comptes de 11–12 ans' in bt,'La preuve navigateur ne couvre pas la Bibliothèque Junior filtrée.')
req('sinjira_reader_library' in browser_test and 'user_entitlements' in browser_test and 'forbidden' in bt,'La preuve navigateur ne vérifie pas l absence de requêtes vers lectures/licences non certifiées.')
req('compte/playtests.html' in browser_test and 'from=restricted&module=playtests.html' in browser_test,'La preuve navigateur ne couvre pas une URL directe vers un module enfant non certifié.')
req('data-junior-access-note' in browser_test,'La preuve navigateur ne vérifie pas le message de repli Junior.')
req('await new promise(resolve=>settimeout(resolve,500))' in bt,'La preuve navigateur ne ralentit pas les capacités pour tester la course de chargement.')
req('composer.is_disabled()' in bt,'La preuve navigateur ne vérifie pas le verrou avant capacités.')
req('composer.is_enabled()' in bt,'La preuve navigateur ne vérifie pas la réactivation après capacités.')

# CI locale uniquement, lecture seule et sans capacité de production.
if workflow:
    req('permissions:\n  contents: read' in workflow,'Le workflow Junior doit rester contents:read.')
    req('persist-credentials: false' in workflow,'Le checkout Junior doit désactiver les credentials persistés.')
    req('secrets.' not in w,'Le workflow Junior ne doit référencer aucun secret.')
    req('pull_request_target' not in w,'pull_request_target interdit.')
    for forbidden in ('supabase db push','supabase link','supabase functions deploy','supabase secrets set'):
        req(forbidden not in w,f'Commande production interdite dans le workflow Junior: {forbidden}')
    req('supabase db reset' in w and 'supabase test db supabase/tests/child_community_v25.test.sql' in w,'Le workflow Junior ne rejoue pas la base et le pgTAP local.')
    req('supabase/migrations/20260924173000_sinjira_v25_junior_comment_author_visibility.sql' in workflow,
        'Le workflow Junior ne surveille pas le correctif de visibilité des commentaires après révocation.')
    req('supabase/migrations/20260924191000_sinjira_v25_junior_hidden_post_comment_guard.sql' in workflow,
        'Le workflow Junior ne surveille pas le refus de commentaire sur publication masquée.')
    req('python tests/e2e/test_child_community.py' in w,'Le workflow Junior ne lance pas la preuve navigateur isolée.')
    req('mcr.microsoft.com/playwright/python:v1.61.0-noble@sha256:' in w,'L image Playwright Junior n est pas épinglée par digest.')
    req("      - name: Démarrer le site statique local\n        shell: bash\n        run: |\n          set -euo pipefail" in workflow,'Le serveur navigateur Junior doit utiliser bash lorsque pipefail est activé.')

if errors:
    print(f'ECHEC Communauté Junior V25: {len(errors)} problème(s).')
    for error in errors:
        print('- '+error)
    raise SystemExit(1)

print('OK V25: Communauté Junior 11–12 isolée, parent-opt-in, pseudonymisée, sans DM/coordonnées/commerce et testée localement.')
