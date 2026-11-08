/* SINJIRA™ — Fracture du Réseau-Mère / Déduction simplifiée — V37.
   Séquence déterministe de rapports publics et Preuve unique par siège.
   Mécanique PURE : aucune identité, session, compte, réseau ou persistance.
   Une future API DOIT conserver l'état et les mains côté serveur, vérifier
   l'identité de l'appelant et le siège contrôlé, puis vérifier la carte
   contre la main authentique AVANT d'appeler fractureResolveProofV37.
   Ne jamais traiter un état ou une main venant du navigateur comme fiables. */
import {fractureSeats,fractureOperationDeck} from './sinjira-fracture-mechanics-v36.mjs';

export const FRACTURE_PUBLIC_REPORTS=Object.freeze(['resistance','reseau','equilibre']);
const CANONICAL_CARDS=new Map(fractureOperationDeck().map(card=>[card.id,card]));

function seatNumber(value,max,label='Siège'){
  if(typeof value!=='number'||!Number.isSafeInteger(value)||value<1||value>max){
    throw new RangeError(label+' doit être un entier de 1 à '+max+'.');
  }
  return value;
}
function immutableState({humans,seats,round,rounds,seatOrder,usedProofSeats,reports,phase,nextSeat}){
  return Object.freeze({
    version:1,humans,seats,round,rounds,
    seatOrder:Object.freeze([...seatOrder]),
    usedProofSeats:Object.freeze([...usedProofSeats]),
    reports:Object.freeze(reports.map(entry=>Object.freeze({...entry}))),
    phase,nextSeat
  });
}
function assertTrustedState(state,expectedPhase){
  // Validation structurelle, PAS une vérification d'authenticité.
  // Le backend doit charger son état depuis un espace serveur protégé.
  if(!state||state.version!==1||state.phase!==expectedPhase||
    !Array.isArray(state.seatOrder)||!Array.isArray(state.usedProofSeats)||
    !Array.isArray(state.reports)||state.seatOrder.length!==state.seats||
    !Number.isSafeInteger(state.seats)||state.seats<3||state.seats>20){
    throw new RangeError('État de rapports invalide ou phase incorrecte.');
  }
}
function canonicalCard(value){
  if(!value||typeof value!=='object')throw new RangeError('Carte de Preuve invalide.');
  const card=CANONICAL_CARDS.get(value.id);
  if(!card||value.faction!==card.faction||value.points!==card.points){
    throw new RangeError('Carte de Preuve non officielle.');
  }
  return card;
}

/** État PUBLIC pour une seule ronde. L'ordre des sièges est explicite.
    usedProofSeats doit provenir du registre SERVEUR de toute la partie. */
export function fractureStartPublicReportsV37(humans,{
  round=1,express=false,duoFirst=1,seatOrder=null,usedProofSeats=[]
}={}){
  const config=fractureSeats(humans,{express,duoFirst});
  seatNumber(round,config.rounds,'Ronde');
  const order=seatOrder===null?
    Array.from({length:config.seats},(_,index)=>index+1):seatOrder;
  if(!Array.isArray(order)||order.length!==config.seats||
     new Set(order).size!==config.seats){
    throw new RangeError('Ordre de sièges incomplet ou dupliqué.');
  }
  for(const seat of order)seatNumber(seat,config.seats);
  if(!Array.isArray(usedProofSeats)||new Set(usedProofSeats).size!==usedProofSeats.length){
    throw new RangeError('Registre de Preuves invalides ou dupliquées.');
  }
  for(const seat of usedProofSeats)seatNumber(seat,config.seats);
  return immutableState({humans:config.humans,seats:config.seats,
    round,rounds:config.rounds,seatOrder:order,usedProofSeats,
    reports:[],phase:'report',nextSeat:order[0]});
}

/** Le rapport peut être volontairement mensonger : aucun contrôle contre
    la véritable main ne doit être fait ici. */
export function fractureSubmitPublicReportV37(state,{seat,report}={}){
  assertTrustedState(state,'report');
  seatNumber(seat,state.seats);
  if(seat!==state.nextSeat||!FRACTURE_PUBLIC_REPORTS.includes(report)){
    throw new RangeError('Rapport invalide ou siège hors de son tour.');
  }
  return immutableState({...state,
    reports:[...state.reports,{seat,report,proof:null}],
    phase:'proof',nextSeat:seat});
}

/** Résolution immédiatement après le rapport du siège.
    proofId=null signifie que la Preuve est déclinée pour cette ronde.
    Sinon receivedCards est la main PRIVÉE de 2 cartes fournie par le SERVEUR;
    seule la carte délibérément révélée figure dans le nouvel état PUBLIC. */
export function fractureResolveProofV37(state,{
  seat,proofId=null,receivedCards=null
}={}){
  assertTrustedState(state,'proof');
  seatNumber(seat,state.seats);
  if(seat!==state.nextSeat||state.reports.at(-1)?.seat!==seat){
    throw new RangeError('La Preuve doit suivre immédiatement le rapport du siège.');
  }
  let proof=null;
  let used=state.usedProofSeats;
  if(proofId!==null){
    if(typeof proofId!=='string'||!CANONICAL_CARDS.has(proofId)){
      throw new RangeError('Identifiant de carte Preuve invalide.');
    }
    if(used.includes(seat))throw new RangeError('Preuve déjà utilisée par ce siège.');
    if(!Array.isArray(receivedCards)||receivedCards.length!==2){
      throw new RangeError('Main privée de deux cartes requise côté serveur.');
    }
    const hand=receivedCards.map(canonicalCard);
    if(hand[0].id===hand[1].id||!hand.some(card=>card.id===proofId)){
      throw new RangeError('Preuve absente de la main authentifiée du siège.');
    }
    proof=CANONICAL_CARDS.get(proofId);
    used=[...used,seat];
  }else if(receivedCards!==null){
    throw new RangeError('Ne pas fournir de main privée sans Preuve révélée.');
  }
  const reports=[...state.reports];
  reports[reports.length-1]={...reports.at(-1),proof};
  const nextIndex=reports.length;
  const finished=nextIndex===state.seats;
  return immutableState({...state,reports,usedProofSeats:used,
    phase:finished?'complete':'report',
    nextSeat:finished?null:state.seatOrder[nextIndex]});
}
