/* SINJIRA™ — Fracture Déduction simplifiée V38.
 * Décompte des accusations finales HUMAINES, sans réseau ni identité.
 * Données d'entrée PRIVÉES. Ne jamais appeler depuis un navigateur
 * avec les votes confidentiels d'autres joueurs.
 * Le serveur doit authentifier les votants, fermer le scrutin et charger
 * les soupçons cumulés depuis une source fiable AVANT ce décompte.
 * Aucun tirage au sort n'est effectué ici; il doit être auditable côté serveur.
 */
import {fractureSeats} from './sinjira-fracture-mechanics-v36.mjs';

function strictSeat(value,max,label){
  if(typeof value!=='number'||!Number.isSafeInteger(value)||value<1||value>max){
    throw new RangeError(label+' doit être un entier de 1 à '+max+'.');
  }
  return value;
}
function validSuspicions(suspicions,seats){
  if(suspicions===null)return Array(seats).fill(0);
  if(!Array.isArray(suspicions)||suspicions.length!==seats){
    throw new RangeError('Les soupçons cumulés doivent couvrir chaque siège.');
  }
  return suspicions.map((count)=>{
    if(typeof count!=='number'||!Number.isSafeInteger(count)||count<0){
      throw new RangeError('Cumul de soupçons invalide.');
    }
    return count;
  });
}

/** Ne retourne JAMAIS les bulletins individuels. Les bulletins sont fournis
 *  dans l'ordre des humains 1..H, pas dans l'ordre des sièges invisibles.
 *  Les égalités au seuil sont départagées d'abord par les soupçons cumulés;
 *  une égalité restante est signalée pour tirage externe, sans Math.random.
 */
export function fractureAggregateFinalBallotsV38(humans,ballots,{suspicionTotals=null}={}){
  const cfg=fractureSeats(humans);
  if(!Array.isArray(ballots)||ballots.length!==cfg.humans){
    throw new RangeError('Un bulletin par joueur humain est obligatoire.');
  }
  const suspicions=validSuspicions(suspicionTotals,cfg.seats);
  const counts=Array(cfg.seats).fill(0);
  for(let human=1;human<=cfg.humans;human++){
    const targets=ballots[human-1];
    if(!Array.isArray(targets)||targets.length!==cfg.agents){
      throw new RangeError('Chaque humain doit accuser exactement '+cfg.agents+' siège(s).');
    }
    const distinct=new Set();
    for(const target of targets){
      strictSeat(target,cfg.seats,'Cible');
      if(target===human)throw new RangeError('Un humain ne peut pas s’accuser lui-même.');
      if(distinct.has(target))throw new RangeError('Une cible ne peut pas être répétée sur un bulletin.');
      distinct.add(target);
      counts[target-1]++;
    }
  }
  const ranked=Array.from({length:cfg.seats},(_,i)=>Object.freeze({
    seat:i+1,votes:counts[i],suspicions:suspicions[i]
  })).sort((a,b)=>b.votes-a.votes||b.suspicions-a.suspicions||a.seat-b.seat);
  const cutoff=ranked[cfg.agents-1];
  const strictlyAbove=ranked.filter(x=>x.votes>cutoff.votes||
    (x.votes===cutoff.votes&&x.suspicions>cutoff.suspicions));
  const tied=ranked.filter(x=>x.votes===cutoff.votes&&x.suspicions===cutoff.suspicions);
  const tieSlots=cfg.agents-strictlyAbove.length;
  const drawRequired=tied.length>tieSlots;
  const selected=drawRequired?strictlyAbove.map(x=>x.seat):ranked.slice(0,cfg.agents).map(x=>x.seat);
  return Object.freeze({
    version:1,humans:cfg.humans,seats:cfg.seats,agents:cfg.agents,
    ballotCount:cfg.humans*cfg.agents,
    status:drawRequired?'draw-required':'resolved',
    selected:Object.freeze(selected),
    tied:Object.freeze(drawRequired?tied.map(x=>x.seat):[]),
    tieSlots:drawRequired?tieSlots:0,
    aggregates:Object.freeze(ranked)
  });
}

/** Le tirage des sièges ex æquo est fait exclusivement par un serveur fiable.
 *  chosenSeats = gagnants du tirage (pas la liste de tous les ex æquo).
 *  Aucun générateur aléatoire ni fournisseur d'identité dans cette fonction.
 */
export function fractureApplyFinalDrawV38(tally,chosenSeats){
  if(!tally||tally.version!==1||tally.status!=='draw-required'||
    !Array.isArray(tally.selected)||!Array.isArray(tally.tied)||
    !Number.isSafeInteger(tally.agents)||!Number.isSafeInteger(tally.seats)||
    !Number.isSafeInteger(tally.tieSlots)||tally.tieSlots<1||
    tally.selected.length+tally.tieSlots!==tally.agents){
    throw new RangeError('Tirage non nécessaire ou décompte invalide.');
  }
  if(!Array.isArray(chosenSeats)||chosenSeats.length!==tally.tieSlots||
    new Set(chosenSeats).size!==chosenSeats.length){
    throw new RangeError('Résultat de tirage incomplet ou dupliqué.');
  }
  for(const seat of chosenSeats){
    strictSeat(seat,tally.seats,'Siège tiré');
    if(!tally.tied.includes(seat)||tally.selected.includes(seat)){
      throw new RangeError('Le siège tiré ne fait pas partie des ex æquo.');
    }
  }
  return Object.freeze({
    version:1,status:'resolved',humans:tally.humans,seats:tally.seats,
    agents:tally.agents,ballotCount:tally.ballotCount,
    selected:Object.freeze([...tally.selected,...chosenSeats]),
    tied:Object.freeze([]),tieSlots:0,aggregates:tally.aggregates
  });
}
