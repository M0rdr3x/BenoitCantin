import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {REQUIRED_G0_CODES,inspectEvidence,assessRegionalG0,assessAllRegions,
  GATE_NOT_PASSED,REVIEW_ONLY} from "../assets/g0-sante-gate-core.mjs";

const matrix=JSON.parse(await readFile(new URL("../data/matrice-preuves-g0-5-sante.json",import.meta.url),"utf8"));
const regional=JSON.parse(await readFile(new URL("../data/portrait-regional-g0-sante-2025.json",import.meta.url),"utf8"));
const byId=Object.fromEntries(matrix.regions.map(x=>[x.rss_id,x]));

test("matrice G0.5: 18 RSS et 8 garanties distinctes cohérentes avec la source",()=>{
 assert.equal(matrix.regions.length,18);
 assert.equal(matrix.categories.length,8);
 assert.deepEqual(matrix.categories.map(x=>x.code),REQUIRED_G0_CODES);
 assert.deepEqual(matrix.regions.map(x=>x.rss_id),regional.regions.map(x=>x.id));
 assert.deepEqual(matrix.regions.map(x=>x.observed_affiliation_2025_percent),regional.regions.map(x=>x.affiliation_percent));
 assert.ok(matrix.regions.every(x=>Object.keys(x.preuves).length===8));
});

test("tous les territoires restent non approuvés; les liens ISQ ne valident pas le G0",()=>{
 const a=assessAllRegions(matrix);
 assert.equal(a.total_regions,18);
 assert.equal(a.regions_with_affiliation,16);
 assert.equal(a.territories_outside_survey,2);
 assert.equal(a.cells_required,144);
 assert.equal(a.validated_cells,0);
 assert.equal(a.ready_for_formal_review,0);
 assert.equal(a.gate,GATE_NOT_PASSED);
 assert.equal(a.pilot_authorized,false);
 assert.equal(a.savings_certified,false);
 assert.ok(a.decisions.every(x=>x.decision===GATE_NOT_PASSED&&x.blockers.length===8));
});

test("une preuve marquée validée sans sources, méthode ni revue est bloquée",()=>{
 const x={status:"VALIDEE_INDEPENDAMMENT",source_id:"ISQ"};
 const result=inspectEvidence(x);
 assert.equal(result.complete,false);
 assert.ok(result.missing.includes("lien_de_preuve_https"));
 assert.ok(result.missing.includes("validation_independante"));
 assert.ok(result.missing.includes("identite_controleur"));
});

test("un seul critère rempli ne transforme pas un résultat d'enquête en permission",()=>{
 const row=structuredClone(byId["06"]);
 row.preuves.PERIMETRE={
  status:"VALIDEE_INDEPENDAMMENT",
  official_source_id:"DOC_JURIDIQUE",
  reference_period:"2026",
  evidence_url:"https://example.org/synthetic-test",
  perimeter_approved:true,methodological_validated:true,independently_validated:true,
  reviewer:"Contrôleur du test fictif"
 };
 const res=assessRegionalG0(row);
 assert.equal(res.validated_dimensions,1);
 assert.equal(res.blockers.length,7);
 assert.equal(res.decision,GATE_NOT_PASSED);
 assert.equal(res.pilot_authorized,false);
});

test("même huit preuves complètes synthétiques ne franchissent PAS G0 automatiquement",()=>{
 const row=structuredClone(byId["03"]);
 for(const code of REQUIRED_G0_CODES){
  row.preuves[code]={
   status:"VALIDEE_INDEPENDAMMENT",official_source_id:"SOURCE_TEST_"+code,
   reference_period:"2025",evidence_url:"https://example.org/synthetic-test/"+code,
   perimeter_approved:true,methodological_validated:true,independently_validated:true,
   reviewer:"Contrôleur du test fictif"
  };
 }
 const res=assessRegionalG0(row);
 assert.equal(res.ready_for_review,true);
 assert.equal(res.decision,REVIEW_ONLY);
 assert.equal(res.pilot_authorized,false);
 assert.equal(res.budget_authorized,false);
});

test("un RSS hors enquête avec taux fictif est refusé même si ses preuves sont complètes",()=>{
 const row=structuredClone(byId["17"]);
 row.observed_affiliation_2025_percent=88;
 const result=assessRegionalG0(row);
 assert.ok(result.blockers.some(x=>x.code==="HORS_CHAMP"));
 assert.equal(result.pilot_authorized,false);
});

test("différents exercices provinciaux ne sont jamais joints aux 16 taux régionaux",()=>{
 const national=matrix.historique_provincial_separe;
 assert.equal(national.length,3);
 assert.ok(national.every(x=>x.period==="2024-2025"&&x.excluded_from_regional_comparison===true));
 assert.deepEqual(national.map(x=>x.value),[36,84,79.5]);
 assert.ok(matrix.sources.some(x=>x.id==="QUEBEC_RH_2024_2025"&&x.status.includes("NON_IMPORTE")));
 assert.ok(matrix.sources.some(x=>x.id==="QUEBEC_PREMIERE_LIGNE"&&x.status.includes("NON_IMPORTES")));
 assert.ok(matrix.sources.some(x=>x.id==="RAMQ_STATS"&&x.status.includes("SANS_COUT")));
 assert.ok(matrix.regions.every(x=>!x.pilote_autorise&&!x.comparateur_cost_certified));
});

test("liste d'acquisition professionnelle: huit tâches non entamées, sans patients",()=>{
 assert.equal(matrix.acquisition_tasks.length,8);
 assert.ok(matrix.acquisition_tasks.every(x=>x.status==="NON_ENTAME"&&x.received===false));
 assert.equal(new Set(matrix.acquisition_tasks.map(x=>x.id)).size,8);
 assert.equal(matrix.detailed_data_contract.no_patient_data,true);
 assert.equal(matrix.detailed_data_contract.no_microdata_without_authorization,true);
 assert.equal(matrix.automatic_decision.gate,"NON_FRANCHI");
 assert.equal(matrix.automatic_decision.economies_chiffrees,null);
});

test("tableau G0.5 ne peut pas être construit sans les 18 RSS",()=>{
 const broken=structuredClone(matrix);
 broken.regions=broken.regions.slice(0,17);
 assert.throws(()=>assessAllRegions(broken),/18 RSS/);
});
