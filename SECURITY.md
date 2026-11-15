# Politique de sécurité — BenoitCantin.com / SINJIRA / Projet NOVA

La sécurité des utilisateurs, des comptes SINJIRA et de la confidentialité des consultations publiques de Projet NOVA est prioritaire.

## Périmètre
Les signalements sont bienvenus pour le site public `www.benoitcantin.com`, ses interfaces de compte et d'administration, les services Supabase, les formulaires et les composants du dépôt GitHub servant ces usages.

## Signaler une vulnérabilité
**Ne publiez pas de détails d'exploitation, de données personnelles, de jetons ou de mots de passe dans une issue ou une pull request GitHub publique.**

Utilisez le [formulaire de contact officiel](https://www.benoitcantin.com/contact.html) en indiquant « Signalement de sécurité » et une description minimale sans secrets. Le point de contact public est également annoncé par [`/.well-known/security.txt`](https://www.benoitcantin.com/.well-known/security.txt). Si GitHub propose l'option **Report a vulnerability** dans l'onglet Security du dépôt, privilégiez ce mécanisme privé. Ne supposez pas qu'une issue ordinaire est privée.

Pour préparer le rapport, précisez uniquement les pages ou fonctionnalités concernées, les conditions nécessaires, l'impact potentiel et la méthode de reproduction **sans exploiter de comptes de tiers**. Les éléments sensibles ne doivent être transmis qu'après accord sur un canal privé approprié.

## Limites de la recherche responsable
- Évitez toute modification, téléchargement ou divulgation de données appartenant à autrui.
- N'effectuez pas de tests de saturation (DoS), de collecte massive, d'ingénierie sociale ou de contournement abusif de contrôles.
- Interrompez les essais en cas d'accès inattendu à des données sensibles et signalez le problème sans conserver les données.
- Aucune permission générale de pentest intrusif sur les services tiers n'est accordée par cette politique.

## Traitement
Les signalements sont examinés, reproduits en environnement isolé lorsque possible, puis corrigés et vérifiés par des tests. Les délais de réponse ou de résolution ne sont pas garantis. Une publication coordonnée des détails pourra être discutée après correction.

## Pratiques du projet
Les correctifs de sécurité doivent passer par une branche et une pull request revues, avec tests automatisés. Les secrets doivent rester hors du dépôt; les changements d'accès, de RLS, de déploiement ou de migration ne doivent pas être promus en production sans revue et contrôle des effets.

Dernière mise à jour : 2026-11-03.
