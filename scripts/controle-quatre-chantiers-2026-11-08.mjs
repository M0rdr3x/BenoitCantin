#!/usr/bin/env node
/**
 * Vérifie le bilan historique du 8 novembre 2026 dans les données canoniques.
 * Aucune mise à jour des chiffres, aucune connexion ou mutation externe.
 */
import {readFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
export const SOURCES=Object.freeze({
  nova:'projets/projet-nova/data/audit-completude-programme-nova-2026-11-05.json',
  services:'projets/projet-nova/data/registre-donnees-services-nova-sinjira.json',
  civic:'docs/nova-sondages/reception-sondage-boussole-2026-11-08.json',
  sinjira:'docs/sinjira/programme-readiness-2026-11-08.json'
});
function expect(ok,message){if(!ok)throw new Error('BILAN INVALIDE : '+message);}
export function load(root=ROOT){
  return Object.fromEntries(Object.entries(SOURCES).map(([key,path])=>
    [key,JSON.parse(readFileSync(resolve(root,path),'utf8'))]));
}
function received(gates,total,label){
  expect(Array.isArray(gates)&&gates.length===total,label+': dénominateur incorrect');
  expect(new Set(gates.map(g=>g.id)).size===total,label+': identifiant dupliqué');
  expect(gates.every(g=>['PASSED','PENDING'].includes(g.status)),label+': statut inattendu');
  return gates.filter(g=>g.status==='PASSED').length;
}
export function assess({nova,services,civic,sinjira}){
  expect(nova.date==='2026-11-05','date Nova');
  expect(nova.scoring?.legal_government_approval===false,'homologation Nova non démontrée');
  expect(nova.dimensions?.length===10,'dimensions Nova');
  const weight=nova.dimensions.reduce((s,d)=>s+d.weight,0);
  const points=nova.dimensions.reduce((s,d)=>s+d.points,0);
  expect(weight===100&&points===47&&nova.scoring.earned===47&&
    nova.scoring.percentage===47&&nova.scoring.maximum===100,'47/100 incohérent');
  const finance=nova.dimensions.find(d=>d.id==='FINANCES');
  expect(finance?.points===3&&finance?.weight===16,'dossier finances 3/16 incohérent');

  expect(services.date_revue==='2026-11-03','date du registre G0');
  expect(services.dossiers?.length===14,'14 secteurs attendus');
  const ids=services.dossiers.map(d=>d.id);
  expect(new Set(ids).size===14,'dossiers dupliqués');
  for(let n=1;n<=14;n++)
    expect(ids.includes('NV-'+String(n).padStart(2,'0')),'secteur NV-'+n+' absent');

  expect(civic.as_of==='2026-11-08'&&civic.status==='NON_HOMOLOGUE','date/statut citoyens');
  expect(civic.compass.questions===64&&civic.compass.dimensions===16,'questionnaire boussole');
  expect(civic.poll.questions===8,'questionnaire sondage');
  const compassPassed=received(civic.compass.gates,12,'boussole');
  const pollPassed=received(civic.poll.gates,11,'sondage');
  expect(compassPassed===9&&pollPassed===6,'résultats de réception historique');
  expect(civic.compass.comparison_enabled===false&&
    civic.compass.all_mandatory_gates_passed===false&&
    civic.cross_cutting.party_comparison_enabled===false,'comparateur non homologué');
  expect(civic.poll.published_in_source===false&&
    civic.poll.all_mandatory_gates_passed===false&&
    civic.decision.opening_poll_approved===false,'sondage non autorisé');

  expect(sinjira.reference_date==='2026-11-08','date SINJIRA');
  expect(sinjira.domains?.length===10,'10 domaines SINJIRA');
  const denominator=sinjira.domains.reduce((s,d)=>s+d.weight,0);
  const maturity=sinjira.domains.reduce((s,d)=>s+d.weight*d.maturity,0)/100;
  expect(denominator===100&&Math.abs(maturity-66.5)<1e-8,'66,5 pondéré non reproductible');
  expect(sinjira.estimate_uncertainty_percentage_points===10,'incertitude non déclarée');
  expect(sinjira.gates?.length===13&&sinjira.gates.every(g=>g.status==='OPEN'),
    '13 portes ouvertes dans le bilan de référence');
  expect(sinjira.launch.approved===false&&sinjira.forecast.estimated_completion_date===null,
    'lancement ou date certifiés sans preuve');
  return {
    reference_date:'2026-11-08',
    policy_programme:{score_points:points,maximum:100,progress_percent:47,
      finances_points:3,finances_maximum:16,finish_date_certified:null},
    public_services:{sectors:14,autonomous_completion_percent:null,finish_date_certified:null},
    electoral_compass:{questions:64,axes:16,gates_passed:compassPassed,gates_total:12,
      reception_percent:75,party_comparison_enabled:false,finish_date_certified:null},
    citizen_poll:{questions:8,gates_passed:pollPassed,gates_total:11,
      reception_percent:54.5,publicly_open:false,finish_date_certified:null},
    sinjira_platform:{domains:10,maturity_estimate_percent:maturity,
      uncertainty_percentage_points:10,launch_gates_open:13,launch_approved:false,
      finish_date_certified:null}
  };
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  try{console.log(JSON.stringify(assess(load()),null,2));}
  catch(error){console.error(error.message);process.exitCode=1;}
}
