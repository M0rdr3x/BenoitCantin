# SINJIRA V134 — valider le vrai bouton Retour du navigateur

**16 novembre 2026 — ajout d'un essai de réception sur PR #1000 (DRAFT), sans déploiement.**

## Objectif

La V133 traite `pageshow.persisted` par un écouteur navigateur et restaure la position paginée. Les premiers tests injectaient cet événement : ils n'exerçaient pas la navigation réelle dans l'historique. La V134 ajoute une **vraie navigation aller / Retour** dans les moteurs Chromium et WebKit du laboratoire de CI.

## Parcours navigateur automatisé

1. Ouvrir la vraie page HTML de la liseuse sur un petit viewport mobile, avec un faux roman sur le serveur local et Supabase interdit.
2. Avancer à la position de lecture simulée d'environ 315 pixels, mémoriser la page source et le scroll et écouter le `pageshow` réel.
3. Naviguer vers la même page sous une autre URL de test, puis `page.go_back()` : il s'agit d'une navigation de navigateur, **pas d'un événement factice**.
4. Si le moteur restaure la page depuis BFCache (`pageshow.persisted === true`), vérifier que la page source n'a pas changé et que le scroll demeure proche de celui qui précédait la navigation, avec deux frames de réagencement.
5. Si le moteur choisit un rechargement complet, vérifier le réaffichage du roman fictif et déclarer explicitement **non observé pour BFCache** : un moteur ne doit pas être présenté comme testé en BFCache s'il l'a désactivé.
6. Dans les deux cas, contrôler un vrai cycle gauche → écran suivant, droite → écran précédent, et refuser les erreurs JS et accès réseau non autorisés.

## Portée

Le fichier de tests `tests/e2e/test_sinjira_liseuse_responsive_v58.py` exécute ce scénario dans les workflows de lecture mobile déjà présents. Aucun code d'authentification, livre protégé, migration, stockage personnel ou déploiement n'est modifié. La **réception sur appareils physiques** et les droits serveur des œuvres intégrales restent hors périmètre. Ne pas promouvoir PR #1000 hors DRAFT uniquement pour la réussite de la simulation navigateur.

**CI du nouveau SHA : à confirmer avant qualification**. Les scores Nova 47 %, boussole 75 %, sondage 54,5 % et SINJIRA 66,5 % ne changent pas automatiquement.
