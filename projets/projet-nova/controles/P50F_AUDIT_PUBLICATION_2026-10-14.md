# Projet Nova — P50F : audit de publication (14 octobre 2026)

**État : NO_GO publication.** Compte rendu de lecture seule. Aucune fusion, aucun changement de page publique, aucune activation de formulaire, aucun mandat ni autorisation électorale attribué par ce document. Identité active : **Projet Nova**. « Parti Nova » est une appellation future conditionnelle.

## État GitHub revalidé

| PR | Changement | Fichiers | HEAD | Statut |
| --- | --- | ---: | --- | --- |
| [636](https://github.com/M0rdr3x/BenoitCantin/pull/636) | participation et avis légal | 5 | `6cd38faf1124a9bcbb2be1beaa12bcd14a85f9fb` | brouillon; non fusionnée; 0 revue |
| [638](https://github.com/M0rdr3x/BenoitCantin/pull/638) | identité Projet Nova | 9 | `e027b0ca130fe91b00e52d9e9fe2f1b301f4b47e` | brouillon; non fusionnée; 0 revue |
| [640](https://github.com/M0rdr3x/BenoitCantin/pull/640) | tests d'intégration uniquement | 14 | `332afe7d9d73390feb41b0deb588692f3c73d48d` | brouillon; **NE PAS FUSIONNER** |

Les vérifications ciblées CI constatées pour ces PR sont réussies, sans équivaloir à une preuve de déploiement.

## Lecture des pages publiques

Contrôle en lecture seule par extraction de contenu HTML public le 14 octobre 2026 (pas d'empreinte brute de réponse HTTP certifiée) :

1. `participer.html` : ancienne mention du « formulaire intégré de soutien et de préadhésion » encore présente; correctif attendu en PR 636.
2. `avis-legal.html` : ancienne description des formulaires servant à communiquer / manifester un intérêt; correctif attendu en PR 636.
3. `code-conduite.html` : ancien titre et formulation « Gouvernance du Parti Nova » encore présents; correctif attendu en PR 638.
4. `recrutement.html` : texte de participation par contact volontaire direct, sans dossier inutile, constaté.

Ces différences correspondent aux fichiers actuellement sur `main`; les versions correctives consultées dans les branches 636 et 638 contiennent les formulations attendues. **Trois écarts publics restent ouverts.**

## Conditions impératives d'une mise en ligne future

- Revue humaine consignée pour les deux PR éditoriales, incluant une vérification de confidentialité.
- Responsable de publication dûment habilité, décision documentée et retour arrière préparé.
- Fusion distincte et autorisée de PR 636 et PR 638 seulement; **la PR 640 demeure strictement un outil de recette, sans fusion**.
- Validation CI sur le nouveau SHA de `main` et audit HTTP réel des quatre pages après déploiement, avec URL finale, réponses HTTP, SHA-256 du contenu et contrôles des formulaires/embeds/liens de paiement.
- Si toute porte reste ouverte, ou si une preuve manque : **NO_GO**.

## Portes institutionnelles indépendantes

Le jalon P50F ne modifie pas les statuts transmis : V3.40 figée; P2-C0-49 EN_COURS; W0 NON_CLOTUREE; W1 NO_GO; W2 à W4 NON_AUTORISEES; E26 0/20; pouvoirs 0/14; pièces financières 0/16; 14/14 portes financières bloquantes. Les demandes financières non autorisées restent non envoyées.

## Suite

**P50G** : revue indépendante / habilitations / confidentialité / critères de décision et test du retour arrière. Le dossier P50F complet de travail (note, registres CSV, vérificateur et 14 tests locaux) est conservé séparément dans le complément documentaire remis à l'utilisateur. Son contenu n'est ni une attestation de conformité juridique ni un justificatif de publication.
