-- SINJIRA V25 — performance de l'audit privé Mon IA
-- L'advisor Supabase signale la FK personal_ai_audit.user_id sans index couvrant.
-- Cet index porte uniquement sur l'identifiant technique du propriétaire; aucun contenu
-- de prompt, réponse, résumé ou source n'est indexé.

begin;

create index if not exists personal_ai_audit_user_idx
  on private.personal_ai_audit(user_id);

comment on index private.personal_ai_audit_user_idx is
  'Index couvrant la FK user_id de l audit minimal Mon IA; aucun contenu conversationnel ou intime n est stocké ni indexé.';

commit;
