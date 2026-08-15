import { corsHeaders, json } from '../_shared/cors.ts';
import { optionalUser, serviceClient } from '../_shared/auth.ts';

const ranks:Record<string,number>={public:1,account:10,player:20,tester:30,admin:100};

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const {document_id}=await req.json();
    if(!document_id)return json({ok:false,error:'Document manquant.'},400);
    const service=serviceClient(),user=await optionalUser(req);
    const {data:doc,error}=await service.from('documents').select('*,projects(id,visibility,status)').eq('id',document_id).maybeSingle();
    if(error||!doc||doc.status!=='approved')return json({ok:false,error:'Document introuvable ou non approuvé.'},404);

    let userRank=0;
    if(user){
      const {data:isAdmin}=await service.rpc('is_sinjira_admin',{p_user_id:user.id});
      if(isAdmin)userRank=100;
      else{
        const {data:accessRank}=await service.rpc('project_access_rank',{p_project_id:doc.project_id,p_user_id:user.id});
        userRank=Number(accessRank||0);
      }
    }else if(doc.projects?.visibility==='public')userRank=1;

    if(userRank<(ranks[doc.access_level]||999))return json({ok:false,error:'Votre compte ne possède pas le niveau d’accès requis.'},403);

    if(doc.external_url)return json({ok:true,url:doc.external_url,protected:false,expires_in:null});
    if(!doc.storage_bucket||!doc.storage_path)return json({ok:false,error:'Fichier non configuré.'},500);

    const {data:signed,error:signedError}=await service.storage.from(doc.storage_bucket).createSignedUrl(doc.storage_path,600);
    if(signedError||!signed?.signedUrl)return json({ok:false,error:'Impossible de créer le lien sécurisé.'},500);
    return json({ok:true,url:signed.signedUrl,protected:true,expires_in:600});
  }catch(e){console.error(e);return json({ok:false,error:'Erreur lors de l’accès au document.'},500)}
});
