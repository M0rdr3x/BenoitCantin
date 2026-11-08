/* SINJIRA — Fracture V40, politique de soupçons PAR HUMAIN.
 * Calcul privé uniquement. Ne pas importer dans une interface qui reçoit
 * les bulletins confidentiels d'autrui, ni exposer les agrégats en direct.
 * Le backend garde la responsabilité JWT, session, sièges, état et RLS.
 */
import {fractureAggregateSuspicionsV39} from './sinjira-fracture-soupcons-v39.mjs';

function seatNumber(value,label,min,max){
  if(typeof value!=='number'||!Number.isSafeInteger(value)||
      value<min||value>max){
    throw new RangeError(label+' doit être un entier de '+min+' à '+max+'.');
  }
  return value;
}

/** L'ordre des humains est contractuellement 1..humans.
 * Le serveur doit résoudre les numéros de sièges depuis sa propre table,
 * et ne JAMAIS se fier à une identité/numéro fourni par le client.
 *
 * allowSelfSuspicion est une décision de règles explicite; sa valeur ne peut
 * pas être déduite de eligibleTargets qui est une liste commune à la table.
 * Le dépouillement V39 vérifie ensuite toutes les rondes et les cumuls.
 */
export function fractureAggregateSeatSafeSuspicionsV40({
  humans,express=false,roundBallots,
  allowAbstention,allowSelfSuspicion,eligibleTargets
}={}){
  seatNumber(humans,'Humains',1,20);
  if(typeof allowSelfSuspicion!=='boolean'){
    throw new TypeError('La politique d’auto-soupçon doit être explicite.');
  }
  if(!Array.isArray(roundBallots)){
    throw new RangeError('Bulletins de soupçons obligatoires.');
  }
  // Le contrat V39 refusera toute ronde manquante ou surnuméraire.
  // Cette validation ne préjuge PAS du droit d'un joueur à son siège.
  const seats=Math.max(3,humans);
  for(const round of roundBallots){
    if(!Array.isArray(round)||round.length!==humans){
      throw new RangeError('Un choix par humain et par ronde est requis.');
    }
    for(let i=0;i<humans;i++){
      const choice=round[i];
      if(choice===null)continue; // Le droit d'abstention est contrôlé par V39.
      seatNumber(choice,'Numéro soupçonné',1,seats);
      if(!allowSelfSuspicion&&choice===i+1){
        throw new RangeError('Auto-soupçon interdit par la politique de la partie.');
      }
    }
  }
  return fractureAggregateSuspicionsV39({
    humans,express,roundBallots,allowAbstention,eligibleTargets
  });
}
