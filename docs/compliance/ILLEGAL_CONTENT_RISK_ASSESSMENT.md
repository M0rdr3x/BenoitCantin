# SINJIRA™ — analyse de risque contenu et activités illicites

Version V24.4.83 — 2026-08-19.

## Risques couverts en priorité

- exploitation sexuelle et sollicitation sexuelle;
- prostitution/proxénétisme et commerce de services sexuels;
- contenu sexuel payant/promu type OnlyFans/Fansly;
- traite, vente, achat ou recrutement de personnes;
- grooming et exploitation d'un mineur;
- vente de drogues et commerce illicite;
- menaces crédibles, harcèlement, haine, fraude, extorsion, usurpation et doxxing;
- tentative de déplacer un mineur hors plateforme;
- sollicitations financières envers un mineur.

## Contrôles existants

V24.4.82 applique une garde serveur sur 14 surfaces persistées et fournit des motifs de signalement structurés. Les contenus à risque critique créent une notification admin et, en V24.4.83, un dossier d'escalade interne distinct.

## Principe de proportionnalité

Le système doit bloquer l'usage du service pour commettre, faciliter, vendre, recruter ou solliciter une activité interdite. Il ne doit pas empêcher une victime de demander de l'aide, un utilisateur de signaler le comportement, ni une discussion légitime de prévention. Les filtres automatiques sont des garde-fous, pas une détermination pénale.

## Procédure de modération

1. Protéger immédiatement la personne: blocage/fermeture de l'interaction lorsque nécessaire.
2. Préserver les références et métadonnées nécessaires; ne pas multiplier les copies de contenu illégal.
3. Classer le dossier et déterminer la juridiction applicable.
4. Appliquer les obligations de signalement/préservation légales selon la juridiction et les faits.
5. Documenter toute décision de retrait, suspension, signalement externe ou absence de signalement.
6. Prévoir un mécanisme de contestation pour les décisions ordinaires; les informations susceptibles de compromettre une enquête ne doivent pas être divulguées.

## Interdictions universelles de produit

SINJIRA™ ne doit jamais être conçu comme:
- marché de services sexuels;
- plateforme de contenu sexuel payant;
- marché de drogues ou biens illicites;
- place de marché de personnes;
- service permettant le contact romantique/sexuel entre adulte et mineur;
- moyen de monétiser l'accès à un mineur ou à ses données;
- service de publicité comportementale fondée sur données sensibles ou données d'enfants.

## Futures fonctions à haut risque

Avant images arbitraires, vidéo en direct, audio public, partage de fichiers, marketplace, géolocalisation ou paiements, effectuer une nouvelle analyse de risques et ajouter des contrôles spécifiques. Une fonction préparée dans le code ne doit pas être considérée activée tant que son gate de conformité n'est pas satisfait.
