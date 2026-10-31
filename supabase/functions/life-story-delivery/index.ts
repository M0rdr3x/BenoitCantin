import { readBoundedRequestText } from '../_shared/bounded-request.mjs';
import { createClient } from 'npm:@supabase/supabase-js@2';

const MAX_REQUEST_BYTES = 256;
const MAX_PDF_BYTES = 15 * 1024 * 1024;
const ALLOWED_ORIGINS = new Set([
  'https://www.benoitcantin.com',
  'https://benoitcantin.com',
]);

function serverKey() {
  const modern = Deno.env.get('SUPABASE_SECRET_KEYS');
  if (modern) {
    try {
      const keys = JSON.parse(modern); const preferred = keys?.default;
      if (typeof preferred === 'string' && preferred.length > 20) return preferred;
      const fallback = Object.values(keys || {}).find((v) => typeof v === 'string' && v.length > 20);
      if (typeof fallback === 'string') return fallback;
    } catch {}
  }
  return Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || '';
}
function serviceClient() {
  const url = Deno.env.get('SUPABASE_URL') || ''; const key = serverKey();
  if (!url || !key) throw new Error('SERVER_CONFIG_MISSING');
  return createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } });
}
function hex(bytes: Uint8Array) { return [...bytes].map((b) => b.toString(16).padStart(2, '0')).join(''); }
async function sha256Hex(value: string) { return hex(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)))); }
function allowedOrigin(req: Request) {
  const origin = req.headers.get('origin') || '';
  return ALLOWED_ORIGINS.has(origin) ? origin : '';
}
function responseHeaders(req: Request, contentType = 'text/plain; charset=utf-8') {
  const origin = allowedOrigin(req);
  const headers: Record<string, string> = {
    'Content-Type': contentType,
    'Cache-Control': 'private, no-store, max-age=0',
    'Pragma': 'no-cache',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'no-referrer',
    'X-Frame-Options': 'DENY',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
    'Content-Security-Policy': "default-src 'none'; frame-ancestors 'none'; sandbox",
    'Vary': 'Origin',
  };
  if (origin) headers['Access-Control-Allow-Origin'] = origin;
  return headers;
}
function errorResponse(req: Request, status = 404) {
  return new Response('Ce lien de remise n est pas disponible.', { status, headers: responseHeaders(req) });
}
function preflight(req: Request) {
  const origin = allowedOrigin(req);
  if (!origin) return errorResponse(req, 403);
  return new Response(null, {
    status: 204,
    headers: {
      ...responseHeaders(req),
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'content-type',
      'Access-Control-Max-Age': '600',
    },
  });
}
function hasPdfSignature(bytes: ArrayBuffer) {
  if (bytes.byteLength < 5) return false;
  const head = new Uint8Array(bytes, 0, 5);
  return String.fromCharCode(...head) === '%PDF-';
}

function canonicalExportPath(record: Record<string,unknown>, exportId:unknown): boolean {
  // Même avec un registre erroné, un lien ne doit pas ouvrir un AUTRE export
  // du même compartiment. Le service d'export écrit exactement ce chemin.
  const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if(typeof record.subject_user_id!=='string'||typeof record.case_id!=='string'||
     typeof record.storage_path!=='string'||typeof exportId!=='string')return false;
  if(!uuid.test(record.subject_user_id)||!uuid.test(record.case_id)||!uuid.test(exportId))
    return false;
  return record.storage_path===`${record.subject_user_id}/${record.case_id}/${exportId}.pdf`;
}

async function readDeliveryToken(req: Request): Promise<{ token?: string; response?: Response }> {
  // Une fonction publique doit refuser le MIME et la taille AVANT la lecture.
  const type=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
  if(type!=='application/json')return {response:errorResponse(req,415)};
  const declared=req.headers.get('content-length');
  if(declared!==null &&
    (!/^[0-9]+$/.test(declared)||!Number.isSafeInteger(Number(declared))||
     Number(declared)>MAX_REQUEST_BYTES))return {response:errorResponse(req,413)};

  let rawBody:string;
  try{
    rawBody=await readBoundedRequestText(req, MAX_REQUEST_BYTES);
  }catch(error){
    if(error instanceof Error && error.message==='REQUEST_TIMEOUT')
      return {response:errorResponse(req,408)};
    if(error instanceof Error && error.message==='REQUEST_TOO_LARGE')
      return {response:errorResponse(req,413)};
    return {response:errorResponse(req,400)};
  }
  // L'intégrité du flux et l'encodage fatal sont garantis par le lecteur partagé.
  let payload:unknown;
  try{payload=JSON.parse(rawBody)}catch{return {response:errorResponse(req,400)}}
  if(!payload||typeof payload!=='object'||Array.isArray(payload))
    return {response:errorResponse(req,400)};
  const body=payload as Record<string,unknown>;
  if(Object.keys(body).length!==1||typeof body.token!=='string')
    return {response:errorResponse(req,400)};
  if(!/^[a-f0-9]{64}$/.test(body.token))return {response:errorResponse(req)};
  return {token:body.token};
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return preflight(req);
  if (req.method !== 'POST') return errorResponse(req, 405);
  if (!allowedOrigin(req)) return errorResponse(req, 403);

  try {
    const requestUrl = new URL(req.url);
    if (requestUrl.search) return errorResponse(req, 400);

    const parsed=await readDeliveryToken(req);
    if(parsed.response)return parsed.response;
    const token=parsed.token!;

    const hash = await sha256Hex(token);
    const service = serviceClient();
    const { data: link, error } = await service
      .from('life_story_delivery_links')
      .select('id,export_id,expires_at,max_downloads,download_count,revoked_at')
      .eq('token_hash', hash)
      .maybeSingle();
    if (error || !link || link.revoked_at || new Date(link.expires_at).getTime() <= Date.now() || Number(link.download_count) >= Number(link.max_downloads)) return errorResponse(req);

    const { data: record, error: exportError } = await service
      .from('life_story_exports')
      .select('status,storage_bucket,storage_path,audience,subject_user_id,case_id')
      .eq('id', link.export_id)
      .maybeSingle();
    if (exportError || !record || !['generated', 'delivered'].includes(record.status) ||
        record.storage_bucket !== 'sinjira-life-story-exports' ||
        !canonicalExportPath(record,link.export_id)) return errorResponse(req);

    const { data: file, error: downloadError } = await service.storage.from('sinjira-life-story-exports').download(record.storage_path);
    if (downloadError || !file) return errorResponse(req, 410);
    if (file.size <= 0 || file.size > MAX_PDF_BYTES) return errorResponse(req, 410);

    const bytes = await file.arrayBuffer();
    if (bytes.byteLength <= 0 || bytes.byteLength > MAX_PDF_BYTES || !hasPdfSignature(bytes)) return errorResponse(req, 410);

    const { error: countError } = await service.rpc('service_life_story_register_download', { p_link_id: link.id });
    if (countError) return errorResponse(req, 410);

    const filename = `histoire-de-vie-${String(record.audience || 'sinjira').replace(/[^a-z0-9-]/gi, '-')}.pdf`;
    return new Response(bytes, {
      status: 200,
      headers: {
        ...responseHeaders(req, 'application/pdf'),
        'Content-Disposition': `attachment; filename="${filename}"`,
        'Content-Length': String(bytes.byteLength),
        'Access-Control-Expose-Headers': 'Content-Disposition, Content-Length',
      },
    });
  } catch {
    console.error('[life-story-delivery]', { code: 'LIFE_STORY_DELIVERY_FAILED' });
    return errorResponse(req, 500);
  }
});
