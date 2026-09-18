-- SINJIRA™ V25 — compatibilité du classifieur de contenu avec les bandes âge 11–12.
-- Forward-only : la migration V24.4.82 reste immuable.
-- La garde de messagerie mineur doit reconnaître child/child_pending et échouer fermé
-- pour toute bande non adulte ou inconnue.

create or replace function private.sinjira_content_policy_code(
  p_body text,
  p_actor_user_id uuid,
  p_recipient_user_id uuid default null,
  p_surface text default 'content'
)
returns text
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v text:=lower(coalesce(p_body,''));
  v_actor_band text:=public.sinjira_age_band(p_actor_user_id);
  v_recipient_band text:=case when p_recipient_user_id is null then null else public.sinjira_age_band(p_recipient_user_id) end;
  -- V25 fail-closed: seules les bandes explicitement adultes/mémorialisées
  -- sortent de la garde renforcée. Toute bande mineure, pending, non vérifiée
  -- ou future/inconnue reste protégée.
  v_youth boolean:=coalesce(v_actor_band not in ('adult','memorial'),true)
    or (
      p_recipient_user_id is not null
      and coalesce(v_recipient_band not in ('adult','memorial'),true)
    );
  v_message boolean:=coalesce(p_surface,'') in ('message','dating_message');
  v_external boolean;
  v_commerce boolean;
  v_sexual boolean;
  v_drugs boolean;
begin
  if btrim(v)='' then return null; end if;

  v_external := v ~ '(https?://|www\.|onlyfans\.|fansly\.|telegram|whatsapp|snapchat|discord|instagram|signal app|t\.me/|@[a-z0-9_]{3,}|[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}|[+]?([0-9][ ()\.\-]?){7,}[0-9])';
  v_commerce := v ~ '(je vends|j[’'']?offre|a vendre|à vendre|prix|tarif|paiement|payer pour|paye[- ]?moi|paie[- ]?moi|cash|virement|crypto|abonnement|abonne[- ]?toi|abonnez[- ]?vous|subscribe|subscription|premium|viens en dm|viens en mp|ecris[- ]?moi|écris[- ]?moi|contacte[- ]?moi|commande|livraison|dollars?|euros?|\$|€)';
  v_sexual := v ~ '(prostitut|escort(e|es|ing)?|prox[eé]n[eé]t|pimp|service[s]? sexuel|massage [eé]rotique|sexe contre argent|contenu adulte|contenu sexuel payant|photo[s]? nue[s]?|nude[s]?|sexting|camgirl|camboy|webcam sex|onlyfans|fansly)';
  v_drugs := v ~ '(drogue[s]?|coca[iï]ne|crack|h[eé]ro[iï]ne|fentanyl|m[eé]thamph[eé]tamine|\mmeth\M|mdma|ecstasy|ghb|lsd|k[eé]tamine|opio[iï]de[s]?)';

  -- Toute promotion/vente de contenu sexuel payant ou de services sexuels est interdite.
  if (v ~ '(onlyfans|fansly|contenu adulte|contenu sexuel payant|photo[s]? nue[s]?|nude[s]?|camgirl|camboy|webcam sex)')
     and (v_commerce or v_external) then
    return 'PAID_SEXUAL_CONTENT';
  end if;

  if (v ~ '(prostitut|escort(e|es|ing)?|prox[eé]n[eé]t|pimp|service[s]? sexuel|massage [eé]rotique|sexe contre argent)')
     and (v_commerce or v_external or v ~ 'sexe contre argent') then
    return 'SEXUAL_EXPLOITATION';
  end if;

  -- Vente/traite de personnes : tolérance zéro lorsqu'une intention transactionnelle ou de contact est présente.
  if (v ~ '(traite des personnes|trafic humain|human trafficking|vente de personne|vente de personnes|personne a vendre|personne à vendre|fille a vendre|fille à vendre|femme a vendre|femme à vendre|acheter une personne|acheter une fille|acheter une femme)')
     and (v_commerce or v_external) then
    return 'HUMAN_TRAFFICKING';
  end if;

  -- Le site ne peut pas servir de marché de drogues.
  if v_drugs and v_commerce then
    return 'ILLICIT_DRUG_SALES';
  end if;

  -- Garde renforcée pour toute messagerie impliquant une personne mineure/jeunesse.
  if v_youth and v_message then
    if v_external then
      return 'MINOR_OFF_PLATFORM_CONTACT';
    end if;
    if v_sexual or v ~ '(photo intime|photo[s]? sexy|envoie.*photo|montre[- ]?moi.*corps|rencontre sexuelle|viens chez moi|viens seul|viens seule|garde [cç]a secret|ne dis pas.*parent|ne le dis pas.*parent)' then
      return 'MINOR_SEXUAL_SOLICITATION';
    end if;
    if v ~ '(envoie[- ]?moi.*argent|donne[- ]?moi.*argent|paye[- ]?moi|paie[- ]?moi|carte cadeau|gift card|virement|crypto)' then
      return 'MINOR_FINANCIAL_SOLICITATION';
    end if;
  end if;

  return null;
end;
$$;

revoke all on function private.sinjira_content_policy_code(text,uuid,uuid,text) from public,anon,authenticated;
grant execute on function private.sinjira_content_policy_code(text,uuid,uuid,text) to service_role;

comment on function private.sinjira_content_policy_code(text,uuid,uuid,text) is
'Classifie côté serveur les sollicitations interdites; V25 traite toute bande autre que adult/memorial comme protégée pour la messagerie afin de rester fail-closed.';
