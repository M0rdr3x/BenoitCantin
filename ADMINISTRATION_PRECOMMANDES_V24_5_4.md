# SINJIRA™ — Administration des précommandes V24.5.4

**Statut : module opérationnel sans paiement ni transport externe.**

Cette version complète la réservation V24.5.3 du Livre I avec une console administrative destinée à mesurer la demande et à préparer l’ouverture future des ventes.

## 1. Périmètre

La console `/admin/sinjira/precommandes.html` est réservée à l’administration SINJIRA et exige MFA/AAL2.

Elle permet de consulter :

- le nombre de réservations actives et annulées;
- le nombre d’exemplaires souhaités;
- les préférences papier, numérique, papier + numérique ou indécises;
- le nombre de personnes ayant demandé un avertissement interne;
- la liste des réservations sans exposer courriel, adresse postale ou identifiant technique.

## 2. Avis interne

L’ouverture future des ventes suit trois actions distinctes :

```text
brouillon → prêt → notification interne SINJIRA
```

L’enregistrement d’un brouillon n’envoie rien. Le passage à l’état `ready` n’envoie rien. L’action finale écrit uniquement dans `user_notifications` pour les réservations actives ayant `contact_when_sales_open=true`.

Aucun avis réel ne doit être envoyé avant que les conditions officielles de vente aient été définies.

## 3. Verrous financiers

La table `preorder_sales_announcements` impose :

```text
external_delivery_enabled = false
payment_activation_allowed = false
```

Le module ne doit jamais :

- créer une commande dans `orders` ou `order_items`;
- ouvrir un checkout;
- débiter une carte;
- appeler Stripe, PayPal ou un autre fournisseur de paiement;
- envoyer un courriel ou SMS via un fournisseur externe;
- convertir automatiquement une réservation en achat.

Le champ de prix de la console est un texte informatif préparatoire uniquement.

## 4. Sécurité

Toutes les opérations administratives utilisent des RPC `SECURITY DEFINER` qui appellent immédiatement `private.require_sinjira_admin_aal2()`.

La table interne est scellée : RLS activée, aucun accès direct `anon` ou `authenticated`, aucune policy de lecture directe. Les données sont exposées seulement par les RPC administratifs minimisés.

## 5. Vie privée

La liste administrative affiche un pseudo ou nom d’affichage lorsqu’il existe, sinon `Compte SINJIRA`. Elle ne fournit pas :

- le courriel;
- l’adresse de facturation;
- l’adresse de livraison;
- l’UUID interne du compte dans l’interface.

## 6. Activation future des ventes

V24.5.4 ne constitue pas une autorisation de vendre. Une future version transactionnelle devra faire l’objet d’une décision distincte concernant le fournisseur de paiement, les coûts, les données transmises, les prix, les conditions de vente et le consentement final de l’acheteur.
