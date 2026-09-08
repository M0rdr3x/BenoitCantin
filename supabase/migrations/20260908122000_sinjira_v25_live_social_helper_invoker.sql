-- SINJIRA V25 — frontière helper RLS « En direct ».
-- Le helper d'adhésion reste self-only mais ne possède aucun privilège SECURITY DEFINER.
-- Il s'exécute avec les droits de l'appelant et reste donc soumis à la RLS de
-- social_live_room_members. Cela respecte le contrat global des helpers publics.

alter function public.social_live_is_room_member(uuid) security invoker;

revoke all on function public.social_live_is_room_member(uuid) from public,anon,authenticated;
grant execute on function public.social_live_is_room_member(uuid) to authenticated,service_role;

comment on function public.social_live_is_room_member(uuid) is
'Helper self-only En direct exécuté en SECURITY INVOKER; la RLS des adhésions reste autoritaire et aucun privilège serveur n est exposé au navigateur.';
