# SINJIRA V25 — Hub Profil natif

## But

Ajouter une nouvelle surface React Native utile et fréquente sans déplacer la source de vérité du profil hors du Web/serveur.

Le bouton **Profil** de l’accueil natif ouvre un hub React Native de navigation seulement. Ce hub ne reçoit aucune donnée utilisateur et n’interroge aucun service.

## Frontière de sécurité

Le hub Profil natif :

- ne lit ni nom affiché, courriel, photo, date de naissance, localisation déclarée, relation ou préférence;
- n’appelle ni Supabase, ni Edge Function, ni RPC;
- n’utilise ni `SecureStore`, ni `AsyncStorage`, ni WebView propre;
- ne télécharge, n’exporte et ne supprime aucune donnée;
- ne modifie aucun profil et ne contourne aucune règle RLS, d’âge, de juridiction ou de sécurité;
- ne reçoit aucun contenu du Registre personnel, de l’Histoire de vie ou de Mon IA.

Les actions réelles restent dans les surfaces existantes :

- profil complet : `/compte/profil.html?surface=web`;
- Vie privée : `/compte/vie-privee.html`;
- Paramètres : `/compte/parametres.html`;
- Ma sécurité : `/compte/securite.html`.

Le paramètre `surface=web` indique explicitement que l’édition complète reste dans la surface canonique actuelle. Il ne transporte aucune donnée utilisateur.

## Intégration

`NativeHomeHub` conserve exactement ses deux capacités historiques : `onOpenPath` et `onOpenSecurity`.

L’ouverture de Profil est un état local d’interface dans `NativeHomeHub`. Les autres destinations continuent d’emprunter `onOpenPath`, donc le même `navigate()` du shell mobile et ses gardes existantes.

## Principe

**L’HUMAIN AVANT TOUT. Protéger sans surveiller.**

La migration native améliore d’abord l’expérience visible. Les données privées restent dans leurs frontières serveur tant qu’une migration équivalente, testée et justifiée n’existe pas.
