import { createClient } from 'npm:@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': 'https://www.benoitcantin.com',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Vary': 'Origin'
};
const json = (data: unknown, status = 200) => new Response(JSON.stringify(data), {
  status,
  headers: { ...corsHeaders, 'Content-Type': 'application/json; charset=utf-8' }
});
function serviceClient(){
  const url=Deno.env.get('SUPABASE_URL'), key=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if(!url||!key) throw new Error('SERVER_CONFIG');
  return createClient(url,key,{auth:{persistSession:false,autoRefreshToken:false}});
}
async function requireAdmin(req:Request, service:any){
  const header=req.headers.get('Authorization')||'', token=header.startsWith('Bearer ')?header.slice(7):'';
  if(!token) throw new Error('AUTH_REQUIRED');
  const {data,error}=await service.auth.getUser(token);
  if(error||!data.user) throw new Error('AUTH_REQUIRED');
  const {data:isAdmin,error:adminError}=await service.rpc('is_sinjira_admin',{p_user_id:data.user.id});
  if(adminError||!isAdmin) throw new Error('ADMIN_REQUIRED');
  return data.user;
}
Deno.serve(async(req)=>{
  if(req.method==='OPTIONS') return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST') return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const service=serviceClient();
    await requireAdmin(req,service);
    const {data:authData,error:authError}=await service.auth.admin.listUsers({page:1,perPage:1000});
    if(authError) throw authError;
    const [{data:profiles,error:profileError},{data:access,error:accessError},{data:admins,error:adminsError}] = await Promise.all([
      service.from('profiles').select('user_id,pseudo,display_name,avatar_path'),
      service.from('project_access').select('*,projects(name,slug)'),
      service.from('internal_admin_users').select('user_id')
    ]);
    if(profileError||accessError||adminsError) throw profileError||accessError||adminsError;
    const pmap=new Map((profiles||[]).map((p:any)=>[p.user_id,p]));
    const adminIds=new Set((admins||[]).map((a:any)=>a.user_id));
    const users=(authData.users||[]).map((u:any)=>({
      id:u.id,email:u.email,created_at:u.created_at,last_sign_in_at:u.last_sign_in_at,
      pseudo:pmap.get(u.id)?.pseudo||'',display_name:pmap.get(u.id)?.display_name||'',
      avatar_path:pmap.get(u.id)?.avatar_path||null,is_admin:adminIds.has(u.id),
      access:(access||[]).filter((a:any)=>a.user_id===u.id)
    }));
    return json({ok:true,users});
  }catch(e){
    console.error(e);
    if(e?.message==='AUTH_REQUIRED') return json({ok:false,error:'Connexion requise.'},401);
    if(e?.message==='ADMIN_REQUIRED') return json({ok:false,error:'Accès administrateur refusé.'},403);
    return json({ok:false,error:'Impossible de charger les comptes joueurs.'},500);
  }
});
