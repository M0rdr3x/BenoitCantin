update public.characters c
set public_description='Une presence reservee, inventive et tenace. Seth ne confond pas l echec d une tentative avec celui du but : il constate, cherche la cause, change de methode et continue tant qu une piste raisonnable existe. Il accorde sa confiance lentement, privilegie les liens sinceres et durables, et prefere etre decouvert a travers ce qu il construit plutot que chercher la lumiere.',
    updated_at=now()
where c.status<>'archived'
  and exists(select 1 from public.internal_admin_users a where a.user_id=c.user_id and a.role='owner');

update public.character_social_profiles csp
set public_description=c.public_description,
    public_name=c.public_name,
    portrait_path=c.portrait_path,
    updated_at=now()
from public.characters c
where csp.character_id=c.id
  and c.status<>'archived'
  and exists(select 1 from public.internal_admin_users a where a.user_id=c.user_id and a.role='owner');

update public.character_submissions cs
set source_payload=coalesce(cs.source_payload,'{}'::jsonb)-'compte_pseudo',
    updated_at=now()
where cs.status='assigned'
  and exists(select 1 from public.internal_admin_users a where a.user_id=cs.user_id and a.role='owner');
