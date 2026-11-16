# SINJIRA V142 — conserver la page lue lors d'une saisie incomplète

**16 novembre 2026 — PR #1000 DRAFT, non fusionnée ni déployée.**

## Défaut constaté

Dans `changePage(value)` du lecteur V26, `clamp(Math.round(value),1,max)` utilisait `Number(value)||min`. Les chaînes `''` et `' '` produisent zéro, donc **page 1**, dès que l'utilisateur effaçait provisoirement son numéro de page et quittait le champ sur son cellulaire. Une valeur mal formée ou infinie pouvait également sélectionner la page initiale. La nouvelle navigation réinitialisait alors la position précise et écrivait une nouvelle progression, perdant le passage lu.

## Correction

- Avant `clamp`, valider la demande comme un **entier sûr strictement positif** après suppression des espaces extérieurs.
- Lorsqu'elle est vide, non entière, négative, nulle, infinie ou invalide, **ne pas changer de page, ne pas défiler, ne pas déclencher de rendu ni écrire une progression**.
- Rétablir les valeurs réelles du champ numérique, du curseur de pages et du chapitre, sans signal global de repagination pendant que le lecteur pourrait être en transition.
- Lorsqu'une demande valide et hors du PDF est bornée à la page actuelle, rétablir aussi les contrôles (l'ancien retour prématuré conservait parfois `999` dans le champ, tandis que la page réelle restait différente).
- Garder les commandes valides (boutons, gestes tactiles, chapitres et saisie d'un entier) inchangées. Ne pas toucher à la sécurité serveur ni au contenu privé.
- Mettre à jour la version cache JS V26 vers `34.11.16.142`, avec le contrat Node correspondant.

## Régression

Dans `tests/e2e/test_sinjira_liseuse_real_page_v57.py` sur la vraie page HTML avec PDF fictif et accès Supabase bloqué : depuis la page 3, vider le champ puis essayer zéro, négatif, décimal et infini; vérifier après chaque commande l'absence d'événement de changement de page et l'identité stricte du numéro, curseur, chapitre, scroll, texte de sauvegarde et valeurs `localStorage` de progression.

Les autres tests automatisés doivent confirmer les changements de page valides et les gestes dans Chromium et WebKit. **CI de SHA final à vérifier.** La PR demeure **NO-GO production** jusqu'aux essais physiques iOS/Android, VoiceOver/TalkBack, homologation des droits privés et synchronisation multiappareils. Les scores des programmes Nova/SINJIRA restent inchangés.
