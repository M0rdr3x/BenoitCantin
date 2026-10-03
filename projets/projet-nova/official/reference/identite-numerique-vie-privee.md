# V316 — Identité numérique publique, permissions, vie privée, cycle de vie des dossiers et audit

## 1. Objet
V316 prolonge les contrôles V308 à V315 sans modifier les paramètres fiscaux, la primauté citoyenne, la protection de la première ligne ni les règles de simplification administrative.

Le principe central est : **une identité numérique sert à prouver ce qui est nécessaire à un service; elle ne crée pas un droit général pour l’État de connaître, centraliser ou croiser toute la vie d’une personne.**

## 2. Identité numérique proportionnée au risque
L’identité numérique publique peut offrir des justificatifs et moyens d’authentification réutilisables, mais le niveau de preuve demandé doit être proportionné à la sensibilité de l’action. Un service banal ne doit pas exiger le même niveau d’identification qu’une action à conséquence juridique, financière ou de sécurité élevée.

La possession d’un compte ou justificatif numérique n’accorde aucun accès universel aux dossiers publics. L’identité, l’authentification et l’autorisation sont trois fonctions distinctes.

Lorsque c’est techniquement et juridiquement approprié, l’État doit pouvoir vérifier un attribut minimal — par exemple une condition d’âge ou de résidence — sans exiger davantage de renseignements que nécessaire.

V316 n’impose pas une biométrie universelle, un facteur d’authentification unique ni une identité numérique comme seul canal d’accès aux services.

## 3. Permissions : moindre privilège et finalité déterminée
Tout accès à un système, dossier ou donnée doit être rattaché à une fonction autorisée, une finalité et un périmètre. Un titre hiérarchique ne constitue pas en soi un droit d’accès général.

Les permissions doivent suivre les principes de moindre privilège, séparation des fonctions, besoin de savoir et révocation lorsque la fonction, le mandat ou la justification disparaît. Les accès exceptionnels ou d’urgence doivent laisser une trace renforcée et faire l’objet d’une revue appropriée.

Les comptes partagés et accès non attribuables à une personne ou fonction déterminée doivent être évités sauf exception technique justifiée et compensée par des contrôles équivalents.

## 4. Réutilisation des données et autorisations de partage
La règle V315 « fournir une fois » demeure, mais elle ne transforme pas l’État en base de données universelle. Une réutilisation ou transmission doit être rattachée à une base légale ou autorisation valide, une finalité déterminée, une donnée minimale et une responsabilité identifiable.

Une autorisation d’accès à une donnée ne vaut pas autorisation d’accès à toutes les données de la même personne. Les interfaces interorganismes doivent exposer uniquement les champs, opérations et événements nécessaires au cas d’usage autorisé.

Le croisement généralisé de dossiers, la constitution silencieuse d’un profil transversal ou l’utilisation secondaire incompatible avec la finalité d’origine sont interdits en l’absence d’une base juridique explicite et des garanties requises.

## 5. Séparation des identifiants et réduction de la corrélation
Lorsque raisonnablement possible, les systèmes évitent qu’un identifiant universel directement réutilisable permette à n’importe quel service de corréler automatiquement toutes les activités d’une personne. Des identifiants sectoriels, pseudonymes, jetons ou mécanismes équivalents peuvent être utilisés lorsque cela réduit la corrélation sans empêcher la vérification légitime.

Cette séparation n’empêche pas une liaison légalement nécessaire; elle exige que la liaison soit contrôlée, justifiée et auditable.

## 6. Cycle de vie des dossiers
Tout dossier public important doit avoir une classe, une finalité, un propriétaire institutionnel, des règles de conservation, une disposition finale et une trace des changements déterminants. La conservation indéfinie par défaut n’est pas une règle acceptable simplement parce que le stockage numérique est peu coûteux.

La suppression, destruction, anonymisation, archivage ou transfert d’un dossier doit respecter les obligations légales, historiques, probatoires et opérationnelles applicables. Une suppression ne doit pas servir à effacer une preuve nécessaire à un audit, recours ou enquête légitime.

V316 ne fixe pas une durée universelle de conservation commune à tous les dossiers.

## 7. Journaux d’audit et accès administratifs
Les accès significatifs aux données sensibles, changements de permissions, consultations exceptionnelles, exports, corrections et actions administratives doivent produire des événements d’audit attribuables et protégés contre l’altération silencieuse.

Le journal doit permettre de répondre à des questions simples : qui a accédé à quoi, quand, par quelle fonction, pour quelle finalité ou référence d’autorisation, et quelle action a été effectuée.

