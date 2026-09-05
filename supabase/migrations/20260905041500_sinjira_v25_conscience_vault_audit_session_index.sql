-- SINJIRA™ V25 — suivi performance du Registre personnel
-- L'advisor Supabase signale la FK conscience_vault_audit.session_id sans index couvrant.
-- Cet index ne change aucun privilège ni contenu; il évite un scan inutile lors des opérations
-- liées aux sessions du coffre, notamment la maintenance de la FK.

begin;

create index if not exists conscience_vault_audit_session_idx
  on private.conscience_vault_audit(session_id)
  where session_id is not null;

comment on index private.conscience_vault_audit_session_idx is
  'Index couvrant la FK session_id du journal de métadonnées du coffre; aucun contenu intime indexé.';

commit;
