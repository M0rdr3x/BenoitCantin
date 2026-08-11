# Fracture du Réseau-Mère - documents officiels v6

Cette mise à jour remplace l'ancienne fiche de partie par les deux documents officiels fournis :

1. **Fiche joueur** - privée.
   - 10 tours : points Résistance, points Réseau-Mère, suspect Résistance, suspect Réseau-Mère.
   - totaux et accusation finale jusqu'à 7 numéros de joueurs.
   - téléchargeable en PDF remplissable.
   - sauvegarde dans le Compte SINJIRA seulement à la demande du joueur.
   - envoi au courriel du Compte SINJIRA seulement à la demande du joueur.
   - **jamais transmise aux données d'équilibrage**.

2. **Feuille de fin de partie** - commune.
   - 10 tours : points des deux camps et camp gagnant du tour.
   - bonus, totaux et gagnant.
   - seule cette feuille peut être transmise volontairement à SINJIRA pour l'équilibrage.

3. **Préparer une partie** - outil dynamique.
   - demande le nombre de joueurs;
   - crée automatiquement une carte/lien de fiche privée pour chaque joueur;
   - reporte le nombre de joueurs vers la Feuille de fin de partie;
   - n'envoie pas les noms/pseudos locaux au serveur.

## Pages

- `/projets/sinjira/jeux/fracture-du-reseau-mere/preparer-partie.html`
- `/projets/sinjira/jeux/fracture-du-reseau-mere/fiche-web.html`
- `/projets/sinjira/jeux/fracture-du-reseau-mere/fiche-joueur.html`
- `/projets/sinjira/jeux/fracture-du-reseau-mere/fin-de-partie.html`

## PDFs

- `SINJIRA_Fiche_Joueur_Interactive.pdf` : deux copies interactives, fidèle au PDF officiel fourni.
- `SINJIRA_Fiche_Joueur_1_Copie_Interactive.pdf` : une copie interactive utilisée par l'outil web individuel.
- `SINJIRA_Feuille_de_fin_de_partie_Interactive.pdf` : feuille interactive fidèle au PDF officiel fourni.

Le backend Supabase a été mis à jour avec `endgame_sheets` et la fonction de contribution a été restreinte aux données de fin de partie.
