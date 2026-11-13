# SINJIRA — V49 : contrôle de répétabilité sans perte pour la migration liseuse V32

**9 novembre 2026 — Test de laboratoire isolé et non certificatif.**

## Problème et objectif

La version V32 ajoute `scroll_ratio numeric(5,4)` (position intrapage) à `public.sinjira_reader_library`, avec conservation des marque-pages antérieurs `scroll_ratio=NULL`. Le prévol V47 du **8 novembre 2026** constatait **7 PASS, 2 BLOCK, 1 REVIEW, NO_GO** sur la production Supabase : la colonne et sa contrainte manquaient. Les tests V48 apportaient une preuve de persistance SQL A/B/A sur un PostgreSQL jetable, **pas une recette sur deux appareils**.

V49 vérifie un autre risque de déploiement : une reprise/relecture **répétée** de la migration V32 ne doit ni réinitialiser les positions existantes ni dupliquer la contrainte, les lignes ou la politique de lecture privée. Le test utilise **le fichier SQL V32 original**, jamais une simulation de son contenu.

## Banc V49

Le workflow existant `.github/workflows/sinjira-reader-v48-multisession.yml` crée une base PostgreSQL 17.6 **éphémère**, confinée à `127.0.0.1`. Après les quatre étapes V48 (initialisation, compte fictif A, compte fictif B et retour A), le nouvel essai :

1. **Vérifie le nom exact de la base jetable** `sinjira_reader_v48_test_only` et la présence de RLS avant la moindre opération d'écriture de la fixture.
2. Ajoute une **troisième progression fictive** antérieure à V32, avec `scroll_ratio=NULL`, dans un deuxième livre du compte A. Elle ne contient aucun contenu du roman.
3. Fige localement une table temporaire de comparaison des trois positions et de leurs dates `created_at`, `updated_at`, `last_opened_at`.
4. Exécute le **SQL V32 d'origine deux fois** à la suite. Vérifie que les lignes, pages, pourcentages, ratios et horodatages sont **strictement identiques** avant/après.
5. Vérifie qu'il existe exactement **une contrainte de plage** et **une politique propriétaire**, sans fuite RLS.
6. Simule les rôles authentifiés A et B et le rôle anonyme : A voit ses deux livres et ne peut modifier B; B ne voit que son livre; anon ne voit aucune progression.
7. Émet `V49-REPEAT-V32-PASS` en cas de succès, mais ne délivre **aucune approbation de migration ou d'ouverture**.

Un contrat Python ajoute sept vérifications empêchant les connexions de production, les secrets, les rôles réels, un changement tacite de migration et une prétendue certification de lancement.

## Limites et portes non franchies

Ce succès ne prouve **pas** que la migration V32 a été exécutée en production, ni que le schéma réel correspond à la fixture miniature. Il ne mesure pas la synchronisation entre deux téléphones réels, la connexion Supabase Auth, la réception sécurisée d'un PDF privé, les délais réseau, la perte de connexion, le cache PWA, les conflits de dates ni la révocation d'une session.

Le statut `reader_v32_prod` reste **OPEN** jusqu'à vérification en production par la procédure autorisée et un nouveau prévol V47. `reader_two_devices` reste **OPEN** jusqu'à un essai réel de deux appareils ou navigateurs distincts autorisés, avec la même identité et les permissions adéquates.

**Aucune donnée client, aucun livre privé, aucune transaction réelle, aucune migration déployée par cette PR.**

## Étapes de réception encore nécessaires

- Appliquer V32 uniquement par le **runbook de production existant**, avec approbation explicite, préparation d'un retour arrière adapté et journal de migration; **ne pas exécuter un push global non revu**.
- Vérifier la colonne, la contrainte et les politiques de la **vraie** table de production par le prévol lecture seule V47, puis faire examiner les GRANT anonymes.
- Faire le test de sauvegarde et de restauration de page+ratio sur deux appareils autorisés : A sauvegarde, B retrouve et met à jour, A reconnecte, comparaison avec une lecture hors ligne, changement de compte, droit d'accès au livre et purge.
- Enregistrer des preuves datées et une approbation d'exploitation indépendante; garder les deux portes **OPEN** en l'absence de ces pièces.

**Avancement de SINJIRA au 8 novembre 2026 : maturité pondérée estimée de 66,5 % (±10 points), 13/13 portes de lancement OPEN, pas de date de fin certifiable.** V49 renforce le test de migrations sans modifier cet indicateur.
