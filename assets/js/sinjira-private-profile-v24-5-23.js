import {getSupabase,requireUser,setStatus} from './sinjira-supabase.js';

const form=document.querySelector('[data-private-profile-form]');
const status=document.querySelector('[data-private-profile-status]');
const saveButton=document.querySelector('[data-private-profile-save]');
const resetButton=document.querySelector('[data-private-profile-reset]');
let loadedSnapshot=null;

const FIELD_NAMES=[
  'birth_date','gender','languages',
  'residence_city','residence_region','residence_country',
  'origin_city','origin_region','origin_country',
  'relationship_status','relationship_since','relationship_partner_label'
];

function normalizeLoaded(data={}){
  const out={};
  for(const name of FIELD_NAMES)out[name]=data?.[name]??'';
  out.languages=Array.isArray(data?.languages)?data.languages.join(', '):String(data?.languages||'');
  if(out.relationship_status==='not_set'||out.relationship_status==='not_specified')out.relationship_status='';
  return out;
}

function fillForm(data){
  if(!form)return;
  for(const name of FIELD_NAMES){
    const field=form.elements.namedItem(name);
    if(field)field.value=data?.[name]??'';
  }
}

function splitLanguages(value){
  return [...new Set(String(value||'').split(/[,;\n]+/).map(v=>v.trim()).filter(Boolean))].slice(0,12);
}

function nullable(value){
  const clean=String(value??'').trim();
  return clean||null;
}

function payload(){
  const fd=new FormData(form);
  return {
    p_birth_date:nullable(fd.get('birth_date')),
    p_gender:nullable(fd.get('gender')),
    p_languages:splitLanguages(fd.get('languages')),
    p_residence_city:nullable(fd.get('residence_city')),
    p_residence_region:nullable(fd.get('residence_region')),
    p_residence_country:nullable(fd.get('residence_country')),
    p_origin_city:nullable(fd.get('origin_city')),
    p_origin_region:nullable(fd.get('origin_region')),
    p_origin_country:nullable(fd.get('origin_country')),
    p_relationship_status:nullable(fd.get('relationship_status')),
    p_relationship_since:nullable(fd.get('relationship_since')),
    p_relationship_partner_label:nullable(fd.get('relationship_partner_label'))
  };
}

function userMessage(error){
  const text=String(error?.message||error||'');
  const rules=[
    [/MFA_REQUIRED/i,'Une authentification renforcée est requise avant de modifier votre coffre privé. Ouvrez Sécurité, complétez la vérification demandée, puis revenez ici.'],
    [/AUTH_REQUIRED/i,'Votre session n’est plus valide. Reconnectez-vous puis réessayez.'],
    [/SINJIRA_MINIMUM_AGE_13/i,'La date de naissance indiquée ne respecte pas l’âge minimum actuellement permis pour un Compte SINJIRA™.'],
    [/INVALID_BIRTH_DATE/i,'La date de naissance indiquée n’est pas valide.'],
    [/INVALID_GENDER/i,'La valeur de genre choisie n’est pas valide.'],
    [/INVALID_RELATIONSHIP_STATUS/i,'Le statut relationnel choisi n’est pas valide.'],
    [/INVALID_RELATIONSHIP_DATE/i,'La date de début de la relation ne peut pas être dans le futur.'],
    [/LANGUAGE_VALUE_TOO_LONG/i,'Une langue indiquée est trop longue. Utilisez des noms courts et clairs.'],
    [/PROFILE_VALUE_TOO_LONG/i,'Un des renseignements est trop long. Raccourcissez-le puis réessayez.'],
    [/YOUTH_JURISDICTION_NOT_ENABLED/i,'Pour un compte de moins de 18 ans, SINJIRA™ est actuellement activé seulement pour la juridiction jeunesse prise en charge. Vérifiez la date de naissance et le pays de résidence.'],
    [/GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14/i,'Pour un compte de moins de 14 ans, un lien parent ou tuteur vérifié doit déjà être présent avant d’enregistrer ces renseignements.'],
    [/Could not find the function|PGRST202|schema cache/i,'Le serveur SINJIRA™ doit encore être synchronisé avec l’éditeur du coffre privé.']
  ];
  for(const [pattern,message] of rules)if(pattern.test(text))return message;
  return 'Impossible d’enregistrer les informations personnelles pour le moment. Réessayez plus tard.';
}

function setBusy(busy){
  if(saveButton)saveButton.disabled=busy;
  if(resetButton)resetButton.disabled=busy;
  for(const field of form?.elements||[]){
    if(field===saveButton||field===resetButton)continue;
    field.disabled=busy;
  }
}

async function loadProfile(){
  const s=getSupabase();
  const {data,error}=await s.rpc('private_profile_get');
  if(error)throw error;
  loadedSnapshot=normalizeLoaded(data||{});
  fillForm(loadedSnapshot);
  setStatus(status,'Vous pouvez compléter ou corriger vos informations personnelles. Elles restent dans votre coffre privé.','info');
}

if(form){
  await requireUser();
  try{
    await loadProfile();
  }catch(error){
    setStatus(status,userMessage(error),'error');
  }

  resetButton?.addEventListener('click',()=>{
    if(!loadedSnapshot)return;
    fillForm(loadedSnapshot);
    setStatus(status,'Les modifications non enregistrées ont été annulées.','info');
  });

  form.addEventListener('submit',async event=>{
    event.preventDefault();
    setBusy(true);
    try{
      const s=getSupabase();
      const {data,error}=await s.rpc('private_profile_save',payload());
      if(error)throw error;
      await loadProfile();
      const reconfirm=Boolean(data?.dating_reconfirmation_required||data?.birth_date_changed);
      setStatus(status,reconfirm
        ?'Informations enregistrées. Comme la date de naissance a été corrigée, Rencontres est désactivé jusqu’à une nouvelle confirmation d’admissibilité.'
        :'Informations personnelles enregistrées. Vous pourrez les corriger de nouveau ici si nécessaire.',
      reconfirm?'info':'success');
    }catch(error){
      setStatus(status,userMessage(error),'error');
    }finally{
      setBusy(false);
    }
  });
}
