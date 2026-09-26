-- SINJIRA™ V25 — fin de visibilité de supervision à la majorité.
-- Un lien historique peut rester stocké pour intégrité/audit privé, mais lorsqu'un
-- ancien mineur devient adulte, l'ancien tuteur ne doit plus pouvoir le lire.
-- La personne concernée conserve l'accès à son propre lien afin de pouvoir le nettoyer.

create or replace function public.sinjira_can_read_guardian_link(p_link_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public
as $$
  select coalesce((
    select case
      when auth.uid()=g.minor_user_id then true
      when auth.uid()=g.guardian_user_id
        then public.sinjira_age_band(g.minor_user_id) in (
          'child','child_pending','youth','youth_pending'
        )
      else false
    end
    from public.guardian_links g
    where g.id=p_link_id
  ),false);
$$;

revoke all on function public.sinjira_can_read_guardian_link(uuid)
from public,anon,authenticated;
grant execute on function public.sinjira_can_read_guardian_link(uuid)
to authenticated;

drop policy if exists guardian_read_parties on public.guardian_links;
drop policy if exists guardian_read_parties_age_bounded on public.guardian_links;

create policy guardian_read_parties_age_bounded
on public.guardian_links
for select
to authenticated
using (public.sinjira_can_read_guardian_link(id));

comment on function public.sinjira_can_read_guardian_link(uuid) is
  'V25 self-only par lien: le mineur/propriétaire voit son historique; le tuteur ne voit le lien que tant que le compte concerné est sous 18 ans.';
comment on policy guardian_read_parties_age_bounded on public.guardian_links is
  'V25: supprime automatiquement la visibilité tuteur au passage du compte lié à adult, sans supprimer l historique privé du compte concerné.';
