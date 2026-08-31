#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    'foundation': ROOT / 'supabase/migrations/20260822012609_sinjira_v24_5_0_life_story_foundation.sql',
    'pipeline': ROOT / 'supabase/migrations/20260822153324_sinjira_v24_5_2_verified_legacy_pdf_pipeline.sql',
    'hardening': ROOT / 'supabase/migrations/20260822153451_sinjira_v24_5_2_legacy_pipeline_hardening.sql',
    'queue': ROOT / 'supabase/migrations/20260822154317_sinjira_v24_5_2_admin_legacy_queue.sql',
    'codes': ROOT / 'supabase/migrations/20260822154450_sinjira_v24_5_2_private_death_report_codes.sql',
    'boundary': ROOT / 'supabase/migrations/20260822161721_sinjira_v24_5_2_export_boundary_enforcement.sql',
    'noop': ROOT / 'supabase/migrations/20260822161849_sinjira_v24_5_2_export_boundary_enforcement_noop_marker.sql',
    'export': ROOT / 'supabase/functions/life-story-export/index.ts',
    'delivery': ROOT / 'supabase/functions/life-story-delivery/index.ts',
    'life_ui': ROOT / 'compte/histoire-de-vie.html',
    'life_js': ROOT / 'assets/js/sinjira-life-story-v24-5-2.js',
    'report_ui': ROOT / 'compte/signaler-deces.html',
    'report_js': ROOT / 'assets/js/sinjira-death-report-v24-5-2.js',
    'admin_ui': ROOT / 'admin/sinjira/heritage.html',
    'admin_js': ROOT / 'assets/js/sinjira-admin-life-story-v24-5-2.js',
    'canon': ROOT / 'HERITAGE_NUMERIQUE_V24_5_2.md',
    'paid_policy': ROOT / 'SERVICES_EXTERNES_PAYANTS.md',
    'architecture': ROOT / 'ARCHITECTURE_COMPTE_UNIVERSEL.md',
    'runtime_config': ROOT / 'assets/js/sinjira-supabase-config.js',
    'config': ROOT / 'supabase/config.toml',
}

REGISTRY_MARKERS = (
    'reader_characters',
    'registry_account_links',
    'sinjira_character_applications',
    'character_questionnaire',
)


def read(name: str) -> str:
    path = FILES[name]
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text('utf-8', errors='ignore')


def require(errors: list[str], text: str, markers: tuple[str, ...] | list[str], label: str) -> None:
    for marker in markers:
        if marker not in text:
            errors.append(f'{label}: marqueur obligatoire absent: {marker}')


def forbid(errors: list[str], text: str, markers: tuple[str, ...] | list[str], label: str) -> None:
    low = text.lower()
    for marker in markers:
        if marker.lower() in low:
            errors.append(f'{label}: marqueur interdit détecté: {marker}')


