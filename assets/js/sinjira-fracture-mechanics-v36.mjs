/* SINJIRA™ — Fracture du Réseau-Mère / Déduction simplifiée — V36.
   Mécanique pure du jeu PHYSIQUE, indépendante du serveur.
   Aucun compte, identité, vote nominatif, persistance ou réseau.
   NE PAS utiliser ce module comme contrôle d'autorisation multijoueur.
   Les cartes et les identités secrètes d'une future partie Web doivent
   rester protégées par le backend et ses règles RLS. */

export const FRACTURE_AGENTS=Object.freeze({
  3:1,4:1,5:2,6:2,7:2,8:3,9:3,10:3,11:4,12:4,13:4,14:5,
  15:5,16:5,17:6,18:6,19:6,20:7
});
export const FRACTURE_OPERATION_COUNTS=Object.freeze({1:30,2:12,3:3});
export const FRACTURE_FACTIONS=Object.freeze(['resistance','reseau']);

function integer(value,name,min,max){
  if(value===null||value===undefined||String(value).trim()===''){
    throw new RangeError(name+' est requis.');
  }
  const n=Number(value);
  if(!Number.isSafeInteger(n)||n<min||n>max){
    throw new RangeError(name+' doit être un entier de '+min+' à '+max+'.');
  }
  return n;
}
function immutableArray(values){
  return Object.freeze(values.map(x=>Object.freeze(x)));
}
export function fractureSeats(humans,{express=false,duoFirst=1}={}){
  const h=integer(humans,'Nombre de joueurs humains',1,20);
  if(typeof express!=='boolean')throw new TypeError('Format Express invalide.');
  if(express&&h<13)throw new RangeError('Express exige 13 à 20 joueurs humains.');
  const first=integer(duoFirst,'Premier joueur Duo',1,2);
  const seats=Math.max(3,h);
  const agents=FRACTURE_AGENTS[seats];
  return Object.freeze({
    humans:h,seats,agents,resistance:seats-agents,
    rounds:express?6:10,express,duoFirst:first,
    cardsDealt:3*seats,cardsCentre:2*seats,
    privateReports:seats,proofsMaximum:seats,finalBallots:h*agents
  });
}

/** Les 90 cartes Opération : par faction 30 × 1 pt, 12 × 2 pts, 3 × 3 pts.
    Chaque carte reçoit un identifiant stable uniquement pour détecter un
    doublon à la table ; ce n'est pas un secret ni une identité de joueur. */
export function fractureOperationDeck(){
  const cards=[];
  for(const faction of FRACTURE_FACTIONS){
    for(const points of [1,2,3]){
      for(let copy=1;copy<=FRACTURE_OPERATION_COUNTS[points];copy++){
        cards.push(Object.freeze({
          id:faction+'-'+points+'-'+copy,faction,points
        }));
      }
    }
  }
  return Object.freeze(cards);
}

const CANONICAL_CARDS=fractureOperationDeck();
const CARDS_BY_ID=new Map(CANONICAL_CARDS.map(c=>[c.id,c]));
function checkCard(value,used){
  if(!value||typeof value!=='object')throw new RangeError('Carte Opération invalide.');
  const canonical=CARDS_BY_ID.get(value.id);
  if(!canonical||canonical.faction!==value.faction||
     canonical.points!==value.points){
    throw new RangeError('Carte Opération absente des 90 cartes officielles.');
  }
  if(used.has(value.id))throw new RangeError('Une carte Opération ne peut apparaître deux fois.');
  used.add(value.id);
  return canonical;
}
function checkedCards(cards,expected){
  if(!Array.isArray(cards)||cards.length!==expected){
    throw new RangeError('Quantité incorrecte de cartes Opération : '+expected+' requises.');
  }
  const used=new Set();
  return cards.map(card=>checkCard(card,used));
}

export function fractureValidateDeck(cards){
  return Object.freeze(checkedCards(cards,90));
}

/** Début de ronde : mélanger d'abord les 90 cartes (physiquement ou via une
    source sûre appropriée au futur backend), puis distribuer 3 par siège.
    Ce module ne choisit pas les cartes secrètes à la place des humains. */
export function fractureDealRound(deck,humans,{express=false,duoFirst=1,round=1}={}){
  const config=fractureSeats(humans,{express,duoFirst});
  const roundNo=integer(round,'Numéro de ronde',1,config.rounds);
  const shuffled=fractureValidateDeck(deck);
  const hands=[];
  for(let i=0;i<config.seats;i++){
    hands.push(Object.freeze({
      seat:i+1,cards:Object.freeze(shuffled.slice(i*3,i*3+3))
    }));
  }
  return Object.freeze({
    config,round:roundNo,
    hands:Object.freeze(hands),
    undealt:Object.freeze(shuffled.slice(config.cardsDealt))
  });
}

/** À chaque siège : conserver deux indices distincts parmi les trois.
    La troisième carte est défaussée, hors du centre et hors du score. */
