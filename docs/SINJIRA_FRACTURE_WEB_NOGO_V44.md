# SINJIRA Fracture V44 — Garde de publication Web (NO_GO automatique)

**Objectif :** empêcher qu'une modification de la page publique Fracture réactive accidentellement l'ancien lobby ou un mécanisme d'action sur l'ancien moteur, tant que la recette de sécurité et l'alignement aux règles V36–V43 ne sont pas terminés.

## Périmètre garanti par ce contrôle

Le script `scripts/validate_fracture_web_nogo_v44.py` inspecte seulement le HTML versionné de :

- `projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html` — page d'état Web suspendu;
- `projets/sinjira/jeux/fracture-du-reseau-mere/index.html` — page de présentation et lien vers cet état.

Le contrôle vérifie que la page d'état indique toujours **« Mode Web en mise à niveau »**, la **suspension du lobby**, les règles de **2N cartes**, deux passages, contrôle humain Solo/Duo et **3 points**. Les liens vers le manuel et la feuille de score physique restent présents.

Il refuse explicitement les formulaires de jeu, champs interactifs, iframes, scripts autres que les deux scripts communs `/assets/js/site.js` et `/assets/js/v19-session.js`, scripts inline, gestionnaires d'événements inline, URLs JavaScript, redirections automatiques, attributs de déclenchement de lobby et références connues aux anciennes fonctions de jeu. Il contrôle aussi que la présentation garde son lien d'état `jouer.html` et ne charge pas l'ancien moteur directement.

## Tests adversariaux

La suite `tests/security/test_fracture_web_nogo_v44.py` lance des variantes fictives du HTML pour vérifier que chaque tentative de réactivation est rejetée et que la page actuelle reste admise. Elle tolère uniquement les changements de version de cache des scripts génériques, sans ouvrir de nouvelle source.

Le workflow `.github/workflows/sinjira-fracture-web-nogo-v44.yml` se déclenche si ces deux pages, le script de validation ou ses tests changent. Aucun secret, aucune connexion réseau, aucune partie ni donnée personnelle ne sont consultés. Aucun déploiement n'est déclenché par ce workflow.

## Limites et procédure de levée du blocage

**Ce garde statique ne constitue pas un pare-feu Web ni une preuve qu'un script générique chargé ne peut pas importer dynamiquement du jeu.** Il protège les modifications directes et accidentelles des pages contrôlées. Les permissions, les politiques RLS, la sécurité des RPC, les revocations de sessions et le déploiement du moteur doivent être contrôlés séparément.

Pour lever le NO_GO, il faudra d'abord terminer les critères de [#872](https://github.com/M0rdr3x/BenoitCantin/issues/872), arbitrer le score final [#857](https://github.com/M0rdr3x/BenoitCantin/issues/857), réaliser des tests multicomptes sur une base isolée, prévoir un retour arrière et obtenir l'approbation de publication. **Ne pas simplement effacer le test ou l'avertissement pour faire passer la CI.**

Cette PR n'active aucun moteur, ne modifie aucune table Supabase et n'augmente pas artificiellement l'avancement global de SINJIRA (environ 67 %).
