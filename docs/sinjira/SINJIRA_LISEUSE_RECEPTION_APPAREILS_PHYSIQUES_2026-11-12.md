# SINJIRA™ — Réception de la liseuse sur appareils physiques

**12 novembre 2026 — protocole à exécuter, aucun essai physique déclaré comme réalisé.**

## Décision de lancement

**Statut : NON VALIDÉ / NO_GO.** La [PR #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000) contient la liseuse mobile tactile V52–V67, mais le succès de Chromium/WebKit Playwright ne démontre pas à lui seul le comportement d'un véritable écran tactile, des lecteurs d'écran, du cache navigateur ou des contrôles d'accès au PDF privé. Cette fiche prépare la **réception manuelle reproductible** sans attribuer fictivement une réussite.

## Préparation et précautions

1. Tester une URL de préproduction issue **du commit exact de la PR #1000**, jamais une version locale non identifiée. Noter le SHA Git et l'environnement de test dans le procès-verbal.
2. Utiliser d'abord **une œuvre entièrement fictive / autorisée** suffisamment longue, avec de petits paragraphes, un grand paragraphe, des titres et une image; **aucun roman privé de client** dans les captures ou les journaux.
3. Pour les tests de droits, utiliser seulement **des comptes de laboratoire autorisés**, un compte sans achat et un compte détenteur de droit fictif. Les tests de révocation serveur ne sont autorisés qu'après revue et application contrôlée de la politique V51/V59; **ne pas déployer le SQL candidate par ce protocole**.
4. Ne jamais enregistrer de jeton, URL signée, courriel personnel, numéro de compte ou texte intégral dans un rapport public.

## Matrice minimale : vrais appareils

| Identifiant | Appareil / navigateur | État |
|---|---|---|
| IOS-SMALL | iPhone de petite largeur, Safari iOS à jour | À exécuter |
| IOS-RECENT | iPhone récent, Safari iOS à jour | À exécuter |
| ANDROID-SMALL | Android 320–360 px CSS, Chrome à jour | À exécuter |
| ANDROID-RECENT | Android 390–440 px CSS, Chrome à jour | À exécuter |
| TABLET-IOS | iPad Safari, portrait et paysage | À exécuter |
| TABLET-ANDROID | Tablette Android Chrome, portrait et paysage | À exécuter |
| A11Y-IOS | VoiceOver iOS, lecture au toucher et au clavier si disponible | À exécuter |
| A11Y-ANDROID | TalkBack Android, lecture au toucher | À exécuter |

Noter les **versions exactes du système, du navigateur et du navigateur intégré**, ainsi que la largeur du viewport. Ne pas inventer de résultats si le matériel n'est pas disponible.

## Procédure et critères d'acceptation

Pour chaque appareil disponible :

1. **Démarrage** — ouvrir le livre de test en mode pages d'écran; vérifier que le texte reste dans le viewport sans barre de défilement horizontale. Les boutons de navigation font au minimum 44 px dans les formats testés.
2. **Un geste = un écran** — balayer **vers la gauche** au centre : une seule portion de texte avance, sans perdre ni répéter une ligne entière. Balayer **vers la droite** : revenir au passage précédent. Faire 20 aller-retour sur de courts et longs paragraphes; noter tout double saut.
3. **Fin de page source** — parcourir une page PDF extraite jusqu'à la fin : le geste suivant avance à la page source suivante; revenir tout de suite avec un geste droit restitue la dernière portion de la page précédente.
4. **Défilement naturel et annulation** — réaliser un défilement vertical, une diagonale, une sélection, un appui long et un zoom multi-doigts : aucun ne doit déclencher un changement involontaire de page.
5. **Geste système** — commencer un mouvement de retour dans les 24 px CSS depuis les bords : la liseuse ne doit pas le capter. Vérifier séparément que le navigateur ou le système exécute ses propres gestes selon l'appareil. Répéter après orientation.
6. **Rotation et typographie** — au milieu du livre, augmenter la police jusqu'à 34 px, modifier l'interligne à 2,1 et tourner portrait/paysage : vérifier la lisibilité, l'absence de texte masqué et le maintien du passage actuellement lu.
7. **Reprise** — fermer et rouvrir la lecture de test : retrouver le numéro de page source PDF et la position locale. Recommencer après bascule de mode PDF/texte libre.
8. **Accessibilité** — tester les boutons au clavier (Tab, Enter, flèches **uniquement lorsque le livre a le focus**) et les annonces « écran X sur Y », page source, précédent/suivant avec VoiceOver ou TalkBack. Vérifier que le focus est visible et qu'aucune annonce n'est répétée en boucle.
9. **Performance et stabilité** — feuilleter durant 15 minutes : pas de page blanche persistante, de plantage du navigateur, de boucle de défilement ou de ralentissement bloquant. Réduire la vitesse réseau, verrouiller/déverrouiller puis reprendre.
10. **Sécurité privée** — seulement lorsque la chaîne d'autorisations serveur a été homologuée : vérifier le refus d'accès sans droit, la révocation, les fichiers cache et la synchronisation entre deux appareils. Le lecteur ne doit pas conserver un URL signé utilisable après révocation.

## Feuille de résultats à renseigner

| ID test | Version OS / navigateur | SHA candidat | Scénarios 1–10 (PASS/FAIL/ND) | Défaut + étapes | Réviseur + date |
|---|---|---|---|---|---|
| IOS-SMALL | Non renseigné | Non renseigné | ND | Non renseigné | Non renseigné |
| IOS-RECENT | Non renseigné | Non renseigné | ND | Non renseigné | Non renseigné |
| ANDROID-SMALL | Non renseigné | Non renseigné | ND | Non renseigné | Non renseigné |
| ANDROID-RECENT | Non renseigné | Non renseigné | ND | Non renseigné | Non renseigné |
| TABLET-IOS | Non renseigné | Non renseigné | ND | Non renseigné | Non renseigné |
| TABLET-ANDROID | Non renseigné | Non renseigné | ND | Non renseigné | Non renseigné |
| A11Y-IOS | Non renseigné | Non renseigné | ND | Non renseigné | Non renseigné |
| A11Y-ANDROID | Non renseigné | Non renseigné | ND | Non renseigné | Non renseigné |

**Règle :** une ligne non renseignée reste **ND** (non démontrée) et non PASS. En cas de défaut bloquant, associer les étapes exactes et une capture expurgée au ticket GitHub; ne pas marquer comme terminé.

## Portes de publication

- [ ] CI complète verte sur le SHA final après synchronisation avec `main`.
- [ ] Revue du différentiel des moteurs V26/V28/V52/V53.
- [ ] Matrice d'appareils physiques couverte, avec preuve de résultat et décision.
- [ ] Revue indépendante de l'accessibilité tactile et des lecteurs d'écran.
- [ ] Droits et révocation des romans privés prouvés côté serveur, sans migrer le candidat SQL par inadvertance.
- [ ] Synchronisation réelle entre deux appareils, hors ligne et après conflits, testée.
- [ ] Responsable de publication et plan de retour arrière approuvés.

**Tant que les cases restent ouvertes, aucune déclaration « terminé », aucune augmentation mécanique du 66,5 % global et aucune date de lancement certifiée.** Source historique : [bilan de référence des quatre programmes](https://github.com/M0rdr3x/BenoitCantin/blob/main/docs/AVANCEMENT_QUATRE_PROGRAMMES_2026-11-10.md).