# SINJIRA™ — V85 : sauvegarde et reprise automatiques fiables sur téléphone

**14 novembre 2026** — [PR #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), **DRAFT / non fusionnée / non déployée**.

## Défaut et objectif

SINJIRA conserve déjà la page et le ratio local de défilement dans `localStorage` et sauvegarde automatiquement les changements de page ou de portion d'écran. Pourtant, `changePage()` affichait toujours « Page mémorisée automatiquement » après `persist()`, **même lorsque le navigateur avait refusé toute écriture** (navigation privée, restrictions de stockage). Il est important de ne pas tromper la personne qui veut pouvoir reprendre son livre là où elle l'a quitté.

## Correction V85

- Conserver le changement de page et les gestes mobiles gauche/suivant et droite/précédent, y compris les transitions texte paginé ↔ illustration PDF.
- Utiliser le **résultat réel de `persist()`** pour annoncer une sauvegarde locale réussie. En cas de refus, afficher un avertissement sans prétendre que la page est enregistrée.
- Pour le roman intégral, ne **pas** annoncer une synchronisation serveur réussie de manière anticipée; préciser seulement qu'elle sera tentée quand elle est applicable. L'état réel du compte reste vérifié séparément.
- Ne modifier ni le contenu des livres, ni Supabase/Auth/RLS, ni les clés de stockage et la progression existante.

## Recette V85 sur la vraie page avec PDF fictif

Le scénario `tests/e2e/test_sinjira_liseuse_auto_resume_v85.py` est ajouté au workflow V69 sous **Chromium et WebKit** :

1. Charger le texte de démonstration en page 3, avancer **par un geste gauche** et vérifier sans bouton manuel que la position exacte (ratio de défilement) est automatiquement sauvegardée.
2. Recharger la vraie page HTML : elle doit rouvrir **la page 3 au même emplacement**, à une tolérance de ±0,12.
3. Passer à une page 4 **illustrée**, glisser vers la gauche jusqu'à la page 5 en texte adaptable, recharger et vérifier que la page 5 est récupérée.
4. Dans un second navigateur de test, refuser toutes les écritures `localStorage`, tourner quand même le livre, vérifier l'avertissement de non-sauvegarde et l'absence de fausse confirmation de réussite.
5. Confirmer aucune erreur JS et aucune requête vers un compte, roman réel ou Supabase. La simulation de stockage refusé concerne uniquement la démo fictive.

**Important :** la réussite de ces tests n'atteste **pas** la synchronisation réelle de l'emplacement du roman intégral entre deux appareils. Le déploiement exige aussi la migration V32 autorisée, la revue des droits et l'essai physique Safari iPhone / Chrome Android, VoiceOver/TalkBack et les critères de lancement.

**Statut : NO-GO**, SINJIRA programme complet **66,5 % estimés ±10 points** et **13 portes de lancement ouvertes**, date finale inconnue.

## Correction V85 de concurrence découverte en CI

La première exécution du nouveau test a révélé un risque de **restitution asynchrone** : une personne peut glisser dès que le texte apparaît, alors que les deux `requestAnimationFrame` de restitution initiale n'ont pas encore fini. Le gestionnaire de `scroll` pouvait ignorer ce geste (`restoringScroll=true`), et une restitution ancienne pouvait ensuite ramener le livre à sa position précédente.

**Réparation :** V53 signale explicitement les tours d'écran initiés par l'utilisateur à V26 via un événement DOM local, sans données ni contenu du livre. V26 invalide les rAF de restitution périmés, retire le verrou, calcule le ratio réellement atteint et le sauvegarde sans attendre le défilement asynchrone. L'événement n'est pas envoyé par les restaurations de mise en page automatiques. La transition vers la dernière portion de la page PDF précédente est également traitée comme un tour demandé.

Les tests de la branche doivent être **relancés sur le SHA contenant cette réparation**, et non crédités comme réussis avec les anciens commits V85. Ceci reste une validation du laboratoire et non une preuve de synchronisation serveur en production.
