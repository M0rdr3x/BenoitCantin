# SINJIRA™ — Héritage numérique V24.5.2

**Statut : complément opérationnel du Cahier maître SINJIRA™.**  
**Principe supérieur : l’humain passe avant tout.**

Ce document transforme les principes du `CAHIER_MAITRE_SINJIRA.md` en contrat technique pour l’Histoire de vie et l’héritage numérique. En cas de conflit, le Cahier maître prévaut.

## 1. Frontière fondamentale

Le **Registre des Consciences n’est pas un héritage** et ne devient pas accessible aux proches après le décès.

Le pipeline posthume travaille exclusivement avec l’**Histoire de vie** et applique la frontière serveur :

- `source_boundary = life_story_only`;
- `registry_access_prohibited = true`.

Le générateur de PDF ne doit pas interroger les tables ou services du Registre, les personnages, les conversations privées de l’IA personnelle ou une autre source intime non explicitement autorisée.

## 2. Consentement avant le décès

Tout élément d’Histoire de vie est privé par défaut.

Pour devenir utilisable dans une œuvre posthume, il doit :

1. avoir été explicitement approuvé par la personne;
2. avoir `posthumous_disclosure = selected_versions`;
3. avoir une date d’approbation utilisateur;
4. être explicitement associé à une version choisie.

Une version doit être marquée prête par la personne et avoir au moins un destinataire actif pour être exportable.

La directive posthume globale doit également être activée. Aucune donnée historique ou ancienne directive ne vaut consentement implicite.

## 3. Signalement d’un décès

SINJIRA n’ouvre pas d’annuaire privé permettant de rechercher les comptes des personnes.

Une personne peut volontairement créer jusqu’à cinq **codes privés de signalement** et en remettre un à un proche de confiance.

Un code :

- contient 256 bits aléatoires;
- est présenté sous forme hexadécimale de 64 caractères;
- n’est affiché en clair qu’au moment de sa création;
- n’est jamais conservé en clair;
- est représenté en base uniquement par son SHA-256;
- peut être révoqué;
- devient inutilisable après un signalement accepté.

L’utilisation d’un code ouvre seulement une **demande de vérification**. Elle ne valide jamais le décès.

Le signalant doit être connecté. L’auto-signalement est interdit.

## 4. Vérification humaine en deux étapes

Le protocole impose deux décisions humaines séparées.

### Première vérification

Un administrateur autorisé avec MFA/AAL2 vérifie le décès selon une catégorie de preuve acceptable. SINJIRA enregistre la catégorie et la décision, mais le pipeline applicatif n’a pas besoin de conserver une copie brute permanente de la preuve.

Cette validation ouvre un **délai de sécurité de 30 jours**.

### Contestation

Si la personne est vivante ou si une déclaration est incorrecte, elle peut contester depuis son compte.

Une contestation ouverte :

- suspend le dossier;
- interdit la deuxième validation;
- interdit tout nouvel export.

Si la contestation est reconnue fondée, le dossier est rejeté.

Si elle est rejetée après examen humain, un **nouveau délai complet de 30 jours** commence. Le temps déjà écoulé avant la contestation n’est pas réutilisé.

### Deuxième validation

Après la fin du délai, sans contestation ouverte, une deuxième action humaine protégée par MFA/AAL2 est nécessaire.

Cette action n’autorise pas de nouveau contenu. Elle autorise seulement la préparation des versions déjà consenties par la personne.

## 5. Instantané autorisé

L’export fige un instantané minimal qui contient uniquement :

- le type de version;
- le nom/titre et les instructions de cette version;
- les éléments d’Histoire de vie explicitement autorisés;
- leur nature déclarée : fait, réflexion ou reconstruction;
- l’ordre choisi;
- les coordonnées nécessaires des destinataires choisis.

Les identifiants internes inutiles ne doivent pas être transmis dans le document ou les liens destinés aux proches.

La qualification **reconstruction** reste visible et ne devient jamais un fait certain par simple approbation narrative.

## 6. PDF numérique

Le format de remise par défaut est un **PDF numérique**.

Le PDF :

