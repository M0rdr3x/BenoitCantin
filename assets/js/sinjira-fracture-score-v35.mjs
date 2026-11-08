/* SINJIRA™ — Fracture du Réseau-Mère, Déduction simplifiée.
   Calculs de la feuille de score pour parties physiques. Sans identité, compte,
   synchronisation, aucune persistance ni accès au moteur multijoueur suspendu. */
export const RESEAU_AGENTS=Object.freeze({
  3:1,4:1,5:2,6:2,7:2,8:3,9:3,10:3,11:4,12:4,13:4,14:5,
  15:5,16:5,17:6,18:6,19:6,20:7
});
export const POINTS_PAR_ACCUSATION=3;
export const CARTES_PAR_FACTION=Object.freeze({unPoint:30,deuxPoints:12,troisPoints:3});

/** Les 90 cartes comprennent deux lots identiques de 45 (30×1, 12×2, 3×3).
    La somme maximale à N sièges ne correspond donc pas à 2N×3 : il n'existe
    que six cartes de 3 points et vingt-quatre de 2 points au total. */
function maxScoreForCards(count){
  const threes=Math.min(count,6);
  const twos=Math.min(Math.max(0,count-threes),24);
  const ones=count-threes-twos;
  return threes*3+twos*2+ones;
}

const SCORE_POSSIBLE_PAR_FACTION=Array.from({length:41},()=>new Set());
for(let un=0;un<=30;un++)for(let deux=0;deux<=12;deux++){
  for(let trois=0;trois<=3;trois++){
    const cards=un+deux+trois;
    if(cards>40)continue;
    SCORE_POSSIBLE_PAR_FACTION[cards].add(un+2*deux+3*trois);
  }
}
function possibleOperationScores(cardCount,resistance,reseau){
  for(let resistanceCards=0;resistanceCards<=cardCount;resistanceCards++){
    const reseauCards=cardCount-resistanceCards;
    if(SCORE_POSSIBLE_PAR_FACTION[resistanceCards]?.has(resistance)&&
       SCORE_POSSIBLE_PAR_FACTION[reseauCards]?.has(reseau))return true;
  }
  return false;
}

function integer(value,label,min,max){
  // Éviter que Number('') ou Number(null) soit interprété comme un zéro saisi.
  if(value===null||value===undefined||String(value).trim()===''){
    throw new RangeError(label+' requis.');
  }
  const n=Number(value);
  if(!Number.isSafeInteger(n)||n<min||n>max){
    throw new RangeError(label+' doit être un entier de '+min+' à '+max+'.');
  }
  return n;
}

/** N sièges, 3N cartes distribuées, 2N cartes au centre puis 2 passages. */
export function fractureConfiguration(humans,{express=false}={}){
  const h=integer(humans,'Nombre de joueurs humains',1,20);
  if(typeof express!=='boolean')throw new TypeError('Format Express invalide.');
  if(express&&h<13)throw new RangeError('Le format Express est réservé à 13 à 20 joueurs.');
  const seats=Math.max(3,h);
  const agents=RESEAU_AGENTS[seats];
  return Object.freeze({
    humans:h,seats,agents,resistance:seats-agents,
    rounds:express?6:10,express,
    dealtCards:3*seats,centralCards:2*seats,
    minRoundPoints:2*seats,maxRoundPoints:maxScoreForCards(2*seats),
    ballots:h*agents
  });
}

/** Chaque carte Opération récupérée marque 1, 2 ou 3 points;
    les 2N cartes sont toutes prises en règle standard. */
export function fractureRound(config,values){
  if(!values||typeof values!=='object')throw new RangeError('Scores de la ronde requis.');
  const max=config.maxRoundPoints;
  const resistance=integer(values.resistance,'Points Résistance',0,max);
  const reseau=integer(values.reseau,'Points Réseau-Mère',0,max);
  const total=resistance+reseau;
  if(total<config.minRoundPoints||total>max){
    throw new RangeError('Total impossible : les '+config.centralCards+
      ' cartes récupérées doivent rapporter '+config.minRoundPoints+
      ' à '+max+' points pour les deux camps réunis.');
  }
  if(!possibleOperationScores(config.centralCards,resistance,reseau)){
    throw new RangeError('Scores impossibles avec les 45 cartes par faction '+
      '(30×1 point, 12×2 points, 3×3 points). Vérifiez les cartes révélées.');
  }
  return Object.freeze({
    resistance,reseau,total,
    winningFaction:resistance>reseau?'resistance':reseau>resistance?'reseau':'egalite'
  });
}

/** La feuille comptabilise les cartes puis les accusations finales. Elle ne
    connaît ni les identités ni les votes : uniquement leur bilan chiffré.
    Les rondes manquantes sont null. Les rondes non nulles sont validées. */
export function fractureScore({humans,express=false,rounds=[],correct=null,incorrect=null}){
  const config=fractureConfiguration(humans,{express});
  if(!Array.isArray(rounds)||rounds.length>config.rounds){
    throw new RangeError('Nombre de rondes incompatible avec le format choisi.');
  }
  let resistance=0,reseau=0,resistanceWins=0,reseauWins=0,played=0;
  for(const entry of rounds){
    if(entry===null||entry===undefined)continue;
    const round=fractureRound(config,entry);
    played++;
    resistance+=round.resistance;reseau+=round.reseau;
    if(round.winningFaction==='resistance')resistanceWins++;
    if(round.winningFaction==='reseau')reseauWins++;
  }
  const completed=played===config.rounds;
  const base={config,played,completed,
    operation:{resistance,reseau},
    roundWins:{resistance:resistanceWins,reseau:reseauWins}};
  if(!completed)return {...base,status:'incomplete',bonus:null,totals:null,winner:null};
  if(correct===null&&incorrect===null){
    return {...base,status:'awaiting-accusations',bonus:null,totals:null,winner:null};
  }
  const successes=integer(correct,'Accusations correctes',0,config.ballots);
  const errors=integer(incorrect,'Accusations erronées',0,config.ballots);
  if(successes+errors!==config.ballots){
    throw new RangeError('Chaque joueur humain doit déposer '+config.agents+
      ' accusation(s) : le total doit être exactement '+config.ballots+
      '. Aucun vote n’est ajouté pour les sièges invisibles.');
  }
  const bonus={resistance:POINTS_PAR_ACCUSATION*successes,
    reseau:POINTS_PAR_ACCUSATION*errors};
  const totals={resistance:resistance+bonus.resistance,reseau:reseau+bonus.reseau};
  const winner=totals.resistance>totals.reseau?'resistance':
    totals.reseau>totals.resistance?'reseau':
    resistanceWins>reseauWins?'resistance':
    reseauWins>resistanceWins?'reseau':null;
  return {...base,status:winner?'finished':'tie-breaker',bonus,totals,winner};
}
