revoke all on table public.orders from anon;
revoke all on table public.order_items from anon;

revoke insert, update, delete, truncate, references, trigger on table public.orders from authenticated;
revoke insert, update, delete, truncate, references, trigger on table public.order_items from authenticated;

grant select on table public.orders to authenticated;
grant select on table public.order_items to authenticated;

comment on table public.orders is
  'Table transactionnelle dormante. Aucun checkout/paiement actif. Lecture self-only via RLS pour authenticated; écritures réservées au serveur.';
comment on table public.order_items is
  'Table transactionnelle dormante. Aucun checkout/paiement actif. Lecture via commande propre seulement; écritures réservées au serveur.';
