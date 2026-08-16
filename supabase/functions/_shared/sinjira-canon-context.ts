import type { SupabaseClient } from 'npm:@supabase/supabase-js@2.112.3';

export async function loadSinjiraCanonContext(service: SupabaseClient) {
  const {data,error}=await service
    .from('sinjira_canon_context')
    .select('context_key,classification,title,source_name,source_version,source_date,source_sha256,public_safe,content')
    .order('context_key');
  if(error) throw error;
  return data || [];
}

export function canonPrompt(contexts:any[]) {
  const safe=contexts.map(c=>({
    key:c.context_key,
    classification:c.classification,
    title:c.title,
    content:c.content
  }));
  return JSON.stringify(safe);
}
