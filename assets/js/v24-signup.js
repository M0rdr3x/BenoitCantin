import {getSupabase,SINJIRA_CONFIG,isSinjiraBackendConfigured,setStatus} from './sinjira-supabase.js';

const form=document.querySelector('[data-signup-form]');
const status=document.querySelector('[data-account-status]');
const backend=document.querySelector('[data-backend-state]');
const birthInput=form?.querySelector('[data-signup-birth-date]');
const guardianWrap=form?.querySelector('[data-guardian-code-wrap]');
const guardianInput=form?.querySelector('[data-guardian-code]');
const GUARDIAN_CODE_RE=/^YOUTH-[A-Z0-9]{10}$/;

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
function setBusy(busy){
  form?.setAttribute('aria-busy',busy?'true':'false');
  const submit=form?.querySelector('[type="submit"]');
  if(submit)submit.disabled=Boolean(busy);
}
function ready(){
  const ok=isSinjiraBackendConfigured();
  if(backend)backend.textContent=ok?'Service de comptes sécurisé actif.':'Service de comptes temporairement indisponible.';
  return ok;
}
function syncYouthControls(){
  if(!guardianWrap||!guardianInput)return;
  const age=ageOn(String(birthInput?.value||''));
  const youth=Number.isInteger(age)&&age>=13&&age<18;
  guardianWrap.hidden=!youth;
  guardianInput.required=Number.isInteger(age)&&age>=13&&age<14;
  guardianInput.setAttribute('aria-required',guardianInput.required?'true':'false');
  if(!youth)guardianInput.value='';
}
if(birthInput){
  birthInput.max=localDateString();
  birthInput.addEventListener('change',syncYouthControls);
  birthInput.addEventListener('input',syncYouthControls);
}
syncYouthControls();
ready();

if(form){
  form.addEventListener('submit',async e=>{
    e.preventDefault();
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
    if(age<13){setStatus(status,'Les Comptes SINJIRA™ sont réservés aux personnes de 13 ans et plus.','error');return}
    if(age>120){setStatus(status,'La date de naissance indiquée n’est pas valide.','error');return}
    if(age<18&&!isCanada(residenceCountry)){setStatus(status,'Pour le moment, les comptes jeunesse de 13 à 17 ans sont disponibles uniquement pour les personnes résidant au Canada. Les autres juridictions jeunesse resteront fermées jusqu’à leur validation spécifique.','error');return}
    if(!['Femme','Homme'].includes(gender)){setStatus(status,'Choisissez Femme ou Homme pour ce profil.','error');return}
    if(age<14&&!guardianCode){setStatus(status,'Pour un compte de 13 ans, un code d’autorisation créé par un parent ou tuteur adulte est obligatoire.','error');return}
    if(guardianCode&&!GUARDIAN_CODE_RE.test(guardianCode)){setStatus(status,'Le code parental doit respecter le format YOUTH-XXXXXXXXXX.','error');return}
    const minor=age<18;
    const languages=String(d.get('languages')||'').split(',').map(x=>x.trim()).filter(Boolean).slice(0,12);
    const wantsQuestionnaire=d.get('wants_character_questionnaire')==='yes';
    const contributor=d.get('initial_contributor_opt_in')==='yes';
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
      account_age_band:minor?'minor_13_17':'adult_18_plus',
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
          setStatus(status,'Le code d’autorisation parentale est absent, expiré ou invalide. Demandez au parent ou tuteur d’en générer un nouveau depuis son Compte SINJIRA™.','error');
        }else if(/YOUTH_JURISDICTION_NOT_ENABLED/i.test(raw)){
          setStatus(status,'Les comptes jeunesse sont actuellement activés uniquement pour le Canada.','error');
        }else setStatus(status,'Création du compte impossible. Vérifiez les renseignements ou utilisez une autre adresse courriel.','error');
        return;
      }
      if(data.session){location.assign(destination);return}
      const youthNote=age>=14&&age<18&&!guardianCode?' Les fonctions sociales resteront protégées jusqu’à la vérification d’un parent ou tuteur.':'';
      setStatus(status,(wantsQuestionnaire?'Compte créé. Confirmez votre adresse courriel; le lien de confirmation vous mènera ensuite au questionnaire complet du Registre.':'Compte créé. Vérifiez votre courriel pour confirmer votre adresse.')+youthNote,'success');
      form.reset();syncYouthControls();
    }catch(err){
      console.warn('[SINJIRA signup]',err);
      setStatus(status,'Création du compte impossible pour le moment. Réessayez dans quelques instants.','error');
    }finally{setBusy(false)}
  });
}
