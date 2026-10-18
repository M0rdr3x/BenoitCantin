# SINJIRA — intégration des catalogues et de la sécurité Pages

13 octobre 2026 — Préparation non publiée.

- Main de départ : 790b1424b20e98ef31ec6597e98c5c8f6b4aa23d
- Sécurité Pages PR #458 : 7cdd33e05615ddf68b05b190dd0b079778de67f0
- Catalogues officiels PR #637 : 81971a0c66ac419bc7c533ec0ab29c6f52c2b919

Les 12 fichiers de la PR #637 sont repris depuis leurs blobs Git exacts dans
l'arbre de la PR #458, sans régénérer les trois visuels binaires et sans
modifier les romans ni les droits privés.

## Contrat de publication

Le manifeste approuve 614 fichiers historiques et 4 ressources supplémentaires :
`projets/sinjira/logiciels/index.html` et les trois bannières de Romans,
Jeux et Logiciels. Total : **618 sources**, **31 fichiers Jekyll générés**,
soit **649 fichiers statiques**. Lors d'une publication contrôlée, le seul
reçu dynamique SHA/run porte le total à **650**.

Le garde de sécurité impose désormais la présence des quatre ressources.
Les audits de navigation couvrent les trois portails et leurs images,
et les tests CDN comparent **22 ressources critiques** aux blobs Git du
SHA de publication. Cette preuve couvre désormais aussi l'accueil SINJIRA,
les pages Romans et Jeux, la feuille de style, la bibliothèque et le
sitemap. Des autotests refusent explicitement les anciennes versions
de chacune de ces pages et ressources.

## Conditions bloquantes

CI du SHA combiné réussie ; réglage Pages = GitHub Actions confirmé par
l'administrateur ; absence de publication racine concurrente ; DRY_RUN
sans upload ; approbation humaine du PUBLISH sur le main exact ; contrôle
HTTPS, 404/410 privés, reçu SHA/run et intégrité des ressources.
Cette branche ne déclenche aucune publication.

## Surveillance quotidienne compatible avec la bascule

Le workflow `publication-boundary-watch.yml` est maintenu en lecture
seule. Son exigence historique `Netlify` devient une alternative
fermée : Netlify avec sa signature d'origine **ou** GitHub Pages avec
le reçu `.well-known/sinjira-pages-release.json` au SHA exact de
`main` exécutant la surveillance. Un simple en-tête `Server:
GitHub.com` ne suffit jamais à faire passer le contrôle.

Les 13 routes privées de l'audit Pages et l'ancien chemin de build
Netlify (14 chemins techniques uniques au total) doivent répondre
en HTTP 404/410, sans redirection trompeuse. Les autotests refusent
les statuts 200, 301, 302, 403, 500, la disparition de preuve,
l'en-tête de fournisseur ambigu, le reçu obsolète, falsifié ou hors MIME.
Le contenu des routes techniques n'est jamais lu par le surveillant.

La surveillance GitHub Pages n'est réputée conforme qu'après la
bascule administrative, la fusion autorisée et un PUBLISH réussi.
Tant que le site sert la racine technique, le monitoring doit
continuer à signaler le risque et ne doit pas être neutralisé.


## Budget global de preuve après PUBLISH

Le contrôle de propagation HTTPS a été borné pour la nouvelle liste de
22 ressources critiques. Il ne peut pas multiplier indéfiniment quatre
tentatives par fichier : les vérifications CDN partagent un budget de
**420 secondes**. Une réponse tardive après la limite est refusée,
tout comme un fichier non vérifié en fin de budget. L'étape GitHub
Actions possède une enveloppe de **20 minutes** couvrant également
l'attente du reçu SHA/run et la vérification des routes publiques et
techniques. Des autotests simulent la limite dépassée.


## Navigation de catalogue — destinations réellement publiables

Les quatre portails publics SINJIRA (accueil, Romans, Jeux, Logiciels) font
désormais l'objet d'un test de **graphe de liens et médias** indépendant.
Chaque destination locale de lien, CSS, JavaScript, image, `srcset`,
`poster` et image sociale doit être présente dans le manifeste public Pages,
ou dans les fichiers explicitement générés par Jekyll. La présence dans
GitHub seul ne suffit pas : les sources `scripts/`, `supabase/` et les
fichiers non approuvés doivent rester inaccessibles depuis ces portails.

Autotests négatifs : lien technique existant mais exclu, route absente,
traversée hors racine, protocole JavaScript, lien interne HTTP,
chemin ambigu, `srcset` invalide et détournement de base HTML.
Ce test s'exécute aussi lorsque l'inventaire Pages est modifié.
Il ne remplace pas la preuve HTTP du site publié.


## Réparation de l'icône Boussole électorale (13 octobre 2026)

