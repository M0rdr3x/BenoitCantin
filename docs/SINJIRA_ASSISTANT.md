# Assistant SINJIRA™ — contrat V24.4.45

L’assistant public du site est une aide contextuelle locale chargée dans le navigateur. Il sert à orienter les visiteurs et les membres vers les bons parcours sans dépendre d’un fournisseur d’IA externe.

## Garanties actuelles

- traitement local dans l’onglet du navigateur;
- aucune clé API embarquée;
- aucune requête réseau émise par le moteur de conversation;
- aucune persistance de la conversation dans `localStorage`, `sessionStorage`, IndexedDB ou les cookies;
- filtrage des demandes contenant des mots de passe, codes de récupération, clés API ou secrets;
- séparation explicite des contextes jeunesse;
- aucune route d’administration proposée par l’assistant public;
- aide contextuelle pour SINJIRA™, le Registre des Consciences, les romans, Fracture, le Compte SINJIRA™, la Communauté, le Monde parallèle et Projet Nova.

## Compatibilité

Le contrat de validation couvre Chromium, Firefox et WebKit/Safari, ainsi qu’un profil mobile. Les parcours doivent rester utilisables au clavier, conserver un focus visible et respecter `prefers-reduced-motion`.

## Limites volontaires

Cette version n’est pas un grand modèle génératif. Elle classe une question dans une base d’aide locale vérifiée et préfère une réponse prudente ou une orientation vers Contact lorsqu’elle ne dispose pas d’une réponse suffisamment fiable. Un fournisseur génératif externe ne devra être activé qu’avec une architecture serveur sécurisée, un choix explicite de confidentialité et une autorisation distincte pour tout service payant.
