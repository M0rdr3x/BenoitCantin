# Hub Commerce natif V25

## Principe

**L’HUMAIN AVANT TOUT. Protéger sans surveiller.**

`NativeCommerceHub` est un sas de navigation uniquement. Il ne devient jamais un portefeuille, un checkout, un grand livre, une boutique ou une source de vérité commerciale.

## Données volontairement absentes du natif

Le hub ne reçoit, ne lit, ne calcule et ne stocke aucun :

- solde de Jetons ou mouvement de grand livre;
- statut propriétaire ou administrateur lié aux Jetons;
- achat, commande, reçu ou téléchargement;
- réservation de précommande, format, quantité ou préférence de contact;
- préférence de livraison ou ramassage;
- adresse de facturation, adresse de livraison ou donnée bancaire;
- annonce, prix, description, état d’objet ou localisation approximative;
- licence ou droit numérique;
- compteur ou résumé financier/transactionnel.

## Paiements

Les surfaces auditées indiquent que les achats payants restent désactivés. Le hub natif ne peut pas initier un checkout, recueillir un moyen de paiement ou transformer une réservation en commande.

Si un fournisseur de paiement est activé plus tard, son intégration devra faire l’objet d’un contrat de sécurité séparé avant toute capacité native.

## Jetons

Le grand livre reste côté serveur. Le hub ne lit ni solde ni historique et ne crédite, débite ou transfère aucun Jeton SINJIRA™. Il ne reproduit pas non plus le traitement spécial éventuel d’un compte propriétaire.

## Marché

Les brouillons restent côté Web/serveur. Le hub ne crée, ne modifie, ne publie et ne supprime aucune annonce et ne conserve jamais sa localisation approximative.

## Précommandes

Une réservation n’est pas une commande et n’est pas un consentement à payer. Le natif ne lit ni format, quantité, référence, conditions acceptées, choix de réception ou estimation logistique.

## Navigation autorisée

Le hub peut seulement ouvrir explicitement :

- `/compte/mes-achats.html?surface=web`;
- `/compte/marche.html?surface=web`;
- `/compte/jetons.html?surface=web`;
- `/compte/licences.html?surface=web`.

Aucun `Supabase`, RPC, `fetch`, WebView, SecureStore, AsyncStorage, notification, presse-papiers ou API de paiement n’est ajouté au composant.

## Pas de profil commercial

Les achats, annonces, Jetons, licences et préférences ne doivent pas être transformés en score de valeur, richesse supposée ou profil comportemental. Les données restent limitées à la fonction explicitement demandée.
