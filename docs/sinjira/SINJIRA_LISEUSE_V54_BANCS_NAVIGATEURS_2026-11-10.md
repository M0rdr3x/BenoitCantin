# SINJIRA™ — V54 : recette navigateur mobile isolée

**Statut : candidate de contrôle, 10 novembre 2026. Aucun déploiement, aucune fermeture de porte.**

Les PR [V52 #961](https://github.com/M0rdr3x/BenoitCantin/pull/961) et [V53 #964](https://github.com/M0rdr3x/BenoitCantin/pull/964) rendent la lecture au doigt et la pagination texte par écrans possibles en code, mais les **47 tests Node** précédents utilisaient des éléments DOM simulés. Pour un véritable lecteur de livre sur cellulaire, il est essentiel de tester les interactions dans des moteurs de navigateur réels.

## Ce que la V54 apporte

Une page de test **locale et synthétique** (`tests/e2e/fixtures/sinjira-liseuse-mobile-v54.html`) intègre les vrais modules de gestes et de pagination V52/V53. Le texte qui y apparaît est une série de lignes fictives, sans extrait de roman ni autre donnée privée. Le banc est démarré en HTTP local `127.0.0.1`, sur un port disponible, le temps du test.

Le parcours `tests/e2e/test_sinjira_liseuse_mobile_v54.py` utilise **Playwright** avec un contexte de **390 × 844 pixels**, activation tactile et moteurs **Chromium et WebKit**. Les événements TouchEvent sont synthétiques, mais les moteurs, règles DOM, CSS, événements capturés/bulle et interactions sont réels.

Le parcours vérifie : 
1. Glissement **gauche** avançant d'une portion d'écran **sans avancer la page PDF**;
2. Glissement **droite** reculant de cette portion; sélection et gestes verticaux non interceptés;
3. Passage à la page PDF suivante seulement quand le texte d'une page source est terminé — sans double saut;
4. Retour à la page précédente au **dernier écran** de son texte;
5. Contrôle aux flèches clavier, boutons tactiles et maintien de la progression locale;
6. Rotation portrait/paysage sans changer de page source involontairement;
7. Mode PDF : délégation aux gestes V52 sans **double changement** de page;
8. Possibilité de désactiver la pagination et de retrouver le défilement libre.

**Limitations à communiquer explicitement :** les tests exécutés sur serveur Linux avec moteur WebKit ne sont **pas** une preuve de bon fonctionnement sur un vrai iPhone ni d'accessibilité VoiceOver/TalkBack. Ils n'incluent pas l'édition intégrale, le téléchargement protégé, la synchronisation CAS V51, les déconnexions réelles, le cache PWA de production ni les performances sur appareils modestes.

## Architecture et sûreté

- Tests et fixture **uniquement**; aucune modification du code serveur, des rôles ou des droits Supabase.
- Playwright version figée, navigateur téléchargé en CI sans identifiants d'utilisateur ni secrets Supabase.
- Le lecteur de livre intégral demeure bloqué par les conditions de sécurité et de réception de [V51 #947](https://github.com/M0rdr3x/BenoitCantin/pull/947) et [issue de droits #955](https://github.com/M0rdr3x/BenoitCantin/issues/955).
- Cette V54 est proposée en PR **empilée sur V53**, elle-même empilée sur V52, puis `main`. Elle ne doit pas être fusionnée directement sans ses dépendances ni revue indépendante.
- Aucune mise à jour des pourcentages de référence : **SINJIRA 66,5 % ±10 points**, **13 conditions de lancement ouvertes**.

## Conditions de réception suivantes

Après un workflow vert pour Chromium et WebKit : essai **physique** iPhone/Safari, Android/Chrome, tablette et mode paysage; vérifications lecteurs d'écran et gestes d'accessibilité; longue lecture du PDF de 520 pages et surlignages; protection après déconnexion; synchronisation multiappareil V51 et mise à jour du service worker. La certification finale nécessite approbation humaine et preuve d'essais.
