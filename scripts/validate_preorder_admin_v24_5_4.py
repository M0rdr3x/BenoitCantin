#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'migration': ROOT / 'supabase/migrations/20260822173401_sinjira_v24_5_4_preorder_admin_and_internal_notice.sql',
    'admin_html': ROOT / 'admin/sinjira/precommandes.html',
    'admin_js': ROOT / 'assets/js/sinjira-admin-preorders-v24-5-4.js',
    'admin_css': ROOT / 'assets/css/sinjira-admin-preorders-v24-5-4.css',
    'admin_console': ROOT / 'assets/js/sinjira-admin-console.js',
    'policy': ROOT / 'SERVICES_EXTERNES_PAYANTS.md',
    'ledger': ROOT / 'supabase/production-migration-ledger.txt',
}


def read(name):
    return FILES[name].read_text('utf-8', errors='ignore')


def require(errors, text, markers, label):
    for marker in markers:
        if marker not in text:
            errors.append(f'{label}: marqueur absent: {marker}')


def forbid(errors, text, markers, label):
    low = text.lower()
    for marker in markers:
        if marker.lower() in low:
            errors.append(f'{label}: marqueur interdit: {marker}')


def main():
    errors = []
    for name, path in FILES.items():
        if not path.exists():
            errors.append(f'Fichier V24.5.4 absent: {path.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- ' + e)
        return 1

    mig = read('migration')
    html = read('admin_html')
    js = read('admin_js')
    css = read('admin_css')
    console = read('admin_console')
    policy = read('policy')
    ledger = read('ledger')

    require(errors, mig, [
        'preorder_sales_announcements',
        'external_delivery_enabled boolean not null default false check (external_delivery_enabled = false)',
        'payment_activation_allowed boolean not null default false check (payment_activation_allowed = false)',
        'alter table public.preorder_sales_announcements enable row level security',
        'revoke all on table public.preorder_sales_announcements from public, anon, authenticated',
        'admin_preorder_overview', 'admin_preorder_list',
        'admin_preorder_save_announcement_draft', 'admin_preorder_mark_announcement_ready',
        'admin_preorder_send_internal_announcement',
        'private.require_sinjira_admin_aal2()',
        "insert into public.user_notifications",
        "pp.status='reserved'",
        'pp.contact_when_sales_open=true',
        "'preorder_sales_opening'",
        "'preorder_sales_announcement'",
        "status='ready'", "status='sent'",
        'PAID_OR_EXTERNAL_DELIVERY_FORBIDDEN',
    ], 'Migration admin précommandes')
    forbid(errors, mig, [
        'insert into public.orders', 'insert into public.order_items',
        'stripe', 'paypal', 'checkout.session', 'resend.com', 'sendgrid', 'mailgun', 'twilio'
    ], 'Migration admin précommandes')

    require(errors, html, [
        'Précommandes du Livre I', 'MFA requis',
        'Réservations actives', 'Exemplaires souhaités', 'À avertir dans SINJIRA',
        'Préparer l’ouverture future des ventes',
        'Enregistrer le brouillon', 'Marquer prêt', 'Envoyer l’avis interne',
        'Transport externe', 'désactivé', 'Paiement', 'Conversion automatique en commande',
        'Aucun courriel, adresse postale ou identifiant technique n’est affiché ici.'
    ], 'Interface admin')
    forbid(errors, html, ['Stripe', 'PayPal', 'Numéro de carte', 'Adresse de facturation'], 'Interface admin')

    require(errors, js, [
        "mfa.getAuthenticatorAssuranceLevel", "currentLevel !== 'aal2'",
        "admin_preorder_overview", "admin_preorder_list",
        "admin_preorder_save_announcement_draft", "admin_preorder_mark_announcement_ready",
        "admin_preorder_send_internal_announcement",
        'Aucun courriel, SMS ou paiement ne sera déclenché.',
        'Aucun service externe n’a été utilisé.',
        "p_limit: 250",
    ], 'Runtime admin')
    forbid(errors, js, [
        '.functions.invoke(', 'fetch(', 'stripe', 'paypal', 'resend', 'sendgrid', 'mailgun', 'twilio',
        "from('orders')", 'from("orders")', "from('order_items')", 'from("order_items")'
    ], 'Runtime admin')

    require(errors, css, ['preorder-admin-stat-grid', 'preorder-announcement-form', '@media(max-width:640px)'], 'Styles admin')
    require(errors, console, ["/admin/sinjira/precommandes.html", 'Précommandes du Livre I', 'data-admin-preorders-link'], 'Accès console admin')
    require(errors, policy, [
        'Administration et avis d’ouverture V24.5.4',
        'brouillon → prêt → notification interne SINJIRA',
        'external_delivery_enabled = false', 'payment_activation_allowed = false',
        'écrit uniquement dans `user_notifications`'
    ], 'Politique services payants')
    require(errors, ledger, ['20260822173401 sinjira_v24_5_4_preorder_admin_and_internal_notice'], 'Ledger production')

    if errors:
        print(f'ECHEC V24.5.4 administration précommandes: {len(errors)} problème(s).')
        for e in errors: print('- ' + e)
        return 1
    print('OK V24.5.4: statistiques admin, MFA/AAL2, brouillon→prêt→avis interne et verrou paiement/services externes validés.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
