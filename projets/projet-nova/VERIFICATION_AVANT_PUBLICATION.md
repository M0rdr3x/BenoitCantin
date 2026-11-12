# Projet Nova — Contrôle avant publication (P50G)

**Procédure préparatoire, aucun GO accordé.** Identité active : Projet Nova. « Parti Nova » reste une appellation future conditionnelle.

## Verrous constants
- [x] Les formulaires externes demeurent suspendus. Ne pas réactiver Formspree, ni une autre collecte, ni un paiement, ni une adhésion.
- [x] La participation annoncée est volontaire par courriel, sans donnée sensible exigée.
- [x] **NE PAS FUSIONNER la PR 640** (branche d'intégration uniquement).
- [x] Les essais de CI ou de code source ne prouvent pas le déploiement.

## Contrôles obligatoires, actuellement NON VALIDÉS
- [ ] Obtenir les revues indépendantes, datées, des PR 636 et 638 sur les SHA finaux.
- [ ] Vérifier le mandat du mainteneur, de l'opérateur et de la personne autorisant la publication.
- [ ] Soumettre les flux réels de la boîte courriel et de tout prestataire à une revue de confidentialité : finalité, consentement, rétention, suppression, accès, sécurité et traitement hors Québec.
- [ ] Obtenir une validation juridique du statut du porteur et du régime électoral applicable. Aucune habilitation ne découle du site.
- [ ] Contrôler les six pages : participer, avis-legal, code-conduite, recrutement, contact, confidentialite.
- [ ] Écarter toute balise de formulaire, appel à une collecte externe, lien de paiement, ou promesse d'adhésion officielle non autorisée.
- [ ] Établir le SHA de sauvegarde, une procédure de restauration et un plan de retour arrière.
- [ ] Exercer le retour arrière dans un environnement isolé, puis faire évaluer ce résultat par l'opérateur habilité.
- [ ] Obtenir **une autorisation humaine explicite**, sur un périmètre et une version de code précis.

## Après une décision GO EXPLICITE, jamais par ce fichier
1. Relever à nouveau les SHA, les revues, les conflits et la CI.
2. Intégrer les PR 636 et 638 séparément si nécessaire, sous l'autorité du mainteneur habilité. Ne pas fusionner la PR 640.
3. Après déploiement réellement confirmé, contrôler les six URL HTTPS à partir des réponses HTTP brutes; documenter codes, redirections, empreintes, textes, formulaires, liens de paiement et cache.
4. Si une preuve manque ou si un écart persiste : arrêter, appliquer la procédure de retour arrière autorisée, et consigner l'incident.
5. Faire clore la recette par les responsables, pas par une CI.

Ce document remplace l'ancienne consigne « Configurer Formspree ». Il ne transfère aucun pouvoir légal ni ne lève les blocages institutionnels antérieurs.

## Références
- [P50G — Procédure détaillée](controles/P50G_PROTOCOLE_PUBLICATION_ET_RETOUR_ARRIERE.md)
- [Élections Québec : autorisation](https://www.electionsquebec.qc.ca/comprendre/comprendre-le-financement-politique/obtenir-une-autorisation/)
- [Québec : outils en protection des renseignements](https://www.quebec.ca/gouvernement/travailler-gouvernement/normes-gouvernance-pratiques-internes/protection-des-renseignements-personnels/outils)
