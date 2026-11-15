-- SINJIRA V42 — CANDIDAT SQL, NON AUTORISÉ POUR LA PRODUCTION.
-- Ne pas placer dans supabase/migrations, ne pas exécuter sur la base liée.
-- Exécution AUTOMATISÉE uniquement sur PostgreSQL éphémère en CI.
-- Avant production : décision, migration versionnée conforme au runbook,
-- prévol distant, approbation et tests de deux comptes réels.
--
-- Alignement sur les politiques INSERT existantes observées le 8 novembre :
--   "fracture endgame owner insert" et "fracture docs own insert".
-- Le prédicat USING actuel est conservé pour limiter la régression.
-- Le nouveau WITH CHECK empêche de déplacer des données vers une partie
-- dont le propriétaire/membre est différent du compte authentifié.

begin;

alter policy "fracture endgame owner update"
  on public.fracture_endgame_reports
  to authenticated
  using (owner_user_id = (select auth.uid()))
  with check (
    owner_user_id = (select auth.uid())
    and exists (
      select 1 from public.fracture_parties p
      where p.id = fracture_endgame_reports.party_id
        and p.owner_user_id = (select auth.uid())
    )
  );

alter policy "fracture docs own update"
  on public.fracture_player_documents
  to authenticated
  using (user_id = (select auth.uid()))
  with check (
    user_id = (select auth.uid())
    and sinjira_rls_internal.is_fracture_party_member(
      party_id, (select auth.uid())
    )
  );

commit;
