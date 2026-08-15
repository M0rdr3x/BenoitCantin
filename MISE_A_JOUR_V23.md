# SINJIRA — Mise à jour V23

Cette version corrige les points prioritaires signalés le 13 août 2026.

## Corrections incluses

- Le chemin canonique de l’administration devient `/admin/sinjira/` en minuscules.
- Tous les liens d’administration principaux pointent vers ce chemin.
- Le logo de marque des pages Compte/SINJIRA/Admin retourne au portail principal `/`.
- Le Registre des Consciences enregistre désormais **d’abord dans Supabase**. Formspree devient une notification secondaire : une panne de Formspree ne doit plus faire perdre une participation correctement enregistrée.
- Le champ « Pronoms » a été supprimé du questionnaire.
- L’échelle de personnalité explique clairement les cinq positions bipolaires.
- La tranche mineure du Registre est harmonisée sur 12–17 ans; moins de 12 ans n’est pas accepté par ce formulaire.
- Un consentement facultatif permet de demander un brouillon assisté par IA. Le brouillon reste provisoire et doit être validé par Benoit Cantin.
- L’administration peut afficher les réponses du questionnaire, consulter temporairement la photo source via URL signée, créer une fiche manuelle, ou lancer un brouillon IA.
- La page « Mon personnage » sait maintenant afficher un portrait.
- Le portrait officiel fourni pour AbyssTime est préparé en 512 × 512 px.
- Une migration ajoute/maintient AbyssTime comme administrateur propriétaire et associe son personnage au Livre II, avec le titre du Livre II laissé à confirmer.

## Déploiement

### GitHub Pages
Téléverser les fichiers du pack à la racine du dépôt `M0rdr3x/BenoitCantin` en conservant les dossiers.

### Supabase
GitHub Pages ne déploie pas les migrations ni les Edge Functions. Il faut ensuite :

1. appliquer `supabase/migrations/20260813_abysstime_character_book2.sql`;
2. redéployer `supabase/functions/submit-character-questionnaire/` si la version de production n’est pas déjà identique;
3. redéployer `supabase/functions/admin-sinjira-v18/` pour que l’administration reçoive `source_payload` et les URL signées des photos;
4. vérifier que `OPENAI_API_KEY` est configurée côté Supabase uniquement si la préparation IA doit être active.

## Test minimal après publication

1. Se connecter avec un compte de test sans personnage.
2. Ouvrir `/projets/sinjira/registre/`.
3. Remplir les champs obligatoires et transmettre.
4. Confirmer que le message indique que le dossier est enregistré dans SINJIRA.
5. Se connecter avec AbyssTime et ouvrir `/admin/sinjira/`.
6. Vérifier que le questionnaire apparaît dans « Personnages des fans ».
7. Vérifier que le détail des réponses s’ouvre.
8. Ouvrir `/compte/mon-personnage.html` avec AbyssTime et confirmer le portrait + « SINJIRA — Livre II (titre à confirmer) ».
