# SINJIRA™ — V94 : protéger l'ouverture privée interrompue par la mise en arrière-plan

**14 novembre 2026.** Correctif candidat dans la PR #1000 (DRAFT). Aucun déploiement ou fusion.

## Problème reproduit

Pendant le chargement initial du roman intégral, le navigateur peut être masqué ou le téléphone verrouillé. Au moment de l'événement `visibilitychange(hidden)`, `state.pdf` est parfois encore `null`. Dans V93, la suspension ne positionnait `privatePaused` à `true` **que si le PDF existait déjà**. La promesse PDF pouvait ensuite se terminer, le code `init()` affichait le livre en arrière-plan, et la reprise n'effectuait aucune nouvelle vérification des droits.

L'enjeu concerne spécifiquement le **début du chargement**, en plus du retour BFCache et de l'interruption en cours de lecture déjà sécurisés dans V92/V93.

## Mesures V94

- Marquer la suspension de l'édition intégrale même avant l'arrivée de `state.pdf`. Garder le conteneur de lecture et la barre latérale masqués.
- Ajouter `privateReaderReady` : la vérification du retour ne doit pas montrer le livre avant l'achèvement de l'initialisation, y compris le rendu initial et les commandes.
- À la fin d'`init()`, si une suspension est en cours : ne **pas** lever `hidden`; déclencher la double vérification lorsque le document est redevenu visible, même si l'événement `visibilitychange(visible)` s'est produit pendant un `await`.
- Conserver le ratio choisi par `restorePage()` quand aucun repère BFCache n'existe parce que la suspension s'est produite avant le téléchargement.
- Réinitialiser `privateReaderReady` lors de la fermeture sécurisée.
- Conserver l'invalidation de génération, l'authentification `auth.getUser()` et l'autorisation serveur `get-novel-file-url` obligatoires de V93.

## Preuves automatisées exigées

Le test E2E dans `tests/e2e/test_sinjira_liseuse_auto_resume_v85.py` se sert d'un **faux roman intégral de 520 pages** et d'un faux client Supabase, sans réseau externe. Il retarde volontairement l'analyse du PDF jusqu'à ce que le navigateur soit simulé masqué. Il vérifie que :
1. Contenu et notes sont masqués lorsque le PDF est absent.
2. Le PDF peut finir de se charger en arrière-plan sans devenir visible, ni demander de nouveaux droits tant que l'onglet reste masqué.
3. Le droit de lecture peut être révoqué pendant cette attente.
4. Au retour au premier plan, le moteur vérifie le droit une nouvelle fois; la révocation empêche tout affichage et détruit les fragments chargés.
5. Les suites Chromium et WebKit déjà existantes valident les balayages gauche/droite, pages et retour, sauvegarde/reprise locale, zoom et paysage.

## Limites et décision

L'homologation en laboratoire n'est pas une validation sur un **vrai iPhone Safari**, un **Android Chrome**, un **vrai compte privé**, ni un test de sécurité de l'Edge Function. Les états visibles sont simulés et aucun contenu intégral privé n'est stocké, publié ou transféré.

**NO-GO production**, 13 conditions de lancement SINJIRA toujours ouvertes, travaux RLS/CAS séparés non fusionnés. Taux de référence au 8 novembre inchangés : Nova 47 %, Nova–Sinjira non calculable, sondage 54,5 %, boussole électorale 75 %, SINJIRA 66,5 % ±10 points. Aucun délai de livraison global garanti.