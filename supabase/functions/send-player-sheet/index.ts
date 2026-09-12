import { PDFDocument, StandardFonts } from 'npm:pdf-lib@1.17.1';
import { corsHeaders } from '../_shared/cors.ts';
import { requiredUser } from '../_shared/auth.ts';

const FUNCTION_VERSION='24.5.54';
const MAX_REQUEST_BYTES=220_000;
const MAX_TEMPLATE_BYTES=15*1024*1024;
const MAX_TEXT=6000;
const PAID_EXTERNAL_SERVICES_ENABLED=false;
const TEMPLATE_ORIGIN='https://www.benoitcantin.com';
const TEMPLATE_PATH_PREFIX='/projets/sinjira/jeux/fracture-du-reseau-mere/documents/';
const STANDARD_TEMPLATE=`${TEMPLATE_ORIGIN}${TEMPLATE_PATH_PREFIX}SINJIRA_Fiche_Joueur_1_Copie_Interactive.pdf`;
const SOLO_TEMPLATE=`${TEMPLATE_ORIGIN}${TEMPLATE_PATH_PREFIX}SINJIRA_Mode_Solo_3_Joueurs_Interactive.pdf`;

const PRIVATE_HEADERS={
  ...corsHeaders,
  'Content-Type':'application/json; charset=utf-8',
  'Cache-Control':'private, no-store, max-age=0',
  'Pragma':'no-cache',
  'X-Content-Type-Options':'nosniff',
  'Referrer-Policy':'no-referrer'
};

function privateJson(data:unknown,status=200){
  return new Response(JSON.stringify(data),{status,headers:PRIVATE_HEADERS});
}

function toBase64(bytes:Uint8Array){
  let binary='';
  for(let i=0;i<bytes.length;i+=0x8000){
    binary+=String.fromCharCode(...bytes.subarray(i,i+0x8000));
  }
  return btoa(binary);
}

async function readLimitedJson(req:Request):Promise<{body?:Record<string,unknown>;response?:Response}>{
  const contentType=(req.headers.get('content-type')||'').toLowerCase();
  if(!contentType.startsWith('application/json')){
    return {response:privateJson({ok:false,error:'Content-Type application/json requis.',code:'UNSUPPORTED_MEDIA_TYPE',function_version:FUNCTION_VERSION},415)};
  }

  const rawLength=req.headers.get('content-length');
  if(rawLength){
    const declared=Number(rawLength);
    if(!Number.isFinite(declared)||declared<0||declared>MAX_REQUEST_BYTES){
      return {response:privateJson({ok:false,error:'Requête trop volumineuse.',code:'REQUEST_TOO_LARGE',function_version:FUNCTION_VERSION},413)};
    }
  }

  const raw=await req.text();
  if(new TextEncoder().encode(raw).byteLength>MAX_REQUEST_BYTES){
    return {response:privateJson({ok:false,error:'Requête trop volumineuse.',code:'REQUEST_TOO_LARGE',function_version:FUNCTION_VERSION},413)};
  }

  try{
    const parsed=JSON.parse(raw||'{}');
    if(!parsed||typeof parsed!=='object'||Array.isArray(parsed))throw new Error('INVALID_JSON');
    return {body:parsed as Record<string,unknown>};
  }catch{
    return {response:privateJson({ok:false,error:'JSON invalide.',code:'INVALID_JSON',function_version:FUNCTION_VERSION},400)};
  }
}

function templateUrl(mode:'solo'|'standard'){
  const raw=mode==='solo'?SOLO_TEMPLATE:STANDARD_TEMPLATE;
  const url=new URL(raw);
  if(
    url.protocol!=='https:'||
    url.origin!==TEMPLATE_ORIGIN||
    !url.pathname.startsWith(TEMPLATE_PATH_PREFIX)||
    !url.pathname.toLowerCase().endsWith('.pdf')||
    url.username||url.password||url.search||url.hash
  ) throw new Error('PLAYER_SHEET_TEMPLATE_NOT_ALLOWED');
  return url.toString();
}

async function fetchTemplateBytes(mode:'solo'|'standard'){
  const response=await fetch(templateUrl(mode),{cache:'no-store',redirect:'error'});
  if(!response.ok)throw new Error('PLAYER_SHEET_TEMPLATE_FETCH_FAILED');

  const declared=Number(response.headers.get('content-length')||'0');
  if(Number.isFinite(declared)&&declared>MAX_TEMPLATE_BYTES)throw new Error('PLAYER_SHEET_TEMPLATE_TOO_LARGE');

  const bytes=new Uint8Array(await response.arrayBuffer());
  if(bytes.byteLength===0||bytes.byteLength>MAX_TEMPLATE_BYTES)throw new Error('PLAYER_SHEET_TEMPLATE_TOO_LARGE');
  if(bytes.length<5||String.fromCharCode(...bytes.subarray(0,5))!=='%PDF-')throw new Error('PLAYER_SHEET_TEMPLATE_NOT_PDF');
  return bytes;
}

