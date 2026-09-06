# SINJIRA V25 — Hub Vie privée natif

## But

Ajouter une surface React Native de navigation pour la Vie privée sans déplacer les demandes, leur état ni les renseignements personnels hors de la source de vérité Web/serveur.

Le bouton **Vie privée** du hub Profil natif ouvre ce hub local. Il n’exécute aucune demande de droit et ne reçoit aucune donnée du compte.

## Frontière

Le hub Vie privée natif :

- ne lit aucune demande Vie privée existante;
- ne crée, ne modifie, ne supprime et ne soumet aucun dossier;
- ne demande aucune pièce d’identité, aucun secret, aucun GPS et aucune adresse IP brute;
- n’appelle ni Supabase, ni Edge Function, ni RPC;
- n’utilise ni WebView propre, ni `SecureStore`, ni `AsyncStorage`;
- ne copie aucune donnée du profil, du Registre personnel, de l’Histoire de vie ou de Mon IA.

Les opérations restent dans les surfaces canoniques :

- exercer un droit : `/compte/vie-privee.html?surface=web`;
- politique publique : `/confidentialite.html`;
- sécurité : `/compte/securite.html`;
- paramètres : `/compte/parametres.html`.

## Intégration

`NativeProfileHub` conserve ses deux capacités (`onOpenPath`, `onBack`). L’ouverture de Vie privée est un état d’interface local; toute sortie réelle repasse par `onOpenPath` et donc par le shell mobile existant.

## Principe

**L’HUMAIN AVANT TOUT. Protéger sans surveiller.**

Le natif simplifie l’orientation sans devenir un second registre de renseignements personnels.
