import { getCurrentUser, getSupabase } from './sinjira-supabase.js';

const DEVICE_KEY='sinjira.security.device_key.v1';
const PUSH_TOKEN='sinjira.security.push_token.v1';
const PUSH_ENABLED='sinjira.security.push_enabled.v1';
const PUSH_PLATFORM='sinjira.security.push_platform.v1';

// Les clés du navigateur et du conteneur natif sont non fiables jusqu'à
// vérification. Une longueur >=16 n'est pas une preuve d'entropie.
function isStrongDeviceKey(value){
  if(typeof value!=='string')return false;
  if(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value))return true;
  const legacy=/^sinjira-([0-9a-f]{48})(?:-[0-9a-z]{1,15})?$/i.exec(value);
  return Boolean(legacy&&!/^0{48}$/.test(legacy[1]));
}

function isExpoPushToken(value){
  // Seuls les tokens de getExpoPushTokenAsync vont au RPC; refuser
  // les chaînes libres, caractères de contrôle et valeurs démesurées.
  return typeof value==='string'&&value.length>=20&&value.length<=300&&
    /^(?:ExponentPushToken|ExpoPushToken)\[[A-Za-z0-9_-]{8,250}\]$/.test(value);
}

async function syncPushEndpoint(){
  try{
    const user=await getCurrentUser();
    if(!user)return;
    const deviceKey=localStorage.getItem(DEVICE_KEY)||'';
    if(!isStrongDeviceKey(deviceKey))return;
    const enabled=localStorage.getItem(PUSH_ENABLED);
    const token=localStorage.getItem(PUSH_TOKEN)||'';
    const platform=String(localStorage.getItem(PUSH_PLATFORM)||'')
      .replace(/[^A-Za-z0-9._ -]/g,'').slice(0,40);
    if(enabled==='1'&&isExpoPushToken(token)){
      const {error}=await getSupabase().rpc('security_register_push_endpoint',{
        p_device_key:deviceKey,p_expo_push_token:token,p_platform:platform
      });
      if(error)throw error;
    }else if(enabled==='0'){
      // Le retrait du consentement reste possible même si le token local
      // est invalide ou a été supprimé.
      const {error}=await getSupabase().rpc('security_disable_push_for_device',{p_device_key:deviceKey});
      if(error)throw error;
    }
  }catch{
    // Ne jamais journaliser le message/objet Postgres (JWT, SQL, courriel).
    console.warn('[SINJIRA push bridge] synchronisation indisponible.');
  }
}

// Une désactivation de push ne doit pas être dépassée par une précédente
// inscription encore en vol : séquencer les RPC et rejouer le dernier état.
let syncInFlight=false;
let syncPending=false;
function schedulePushSync(){
  syncPending=true;
  if(syncInFlight)return;
  syncInFlight=true;
  void (async()=>{
    try{
      while(syncPending){
        syncPending=false;
        await syncPushEndpoint();
      }
    }finally{
      syncInFlight=false;
      if(syncPending)schedulePushSync();
    }
  })();
}

window.addEventListener('sinjira:push-changed',schedulePushSync);
schedulePushSync();
