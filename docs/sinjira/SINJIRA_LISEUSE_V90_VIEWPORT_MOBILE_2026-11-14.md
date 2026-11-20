# SINJIRA™ — V90 : garder le passage lorsque le navigateur mobile change sa hauteur visible

**14 novembre 2026 — candidat de la PR #1000; aucun déploiement ni fusion.**

## Problème visé

Safari sur iPhone et Chrome sur Android peuvent faire apparaître ou disparaître leurs barres d'interface pendant la lecture. Lorsque la hauteur `100dvh` change, le nombre de lignes visibles et les dimensions de la fenêtre de livre peuvent évoluer alors que le navigateur ne transmet pas forcément de `window.resize`. Un lecteur paginé ne doit pas perdre son passage à cause de cette variation de hauteur.

## Correction V90

- Écouter `window.visualViewport.resize` **lorsqu'il existe** et, uniquement en mode texte paginé sans zoom, reprendre la logique de restitution d'ancre V63/V69.
- **Ignorer** les événements quand `visualViewport.scale > 1.01` : le pincement pour agrandir et le déplacement natif du texte appartiennent au navigateur.
- Conserver les garanties V69/V85 : un geste tactile réel invalide toute restitution de géométrie différée en attente.
- Déconnecter le listener lors de la fermeture du lecteur. Aucun changement de données personnelles, livre privé, position serveur ou auth.

## Preuves de vérification

- **Tests Node :** notification du `visualViewport` seule, sans `window.resize`; conservation d'une proportion lisible après changement de hauteur; absence de restitution pendant un pincement; reprise après dézoom; priorité d'un swipe engagé; absence de listener résiduel.
- **Tests navigateur :** vraie page `compte/liseuse.html`, PDF synthétique, réseau Supabase et externe interdits, vérification sous Chromium et WebKit après variation CSS de hauteur de lecteur et émission explicite de l'événement `visualViewport.resize`. La position d'un caractère visible est vérifiée à moins de 35 px de sa hauteur relative.

**Limite de preuve :** l'événement est émis artificiellement en laboratoire; la variation des barres de navigateur système et les gestes simultanés doivent encore être testés sur des téléphones physiques Safari iOS et Chrome Android. Les droits d'accès au roman intégral, la synchronisation CAS et les 13 conditions de lancement restent **NO-GO**. Le score global SINJIRA ne change pas automatiquement (66,5 % ±10 points au 8 novembre).