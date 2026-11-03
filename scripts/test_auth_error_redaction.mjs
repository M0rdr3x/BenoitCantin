#!/usr/bin/env node
// Execute actual TypeScript Edge auth guards after removing parameter type
// annotations only. All secret/user values are synthetic.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const source=readFileSync(resolve(root,'supabase/functions/_shared/auth.ts'),'utf8');
const leakedSecret='NEVER_LOG_SB_SECRET_API_KEY_OR_USER_TOKEN_TEST_98345';
const recorder=()=> {
  const events=[];
  return {events, logger:{
    warn:(...args)=>events.push(['warn',...args]),
    error:(...args)=>events.push(['error',...args])
  }};
};
function extract(startMarker,endMarker,funcName) {
  const start=source.indexOf(startMarker);
  const end=source.indexOf(endMarker,start);
  assert.ok(start>=0&&end>start,'Actual auth implementation not found: '+funcName);
  return source.slice(start,end).replaceAll(
    'context: Awaited<ReturnType<typeof authenticatedContext>>','context'
  );
}
function assertSanitized(events) {
  const log=JSON.stringify(events);
  assert.ok(!log.includes(leakedSecret),'Sensitive provider error leaked into Edge logs');
  assert.equal(events.length,1,'Expected exactly one fixed-code diagnostics event');
  assert.equal(events[0].length,3,'Provider errors must not be passed as log arguments');
  assert.equal(typeof events[0][2],'object');
  assert.equal(Object.keys(events[0][2]).join(','),'code');
  assert.match(events[0][2].code,/^[A-Z_]+$/);
}
async function deny(promise,code) {
  await assert.rejects(promise, e=>e instanceof Error && e.message===code,
    'Expected fixed failure code '+code);
}

const secretSrc=extract('function serverSecretKey()','export function serviceClient()','serverSecretKey');
function secretKey(env,logger) {
  const Deno={env:{get:(name)=>env[name]}};
  return new Function('Deno','console',secretSrc+'\nreturn serverSecretKey;')(Deno,logger)();
}
{
  const {events,logger}=recorder();
  const modern='{"default":"'+leakedSecret+'",'; // Invalid JSON with secret material
  assert.equal(secretKey({SUPABASE_SECRET_KEYS:modern,SUPABASE_SERVICE_ROLE_KEY:'legacy-key-test'},logger),'legacy-key-test');
  assertSanitized(events);
  assert.deepEqual(events[0],['warn','[SINJIRA auth]',{code:'SUPABASE_SECRET_KEYS_INVALID'}]);
}
{
  const {events,logger}=recorder();
  assert.equal(secretKey({SUPABASE_SECRET_KEYS:'{'+leakedSecret,SUPABASE_SERVICE_ROLE_KEY:undefined},logger),'');
  assertSanitized(events);
}
{
  const {events,logger}=recorder();
  const modern='synthetic-modern-server-key-abcdefghijklmnopqrstuvwxyz';
  assert.equal(secretKey({SUPABASE_SECRET_KEYS:JSON.stringify({default:modern}),SUPABASE_SERVICE_ROLE_KEY:'legacy'},logger),modern);
  assert.deepEqual(events,[],'Valid modern secret must never be logged');
}
{
  const {events,logger}=recorder();
  const alt='synthetic-secondary-server-key-abcdefghijklmnopqrstuvwxyz';
  assert.equal(secretKey({SUPABASE_SECRET_KEYS:JSON.stringify({secondary:alt}),SUPABASE_SERVICE_ROLE_KEY:'legacy'},logger),alt);
  assert.deepEqual(events,[]);
}

const stepSrc=extract('async function sensitiveStepUpEnabled(','async function assertSensitiveMfa(','sensitiveStepUpEnabled');
function stepUp(context,logger){
  return new Function('console',stepSrc+'\nreturn sensitiveStepUpEnabled;')(logger)(context);
}
function sensitiveContext(data,error=null) {
  const chain={
    select:(columns)=>{assert.equal(columns,'sensitive_step_up');return chain;},
    eq:(column,user)=>{assert.equal(column,'user_id');assert.equal(user,'user-synthetic');return chain;},
    maybeSingle:async()=>({data,error})
  };
  return {user:{id:'user-synthetic'},service:{
    from:(table)=>{assert.equal(table,'security_user_settings');return chain;}
  }};
}
{
  const {events,logger}=recorder();
  await deny(stepUp(sensitiveContext(null,new Error(leakedSecret)),logger),'SECURITY_STATE_UNAVAILABLE');
  assertSanitized(events);
  assert.deepEqual(events[0],['error','[SINJIRA sensitive auth]',{code:'SECURITY_STATE_UNAVAILABLE'}]);
}
{
  const {events,logger}=recorder();
  assert.equal(await stepUp(sensitiveContext({sensitive_step_up:false}),logger),false);
  assert.equal(await stepUp(sensitiveContext({sensitive_step_up:true}),logger),true);
  assert.equal(await stepUp(sensitiveContext(null),logger),true,'Missing preference must stay fail-closed');
  assert.deepEqual(events,[]);
}

const sensitiveSrc=extract('async function assertSensitiveMfa(','async function assertVaultMfa(','assertSensitiveMfa');
function sensitiveMfa(stepEnabled,assuranceLevel,logger) {
  return new Function('console','sensitiveStepUpEnabled','assuranceLevel',
    sensitiveSrc+'\nreturn assertSensitiveMfa;')(logger,stepEnabled,assuranceLevel);
}
const ctx=sensitiveContext({sensitive_step_up:true});
{
  const {events,logger}=recorder();
  const guard=sensitiveMfa(async()=>true,async()=>{throw new Error(leakedSecret);},logger);
  await deny(guard(ctx),'MFA_STATE_UNAVAILABLE');
  assertSanitized(events);
  assert.deepEqual(events[0],['error','[SINJIRA sensitive auth]',{code:'MFA_STATE_UNAVAILABLE'}]);
}
{
  const {events,logger}=recorder();
  const aal=(currentLevel,nextLevel)=>({currentLevel,nextLevel});
  assert.equal(await sensitiveMfa(async()=>false,async()=>{throw Error('not consulted');},logger)(ctx),null);
  await deny(sensitiveMfa(async()=>true,async()=>aal('aal1','aal2'),logger)(ctx),'MFA_REQUIRED');
  await deny(sensitiveMfa(async()=>true,async()=>aal('aal1','aal1'),logger)(ctx),'MFA_SETUP_REQUIRED');
  assert.equal((await sensitiveMfa(async()=>true,async()=>aal('aal2','aal2'),logger)(ctx)).currentLevel,'aal2');
  assert.deepEqual(events,[],'Expected failures must not leak user/provider errors');
}
// Every relevant error source in the shared auth module now uses fixed-code logs.
for(const raw of [
  "console.warn('[SINJIRA auth] SUPABASE_SECRET_KEYS illisible, repli sur la clé legacy.', error)",
  "console.error('[SINJIRA sensitive auth] préférences de sécurité indisponibles', error)",
  "console.error('[SINJIRA sensitive auth] état MFA indisponible', error)",
]){
  assert.ok(!source.includes(raw),'Legacy provider-error logging restored');
}
console.log('PASS auth redaction: malformed secret JSON, PostgREST and MFA errors never log tokens; real guards retain fail-closed behavior.');
