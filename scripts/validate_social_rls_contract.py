#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase' / 'migrations'

OWNER = 'kingtyrano@gmail.com'
SOCIAL_VERSION = '24.4.42'
PAGE_VERSION = '24.4.44'
MESSAGE_VERSION = '24.4.71'

errors: list[str] = []


def compact(value: str) -> str:
    return re.sub(r'\s+', '', value.lower())


def latest_function(sql: str, name: str) -> str:
    matches = list(re.finditer(
        rf'create\s+(?:or\s+replace\s+)?function\s+public\.{re.escape(name)}\s*\([^)]*\).*?\$\$.*?\$\$\s*;',
        sql,
        re.I | re.S,
    ))
    return matches[-1].group(0) if matches else ''


def latest_policy(sql: str, name: str) -> str:
    matches = list(re.finditer(
        rf'create\s+policy\s+{re.escape(name)}\b.*?(?=\n\s*(?:drop\s+policy|create\s+policy|create\s+(?:or\s+replace\s+)?function|alter\s+table|revoke|grant|$))',
        sql,
        re.I | re.S,
    ))
    return matches[-1].group(0) if matches else ''


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


files = sorted(MIG.glob('*.sql'))
sql = '\n'.join(path.read_text('utf-8', errors='ignore') for path in files)

required_migrations = {
    '20260817102744_sinjira_v24_4_41_owner_social_age_band_repair.sql',
    '20260817102839_sinjira_v24_4_42_owner_social_health_guard.sql',
    '20260817103310_sinjira_v24_4_43_public_table_ddl_acl_hardening.sql',
    '20260817103625_sinjira_v24_4_44_age_band_self_only_acl.sql',
}
for name in sorted(required_migrations):
    require((MIG / name).exists(), f'Migration sociale/ACL absente: {name}')

age = latest_function(sql, 'sinjira_age_band')
age_compact = compact(age)
require(bool(age), 'Dernière définition de sinjira_age_band() introuvable.')
for marker in (
    OWNER,
    'fromauth.usersu',
    "then'adult'",
    'account_safety_profiles',
    "g.status='verified'",
    "'youth_pending'",
    "'under12'",
    "'unverified'",
):
    require(compact(marker) in age_compact, f'sinjira_age_band() incomplet: {marker}')
owner_pos = age_compact.find(compact(OWNER))
unverified_pos = age_compact.find("whens.user_idisnullors.date_of_birthisnullors.date_of_birth>current_datethen'unverified'")
require(owner_pos >= 0 and unverified_pos >= 0 and owner_pos < unverified_pos,
        'Le compte propriétaire doit être classé adulte avant le repli unverified, sans inventer une date de naissance.')

self_band = compact(latest_function(sql, 'sinjira_my_age_band'))
require('sinjira_age_band(auth.uid())' in self_band,
        'sinjira_my_age_band() ne reste pas limité au compte courant.')

acl = compact((MIG / '20260817103625_sinjira_v24_4_44_age_band_self_only_acl.sql').read_text('utf-8', errors='ignore'))
require('revokeexecuteonfunctionpublic.sinjira_age_band(uuid)frompublic,anon,authenticated' in acl,
        'La variante paramétrée sinjira_age_band(uuid) n’est pas révoquée aux rôles navigateur.')
require('grantexecuteonfunctionpublic.sinjira_age_band(uuid)toservice_role' in acl,
        'sinjira_age_band(uuid) doit rester disponible au service_role.')
require('grantexecuteonfunctionpublic.sinjira_age_band(uuid)toauthenticated' not in acl,
        'La migration finale réexpose sinjira_age_band(uuid) aux membres.')

for policy_name in ('real_posts_insert', 'char_posts_insert'):
    block = compact(latest_policy(sql, policy_name))
    require(bool(block), f'Politique RLS absente: {policy_name}')
    require('sinjira_my_age_band()' in block,
            f'{policy_name} doit utiliser la cohorte self-only.')
    require("in('youth','adult')" in block or "=any(array['youth'::text,'adult'::text])" in block,
            f'{policy_name} doit exclure les cohortes non vérifiées.')
    require('has_accepted_community_rules' in block,
            f'{policy_name} doit exiger les règles communautaires.')
    require('social_is_suspended' in block,
            f'{policy_name} doit refuser les comptes suspendus.')

hardening = compact((MIG / '20260817103310_sinjira_v24_4_43_public_table_ddl_acl_hardening.sql').read_text('utf-8', errors='ignore'))
for privilege in ('truncate', 'trigger', 'references'):
    require(privilege in hardening, f'Privilège structurel non durci: {privilege}')
require('revoke' in hardening and 'alltablesinschemapublic' in hardening and 'anon,authenticated' in hardening,
        'Le durcissement global des tables public est absent ou incomplet.')