def main() -> int:
    errors: list[str] = []
    for name, path in FILES.items():
        if not path.exists():
            errors.append(f'Fichier V24.5.2 absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors:
            print('- ' + error)
        return 1

    foundation = read('foundation')
    pipeline = read('pipeline')
    hardening = read('hardening')
    queue = read('queue')
    codes = read('codes')
    boundary = read('boundary')
    noop = read('noop')
    export = read('export')
    delivery = read('delivery')
    life_ui = read('life_ui')
    life_js = read('life_js')
    report_ui = read('report_ui')
    report_js = read('report_js')
    admin_ui = read('admin_ui')
    admin_js = read('admin_js')
    canon = read('canon')
    paid_policy = read('paid_policy')
    architecture = read('architecture')
    runtime_config = read('runtime_config')
    config = read('config')

    require(errors, foundation, [
        'life_story_entries', 'life_story_versions', 'life_story_version_entries',
        'life_story_recipients', 'life_story_legacy_settings',
        "posthumous_disclosure text not null default 'never'",
        "approval_status text not null default 'draft'",
        'legacy_directive_review_required',
    ], 'Fondation Histoire de vie')

    require(errors, pipeline, [
        'life_story_posthumous_cases', 'life_story_posthumous_contests',
        'life_story_exports', 'life_story_delivery_links', 'life_story_cleanup_tasks',
        "source_boundary text not null default 'life_story_only'",
        'registry_access_prohibited boolean not null default true',
        "now()+interval '30 days'",
        'private.require_sinjira_admin_aal2()',
        'SAFETY_HOLD_NOT_ELAPSED', 'OPEN_CONTEST_EXISTS',
        'POSTHUMOUS_DELIVERY_NOT_AUTHORIZED',
        'admin_life_story_confirm_case', 'admin_life_story_prepare_export',
        'service_life_story_register_download',
        "values ('sinjira-life-story-exports','sinjira-life-story-exports',false",
        "array['application/pdf']",
    ], 'Pipeline posthume')
    require(errors, pipeline + hardening, [
        "status='contested'", "status='rejected'", "status='verified_hold'",
        "hold_until=now()+interval '30 days'",
        'RECIPIENT_VERSION_NOT_DELIVERED',
        "'life_story_source_review'", "'registry_private_data_review'",
        "now()+interval '90 days'",
    ], 'Durcissement posthume')

    final_prepare = hardening
    require(errors, final_prepare, [
        "'source_boundary','life_story_only'",
        "'registry_access_prohibited',true",
        "'entries',v_entries",
        "approval_status='approved'",
        "posthumous_disclosure='selected_versions'",
        'user_approved_at is not null',
    ], 'Instantané autorisé')
    forbid(errors, final_prepare, ["'recipient_user_id'", "'entry_id'", "'recipient_id'"], 'Instantané autorisé')
    for marker in REGISTRY_MARKERS:
        if marker in final_prepare:
            errors.append(f'Instantané autorisé: accès Registre/personnage interdit: {marker}')

    require(errors, boundary, [
        'admin_life_story_get_export',
        'private.require_sinjira_admin_aal2()',
        'content_snapshot', 'recipients_snapshot',
        'source_boundary', 'registry_access_prohibited',
        'revoke all on function public.admin_life_story_get_export',
    ], 'Frontière finale de lecture export')
    forbid(errors, boundary, REGISTRY_MARKERS, 'Frontière finale de lecture export')
    require(errors, noop, ['Aucun schéma ni aucune donnée', 'select 1;'], 'Marqueur production sans effet')

    require(errors, codes, [
        'life_story_report_codes', 'gen_random_bytes(32)',
        "digest(v_raw,'sha256')", 'code_hash text not null unique',
        'v_active>=5', 'SELF_DEATH_REPORT_FORBIDDEN',
        "status='active'", "status='used'", "status='revoked'",
        "insert into public.memorial_requests", "'pending'",
        'REPORT_ALREADY_EXISTS',
    ], 'Codes privés de signalement')
    if re.search(r'\bcode\s+text\s+(?:not\s+null\s+)?(?:unique\s+)?[,)]', codes, re.I):
        errors.append('Codes privés: un code brut ne doit jamais être stocké en colonne.')
    if "values(v_code.user_id,v_requester,btrim(p_relationship_claim),'verified'" in codes:
        errors.append('Codes privés: le signalement ne doit jamais créer une demande déjà vérifiée.')

    require(errors, export, [
        'requiredAdmin', 'admin_life_story_get_export', 'pdf-lib',
        'service_life_story_mark_export_generated', 'sha256Hex',
        'create_delivery_links', 'crypto.getRandomValues(new Uint8Array(32))',
        'token_hash', 'max_downloads: 3',
        "transport: 'manual_or_future_sender'",
    ], 'Edge export')
    forbid(errors, export, REGISTRY_MARKERS, 'Edge export')
    if ".from('life_story_entries')" in export or '.from("life_story_entries")' in export:
        errors.append('Edge export: le générateur doit lire uniquement l’instantané serveur, pas les souvenirs sources.')

    require(errors, delivery, [
        'sha256Hex', 'token_hash', 'expires_at', 'max_downloads',
        'download_count', 'service_life_story_register_download',
        "'Cache-Control':", 'no-store',
        'sinjira-life-story-exports',
    ], 'Edge remise')
    forbid(errors, delivery, REGISTRY_MARKERS + ('life_story_entries', 'life_story_versions'), 'Edge remise')
    require(errors, config, [
        '[functions.life-story-export]', 'verify_jwt = true',
        '[functions.life-story-delivery]', 'verify_jwt = false',
    ], 'Configuration Edge')

    require(errors, life_ui + life_js, [
        'data-life-story-contest-form', 'life_story_my_posthumous_case',
        'life_story_contest_death_verification', 'life_story_create_report_code',
        'life_story_list_report_codes', 'life_story_revoke_report_code',
        '/compte/signaler-deces.html',
    ], 'Interface Histoire de vie')
    require(errors, report_ui + report_js, [
        'data-death-report-form', 'life_story_report_death_by_code',
        '64', 'vérification humaine',
    ], 'Interface signalement')

    require(errors, admin_ui + admin_js, [
        'Héritage numérique', 'mfa.getAuthenticatorAssuranceLevel', "currentLevel !== 'aal2'",
        'admin_life_story_pending_requests', 'admin_life_story_verify_death',
        'admin_life_story_resolve_contest', 'admin_life_story_confirm_case',
        'admin_life_story_prepare_export', "functions.invoke('life-story-export'",
        'admin_life_story_complete_case', 'admin_life_story_cleanup_due',
        'admin_life_story_complete_cleanup_task',
    ], 'Console héritage')
    direct_table_patterns = [
        ".from('life_story_posthumous_cases')", ".from('life_story_exports')",
        ".from('life_story_delivery_links')", ".from('life_story_cleanup_tasks')",
        ".from('life_story_report_codes')",
    ]
    forbid(errors, admin_js, direct_table_patterns, 'Console héritage')
    require(errors, queue, ['private.require_sinjira_admin_aal2()', 'admin_life_story_pending_requests', 'admin_life_story_cleanup_due'], 'File admin')

    require(errors, canon, [
        'l’humain passe avant tout', 'Registre des Consciences n’est pas un héritage',
        'life_story_only', '30 jours', 'nouveau délai complet de 30 jours',
        '256 bits', 'SHA-256', 'AAL2', 'no-store',
        'n’active aucun fournisseur externe de courriel', 'tâches de revue humaine',
    ], 'Canon héritage')
    require(errors, paid_policy, [
        'Préparer une intégration ne constitue jamais une autorisation de l’activer',
        'décision explicite',
        'paidExternalServicesEnabled',
        'externalEmailDeliveryEnabled',
        'nativeStorePublishingEnabled',
        'App Store', 'Google Play',
    ], 'Politique services externes payants')
    require(errors, runtime_config, [
        'paidExternalServicesEnabled: false',
        'externalEmailDeliveryEnabled: false',
        'nativeStorePublishingEnabled: false',
        'remoteAiEnabled: false',
        'commercePublishingEnabled: false',
        'tokenPurchasesEnabled: false',
    ], 'Configuration runtime gratuite')
    require(errors, architecture, [
        'HERITAGE_NUMERIQUE_V24_5_2.md', 'SERVICES_EXTERNES_PAYANTS.md', 'Histoire de vie',
        'Codes privés de signalement', 'Délai de sécurité de 30 jours',
        'life_story_only', 'sinjira-life-story-exports',
        'Services externes payants',
    ], 'Architecture Compte')

    combined_runtime = export + delivery + admin_js + report_js + life_js
    forbid(errors, combined_runtime, ['sendgrid', 'mailgun', 'postmark', 'resend.com', 'ses.amazonaws.com'], 'Transport posthume')

    if errors:
        print(f'ECHEC Histoire de vie / héritage V24.5.2: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK Histoire de vie / héritage V24.5.2: consentement explicite, deux validations humaines, délai de 30 jours, contestation, frontière Registre, PDF privé, jetons hashés et services externes payants désactivés vérifiés.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
