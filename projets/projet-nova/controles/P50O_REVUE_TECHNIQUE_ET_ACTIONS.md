# Projet Nova — P50O : revue technique des PR 636 et 638, contre-exemples et actions

**14 octobre 2026 · Constat de code uniquement · Avis technique préparatoire NON INDÉPENDANT · NO_GO publication.**

## 1. Conclusion vérifiable

La **PR 652 (P50M) existe** et est bien un brouillon non fusionné. Les PR 636 et 638 restent également des brouillons non fusionnés. La PR 640 demeure une **branche de validation : NE PAS FUSIONNER**.

Le correctif de participation (PR 636) remplace les mentions périmées dans `participer.html` et `avis-legal.html` et ajoute un validateur Python (`scripts/validate_nova_publication_p50b.py`). Les changements éditoriaux sont ciblés et leur correspondance de blobs dans la PR 640 a été vérifiée à P50N. Le nouveau validateur traite correctement plusieurs cas simples mais n'examine qu'une liste restreinte de mécanismes.

La PR 638 harmonise la dénomination et rend la présentation de `code-conduite.html` et `official/reference/statuts.md` explicitement provisoire. Elle actualise `data/sources.json` et ajoute un garde-fou de dénomination. Le SHA-256 des statuts, tel que vérifié par le contrôle P50N, a été cohérent sur les commits figés.

**Aucune de ces observations ne prouve une publication réelle ou une autorisation juridique.**

## 2. Problèmes de PR 636 à traiter avant approbation

| Code | Sévérité | Constat sur le validateur candidat | Action minimale recommandée |
| --- | --- | --- | --- |
| F01 | Haute | Un lien vers **Google Forms** (`forms.gle`) n'est pas dans les détecteurs | Analyser les URL `href`, `src`, `action` et leurs hôtes, pas seulement Formspree/Formsubmit |
| F02 | Haute | Un iframe `docs.google.com/forms` n'est pas reconnu | Inclure les embeds de formulaires et les URI de fournisseur selon une politique de sorties autorisées |
| F03 | Haute | Un lien Typeform n'est pas reconnu | Ajouter un test de refus spécifique avec un formulaire externe fictif |
| F04 | Haute | Un lien Jotform n'est pas reconnu | Étendre les tests et les règles de contrôle, sans présumer que la liste est exhaustive |
| F05 | Haute | Un lien **Stripe Checkout** n'est pas bloqué | Bloquer les chemins d'activation de paiement dans le périmètre des pages de participation |
| F06 | Haute | Un lien de **don PayPal** n'est pas bloqué | Ajouter un contrôle de paiement et de collecte financière |
| F07 | Moyenne | Une chaîne `mailto:` dans un commentaire HTML peut satisfaire la vérification sans lien cliquable | Vérifier la présence d'une vraie ancre `<a href="mailto:...">` par analyse HTML |
| F08 | Moyenne | Un script contenant un lien de formulaire externe non reconnu peut passer | Rechercher les URLs dans les scripts statiques et imposer une revue manuelle pour la logique dynamique |

**Important : ces problèmes sont des angles morts du test, pas des preuves qu'un paiement ou un formulaire externe est actuellement actif dans les pages candidates.** Les trois contrôles positifs C01–C03 doivent également réussir : balise `form`, Formspree explicite et ancien lien vers le PDF de soutien.

Le diagnostiqueur `scripts/diagnostic_nova_pr636_p50o.py` exécute **11 sondes fictives** sur le validateur de la PR 636 à son SHA `6cd38faf1124a9bcbb2be1beaa12bcd14a85f9fb`. Un succès CI du diagnostiqueur signifie seulement que le protocole d'examen s'est exécuté. La CI affiche un avertissement lorsque des angles morts sont reproduits; elle ne valide **jamais** la sûreté de la PR 636.

