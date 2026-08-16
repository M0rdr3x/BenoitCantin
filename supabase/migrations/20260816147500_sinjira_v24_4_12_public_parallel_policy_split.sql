-- SINJIRA™ V24.4.12 — séparer les lectures publiques des lectures par cohorte.
-- Les visiteurs anonymes ne peuvent appeler aucune RPC de cohorte ; ils voient uniquement audience='all'.

revoke execute on function public.sinjira_my_age_band() from anon;
grant execute on function public.sinjira_my_age_band() to authenticated;

drop policy if exists parallel_stories_public on public.parallel_story_installments;
drop policy if exists parallel_stories_anon_public on public.parallel_story_installments;
drop policy if exists parallel_stories_authenticated on public.parallel_story_installments;

create policy parallel_stories_anon_public
on public.parallel_story_installments
for select to anon
using (
  published_at is not null
  and story_kind='collective'
  and audience='all'
);

create policy parallel_stories_authenticated
on public.parallel_story_installments
for select to authenticated
using (
  published_at is not null and (
    (story_kind='collective' and audience='all')
    or (story_kind='collective' and audience=public.sinjira_my_age_band())
    or (
      story_kind='individual'
      and exists(
        select 1 from public.sinjira_characters c
        where c.id=parallel_story_installments.character_id
          and c.user_id=(select auth.uid())
      )
    )
  )
);

drop policy if exists parallel_cycles_public_read on public.parallel_world_cycles;
drop policy if exists parallel_cycles_anon_public on public.parallel_world_cycles;
drop policy if exists parallel_cycles_authenticated on public.parallel_world_cycles;

create policy parallel_cycles_anon_public
on public.parallel_world_cycles
for select to anon
using (
  (published_at is not null or status='open')
  and audience='all'
);

create policy parallel_cycles_authenticated
on public.parallel_world_cycles
for select to authenticated
using (
  (published_at is not null or status='open')
  and (audience='all' or audience=public.sinjira_my_age_band())
);
