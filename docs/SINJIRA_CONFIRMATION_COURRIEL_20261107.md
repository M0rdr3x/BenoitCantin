# Correctif SINJIRA™ — inscription, confirmation, Registre et notifications Formspree
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

## Intégration Formspree (avis techniques seulement)

Deux formulaires ont été créés dans Formspree :

- **Créer votre compte** : `https://formspree.io/f/xzeeqynp`. La notification n'est faite qu'après confirmation réelle du courriel dans Supabase.
- **Registre des Consciences** : `https://formspree.io/f/mrppvrwa`. La notification n'est faite qu'après écriture confirmée dans `character_submissions`.

Les deux avis sont déclenchés **côté serveur** par un helper unique `supabase/functions/_shared/sinjira-formspree.ts`.
Chaque avis contient seulement `event`, `reference` (UUID aléatoire distinct du compte/dossier), `message` générique et `date`. **Aucune donnée personnelle, photo, courriel, questionnaire, mot de passe ou code parental n'est envoyé à Formspree.** Les dossiers authentiques restent dans Supabase.

Un registre dédié `public.sinjira_formspree_events`, fermé aux rôles `anon`/`authenticated` par RLS et privilèges SQL, assure une seule notification réservée par `(event_type, source_id)`. Un échec Formspree n'annule jamais la sauvegarde du questionnaire ni l'activation du compte. Contrôler aussi l'onglet Spam : Formshield est activé.

### Mise en production dans cet ordre

1. Examiner et tester les modifications de la PR unifiée (remplaçant la PR de confirmation initiale).
2. Exécuter la migration `supabase/migrations/20261108041500_sinjira_formspree_notification_ledger.sql` **avant** de déployer les nouvelles fonctions.
3. Déployer `submit-character-questionnaire` (avec l'import partagé) et `notify-account-confirmation` sur le projet `gpvivleexywljowcqkru`. Conserver **verify_jwt=true** pour les deux.
4. Déployer les fichiers Web depuis GitHub/Netlify et vérifier que `/compte/confirmer.html`, `/assets/js/sinjira-confirm-email.js` et les deux formulaires sont accessibles.
5. Configurer **Supabase Authentication → URL Configuration → Site URL** à `https://www.benoitcantin.com` et autoriser `https://www.benoitcantin.com/compte/confirmer.html` dans Redirect URLs.
6. Dans **Supabase Authentication → Email Templates → Confirm sign up**, installer le modèle avec le fragment `#token_hash={{ .TokenHash }}&amp;type=email` ci-dessus. **Ne jamais activer ce modèle avant que la page `confirmer.html` soit déployée.**
7. Vérifier que la confirmation ne s'effectue pas simplement à l'ouverture du courriel. Seul le clic `Confirmer mon compte` doit échanger le jeton.
8. Faire un essai avec **une adresse de test contrôlée**, puis confirmer que la notification apparaît dans le Formspree **Créer votre compte** une seule fois. Ne jamais soumettre directement à Formspree le formulaire d'inscription contenant les mots de passe.
9. Avec ce compte, configurer le second facteur via `/compte/securite.html`, se reconnecter en AAL2, envoyer une participation factice consentie du Registre, puis vérifier qu'un **seul dossier** est sauvegardé dans Supabase et qu'un **seul avis non nominatif** apparaît dans le Formspree du Registre.
10. Vérifier les erreurs, les délais de courriel, les journaux Auth Supabase et les alertes du Registre. Les courriels de copie du questionnaire restent désactivés par `PAID_EXTERNAL_SERVICES_ENABLED=false` jusqu'à validation d'un transport externe distinct.

### Limites et échecs possibles

- Les anciens courriels utilisant un lien Supabase direct peuvent déjà être expirés ou consommés; l'utilisateur doit demander un **nouveau** lien depuis `/compte/confirmer.html`.
- L'envoi d'avis Formspree est un service **secondaire** et dépend de ses protections anti-spam, quotas et disponibilité.
- Un avis en échec est marqué `delivery_status='failed'` dans le registre interne. Par défaut, aucune répétition automatique n'est lancée, afin de privilégier l'absence de doublons; une reprise contrôlée devra être développée si nécessaire.
- Si JavaScript ne charge pas, les boutons d'envoi restent désactivés. Aucune inscription ou participation ne doit être présentée comme enregistrée.
- La configuration des **modèles de courriel Supabase hébergés** n'est pas modifiée par un commit GitHub : c'est une étape manuelle impérative.

### Vérifications statiques prévues

```sh
python3 scripts/validate_auth.py
python3 scripts/validate_character_questionnaire_security.py
python3 scripts/validate_edge_function_inventory.py
python3 scripts/validate_public_edge_auth.py
python3 scripts/validate_production_schema_manifest.py
python3 scripts/validate_sinjira_signup_registry_delivery.py
```
