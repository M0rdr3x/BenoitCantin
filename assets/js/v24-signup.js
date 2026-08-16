import {getSupabase,SINJIRA_CONFIG,isSinjiraBackendConfigured,setStatus} from './sinjira-supabase.js';

const form=document.querySelector('[data-signup-form]');
const status=document.querySelector('[data-account-status]');

function ageOn(dateString){
  const dob=new Date(`${dateString}T00:00:00`);
  if(Number.isNaN(dob.getTime()))return null;
  const now=new Date();
  let age=now.getFullYear()-dob.getFullYear();
  const beforeBirthday=now.getMonth()<dob.getMonth()||(now.getMonth()===dob.getMonth()&&now.getDate()<dob.getDate());
  if(beforeBirthday)age--;
  return age;
}
function nextDestination(def='/compte/index.html'){
  if(window.SINJIRA_AUTH_ROUTE?.next)return window.SINJIRA_AUTH_ROUTE.next(def);
  const value=new URLSearchParams(location.search).get('next');
  if(!value||!value.startsWith('/')||value.startsWith('//')||value.includes('\\')||/[\u0000-\u001f\u007f]/.test(value))return def;
  try{const url=new URL(value,location.origin);return url.origin===location.origin?`${url.pathname}${url.search}${url.hash}`:def}catch{return def}
}

if(form){
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!isSinjiraBackendConfigured()){
      setStatus(status,'Le service de comptes SINJIRA™ est temporairement indisponible.','error');
      return;
    }
    const d=new FormData(form);
    const email=String(d.get('email')||'').trim();
    const password=String(d.get('password')||'');
    const confirm=String(d.get('password_confirm')||'');
    const birthDate=String(d.get('birth_date')||'');
    const age=ageOn(birthDate);
    if(password.length<12){setStatus(status,'Utilisez un mot de passe d’au moins 12 caractères.','error');return}
    if(password!==confirm){setStatus(status,'Les mots de passe ne correspondent pas.','error');return}
    if(age===null){setStatus(status,'Indiquez une date de naissance valide.','error');return}
    if(age<12){setStatus(status,'Les Comptes SINJIRA™ sont réservés aux personnes de 12 ans et plus.','error');return}
    const minor=age<18;
    const languages=String(d.get('languages')||'').split(',').map(x=>x.trim()).filter(Boolean).slice(0,12);
    const wantsQuestionnaire=d.get('wants_character_questionnaire')==='yes';
    const contributor=d.get('initial_contributor_opt_in')==='yes';
    const metadata={
      pseudo:String(d.get('pseudo')||'').trim(),
      display_name:String(d.get('display_name')||'').trim(),
      birth_date:birthDate,
      gender:String(d.get('gender')||''),
      languages,
      residence_city:String(d.get('residence_city')||'').trim(),
      residence_region:String(d.get('residence_region')||'').trim(),
      residence_country:String(d.get('residence_country')||'').trim(),
      origin_city:String(d.get('origin_city')||'').trim(),
      origin_region:String(d.get('origin_region')||'').trim(),
      origin_country:String(d.get('origin_country')||'').trim(),
      relationship_status:String(d.get('relationship_status')||''),
      relationship_since:String(d.get('relationship_since')||''),
      relationship_partner_label:String(d.get('relationship_partner_label')||'').trim(),
      wants_character_questionnaire:wantsQuestionnaire,
      account_age_band:minor?'minor_12_17':'adult_18_plus',
      guardian_controls_required:minor,
      initial_contributor_opt_in:contributor,
      initial_share_free_text:contributor&&d.get('share_free_text')==='yes'
    };
    const destination=wantsQuestionnaire?'/projets/sinjira/registre/':nextDestination();
    const {data,error}=await getSupabase().auth.signUp({
      email,password,
      options:{emailRedirectTo:`${SINJIRA_CONFIG.siteUrl}${destination}`,data:metadata}
    });
    if(error){setStatus(status,'Création du compte impossible. Vérifiez les renseignements ou utilisez une autre adresse courriel.','error');return}
    if(data.session){location.assign(destination);return}
    setStatus(status,wantsQuestionnaire?'Compte créé. Confirmez votre adresse courriel; le lien de confirmation vous mènera ensuite au questionnaire complet du Registre.':'Compte créé. Vérifiez votre courriel pour confirmer votre adresse.','success');
    form.reset();
  });
}
