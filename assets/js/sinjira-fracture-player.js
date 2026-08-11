import { PDFDocument } from 'https://cdn.jsdelivr.net/npm/pdf-lib@1.17.1/+esm';
import { getSupabase, getCurrentUser, isSinjiraBackendConfigured } from './sinjira-supabase.js';

const GAME_SLUG='fracture-du-reseau-mere';
const form=document.querySelector('[data-private-player-form]');
const status=document.querySelector('[data-player-status]');
const params=new URLSearchParams(location.search);
let sessionId=params.get('session')||null;
const humanNo=Math.max(1,Math.min(3,Number(params.get('joueur'))||1));
const humanCount=Math.max(1,Math.min(3,Number(params.get('players'))||1));
const effectiveCount=3;
const role=params.get('role')==='invisible3'?'invisible3':'self';
const sheetKey=params.get('sheet')||(role==='invisible3'?`p${humanNo}_invisible_3`:`p${humanNo}_self`);

function show(msg,type='info'){status.hidden=false;status.textContent=msg;status.dataset.type=type}
function partyCode(){
  const direct=params.get('party');if(direct)return direct;
  try{const s=JSON.parse(sessionStorage.getItem('sinjira_fracture_setup')||'null');if(s?.party_code)return s.party_code}catch{}
  return '';
}
function roleLabel(){
  if(role==='invisible3')return `Joueur invisible 3 - copie privée du Joueur ${humanNo}`;
  const name=params.get('nom');return name?`Joueur ${humanNo} - ${name}`:`Joueur ${humanNo}`;
}
function rowFields(){
  document.querySelector('[data-player-rounds]').innerHTML=Array.from({length:10},(_,i)=>{const n=i+1;return `<tr><td>${n}</td><td><input name="tour_${n}_points_resistance"></td><td><input name="tour_${n}_points_reseau_mere"></td><td><input name="tour_${n}_suspect_resistance"></td><td><input name="tour_${n}_suspect_reseau_mere"></td></tr>`}).join('');
  document.querySelector('[data-accusations]').innerHTML=Array.from({length:7},(_,i)=>`<input name="accusation_${i+1}" aria-label="Accusation ${i+1}" placeholder="${i+1}">`).join('');
}
function allFields(){const fd=new FormData(form),o={};for(const [k,v] of fd.entries())o[k]=String(v);o.sheet_key=sheetKey;o.sheet_role=role;o.human_player_number=String(humanNo);return o}
function setupFromUrl(){
  form.elements.player_label.value=roleLabel();
  form.elements.party_code.value=partyCode();
  const h=document.querySelector('[data-sheet-title]');if(h)h.textContent=role==='invisible3'?`Joueur invisible 3 - fiche privée du Joueur ${humanNo}`:`Fiche privée - Joueur ${humanNo}`;
  const c=document.querySelector('[data-sheet-context]');if(c)c.textContent=role==='invisible3'?`À 2 joueurs humains, chacun possède sa propre copie indépendante du Joueur invisible 3. Cette page est la copie du Joueur ${humanNo}.`:`Cette page est la fiche personnelle du Joueur ${humanNo}.`;
  if(partyCode())form.elements.session_title.value=`Partie ${partyCode()} - Fracture du Réseau-Mère`;
}
async function findSession(user){
  if(sessionId)return sessionId;
  const code=partyCode();if(!code)return null;
  const {data}=await getSupabase().from('game_sessions').select('id').eq('user_id',user.id).eq('game_slug',GAME_SLUG).eq('party_code',code).maybeSingle();
  if(data?.id){sessionId=data.id;params.set('session',sessionId);history.replaceState(null,'',`${location.pathname}?${params.toString()}`);return sessionId}
  return null;
}
async function loadExisting(){
  if(!isSinjiraBackendConfigured())return;const user=await getCurrentUser();if(!user)return;
  await findSession(user);if(!sessionId)return;
  const s=getSupabase();
  const [{data:session},{data:sheet}]=await Promise.all([
    s.from('game_sessions').select('*').eq('id',sessionId).eq('user_id',user.id).maybeSingle(),
    s.from('player_sheets').select('fields,sheet_label').eq('session_id',sessionId).eq('user_id',user.id).eq('sheet_key',sheetKey).maybeSingle()
  ]);
  if(session?.title&&role==='self')form.elements.session_title.value=session.title;
  if(sheet?.fields)for(const [k,v] of Object.entries(sheet.fields)){if(form.elements[k])form.elements[k].value=v??''}
  if(sheet)show('Cette fiche privée a été chargée depuis votre compte.','success');
}
async function ensureSession(user,fields){
  const s=getSupabase(),code=partyCode();
  if(!sessionId)await findSession(user);
  if(sessionId){
    await s.from('game_sessions').update({
      title:fields.session_title||`Partie ${code||''} - Fracture du Réseau-Mère`,player_count:humanCount,human_player_count:humanCount,effective_player_count:effectiveCount,play_mode:humanCount===1?'solo':'multiplayer',party_code:code||null
    }).eq('id',sessionId).eq('user_id',user.id);
    return sessionId;
  }
  const {data,error}=await s.from('game_sessions').insert({
    user_id:user.id,game_slug:GAME_SLUG,title:fields.session_title||`Partie ${code||''} - Fracture du Réseau-Mère`,status:'in_progress',
    player_count:humanCount,human_player_count:humanCount,effective_player_count:effectiveCount,play_mode:humanCount===1?'solo':'multiplayer',party_code:code||null
  }).select('id').single();
  if(error)throw error;sessionId=data.id;params.set('session',sessionId);history.replaceState(null,'',`${location.pathname}?${params.toString()}`);return sessionId;
}
async function saveToAccount(){
  if(!isSinjiraBackendConfigured()){show('Le Compte SINJIRA n’est pas encore relié à Supabase.','error');return}
  const user=await getCurrentUser();if(!user){show('Connectez-vous à votre Compte SINJIRA pour sauvegarder cette fiche.','error');return}
  const fields=allFields();
  try{
    const sid=await ensureSession(user,fields),s=getSupabase();
    const {error}=await s.from('player_sheets').upsert({session_id:sid,user_id:user.id,sheet_key:sheetKey,sheet_label:roleLabel(),fields},{onConflict:'session_id,sheet_key'});
    if(error)throw error;
    show('Fiche sauvegardée séparément dans votre compte. Elle reste privée et n’est jamais utilisée pour l’analyse du jeu.','success');
  }catch(e){show(e.message||'Sauvegarde impossible.','error')}
}
async function createPdfBlob(){
  const pdf=await PDFDocument.load(await (await fetch('documents/SINJIRA_Fiche_Joueur_1_Copie_Interactive.pdf')).arrayBuffer());const f=pdf.getForm(),fields=allFields();
  for(const [k,v] of Object.entries(fields)){if(['player_label','session_title','party_code','sheet_key','sheet_role','human_player_number'].includes(k))continue;try{f.getTextField(k).setText(String(v||''))}catch{}}
  return new Blob([await pdf.save()],{type:'application/pdf'});
}
function safeName(v){return String(v||'fiche').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-zA-Z0-9_-]+/g,'_').replace(/_+/g,'_').replace(/^_|_$/g,'')}
async function downloadPdf(){
  try{const blob=await createPdfBlob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`SINJIRA_${safeName(roleLabel())}_Remplie.pdf`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1500);show('Votre PDF privé a été généré sur votre appareil.','success')}catch(e){show('Impossible de générer le PDF rempli.','error')}
}
async function emailPdf(){
  if(!isSinjiraBackendConfigured()){show('Le service SINJIRA n’est pas encore configuré.','error');return}
  const user=await getCurrentUser();if(!user){show('Connectez-vous pour envoyer la fiche au courriel de votre Compte SINJIRA.','error');return}
  try{
    const {data,error}=await getSupabase().functions.invoke('send-player-sheet',{body:{mode:'standard',sheet_label:roleLabel(),fields:allFields()}});
    if(error||!data?.ok)throw new Error(data?.error||error?.message||'Envoi impossible');
    show(`La fiche privée a été envoyée à ${user.email}. Elle n’a pas été ajoutée aux données d’analyse.`,'success');
  }catch(e){show(e.message||'Envoi impossible. Le service courriel peut ne pas être activé.','error')}
}
rowFields();setupFromUrl();loadExisting();
document.querySelector('[data-download-player]').addEventListener('click',downloadPdf);
document.querySelector('[data-save-player]').addEventListener('click',saveToAccount);
document.querySelector('[data-email-player]').addEventListener('click',emailPdf);