La capture du portail montrait une image cassée dans la quatrième carte.
La correction distingue désormais deux usages : l'alias public
`assets/media/nova-boussole-electorale.webp` est un pictogramme
**160 × 160, léger et décodable** pour l'accueil, tandis que
`assets/media/nova-boussole-electorale-v2.webp` conserve son
illustration originale **360 × 360** pour l'accueil de Projet Nova
et le héros de la Boussole électorale. Cette séparation évite
une régression de qualité sur la page de l'outil civique.

Les trois références de l'accueil (image orbitale, carte et aperçu
central) utilisent l'alias avec une nouvelle version d'URL pour
supprimer le cache problématique. L'orbite charge son image
prioritairement. Les tests `scripts/validate_boussole_home_visual.py`
vérifient les octets du nouvel alias, RIFF/VP8, SHA-256,
dimensions et intégrité du build Jekyll. Les tests navigateur
Chromium/Firefox/WebKit vérifient le décodage effectif de l'alias
et celui de l'image originale 360 × 360 sur Projet Nova.

Le contrôle HTTP post-PUBLISH vérifie MIME/présence de l'alias ;
l'intégrité CDN compare ses octets au commit exact Git approuvé.
Le total est porté à 22 ressources critiques. L'issue #450 reste
bloquante pour la publication de l'ensemble de la PR #639.


## Preuve CDN de l'ensemble du parcours Boussole

L'attestation CDN couvre désormais **22 ressources**, dont la racine
`index.html`, la page Boussole de Projet Nova, le WebP compact
de l'accueil et le WebP original v2 du héros Nova. Tests négatifs
sur contenu ancien pour chacun de ces fichiers. Les changements
préservent l'intervalle monotone global de 420 secondes et
n'impliquent aucune publication réelle.


## Mesure pré-bascule sans lecture de documents techniques

Le diagnostic PR inclut maintenant `report_pages_live_exposure.py`.
Il collecte seulement les **codes HEAD** sur 14 chemins techniques
fixés, classe `EXPOSÉ / NON_CONFORME / INCONNU / REFUS_HEAD_OBSERVÉ`
et conserve le verdict dans le résumé Actions. Aucune récupération
du corps des fichiers ni changement de Pages. La mesure HEAD n'est
pas une certification GET; le reçu SHA/run et les vérifications
post-PUBLISH restent indispensables.


## Accessibilité des quatre portails — navigation courante explicite

Le menu principal des catégories Romans, Jeux et Logiciels indique désormais
SINJIRA™ comme **section parente** (`aria-current="location"`), et non comme
page active. Le sous-menu identifie quant à lui **une seule page réellement
courante** (`aria-current="page"`). Sur l'accueil SINJIRA, le menu principal
peut correctement signaler la page elle-même. Le validateur catalogue
contrôle indépendamment ces deux rôles et refuse une sélection ambiguë.
Cela améliore le retour des lecteurs d'écran et la cohérence des chemins
de navigation, sans modifier le contenu ou les droits des membres.


## Complétude des aperçus sociaux et SEO des catalogues

Les pages Romans, Jeux et Logiciels publient désormais chacune une URL canonique,
les liens hreflang fr-CA et x-default, le même titre sous HTML/Open Graph/Twitter,
une image sociale officielle avec texte alternatif, une description et un
JSON-LD `CollectionPage` cohérent avec la route affichée.

Le validateur `scripts/validate_sinjira_catalogues_metadata.py` rejette les
métadonnées manquantes/dupliquées, les bannières substituées, les URL erronées
et les schémas JSON-LD non alignés. Il s'exécute sur les PR DRAFT, dans la
compilation Jekyll sans publication et avant un éventuel upload Pages contrôlé.
Aucun changement de vente, de disponibilité logicielle, de droit privé ou de
contenu des romans n'est associé à ce correctif.


## Preuve des métadonnées réellement livrées dans l'artefact Jekyll

L'audit `validate_sinjira_catalogues_metadata.py --built _site` ne se
contente plus de lire les trois fichiers HTML du dépôt. Il compare
**octet pour octet** le HTML de Romans, Jeux et Logiciels dans `_site`
aux originaux, réanalyse leurs métadonnées SEO/partage, et vérifie les
**trois WebP officiels** présents dans `_site` contre leurs empreintes
SHA-256 approuvées et les fichiers sources.

Les autotests négatifs simulent une page manquante, des métadonnées
modifiées après compilation, une affiche absente ou modifiée et un
répertoire de sortie invalide. Cette vérification intervient dans la
CI Jekyll sans publication **et comme audit exécutable obligatoire
avant tout upload Pages**; le garde du workflow rejette un contrôle
remplacé par une commande factice ou privé de `--built _site`.
Cette preuve de prépublication ne remplace pas le contrôle HTTP/CDN
sur le domaine réel après un PUBLISH explicitement approuvé.


## Bibliothèque : vérité des achats et droits réellement vérifiés

