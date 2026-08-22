# SINJIRA™ — Politique des services externes payants

**Statut : garde-fou produit et déploiement — V24.5.4**

SINJIRA peut préparer le code, les interfaces, les contrats techniques et les points d’intégration nécessaires à de futurs services externes. **Préparer une intégration ne constitue jamais une autorisation de l’activer.**

## Règle par défaut

Tout service externe qui exige un paiement, un abonnement, un compte développeur payant ou qui peut générer des frais d’usage reste **désactivé par défaut** tant qu’une décision explicite distincte n’a pas autorisé son activation.

Cette règle couvre notamment :

- fournisseurs de paiement et checkout;
- IA distante facturée à l’usage;
- fournisseurs externes de courriel transactionnel;
- fournisseurs SMS/téléphonie payants;
- publication commerciale nécessitant une infrastructure payante;
- soumission App Store / Google Play lorsqu’elle exige un compte développeur payant ou une action de publication;
- tout autre service tiers dont l’activation peut créer une dépense.

## Ce qui peut être construit sans activation

Il est permis de préparer :

- schémas de données;
- écrans et boutons non actifs;
- interfaces d’adaptation fournisseur;
- variables de configuration laissées désactivées;
- documentation;
- tests utilisant des doubles/mocks locaux;
- workflows de validation qui ne publient ni n’achètent rien;
- application mobile et métadonnées de store sans soumission.

## Activation

Une activation future doit être une décision séparée. Elle doit préciser au minimum :

1. le fournisseur;
2. le coût ou mode de facturation connu;
3. les données transmises au fournisseur;
4. la finalité;
5. les moyens de désactivation;
6. les limites de dépense ou de consommation lorsqu’elles existent.

Aucune simple fusion de code, migration de base de données, création de branche ou mise à jour d’interface ne vaut autorisation d’achat.

## Configuration actuelle

Le runtime public doit conserver les drapeaux suivants à `false` :

- `paidFeaturesEnabled`;
- `paidExternalServicesEnabled`;
- `remoteAiEnabled`;
- `externalEmailDeliveryEnabled`;
- `commercePublishingEnabled`;
- `tokenPurchasesEnabled`;
- `nativeStorePublishingEnabled`.

Le CI doit échouer si une intégration payante connue est activée dans le navigateur, les Edge Functions ou un workflow de publication mobile alors que ces garde-fous restent désactivés.

## Précommandes du Livre I

La V24.5.3 permet d’enregistrer une **réservation de précommande** de `SINJIRA™ — Livre I : La Cendre du Jugement` sans activer le commerce payant.

La table `product_preorders` impose :

```text
payment_status = not_collected
financial_commitment = false
```

Aucune carte bancaire, adresse de facturation ou adresse de livraison n’est demandée dans cette phase. Une réservation ne doit jamais être convertie automatiquement en commande payante. L’ouverture d’un checkout futur exige une décision explicite séparée sur le fournisseur, le coût, les données transmises et les conditions de vente, puis une nouvelle confirmation volontaire de la personne.

### Administration et avis d’ouverture V24.5.4

L’administration peut mesurer la demande et préparer un avis pour les personnes ayant choisi `contact_when_sales_open=true`.

Cet avis suit obligatoirement le parcours :

```text
brouillon → prêt → notification interne SINJIRA
```

La table `preorder_sales_announcements` impose :

```text
external_delivery_enabled = false
payment_activation_allowed = false
```

L’action d’envoi V24.5.4 écrit uniquement dans `user_notifications`. Elle ne doit appeler aucun fournisseur de courriel ou SMS, ne doit ouvrir aucun checkout et ne doit convertir aucune réservation en commande. Le prix éventuellement saisi dans la console est un texte informatif destiné à préparer la communication; il n’autorise aucun débit.

## Héritage numérique

V24.5.2 génère et protège les PDF posthumes sans activer de fournisseur externe de courriel. Les liens de remise peuvent être transmis manuellement. Un transport automatisé futur peut être préparé, mais ne doit pas être activé sans décision explicite sur le fournisseur, la confidentialité et le coût.

> **Construire d’abord; payer ou activer un service externe seulement après une décision explicite.**
