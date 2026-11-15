/* SINJIRA™ — Fracture Déduction simplifiée V39.
 * Décompte strict des soupçons de fin de ronde, PRIVÉ et sans réseau.
 * Ce module n'authentifie pas les joueurs et ne gère ni permissions, ni RLS.
 *
 * Les décisions éditoriales en attente sont EXPLICITES :
 * - allowAbstention : les soupçons peuvent-ils être facultatifs ?
 * - eligibleTargets : quels numéros de sièges sont des cibles admises ?
 * Le serveur doit fournir ces règles approuvées et les bulletins réels,
 * sans jamais remettre les bulletins d'autrui au navigateur.
 * L'agrégat peut aussi être révélateur (surtout en Solo) : NE PAS
 * PUBLIER avant la clôture du scrutin selon les règles approuvées.
 */
import {fractureSeats} from './sinjira-fracture-mechanics-v36.mjs';

function exactInteger(value, label, min, max) {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) ||
      value < min || value > max) {
    throw new RangeError(label+' doit être un entier de '+min+' à '+max+'.');
  }
  return value;
}

export function fractureAggregateSuspicionsV39({
  humans, express=false, roundBallots,
  allowAbstention, eligibleTargets
}={}) {
  // Refuser les conversions implicites du module V36.
  exactInteger(humans,'Humains',1,20);
  const config=fractureSeats(humans,{express});
  if (typeof allowAbstention !== 'boolean') {
    throw new TypeError('La politique de soupçons facultatifs doit être explicite.');
  }
  if (!Array.isArray(eligibleTargets) || eligibleTargets.length===0 ||
      eligibleTargets.length>config.seats ||
      new Set(eligibleTargets).size!==eligibleTargets.length) {
    throw new RangeError('Les cibles autorisées doivent être définies sans doublon.');
  }
  for (const target of eligibleTargets) {
    exactInteger(target,'Siège autorisé',1,config.seats);
  }
  if (!Array.isArray(roundBallots) || roundBallots.length!==config.rounds) {
    throw new RangeError('Toutes les rondes de la partie doivent être fournies.');
  }
  const allowed=new Set(eligibleTargets);
  const totals=Array(config.seats).fill(0);
  const perRound=[];
  let submitted=0, abstentions=0;
  for (let index=0;index<config.rounds;index++) {
    const ballots=roundBallots[index];
    if (!Array.isArray(ballots) || ballots.length!==config.humans) {
      throw new RangeError('Un emplacement de soupçon par humain et par ronde est obligatoire.');
    }
    let roundSubmitted=0, roundAbstentions=0;
    for (const choice of ballots) {
      if (choice===null) {
        if (!allowAbstention) {
          throw new RangeError('Abstention interdite par la politique de la partie.');
        }
        roundAbstentions++;
        continue;
      }
      const target=exactInteger(choice,'Numéro soupçonné',1,config.seats);
      if (!allowed.has(target)) {
        throw new RangeError('Numéro de siège non autorisé par les règles approuvées.');
      }
      totals[target-1]++;
      roundSubmitted++;
    }
    submitted+=roundSubmitted;
    abstentions+=roundAbstentions;
    perRound.push(Object.freeze({
      round:index+1,submitted:roundSubmitted,abstentions:roundAbstentions
    }));
  }
  if (submitted+abstentions!==config.humans*config.rounds) {
    throw new RangeError('Comptage de soupçons incohérent.');
  }
  return Object.freeze({
    version:1,humans:config.humans,seats:config.seats,rounds:config.rounds,
    submitted,abstentions,
    totals:Object.freeze(totals),
    perRound:Object.freeze(perRound)
  });
}