La bibliothèque ne prétend plus « aucun achat » avant le chargement du
compte. Les quatre indicateurs commencent à « — » et le statut précise
que les droits sont en cours de vérification. Le rôle propriétaire et les
licences ne sont annoncés qu'en présence de réponses valides de l'API;
une erreur ne devient jamais un faux « aucun droit ». En cas d'échec,
les sections privées affichent leur indisponibilité sans inventer de
licences ni exposer de PDF intégral. Le propriétaire reste distinct
des licences explicites, et les signatures de documents restent émises
par les fonctions serveur privées selon leurs contrôles d'autorisation.

Le contrat `scripts/validate_sinjira_library_status.py` valide
ces libellés et le comportement prudent prévu en cas d'erreur, sans
jeton ni accès aux comptes. La CI des catalogues et l'audit Jekyll
exécutent ses autotests négatifs avant publication.


## Historique des paiements vs droits réellement attribués

La page `compte/mes-achats.html` ne déduit plus qu'un compte n'a
**aucun achat payant** simplement parce que la boutique en ligne est
encore désactivée. Elle distingue explicitement l'absence d'un
historique transactionnel interrogé sur cette page des droits
numériques réellement attribués, et propose un lien vers la
bibliothèque du compte. La page Licences ne qualifie plus
tous les comptes de « mode gratuit » lorsqu'un code physique
ou une licence accordée pourrait exister.

Les cas négatifs du contrat `validate_sinjira_library_status.py`
couvrent ces deux pages et le workflow catalogue se redéclenche
lorsqu'elles sont modifiées. Aucune logique de paiement
n'est activée et aucune vente n'est déduite ou simulée.


## Bibliothèque : séparation des projets visibles et des accès autorisés

Le contrat utilisateur distingue les aperçus des projets restreints et
les espaces ouvrables depuis la bibliothèque. Un compte sans droit
explicite ne voit plus les boutons « Ouvrir l'espace » et « Jouer » sur
un projet `restricted`, même si la fiche du projet est présente à titre
informatif. Les accès périmés ou mal datés sont traités comme absents;
les espaces publics ou inclus avec un compte restent accessibles, de
même que les espaces du propriétaire ou administrateur confirmés par
RPC. Les URL de lancement de jeux issues du catalogue doivent être
des chemins internes. Le compteur « Espaces accessibles » mesure
uniquement les cartes effectivement ouvrables et cesse d'annoncer
un nombre si la vérification des rôles ou des accès a échoué.

Les compteurs retirent leur étiquette accessible « en cours » une fois
la réponse validée, et distinguent un service momentanément
indisponible d'une vraie valeur numérique. Un test Node isolé,
sans compte réel ni service distant, exerce les états membre,
propriétaire, droits expirés, liens malveillants et accessibilité du
compteur. Il fait partie des validations PR et du workflow Pages
contrôlé. Ces restrictions de boutons sont une **présentation
prudente**, pas une autorisation côté client : les règles RLS et les
fonctions privées conservent la décision finale.


## Convergence du détail des projets avec les droits des membres

Le module de la page historique `/compte/projet.html`, distinct de
la nouvelle bibliothèque, est aligné sur les rôles réellement
confirmés par RPC et les accès `player`/`tester` non expirés.
La comparaison d'adresse courriel dans le navigateur a été retirée
pour les rôles privilégiés de cette page. Un compte sans droit ne
reçoit plus de bouton « Jouer » ni de liste de documents ou playtests
privés sur un projet restreint. Les erreurs d'API sont annoncées
comme indisponibilités, et non comme absence réelle de documents.
Les URL de lancement doivent être internes. Le schéma SQL n'autorise
que les niveaux `player` et `tester`; les deux interfaces refusent
désormais toute autre chaîne.

Il s'agit d'une mesure de présentation conservatrice; le contrôle
RLS et la signature du document restent la frontière de sécurité
réelle, à tester distinctement lors de la recette authentifiée.


## Autorisations de signature des documents — contrat RPC propriétaire

L'Edge Function privée `get-document-url` vérifie désormais explicitement
`is_sinjira_owner` **et** `is_sinjira_admin` auprès de Supabase
pour le membre authentifié. Le propriétaire confirmé reçoit le rang
privilégié comme l'administrateur confirmé, sans devoir posséder une
licence d'achat ou une attribution `project_access` fictive. Les autres
membres restent soumis au calcul serveur `project_access_rank` et
aux documents réellement approuvés; une erreur RPC de rang refuse
la signature (503), jamais un droit implicite.

Huit tests Node locaux exécutent **la fonction Edge elle-même** avec
une base simulée sans accès réseau : propriétaire, administrateur,
membre autorisé, membre refusé, RPC en échec, rôle propriétaire non
confirmé, fichier non approuvé et requête anonyme. Ils attestent
qu'aucun lien signé n'est créé pour un scénario refusé. Ces cas sont
appelés depuis la CI PR et le dernier garde pré-upload Pages; ils
ne remplacent pas une recette Supabase/RLS en environnement sécurisé.


