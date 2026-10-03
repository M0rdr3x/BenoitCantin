import {getSupabase,SINJIRA_CONFIG,isSinjiraBackendConfigured,setStatus} from './sinjira-supabase.js';

const form=document.querySelector('[data-signup-form]');
const status=document.querySelector('[data-account-status]');
const backend=document.querySelector('[data-backend-state]');
const sessionWarning=document.querySelector('[data-signup-session-warning]');
const sessionSignOut=document.querySelector('[data-signup-session-signout]');
const birthInput=form?.querySelector('[data-signup-birth-date]');
const guardianWrap=form?.querySelector('[data-guardian-code-wrap]');
const guardianGuide=form?.querySelector('[data-child-guardian-guide]');
const guardianInput=form?.querySelector('[data-guardian-code]');
const contributorPanel=form?.querySelector('[data-contributor-panel]');
const contributorInput=form?.querySelector('[name="initial_contributor_opt_in"]');
const shareFreeTextInput=form?.querySelector('[name="share_free_text"]');
const GUARDIAN_CODE_RE=/^YOUTH-[A-Z0-9]{10}(?:[A-Z0-9]{6})?$/;
const MIN_ACCOUNT_AGE=11;
let busyState=false;
let sessionBoundaryState='checking';

function parseBirthDate(dateString){
  const match=/^(\d{4})-(\d{2})-(\d{2})$/.exec(String(dateString||''));
  if(!match)return null;
  const year=Number(match[1]),month=Number(match[2]),day=Number(match[3]);
  const dob=new Date(year,month-1,day);
  if(dob.getFullYear()!==year||dob.getMonth()!==month-1||dob.getDate()!==day)return null;
  return dob;
}
function ageOn(dateString){
  const dob=parseBirthDate(dateString);
  if(!dob)return null;
  const now=new Date();
  let age=now.getFullYear()-dob.getFullYear();
  const beforeBirthday=now.getMonth()<dob.getMonth()||(now.getMonth()===dob.getMonth()&&now.getDate()<dob.getDate());
  if(beforeBirthday)age--;
  return age;
}
function localDateString(date=new Date()){
  const y=date.getFullYear(),m=String(date.getMonth()+1).padStart(2,'0'),d=String(date.getDate()).padStart(2,'0');
  return `${y}-${m}-${d}`;
}
function nextDestination(def='/compte/index.html'){
  if(window.SINJIRA_AUTH_ROUTE?.next)return window.SINJIRA_AUTH_ROUTE.next(def);
  const value=new URLSearchParams(location.search).get('next');
  if(!value||!value.startsWith('/')||value.startsWith('//')||value.includes('\\')||/[\u0000-\u001f\u007f]/.test(value))return def;
  try{const url=new URL(value,location.origin);return url.origin===location.origin?`${url.pathname}${url.search}${url.hash}`:def}catch{return def}
}
function normalizeGuardianCode(value=''){return String(value).trim().toUpperCase().replace(/\s+/g,'')}
function isCanada(value=''){return ['canada','ca','can'].includes(String(value).trim().toLowerCase())}
function syncSubmitState(){
  const submit=form?.querySelector('[type="submit"]');
  if(submit)submit.disabled=busyState||sessionBoundaryState!=='clear';
}
function setBusy(busy){
  busyState=Boolean(busy);
  form?.setAttribute('aria-busy',busyState?'true':'false');
  syncSubmitState();
}
function ready(){
  const ok=isSinjiraBackendConfigured();
  if(backend)backend.textContent=ok?'Service de comptes sécurisé actif.':'Service de comptes temporairement indisponible.';
  return ok;
}
async function refreshSessionBoundary(){
  if(!isSinjiraBackendConfigured()){
    sessionBoundaryState='clear';
    if(sessionWarning)sessionWarning.hidden=true;
    syncSubmitState();
    return sessionBoundaryState;
  }
  sessionBoundaryState='checking';
  syncSubmitState();
  try{
    const {data,error}=await getSupabase().auth.getSession();
    if(error)throw error;
    sessionBoundaryState=data?.session?.user?'active':'clear';
    if(sessionWarning)sessionWarning.hidden=sessionBoundaryState!=='active';
  }catch(error){
    console.warn('[SINJIRA signup session boundary]',error?.message||error);
    sessionBoundaryState='error';
    if(sessionWarning)sessionWarning.hidden=false;
  }
  syncSubmitState();
  return sessionBoundaryState;
}
function syncYouthControls(){
  const age=ageOn(String(birthInput?.value||''));
  const minor=Number.isInteger(age)&&age>=MIN_ACCOUNT_AGE&&age<18;
  const child=Number.isInteger(age)&&age>=MIN_ACCOUNT_AGE&&age<13;
  const guardianRequired=Number.isInteger(age)&&age>=MIN_ACCOUNT_AGE&&age<14;
  if(guardianGuide)guardianGuide.hidden=!guardianRequired;
  if(guardianWrap&&guardianInput){
    guardianWrap.hidden=!minor;
    guardianInput.required=guardianRequired;
    guardianInput.setAttribute('aria-required',guardianInput.required?'true':'false');
    if(!minor)guardianInput.value='';
  }
  if(contributorPanel){
    contributorPanel.hidden=child;
    if(child)contributorPanel.open=false;
  }
  if(contributorInput){
    contributorInput.disabled=child;
    if(child)contributorInput.checked=false;
  }
  if(shareFreeTextInput){
    shareFreeTextInput.disabled=child;
    if(child)shareFreeTextInput.checked=false;
  }
}
if(birthInput){
  birthInput.max=localDateString();
  birthInput.addEventListener('change',syncYouthControls);
  birthInput.addEventListener('input',syncYouthControls);
}
sessionSignOut?.addEventListener('click',async()=>{
  if(!isSinjiraBackendConfigured())return;
  sessionSignOut.disabled=true;
  try{
    const {error}=await getSupabase().auth.signOut({scope:'local'});
    if(error)throw error;
    const boundary=await refreshSessionBoundary();
    if(boundary==='clear')setStatus(status,'La session précédente est déconnectée. Vous pouvez maintenant créer ce nouveau compte sans mélanger les identités.','success');
    else setStatus(status,'La session active n’a pas pu être séparée de façon sûre. Réessayez avant de créer un nouveau compte.','error');
  }catch(error){
    console.warn('[SINJIRA signup local signout]',error?.message||error);
    sessionBoundaryState='error';
    if(sessionWarning)sessionWarning.hidden=false;
    syncSubmitState();
    setStatus(status,'Impossible de déconnecter la session active de façon sûre. Aucun nouveau compte ne sera créé tant que cette séparation n’est pas confirmée.','error');
  }finally{sessionSignOut.disabled=false}
});
syncYouthControls();
ready();
syncSubmitState();
await refreshSessionBoundary();

