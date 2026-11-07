# Projet Nova — Contrôle de conformité préalable à l'ouverture du sondage

**Date :** 7 novembre 2026. **Statut :** revue documentaire préparatoire, **pas un avis juridique**, ni un certificat de conformité. Consultation **non ouverte** et aucun bulletin de test déposé en production.

## 1. Nature de l'outil

Le sondage `nova-consultation-v1` présente huit propositions issues de la boussole électorale. Le public volontaire de **18 ans et plus** s'auto-sélectionne; le projet **ne revendique aucune représentativité statistique**, aucune intention de vote et aucune vérification d'identité. Il ne conserve pas de bulletin individuel dans les tables de vote : chaque réponse est comptée par option et un jeton HMAC anti-rejeu distinct est conservé. Les services d'hébergement et d'anti-bot peuvent néanmoins traiter des métadonnées techniques.

**Important :** l'absence de nom, de courriel et de bulletin individuel ne prouve pas, à elle seule, l'absence de tout traitement de renseignements personnels au sens de la loi. Les opinions politiques sont potentiellement des renseignements personnels **sensibles**, selon leur contexte d'utilisation. L'âge est uniquement **déclaré**, non vérifié par une pièce d'identité.

## 2. Références officielles à considérer

1. **Commission d'accès à l'information du Québec (CAI), consentement des personnes dans le privé** : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/consentement-personnes-entreprises . La CAI décrit le consentement **manifeste, libre, éclairé, spécifique, temporaire, granulaire, compréhensible et distinct** et l'importance du **consentement exprès** pour un renseignement personnel sensible.
2. **Québec.ca, concepts de renseignements personnels sensibles** : https://www.quebec.ca/gouvernement/travailler-gouvernement/normes-gouvernance-pratiques-internes/protection-des-renseignements-personnels/definitions-concepts/concepts . Les **opinions politiques** figurent parmi les renseignements généralement considérés comme sensibles.
3. **CAI, obligations des partis politiques provinciaux** : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-pour-partis-politiques-provinciaux . Certaines règles particulières de la Loi électorale et de la Loi sur le privé s'appliquent aux partis autorisés, instances, députés et candidats; **Projet Nova n'est pas traité ici comme un parti officiellement autorisé**.
4. **Élections Québec, lignes directrices pour les médias, section « Sondages »** : https://www.electionsquebec.qc.ca/salle-de-presse/lignes-directrices-pour-les-medias/ . Les sondages ne sont pas interdits en période électorale, mais leurs coûts de réalisation/diffusion peuvent constituer des **dépenses électorales** selon le contexte, l'auteur de la commande et l'effet de la diffusion. Un examen par la personne responsable de la conformité électorale est nécessaire avant une future campagne.
5. **CAI, principaux changements de la Loi 25** : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/sujets-et-domaines-dinteret/principaux-changements-loi-25 . Cette page précise les exigences de finalité, de consentement et, selon les cas, d'évaluation relative à la vie privée.

## 3. Amélioration appliquée au formulaire

La case distincte `poll-agree` a été reformulée pour obtenir un accord **explicite** : la personne consent à la transmission de ses **réponses politiques** pour leur **comptabilisation** et, sous des conditions de confidentialité, la publication de **statistiques agrégées**. Un lien direct mène à `confidentialite.html` et le texte rappelle la non-représentativité.

Le formulaire indique désormais qu'**aucun choix n'est envoyé avant le clic sur « Envoyer mes réponses »** et que, puisque les réponses sont additionnées sans bulletin individuel, **il n'est pas possible de retirer un bulletin en particulier après réception**. La case d'âge `poll-adult` demeure distincte. Le bouton d'envoi continue d'exiger les deux cases et la vérification anti-robots.

### Risques persistants à trancher

- **Applicabilité légale et responsable du traitement** : confirmer la qualification juridique du projet, de l'exploitant du site, de la société ou de l'instance politique, et la personne responsable de la vie privée.
- **Chaîne de traitement** : préciser données de la requête, risques de journaux IP de Cloudflare/Supabase/hébergeur, durée de conservation, modalités d'accès et suppression des jetons anti-rejeu, sous-traitance et transferts éventuels hors Québec.
- **Droit de retrait** : documenter l'impossibilité technique de suppression d'un bulletin individualisé dès l'agrégation, sous réserve de l'analyse juridique des droits applicables.
- **Résultats publics** : revoir les seuils et la protection contre les attaques par comparaison de lots successifs, y compris un nombre faible de réponses par option et la possibilité de réidentification indirecte.
- **Sécurité** : test d'intégration isolé de Turnstile, contrôle HMAC anti-rejeu, limites de débit, concurrence/atomicité, fiabilité des résultats et absence de contournement du rôle `service_role`.
- **Intégrité électorale** : neutralité du libellé, caractère volontaire, séparation claire entre sondage et campagne, droit des dépenses électorales et conformité des messages de diffusion, suivant le contexte.
- **Éthique et méthode** : absence de validation indépendante « une personne, un vote », non-représentativité, méthodologie ouverte et justification de la pertinence des huit propositions.

## 4. Portes de décision

**À établir avant toute activation** : avis d'un responsable juridique qualifié, politique de confidentialité et conservation finalisées, données de sous-traitants vérifiées, test d'intrusion/anti-rejeu isolé et critères de publication, approbation explicite de la version et registre de décision. Les règles de consentement du formulaire ne remplacent **aucun** de ces contrôles.

L'Edge Function Supabase `nova-civic-poll` demeure en place avec ses conditions de fermeture par défaut. **Aucun changement aux secrets, aux drapeaux d'ouverture, aux privilèges RLS ou aux données de votes n'a été effectué** pendant ce contrôle.

**Verdict :** formulaire plus clair, sources officielles documentées; **homologation juridique non acquise**, consultation non ouverte. La boussole demeure un calcul local indépendant de ce sondage. Le score global de préparation du programme politique est **47/100**, distinct de cet outil.
