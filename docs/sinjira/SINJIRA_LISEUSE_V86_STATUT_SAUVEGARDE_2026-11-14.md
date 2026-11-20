# SINJIRA™ — V86 : sauvegarde fiable et statut compréhensible sur la liseuse mobile

**Date : 14 novembre 2026 — candidat de la PR #1000, sans fusion ni déploiement.**

## Défaut observé dans le code

Au démarrage, le moteur affichait « Enregistrement automatique actif sur cet appareil » (et, pour le roman intégral, « sur votre compte ») avant toute écriture vérifiée. Un navigateur qui refuse `localStorage.setItem` pouvait donc présenter une confirmation trompeuse alors que la première sauvegarde échouait. Le texte d'aide promettait en outre qu'une sauvegarde après coupure réseau n'écraserait jamais une position plus récente d'un autre appareil; cette propriété n'est pas garantie par l'ancien `upsert` sans compare-and-swap atomique côté serveur (V51/V59 non homologués).

## Correctif

- Lors du chargement, afficher une **position reprise**, distincte de la **confirmation d'une nouvelle sauvegarde**, et annoncer explicitement que celle-ci sera vérifiée lors d'un changement de position.
- Conserver l'enregistrement automatique existant, la navigation tactile, les pages d'écran, le mode PDF, la restauration V85, les annotations et les réglages.
- Retirer des textes d'interface toute garantie prématurée de sauvegarde locale ou de synchronisation interappareils. L'utilisateur peut solliciter une vérification explicite avec « Enregistrer ma position ».
- Les garanties de synchronisation ne sont pas renforcées par un simple texte : **V32, CAS V51 et droits V59** doivent être revus et appliqués selon les contrôles de production autorisés; ne jamais attribuer une réussite sur la seule base de l'UI.

## Test de non-régression

Le scénario existant `tests/e2e/test_sinjira_liseuse_auto_resume_v85.py` a été prolongé :
1. Sur le **vrai HTML** avec PDF fictif et navigateur simulé, vérifier au démarrage qu'aucune sauvegarde nouvelle n'est encore déclarée confirmée.
2. Après balayage horizontal, vérifier l'enregistrement automatique de la page et de la position, puis la reprise sur rechargement.
3. Sur une deuxième session où `Storage.prototype.setItem` échoue, vérifier que l'interface ne présente **pas** de succès au démarrage, et qu'un changement de page annonce le refus du stockage.
4. Vérifier que l'aide ne prétend plus éliminer les conflits multiappareils.

Les scénarios s'exécutent dans la CI de la PR #1000 avec **Chromium et WebKit**, en bloquant les services externes et sans aucun compte, livre privé ni donnée Supabase réelle. Un résultat CI vert prouve seulement ces cas simulés.

## Critères de réception restant ouverts

- Safari sur iPhone physique, Chrome sur Android physique, TalkBack/VoiceOver et sélection de texte.
- Accès réellement autorisé au roman intégral, annulation après déconnexion et expiration de session.
- Lecture/sauvegarde/reprise réelle sur deux appareils avec la migration V32 et la protection serveur CAS V51/V59 effectivement approuvées.
- Vérification du cache PWA, de la version exacte des fichiers publiés, des risques de concurrence et revue indépendante.

**Décision : NO-GO production.** Les indicateurs de programme du 8 novembre restent : **66,5 % de maturité SINJIRA (±10 points)**, **13 portes de lancement ouvertes**, date de fin indéterminée. Aucun changement d'Auth, des RLS, de migration SQL, de paiement ou de contenu privé par V86.
