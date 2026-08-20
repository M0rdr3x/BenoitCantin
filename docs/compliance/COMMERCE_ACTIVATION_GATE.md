# SINJIRA™ — gate d'activation commerce et fonctions payantes

Version V24.4.83. État actuel: **désactivé**.

Aucune fonction d'achat de Points SINJIRA™, marketplace, abonnement, paiement, IA distante payante ou publication commerciale ne peut être considérée prête à activer tant que tous les points ci-dessous ne sont pas satisfaits et que Benoit Cantin n'a pas donné une approbation explicite d'activation payante.

## Contrôles obligatoires avant activation

1. **Protection du consommateur**: prix total, devise, taxes, conditions, remboursement, renouvellement, livraison et preuve de transaction selon les juridictions ciblées.
2. **Paiement**: fournisseur spécialisé; SINJIRA™ ne stocke pas de numéro complet de carte ni de code de sécurité.
3. **Mineurs**: déterminer si les achats jeunesse sont interdits, soumis à consentement parental ou à des règles spéciales; par défaut, aucun achat jeunesse.
4. **Points SINJIRA™**: préciser clairement leur nature, expiration éventuelle, remboursement/transfert, valeur et absence de confusion avec une monnaie réglementée.
5. **CASL/marketing**: consentement, identification et désabonnement avant toute messagerie commerciale automatisée.
6. **Vie privée**: EFVP, fournisseurs, transfert hors Québec, conservation, finalités et politique publique à jour.
7. **Sécurité**: anti-fraude, idempotence, journal de transaction, remboursements, litiges et contrôle d'accès.
8. **Fiscalité/comptabilité**: obligations applicables validées.
9. **Marketplace**: identité/coordonnées vendeur, biens interdits, modération, retraits et obligations locales validés avant ouverture.
10. **Contenu interdit**: aucune monétisation de prostitution, exploitation sexuelle, contenu sexuel payant, traite, drogues, armes/biens interdits ou accès à un mineur.

## Conditions de déploiement

- `paidFeaturesEnabled=false` jusqu'à approbation explicite;
- `commercePublishingEnabled=false`;
- `tokenPurchasesEnabled=false`;
- `remoteAiEnabled=false`;
- `allowPaymentCredentials=false`;
- aucune clé de paiement ou OpenAI ne doit être auto-provisionnée par les workflows;
- une PR dédiée, EFVP mise à jour et tests de sécurité sont requis avant tout changement de ces valeurs.

## Critère d'arrêt

S'il existe un doute matériel sur une obligation de consommation, d'âge, de fiscalité, de données ou de paiement dans une juridiction ciblée, la fonction reste désactivée jusqu'à validation spécialisée.
