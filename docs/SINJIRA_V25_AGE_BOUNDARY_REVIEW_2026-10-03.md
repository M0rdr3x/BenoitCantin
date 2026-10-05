# SINJIRA V25 — Revue de la frontière calendrier 11 / 13 / 18 ans

> Document de revue uniquement. Ce fichier ne modifie aucune migration et ne constitue pas une approbation production.

Suivi : #453  
Revue humaine du lot : #438  
PR : #435  
HEAD observé au moment de la préparation : `f6b1cff1f6961a1dede6c3ea84bf8d99c4382119`


## Statut après décision et correction — 4 octobre 2026

La décision de travail a été enregistrée dans #438 puis le correctif minimal a été appliqué sans merge ni production :

- commit SQL : `28c28409bcd610ad873c31e96cac9af46d240a7a`;
- migration modifiée : `supabase/migrations/20260916210000_sinjira_v25_child_guardian_signup.sql`;
- ancien blob : `8c7239489d57f0a821da104b5df5ead16fc8103e`;
- nouveau blob : `3231fc2720a28700be9d1be117e53a9a2448b08b`;
- garde statique aligné : commit `b065aa6098d335bd84437e2a84e88e10ecdae7a4`;
- preuve fonctionnelle : run `37181885399`, job `111375942461`, **75/75 assertions pgTAP**;
- reconstruction Supabase locale, coffre privé et inscription Auth HTTP exactement 11 ans : **SUCCESS**;
- #453 : **fermé comme terminé**.

Le défaut des veilles des 13 et 18 ans est donc corrigé. La revue globale #438 reste toutefois ouverte : les **43 migrations futures restent explicitement non revues**, le reviewed batch et le ledger production sont inchangés, et aucune promotion Supabase production n'est autorisée par cette correction.

## Défaut reproduit avant correction

Avant le correctif, le workflow **SINJIRA V25 — Inscription enfant 11 ans** a d'abord reproduit le défaut sur la veille des 13 ans, puis l'extension de preuve à 75 assertions a confirmé la même classe d'erreur à la veille des 18 ans :

- test : « la veille des 13 ans reste classée child »;
- attendu : `child`;
- observé : `youth`.

La fonction concernée est `public.sinjira_age_band()`, définie dans :

`supabase/migrations/20260916210000_sinjira_v25_child_guardian_signup.sql`.

Le classifieur utilise actuellement des comparaisons de la forme :

```sql
age(current_date, s.date_of_birth) < interval '11 years'
age(current_date, s.date_of_birth) < interval '13 years'
age(current_date, s.date_of_birth) < interval '18 years'
```

Les comparaisons PostgreSQL d'intervalles peuvent normaliser mois et jours de façon à rendre une valeur calendaire comme 12 ans 11 mois 30 jours équivalente au seuil de 13 ans pour la comparaison. Le classement peut donc franchir la frontière avant le jour réel de l'anniversaire.

## Audit du périmètre SQL

Un audit du diff complet de la PR #435 (**555 fichiers modifiés**) a recherché les comparaisons d'âge basées sur `age(current_date, ...)`, les seuils `interval '11 years'`, `interval '13 years'`, `interval '18 years'` et les usages d'âge complété.

Résultat :
- un seul **classifieur de production** utilise encore les comparaisons fragiles d'intervalles aux seuils 11/13/18 : `public.sinjira_age_band()` dans `20260916210000_sinjira_v25_child_guardian_signup.sql`;
- les autres contrôles d'âge de cette migration utilisent déjà `extract(year from age(...))::integer`;
- `20260919100000_sinjira_v25_private_profile_age_11.sql` utilise déjà l'âge complété entier pour ses frontières;
- les autres occurrences retrouvées concernent des fixtures/tests de dates exactes, pas un classifieur production concurrent.

Le défaut a donc été corrigé par un diff minimal dans `sinjira_age_band()` après décision tracée dans #438. Cette correction réduit le périmètre technique mais **ne vaut pas approbation globale des 43 migrations futures**.

