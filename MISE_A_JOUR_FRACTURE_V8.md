# Fracture du Réseau-Mère - V8

## Logique validée

- **Solo (1 humain)** : une seule fiche regroupe le joueur principal + Joueur invisible 2 + Joueur invisible 3.
- **2 joueurs humains** : la partie compte 3 participants effectifs. Chaque humain possède **2 fiches privées séparées** :
  1. sa fiche personnelle;
  2. sa propre copie privée du **Joueur invisible 3**.
  Les deux copies du Joueur invisible 3 sont indépendantes : le Joueur 1 ne voit ni ne modifie la copie du Joueur 2, et inversement.
- **3 joueurs humains** : 3 participants effectifs, une fiche personnelle privée par joueur, aucun joueur invisible.
- La page `preparer-partie.html` ne montre jamais le contenu rempli des fiches : elle crée seulement les accès nécessaires.
- Les fiches joueur restent privées. Seule la Feuille de fin de partie peut être transmise volontairement à SINJIRA pour l'équilibrage.

## Sauvegarde

La base accepte maintenant plusieurs fiches privées dans une même partie grâce à `player_sheets.sheet_key`. Un même compte peut donc conserver sa fiche personnelle et sa fiche du Joueur invisible 3 sous le même code de partie.
