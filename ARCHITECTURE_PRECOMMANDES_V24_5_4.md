# SINJIRA™ — Architecture des précommandes V24.5.4

Cette note complète `PRECOMMANDES_ROMAN_V24_5_3.md` et `ADMINISTRATION_PRECOMMANDES_V24_5_4.md`.

```text
Compte SINJIRA
   ↓
Réservation V24.5.3
   ↓
product_preorders
   ↓
Administration MFA/AAL2
   ├── statistiques agrégées
   ├── liste minimisée
   └── brouillon d’avis
            ↓
         prêt
            ↓
notification interne SINJIRA
            ↓
user_notifications
```

Aucune branche de ce flux ne mène à `orders`, `order_items`, un checkout ou un fournisseur externe.

Les invariants demeurent :

```text
payment_status = not_collected
financial_commitment = false
external_delivery_enabled = false
payment_activation_allowed = false
```

L’ouverture future d’une vente devra être une version séparée, accompagnée d’un nouveau consentement de l’acheteur et d’une décision explicite avant toute activation d’un service payant.
