-- V59 : schéma d'accès volontairement FICTIF, laboratoire PostgreSQL local.
-- Utilise les noms et types de colonnes observés en lecture seule dans le
-- catalogue SINJIRA le 10 novembre 2026. Aucune donnée réelle n'est copiée.
\set ON_ERROR_STOP on
DO $guard$
BEGIN
 IF current_database()<>'sinjira_reader_v51_lab' THEN
   RAISE EXCEPTION 'V59: fixture interdite hors base jetable';
 END IF;
END $guard$;

CREATE TABLE public.products(
 id uuid PRIMARY KEY,
 active boolean NOT NULL DEFAULT false
);
CREATE TABLE public.user_entitlements(
 user_id uuid NOT NULL REFERENCES auth.users(id),
 product_id uuid NOT NULL REFERENCES public.products(id),
 PRIMARY KEY(user_id,product_id)
);
ALTER TABLE public.sinjira_novels
 ADD COLUMN status text NOT NULL DEFAULT 'published',
 ADD COLUMN file_ready boolean NOT NULL DEFAULT true,
 ADD COLUMN product_id uuid REFERENCES public.products(id);

-- Mêmes signatures (sans recopier une fonction ni une donnée réelle).
CREATE FUNCTION public.is_sinjira_owner(p_user_id uuid)
RETURNS boolean LANGUAGE sql STABLE SET search_path=''
AS $fn$ SELECT p_user_id='00000000-0000-0000-0000-000000000003'::uuid
 AND p_user_id=auth.uid() $fn$;
CREATE FUNCTION public.is_sinjira_admin(p_user_id uuid)
RETURNS boolean LANGUAGE sql STABLE SET search_path=''
AS $fn$ SELECT p_user_id='00000000-0000-0000-0000-000000000005'::uuid
 AND p_user_id=auth.uid() $fn$;

INSERT INTO auth.users(id) VALUES
 ('00000000-0000-0000-0000-000000000003'),
 ('00000000-0000-0000-0000-000000000004'),
 ('00000000-0000-0000-0000-000000000005');

INSERT INTO public.products(id,active) VALUES
 ('20000000-0000-0000-0000-000000000001',true),
 ('20000000-0000-0000-0000-000000000002',true),
 ('20000000-0000-0000-0000-000000000003',true),
 ('20000000-0000-0000-0000-000000000004',true),
 ('20000000-0000-0000-0000-000000000005',false),
 ('20000000-0000-0000-0000-000000000006',true),
 ('20000000-0000-0000-0000-000000000007',true);

UPDATE public.sinjira_novels SET product_id=
 CASE id
 WHEN '10000000-0000-0000-0000-000000000001'::uuid
   THEN '20000000-0000-0000-0000-000000000001'::uuid
 ELSE '20000000-0000-0000-0000-000000000002'::uuid END;

INSERT INTO public.sinjira_novels(id,status,file_ready,product_id) VALUES
 ('10000000-0000-0000-0000-000000000003','published',true,
  '20000000-0000-0000-0000-000000000003'),
 ('10000000-0000-0000-0000-000000000004','announced',true,
  '20000000-0000-0000-0000-000000000004'),
 ('10000000-0000-0000-0000-000000000005','published',true,
  '20000000-0000-0000-0000-000000000005'),
 ('10000000-0000-0000-0000-000000000006','published',false,
  '20000000-0000-0000-0000-000000000006'),
 ('10000000-0000-0000-0000-000000000007','published',true,
  '20000000-0000-0000-0000-000000000007');

-- A possède les livres 1 et 2; B le livre 1;
-- faux droits aux autres cas pour tester les rejets de statut/produit/fichier.
INSERT INTO public.user_entitlements(user_id,product_id) VALUES
 ('00000000-0000-0000-0000-000000000001','20000000-0000-0000-0000-000000000001'),
 ('00000000-0000-0000-0000-000000000001','20000000-0000-0000-0000-000000000002'),
 ('00000000-0000-0000-0000-000000000002','20000000-0000-0000-0000-000000000001'),
 ('00000000-0000-0000-0000-000000000001','20000000-0000-0000-0000-000000000004'),
 ('00000000-0000-0000-0000-000000000001','20000000-0000-0000-0000-000000000005'),
 ('00000000-0000-0000-0000-000000000001','20000000-0000-0000-0000-000000000006');

\echo 'V59-SETUP-PASS: livres/produits/droits fictifs pour tester la RPC définié'
