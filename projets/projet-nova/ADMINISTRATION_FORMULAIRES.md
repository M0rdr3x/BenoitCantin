# Administration des formulaires — état actuel

## Statut public

Les formulaires externes historiques de Projet Nova sont **désactivés**. Les pages publiques actives de contact, participation et propositions utilisent actuellement un **contact direct par courriel** et ne soumettent pas de données à Formspree.

Le courriel public affiché par Projet Nova est `officiellenovaparti@gmail.com`.

## Parcours publics actuels

- Contact : `contact.html`
- Participation : `recrutement.html`
- Propositions citoyennes : `propositions.html`
- Ancien formulaire de soutien : redirection vers `recrutement.html`
- Ancienne page de confirmation : avis de retrait du parcours; elle ne confirme aucun envoi actuel.

## Réactivation future d’un fournisseur de formulaire

Avant toute réactivation d’un service externe de formulaire, il faut documenter et valider au minimum :

1. la finalité et la nécessité des renseignements demandés;
2. la minimisation des champs;
3. la destination administrative et les contrôles d’accès;
4. la localisation du traitement et les transferts hors Québec;
5. la durée de conservation et la destruction;
6. les mentions de confidentialité et le consentement approprié;
7. les protections particulières applicables aux renseignements sensibles ou à la participation politique;
8. la configuration distincte des autres projets du portail.

Aucun endpoint Formspree ne doit être copié dans une page publique avant cette validation.

## Sécurité

- Utiliser des comptes administratifs protégés par MFA.
- Ne jamais publier de réponses, pièces jointes ou exports privés dans GitHub.
- Ne pas intégrer une adresse administrative privée dans le code ou la documentation publique lorsque le courriel public du projet suffit.
- Documenter la suppression et la conservation exceptionnelle lorsqu’elles s’appliquent.
