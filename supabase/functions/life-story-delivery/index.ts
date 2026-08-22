import { createClient } from 'npm:@supabase/supabase-js@2';

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
function errorResponse(status = 404) {
  return new Response('Ce lien de remise n est pas disponible.', { status, headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer' } });
}

Deno.serve(async (req) => {
  if (req.method !== 'GET') return errorResponse(405);
  try {
    const token = new URL(req.url).searchParams.get('token') || '';
    if (!/^[a-f0-9]{64}$/.test(token)) return errorResponse();
    const hash = await sha256Hex(token);
    const service = serviceClient();
    const { data: link, error } = await service
      .from('life_story_delivery_links')
      .select('id,export_id,expires_at,max_downloads,download_count,revoked_at')
      .eq('token_hash', hash)
      .maybeSingle();
    if (error || !link || link.revoked_at || new Date(link.expires_at).getTime() <= Date.now() || Number(link.download_count) >= Number(link.max_downloads)) return errorResponse();
    const { data: record, error: exportError } = await service
      .from('life_story_exports')
      .select('status,storage_bucket,storage_path,audience')
      .eq('id', link.export_id)
      .maybeSingle();
    if (exportError || !record || !['generated', 'delivered'].includes(record.status) || record.storage_bucket !== 'sinjira-life-story-exports' || !record.storage_path) return errorResponse();
    const { data: file, error: downloadError } = await service.storage.from('sinjira-life-story-exports').download(record.storage_path);
    if (downloadError || !file) return errorResponse(410);
    const { error: countError } = await service.rpc('service_life_story_register_download', { p_link_id: link.id });
    if (countError) return errorResponse(410);
    const bytes = await file.arrayBuffer();
    const filename = `histoire-de-vie-${String(record.audience || 'sinjira').replace(/[^a-z0-9-]/gi, '-')}.pdf`;
    return new Response(bytes, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${filename}"`,
        'Content-Length': String(bytes.byteLength),
        'Cache-Control': 'private, no-store, max-age=0',
        'Pragma': 'no-cache',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'X-Frame-Options': 'DENY'
      }
    });
  } catch (error) {
    console.error('[life-story-delivery]', error);
    return errorResponse(500);
  }
});
