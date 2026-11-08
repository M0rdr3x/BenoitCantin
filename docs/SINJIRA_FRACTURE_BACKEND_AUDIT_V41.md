# SINJIRA — Fracture V41 : audit du moteur serveur, lecture seule (NO_GO)

**Référence :** suivi [#872](https://github.com/M0rdr3x/BenoitCantin/issues/872), programme [#826](https://github.com/M0rdr3x/BenoitCantin/issues/826), arbitrage des règles [#857](https://github.com/M0rdr3x/BenoitCantin/issues/857).

## Exécution vérifiée — 8 novembre 2026

La requête **`scripts/audits/sinjira_fracture_backend_v41_readonly.sql`** a été exécutée sur **les métadonnées PostgreSQL de la base SINJIRA**. Son unique `SELECT` lit les catalogues `pg_class`, `pg_namespace`, `pg_proc` et `pg_policies`, ainsi que les privilèges associés. Elle ne lit **ni ligne de partie, ni bulletin, ni identité, ni courriel**. Elle ne modifie **aucun schéma, politique, compte, partie ou paramètre**.

| Contrôle | Résultat | Signification |
|---|---|---|
| `engine_internal_rls` | **PASS** | Les 7 tables internes sont présentes et ont RLS activée |
| `engine_no_web_table_grants` | **PASS** | Pas de droit de lecture/écriture direct à `anon` / `authenticated` sur les 7 tables |
| `public_engine_rpc_anon` | **PASS** | Les entrées publiques du moteur examinées ne sont pas exécutables par `anon` |
| `legacy_final_bonus` | **BLOCK** | Le moteur historique donne +5 par siège accusé; les règles courantes indiquent +3 |
| `legacy_automatic_seats` | **BLOCK** | L'ancien moteur contrôle automatiquement des sièges `bot` ; la règle actuelle exige un contrôle humain des sièges invisibles |
| `legacy_engine_version` | **BLOCK** | Lancement basé sur `24.4.6` ; non réconcilié avec V36–V40 |
| `endgame_update_party_integrity` | **BLOCK** | La politique UPDATE ne vérifie pas explicitement la propriété de la **partie cible**, seulement celle de la ligne |
| `player_documents_update_membership` | **BLOCK** | La politique UPDATE ne vérifie pas explicitement l'appartenance à la **partie cible**, seulement celle de la ligne |
| `active_session_validation` | **BLOCK** | Pas de preuve de validation d'une session non révoquée dans la routine de rapport examinée. À confirmer sur toute la chaîne d'appel |
| `raw_state_member_boundary` | **REVIEW** | Garde membre visible dans la routine; tests multicomptes et absence d'exfiltration encore nécessaires |

**Totaux : 3 PASS, 6 BLOCK, 1 REVIEW.** Un résultat `BLOCK` indique un critère de lancement non satisfait dans ce contrôle; il ne constitue **pas automatiquement la preuve d'une exploitation possible**. Un `PASS` ne certifie pas la sécurité globale. La présence de RLS sur une table ne prouve pas à elle seule que les `SECURITY DEFINER` appelées sont correctement autorisées.

Le linter Supabase a également signalé `auth_leaked_password_protection` (`WARN`) et `rls_enabled_no_policy` (`INFO`). Des tables internes avec RLS sans politique ni droits directs peuvent être volontairement fermées; ne pas leur ajouter une politique générale pour « éliminer » l'avis. L'option Auth nécessite un examen séparé, sans abonnement payant automatique.

## Remédiations ordonnées

1. **Arbitrer #857 avant toute modification de calcul des bonus.** La valeur +5 du serveur doit être éliminée lors de la refonte alignée sur la règle officielle +3, mais il reste à décider si chaque vote individuel ou seulement les sièges retenus collectivement comptent. Ajouter tests sur un cas à trois humains (2 bonnes accusations, 1 mauvaise) avant changement de formule.
2. **Remplacer le comportement `bot` par le contrôle humain délégué des sièges invisibles.** Un utilisateur ne peut commander que son siège ou, dans Solo/Duo, les sièges explicitement attribués par l'instance serveur. Interdire toute usurpation, double passage ou accès à une main étrangère.
3. **Rapprocher V36–V40 du serveur** : 90 cartes canoniques, centre 2N, rapports/Preuve unique, soupçons privés, décisions de politique explicites, accusés distincts et départages atomiques.
4. **Durcir les politiques UPDATE avec `WITH CHECK` sur la cible**. Pour les documents joueurs, la nouvelle `party_id` doit demeurer une partie où l'utilisateur est membre. Pour les rapports finaux du propriétaire, la nouvelle `party_id` doit demeurer une partie dont l'utilisateur est le propriétaire. Contrôler les clés étrangères et tester le transfert malveillant entre deux parties. Préparer une migration **après revue**, ne pas écrire sur la production ici.
5. **Vérifier sessions révoquées et fonctions privilégiées** : `auth.uid()` et le droit `authenticated` ne suffisent pas à garantir la validité d'une session actuelle. Auditer l'entrée et chaque appel à une fonction `SECURITY DEFINER`, avec les protections complémentaires déjà suivies par les PR de sécurité.
6. **Recette sur un environnement isolé**, avec au minimum deux comptes membres et un non-membre : lecture d'identités adverses, mains, soupçons, rejouements, simultanéité, tests RLS et séparation des sièges; puis approbation de production protégée avec retour arrière et vérification post-livraison.

## Conditions de sécurité de cette PR

La requête est déposée dans **`scripts/audits/`**, pas dans `supabase/migrations/`. Le workflow de CI ne l'exécute **jamais sur la base distante** : ses tests vérifient uniquement qu'il s'agit d'un unique `SELECT` et qu'aucune table de données joueur n'est lue.

Pour la reproduire manuellement, exécuter le fichier tel quel à travers un accès autorisé **en lecture seule** et constater les résultats sans télécharger ni publier les identités ou les données utilisateurs.

**NO_GO :** ne pas réactiver le lobby, fusionner une migration non revue, appliquer un patch de RLS directement ni attribuer un bonus de partie sans règles approuvées. Cette livraison d'audit n'augmente pas automatiquement la maturité globale SINJIRA, estimée à **66,5 % ≈ 67 % (±10 points)**.
