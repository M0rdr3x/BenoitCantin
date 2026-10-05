#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EDGE=(ROOT/'supabase/functions/personal-ai/index.ts').read_text('utf-8')
MIG=(ROOT/'supabase/migrations/20260905000500_sinjira_v25_personal_ai_foundation.sql').read_text('utf-8')
HTML=(ROOT/'compte/mon-ia.html').read_text('utf-8')
JS=(ROOT/'assets/js/sinjira-personal-ai-v25.js').read_text('utf-8')
AUTH=(ROOT/'supabase/functions/_shared/auth.ts').read_text('utf-8')
CONFIG=(ROOT/'supabase/config.toml').read_text('utf-8')

errors=[]

def need(text,marker,label):
    if marker not in text: errors.append(label)

def need_ci(text,marker,label):
    if marker.casefold() not in text.casefold(): errors.append(label)

def forbid(text,marker,label):
    if marker in text: errors.append(label)

for marker in (
    'requiredPersonalAiUser','readBoundedJson','req.body.getReader()',
    'service_personal_ai_evaluate_access','CLIENT_IDENTITY_FORBIDDEN','private, no-store',
    'X-Content-Type-Options','Referrer-Policy','const MAX_REQUEST_BYTES = 16 * 1024;',
    "const rawLength = req.headers.get('content-length');",
    "if (!/^\\d+$/.test(normalizedLength)) throw new Error('REQUEST_TOO_LARGE');",
    'if (!Number.isSafeInteger(declared) || declared > MAX_REQUEST_BYTES)',
    "reader.cancel('REQUEST_TOO_LARGE')",
    "new TextDecoder('utf-8', { fatal: true })",
):
    need(EDGE,marker,f'Edge: garde manquante {marker}')
need(EDGE,"service_personal_ai_get_state",'Edge: RPC état absente')
need(EDGE,"service_personal_ai_update_settings",'Edge: RPC réglages absente')
need(EDGE,"service_personal_ai_set_source_permission",'Edge: RPC consentement absente')
need(EDGE,"service_personal_ai_delete_data",'Edge: RPC suppression absente')
for marker in (
    "await req.json()",
    "await req.text()",
    "Number(req.headers.get('content-length') || 0)",
    "service.rpc('security_evaluate_context'",
    "conscience_entries","service_conscience_","life_story_entries","employment_profiles","employment_applications",
):
    forbid(EDGE,marker,f'Edge: accès/lecture interdite détectée {marker}')
for action in ("'chat'","'memory'","'retrieve_source'","'complete'","'generate'"):
    forbid(EDGE,action,f'Edge: runtime IA prématuré détecté {action}')

auth_pos=EDGE.find('const { user, service } = await requiredPersonalAiUser(req);')
body_pos=EDGE.find('const body = await readBoundedJson(req);')
if auth_pos < 0 or body_pos < 0 or auth_pos > body_pos:
    errors.append('Edge: requiredPersonalAiUser(req) doit précéder toute lecture du corps Mon IA')
reader_pos=EDGE.find('req.body.getReader()')
bound_pos=EDGE.find('if (total > MAX_REQUEST_BYTES)', reader_pos)
decode_pos=EDGE.find("new TextDecoder('utf-8', { fatal: true })", bound_pos)
parse_pos=EDGE.find('JSON.parse(', decode_pos)
if reader_pos < 0 or bound_pos < reader_pos or decode_pos < bound_pos or parse_pos < decode_pos:
    errors.append('Edge: le corps Mon IA doit être borné pendant le flux avant décodage UTF-8 strict et parsing JSON')

for marker in ('personal_ai_settings','personal_ai_source_permissions','personal_ai_audit','ai_private','service_personal_ai_evaluate_access','PERSONAL_AI_AAL2_REQUIRED','PERSONAL_AI_RISK_REFUSED'):
    need(MIG,marker,f'SQL: contrat manquant {marker}')
need(MIG,"source_type in ('life_story','employment')",'SQL: sources bornées manquantes')
for marker in ('conscience_vault','personal_registry','conscience_entries'):
    if f"'{marker}'" in MIG.split('source_type in',1)[-1].split(')',1)[0]:
        errors.append(f'SQL: source Registre interdite {marker}')
need(MIG,"runtime_status text not null default 'not_configured'",'SQL: runtime doit rester non configuré')
need(MIG,'conversation_enabled','SQL: état runtime conversation désactivée absent')
need(MIG,'source_retrieval_enabled','SQL: état récupération source désactivée absent')

need(AUTH,'requiredPersonalAiUser','Auth: helper Mon IA absent')
need(AUTH,'assertPersonalAiMfa','Auth: AAL2 Mon IA absent')
for marker in ('sensitiveStepUpEnabled(context)','security_user_settings'):
    block=AUTH[AUTH.find('async function assertPersonalAiMfa'):AUTH.find('export async function optionalUser')]
    forbid(block,marker,f'Auth: Mon IA ne doit pas dépendre de la préférence désactivable {marker}')

need(CONFIG,'[functions.personal-ai]','Config: personal-ai absente')
config_block=CONFIG.split('[functions.personal-ai]',1)[1].split('[functions.',1)[0]
need(config_block,'verify_jwt = true','Config: personal-ai doit vérifier le JWT')

for marker in ('Aucun moteur conversationnel n’est encore activé','aucune conversation','Registre personnel','Aucun clone IA après votre décès','data-personal-ai-source="life_story"','data-personal-ai-source="employment"'):
    need_ci(HTML,marker,f'Web: limite/contrôle manquant {marker}')
for marker in ('localStorage.setItem(\'personal_ai','sessionStorage.setItem(\'personal_ai','indexedDB'):
    forbid(JS,marker,f'Web: persistance Mon IA locale interdite {marker}')
need(JS,"functions.invoke('personal-ai'",'Web: doit utiliser l Edge privée')
for marker in (".from('personal_ai",'.from("personal_ai'):
    forbid(JS,marker,'Web: accès direct aux tables Mon IA interdit')

if errors:
    print(f'ECHEC contrat Mon IA V25: {len(errors)} problème(s).')
    for error in errors: print('- '+error)
    raise SystemExit(1)
print('OK Mon IA V25: AAL2/ai_private, JSON 16 KiB borné en streaming, Content-Length fail-closed, UTF-8 strict, aucune mémoire/chat/provider, aucune lecture directe du Registre/Histoire de vie/Emploi et contrôle explicite des consentements.')
