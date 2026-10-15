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
