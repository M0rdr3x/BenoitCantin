-- SINJIRA™ V24.4.12 — optimisation RLS des parcours cœur
-- Même autorisation fonctionnelle, moins de politiques permissives concurrentes et auth.uid() initialisé une seule fois.

-- PROJETS : conserver la lecture publique, fusionner lecture membre + admin.
drop policy if exists admin_read_all_projects on public.projects;
drop policy if exists projects_read on public.projects;
drop policy if exists projects_public_read on public.projects;
drop policy if exists projects_authenticated_read on public.projects;
create policy projects_public_read on public.projects for select to anon
using (status<>'draft' and visibility='public');
create policy projects_authenticated_read on public.projects for select to authenticated
using (
  public.is_sinjira_admin((select auth.uid()))
  or (
    status<>'draft' and (
      visibility in ('public','account')
      or private.project_access_rank(id,(select auth.uid()))>=20
    )
  )
);

-- SESSIONS DE JEU : propriétaire CRUD, admin lecture.
drop policy if exists sessions_all_own on public.game_sessions;
drop policy if exists admin_read_all_game_sessions on public.game_sessions;
drop policy if exists sessions_read_authorized on public.game_sessions;
drop policy if exists sessions_insert_own on public.game_sessions;
drop policy if exists sessions_update_own on public.game_sessions;
drop policy if exists sessions_delete_own on public.game_sessions;
create policy sessions_read_authorized on public.game_sessions for select to authenticated
using ((select auth.uid())=user_id or public.is_sinjira_admin((select auth.uid())));
create policy sessions_insert_own on public.game_sessions for insert to authenticated
with check ((select auth.uid())=user_id);
create policy sessions_update_own on public.game_sessions for update to authenticated
using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
create policy sessions_delete_own on public.game_sessions for delete to authenticated
using ((select auth.uid())=user_id);

-- FEUILLES JOUEUR.
drop policy if exists sheets_all_own on public.player_sheets;
create policy sheets_all_own on public.player_sheets for all to authenticated
using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);

-- CONSENTEMENTS RECHERCHE.
drop policy if exists consent_insert_own on public.research_consents;
drop policy if exists consent_select_own on public.research_consents;
drop policy if exists consent_update_own on public.research_consents;
drop policy if exists admin_read_all_research_consents on public.research_consents;
drop policy if exists consent_read_authorized on public.research_consents;
create policy consent_insert_own on public.research_consents for insert to authenticated
with check ((select auth.uid())=user_id);
create policy consent_read_authorized on public.research_consents for select to authenticated
using ((select auth.uid())=user_id or public.is_sinjira_admin((select auth.uid())));
create policy consent_update_own on public.research_consents for update to authenticated
using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);

-- FEEDBACK DE SESSION.
drop policy if exists feedback_all_own on public.session_feedback;
create policy feedback_all_own on public.session_feedback for all to authenticated
using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);

-- RAPPORTS JOUEUR.
drop policy if exists reports_select_own on public.player_reports;
drop policy if exists admin_read_all_player_reports on public.player_reports;
drop policy if exists reports_read_authorized on public.player_reports;
create policy reports_read_authorized on public.player_reports for select to authenticated
using ((select auth.uid())=user_id or public.is_sinjira_admin((select auth.uid())));

-- ACCÈS PROJET.
drop policy if exists access_select_own on public.project_access;
drop policy if exists admin_read_all_project_access on public.project_access;
drop policy if exists access_read_authorized on public.project_access;
create policy access_read_authorized on public.project_access for select to authenticated
using ((select auth.uid())=user_id or public.is_sinjira_admin((select auth.uid())));

-- DEMANDES D'ACCÈS.
drop policy if exists requests_insert_own on public.access_requests;
drop policy if exists requests_select_own on public.access_requests;
drop policy if exists admin_read_all_access_requests on public.access_requests;
drop policy if exists requests_read_authorized on public.access_requests;
create policy requests_insert_own on public.access_requests for insert to authenticated
with check ((select auth.uid())=user_id and status='pending');
create policy requests_read_authorized on public.access_requests for select to authenticated
using ((select auth.uid())=user_id or public.is_sinjira_admin((select auth.uid())));

-- DOCUMENTS : politique publique séparée de la politique membre/admin.
drop policy if exists documents_read_by_access on public.documents;
drop policy if exists admin_read_all_documents on public.documents;
drop policy if exists documents_anon_read on public.documents;
drop policy if exists documents_authenticated_read on public.documents;
create policy documents_anon_read on public.documents for select to anon
using (status='approved' and private.project_access_rank(project_id,null)>=public.document_access_rank(access_level));
create policy documents_authenticated_read on public.documents for select to authenticated
using (
  public.is_sinjira_admin((select auth.uid()))
  or (status='approved' and private.project_access_rank(project_id,(select auth.uid()))>=public.document_access_rank(access_level))
);

-- PLAYTESTS.
drop policy if exists playtests_read on public.playtests;
drop policy if exists admin_read_all_playtests on public.playtests;
drop policy if exists playtests_read_authorized on public.playtests;
create policy playtests_read_authorized on public.playtests for select to authenticated
using (
  public.is_sinjira_admin((select auth.uid()))
  or (status in ('open','active') and private.project_access_rank(project_id,(select auth.uid()))>=10)
);