Les journaux ne doivent pas devenir un mécanisme de surveillance générale des citoyens ou des employés au-delà de ce qui est nécessaire à la sécurité, à l’intégrité, à la conformité et à l’audit.

## 8. Transparence et accès du citoyen
Lorsque la loi le permet, une personne doit pouvoir connaître les principales données déterminantes détenues à son sujet, demander la correction d’une donnée inexacte et obtenir une explication suffisante sur l’origine ou l’utilisation d’une donnée ayant contribué à une décision.

Un mécanisme de consultation des accès significatifs peut être offert lorsque cela ne compromet pas la sécurité, une enquête, la protection d’un tiers ou une autre exception légitime. Toute exception doit être définie et non laissée à une discrétion générale.

## 9. Interopérabilité sécurisée
L’interopérabilité doit reposer sur des contrats d’interface documentés : identité du service appelant, opération autorisée, données minimales, finalité, règles d’erreur, journalisation et responsabilité.

La connexion technique de deux systèmes n’élargit pas automatiquement les pouvoirs juridiques de l’un ou de l’autre. Une API, un bus d’événements ou une plateforme d’échange ne constitue jamais à elle seule une autorisation juridique.

V316 ne crée pas de « superbase » centrale obligatoire ni un droit d’agréger tous les dossiers dans un profil unique.

## 10. Sécurité, incidents et révocation
Les identifiants, justificatifs et permissions compromis doivent pouvoir être suspendus ou révoqués. Les incidents doivent être enregistrés, contenus, analysés et corrigés selon leur nature, avec conservation des preuves nécessaires.

Les secrets techniques, clés et moyens d’administration doivent être séparés des usages ordinaires et soumis à des contrôles adaptés. Les mécanismes de récupération de compte ne doivent pas devenir une voie plus faible permettant de contourner l’authentification normale.

## 11. Continuité et accès non numérique
La transformation numérique ne doit pas rendre inaccessible un service essentiel à une personne qui ne peut raisonnablement utiliser le mécanisme numérique applicable. Les voies alternatives doivent offrir une sécurité et une traçabilité adaptées sans exiger une identité numérique universelle.

Une panne d’un fournisseur d’identité ou d’une plateforme centrale ne doit pas paralyser sans solution de continuité tous les services critiques.

## 12. Automatisation, profilage et décisions
Un système automatisé peut aider à vérifier une permission, détecter une anomalie ou router une demande, mais il ne reçoit pas un pouvoir souverain. Les décisions à effet important doivent rester soumises aux règles applicables de preuve, de justification, de révision et de responsabilité.

V316 n’autorise pas un score citoyen général, un profil politique ou comportemental transversal, ni une surveillance prédictive générale de la population.

## 13. Registres V316
V316 introduit huit modèles interopérables :
1. registre des identités et justificatifs;
2. registre des permissions et accès;
3. registre des bases légales, finalités et partages;
4. registre du cycle de vie des dossiers;
5. registre des journaux d’audit et accès significatifs;
6. registre des interfaces et échanges interopérables;
7. registre des incidents, suspensions et révocations;
8. registre de l’accès citoyen et des corrections.

## 14. Paramètres volontairement laissés ouverts
V316 ne fixe pas automatiquement :
- un niveau universel d’assurance d’identité;
- une obligation biométrique universelle;
- une obligation universelle d’authentification multifacteur;
- une durée universelle de conservation des dossiers ou journaux;
- une fréquence universelle de revue des permissions;
- une durée universelle de session ou de validité des justificatifs;
- un délai universel de notification d’incident;
- un seuil universel de partage interorganismes;
- une période universelle de rotation des identifiants pseudonymes;
- un algorithme cryptographique unique inscrit politiquement dans la doctrine.

Ces valeurs doivent être déterminées par la loi, les normes techniques applicables, le risque du service et les décisions explicitement adoptées.

## 15. Primauté citoyenne et absence d’effet juridique automatique
La primauté citoyenne demeure inchangée : l’identité numérique est un outil de service et de preuve, pas une source de souveraineté administrative. Aucun administrateur de système, responsable de sécurité ou gestionnaire d’identité n’acquiert un pouvoir personnel sur le citoyen.

V316 ne produit aucun effet juridique automatique, ne ferme aucune des 14 décisions politiques héritées, ne valide aucune des 26 sections anglaises et ne modifie aucun paramètre fiscal V308.

---

**Transparence IA —** Idées, vision et décisions : Benoit Cantin. Mise en œuvre assistée par des outils d'intelligence artificielle. Validation finale et responsabilité du contenu : Benoit Cantin.