if(form){
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    const boundary=await refreshSessionBoundary();
    if(boundary==='active'){
      setStatus(status,'Un compte est déjà connecté dans ce navigateur. Déconnectez d’abord la session active pour éviter de mélanger le compte du parent et le nouveau compte.','error');
      return;
    }
    if(boundary==='error'){
      setStatus(status,'SINJIRA™ ne peut pas confirmer que la session du navigateur est libre. Par sécurité, la création d’un nouveau compte est bloquée pour le moment.','error');
      return;
    }
    if(!form.checkValidity()){form.reportValidity();return}
    if(!ready()){
      setStatus(status,'Le service de comptes SINJIRA™ est temporairement indisponible.','error');
      return;
    }
    const d=new FormData(form);
    const displayName=String(d.get('display_name')||'').trim();
    const email=String(d.get('email')||'').trim();
    const password=String(d.get('password')||'');
    const confirm=String(d.get('password_confirm')||'');
    const birthDate=String(d.get('birth_date')||'');
    const gender=String(d.get('gender')||'').trim();
    const guardianCode=normalizeGuardianCode(d.get('guardian_code')||'');
    const residenceCountry=String(d.get('residence_country')||'').trim();
    const age=ageOn(birthDate);
    if(!displayName){setStatus(status,'Choisissez le nom à afficher sur votre profil.','error');return}
    if(password.length<12){setStatus(status,'Utilisez un mot de passe d’au moins 12 caractères.','error');return}
    if(password!==confirm){setStatus(status,'Les mots de passe ne correspondent pas.','error');return}
    if(age===null||age<0){setStatus(status,'Indiquez une date de naissance valide.','error');return}
    if(age<MIN_ACCOUNT_AGE){setStatus(status,'Les Comptes SINJIRA™ supervisés sont disponibles à partir de 11 ans.','error');return}
    if(age>120){setStatus(status,'La date de naissance indiquée n’est pas valide.','error');return}
    if(age<18&&!isCanada(residenceCountry)){setStatus(status,'Pour le moment, les comptes jeunesse de 11 à 17 ans sont disponibles uniquement pour les personnes résidant au Canada. Les autres juridictions jeunesse resteront fermées jusqu’à leur validation spécifique.','error');return}
    if(!['Femme','Homme'].includes(gender)){setStatus(status,'Choisissez Femme ou Homme pour ce profil.','error');return}
    if(age<14&&!guardianCode){setStatus(status,'De 11 à 13 ans, un code parental est obligatoire. Le parent ou tuteur adulte doit se connecter à son Compte SINJIRA™, ouvrir Relations, générer un code à usage unique, puis vous le remettre.','error');return}
    if(guardianCode&&!GUARDIAN_CODE_RE.test(guardianCode)){setStatus(status,'Utilisez le code parental exactement tel qu’il a été généré depuis le compte adulte du parent ou tuteur.','error');return}
    const minor=age<18;
    const child=age<13;
    const languages=String(d.get('languages')||'').split(',').map(x=>x.trim()).filter(Boolean).slice(0,12);
    const wantsQuestionnaire=d.get('wants_character_questionnaire')==='yes';
    const contributor=!child&&d.get('initial_contributor_opt_in')==='yes';
    const legacySex=gender==='Femme'?'female':'male';
    const metadata={
      // `pseudo` demeure un champ de compatibilité et reçoit le nom affiché.
      // L’identifiant technique du compte est généré côté serveur dans private.account_identities.
      pseudo:displayName,
      display_name:displayName,
      birth_date:birthDate,
      date_of_birth:birthDate,
      gender,
      sex:legacySex,
      guardian_code:guardianCode,
      languages,
      residence_city:String(d.get('residence_city')||'').trim(),
      residence_region:String(d.get('residence_region')||'').trim(),
      residence_country:residenceCountry,
      origin_city:String(d.get('origin_city')||'').trim(),
      origin_region:String(d.get('origin_region')||'').trim(),
      origin_country:String(d.get('origin_country')||'').trim(),
      relationship_status:String(d.get('relationship_status')||''),
      relationship_since:String(d.get('relationship_since')||''),
      relationship_partner_label:String(d.get('relationship_partner_label')||'').trim(),
      wants_character_questionnaire:wantsQuestionnaire,
      account_age_band:child?'child_11_12':minor?'minor_13_17':'adult_18_plus',
      guardian_controls_required:minor,
      initial_contributor_opt_in:contributor,
      initial_share_free_text:contributor&&d.get('share_free_text')==='yes'
    };
    const destination=wantsQuestionnaire?'/projets/sinjira/registre/':nextDestination();
    setBusy(true);
    try{
      const {data,error}=await getSupabase().auth.signUp({email,password,options:{emailRedirectTo:`${SINJIRA_CONFIG.siteUrl}${destination}`,data:metadata}});
      if(error){
        const raw=String(error.message||'');
        if(/GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14|INVALID_OR_EXPIRED_GUARDIAN_CODE|ADULT_GUARDIAN_REQUIRED/i.test(raw)){
          setStatus(status,'Le code parental est absent, expiré, déjà utilisé ou ne provient pas d’un compte adulte valide. Le parent ou tuteur doit en générer un nouveau depuis Compte SINJIRA™ → Relations.','error');
        }else if(/SINJIRA_MINIMUM_AGE_11/i.test(raw)){
          setStatus(status,'Les Comptes SINJIRA™ supervisés sont disponibles à partir de 11 ans.','error');
        }else if(/YOUTH_JURISDICTION_NOT_ENABLED/i.test(raw)){
          setStatus(status,'Les comptes jeunesse sont actuellement activés uniquement pour le Canada.','error');
        }else setStatus(status,'Création du compte impossible. Vérifiez les renseignements ou utilisez une autre adresse courriel.','error');
        return;
      }
      if(data.session){location.assign(destination);return}
      const childNote=child?' Le compte enfant restera sous supervision parentale et ses fonctions sociales seront désactivées jusqu’à 13 ans.':'';
      const youthNote=age>=14&&age<18&&!guardianCode?' Les fonctions sociales resteront protégées jusqu’à la vérification d’un parent ou tuteur.':'';
      setStatus(status,(wantsQuestionnaire?'Compte créé. Confirmez votre adresse courriel; le lien de confirmation vous mènera ensuite au questionnaire complet du Registre.':'Compte créé. Vérifiez votre courriel pour confirmer votre adresse.')+childNote+youthNote,'success');
      form.reset();syncYouthControls();
    }catch(err){
      console.warn('[SINJIRA signup]',err);
      setStatus(status,'Création du compte impossible pour le moment. Réessayez dans quelques instants.','error');
    }finally{setBusy(false)}
  });
}
