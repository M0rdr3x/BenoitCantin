/* SINJIRA™ — Fracture V43, garde de contrôle HUMAIN des sièges.
 * Ce module pur ne représente jamais une authentification de compte.
 * Entrées humaines et numéros de siège DOIVENT provenir du serveur,
 * après vérification JWT + session active + membre + appartenance à la partie.
 * Ne jamais accepter actorHumanSeat ou partyId fournis par un navigateur
 * comme identité autoritaire. Ne renvoie aucune faction, main ou carte.
 */
import {
  fractureSeats,
  fractureSeatController
} from './sinjira-fracture-mechanics-v36.mjs';

function exact(value,label,min,max){
  if(typeof value!=='number'||!Number.isSafeInteger(value)||
      value<min||value>max){
    throw new RangeError(label+' doit être un entier de '+min+' à '+max+'.');
  }
  return value;
}

const SEAT_ACTIONS=Object.freeze(['keep','pick','report','proof']);
const BALLOT_ACTIONS=Object.freeze(['suspicion','final-accusation']);

/** Valide le CONTRÔLE du siège demandé, jamais la phase ou la main.
 * Le serveur devra EN PLUS valider phase, tour, version de partie,
 * possession des cartes, Preuve unique, et transaction atomique.
 */
export function fractureAuthorizeSeatActionV43({
  humans,actorHumanSeat,targetSeat,round,
  express=false,duoFirst=1,action
}={}){
  const h=exact(humans,'Humains',1,20);
  exact(duoFirst,'Premier joueur Duo',1,2);
  const cfg=fractureSeats(h,{express,duoFirst});
  const actor=exact(actorHumanSeat,'Siège humain authentifié',1,h);
  const seat=exact(targetSeat,'Siège de l’action',1,cfg.seats);
  const turn=exact(round,'Ronde',1,cfg.rounds);
  if(!SEAT_ACTIONS.includes(action)){
    throw new RangeError('Action de siège invalide ou non prise en charge.');
  }
  const controller=fractureSeatController(h,seat,turn,{express,duoFirst});
  if(controller!==actor){
    throw new RangeError('SEAT_NOT_CONTROLLED');
  }
  return Object.freeze({
    version:1,allowed:true,action,
    humanSeat:actor,targetSeat:seat,round:turn,
    isInvisible:seat>h
  });
}

/** Les bulletins de soupçon et d'accusation sont déposés seulement par
 * de vrais humains, même quand ils contrôlent des sièges invisibles.
 * ballotSeat désigne l'AUTEUR, jamais la cible du soupçon.
 * Les contenus des bulletins doivent être contrôlés par V38–V40.
 */
export function fractureAuthorizeHumanBallotV43({
  humans,actorHumanSeat,ballotSeat,action
}={}){
  const h=exact(humans,'Humains',1,20);
  const actor=exact(actorHumanSeat,'Siège humain authentifié',1,h);
  const seat=exact(ballotSeat,'Auteur du bulletin',1,Math.max(3,h));
  if(!BALLOT_ACTIONS.includes(action)){
    throw new RangeError('Type de bulletin invalide ou non pris en charge.');
  }
  if(seat!==actor){
    throw new RangeError('BALLOT_NOT_OWNED');
  }
  return Object.freeze({
    version:1,allowed:true,action,humanSeat:actor,ballotSeat:seat
  });
}
