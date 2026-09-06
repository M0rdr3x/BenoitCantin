const DEVICE_KEY_STORAGE='sinjira.security.device_key.v1';
const NATIVE_REQUEST_TYPE='sinjira.device-key.request';
const NATIVE_RESPONSE_EVENT='sinjira:native-device-key-response';
const NATIVE_TIMEOUT_MS=3000;

function randomDeviceKey(){
  if(globalThis.crypto?.randomUUID)return globalThis.crypto.randomUUID();
  const bytes=new Uint8Array(24);
  globalThis.crypto?.getRandomValues?.(bytes);
  return `sinjira-${Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('')}-${Date.now().toString(36)}`;
}

function requestId(){
  if(globalThis.crypto?.randomUUID)return globalThis.crypto.randomUUID();
  const bytes=new Uint8Array(16);
  globalThis.crypto?.getRandomValues?.(bytes);
  return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
}

function nativeBridge(){
  const bridge=globalThis.ReactNativeWebView;
  return bridge&&typeof bridge.postMessage==='function'?bridge:null;
}

function browserDeviceKey(){
  try{
    let value=localStorage.getItem(DEVICE_KEY_STORAGE);
    if(!value){value=randomDeviceKey();localStorage.setItem(DEVICE_KEY_STORAGE,value)}
    return value;
  }catch{
    try{
      let value=sessionStorage.getItem(DEVICE_KEY_STORAGE);
      if(!value){value=randomDeviceKey();sessionStorage.setItem(DEVICE_KEY_STORAGE,value)}
      return value;
    }catch{return randomDeviceKey()}
  }
}

function requestNativeDeviceKey(bridge){
  return new Promise((resolve,reject)=>{
    const id=requestId();
    let finished=false;
    const cleanup=()=>{
      globalThis.removeEventListener(NATIVE_RESPONSE_EVENT,onResponse);
      clearTimeout(timer);
    };
    const finish=(callback,value)=>{
      if(finished)return;
      finished=true;
      cleanup();
      callback(value);
    };
    const onResponse=(event)=>{
      const detail=event?.detail;
      if(!detail||detail.request_id!==id)return;
      if(detail.error){
        finish(reject,Object.assign(new Error('La clé sécurisée de cet appareil est indisponible.'),{code:String(detail.error)}));
        return;
      }
      const key=String(detail.device_key||'');
      if(key.length<16){
        finish(reject,Object.assign(new Error('Réponse de clé appareil invalide.'),{code:'NATIVE_DEVICE_KEY_INVALID'}));
        return;
      }
      finish(resolve,key);
    };
    const timer=setTimeout(()=>finish(reject,Object.assign(new Error('Le pont de sécurité mobile ne répond pas.'),{code:'NATIVE_DEVICE_KEY_TIMEOUT'})),NATIVE_TIMEOUT_MS);
    globalThis.addEventListener(NATIVE_RESPONSE_EVENT,onResponse);
    try{
      bridge.postMessage(JSON.stringify({type:NATIVE_REQUEST_TYPE,request_id:id}));
    }catch{
      finish(reject,Object.assign(new Error('Le pont de sécurité mobile est indisponible.'),{code:'NATIVE_DEVICE_KEY_UNAVAILABLE'}));
    }
  });
}

export async function getDeviceKey(){
  const bridge=nativeBridge();
  if(bridge)return requestNativeDeviceKey(bridge);
  return browserDeviceKey();
}

export async function getDeviceMetadata(){
  const ua=navigator.userAgent||'';
  const platform=String(navigator.userAgentData?.platform||navigator.platform||'').slice(0,120);
  let type='browser';
  if(/iPad|Tablet/i.test(ua))type='tablet';
  else if(/iPhone|iPod/i.test(ua))type='ios';
  else if(/Android/i.test(ua))type='android';
  const browser=/Firefox/i.test(ua)?'Firefox':/Edg\//i.test(ua)?'Edge':/Chrome|CriOS/i.test(ua)?'Chrome':/Safari/i.test(ua)?'Safari':'Navigateur';
  return {
    device_key:await getDeviceKey(),
    display_name:`${browser}${platform?` — ${platform}`:''}`.slice(0,120),
    device_type:type,
    platform
  };
}

export const deviceKeyBoundary={
  storageKey:DEVICE_KEY_STORAGE,
  nativeRequestType:NATIVE_REQUEST_TYPE,
  nativeResponseEvent:NATIVE_RESPONSE_EVENT
};