export function fractureBuildCentre(deal,keptBySeat){
  const {config,hands}=deal||{};
  if(!config||!Array.isArray(hands)||hands.length!==config.seats||
     !Array.isArray(keptBySeat)||keptBySeat.length!==config.seats){
    throw new RangeError('Distribution et choix des sièges incompatibles.');
  }
  const center=[],discard=[];
  const all=new Set();
  for(let index=0;index<config.seats;index++){
    const hand=hands[index];
    const kept=keptBySeat[index];
    if(hand?.seat!==index+1||!Array.isArray(hand.cards)||hand.cards.length!==3||
       !Array.isArray(kept)||kept.length!==2){
      throw new RangeError('Il faut deux choix par siège, parmi trois cartes.');
    }
    const first=integer(kept[0],'Choix de carte',0,2);
    const second=integer(kept[1],'Choix de carte',0,2);
    if(first===second)throw new RangeError('Les deux cartes conservées doivent être distinctes.');
    for(const card of hand.cards)checkCard(card,all);
    center.push(hand.cards[first],hand.cards[second]);
    discard.push(hand.cards[[0,1,2].find(i=>i!==first&&i!==second)]);
  }
  if(center.length!==config.cardsCentre||discard.length!==config.seats){
    throw new RangeError('Le centre doit contenir exactement 2N cartes.');
  }
  return Object.freeze({
    config,center:Object.freeze(center),discard:Object.freeze(discard)
  });
}

/** Deux passages, un choix de carte par siège et par passage.
    selections[passage][siège-1] est un index dans les cartes encore au centre
    à l'instant de ce choix (0 signifie la première carte disponible).
    Le paquet reçu en argument DOIT être déjà mélangé par l'arbitre.
    Aucun bot ni choix automatisé de siège invisible. */
export function fractureTwoPasses(shuffledCentre,selections,seats){
  const n=integer(seats,'Sièges actifs',3,20);
  const remaining=checkedCards(shuffledCentre,2*n).slice();
  if(!Array.isArray(selections)||selections.length!==2||
     selections.some(pass=>!Array.isArray(pass)||pass.length!==n)){
    throw new RangeError('Il faut exactement deux passages de N choix.');
  }
  const hands=Array.from({length:n},(_,i)=>({seat:i+1,cards:[]}));
  for(let pass=0;pass<2;pass++){
    for(let seat=0;seat<n;seat++){
      const choice=integer(selections[pass][seat],'Index de carte choisie',0,remaining.length-1);
      hands[seat].cards.push(remaining.splice(choice,1)[0]);
    }
  }
  if(remaining.length!==0||hands.some(hand=>hand.cards.length!==2)){
    throw new RangeError('Les 2N cartes doivent être redistribuées sans reste.');
  }
  return Object.freeze({
    seats:n,hands:immutableArray(hands.map(h=>({
      seat:h.seat,cards:Object.freeze(h.cards)
    }))),remaining:Object.freeze(remaining)
  });
}

/** Calcul public APRÈS révélation et mélange des cartes de tous les sièges.
    La faction imprimée sur la carte marque, pas la faction secrète du siège. */
export function fractureRevealOperationCards(distributed){
  const {hands,seats}=distributed||{};
  const n=integer(seats,'Sièges actifs',3,20);
  if(!Array.isArray(hands)||hands.length!==n){
    throw new RangeError('La distribution doit contenir N sièges.');
  }
  const used=new Set();
  let resistance=0,reseau=0;
  for(let index=0;index<n;index++){
    const hand=hands[index];
    if(hand?.seat!==index+1||!Array.isArray(hand.cards)||hand.cards.length!==2){
      throw new RangeError('Chaque siège doit recevoir exactement deux cartes.');
    }
    for(const card of hand.cards){
      const valid=checkCard(card,used);
      if(valid.faction==='resistance')resistance+=valid.points;
      else reseau+=valid.points;
    }
  }
  return Object.freeze({
    seats:n,scoredCards:2*n,resistance,reseau,
    winner:resistance>reseau?'resistance':reseau>resistance?'reseau':null
  });
}

/** Contrôle humain de sièges invisibles. Ne révèle aucune identité.
    Solo : le seul humain contrôle les trois sièges.
    Duo : siège 3 alterné entre humains à chaque ronde, en commençant
    par le Premier joueur choisi (1 ou 2).
    3–20 humains : chacun contrôle son siège. */
export function fractureSeatController(humans,seat,round,{duoFirst=1,express=false}={}){
  const config=fractureSeats(humans,{duoFirst,express});
  const s=integer(seat,'Siège',1,config.seats);
  const r=integer(round,'Ronde',1,config.rounds);
  if(config.humans===1)return 1;
  if(config.humans===2&&s===3){
    return r%2===1?config.duoFirst:3-config.duoFirst;
  }
  return s;
}
