#!/usr/bin/env node
// Security regression tests against the real HMAC geo helper.
// Synthetic headers only; no IP, account, Supabase, real session or location.
import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { verifiedCoarseGeo } from '../supabase/functions/_shared/verified-geo.mjs';

if (!globalThis.crypto) globalThis.crypto = webcrypto;
const secret = 'test-only-geo-proxy-key-32-bytes-NEVER-PRODUCTION';
const session = '123e4567-e89b-42d3-a456-426614174000';
const otherSession = '123e4567-e89b-42d3-a456-426614174001';
const now = 1_800_000_000_000;
const stamp = String(now);
const encoder = new TextEncoder();
const EMPTY = { country: null, region: null };
const headersFor = ({country='CA',region='Québec',timestamp=stamp,proof=''}={}) => ({
  headers: new Headers({
    'cf-ipcountry': country,
    'x-sinjira-region': region,
    'x-sinjira-geo-timestamp': timestamp,
    'x-sinjira-geo-proof': proof
  })
});
async function makeProof({userSession=session,country='CA',region='Québec',timestamp=stamp,keySecret=secret}={}) {
  const key = await crypto.subtle.importKey(
    'raw', encoder.encode(keySecret), {name:'HMAC',hash:'SHA-256'}, false, ['sign']
  );
  const payload = ['sinjira-geo/v1',userSession.toLowerCase(),timestamp,country,region].join('\n');
  const bytes = new Uint8Array(await crypto.subtle.sign('HMAC',key,encoder.encode(payload)));
  return 'v1='+Array.from(bytes, b => b.toString(16).padStart(2,'0')).join('');
}
const verified = (req,userSession=session,opts={}) =>
  verifiedCoarseGeo(req,userSession,{enabled:true,secret,now,...opts});

test('No opt-in, no secret, and unproven raw headers are always ignored', async()=>{
  const req=headersFor();
  assert.deepEqual(await verifiedCoarseGeo(req,session,{enabled:false,secret,now}),EMPTY);
  assert.deepEqual(await verifiedCoarseGeo(req,session,{enabled:true,secret:'',now}),EMPTY);
  assert.deepEqual(await verified(req),EMPTY);
});

test('Accept a valid proxy HMAC bound to this verified JWT session', async()=>{
  const proof = await makeProof();
  assert.deepEqual(await verified(headersFor({proof})), {country:'CA',region:'Québec'});
});

test('The original raw headers cannot change an attested country/region', async()=>{
  const proof=await makeProof();
  assert.deepEqual(await verified(headersFor({proof,country:'FR'})),EMPTY);
  assert.deepEqual(await verified(headersFor({proof,region:'Ontario'})),EMPTY);
  assert.deepEqual(await verified(headersFor({proof:proof.slice(0,-1)+(proof.endsWith('0')?'1':'0')})),EMPTY);
});

test('HMAC proof cannot be replayed under another user session', async()=>{
  const proof=await makeProof();
  assert.deepEqual(await verified(headersFor({proof}),otherSession),EMPTY);
});

test('Timestamp must be signed, recent, and neither stale nor far in future', async()=>{
  const proof=await makeProof();
  assert.deepEqual(await verified(headersFor({proof,timestamp:String(now+1)})),EMPTY);
  assert.deepEqual(await verified(headersFor({proof}),session,{now:now+60_001}),EMPTY);
  assert.deepEqual(await verified(headersFor({proof}),session,{now:now-60_001}),EMPTY);
  assert.deepEqual(await verified(headersFor({proof}),session,{now:now+60_000}),{country:'CA',region:'Québec'});
});

test('Weak, bad-format, empty, malformed or unrelated proof fails closed', async()=>{
  const proof=await makeProof();
  assert.deepEqual(await verified(headersFor({proof}),session,{secret:'weak'}),EMPTY);
  assert.deepEqual(await verified(headersFor({proof:'v1='+'0'.repeat(64)})),EMPTY);
  assert.deepEqual(await verified(headersFor({proof:proof.toUpperCase()})),EMPTY);
  assert.deepEqual(await verified(headersFor({proof,timestamp:'0001800000000000'})),EMPTY);
  assert.deepEqual(await verified(headersFor({proof,region:'<script>'})),EMPTY);
  assert.deepEqual(await verified(headersFor({proof,country:'XX3'})),EMPTY);
  assert.deepEqual(await verified(headersFor({proof}),"bad-session"),EMPTY);
  assert.deepEqual(await verified({headers:{get(){throw new Error('unavailable');}}}),EMPTY);
});

test('Country-only signed proof stays coarse and nulls missing region', async()=>{
  const proof=await makeProof({region:''});
  assert.deepEqual(await verified(headersFor({proof,region:''})),{country:'CA',region:null});
});

test('The helper contains no IP collection or private-error logging',()=>{
  const src=readFileSync(new URL('../supabase/functions/_shared/verified-geo.mjs',import.meta.url),'utf8');
  assert.match(src,/crypto\.subtle\.verify\(/);
  assert.match(src,/sinjira-geo\/v1/);
  assert.match(src,/sessionId\.toLowerCase\(\)/);
  assert.doesNotMatch(src,/\b(?:cf-connecting-ip|x-forwarded-for|x-real-ip)\b/i);
  assert.doesNotMatch(src,/console\.(?:warn|error|log)\(/);
});

test('The security-context route awaits the proof before sending geo to the RPC',()=>{
  const src=readFileSync(new URL('../supabase/functions/security-context/index.ts',import.meta.url),'utf8');
  assert.match(src,/import \{ verifiedCoarseGeo \} from '\.\.\/_shared\/verified-geo\.mjs'/);
  assert.match(src,/enabled: Deno\.env\.get\('SINJIRA_TRUST_GEO_HEADERS'\) === 'true'/);
  assert.match(src,/secret: Deno\.env\.get\('SINJIRA_GEO_PROXY_HMAC_SECRET'\) \|\| ''/);
  assert.match(src,/const sessionId = sessionIdFromVerifiedRequest\(req\);/);
  assert.match(src,/const geo = await trustedGeo\(req, sessionId\);/);
  assert.match(src,/p_country_code: geo\.country/);
  assert.match(src,/p_region_code: geo\.region/);
});
