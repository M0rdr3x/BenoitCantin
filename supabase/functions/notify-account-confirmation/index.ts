import {corsHeaders} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';
import {sendFormspreeNotice} from '../_shared/sinjira-formspree.ts';

const privateHeaders={
  ...corsHeaders,
  'Content-Type':'application/json; charset=utf-8',
  'Cache-Control':'private, no-store, max-age=0',
  'Referrer-Policy':'no-referrer',
  'X-Content-Type-Options':'nosniff'
};
const response=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:privateHeaders});

Deno.serve(async req=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return response({ok:false,code:'METHOD_NOT_ALLOWED'},405);
  try{
    // Le JWT réel est vérifié côté serveur. Rien n'est accepté depuis le corps HTTP.
    const user=await requiredUser(req);
    if(!user.email_confirmed_at)return response({ok:false,code:'EMAIL_NOT_CONFIRMED'},403);
    const result=await sendFormspreeNotice(serviceClient(),'compte_confirme',user.id);
    return response({ok:true,notification_sent:result.accepted,already_recorded:result.already});
  }catch{
    console.warn('[SINJIRA compte Formspree]','NOTIFICATION_NOT_AVAILABLE');
    return response({ok:false,code:'NOTIFICATION_NOT_AVAILABLE'},503);
  }
});
