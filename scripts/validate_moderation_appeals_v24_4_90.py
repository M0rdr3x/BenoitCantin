#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260821005919_sinjira_v24_4_90_moderation_decisions_appeals.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
EDGE=ROOT/'supabase/functions/admin-social-v20/index.ts'
USER_HTML=ROOT/'compte/moderation.html'
USER_JS=ROOT/'assets/js/sinjira-moderation-appeals-v24-4-90.js'
ADMIN_JS=ROOT/'assets/js/sinjira-admin-social-v20.js'
MANIFEST=ROOT/'scripts/validate_production_schema_manifest.py'
errors=[]

def read(path):
    if not path.exists():
        errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
        return ''
    return path.read_text('utf-8',errors='ignore')

def need(ok,msg):
    if not ok: errors.append(msg)

mig=read(MIG); ledger=read(LEDGER); edge=read(EDGE); user_html=read(USER_HTML); user_js=read(USER_JS); admin_js=read(ADMIN_JS); manifest=read(MANIFEST)
low=''.join(mig.lower().split())
edge_low=''.join(edge.lower().split())

need('20260821005919 sinjira_v24_4_90_moderation_decisions_appeals' in ledger,'Migration V24.4.90 absente du ledger production.')
for marker in (
    'create table if not exists private.moderation_decisions',
    'create table if not exists private.moderation_appeals',
    'alter table private.moderation_decisions enable row level security',
    'alter table private.moderation_appeals enable row level security',
    'revoke all on table private.moderation_decisions from public,anon,authenticated',
    'revoke all on table private.moderation_appeals from public,anon,authenticated',
    'create or replace function public.moderation_content_visible',
    'create or replace function public.moderation_my_decisions',
    'create or replace function public.moderation_submit_appeal',
): need(marker in mig.lower(),f'Contrat SQL V24.4.90 absent: {marker}')
need("appeal_deadline>=decided_at+interval'6months'" in low,'Le délai minimal d’appel de six mois n’est pas garanti côté serveur.')
need("decision_source='human_admin'" in low,'Les décisions ne sont pas verrouillées sur une source humaine.')
need('human_review_required=true' in low,'La révision humaine obligatoire des appels est absente.')
need("'fee',0" in low,'Le RPC d’appel ne garantit pas explicitement un coût nul.')
for scope in (("'real','post'",'public.social_real_posts'),("'real','comment'",'public.social_real_comments'),("'character','post'",'public.social_character_posts'),("'character','comment'",'public.social_character_comments'),("'real','message'",'public.social_real_messages'),("'character','message'",'public.social_character_messages')):
    need(scope[0] in mig and 'moderation_content_visible' in mig,f'Filtre de visibilité réversible absent pour {scope[1]}.')

for marker in ('restrict_reported_content','list_appeals','review_appeal','moderation_decisions','moderation_appeals','moderation_decision_id'):
    need(marker in edge,f'Edge Function de modération incomplète: {marker}')
need(".delete().eq('id',r.target_id)" not in edge_low,'La modération ordinaire contient encore une suppression physique de contenu.')
need('suspenddatingforuser' not in edge_low,'La suspension ferme encore Rencontres via l’ancien mécanisme irréversible.')
need("dating_connections').update({status:'closed'" not in edge,'Une suspension de modération ferme encore définitivement des conversations Rencontres.')

for marker in ('Mes décisions de modération et mes appels','appel interne est <strong>gratuit</strong>','révision humaine','data-moderation-list'):
    need(marker.lower() in user_html.lower(),f'Interface utilisateur des appels incomplète: {marker}')
for marker in ("rpc('moderation_my_decisions'","rpc('moderation_submit_appeal'",'p_appeal_text'):
    need(marker in user_js,f'Client utilisateur des appels incomplet: {marker}')
for marker in ('data-social-appeal-count','data-social-appeal-list','Maintenir la décision','Renverser la décision','review_appeal'):
    need(marker in admin_js,f'Console admin des appels incomplète: {marker}')
need("'moderation_appeals'" in manifest and "'moderation_decisions'" in manifest,'Manifeste production incomplet pour les tables privées de modération.')

if errors:
    print(f'ECHEC modération/appels V24.4.90: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK V24.4.90: décisions humaines motivées, masquage réversible, appel gratuit >= 6 mois, révision humaine et reversal vérifiés.')
