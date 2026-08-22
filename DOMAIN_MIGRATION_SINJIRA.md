# Migration de domaine SINJIRA™ — plan de bascule

Version : **V24.4.99**  
Statut : **préparation uniquement — aucun changement DNS autorisé par ce document**

## 1. État actuel

- Site actif : `https://www.benoitcantin.com`
- Domaine réservé : `sinjira.com`
- Application mobile : origine active `https://www.benoitcantin.com`
- Supabase : projet de production actuel inchangé
- Passkeys/WebAuthn : **non activées**

Le domaine réservé ne doit pas devenir l’origine de production par simple modification isolée. La bascule doit être atomique, vérifiable et réversible.

## 2. Cible

Les hôtes prévus sont :

- `sinjira.com`
- `www.sinjira.com`

Le choix du nom canonique public (`sinjira.com` ou `www.sinjira.com`) doit être fixé au moment du cutover. L’autre hôte redirigera en HTTPS vers le canonique.

Pour les futures passkeys, le RP ID prévu est **`sinjira.com`**, afin de pouvoir couvrir le domaine racine et les sous-domaines compatibles.

## 3. Préparation déjà réalisée en V24.4.99

- l’origine Web de l’app Expo est configurable par `expo.extra.webOrigin`;
- la valeur active reste `https://www.benoitcantin.com`;
- l’app refuse les origines qui ne font pas partie de la liste SINJIRA autorisée;
- iOS déclare à l’avance `applinks:sinjira.com` et `applinks:www.sinjira.com`;
- Android déclare à l’avance les routes `/app`, `/compte` et `/projets/sinjira` pour les deux futurs hôtes;
- aucune passkey n’est créée avant le domaine définitif.

Ces déclarations mobiles ne prouvent pas encore la propriété des domaines : les fichiers d’association doivent être publiés au cutover avec les identifiants réels de signature.

## 4. Prévol obligatoire avant changement DNS

### Web et hébergement

1. Confirmer quel hôte sera canonique.
2. Préparer le certificat HTTPS pour les deux hôtes.
3. Vérifier que toutes les routes critiques fonctionnent sur le futur hôte :
   - `/`
   - `/app/`
   - `/compte/connexion.html`
   - `/compte/securite.html`
   - `/projets/sinjira/registre/`
4. Préparer les redirections permanentes de l’ancien domaine sans créer de boucle.
5. Conserver `www.benoitcantin.com` comme redirection de continuité après la migration.

### Supabase Auth

Avant la bascule :

- ajouter le futur domaine dans les URL autorisées;
- ajouter les callbacks de connexion, confirmation de courriel et récupération de mot de passe;
- vérifier que le Site URL et les redirect URLs correspondent au canonique choisi;
- tester inscription, connexion, MFA, récupération, déconnexion globale et Bouclier de connexion;
- ne retirer aucune URL de l’ancien domaine avant que les liens déjà envoyés aient eu le temps d’expirer.

### Application iOS

Publier sur le domaine définitif :

`/.well-known/apple-app-site-association`

Le fichier devra contenir le véritable **Apple Team ID** et le bundle `com.benoitcantin.sinjira`. Ne jamais inventer le Team ID.

### Application Android

Publier :

`/.well-known/assetlinks.json`

Le fichier devra contenir le package `com.benoitcantin.sinjira` et le véritable **SHA-256 du certificat de signature de production**. Ne jamais utiliser une empreinte de développement à la place.

## 5. Cutover

Ordre recommandé :

1. Mettre en place les associations et callbacks sans retirer l’ancien domaine.
2. Valider HTTPS et les pages critiques sur `sinjira.com`/`www.sinjira.com`.
3. Modifier `mobile-native/app.json` → `extra.webOrigin` vers le domaine canonique.
4. Exécuter tous les tests Web, Auth, Supabase et mobile.
5. Modifier le DNS seulement lorsque le prévol est vert.
6. Vérifier immédiatement connexion, récupération, MFA, Registre, Ma sécurité et notifications.
7. Activer les redirections de continuité depuis `benoitcantin.com`.
8. Surveiller les erreurs 4xx/5xx, callbacks Auth et liens profonds pendant la période de transition.

## 6. Passkeys — après le cutover uniquement

Les passkeys ne doivent être activées qu'après :

- domaine définitif en HTTPS;
- RP ID fixé à `sinjira.com`;
- callbacks Supabase définitifs;
- associations mobiles vérifiées;
- procédure de récupération de compte testée sans passkey puis avec passkey;
- possibilité claire de révoquer une passkey depuis Ma sécurité.

La biométrie du téléphone reste locale : SINJIRA ne reçoit ni visage ni empreinte.

## 7. Rollback

Si une erreur critique apparaît après bascule :

1. restaurer l’ancien hôte comme origine active;
2. rétablir les callbacks Supabase précédents;
3. remettre `extra.webOrigin` sur `https://www.benoitcantin.com` pour la prochaine build mobile;
4. conserver les nouveaux hôtes en redirection temporaire si cela n’aggrave pas l’incident;
5. ne jamais supprimer les données Auth, les appareils ou le Registre pour résoudre un problème DNS.

## 8. Interdictions de sécurité

- pas de DNS modifié sans prévol complet;
- pas de passkey attachée au domaine temporaire par commodité;
- pas de GPS ou d’IP brute ajoutés pour « faciliter » la migration;
- pas de copie de base de données vers un second compte utilisateur;
- pas de changement d’identité entre le compte Web et l’application native;
- pas de suppression de l’ancien domaine avant la période de continuité.

**Principe : une migration de domaine doit déplacer l’adresse de SINJIRA, pas l’identité ni les droits de la personne.**
