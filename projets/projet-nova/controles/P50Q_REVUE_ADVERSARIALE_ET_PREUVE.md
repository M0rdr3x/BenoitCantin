# Projet Nova — P50Q : validation adversariale de la seconde correction

**16 octobre 2026 · Dossier de décision technique · Projet Nova · NO_GO pour toute fusion publique et collecte**

## 1. Chaîne de traçabilité

- `main` avant P50Q : `9ed5f70cbe7022f25a679346a1288701f3b09067`.
- PR 636 : correction éditoriale des anciennes annonces de formulaires, non fusionnée; SHA `6cd38faf1124a9bcbb2be1beaa12bcd14a85f9fb`.
- PR 638 : cohérence de l'identité Projet Nova et des statuts proposés, non fusionnée; SHA `e027b0ca130fe91b00e52d9e9fe2f1b301f4b47e`.
- PR 640 : validation d'intégration uniquement. **NE PAS FUSIONNER**. SHA `332afe7d9d73390feb41b0deb588692f3c73d48d`.
- PR 655 : premier correctif du validateur PR636 — **26 tests réellement réussis** en P50P; SHA `8541f761be8dbabda0c3f024f8969562ab816bc7`.
- PR 656 : preuve d'exécution P50P en CI au [run 38811861854](https://github.com/M0rdr3x/BenoitCantin/actions/runs/38811861854), démontrant sur 11 sondes anciennes **8 → 0** défauts de détection, cinq pages candidates conformes dans la copie source. Cette réussite ne donne pas de GO.
- PR 657 : **seconde correction P50Q**, base **branche PR655** et non `main`; SHA `0db5589f2129723eb3f046cc2e147179675ac7bd`, deux fichiers modifiés (validateur et tests).

La suite P50Q doit exécuter les 26 tests originaux et les **40 tests du code révisé**, puis comparer les mêmes 14 sondes sur les deux versions. Les résultats techniques et leur horodatage doivent être recueillis dans les logs de la CI de la PR de contrôle. **Ne jamais décrire comme réussi un test non exécuté.**

## 2. Périmètre exact de P50Q : 14 sondes additionnelles

| ID | Type | Scénario ciblé |
| --- | --- | --- |
| U01 | Blocage attendu | `//forms.gle/` sans schéma |
| U02 | Blocage attendu | `//checkout.stripe.com/` sans schéma |
| U03 | Blocage attendu | URL Google Forms encodée dans le paramètre d'une redirection |
| U04 | Blocage attendu | URL doublement encodée dans le paramètre d'une redirection |
| U05 | Blocage attendu | Séquences JS `\/ ` dissimulant un domaine de formulaire |
| U06 | Blocage attendu | URL historique `paypal.com/cgi-bin/webscr?cmd=_donations` |
| U07 | Blocage attendu | URL `paypal.com/paypalme/` |
| U08 | Blocage attendu | Seul `mailto:` à l'intérieur d'un élément `template` |
| U09 | Blocage attendu | Seul `mailto:` masqué par l'attribut HTML `hidden` |
| U10 | Blocage attendu | Seul `mailto:` masqué par `aria-hidden=true` |
| U11 | Blocage attendu | Seul `mailto:` directement masqué par `display:none` |
| N01 | Autorisé en contrôle | Domaine qui ressemble à `forms.gle` mais appartient à un autre hôte |
| N02 | Autorisé en contrôle | Lien institutionnel externe neutre, sans schéma |
| N03 | Autorisé en contrôle | Page PayPal informative sans demande de paiement |

Aucune URL ne contient de véritable référence de paiement ou de demande de renseignements. Ces scénarios synthétiques ont pour seul objet de mesurer la détection du validateur. **Une simple comparaison d'URL ne prouve pas qu'un fournisseur fonctionne ou que le site est en ligne.**

## 3. Critères d'acceptation technique P50Q

1. Les 5 tests du comparateur propre à P50Q doivent réussir.
2. Les **26 tests P50P** du validateur PR 655 doivent réussir sur le SHA fixé.
3. Les **40 tests P50Q** du validateur PR 657 doivent réussir sur son SHA fixé.
4. Le validateur PR 657 doit réussir l'inspection source de `participer.html`, `avis-legal.html`, `recrutement.html`, `confidentialite.html` et `contact.html` **sans modification ni déploiement**.
5. Les 14 sondes doivent donner **11 écarts avant et 0 après**, dont trois liens neutres toujours acceptés.
6. Le compte rendu doit annoncer `NO_GO_AUTOMATIQUE`; CI au vert signifie contrôle reproductible, et non approbation.
7. Tout nouveau commit modifiant ces fichiers nécessite un autre passage de CI; aucun contrôle passé n'est réputé valide sur des octets modifiés.

## 4. Limites de la deuxième correction

Le scanner HTML :
- ne télécharge pas et n'exécute pas le JavaScript externe, ne lit pas les données serveur;
- ne peut pas connaître les redirections réellement appliquées ou les services configurés;
- ne remplace pas un contrôle de sécurité applicative, une politique CSP ou l'analyse du code complet;
- ne garantit pas l'exhaustivité de la liste des moyens de paiement et de formulaires;
- n'atteste ni les pratiques d'hébergement, de messagerie, de confidentialité ou de conservation.

La reconnaissance de certains liens dissimulés et du `mailto:` masqué diminue des faux négatifs **dans les 14 sondes**, sans prétendre rendre impossible toute forme de contournement.

## 5. Décision de gouvernance et prochaines actions

**Maintenir NO_GO pour la publication.** À ce jour, les PR 636, 638, 655 et 656 n'ont pas de revue GitHub formelle observée; les mandats juridiques et institutionnels restent non attestés.

Étapes à suivre :
- Faire exécuter et consigner les contrôles P50Q, puis reporter les résultats dans les conversations PR 655 et 657.
- Réviser indépendamment le code du correctif P50Q; vérifier les faux positifs sur les pages réelles, les bibliothèques et les limites du scanner.
- Si autorisé, traiter d'abord l'intégration **PR 657 → PR 655**, puis seulement ensuite **PR 655 → branche PR 636**, avec réexécution et nouveaux SHA.
- Ne fusionner **aucune** PR dans `main` avant mandat, revue humaine, avis légal/PRP appropriés, plan de rollback, examen des conséquences et décision distincte.
- PR 638 suit une piste d'approbation distincte. PR **640 : NE PAS FUSIONNER**.
- Les tests HTTP et la recette de production ne pourront constituer une clôture qu'**après** une publication légitimement autorisée.

**V3.40, P2-C0-49, W0/W1/W2–W4, E26, pouvoirs, preuves financières et quatorze portes financières bloquantes : inchangés.** Aucune contribution politique, collecte de signatures, demande d'adhésion, paiement ou nouveau formulaire n'est activé.

*Document de vérification technique préparatoire, non avis juridique et non autorisation.*
