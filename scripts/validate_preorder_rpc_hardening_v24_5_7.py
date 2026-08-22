#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260822193403_sinjira_v24_5_7_preorder_rpc_and_index_hardening.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'PRECOMMANDES_SECURITE_RPC_V24_5_7.md'
PAGE=ROOT/'projets/sinjira/romans/precommande.html'


def read(path: Path) -> str:
    return path.read_text('utf-8',errors='ignore') if path.exists() else ''


def compact(text: str) -> str:
    return re.sub(r'\s+',' ',text.lower()).strip()


def main() -> int:
    errors=[]
    for p in [MIG,LEDGER,DOC,PAGE]:
        if not p.exists(): errors.append(f'Fichier V24.5.7 absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1

    sql=read(MIG); low=sql.lower(); flat=compact(sql)
    ledger=read(LEDGER); doc=read(DOC).lower(); page=read(PAGE).lower()

    if 'create schema if not exists preorder_public_internal' not in low:
        errors.append('Schéma interne preorder_public_internal absent.')
    if 'revoke all on schema preorder_public_internal from public' not in low:
        errors.append('Le schéma interne n’est pas révoqué à PUBLIC.')

    public_funcs=[
        'product_preorder_commercial_info',
        'product_preorder_fulfillment_options',
        'product_preorder_shipping_estimate',
    ]
    for name in public_funcs:
        if f'function public.{name}' not in low:
            errors.append(f'Wrapper public absent: {name}')
        if f'function preorder_public_internal.{name}' not in low:
            errors.append(f'Lecteur interne absent: {name}')

    # Trois wrappers publics doivent être invoker; les trois lecteurs internes peuvent être definer.
    invoker_count=len(re.findall(r'create\s+or\s+replace\s+function\s+public\.product_preorder_(?:commercial_info|fulfillment_options|shipping_estimate).*?security\s+invoker',low,re.S))
    internal_definer_count=len(re.findall(r'create\s+or\s+replace\s+function\s+preorder_public_internal\.product_preorder_(?:commercial_info|fulfillment_options|shipping_estimate).*?security\s+definer',low,re.S))
    if invoker_count != 3: errors.append(f'Wrappers publics SECURITY INVOKER: {invoker_count}/3.')
    if internal_definer_count != 3: errors.append(f'Lecteurs internes SECURITY DEFINER: {internal_definer_count}/3.')

    for name,signature in [
        ('product_preorder_commercial_info','text'),
        ('product_preorder_fulfillment_options','text'),
        ('product_preorder_shipping_estimate','text,text,integer'),
    ]:
        marker=f'grant execute on function public.{name}({signature}) to anon, authenticated'
        if marker not in flat: errors.append(f'Grant contrôlé manquant pour {name}.')

    sealed_tables=['preorder_commercial_plans','preorder_fulfillment_settings','preorder_shipping_zones','preorder_pickup_points']
    for table in sealed_tables:
        forbidden_patterns=[
            rf'grant\s+select\s+on(?:\s+table)?\s+public\.{table}\s+to\s+(?:anon|authenticated)',
            rf'grant\s+(?:insert|update|delete|all)\s+on(?:\s+table)?\s+public\.{table}\s+to\s+(?:anon|authenticated)',
        ]
        for pattern in forbidden_patterns:
            if re.search(pattern,low): errors.append(f'Accès direct interdit ajouté sur {table}.')

    for old in ['product_preorders_admin_read','product_preorders_own_read']:
        if f'drop policy if exists {old} on public.product_preorders' not in low:
            errors.append(f'Ancienne politique non retirée: {old}')
    if 'create policy product_preorders_read' not in low:
        errors.append('Politique SELECT combinée product_preorders_read absente.')
    if '(select auth.uid()) = user_id' not in flat or 'public.is_sinjira_admin((select auth.uid()))' not in flat:
        errors.append('Politique combinée ne conserve pas propriétaire OU administrateur.')

    indexes=[
        'moderation_appeals_reviewed_by_fkey_idx',
        'moderation_decisions_decided_by_fkey_idx',
        'moderation_decisions_reversed_by_fkey_idx',
        'privacy_incident_register_created_by_fkey_idx',
        'privacy_incident_register_updated_by_fkey_idx',
        'privacy_legal_holds_created_by_fkey_idx',
        'privacy_legal_holds_user_id_fkey_idx',
        'dating_connections_requested_by_profile_id_fkey_idx',
        'dating_messages_sender_profile_id_fkey_idx',
    ]
    for idx in indexes:
        if f'create index if not exists {idx}' not in low:
            errors.append(f'Index V24.5.7 absent: {idx}')

    forbidden=['canadapost','canada post','ups.com','fedex','purolator','shippo','easypost','stripe','paypal','twilio','api.resend.com']
    for token in forbidden:
        if token in low: errors.append(f'Intégration externe interdite dans la migration: {token}')

    historical='20260822193403 sinjira_v24_5_7_preorder_rpc_and_index_hardening'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if historical not in rows:
        errors.append('Ledger sans migration V24.5.7.')
    if len(rows) < 137:
        errors.append(f'Ledger tronqué: {len(rows)} migrations, minimum historique attendu 137.')
    elif rows[136] != historical:
        errors.append('La position historique de V24.5.7 dans le ledger a été modifiée.')
    versions=[row.split()[0] for row in rows]
    if versions != sorted(versions):
        errors.append('Le ledger n’est plus ordonné chronologiquement.')

    for marker in ['security invoker','preorder_public_internal','mots de passe compromis','137']:
        if marker not in doc: errors.append(f'Document V24.5.7 incomplet: {marker}')

    for marker in ['les frais de livraison seront à la charge du client','ramassage sur place','0 $']:
        if marker not in page: errors.append(f'Contrat public V24.5.6 régressé: {marker}')

    if errors:
        print(f'ECHEC V24.5.7 hardening RPC: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.7: invariant historique conservé; wrappers publics SECURITY INVOKER, lecteurs privilégiés isolés, tables scellées, politique SELECT unifiée, 9 FK couvertes et aucun service externe activé.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
