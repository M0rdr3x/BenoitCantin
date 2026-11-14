# SINJIRA™ — V82 : récupération gracieuse après erreur d'extraction du texte PDF

**14 novembre 2026** — [PR intégrée de liseuse mobile #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), non fusionnée.

## Incident couvert

V81 montrait automatiquement le PDF pour une couverture sans texte, mais une page PDF dont `getTextContent()` rejetait la promesse (police/structure non prise en charge, scan mal formé) provoquait encore l'erreur globale « Impossible d'afficher cette page », malgré un `page.render()` potentiellement valide.

## Solution V82

- En mode texte, tenter l'extraction du PDF et la conversion en paragraphes; si l'extraction **échoue** ou ne produit aucun texte lisible, lancer le rendu canvas PDF de cette **page uniquement** sans changer le mode préféré.
- Maintenir le geste **gauche = suivante** et **droite = précédente**, puis reprendre automatiquement le texte sélectionnable et la pagination mobile sur les pages suivantes valides.
- Vérifier `renderVersion` après extraction, après erreur et après le rendu : aucune ancienne page ne doit réapparaître après navigation rapide.
- **Aucun contenu ni message d'erreur d'extraction contenant potentiellement des données privées dans les journaux** : l'erreur n'est pas imprimée. Une vraie erreur de rendu canvas conserve le traitement général d'erreur existant.
- Conserver le rôle `status` accessible et `aria-describedby` stable. Aucun changement Auth, RLS, SQL, sauvegarde, progression interappareils ou droit privé.

## Réception automatisée du vrai HTML

Le scénario `tests/e2e/test_sinjira_liseuse_extract_error_v82.py` charge la vraie page avec PDF **fictif** et **erreur `getTextContent()` injectée uniquement pour la page 4**. Sous Chromium et WebKit, confirmer :

1. page 3 : texte paginé et notification absente;
2. page 4 : PDF original visible, message `role=status`, aucune page d'erreur générale, préférence texte inchangée;
3. geste gauche : page 5 texte paginé normalement accessible;
4. retour page 4 puis geste droite : page 3 texte paginé, sans gel de la file de rendus;
5. aucune erreur JS inattendue ni connexion Supabase ou externe.

Workflow V69 : exécuter ces tests, la recette des pages illustrées V81, les 128 tests Node et les parcours Chromium/WebKit sur le **SHA V82 exact**. La validation est distincte d'un essai physique.

**Publication bloquée** par la réception iPhone Safari / Android Chrome, VoiceOver/TalkBack, les droits des romans privés et l'homologation de la reprise de lecture entre appareils. PR DRAFT / NO-GO; score SINJIRA complet **66,5 % ±10 points** estimé, 13 portes ouvertes.