Le test de reproduction construit bien la veille des 13 ans avec :

`current_date - interval '13 years' + interval '1 day'`

et observait `youth` au lieu de `child` avant le correctif.

## Changement retenu et appliqué

La décision explicite a été enregistrée dans #438 avant modification. Le diff minimal retenu remplace les comparaisons d'intervalles par l'âge complété entier.

Remplacer le calcul répété par un âge complété entier :

```sql
extract(year from age(current_date, s.date_of_birth))::integer
```

Puis appliquer les seuils numériques :

```sql
case
  when ... then 'adult'
  when s.user_id is null
    or s.date_of_birth is null
    or s.date_of_birth > current_date
    then 'unverified'
  when s.legacy_status = 'memorialized'
    then 'memorial'
  when extract(year from age(current_date, s.date_of_birth))::integer < 11
    then 'under11'
  when extract(year from age(current_date, s.date_of_birth))::integer < 13
    then case
      when exists (
        select 1
        from public.guardian_links g
        where g.minor_user_id = s.user_id
          and g.status = 'verified'
          and g.revoked_at is null
      ) then 'child'
      else 'child_pending'
    end
  when extract(year from age(current_date, s.date_of_birth))::integer < 18
    then case
      when exists (
        select 1
        from public.guardian_links g
        where g.minor_user_id = s.user_id
          and g.status = 'verified'
          and g.revoked_at is null
      ) then 'youth'
      else 'youth_pending'
    end
  else 'adult'
end
```

La logique de supervision ne change pas. Seule la définition du franchissement calendaire des seuils est proposée à la correction.

## Alternative à considérer pendant la revue

Une autre écriture possible consiste à comparer directement les dates d'anniversaire :

```sql
s.date_of_birth > current_date - interval '13 years'
```

Cette variante doit toutefois être vérifiée avec soin pour le 29 février. L'âge complété via `extract(year from age(...))` est déjà utilisé ailleurs dans le même lot et offre une cohérence interne plus forte.

## Matrice de tests exigée

La correction ne doit être considérée comme valide que si les cas suivants sont couverts :

| Frontière | Date de naissance de test | Classe attendue |
|---|---|---|
| veille des 11 ans | anniversaire demain | `under11` |
| jour des 11 ans | anniversaire aujourd'hui | `child` ou `child_pending` selon supervision |
| veille des 13 ans | anniversaire demain | `child` ou `child_pending` |
| jour des 13 ans | anniversaire aujourd'hui | `youth` ou `youth_pending` |
| veille des 18 ans | anniversaire demain | `youth` ou `youth_pending` |
| jour des 18 ans | anniversaire aujourd'hui | `adult` |

Ajouter aussi des cas autour du 29 février :
- naissance le 29 février;
- année courante bissextile;
- année courante non bissextile;
- veille et jour du seuil légal retenu par la logique applicative.

## Contraintes de non-régression

La correction doit conserver :
- `child / child_pending` pour 11–12 ans;
- `youth / youth_pending` pour 13–17 ans;
- `adult` à partir de 18 ans;
- la révocation immédiate d'un lien tuteur;
- le passage `child_pending -> child` après rétablissement valide;
- la coupure des fonctions sociales pour `child`;
- les contrôles AAL2 existants;
- l'absence d'oracle UUID;
- la minimisation des métadonnées parentales.

## Gouvernance de la modification

Avant toute modification du blob migration :
1. enregistrer la décision humaine dans #438;
2. choisir le correctif exact;
3. modifier la migration future concernée;
4. étendre les tests de frontière;
5. recalculer le SHA du blob;
6. revalider la décision de revue sur ce nouveau blob;
7. seulement ensuite envisager une mise à jour du reviewed batch / ledger selon le processus prévu.

Ce document n'autorise ni synchronisation Supabase, ni `apply=true`, ni déploiement production.
