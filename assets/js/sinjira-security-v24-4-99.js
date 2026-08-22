import {getSupabase,setStatus} from './sinjira-supabase.js';

const s=getSupabase();
const status=document.querySelector('[data-security-center-status]');
const devices=document.querySelector('[data-security-devices]');

function report(message,type='info'){setStatus(status,message,type)}
function augmentLostDeviceActions(){
  if(!devices)return;
  devices.querySelectorAll('[data-device-revoke]').forEach(revokeButton=>{
    const id=String(revokeButton.getAttribute('data-device-revoke')||'');
    if(!id||devices.querySelector(`[data-device-lost="${CSS.escape(id)}"]`))return;
    const button=document.createElement('button');
    button.className='btn btn-secondary';
    button.type='button';
    button.dataset.deviceLost=id;
    button.textContent='Déclarer perdu';
    revokeButton.insertAdjacentElement('afterend',button);
  });
}
function addPasskeyReadiness(){
  const anchor=document.querySelector('[aria-labelledby="mfa-active-title"]');
  if(!anchor||document.querySelector('[data-passkey-readiness]'))return;
  const supported=typeof globalThis.PublicKeyCredential!=='undefined';
  const section=document.createElement('section');
  section.className='security-card security-section-card';
  section.setAttribute('data-passkey-readiness','');
  section.setAttribute('aria-labelledby','passkey-readiness-title');
  section.innerHTML=`<div class="security-card-head"><div><h2 id="passkey-readiness-title">Passkeys</h2><p>Préparation WebAuthn pour le futur domaine définitif de SINJIRA.</p></div><span class="security-state-chip">Préparé</span></div><p><strong>${supported?'Cet appareil prend en charge les passkeys.':'Compatibilité passkey non détectée sur ce navigateur.'}</strong></p><p class="v24-feature-note">État : préparé, non activé. Aucun identifiant WebAuthn n’est créé tant que le RP ID définitif n’est pas <strong>sinjira.com</strong>.</p>`;
  anchor.insertAdjacentElement('afterend',section);
}

const observer=new MutationObserver(()=>augmentLostDeviceActions());
if(devices)observer.observe(devices,{childList:true,subtree:true});
augmentLostDeviceActions();
addPasskeyReadiness();

document.addEventListener('click',async event=>{
  const button=event.target.closest?.('[data-device-lost]');
  if(!button)return;
  const id=String(button.dataset.deviceLost||'');
  if(!id)return;
  if(!globalThis.confirm('Déclarer cet appareil perdu ? SINJIRA retirera sa confiance, désactivera ses notifications de sécurité et fermera les autres sessions du compte.'))return;
  button.disabled=true;
  try{
    const {error}=await s.rpc('security_report_lost_device',{p_device_id:id});
    if(error)throw error;
    await s.auth.signOut({scope:'others'});
    report('Appareil déclaré perdu. Sa confiance et ses notifications ont été révoquées; les autres sessions ont été fermées.','success');
    setTimeout(()=>location.reload(),900);
  }catch(error){
    console.warn('[SINJIRA lost device]',error);
    report(error?.message==='AAL2_REQUIRED'?'Vérification MFA requise avant de déclarer cet appareil perdu.':'Impossible de terminer la protection de cet appareil pour le moment.','error');
    button.disabled=false;
  }
});