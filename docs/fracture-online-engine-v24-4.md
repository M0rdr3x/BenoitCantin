# SINJIRA™ — Fracture du Réseau-Mère — moteur Web V24.4.1

## Objectif

Le mode Web devient jouable sans paquet physique. Le serveur Supabase est l’autorité pour les identités, le paquet de 90 cartes, les mains privées, l’ordre des tours, les rapports, les preuves, les soupçons, les accusations et les scores.

## Solo et Duo

- **Solo (1 humain)** : siège 1 humain; sièges invisibles 2 et 3 contrôlés par le moteur tactique.
- **Duo (2 humains)** : sièges 1 et 2 humains; siège invisible 3 contrôlé par le moteur tactique.
- Le moteur tactique ne nécessite aucune API d’IA générative. Il choisit ses cartes à partir de sa propre identité et de ses propres informations, choisit les cartes centrales face cachée aléatoirement, peut bluffer dans son rapport et génère ses soupçons sans consulter l’identité secrète des adversaires.

## Multijoueur

De 3 à 20 humains, chaque siège est contrôlé par un Compte SINJIRA™ distinct. Les pages se resynchronisent automatiquement avec le serveur. Une action est acceptée seulement si le serveur confirme la phase et le tour du joueur.

## Sécurité des informations de jeu

Les tables internes du moteur sont protégées et ne sont pas lisibles directement par les comptes authentifiés. Les RPC retournent uniquement :

- l’identité du joueur connecté;
- sa main quand elle doit être visible;
- ses cartes récupérées;
- le centre sous forme de cartes face cachée;
- les informations publiques de la partie.

Les identités adverses sont révélées uniquement à la fin.

## Déroulement numérique

1. création/jonction du salon;
2. démarrage par le créateur lorsque tous les humains sont présents;
3. distribution serveur des identités et des 90 cartes;
4. chaque siège conserve 2 cartes sur 3;
5. ajout automatique des cartes système au centre;
6. deux passages de sélection face cachée;
7. rapport, Preuve facultative et soupçon;
8. résolution automatique de la ronde;
9. accusation finale des humains;
10. calcul des bonus et résultat;
11. ronde(s) de départage si l’égalité persiste.

## Déploiement

Le navigateur V24.4 exige le marqueur serveur `24.4.x`. Les migrations `20260816_fracture_web_engine_v24_4.sql` puis `20260816_fracture_web_engine_v24_4_1_hotfix.sql` doivent être appliquées à Supabase production avant que le salon soit déverrouillé.