require('alterdefaultprivilegesinschemapublic' in hardening,
        'Les privilèges par défaut des futures tables ne sont pas durcis.')

health = compact(latest_function(sql, 'sinjira_owner_social_health'))
for marker in (
    "'health_version','24.4.42'",
    "'effective_age_band',v_band",
    "'rules_accepted',v_rules",
    "'suspended',v_suspended",
    "'social_profile',v_profile",
):
    require(compact(marker) in health, f'Diagnostic social propriétaire incomplet: {marker}')
require('revokeallonfunctionpublic.sinjira_owner_social_health()frompublic,anon,authenticated' in compact(sql),
        'Le diagnostic social propriétaire doit être inaccessible aux rôles navigateur.')

common_path = ROOT / 'assets' / 'js' / 'sinjira-social-common.js'
common = common_path.read_text('utf-8', errors='ignore') if common_path.exists() else ''
for marker in (
    f"SOCIAL_RUNTIME_VERSION='{SOCIAL_VERSION}'",
    'socialErrorMessage',
    "code==='42501'",
    "message.includes('row-level security')",
    'socialErrorStatus',
):
    require(marker in common, f'Couche d’erreur sociale sûre incomplète: {marker}')

social_clients = (
    ROOT / 'assets' / 'js' / 'sinjira-community-character.js',
    ROOT / 'assets' / 'js' / 'sinjira-community-real.js',
    ROOT / 'assets' / 'js' / 'sinjira-community-rules.js',
    ROOT / 'assets' / 'js' / 'sinjira-messages-character.js',
    ROOT / 'assets' / 'js' / 'sinjira-messages-real.js',
    ROOT / 'assets' / 'js' / 'sinjira-social-blocks.js',
)
for path in social_clients:
    require(path.exists(), f'Client social absent: {path.relative_to(ROOT)}')
    if not path.exists():
        continue
    text = path.read_text('utf-8', errors='ignore')
    require(f"sinjira-social-common.js?v={SOCIAL_VERSION}" in text,
            f'{path.relative_to(ROOT)} ne force pas la couche sociale {SOCIAL_VERSION}.')
    for forbidden in ('alert(error.message)', 'fail(error.message)', "socialStatus(status,error.message"):
        require(forbidden not in text,
                f'{path.relative_to(ROOT)} expose encore une erreur technique brute: {forbidden}')

# Les pages sociales historiques gardent leur contrat social 24.4.42/24.4.44.
# Les deux messageries peuvent avancer indépendamment tant qu'elles importent
# toujours la couche sociale canonique et que leur propre version reste explicite.
social_pages = {
    ROOT / 'compte' / 'communaute.html': ('sinjira-community-real.js', SOCIAL_VERSION, PAGE_VERSION),
    ROOT / 'compte' / 'reseau-personnage.html': ('sinjira-community-character.js', SOCIAL_VERSION, PAGE_VERSION),
    ROOT / 'compte' / 'messages-reels.html': ('sinjira-messages-real.js', MESSAGE_VERSION, MESSAGE_VERSION),
    ROOT / 'compte' / 'messages-personnage.html': ('sinjira-messages-character.js', MESSAGE_VERSION, MESSAGE_VERSION),
    ROOT / 'compte' / 'regles-communaute.html': ('sinjira-community-rules.js', SOCIAL_VERSION, PAGE_VERSION),
    ROOT / 'compte' / 'blocages.html': ('sinjira-social-blocks.js', SOCIAL_VERSION, PAGE_VERSION),
}
for path, (asset, runtime_version, shell_version) in social_pages.items():
    require(path.exists(), f'Page sociale absente: {path.relative_to(ROOT)}')
    if not path.exists():
        continue
    html = path.read_text('utf-8', errors='ignore')
    require(f'{asset}?v={runtime_version}' in html,
            f'{path.relative_to(ROOT)} ne force pas {asset} V{runtime_version}.')
    require(f'data-social-runtime="{runtime_version}"' in html,
            f'{path.relative_to(ROOT)} ne déclare pas le runtime social V{runtime_version}.')
    require(f'site.js?v={shell_version}' in html,
            f'{path.relative_to(ROOT)} ne force pas le shell privé V{shell_version}.')

sw = (ROOT / 'sw.js').read_text('utf-8', errors='ignore') if (ROOT / 'sw.js').exists() else ''
require('benoitcantin-v24-4-44-public-1' in sw,
        'Le cache du service worker n’a pas été invalidé après les correctifs sociaux.')

if errors:
    print(f'ECHEC contrat social/RLS: {len(errors)} problème(s).')
    for error in errors:
        print('- ' + error)
    raise SystemExit(1)

print('OK — contrat social/RLS: socle V24.4.44 conservé, messageries V24.4.71 explicites, cohorte self-only, ACL DDL durcies et erreurs publiques assainies.')