### Décision de traitement proposée pour PR 636
- Préparer sur la branche de la PR 636 une modification du validateur, **après** examen du mainteneur réellement habilité.
- Ajouter les huit contre-exemples comme tests de régression, et quelques tests de non-détection sur pages propres.
- Revoir les textes des deux pages, le lien de participation et le document historique vers lequel renvoyait autrefois le bouton.
- Actualiser les SHA et soumettre la version finale à une revue technique indépendante, une revue des informations juridiques publiées et un plan de retour arrière avant tout GO.

## 3. PR 638 : constat et points de revue distincts

| Code | État | Objet de contrôle |
| --- | --- | --- |
| I01 | Correctif apparent | `code-conduite.html` et ses métadonnées disent **Projet Nova**, et présentent les règles comme proposées |
| I02 | Contrôle technique antérieur réussi | Le manifeste SHA-256 doit toujours correspondre à `official/reference/statuts.md` après le dernier changement, et être vérifié à nouveau si SHA modifié |
| I03 | Revue humaine à obtenir | Le contenu des projets de statuts, des organes et du CTA « Lire les Statuts et la gouvernance » doit indiquer sans équivoque le caractère **non adopté** |
| I04 | Sécurité CI à apprécier | La configuration nouvelle `nova-identite.yml` doit faire l'objet d'une revue des permissions, de la persistance des credentials et des actions utilisées |
| I05 | Revue humaine à obtenir | Le scanner d'ancienne dénomination ne vérifie que des formats de fichiers textuels ; il ne prouve ni absence de traces anciennes dans les PDF/images ni statut électoral |

Aucune approbation humaine du contenu, des pouvoirs ou de l'identité juridique n'a été constatée. Le correctif proposé ne justifie pas de demander seul l'inscription électorale, de recevoir des contributions ou de déclarer le futur Parti Nova déjà constitué.

## 4. État exact du document de soutien historique

Sur `main`, `formulaire-soutien.html` est une **redirection** vers `recrutement.html` et annonce que l'ancien formulaire n'est plus utilisé. Les inventaires `assets/documents.js` et `documents.json` consultés ne listent pas l'identifiant `formulaire-soutien`. Ce constat est **limité au code consulté** : il ne certifie pas l'impossibilité d'accès à un ancien PDF par URL directe, cache, index, autre fichier historique ou hébergeur.

## 5. Porte de sortie P50O

**GO publication impossible** sans l'ensemble des éléments suivants :
1. Tous les défauts haute sévérité F01–F06 sont corrigés ou bloqués par un contrôle équivalent explicitement justifié et testé.
2. Les défauts moyens F07–F08 sont traités, ou une réduction de risque compensatoire est vérifiée et signée.
3. Tests sur les **SHA finaux** des PR 636/638, revues indépendantes et analyse des écarts résiduels.
4. Revue juridique ciblée sur les informations publiques, qualification du porteur, mandats réels et confidentialité du contact courriel.
5. Sauvegarde et plan de restauration testés par l'opérateur habilité.
6. Décision écrite de la personne habilitée, limitée à des SHA déterminés.
7. Publication autorisée, puis recette HTTP du contenu réel, des flux et des liens, avec clôture indépendante.
8. **PR 640 : ne jamais fusionner dans ce plan.**

Aucune dérogation implicite n'est créée par une CI verte ou par une note rédigée par l'assistant. En l'absence d'une seule preuve requise, état **NO_GO**.

## 6. Stratégie de progression réelle

La suite ne doit pas créer une série supplémentaire de dossiers de plus en plus abstraits. Les deux priorités réellement utiles sont **(a) corriger la couverture du validateur de la PR 636, (b) obtenir une revue indépendante vérifiable des PR 636 et 638**. L'exécution de ces deux tâches nécessite une personne autorisée à intervenir sur les PR cibles; le présent jalon n'usurpe pas sa fonction.

Les documents P50F–P50N, V3.40 et les blocages juridiques/financiers précédents sont préservés. Toutes les contributions, signatures, adhésions et nouvelles collectes demeurent suspendues.