## Lecture HTTP bornée de la fonction de documents

La fonction `get-document-url` limite maintenant le JSON à 512 octets
**au cours du flux**, sans attendre une lecture entière avec `req.text()`.
Lors d'un dépassement, elle annule le lecteur; le type MIME JSON est
comparé strictement et l'UTF-8 invalide est refusé.

Le validateur statique rejette le retour aux lectures non bornées et
teste les mutations négatives. Quatre essais supplémentaires exécutent
la fonction Edge simulée avec dépassement de taille sans longueur
déclarée, longueur explicitement excessive, JSON ou UTF-8 invalide et
MIME incorrect. Aucun accès réseau ou secret n'est nécessaire.


## Contrôle serveur du téléchargement intégral des romans — 14 octobre 2026

Le téléchargement `get-novel-file-url` utilise maintenant une validation
stricte du type de requête `application/json`, du plafond de corps HTTP à
2 048 octets et de l'UTF-8. Le slug doit être une chaîne valide, sans
chemin ni coercition implicite d'objet.

Le rôle créateur et le rôle administrateur sont chacun confirmés
par réponse RPC `true` sans erreur. Si aucun rôle privilégié n'est
confirmé, le serveur vérifie l'attribution `user_entitlements` et
l'état actif du produit : une erreur de l'API de droits renvoie HTTP
503 et jamais un faux « pas d'achat » (403). Une licence explicitement
vérifiée reste valable même si la vérification du rôle privilégié
est temporairement indisponible. Les exceptions inattendues sont
journalisées sous un code fixe sans reproduire de détails privés.

`tests/test_novel_file_authorization.cjs` exerce la véritable fonction
Edge sans clés ni base réelle : propriétaire, administrateur, achat,
refus, panne RPC/licence, statut inédit, fichier non prêt, anonyme,
requête excessive, MIME et encodage malformés. La CI SINJIRA,
la compilation Jekyll isolée et le garde final pré-upload Pages
refusent les régressions. Cette fonction corrigée reste dans la
PR non fusionnée, sans déploiement Supabase.


## Livre I — seconde porte privée harmonisée avec les droits du créateur

La fonction `get-private-book-url` utilisait seulement la licence
`user_entitlements` et le produit actif, même pour un propriétaire
confirmé. La fonction `get-novel-file-url` possédait déjà une voie
distincte pour le créateur. La correction unifie les deux politiques :
les RPC serveur `is_sinjira_owner` et `is_sinjira_admin` doivent
confirmer explicitement `true` pour ignorer le contrôle d'achat.
Les membres ordinaires doivent toujours disposer d'un produit actif
et d'une attribution propre à leur UID. Une erreur de vérification
donne un état indisponible (HTTP 503), jamais un achat imaginaire.

Le stockage privé continue d'être activé uniquement par le drapeau
d'environnement côté Supabase, avec bucket et chemin serveur,
signature limitée à 300 secondes et `verify_jwt=true`. Des tests
Node isolés exécutent la véritable Edge Function avec faux RPC,
fausses licences et faux stockage; le validateur de contrat comporte
des mutations négatives (rôle truthy, RPC supprimée, bypass, filtre
produit manquant). Les contrôles sont exécutés en CI, Jekyll et
avant tout upload Pages. Aucune fonction Supabase ni Pages n'est
déployée par ces changements en PR.


## Pré-bascule Pages : double diagnostic HTTP HEAD / GET sans corps

Le diagnostic de la PR distinguait jusqu'ici la réponse HTTP HEAD de
celle d'une requête GET. Le nouveau
`scripts/report_pages_live_get_status.py` vérifie les **statuts GET**
des mêmes 14 chemins techniques fixes sur le domaine officiel.
Le programme ne lit, n'imprime ni n'enregistre le corps de la réponse;
les redirections, erreurs et cas inconnus sont explicitement classés.
Un test local de réponse fictive échoue si une lecture du corps est
tentée. La CI prévol exécute ses autotests négatifs et publie un
rapport lisible dans GitHub Actions, sans fichier téléchargé dans
les artefacts et sans déploiement.

Une réponse GET 200/206 confirme que l'URL est accessible, mais ne
prouve pas quels octets ou secrets sont servis. Les résultats GET
404/410 ne certifient pas à eux seuls la provenance du site, le SHA
déployé ni l'intégrité CDN. Le verrou de publication Pages Actions
et les contrôles post-déploiement demeurent inchangés.

