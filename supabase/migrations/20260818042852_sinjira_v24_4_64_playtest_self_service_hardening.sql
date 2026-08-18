revoke all on table public.playtests from public, anon, authenticated;
grant select on table public.playtests to authenticated;
grant select, insert, update, delete on table public.playtests to service_role;

revoke all on table public.playtest_participants from public, anon, authenticated;
grant select on table public.playtest_participants to authenticated;
grant insert (playtest_id, user_id, status, application_message) on table public.playtest_participants to authenticated;
grant update (status) on table public.playtest_participants to authenticated;
grant select, insert, update, delete on table public.playtest_participants to service_role;

drop policy if exists playtests_read_authorized on public.playtests;
create policy playtests_read_authorized
on public.playtests
for select
to authenticated
using (
  is_sinjira_admin((select auth.uid()))
  or exists (
    select 1
    from public.playtest_participants pp
    where pp.playtest_id = playtests.id
      and pp.user_id = (select auth.uid())
  )
  or (
    status in ('open','active')
    and private.project_access_rank(project_id, (select auth.uid())) >= case required_access
      when 'tester' then 30
      when 'player' then 20
      else 10
    end
  )
);

drop policy if exists playtest_participants_apply on public.playtest_participants;
create policy playtest_participants_apply
on public.playtest_participants
for insert
to authenticated
with check (
  (select auth.uid()) = user_id
  and status = 'applied'
  and exists (
    select 1
    from public.playtests p
    where p.id = playtest_participants.playtest_id
      and p.status = 'open'
      and private.project_access_rank(p.project_id, (select auth.uid())) >= case p.required_access
        when 'tester' then 30
        when 'player' then 20
        else 10
      end
  )
);

drop policy if exists playtest_participants_withdraw_own on public.playtest_participants;
create policy playtest_participants_withdraw_own
on public.playtest_participants
for update
to authenticated
using (
  (select auth.uid()) = user_id
  and status in ('invited','applied','approved')
)
with check (
  (select auth.uid()) = user_id
  and status = 'withdrawn'
);
