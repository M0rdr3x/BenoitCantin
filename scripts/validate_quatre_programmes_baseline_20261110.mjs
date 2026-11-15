/**
 * Provenance du bilan multi-projets au 8 novembre 2026.
 * Données UNIQUEMENT issues des registres GitHub datés; aucun % de projet
 * de services publics extrapolé depuis les 14 secteurs.
 */
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';

const read=path=>JSON.parse(readFileSync(new URL('../'+path,import.meta.url),'utf8'));
const sum=(rows,key)=>rows.reduce((total,row)=>total+Number(row[key]||0),0);
const round1=x=>Math.round(x*10)/10;

export function buildBaseline(){
  const nova=read('projets/projet-nova/data/audit-completude-programme-nova-2026-11-05.json');
  const civic=read('docs/nova-sondages/reception-sondage-boussole-2026-11-08.json');
  const services=read('projets/projet-nova/data/registre-donnees-services-nova-sinjira.json');
  const sinjira=read('docs/sinjira/programme-readiness-2026-11-08.json');

  assert.equal(nova.status,'AUDIT_INTERNE_PROVISOIRE_NON_CERTIFIE');
  assert.equal(sum(nova.dimensions,'weight'),100);
  assert.equal(sum(nova.dimensions,'points'),nova.scoring.earned);
  assert.equal(nova.scoring.maximum,100);
  assert.equal(nova.scoring.earned,nova.scoring.percentage);
  const finance=nova.dimensions.find(d=>d.id==='FINANCES');
  assert.ok(finance,'Dimension finances absente');

  const civicScore=(tool,summary)=>{
    assert.equal(tool.gates.length,summary.total);
    const passed=tool.gates.filter(g=>g.status==='PASSED').length;
    assert.equal(passed,summary.passed);
    assert.equal(round1(passed/summary.total*100),summary.percent);
    assert.equal(tool.all_mandatory_gates_passed,false);
    return {passed,total:tool.gates.length,percent:summary.percent,
      remaining:tool.gates.length-passed,approved:false};
  };
  const compass=civicScore(civic.compass,civic.summary.compass);
  const poll=civicScore(civic.poll,civic.summary.poll);
  assert.equal(civic.compass.comparison_enabled,false);
  assert.equal(civic.poll.published_in_source,false);

  assert.equal(services.dossiers.length,14);
  assert.equal(new Set(services.dossiers.map(x=>x.id)).size,14);
  assert.equal(services.status,'inventaire-des-besoins-sans-series-sectorielles-validees');
  const missingEvidence=services.dossiers.filter(x=>
    x.qualite_verifiee!==true||x.chiffrage_valide!==true).length;

  assert.equal(sum(sinjira.domains,'weight'),100);
  const weighted=round1(sinjira.domains.reduce((t,d)=>t+d.weight*d.maturity,0)/100);
  assert.equal(weighted,66.5);
  assert.equal(sinjira.gates.length,13);
  assert.equal(sinjira.gates.filter(g=>g.status==='OPEN').length,13);
  assert.equal(sinjira.launch.approved,false);
  assert.equal(sinjira.forecast.estimated_completion_date,null);

  return {
    reference_date:'2026-11-08',audit_date:nova.date,
    political:{percent:nova.scoring.percentage,method:'provisional_internal_weighted_audit',
      earned:nova.scoring.earned,max:nova.scoring.maximum,
      finance:{earned:finance.points,max:finance.weight},
      completion_target:'2027-12-31',completion_target_conditional:true},
    public_services:{percent:null,sectors:services.dossiers.length,
      missingValidatedSectorEvidence:missingEvidence,completion_date:null},
    electoral_compass:compass,civic_poll:poll,
    sinjira:{percent:weighted,uncertainty_points:sinjira.estimate_uncertainty_percentage_points,
      gates_open:13,gates_total:13,completion_date:null,approved:false}
  };
}

if(process.argv[1]?.endsWith('validate_quatre_programmes_baseline_20261110.mjs')){
  const data=buildBaseline();
  process.stdout.write('4-CHANTIERS-BASELINE-PASS '+JSON.stringify(data)+'\n');
}
