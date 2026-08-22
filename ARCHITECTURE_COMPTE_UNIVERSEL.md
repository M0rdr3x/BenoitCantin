# Architecture — Compte SINJIRA universel

> Référence normative : [`CAHIER_MAITRE_SINJIRA.md`](CAHIER_MAITRE_SINJIRA.md). En cas de conflit, le Cahier maître prévaut.
>
> Protocole opérationnel d’héritage numérique : [`HERITAGE_NUMERIQUE_V24_5_2.md`](HERITAGE_NUMERIQUE_V24_5_2.md).
>
> Protocole de réservation du Livre I : [`PRECOMMANDES_ROMAN_V24_5_3.md`](PRECOMMANDES_ROMAN_V24_5_3.md).
>
> Préparation commerciale du Livre I : [`PREPARATION_COMMERCIALE_LIVRE_I_V24_5_5.md`](PREPARATION_COMMERCIALE_LIVRE_I_V24_5_5.md).
>
> Livraison et ramassage du Livre I : [`LIVRAISON_RAMASSAGE_LIVRE_I_V24_5_6.md`](LIVRAISON_RAMASSAGE_LIVRE_I_V24_5_6.md).
>
> Garde-fou de déploiement : [`SERVICES_EXTERNES_PAYANTS.md`](SERVICES_EXTERNES_PAYANTS.md). Une intégration externe payante peut être construite, mais elle reste désactivée sans décision explicite séparée.

```text
Compte SINJIRA
├── Mon espace
├── Bibliothèque
│   ├── Fracture du Réseau-Mère
│   ├── Réseau-Mère : Résistance
│   └── futurs jeux
├── Documents approuvés
├── Mes parties
├── Playtests
├── Profil
├── Contributions
├── Mes achats et précommandes
│   ├── Précommande Livre I — La Cendre du Jugement
│   │   ├── Informations commerciales publiées, si disponibles
│   │   ├── Estimation de livraison par zone
│   │   └── Préférence livraison / ramassage / plus tard
│   └── Achats payants (désactivés tant que la boutique n’est pas autorisée)
├── Histoire de vie
│   ├── Mes éléments privés
│   ├── Mes versions
│   │   ├── Famille
│   │   ├── Personnelle
│   │   └── Générale
│   ├── Destinataires choisis
│   ├── Directive posthume
│   ├── Codes privés de signalement
│   └── Contestation d’une fausse déclaration de décès
├── Ma sécurité
│   ├── Mes appareils
│   ├── Connexions récentes
│   ├── Mode Voyage
│   ├── Passkeys et authentification
│   ├── Téléphone perdu
│   ├── Compte compromis
│   └── Récupération du compte
└── Paramètres
```

## Principe de sécurité du Compte

Le Compte universel respecte le principe **protéger sans surveiller** : les données techniques utilisées pour la sécurité sont minimisées et ne sont pas réutilisées à des fins publicitaires, commerciales, sociales, de Rencontres, d’Emploi ou de profilage sans consentement distinct.

La localisation seule ne suffit pas à conclure qu’une connexion est frauduleuse. Le Bouclier de connexion doit combiner plusieurs signaux, avec une réponse graduée et une authentification renforcée lorsque le risque l’exige.

Le **Registre des Consciences**, les conversations privées avec l’IA personnelle, les moyens de récupération du compte et les opérations d’héritage numérique appartiennent au niveau **extrêmement sensible** et peuvent exiger une nouvelle authentification même lorsqu’une session est déjà ouverte.

## Précommandes de romans

Une réservation de précommande est un objet distinct d’une commande payante.

En V24.5.3, le Livre I peut être réservé depuis la section Littérature ou depuis **Mes achats et précommandes**. La réservation conserve le produit, le format souhaité, la quantité et une préférence d’avertissement interne. Elle ne collecte ni carte bancaire, ni adresse de facturation, ni adresse de livraison.

Les invariants serveur de cette phase sont :

```text
payment_status = not_collected
financial_commitment = false
```

Une réservation ne peut jamais être transformée automatiquement en vente. Une future ouverture de la boutique doit présenter les prix et conditions réels, puis obtenir une nouvelle confirmation volontaire avant tout checkout.

### Préparation commerciale V24.5.5

La fiche commerciale du Livre I est séparée de `product_preorders`, `orders` et `order_items`.

Elle permet à l’administration MFA/AAL2 de préparer puis de publier uniquement des informations confirmées : devise, prix, éditions, date de sortie, disponibilité et résumé des conditions. Aucun prix ni aucune date n’est prérempli automatiquement.

Le parcours est :

```text
brouillon privé
      ↓
prêt après contrôle de complétude
      ↓
publication informative
```

La publication informative n’est jamais assimilée à l’ouverture des ventes. La base impose :

```text
sales_enabled = false
checkout_enabled = false
payment_enabled = false
external_fulfillment_enabled = false
auto_conversion_allowed = false
```

Une révision publiée devient immuable. Une modification future doit passer par une nouvelle révision afin que l’information précédemment affichée ne soit pas réécrite silencieusement.

La publication de la fiche commerciale ne crée aucune notification. Le mécanisme d’avis interne V24.5.4 demeure un parcours séparé.

### Livraison et ramassage V24.5.6

