-- SINJIRA™ V24.4.43 — réduit les privilèges de structure inutiles des rôles API.
-- RLS protège les lignes, mais TRUNCATE n'est pas une opération ligne-par-ligne.
-- Les visiteurs et membres n'ont jamais besoin de TRUNCATE, TRIGGER ou REFERENCES via l'API.

revoke truncate, trigger, references on all tables in schema public from anon, authenticated;

alter default privileges in schema public
  revoke truncate, trigger, references on tables from anon, authenticated;
