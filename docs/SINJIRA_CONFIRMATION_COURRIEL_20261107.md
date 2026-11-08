# Correctif SINJIRA™ — activation des comptes par confirmation volontaire
Date : 2026-11-07

## Diagnostic du projet connecté

- Le point d'entrée `/compte/inscription.html` appelle Supabase Auth `signUp`.
- Des journaux Auth ont montré des réponses d'inscription 200, puis des vérifications `/verify` avec « One-time token not found » et « Email link is invalid or has expired ».
- Les systèmes de sécurité des messageries peuvent préouvrir les URL et consommer les liens à usage unique. C'est une **cause possible**, pas une certitude établie pour chaque visiteur.
- Le formulaire `/projets/sinjira/registre/` exige une session authentifiée; il vérifie en outre la protection AAL2/TOTP quand `sensitive_step_up` est activé (valeur par défaut).
- L'envoi externe des copies et avis du Registre est désactivé dans la fonction actuelle. Il est distinct des courriels de confirmation de Supabase Auth.

## Déploiement — ordre impératif

1. Fusionner puis déployer les fichiers de ce correctif. **Ne pas modifier le modèle de courriel avant que la page et son script soient effectivement disponibles en production.**
2. Vérifier que les deux URL publiques répondent :
   - `https://www.benoitcantin.com/compte/confirmer.html`
   - `https://www.benoitcantin.com/assets/js/sinjira-confirm-email.js`
3. Ouvrir Supabase Dashboard → Authentication → URL Configuration :
   - **Site URL** : `https://www.benoitcantin.com` (ne pas laisser localhost).
   - Ajouter dans les **Redirect URLs** : `https://www.benoitcantin.com/compte/confirmer.html`.
   - Conserver temporairement les anciennes routes de retour tant que les anciens courriels circulent.
4. Ouvrir Supabase Dashboard → Authentication → Email Templates → **Confirm sign up**.
5. Remplacer uniquement le modèle **Confirm sign up** par ce modèle (ne pas changer les modèles de récupération et de changement d'adresse) :

```html
<!doctype html>
<html lang="fr">
  <body>
    <h2>Confirmez votre adresse courriel SINJIRA™</h2>
    <p>Pour activer votre compte, ouvrez la page suivante et cliquez ensuite sur « Confirmer mon compte » :</p>
    <p>
      <a href="https://www.benoitcantin.com/compte/confirmer.html#token_hash={{ .TokenHash }}&amp;type=email">
        Ouvrir la confirmation SINJIRA™
      </a>
    </p>
    <p>Si vous n'avez pas demandé de compte SINJIRA™, ignorez ce message.</p>
  </body>
</html>
```

Le `#token_hash=` fait voyager le jeton dans le fragment URL (non envoyé au serveur de pages statiques). La page **n'appelle pas** `verifyOtp` pendant le chargement; elle l'appelle seulement après un clic explicite. Ne pas inclure de jeton dans une capture d'écran, un ticket, un journal ou un message.

6. Si un prestataire de courriel réécrit les liens pour le suivi de clic, **désactiver le suivi des liens** pour les messages d'authentification.
7. Faire un test avec un compte de test et une boîte de réception administrée par vous : inscription → courriel → page SINJIRA → clic explicite → authentification → ouverture Compte ou Registre. Vérifier la récupération quand un lien est expiré au moyen de « Renvoyer un lien ».
8. Pour transmettre le questionnaire, le visiteur doit être connecté. Lorsque la protection sensible est activée, il doit configurer la 2FA dans `/compte/securite.html` et valider la session AAL2. **Ce correctif ne diminue pas les contrôles de sécurité des dossiers privés.**
9. Tester un questionnaire de test avec consentement et vérifier le nouvel enregistrement dans l'administration. Les copies par courriel du questionnaire resteront **désactivées** jusqu'à configuration explicite d'un service d'envoi adapté; cela ne doit pas être confondu avec une erreur de sauvegarde.

## Tests de non-régression suggérés

- Le lien du modèle ne vise **pas** `/auth/v1/verify` directement.
- Consulter la page sans cliquer n'active pas le compte.
- Un lien à jeton invalide affiche un message et le renvoi, sans consommer d'autres jetons.
- Le renvoi d'une confirmation n'expose pas l'existence d'un compte (message générique).
- L'option « questionnaire » dirige vers le Registre après validation.
- Le Registre ne transmet pas sans session valide et conserve son contrôle MFA/AAL2.
- Aucun secret serveur, clé de service ou donnée personnelle n'est ajouté au dépôt.
- Vérifier les tests CI et l'allowlist de publication Web avant fusion.

Documentation officielle :
- https://supabase.com/docs/guides/auth/auth-email-templates
- https://supabase.com/docs/guides/auth/redirect-urls
- https://supabase.com/docs/reference/javascript/auth-verifyotp
