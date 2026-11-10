-- CANDIDAT EXCLUSIVEMENT : ne PAS déplacer vers supabase/migrations sans revue
-- indépendante, tests PostgreSQL et approbation du ledger de production.
--
-- Exécution RPC par le serveur Supabase (service_role) seulement.
-- IMPORTANT : le client Edge valide le JWT utilisateur + l'admin + l'AAL2
-- AVANT d'appeler cette RPC avec la clé serveur. Cette RPC vérifie à nouveau
-- l'appartenance à la liste d'administrateurs; elle ne remplace pas l'AAL2 Edge.
-- AUCUN accès EXECUTE pour PUBLIC, anon ou authenticated.
--
-- Chaque appel de fonction PL/pgSQL est exécuté dans une transaction unique.
-- Une exception lors de l'une des écritures annule toutes les autres écritures.
create or replace function private.sinjira_admin_moderate_atomic(
  p_admin_id uuid,
  p_report_id uuid,
  p_action text,
  p_policy_rule text default null,
  p_statement text default null,
  p_urgency text default 'standard',
  p_days integer default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_report public.social_reports%rowtype;
  v_subject uuid;
  v_target_id uuid;
  v_network text;
  v_type text;
  v_target_snapshot jsonb;
  v_rule text;
  v_statement text;
  v_days integer;
  v_ends_at timestamptz;
  v_decision_id uuid;
  v_closed uuid;
  v_previous_until timestamptz;
  v_existing_suspension boolean;
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role'
     or not coalesce(public.is_sinjira_admin(p_admin_id),false) then
    raise exception 'ADMIN_REQUIRED';
  end if;

  if p_report_id is null or p_action not in
     ('resolve_report','hide_content','suspend_social') then
    raise exception 'INVALID_MODERATION_INPUT';
  end if;

  -- Sérialise les opérations concurrentes sur un même signalement.
  select * into v_report
  from public.social_reports
  where id=p_report_id
  for update;
  if not found or v_report.status <> 'open' then
    raise exception 'REPORT_NOT_OPEN';
  end if;

  if p_action='resolve_report' then
    update public.social_reports
    set status='resolved',reviewed_at=now(),reviewed_by=p_admin_id
    where id=v_report.id and status='open'
    returning id into v_closed;
    if v_closed is null then raise exception 'REPORT_NOT_OPEN'; end if;
    return pg_catalog.jsonb_build_object('ok',true,'resolved',true,'report_id',v_report.id);
  end if;

  v_rule:=pg_catalog.btrim(coalesce(p_policy_rule,''));
  v_statement:=pg_catalog.btrim(coalesce(p_statement,''));
  if pg_catalog.char_length(v_rule) not between 3 and 240
     or pg_catalog.char_length(v_statement) not between 20 and 4000
     or p_urgency not in ('standard','urgent_harm','illegal_content') then
    raise exception 'INVALID_MODERATION_INPUT';
  end if;

  v_target_id:=v_report.target_id;
  v_network:=v_report.network;
  v_type:=v_report.target_type;

  -- Source Rencontres : le profil est résolu uniquement dans la base privée.
  -- Une identité déclarée dans le JSON de signalement reste une donnée non
  -- fiable; vérifier sa forme avant de la convertir en UUID.
  if v_report.snapshot->>'source'='dating' then
    if p_action='hide_content' then raise exception 'CONTENT_TARGET_NOT_REVERSIBLE'; end if;
    if coalesce(v_report.snapshot->>'dating_profile_id','')<>'' then
      if (v_report.snapshot->>'dating_profile_id') !~
         '^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$' then
        raise exception 'INVALID_MODERATION_TARGET';
      end if;
      v_target_id:=(v_report.snapshot->>'dating_profile_id')::uuid;
    end if;
    v_network:='dating';
    v_type:='account';
    select d.user_id into v_subject from public.dating_profiles d where d.id=v_target_id;
  elsif v_report.network='real' then
    if v_report.target_type='post' then
      select p.user_id,to_jsonb(p) into v_subject,v_target_snapshot
      from public.social_real_posts p where p.id=v_target_id;
    elsif v_report.target_type='comment' then
      select c.user_id,to_jsonb(c) into v_subject,v_target_snapshot
      from public.social_real_comments c where c.id=v_target_id;
    elsif v_report.target_type='message' then
      select m.sender_user_id,to_jsonb(m) into v_subject,v_target_snapshot
      from public.social_real_messages m where m.id=v_target_id;
    elsif v_report.target_type='profile' then
      select p.user_id into v_subject
      from public.social_profiles p where p.user_id=v_target_id;
    end if;
  elsif v_report.network='character' then
    if v_report.target_type='post' then
      select p.user_id,to_jsonb(p) into v_subject,v_target_snapshot
      from public.social_character_posts p where p.id=v_target_id;
    elsif v_report.target_type='comment' then
      select c.user_id,to_jsonb(c) into v_subject,v_target_snapshot
      from public.social_character_comments c where c.id=v_target_id;
    elsif v_report.target_type='message' then
      select m.sender_user_id,to_jsonb(m) into v_subject,v_target_snapshot
      from public.social_character_messages m where m.id=v_target_id;
    elsif v_report.target_type='profile' then
      select p.user_id into v_subject
      from public.character_social_profiles p where p.character_id=v_target_id;
    end if;
  else
    -- Aucun chemin générique pour un futur réseau inconnu (ex. live V25).
    raise exception 'INVALID_MODERATION_TARGET';
  end if;

  if v_subject is null then raise exception 'TARGET_USER_NOT_FOUND'; end if;
  if p_action='hide_content' and v_type not in ('post','comment','message') then
    raise exception 'CONTENT_TARGET_NOT_REVERSIBLE';
  end if;

  -- Le verrou sur l'utilisateur sérialise aussi les suspensions de plusieurs
  -- signalements distincts visant le même compte.
  perform u.id from auth.users u where u.id=v_subject for update;
  if not found then raise exception 'TARGET_USER_NOT_FOUND'; end if;

  if p_action='suspend_social' then
    v_days:=coalesce(p_days,7);
    if v_days not between 1 and 365 then raise exception 'INVALID_SUSPENSION_DURATION'; end if;
    v_ends_at:=now()+pg_catalog.make_interval(days=>v_days);
    v_existing_suspension:=false;
    select true,s.until_at into v_existing_suspension,v_previous_until
    from public.social_suspensions s
    where s.user_id=v_subject
    for update;
    if v_existing_suspension and (v_previous_until is null or v_previous_until>now()) then
      raise exception 'SUSPENSION_ALREADY_ACTIVE';
    end if;
  end if;

  insert into private.moderation_decisions(
    subject_user_id,report_id,network,target_type,target_id,action,status,
    policy_rule,statement_of_reasons,evidence_snapshot,urgency,
    decision_source,decided_by,ends_at
  ) values (
    v_subject,v_report.id,v_network,v_type,v_target_id,p_action,'active',
    v_rule,v_statement,pg_catalog.jsonb_build_object(
      'report_snapshot',v_report.snapshot,
      'target_snapshot',v_target_snapshot,
      'report_reason',v_report.reason,
      'report_created_at',v_report.created_at
    ),p_urgency,'human_admin',p_admin_id,v_ends_at
  ) returning id into v_decision_id;

  if p_action='suspend_social' then
    insert into public.social_suspensions(
      user_id,reason,until_at,created_by,moderation_decision_id
    ) values(v_subject,v_statement,v_ends_at,p_admin_id,v_decision_id)
    on conflict(user_id) do update
    set reason=excluded.reason,until_at=excluded.until_at,
        created_by=excluded.created_by,moderation_decision_id=excluded.moderation_decision_id;
  end if;

  update public.social_reports
  set status='resolved',reviewed_at=now(),reviewed_by=p_admin_id
  where id=v_report.id and status='open'
  returning id into v_closed;
  if v_closed is null then raise exception 'REPORT_NOT_OPEN'; end if;

  -- Une notification échouée provoque le rollback de toute la sanction.
  insert into public.user_notifications(
    user_id,notification_type,title,body,
    related_entity_type,related_entity_id,action_path
  ) values (
    v_subject,'moderation_decision',
    case when p_action='hide_content'
      then 'Décision de modération — contenu masqué'
      else 'Décision de modération — suspension sociale' end,
    pg_catalog.left(v_statement,1000),
    'moderation_decision',v_decision_id,'/compte/moderation.html'
  );

  return pg_catalog.jsonb_build_object(
    'ok',true,'decision_id',v_decision_id,
    'report_id',v_report.id,'until_at',v_ends_at,'reversible',true
  );
end;
$function$;

create or replace function private.sinjira_admin_review_appeal_atomic(
  p_admin_id uuid,
  p_appeal_id uuid,
  p_outcome text,
  p_review_reason text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_appeal private.moderation_appeals%rowtype;
  v_decision private.moderation_decisions%rowtype;
  v_reason text;
  v_now timestamptz:=now();
  v_closed uuid;
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role'
     or not coalesce(public.is_sinjira_admin(p_admin_id),false) then
    raise exception 'ADMIN_REQUIRED';
  end if;
  v_reason:=pg_catalog.btrim(coalesce(p_review_reason,''));
  if p_appeal_id is null or p_outcome not in ('upheld','reversed')
     or pg_catalog.char_length(v_reason) not between 20 and 4000 then
    raise exception 'INVALID_APPEAL_REVIEW';
  end if;

  -- Lock ordre : appel -> décision -> utilisateur, pour empêcher deux
  -- réviseurs de statuer simultanément sur le même dossier.
  select * into v_appeal from private.moderation_appeals
  where id=p_appeal_id for update;
  if not found or v_appeal.status<>'pending' then
    raise exception 'APPEAL_NOT_PENDING';
  end if;
  select * into v_decision from private.moderation_decisions
  where id=v_appeal.decision_id for update;
  if not found or v_decision.status<>'active' then
    raise exception 'DECISION_NOT_ACTIVE';
  end if;

  if v_decision.subject_user_id is not null then
    perform u.id from auth.users u where u.id=v_decision.subject_user_id for update;
    -- Un compte supprimé reste révisable : le dossier privé est conservé.
  end if;

  if p_outcome='reversed' then
    update private.moderation_decisions
    set status='reversed',reversed_at=v_now,reversed_by=p_admin_id,
        reversal_reason=v_reason,updated_at=v_now
    where id=v_decision.id and status='active'
    returning id into v_closed;
    if v_closed is null then raise exception 'DECISION_NOT_ACTIVE'; end if;
    if v_decision.action='suspend_social' then
      -- Ne jamais supprimer une nouvelle suspension d'une autre décision.
      delete from public.social_suspensions
      where moderation_decision_id=v_decision.id;
    end if;
  end if;

  update private.moderation_appeals
  set status=p_outcome,reviewed_by=p_admin_id,reviewed_at=v_now,
      review_reason=v_reason,updated_at=v_now
  where id=v_appeal.id and status='pending'
  returning id into v_closed;
  if v_closed is null then raise exception 'APPEAL_NOT_PENDING'; end if;

  if v_appeal.appellant_user_id is not null then
    insert into public.user_notifications(
      user_id,notification_type,title,body,
      related_entity_type,related_entity_id,action_path
    ) values (
      v_appeal.appellant_user_id,'moderation_decision',
      case when p_outcome='reversed'
        then 'Appel accepté — décision renversée'
        else 'Appel examiné — décision maintenue' end,
      pg_catalog.left(v_reason,1000),
      'moderation_decision',v_decision.id,'/compte/moderation.html'
    );
  end if;

  return pg_catalog.jsonb_build_object(
    'ok',true,'outcome',p_outcome,'decision_id',v_decision.id,'appeal_id',v_appeal.id
  );
end;
$function$;

-- Une fonction SECURITY DEFINER nouvellement créée hérite d'EXECUTE PUBLIC :
-- retirer explicitement cet accès AVANT d'autoriser le rôle serveur.
revoke all on function private.sinjira_admin_moderate_atomic(
  uuid,uuid,text,text,text,text,integer
) from public,anon,authenticated;
revoke all on function private.sinjira_admin_review_appeal_atomic(
  uuid,uuid,text,text
) from public,anon,authenticated;

grant usage on schema private to service_role;
grant execute on function private.sinjira_admin_moderate_atomic(
  uuid,uuid,text,text,text,text,integer
) to service_role;
grant execute on function private.sinjira_admin_review_appeal_atomic(
  uuid,uuid,text,text
) to service_role;

comment on function private.sinjira_admin_moderate_atomic(
  uuid,uuid,text,text,text,text,integer
) is 'Candidat non déployé : transaction de modération avec verrou rapport/cible, notification et rollback. service_role uniquement, AAL2 contrôlé au niveau Edge.';
comment on function private.sinjira_admin_review_appeal_atomic(
  uuid,uuid,text,text
) is 'Candidat non déployé : transaction de révision humaine avec lock appel/décision et rollback. service_role uniquement.';
