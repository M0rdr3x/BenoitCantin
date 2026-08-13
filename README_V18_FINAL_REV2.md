# BenoitCantin — V18 FINAL REV2

Cette révision consolide les choix approuvés après la V18 finale.

## Accueil
- Projet Nova
- SINJIRA – Littérature
- SINJIRA – Jeux
- SINJIRA – Registre des Consciences
- Centre de la constellation : sceau BC au repos, visuel de la section au survol.
- Bloc Compte SINJIRA directement sur l’accueil : connexion, inscription, profil, documents, personnages, parties et administration si le rôle est autorisé.

## Visuels officiels
- `assets/media/sinjira-litterature.webp` : nouveau visuel officiel Littérature.
- `assets/media/sinjira-jeux.webp` : nouveau visuel officiel Jeux.
- `assets/media/sinjira-registre.webp` : visuel officiel Registre des Consciences.

## Registre des Consciences
L’URL publique canonique est `/projets/sinjira/registre/`. L’ancienne page `/personnages/` redirige vers le Registre.
Le questionnaire reste fondé sur la personnalité réelle du participant. La section de liaison au compte affiche maintenant clairement :
- nom du compte;
- courriel associé;
- notes complémentaires.
Le fan n’a pas à inventer le nom, le rôle ou le roman du personnage final.

## Mode manuel sans API OpenAI
La V18 REV2 fonctionne sans `OPENAI_API_KEY`. À l’envoi :
1. le questionnaire est envoyé par Formspree vers le flux personnel déjà configuré (`xdenkzrv`, attendu : `kingtyrano@gmail.com`);
2. le système tente aussi d’enregistrer le dossier dans Supabase pour le suivi du Compte SINJIRA;
3. la création du personnage est effectuée manuellement par Benoit Cantin.

La fonction serveur accepte `manual_only:true` afin d’éviter une génération IA automatique.

## Administration
L’administration reste unique et protégée. La section Personnages fans permet désormais de créer une fiche de personnage manuelle depuis une soumission, puis de la compléter dans la Bible des personnages.

## Canon
La révision publique mentionne la Bible maîtresse CANON v1.1. Les manuscrits et informations SECRET AUTEUR ne sont pas inclus dans le paquet GitHub public.