**Preuve réelle du 15 octobre 2026 UTC :** [prévol GitHub #38664343729](https://github.com/M0rdr3x/BenoitCantin/actions/runs/38664343729) a terminé les tests du nouveau diagnostic et a relevé **9 réponses GET 200 et 5 GET 404**, identiques aux statuts HEAD. Source Pages toujours `legacy`. Aucun corps technique n'a été lu par le script; aucun secret n'a été vérifié. [Issue #450](https://github.com/M0rdr3x/BenoitCantin/issues/450) demeure ouverte et bloque toute publication.


## Garde de promotion sur les PR hors brouillon

Un rapport GitHub Actions peut être « réussi » tout en affichant
`build_type=legacy`, car il atteste seulement la fin du diagnostic.
Pour éliminer cette ambiguïté au moment de la revue, le workflow
`pages-cutover-preflight.yml` ajoute une **porte bloquante** quand une
PR est déclarée prête : Source GitHub Actions, domaine CNAME et HTTPS
sont exigés via l'API GitHub. Un retour incomplet ou une erreur de
permissions bloque également la porte. Les PR en brouillon continuent
d'obtenir un rapport sans risque de déploiement.

Cette porte vérifie la configuration **seulement**; elle ne remplace
pas la vérification du dernier SHA, les GET 404/410, le reçu SHA/run
ni la comparaison des hachages CDN. Pour devenir une garantie contre
une fusion non autorisée, le job doit être marqué **required** dans
les règles de protection `main` par le propriétaire du dépôt.

## Documents publics — contrôle renforcé des URL de destination

Le parcours `get-document-url` préserve l'accès aux documents approuvés
`public` des projets `public` actifs, même quand le visiteur est connecté.
Les documents `account`, `player`, `tester` ou `admin` conservent
la décision d'autorisation côté serveur et le refus avant tout lien signé.

La validation des `external_url` empêche désormais qu'un chemin apparemment
local contenant une barre oblique inversée soit interprété comme un autre
hôte par le navigateur. Elle refuse également les séparateurs encodés,
les caractères de contrôle, les identifiants intégrés dans l'URL et les
schémas HTTPS malformés. Les destinations HTTPS externes explicites et les
chemins locaux réellement rattachés à `www.benoitcantin.com` restent
acceptés. Les tests Node exécutent la véritable fonction Edge avec des
simulations isolées, et le contrat statique rejette quatre mutations
réintroduisant cette ambiguïté.

Il s'agit de protections de code dans la **PR non déployée**, sans accès à
Supabase réel ni changement des droits RLS en production. Les décisions
de publication Pages et d'activation des fonctions privées restent
indépendantes et soumises aux procédures approuvées.

## Validation stricte des niveaux d'accès documentaires (17 octobre 2026)

La fonction publique `get-document-url` autorise uniquement les cinq
niveaux explicites du registre : `public`, `account`, `player`,
`tester`, `admin`. L'ancienne consultation
`ranks[doc.access_level]||999` n'était pas une liste blanche :
avec un objet JavaScript ordinaire, des valeurs telles que
`constructor`, `toString` ou `__proto__` récupéraient une propriété
héritée non numérique. La comparaison au rang du membre pouvait alors
évaluer `NaN` et laisser passer une signature de lien non autorisée.

La décision repose maintenant sur un niveau textuel **et**
`Object.hasOwn(ranks,doc.access_level)`. Toute valeur hors inventaire est immédiatement refusée par une
réponse HTTP **403**, avant toute requête de rôle, tout calcul de rang
et toute génération de lien. Cette garantie ne repose plus sur la
sentinelle `999`, qui était susceptible d'être dépassée par un rang
serveur erroné ou exceptionnellement élevé. Des tests Node vérifient les valeurs
malformées, les propriétés héritées, les seuils de chaque niveau
autorisé et le refus des liens. Les contrats Python Edge et Livre I
incluent des mutations négatives interdisant la suppression de la liste
blanche.

Cette protection concerne le code de la PR #639 **non fusionnée** :
elle ne constitue ni un déploiement Supabase, ni une attestation des
permissions RLS réelles. Aucun roman ou fichier commercial n'est modifié.

## Liens des catalogues : autorité canonique et inventaire public

Les quatre pages d'entrée SINJIRA (accueil de l'univers, Romans, Jeux,
Logiciels) sont contrôlées par `scripts/validate_sinjira_public_links.py`
contre l'inventaire des fichiers autorisés dans l'artefact Pages isolé.
Une ancienne comparaison de `netloc` pouvait traiter des variantes du
domaine officiel (`www.benoitcantin.com.`, `:443`, présence de
`userinfo@`) comme des sites externes et **omettre** la vérification
d'un chemin technique ou non publié.

Le validateur refuse à présent les autorités locales non canoniques,
les identifiants intégrés, les ports sur les liens du domaine officiel,
les séparateurs inverses, les contrôles ASCII et les autorités encodées.
Les liens officiels HTTPS explicites sont vérifiés contre l'inventaire;
les liens externes classiques, notamment les réseaux sociaux, restent
possibles. Les autotests couvrent les variantes d'hôte et les destinations
techniques exclues, sans requêtes réseau et sans lire de fichiers privés.

