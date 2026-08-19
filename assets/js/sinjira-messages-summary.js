import {requireCommunityUser,socialErrorStatus} from './sinjira-social-common.js?v=24.4.42';
import {unreadTotal} from './sinjira-message-read-state.js?v=24.4.71';

const realNode=document.querySelector('[data-real-unread]');
const characterNode=document.querySelector('[data-character-unread]');
const status=document.querySelector('[data-social-status]');

function label(count){
  return count>0?`${count} message${count>1?'s':''} non lu${count>1?'s':''}`:'Aucun message non lu';
}

(async()=>{
  try{
    const user=await requireCommunityUser();
    const [realCount,characterCount]=await Promise.all([
      unreadTotal('social_real_messages',user.id),
      unreadTotal('social_character_messages',user.id)
    ]);
    if(realNode)realNode.textContent=label(realCount);
    if(characterNode)characterNode.textContent=label(characterCount);
  }catch(error){
    if(error?.message!=='RULES_REQUIRED'&&error?.message!=='Connexion requise'){
      socialErrorStatus(status,error,'Impossible de charger le nombre de messages non lus.');
    }
  }
})();