drop policy if exists playtest_participants_apply on public.playtest_participants;
drop policy if exists playtest_participants_select_own on public.playtest_participants;
drop policy if exists admin_read_all_playtest_participants on public.playtest_participants;
drop policy if exists playtest_participants_read_authorized on public.playtest_participants;
create policy playtest_participants_apply on public.playtest_participants for insert to authenticated
with check ((select auth.uid())=user_id and status='applied');
create policy playtest_participants_read_authorized on public.playtest_participants for select to authenticated
using ((select auth.uid())=user_id or public.is_sinjira_admin((select auth.uid())));

-- EXTENSIONS : public séparé de l'admin pour éviter le doublon authenticated.
drop policy if exists extensions_public on public.extensions;
drop policy if exists admin_read_all_extensions on public.extensions;
drop policy if exists extensions_anon_public on public.extensions;
drop policy if exists extensions_authenticated_read on public.extensions;
create policy extensions_anon_public on public.extensions for select to anon
using (is_public=true and status in ('approved','released'));
create policy extensions_authenticated_read on public.extensions for select to authenticated
using (public.is_sinjira_admin((select auth.uid())) or (is_public=true and status in ('approved','released')));

-- REÇUS DE CONTRIBUTION.
drop policy if exists receipts_select_own on public.contribution_receipts;
drop policy if exists admin_read_all_contribution_receipts on public.contribution_receipts;
drop policy if exists receipts_read_authorized on public.contribution_receipts;
create policy receipts_read_authorized on public.contribution_receipts for select to authenticated
using ((select auth.uid())=user_id or public.is_sinjira_admin((select auth.uid())));

-- FEUILLES DE FIN DE PARTIE : propriétaire CRUD, admin lecture.
drop policy if exists endgame_all_own on public.endgame_sheets;
drop policy if exists admin_read_all_endgame_sheets on public.endgame_sheets;
drop policy if exists endgame_read_authorized on public.endgame_sheets;
drop policy if exists endgame_insert_own on public.endgame_sheets;
drop policy if exists endgame_update_own on public.endgame_sheets;
drop policy if exists endgame_delete_own on public.endgame_sheets;
create policy endgame_read_authorized on public.endgame_sheets for select to authenticated
using ((select auth.uid())=user_id or public.is_sinjira_admin((select auth.uid())));
create policy endgame_insert_own on public.endgame_sheets for insert to authenticated with check ((select auth.uid())=user_id);
create policy endgame_update_own on public.endgame_sheets for update to authenticated using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
create policy endgame_delete_own on public.endgame_sheets for delete to authenticated using ((select auth.uid())=user_id);

-- DOCUMENTS PRIVÉS FRACTURE.
drop policy if exists "fracture docs own read" on public.fracture_player_documents;
drop policy if exists "fracture docs own insert" on public.fracture_player_documents;
drop policy if exists "fracture docs own update" on public.fracture_player_documents;
drop policy if exists "fracture docs own delete" on public.fracture_player_documents;
create policy "fracture docs own read" on public.fracture_player_documents for select to authenticated
using (user_id=(select auth.uid()));
create policy "fracture docs own insert" on public.fracture_player_documents for insert to authenticated
with check (user_id=(select auth.uid()) and public.is_fracture_party_member(party_id,(select auth.uid())));
create policy "fracture docs own update" on public.fracture_player_documents for update to authenticated
using (user_id=(select auth.uid())) with check (user_id=(select auth.uid()));
create policy "fracture docs own delete" on public.fracture_player_documents for delete to authenticated
using (user_id=(select auth.uid()));

-- RAPPORT FINAL FRACTURE : membre/admin en une seule lecture.
drop policy if exists admin_read_all_fracture_endgame on public.fracture_endgame_reports;
drop policy if exists "fracture endgame members read" on public.fracture_endgame_reports;
drop policy if exists fracture_endgame_read_authorized on public.fracture_endgame_reports;
create policy fracture_endgame_read_authorized on public.fracture_endgame_reports for select to authenticated
using (public.is_sinjira_admin((select auth.uid())) or public.is_fracture_party_member(party_id,(select auth.uid())));
drop policy if exists "fracture endgame owner insert" on public.fracture_endgame_reports;
create policy "fracture endgame owner insert" on public.fracture_endgame_reports for insert to authenticated
with check (
  owner_user_id=(select auth.uid())
  and exists(select 1 from public.fracture_parties p where p.id=fracture_endgame_reports.party_id and p.owner_user_id=(select auth.uid()))
);
drop policy if exists "fracture endgame owner update" on public.fracture_endgame_reports;
create policy "fracture endgame owner update" on public.fracture_endgame_reports for update to authenticated
using (owner_user_id=(select auth.uid())) with check (owner_user_id=(select auth.uid()));

-- SOUMISSIONS PERSONNAGE LECTEUR.
drop policy if exists reader_character_submissions_insert_own on public.reader_character_submissions;
create policy reader_character_submissions_insert_own on public.reader_character_submissions for insert to authenticated
with check (user_id=(select auth.uid()));
drop policy if exists reader_character_submissions_admin_read on public.reader_character_submissions;
create policy reader_character_submissions_admin_read on public.reader_character_submissions for select to authenticated
using (public.is_sinjira_admin((select auth.uid())));