Cette modification renforce **le code de contrôle de la PR**, mais
n'assainit pas le domaine en production tant que la publication de la
racine GitHub Pages reste active (incident #450).

## Ancres de navigation et destinations réelles des catalogues

Le validateur `scripts/validate_sinjira_public_links.py` contrôle
désormais aussi les **fragments HTML locaux** des quatre portails
SINJIRA. Les liens d'évitement `#contenu`, les raccourcis `#outils`
et `#avenir` de Logiciels et les liens vers
`/compte/bibliotheque.html#livre-i` ou
`/compte/mes-achats.html#precommandes` doivent désigner une
**ancre réellement présente et unique** dans le document public cible.

L'analyse ne suit les fragments qu'après acceptation de l'URL par
l'inventaire public Pages; elle ne lit que du HTML statique public
sans session ni réseau. Les fragments des PDF promotionnels, comme
`#page=1`, restent gérés par le lecteur PDF et ne sont pas
faussement rejetés comme identifiants HTML. Les liens tiers ne sont
pas interrogés. Des tests négatifs vérifient les ancres absentes,
dupliquées, mal formées et une mutation réelle de `href="#outils"`
dans la page Logiciels, en passant par la fonction d'audit complète.

Cette garantie est testée dans la PR non publiée : elle ne remplace
ni les tests multi-navigateurs, ni la preuve HTTP après bascule du
site. Le blocage GitHub Pages `legacy` (#450) demeure.

## Ouverture fiable des documents et du Livre I après vérification des droits

Les boutons `Ouvrir le document` du compte historique et
`Ouvrir l'édition intégrale` de la bibliothèque v24.4.61 attendaient
jusqu'ici la réponse asynchrone des fonctions Supabase avant d'appeler
`window.open`. Les navigateurs pouvaient alors considérer la nouvelle
fenêtre comme une fenêtre publicitaire et la bloquer **malgré le clic de
l'utilisateur et le droit serveur valide**.

La bibliothèque prépare maintenant un onglet `about:blank` dès le
geste de clic, avec `opener=null`, un état neutre de vérification et
les boutons temporairement désactivés contre les doubles demandes.
Ce n'est qu'après l'autorisation renvoyée par `get-document-url` ou
`get-novel-file-url` que le client vérifie l'URL reçue (HTTPS, chemin
local exact ou destination HTTPS distante, sans protocole exécutable,
identifiants ou séparateurs ambigus) et navigue vers le lien éphémère.
Un refus d'accès, une erreur réseau ou une URL malformée **ferme
l'onglet vide**. Si la fenêtre est bloquée, le lien vérifié peut être
ouvert **dans l'onglet courant** plutôt que devenir inaccessible.

Cette adaptation est un correctif de **parcours utilisateur**, pas une
autorisation de document : chaque fonction Edge et les contrôles de
stockage privés continuent à décider séparément des droits. Les tests
Node simulent réellement l'ordre geste → ouverture → RPC, les
documents publics/privés, les refus, les fenêtres bloquées, le lien
malveillant et les erreurs réseau, sans accès à un compte réel.

La PR #639 reste en brouillon et aucune fonction Supabase ou page
n'est déployée. La publication GitHub Pages legacy est toujours
bloquée par #450.

## Navigation sûre des romans suivis et des projets depuis le compte

Dans la bibliothèque v24.4.61, les boutons **Continuer la lecture /
Lire la démo** et **Page du roman** utilisent des chemins provenant
du registre de romans (`sinjira_novels.demo_path` et `public_path`).
De même, les boutons **Jouer** et **Page publique** utilisent les chemins
de projets du registre Supabase. L'échappement HTML protégeait les
attributs de certains caractères, mais ne validait pas la destination
de navigation (`href="javascript:..."`, URL externe, variante
`//...`, séparateurs encodés, segments `.. `, etc.).

Un validateur commun `safeLibraryRoute` dans
`assets/js/sinjira-supabase.js` n'autorise maintenant que des chemins
absolus **locaux**, conformes à l'origine réelle du site, sans caractères
de contrôle, antislash, segments de traversée, caractères de contrôle
encodés, ambiguïté d'encodage ni préfixe `//`. Les deux bibliothèques
l'emploient pour les routes « Jouer » et « Page publique »; les chemins
de roman l'utilisent **avant** de former leurs liens. Une URL de démo
non sûre est omise; une URL publique du roman non sûre est remplacée par
`/projets/sinjira/romans/`, sans exposer de lien tiers. Les URL des
fichiers privés sont toujours délivrées par les fonctions Edge après
autorisation, indépendamment de ce validateur de navigation.

Les tests Node chargent la vraie fonction `safeLibraryRoute` et
vérifient le **HTML réellement produit** par `renderReads` :
destinations locales valides, refus des protocoles exécutables, hôtes
externes, URL à double slash, traversée `%2e`, encodage de séparateurs
et chemins malformés. Le contrat Python de bibliothèque impose aussi
l'appel au validateur par les deux interfaces. Aucune base de données,
droit d'utilisateur ou fichier de roman n'est modifié.

### Refus des chemins internes techniques dans les liens de bibliothèque

La même origine HTTPS **ne suffit pas** à rendre une destination
publique : la source Pages actuellement en mode `legacy` expose encore
des routes de développement, même sous `www.benoitcantin.com`. Les
champs de destination provenant du registre Supabase ne doivent
jamais orienter un lecteur vers un tel chemin.

Le validateur commun `safeLibraryRoute` bloque donc aussi les
espaces techniques racine `/.github/`, `/.git/`, `/supabase/`,
`/scripts/`, `/tests/`, `/docs/`, `/mobile-native/`,
`/node_modules/` et `/_site/`, les sous-arborescences
`/codex/` et les noms / extensions de source technique
(`netlify.toml`, `README.md`, `.py`, `.tsx`, `.sql`, etc.).
Les routes publiques utiles comme `/projets/sinjira/romans/`,
`/projets/sinjira/jeux/`, `/compte/projet.html`, la boussole
électorale et le PDF **démo public** continuent d'être autorisées.

Les tests Node couvrent explicitement les **14 chemins interdits du
prévol Pages**, des variantes sensibles et le rendu des boutons
« Lire », « Page du roman » et « Jouer ». Le contrat Python empêche
la suppression de ces contrôles. Cette mesure de défense en
profondeur **ne remplace pas** la correction réelle de GitHub Pages :
l'issue de publication #450 reste bloquante.

### Chemins URL encodés et progression de lecture normalisée

Le rejet des dossiers techniques sur les liens issus du registre doit aussi
résister à **l'encodage d'une lettre** : `/%73upabase/private.html`,
`/scrip%74s/report.html` et
`/projets/sinjira/%63odex/private.html` peuvent désigner côté serveur
des chemins techniques bien que le nom de dossier ne corresponde plus
littéralement à la liste d'exclusion du navigateur. Désormais,
`safeLibraryRoute` refuse **toute séquence `%` dans le chemin de
destination**, tout en permettant les valeurs encodées dans la requête
ou l'ancre (ex. `?recherche=La%20Cendre`). Les routes de catalogue
existantes utilisent des chemins littéraux; aucune route de contenu
déjà validée ne nécessite un segment encodé.

La carte de lecture du compte contrôle en outre les données de
progression renvoyées par le registre : une progression non finie
(`NaN`, `Infinity`) devient 0 %, une progression finie est bornée
entre 0 et 100 % et arrondie à l'entier, et le numéro de page n'est
affiché que s'il est un entier positif représentable sans perte.
L'interface ne rend plus `width:NaN%`, un pourcentage négatif ni
une page absurde. Les tests Node exécutent la vraie fonction de
navigation et le rendu de `renderReads`, tandis que le contrat Python
détecte la suppression des gardes.

Ce contrôle concerne uniquement les **données affichées** : il ne
modifie ni la progression stockée, ni les droits de lecture, ni les
fichiers privés. La source GitHub Pages reste en mode `legacy` en
production jusqu'à la résolution de l'incident #450.

### Couvertures locales vérifiées pour les projets et les jeux

Les couvertures des projets (`projects.cover_url`) étaient
auparavant utilisées directement dans les attributs `src` de la
bibliothèque et du détail de projet. Bien qu'échappée pour le HTML,
une destination `https://` vers un domaine non approuvé pouvait
déclencher une requête vers un tiers quand un membre consulte sa
bibliothèque. Une URL de source technique, une image SVG dynamique
ou un chemin brisé pouvaient également être affichés.

`safeLibraryCover`, partagé par les deux bibliothèques, vérifie
désormais que les couvertures issues du registre sont des fichiers
locaux sous `/assets/media/`, avec une extension d'image explicite
(`.webp`, `.png`, `.jpg`, `.jpeg` ou `.avif`) et sans requête,
fragment, antislash, encodage de chemin ni traversée. Les couvertures
invalides sont remplacées par le visuel public SINJIRA
`/assets/media/sinjira-emblem.webp`, ou par la couverture
officielle du jeu lorsqu'une correspondance de projet connue existe.
Les chemins prévus par la migration initiale des jeux sont donc
conservés.

Les tests Node exécutent les véritables fonctions de validation et
le rendu des cartes, notamment avec des URL externes, SVG ou
techniques; le contrat Python empêche les deux bibliothèques de
revenir à l'utilisation directe de `cover_url`. Cette défense
protège le chargement d'images de l'interface, **sans modifier**
la source des données, les permissions Supabase ni le statut de
publication GitHub Pages. L'incident `legacy` #450 reste bloquant.

### Identifiants des comptes : attributs HTML échappés dans les deux bibliothèques

Le registre des projets, documents et playtests est la source des
identifiants réinjectés dans l'interface membre. Les titres,
descriptions et adresses d'images étaient échappés, mais certains
identifiants étaient interpolés directement dans `data-*` ou `id`
lors de la génération par `innerHTML`.

La bibliothèque v24.4.61 protège maintenant l'attribut
`data-v2461-request-tester`. La bibliothèque historique protège
`data-request-tester`, les **deux** occurrences de
`data-open-document`, `data-apply-playtest` et `id` des cartes de
playtests. Tous utilisent `escapeHtml` avant l'insertion dans un
attribut entouré de guillemets. Les valeurs de type UUID existantes
ne changent pas, pas plus que les requêtes côté serveur.

Deux tests Node exercent le **rendu HTML réel** avec des identifiants
malformés contenant guillemets, `onclick`, `<svg>` et `onload`,
sur les deux interfaces. Ils exigent que les guillemets soient
encodés et qu'aucun attribut/élément injectable ne soit ajouté.
Le contrat Python `validate_sinjira_library_status.py` interdit la
suppression des appels `escapeHtml` et protège explicitement les
**deux** boutons de documents.

Ces protections sont une défense supplémentaire du navigateur, et
ne confèrent jamais d'accès à un document ou à un playtest :
les décisions d'accès sont toujours prises par Supabase/RLS et les
fonctions Edge. La publication Pages `legacy` (#450) reste bloquante.

### Demandes testeur et candidatures : Annuler, écriture unique et nouvelle tentative

Les anciennes versions de la bibliothèque interprétaient un clic sur
**Annuler** dans l'invite de message optionnel comme un message vide, puis
envoyaient quand même une demande testeur ou une candidature au playtest.
Elles ne verrouillaient le bouton qu'après la réponse réseau, permettant
deux soumissions simultanées, et ne réactivaient pas toujours le bouton
après une exception Supabase.

Le nouveau contrat `submitLibraryRequest` partagé dans
`assets/js/sinjira-supabase.js` impose :

- **Annuler = aucune écriture et aucun changement de statut**;
  un message vide explicitement confirmé reste permis.
- **Verrouillage immédiat** du bouton pendant la requête : un double clic
  ne peut pas créer de deuxième demande.
- **Réactivation après erreur** réseau ou refus serveur, afin de
  permettre une nouvelle tentative ; une soumission réussie reste
  verrouillée et le libellé ou la carte indique l'état confirmé.
- **Message limité à 1 500 caractères**, sans exposer les détails
  techniques de l'échec du backend dans l'interface.

La bibliothèque actuelle v24.4.61 et l'interface historique, y compris
les candidatures aux playtests, utilisent le même composant. Les tests
Node exécutent le véritable contrôle et les véritables gestionnaires de
clic des trois parcours (annulation, message vide validé, double clic,
réponse différée, rejet serveur/réseau et récupération). Le contrat
Python empêche la suppression de ces gardes.

Il s'agit d'une protection de l'expérience utilisateur contre les
écritures répétées, **pas d'une garantie d'unicité des lignes côté
base de données** : la RLS et les contraintes SQL restent
responsables des autorisations et de l'intégrité persistante.
La PR n'est pas publiée et le blocage GitHub Pages #450 demeure.

### Doublons Postgres déjà protégés : retour utilisateur précis

Deux appareils ou sessions simultanées peuvent produire des écritures
répétées même après un verrouillage du bouton. Le schéma SQL SINJIRA
dispose **déjà** des contraintes serveur appropriées :

- `access_requests_one_pending_idx` : index unique partiel sur
  `(user_id, project_id, requested_level)`, uniquement pour
  `status='pending'`.
- `playtest_participants_pkey` : clé primaire sur
  `(playtest_id, user_id)`.
- Les politiques RLS restrictives sont maintenues. Aucune nouvelle
  migration n'est nécessaire.

Les deux bibliothèques reconnaissent une réponse `23505` seulement
si elle désigne **exactement** la contrainte attendue. La demande
testeur affiche « déjà en attente » et une participation existante
renvoie vers son statut, sans deuxième insertion ni nouvel essai
inutile. Un refus d'autorisation, un problème réseau ou une collision
sur une autre contrainte reste une **erreur**, jamais un succès.

Trois nouveaux tests Node prouvent les contraintes présentes dans les
migrations, la distinction entre vraie violation `23505` et fausse
correspondance, puis le comportement des deux interfaces. Le contrat
Python protège ces vérifications contre leur suppression accidentelle.

Il s'agit d'un changement du frontend et des tests du candidat
GitHub, **sans modification de la base de production**. Le blocage
GitHub Pages #450 reste actif.
