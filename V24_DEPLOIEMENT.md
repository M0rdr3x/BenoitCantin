# SINJIRA™ V24 — déploiement

Ce dépôt est le **pack cumulatif prêt à remplacer le contenu actuel du dépôt GitHub Pages**.
Il part du site fourni le 14 août 2026 et intègre les correctifs V23 ainsi que la fondation Web V24.

## Ordre recommandé

1. Faire une sauvegarde du dépôt GitHub actuel.
2. Copier **tout le contenu de ce pack à la racine du dépôt** `M0rdr3x/BenoitCantin`.
3. Vérifier que `.nojekyll`, `CNAME`, `index.html`, `assets/`, `projets/`, `compte/`, `admin/` et `supabase/` sont bien à la racine.
4. Publier GitHub Pages et vérifier les pages publiques.
5. **Avant d'utiliser les nouveaux champs privés, Relations, Monde parallèle, Marché, Jetons ou codes d'activation**, appliquer dans Supabase :
   `supabase/migrations/20260814_sinjira_v24_foundation.sql`
6. Redéployer les Edge Functions déjà modifiées en V23 si ce n'est pas encore fait :
   - `submit-character-questionnaire`
   - `admin-sinjira-v18`
7. Pour les licences physiques, déployer aussi :
   - `admin-license-codes`
   - `redeem-license-code`
8. Créer dans les secrets Supabase un secret aléatoire long nommé `SINJIRA_LICENSE_PEPPER` avant de générer des codes.

## IA

L'IA reste **désactivée en V24**. Le questionnaire envoie `manual_only: true`.
Le fichier `assets/js/v24-feature-flags.js` garde `ai: false`.

## Livre I

La nouvelle couverture Web est intégrée dans `assets/media/`.
La nouvelle démo corrigée remplace le PDF public existant.

Le PDF intégral corrigé du Livre I n'est volontairement **pas inclus** dans ce dépôt public GitHub Pages.
Empreinte SHA-256 du maître reçu :
`650a025509d831bb3b4deca70de2e221948f5b6ddf1396c599ce27be51a22c29`

Empreinte SHA-256 de la démo corrigée publique :
`b5aef85dc04369f36a7687e97fbe39d606ea2b211620e0ab9640fc9dd53f0e37`

Empreinte SHA-256 de la nouvelle couverture source reçue :
`a5b8f1992df03a3d46ffbc2caf000d5a6b772410210585b3eb80e51cbfdd784f`

## Fonctions préparées mais non activées commercialement

- paiements du Marché;
- vente de Jetons SINJIRA™;
- conseil de prix IA;
- IA du Monde parallèle;
- vidéoconférence / partage d'écran;
- canaux temps réel avancés;
- paiement de la version numérique de Fracture.

Les pages et tables de fondation sont présentes afin de ne pas refaire l'architecture plus tard, mais ces fonctions doivent rester désactivées jusqu'aux tests, fournisseurs et règles finales.