Le parcours de livraison est séparé du paiement. Pour un livre physique expédié, les frais de livraison sont à la charge du client et doivent être annoncés avant l’achat.

Le calculateur de précommande utilise uniquement une zone publiée et la quantité. Il ne demande ni ne stocke l’adresse de livraison. La fourchette affichée est indicative et le montant réel doit être présenté avant toute future commande.

La préférence de réception peut être :

```text
shipping
pickup
undecided
```

Le ramassage sur place n’ajoute aucun frais de livraison. Un point de retrait reste privé jusqu’à publication explicite de son adresse et de ses instructions par un administrateur MFA/AAL2. Modifier un tarif ou un point publié le remet en brouillon avant une nouvelle publication.

Aucune API transporteur ou achat d’étiquette externe n’est actif en V24.5.6.

## Histoire de vie et héritage numérique

L’**Histoire de vie** et le **Registre des Consciences** sont deux domaines techniques et fonctionnels distincts.

Un élément ajouté à l’Histoire de vie est **privé par défaut**. Il n’entre dans une œuvre transmissible qu’après deux choix explicites de la personne :

1. autoriser l’élément pour l’œuvre;
2. choisir la ou les versions dans lesquelles il peut apparaître.

La transmission posthume est désactivée tant que la personne n’a pas activé sa directive. Les destinataires sont choisis par la personne et peuvent être absents.

Le protocole posthume V24.5.2 suit obligatoirement cette séquence :

```text
Code privé ou demande légitime
            ↓
Signalement de décès
            ↓
Première vérification humaine
            ↓
Délai de sécurité de 30 jours
            ↓
Contestation possible à tout moment applicable
            ↓
Deuxième validation humaine avec MFA/AAL2
            ↓
Instantané Histoire de vie autorisé uniquement
            ↓
PDF privé
            ↓
Lien de remise opaque, expirant et révocable
            ↓
Revue humaine de rétention / suppression
```

Un signalement ne constitue jamais une validation. Une contestation ouverte suspend la seconde validation et la génération. Si une contestation est rejetée après vérification humaine, un **nouveau délai complet de 30 jours** commence.

Le générateur PDF applique une frontière serveur `life_story_only` et ne doit jamais lire le Registre, les personnages, les conversations privées de l’IA ou une autre source intime non explicitement autorisée.

Les liens destinés aux proches ne rendent aucun bucket public. Le jeton brut n’est pas stocké : seul son hash est conservé, avec expiration, révocation et limite de téléchargements.

Aucun fournisseur externe de courriel n’est requis par défaut. Une remise peut rester manuelle afin d’éviter d’introduire un service tiers ou payant sans décision explicite.

Après les opérations autorisées, les tâches de nettoyage sont des **revues humaines**. Elles ne doivent pas effacer automatiquement le Registre ou les données sources à partir d’un simple délai.

## Mode Voyage

Le Compte doit prévoir un Mode Voyage accessible depuis **Ma sécurité**. L’utilisateur peut indiquer une destination ou région approximative et une période, sans fournir d’hôtel, de trajet quotidien, de numéro de vol ou de GPS permanent.

Les données spécifiques au voyage doivent avoir une durée de conservation courte et servir exclusivement à la sécurité.

## Appareils de confiance

L’utilisateur doit pouvoir reconnaître et révoquer ses appareils de confiance, déconnecter un appareil ou déconnecter toutes les autres sessions. L’application mobile peut devenir l’appareil principal de confiance pour autoriser ou refuser certaines nouvelles connexions.

## Niveaux de documents

- `public` : public si le projet est public.
- `account` : tout Compte SINJIRA connecté.
- `player` : joueur explicitement approuvé pour le projet.
- `tester` : testeur explicitement approuvé pour le projet.
- `admin` : administration seulement.

Le statut **Contributeur** est séparé de ces niveaux. Il correspond à un consentement volontaire de partage de données de gameplay.

## Documents privés

Les documents non publics ne doivent pas être placés dans GitHub Pages.

Ils sont téléversés dans le bucket privé :

`sinjira-private-documents`

Quand un joueur ouvre un document, `get-document-url` :
1. vérifie que le document est approuvé;
2. vérifie le projet;
3. vérifie le niveau d'accès du compte;
4. génère un lien signé temporaire de 10 minutes.

Les PDF posthumes utilisent un bucket distinct et privé :

`sinjira-life-story-exports`

Ce bucket n’est jamais une source publique et ses fichiers ne sont accessibles que par le protocole de remise autorisé.

## Playtests

Un compte peut poser sa candidature.
L'administration approuve ou refuse.
Une approbation peut automatiquement donner le niveau `tester` sur le projet.

## Services externes payants

Le code peut préparer des adaptateurs ou intégrations futures, mais leur activation reste séparée du développement. Par défaut : paiements, IA distante payante, courriel/SMS externe payant, transporteurs externes, publication commerciale transactionnelle et soumission App Store/Google Play restent désactivés. Le CI doit empêcher leur activation accidentelle tant que le projet demeure en mode gratuit.

## Futures extensions

Les commentaires de joueurs utilisés dans la section Extensions proviennent uniquement des contributions volontaires.
Les courriels, pseudos, codes de partie et notes privées ne sont pas inclus dans l'analyse de gameplay.
