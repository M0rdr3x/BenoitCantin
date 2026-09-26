-- SINJIRA™ V25 — fin de visibilité des invitations parentales consommées à la majorité.
-- Un code non consommé appartient au tuteur et reste lisible sous AAL2.
-- Une invitation consommée liée à un ancien mineur ne doit plus rester visible
-- au tuteur lorsque ce compte devient adulte.

drop policy if exists guardian_signup_invites_own_aal2
on public.guardian_signup_invites;

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

comment on policy guardian_signup_invites_own_aal2
on public.guardian_signup_invites is
  'V25: AAL2 self-only; une invitation consommée n est lisible que tant que le guardian_link correspondant reste visible, donc jamais après la majorité du compte lié.';
