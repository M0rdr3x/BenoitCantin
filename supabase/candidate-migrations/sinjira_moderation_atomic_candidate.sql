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

  if p_report_id is null or coalesce(p_action,'') not in
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
     or coalesce(p_urgency,'') not in ('standard','urgent_harm','illegal_content') then
    raise exception 'INVALID_MODERATION_INPUT';
  end if;

  v_target_id:=v_report.target_id;
  v_network:=v_report.network;
  v_type:=v_report.target_type;

  -- Le snapshot du signalement ne prouve PAS la provenance du dossier.
  -- Un signalant pourrait y placer source=dating et dating_profile_id
  -- pour détourner une sanction vers un autre compte. Tant qu'aucune
  -- relation SQL canonique et vérifiable du dossier Rencontres n'existe,
  -- interdire toute sanction basée sur ce chemin non fiable.
  if v_report.snapshot->>'source'='dating' then
    raise exception 'UNVERIFIED_DATING_PROVENANCE';
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
  if p_appeal_id is null or coalesce(p_outcome,'') not in ('upheld','reversed')
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

-- Lecture privée des appels, SANS ouvrir SELECT aux tables privées :
-- remplace les lectures directes Edge qui n'ont pas d'ACL service_role.
create or replace function private.sinjira_admin_appeals_overview(
  p_admin_id uuid, p_limit integer default 300
)
returns jsonb language plpgsql security definer set search_path=''
as $function$
declare
  v_count bigint;
  v_rows jsonb;
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role'
     or not coalesce(public.is_sinjira_admin(p_admin_id),false) then
    raise exception 'ADMIN_REQUIRED';
  end if;
  if p_limit is null or p_limit<1 or p_limit>300 then
    raise exception 'INVALID_APPEALS_LIMIT';
  end if;

  select count(*) into v_count
  from private.moderation_appeals a where a.status='pending';

  select coalesce(pg_catalog.jsonb_agg(q.payload order by q.submitted_at),'[]'::jsonb)
  into v_rows
  from (
    select a.submitted_at,
      (to_jsonb(a) || pg_catalog.jsonb_build_object('decision',
        pg_catalog.jsonb_build_object(
          'id',d.id,'subject_user_id',d.subject_user_id,
          'network',d.network,'target_type',d.target_type,
          'target_id',d.target_id,'action',d.action,'status',d.status,
          'policy_rule',d.policy_rule,
          'statement_of_reasons',d.statement_of_reasons,
          'urgency',d.urgency,'starts_at',d.starts_at,
          'ends_at',d.ends_at,'appeal_deadline',d.appeal_deadline,
          'decided_at',d.decided_at
        )
      )) as payload
    from private.moderation_appeals a
    join private.moderation_decisions d on d.id=a.decision_id
    where a.status='pending'
    order by a.submitted_at,a.id
    limit p_limit
  ) q;
  return pg_catalog.jsonb_build_object('pending_count',v_count,'appeals',v_rows);
end;
$function$;

revoke all on function private.sinjira_admin_appeals_overview(uuid,integer)
from public,anon,authenticated;
grant execute on function private.sinjira_admin_appeals_overview(uuid,integer)
to service_role;

-- Points d'entrée PostgREST : schema public exposé, mais EXECUTE UNIQUEMENT
-- au rôle serveur. Le wrapper SECURITY INVOKER ne contourne aucune ACL.
-- La fonction SQL privée garde le verrou transactionnel et les contrôles
-- indépendants du navigateur / des paramètres d'administration.
create or replace function public.sinjira_admin_moderate_atomic(
  p_admin_id uuid, p_report_id uuid, p_action text,
  p_policy_rule text default null, p_statement text default null,
  p_urgency text default 'standard', p_days integer default null
)
returns jsonb
language sql
security invoker
set search_path = ''
as $public_rpc$
  select private.sinjira_admin_moderate_atomic(
    p_admin_id,p_report_id,p_action,
    p_policy_rule,p_statement,p_urgency,p_days
  );
$public_rpc$;

create or replace function public.sinjira_admin_review_appeal_atomic(
  p_admin_id uuid, p_appeal_id uuid,
  p_outcome text, p_review_reason text
)
returns jsonb
language sql
security invoker
set search_path = ''
as $public_rpc$
  select private.sinjira_admin_review_appeal_atomic(
    p_admin_id,p_appeal_id,p_outcome,p_review_reason
  );
$public_rpc$;

create or replace function public.sinjira_admin_appeals_overview(
  p_admin_id uuid, p_limit integer default 300
)
returns jsonb language sql security invoker set search_path=''
as $public_rpc$
  select private.sinjira_admin_appeals_overview(p_admin_id,p_limit);
$public_rpc$;

revoke all on function public.sinjira_admin_appeals_overview(uuid,integer)
from public,anon,authenticated;
grant execute on function public.sinjira_admin_appeals_overview(uuid,integer)
to service_role;

revoke all on function public.sinjira_admin_moderate_atomic(
  uuid,uuid,text,text,text,text,integer
) from public,anon,authenticated;
revoke all on function public.sinjira_admin_review_appeal_atomic(
  uuid,uuid,text,text
) from public,anon,authenticated;
grant execute on function public.sinjira_admin_moderate_atomic(
  uuid,uuid,text,text,text,text,integer
) to service_role;
grant execute on function public.sinjira_admin_review_appeal_atomic(
  uuid,uuid,text,text
) to service_role;

comment on function public.sinjira_admin_moderate_atomic(
  uuid,uuid,text,text,text,text,integer
) is 'PostgREST service_role seulement; wrapper invoker du candidat SQL transactionnel.';
comment on function public.sinjira_admin_review_appeal_atomic(
  uuid,uuid,text,text
) is 'PostgREST service_role seulement; wrapper invoker du candidat de révision atomique.';

comment on function private.sinjira_admin_moderate_atomic(
  uuid,uuid,text,text,text,text,integer
) is 'Candidat non déployé : transaction de modération avec verrou rapport/cible, notification et rollback. service_role uniquement, AAL2 contrôlé au niveau Edge.';
comment on function private.sinjira_admin_review_appeal_atomic(
  uuid,uuid,text,text
) is 'Candidat non déployé : transaction de révision humaine avec lock appel/décision et rollback. service_role uniquement.';