async function buildPlayerSheet(mode:'solo'|'standard',fields:Record<string,unknown>){
  const templateBytes=await fetchTemplateBytes(mode);
  const pdf=await PDFDocument.load(templateBytes);
  const form=pdf.getForm();

  for(const [name,value] of Object.entries(fields)){
    if(['session_title','party_code','player_label'].includes(name))continue;
    try{
      form.getTextField(name).setText(String(value??'').slice(0,MAX_TEXT));
    }catch{
      // Un champ absent d'une version du PDF ne doit pas bloquer la fiche.
    }
  }

  try{
    const font=await pdf.embedFont(StandardFonts.Helvetica);
    form.updateFieldAppearances(font);
  }catch{
    // Certains lecteurs PDF régénèrent eux-mêmes les apparences.
  }

  return await pdf.save();
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.',code:'METHOD_NOT_ALLOWED',function_version:FUNCTION_VERSION},405);

  try{
    const user=await requiredUser(req);
    if(!user?.email)return privateJson({ok:false,error:'Adresse courriel du compte indisponible.',code:'ACCOUNT_EMAIL_REQUIRED',function_version:FUNCTION_VERSION},400);

    // Intégration préparée uniquement. Aucune requête applicative ou fournisseur
    // n'est traitée tant qu'une activation explicite distincte n'a pas eu lieu.
    if(!PAID_EXTERNAL_SERVICES_ENABLED){
      return privateJson({ok:false,error:'Le transport courriel externe est préparé mais désactivé.',code:'PAID_EXTERNAL_SERVICE_DISABLED',function_version:FUNCTION_VERSION},503);
    }

    const parsed=await readLimitedJson(req);
    if(parsed.response)return parsed.response;
    const body=parsed.body||{};
    const mode: 'solo'|'standard'=body.mode==='solo'?'solo':'standard';
    const fields=(body.fields&&typeof body.fields==='object'&&!Array.isArray(body.fields))
      ? body.fields as Record<string,unknown>
      : {};

    const bytes=await buildPlayerSheet(mode,fields);
    const key=Deno.env.get('RESEND_API_KEY');
    if(!key)return privateJson({ok:false,error:'Le service courriel SINJIRA n’est pas configuré.',code:'EMAIL_PROVIDER_NOT_CONFIGURED',function_version:FUNCTION_VERSION},503);

    const from=Deno.env.get('REPORT_FROM_EMAIL')||'SINJIRA <no-reply@benoitcantin.com>';
    const filename=mode==='solo'?'SINJIRA_Fracture_Mode_Solo_3_Joueurs.pdf':'SINJIRA_Fracture_Fiche_Joueur.pdf';
    const sent=await fetch('https://api.resend.com/emails',{
      method:'POST',
      redirect:'error',
      headers:{Authorization:`Bearer ${key}`,'Content-Type':'application/json'},
      body:JSON.stringify({
        from,
        to:[user.email],
        subject:mode==='solo'?'SINJIRA - Fiche privée mode solo':'SINJIRA - Fiche joueur privée',
        html:'<p>Voici votre fiche privée de <strong>SINJIRA - Fracture du Réseau-Mère</strong>.</p><p>Cette fiche n’est pas utilisée dans les données d’équilibrage du jeu.</p>',
        attachments:[{filename,content:toBase64(bytes)}]
      })
    });

    if(!sent.ok){
      console.error('[send-player-sheet]',{code:'PLAYER_SHEET_EMAIL_PROVIDER_FAILED',status:sent.status});
      return privateJson({ok:false,error:'Le courriel n’a pas pu être envoyé.',code:'EMAIL_DELIVERY_FAILED',function_version:FUNCTION_VERSION},502);
    }

    return privateJson({ok:true,email:user.email,mode,function_version:FUNCTION_VERSION});
  }catch(error){
    const code=error instanceof Error?error.message:'';
    if(code==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.',code:'AUTH_REQUIRED',function_version:FUNCTION_VERSION},401);
    console.error('[send-player-sheet]',{code:'SEND_PLAYER_SHEET_FAILED'});
    return privateJson({ok:false,error:'Erreur lors de la préparation de la fiche.',code:'PLAYER_SHEET_FAILED',function_version:FUNCTION_VERSION},500);
  }
});
