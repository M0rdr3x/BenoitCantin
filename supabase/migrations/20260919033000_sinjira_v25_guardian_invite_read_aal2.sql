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
);

revoke all on table public.guardian_signup_invites from anon;
grant select on table public.guardian_signup_invites to authenticated;

comment on policy guardian_signup_invites_own_aal2
on public.guardian_signup_invites is
  'V25: un tuteur ne peut relire ses codes parentaux qu en session AAL2; RLS self-only + step-up.';
