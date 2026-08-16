import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';

async function requireAdmin(req:Request){
  const user=await requiredUser(req),service=serviceClient();
  const {data:isAdmin,error}=await service.rpc('is_sinjira_admin',{p_user_id:user.id});
  if(error||!isAdmin)throw new Error('ADMIN_REQUIRED');
  return {user,service};
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const {service}=await requireAdmin(req);
    const {data:authData,error:authError}=await service.auth.admin.listUsers({page:1,perPage:1000});
    if(authError)throw authError;
    const [{data:profiles,error:profileError},{data:access,error:accessError},{data:admins,error:adminsError}]=await Promise.all([
      service.from('profiles').select('user_id,pseudo,display_name,avatar_path'),
      service.from('project_access').select('*,projects(name,slug)'),
      service.from('internal_admin_users').select('user_id')
    ]);
    if(profileError||accessError||adminsError)throw profileError||accessError||adminsError;
    const pmap=new Map((profiles||[]).map((p:any)=>[p.user_id,p]));
    const adminIds=new Set((admins||[]).map((a:any)=>a.user_id));
    const byUser=new Map<string,any[]>();
    for(const item of access||[]){
      const rows=byUser.get(item.user_id)||[];
      rows.push(item);
      byUser.set(item.user_id,rows);
    }
    const users=(authData.users||[]).map((u:any)=>({
      id:u.id,
      email:u.email,
      created_at:u.created_at,
      last_sign_in_at:u.last_sign_in_at,
      pseudo:pmap.get(u.id)?.pseudo||'',
      display_name:pmap.get(u.id)?.display_name||'',
      avatar_path:pmap.get(u.id)?.avatar_path||null,
      is_admin:adminIds.has(u.id),
      access:byUser.get(u.id)||[]
    }));
    return json({ok:true,users});
  }catch(e){
    console.error('[SINJIRA admin users]',e);
    if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);
    if(e?.message==='ADMIN_REQUIRED')return json({ok:false,error:'Accès administrateur refusé.'},403);
    return json({ok:false,error:'Impossible de charger les comptes joueurs.'},500);
  }
});
