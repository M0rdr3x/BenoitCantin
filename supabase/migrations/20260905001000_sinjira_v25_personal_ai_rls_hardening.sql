-- SINJIRA V25 — défense en profondeur RLS pour Mon IA
-- Les privilèges directs restent révoqués; RLS ajoute une deuxième barrière cohérente
-- avec le contrat Supabase global et le coffre des consciences.

begin;

alter table private.personal_ai_settings enable row level security;
alter table private.personal_ai_source_permissions enable row level security;
alter table private.personal_ai_audit enable row level security;

-- Aucune policy client n'est créée : les tables restent inaccessibles directement.
-- Les RPC SECURITY DEFINER serveur demeurent la seule voie d'accès prévue.

commit;
