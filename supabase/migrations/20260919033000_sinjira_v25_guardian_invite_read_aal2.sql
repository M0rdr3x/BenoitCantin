-- SINJIRA™ V25 — lecture des codes parentaux réservée à AAL2.
-- La création est déjà AAL2. La confidentialité doit rester équivalente à la lecture :
-- une session AAL1 ne doit jamais pouvoir relire un code encore valide.

drop policy if exists guardian_signup_invites_own on public.guardian_signup_invites;
drop policy if exists guardian_signup_invites_own_aal2 on public.guardian_signup_invites;

create policy guardian_signup_invites_own_aal2
on public.guardian_signup_invites
for select
to authenticated
using (
  (select auth.uid())=guardian_user_id
  and coalesce(auth.jwt()->>'aal','aal1')='aal2'
  and (
    minor_user_id is null
    or exists(
      select 1
      from public.guardian_links g
      where g.guardian_user_id=(select auth.uid())
        and g.minor_user_id=guardian_signup_invites.minor_user_id
    )
  )
);

revoke all on table public.guardian_signup_invites from anon;
grant select on table public.guardian_signup_invites to authenticated;

comment on policy guardian_signup_invites_own_aal2
on public.guardian_signup_invites is
  'V25: AAL2 self-only; un code non consommé reste lisible au tuteur, une invitation consommée reste lisible uniquement tant que le guardian_link associé est encore visible avant la majorité.';
