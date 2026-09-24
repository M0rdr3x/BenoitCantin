-- SINJIRA™ V25 — ancrage canonique du Livre I dans le catalogue romans.
-- Forward-only : le registre privé V25 dépend de sinjira_novels; une reconstruction
-- locale historique ne contenait jusqu'ici que le schéma, sans ligne Livre I.
-- Aucun PDF intégral ni chemin de stockage privé n'est publié par cette migration.

begin;

insert into public.sinjira_novels(
  slug,title,subtitle,description,status,cover_url,
  public_path,demo_path,comments_enabled,sort_order
)
values(
  'la-cendre-du-jugement',
  'SINJIRA — La Cendre du Jugement',
  'Livre I',
  'Premier roman officiel de SINJIRA™, avec démo publique et édition intégrale privée réservée aux comptes autorisés.',
  'published',
  '/assets/media/sinjira-livre-1-cover.webp',
  '/projets/sinjira/romans/index.html',
  '/projets/sinjira/romans/lire-demo.html',
  true,
  10
)
on conflict(slug) do update
set title=excluded.title,
    subtitle=excluded.subtitle,
    description=excluded.description,
    status='published',
    cover_url=excluded.cover_url,
    public_path=excluded.public_path,
    demo_path=excluded.demo_path,
    comments_enabled=true,
    sort_order=excluded.sort_order,
    updated_at=now();

insert into private.sinjira_private_novel_assets(
  novel_id,product_slug,delivery_mode,download_name,total_pages,enabled
)
select n.id,
       'sinjira-livre-01-la-cendre-du-jugement',
       'legacy_env',
       'SINJIRA_Livre_01_La_Cendre_du_Jugement.pdf',
       1066,
       false
from public.sinjira_novels n
where n.slug='la-cendre-du-jugement'
on conflict(novel_id) do nothing;

comment on table private.sinjira_private_novel_assets is
  'Registre serveur des actifs romans intégraux. Les chemins privés ne sont jamais livrés au catalogue navigateur; Livre I reste désactivé tant qu un stockage privé n est pas explicitement configuré.';

commit;
