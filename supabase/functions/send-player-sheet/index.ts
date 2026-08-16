import { PDFDocument, StandardFonts } from 'npm:pdf-lib@1.17.1';
import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser} from '../_shared/auth.ts';

const MAX_REQUEST_BYTES=160_000;
const SITE='https://www.benoitcantin.com/projets/sinjira/jeux/fracture-du-reseau-mere/documents/';
const templateCache=new Map<string,Promise<Uint8Array>>();
function base64(bytes:Uint8Array){let binary='';for(let i=0;i<bytes.length;i+=0x8000)binary+=String.fromCharCode(...bytes.subarray(i,i+0x8000));return btoa(binary)}
async function requestJson(req:Request){const declared=Number(req.headers.get('content-length')||0);if(Number.isFinite(declared)&&declared>MAX_REQUEST_BYTES)throw new Error('PAYLOAD_TOO_LARGE');const text=await req.text();if(new TextEncoder().encode(text).byteLength>MAX_REQUEST_BYTES)throw new Error('PAYLOAD_TOO_LARGE');try{return text?JSON.parse(text):{}}catch{throw new Error('INVALID_JSON')}}
async function getTemplate(mode:'solo'|'standard'){
  if(!templateCache.has(mode))templateCache.set(mode,(async()=>{
    const url=mode==='solo'?`${SITE}SINJIRA_Mode_Solo_3_Joueurs_Interactive.pdf`:`${SITE}SINJIRA_Fiche_Joueur_1_Copie_Interactive.pdf`;
    const res=await fetch(url,{cache:'no-store',signal:AbortSignal.timeout(10_000)});if(!res.ok)throw new Error('TEMPLATE_UNAVAILABLE');
    const bytes=new Uint8Array(await res.arrayBuffer());if(bytes.byteLength<1000||bytes.byteLength>15*1024*1024)throw new Error('TEMPLATE_INVALID_SIZE');return bytes;
  })());
  try{return await templateCache.get(mode)!}catch(e){templateCache.delete(mode);throw e}
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const user=await requiredUser(req);if(!user.email)return json({ok:false,error:'Courriel du compte indisponible.'},409);
    const body=await requestJson(req),mode: 'solo'|'standard'=body?.mode==='solo'?'solo':'standard';
    const rawFields=body?.fields&&typeof body.fields==='object'&&!Array.isArray(body.fields)?body.fields:{};
    const fields:Record<string,string>={};for(const [name,value] of Object.entries(rawFields)){if(['session_title','party_code','player_label'].includes(name))continue;if(!/^[a-z0-9_]{1,80}$/i.test(name))continue;fields[name]=String(value??'').slice(0,6000)}
    const pdf=await PDFDocument.load(await getTemplate(mode)),form=pdf.getForm();
    for(const [name,value] of Object.entries(fields)){try{form.getTextField(name).setText(value)}catch{}}
    try{const font=await pdf.embedFont(StandardFonts.Helvetica);form.updateFieldAppearances(font)}catch{}
    const bytes=await pdf.save(),key=Deno.env.get('RESEND_API_KEY');if(!key)return json({ok:false,error:'Le service courriel SINJIRA n’est pas encore activé.'},503);
    const from=Deno.env.get('REPORT_FROM_EMAIL')||'SINJIRA <no-reply@benoitcantin.com>',filename=mode==='solo'?'SINJIRA_Fracture_Mode_Solo_3_Joueurs.pdf':'SINJIRA_Fracture_Fiche_Joueur.pdf';
    const sent=await fetch('https://api.resend.com/emails',{method:'POST',signal:AbortSignal.timeout(12_000),headers:{Authorization:`Bearer ${key}`,'Content-Type':'application/json'},body:JSON.stringify({from,to:[user.email],subject:mode==='solo'?'SINJIRA - Fiche privée mode solo':'SINJIRA - Fiche joueur privée',html:'<p>Voici votre fiche privée de <strong>SINJIRA - Fracture du Réseau-Mère</strong>.</p><p>Cette fiche n’est pas utilisée dans les données d’équilibrage du jeu.</p>',attachments:[{filename,content:base64(bytes)}]})});
    if(!sent.ok){console.error('[SINJIRA player sheet email]',sent.status);return json({ok:false,error:'Le courriel n’a pas pu être envoyé.'},502)}
    return json({ok:true,email:user.email,mode});
  }catch(e){
    console.error('[SINJIRA player sheet]',e);
    if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);
    if(e?.message==='PAYLOAD_TOO_LARGE')return json({ok:false,error:'La fiche dépasse la taille autorisée.'},413);
    if(e?.message==='INVALID_JSON')return json({ok:false,error:'Fiche invalide.'},400);
    if(e?.message==='TEMPLATE_UNAVAILABLE'||e?.message==='TEMPLATE_INVALID_SIZE')return json({ok:false,error:'Le modèle PDF n’est pas encore disponible sur le site.'},503);
    return json({ok:false,error:'Erreur lors de la préparation de la fiche.'},500);
  }
});