- est généré côté serveur;
- est placé dans le bucket privé `sinjira-life-story-exports`;
- possède une empreinte SHA-256;
- rappelle qu’il provient de l’Histoire de vie autorisée et non du Registre;
- n’est pas automatiquement imprimé;
- n’est pas automatiquement publié.

## 7. Remise aux proches

Un proche choisi peut ne pas disposer d’un Compte SINJIRA. La remise peut donc utiliser un jeton opaque propre au document.

Chaque jeton :

- contient 256 bits aléatoires;
- n’est stocké qu’en SHA-256;
- expire après une durée limitée;
- possède un nombre maximal de téléchargements;
- peut être révoqué;
- ne donne accès qu’au PDF déjà généré.

Le bucket n’est jamais rendu public.

Les réponses de téléchargement doivent empêcher la mise en cache inutile du document, notamment avec `Cache-Control: no-store`.

**Aucun fournisseur externe de courriel n’est activé en V24.5.2.** Les liens peuvent être remis manuellement. Un éventuel transport automatisé futur devra faire l’objet d’une décision distincte concernant la confidentialité, la sécurité, le coût et le fournisseur.

## 8. Révocation et rétention

Un export peut être révoqué. La révocation invalide ses liens actifs.

Après la remise, le PDF possède une échéance de purge. La purge :

- supprime le fichier du stockage privé;
- retire les métadonnées de contenu devenues inutiles;
- supprime les liens associés devenus inutiles.

Les liens expirés ou révoqués peuvent être nettoyés automatiquement parce qu’ils ne constituent pas le contenu source de la personne.

## 9. Données sources et Registre après décès

La suppression de l’Histoire de vie source et du Registre ne doit pas être déclenchée automatiquement par un simple délai.

Après la fin d’un dossier, SINJIRA crée des **tâches de revue humaine** distinctes :

- revue des données sources Histoire de vie;
- revue des données privées du Registre.

Une tâche indique qu’une décision est due. Elle ne constitue pas elle-même une autorisation de suppression.

Une suppression irréversible future devra respecter :

- le consentement et les directives de la personne;
- les obligations légales applicables;
- les éventuels litiges ou blocages de conservation;
- une vérification humaine suffisante;
- le principe que les intérêts de SINJIRA ne justifient pas une conservation indéfinie.

## 10. Journalisation et minimisation

Le système conserve uniquement les traces nécessaires pour expliquer les décisions importantes :

- signalement;
- première validation;
- période de sécurité;
- contestation et résolution;
- deuxième validation;
- génération/révocation/purge du PDF;
- état des tâches de nettoyage.

La journalisation ne doit pas devenir un mécanisme de surveillance des proches ou de la personne.

## 11. Interface utilisateur

La personne doit pouvoir depuis son compte :

- créer et gérer son Histoire de vie;
- choisir les versions et destinataires;
- activer ou désactiver la directive posthume;
- créer/révoquer ses codes privés de signalement;
- voir si une procédure posthume la concerne;
- contester immédiatement une déclaration incorrecte.

Un proche possédant un code peut utiliser la page de signalement sans obtenir d’accès au compte de la personne.

## 12. Interface administrative

La console Héritage numérique :

- exige un administrateur autorisé et MFA/AAL2;
- utilise des RPC contrôlés plutôt qu’un accès direct aux tables internes;
- n’expose pas le Registre;
- rend explicites les transitions irréversibles ou sensibles;
- exige une confirmation humaine avant les décisions de statut;
- affiche les liens de remise en clair uniquement au moment où ils sont créés.

## 13. Test d’arbitrage

Lorsqu’une optimisation du pipeline entre en conflit avec la volonté ou la vie privée de la personne, l’ordre d’arbitrage est :

1. dignité et sécurité humaine;
2. liberté, volonté et consentement;
3. confidentialité et minimisation;
4. exactitude et traçabilité;
5. facilité opérationnelle;
6. intérêts techniques ou commerciaux.

> **SINJIRA ne transmet pas les secrets d’une personne après sa mort. Elle transmet l’histoire qu’elle a choisi de laisser derrière elle.**
